"""What exists on the DATASUS FTP: states, layouts ("eras"), files and month ranges."""
from __future__ import annotations

import ftplib
import random
import re
import time
from collections import defaultdict
from dataclasses import dataclass

FTP_HOST = "ftp.datasus.gov.br"

# IBGE code, name and region for each state.
STATES: dict[str, tuple[str, str, str]] = {
    "RO": ("11", "Rondônia", "Norte"), "AC": ("12", "Acre", "Norte"),
    "AM": ("13", "Amazonas", "Norte"), "RR": ("14", "Roraima", "Norte"),
    "PA": ("15", "Pará", "Norte"), "AP": ("16", "Amapá", "Norte"),
    "TO": ("17", "Tocantins", "Norte"), "MA": ("21", "Maranhão", "Nordeste"),
    "PI": ("22", "Piauí", "Nordeste"), "CE": ("23", "Ceará", "Nordeste"),
    "RN": ("24", "Rio Grande do Norte", "Nordeste"), "PB": ("25", "Paraíba", "Nordeste"),
    "PE": ("26", "Pernambuco", "Nordeste"), "AL": ("27", "Alagoas", "Nordeste"),
    "SE": ("28", "Sergipe", "Nordeste"), "BA": ("29", "Bahia", "Nordeste"),
    "MG": ("31", "Minas Gerais", "Sudeste"), "ES": ("32", "Espírito Santo", "Sudeste"),
    "RJ": ("33", "Rio de Janeiro", "Sudeste"), "SP": ("35", "São Paulo", "Sudeste"),
    "PR": ("41", "Paraná", "Sul"), "SC": ("42", "Santa Catarina", "Sul"),
    "RS": ("43", "Rio Grande do Sul", "Sul"), "MS": ("50", "Mato Grosso do Sul", "Centro-Oeste"),
    "MT": ("51", "Mato Grosso", "Centro-Oeste"), "GO": ("52", "Goiás", "Centro-Oeste"),
    "DF": ("53", "Distrito Federal", "Centro-Oeste"),
}


@dataclass(frozen=True)
class Era:
    """One DATASUS file layout, stored in its own FTP folder and local table."""
    key: str        # local folder / partition root
    view: str       # DuckDB view name
    ftp_dir: str
    first: int      # first competência (YYYYMM)
    last: int       # last competência (YYYYMM), inclusive


LEGACY = Era("pa_legacy", "pa_legacy", "/dissemin/publicos/SIASUS/199407_200712/Dados", 199407, 200712)
CURRENT = Era("pa", "pa", "/dissemin/publicos/SIASUS/200801_/Dados", 200801, 999912)
ERAS = (LEGACY, CURRENT)

FILE_RE = re.compile(r"^PA([A-Z]{2})(\d{2})(\d{2})([A-Z]?)\.DBC$", re.IGNORECASE)


def era_for(comp: int) -> Era:
    return LEGACY if comp <= LEGACY.last else CURRENT


@dataclass(frozen=True)
class RemoteFile:
    name: str
    size: int
    uf: str
    competencia: int
    part: str  # "" for a single file, "a", "b", ... for split states


def parse_name(name: str, size: int = 0) -> RemoteFile | None:
    """'PASP2605b.dbc' -> RemoteFile(uf='SP', competencia=202605, part='b')."""
    m = FILE_RE.match(name)
    if not m:
        return None
    uf = m.group(1).upper()
    if uf not in STATES:
        return None
    yy, mm = int(m.group(2)), int(m.group(3))
    if not 1 <= mm <= 12:
        return None
    year = 1900 + yy if yy >= 90 else 2000 + yy
    return RemoteFile(name, size, uf, year * 100 + mm, m.group(4).lower())


@dataclass(frozen=True)
class Partition:
    """Everything DATASUS publishes for one state and one month (one or more files)."""
    uf: str
    competencia: int
    files: tuple[RemoteFile, ...]

    @property
    def era(self) -> Era:
        return era_for(self.competencia)

    @property
    def size(self) -> int:
        return sum(f.size for f in self.files)

    @property
    def key(self) -> str:
        return f"{self.uf}/{self.competencia}"

    def signature(self) -> dict[str, int]:
        return {f.name: f.size for f in self.files}


def group(files: list[RemoteFile]) -> list[Partition]:
    by: dict[tuple[str, int], list[RemoteFile]] = defaultdict(list)
    for f in files:
        by[(f.uf, f.competencia)].append(f)
    return [
        Partition(uf, comp, tuple(sorted(fs, key=lambda f: f.part)))
        for (uf, comp), fs in sorted(by.items(), key=lambda kv: (kv[0][1], kv[0][0]))
    ]


def _parse_list_line(line: str) -> tuple[str, int] | None:
    """Parse an IIS-style LIST line: '10-30-26  09:48PM   169954126 PAPR2604a.dbc'."""
    parts = line.split(maxsplit=3)
    if len(parts) == 4 and parts[2].isdigit():
        return parts[3].strip(), int(parts[2])
    parts = line.split()  # Unix-style fallback: perms links owner group size mon day time name
    if len(parts) >= 9 and parts[4].isdigit():
        return parts[-1], int(parts[4])
    return None


class _PasvFixFTP(ftplib.FTP):
    """The DATASUS server sometimes advertises a wrong IP in PASV replies;
    always open data connections to the host we are already talking to."""

    def makepasv(self):
        _, port = super().makepasv()
        return self.sock.getpeername()[0], port


def connect(timeout: int = 120, host: str = FTP_HOST) -> ftplib.FTP:
    ftp = _PasvFixFTP()
    ftp.connect(host, 21, timeout=timeout)
    ftp.login()
    ftp.set_pasv(True)
    return ftp


def backoff(attempt: int) -> None:
    """Exponential backoff with jitter (attempt starts at 1)."""
    time.sleep(min(5 * 2 ** (attempt - 1), 120) + random.uniform(0, 3))


def list_remote(eras: tuple[Era, ...] = ERAS, retries: int = 5) -> list[RemoteFile]:
    """List every PA file in the requested eras' FTP folders."""
    for attempt in range(1, retries + 1):
        try:
            return _list_remote(eras)
        except (*ftplib.all_errors, EOFError):
            if attempt == retries:
                raise
            backoff(attempt)
    return []


def _list_remote(eras: tuple[Era, ...]) -> list[RemoteFile]:
    out: dict[str, RemoteFile] = {}
    with connect(timeout=180) as ftp:
        for era in eras:
            lines: list[str] = []
            ftp.cwd(era.ftp_dir)
            ftp.retrlines("LIST", lines.append)
            for line in lines:
                parsed = _parse_list_line(line)
                if not parsed:
                    continue
                rf = parse_name(*parsed)
                # each folder should only hold its own era; ignore strays.
                # The FTP sometimes lists X.DBC and X.dbc: keep one.
                if rf and era.first <= rf.competencia <= era.last:
                    out.setdefault(rf.name.upper(), rf)
    return list(out.values())


def select(partitions: list[Partition], states: set[str] | None, start: int, end: int) -> list[Partition]:
    return [
        p for p in partitions
        if start <= p.competencia <= end and (states is None or p.uf in states)
    ]


# ---------------------------------------------------------------- arguments
def parse_states(value: str | None) -> set[str] | None:
    """'SP,RJ' / 'sp rj' / 'all' / 'Sudeste' -> set of UFs (None means every state)."""
    if value is None or value.strip().lower() in ("", "all", "todos", "br"):
        return None
    regions = {r.lower(): r for _, _, r in STATES.values()}
    out: set[str] = set()
    for tok in re.split(r"[,\s]+", value.strip()):
        if not tok:
            continue
        if tok.lower() in regions:
            out |= {uf for uf, (_, _, r) in STATES.items() if r == regions[tok.lower()]}
        elif tok.upper() in STATES:
            out.add(tok.upper())
        else:
            raise ValueError(f"unknown state or region {tok!r} (use codes like SP, RJ, or a region like Sudeste)")
    return out


def parse_period(value: str, *, is_end: bool) -> int:
    """'2023' -> 202301 (start) or 202312 (end); '2023-05' / '202305' -> 202305."""
    v = value.strip().replace("-", "").replace("/", "")
    if re.fullmatch(r"\d{4}", v):
        return int(v) * 100 + (12 if is_end else 1)
    if re.fullmatch(r"\d{6}", v) and 1 <= int(v[4:]) <= 12:
        return int(v)
    raise ValueError(f"expected YYYY or YYYYMM, got {value!r}")


def months(start: int, end: int) -> list[int]:
    out, y, m = [], start // 100, start % 100
    while y * 100 + m <= end:
        out.append(y * 100 + m)
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out
