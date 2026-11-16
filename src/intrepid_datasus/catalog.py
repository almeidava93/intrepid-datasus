"""What exists on the DATASUS FTP: SIA file types, their layouts ("eras"), states, files and months.

``REGISTRY`` holds one ``FileType`` per supported SIA file type (PA, BI, ...). Each file type
has one or more ``Era``s (layouts over time); each era has its FTP folder, its local folder
(``data/<era.key>/``) and its DuckDB views (``<era.key>`` and ``<era.key>_raw``).
"""
from __future__ import annotations

import ftplib
import random
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Mapping

from . import dictionary

FTP_HOST = "ftp.datasus.gov.br"
FTP_LEGACY_DIR = "/dissemin/publicos/SIASUS/199407_200712/Dados"  # Jul/1994 - Dec/2007
FTP_CURRENT_DIR = "/dissemin/publicos/SIASUS/200801_/Dados"       # Jan/2008 onward

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
    """One layout of a file type: its FTP folder, months, local table and columns."""
    key: str        # local folder (data/<key>/...) and DuckDB view name (<key>, <key>_raw)
    ftp_dir: str
    first: int      # first competência (YYYYMM)
    last: int       # last competência (YYYYMM), inclusive
    dictionary: Mapping[str, str] = field(default_factory=dict, compare=False, repr=False)
    quantity_cols: tuple[str, ...] = ()  # cast to BIGINT in the typed view
    value_cols: tuple[str, ...] = ()     # cast to DOUBLE in the typed view

    @property
    def view(self) -> str:
        return self.key

    def covers(self, comp: int) -> bool:
        return self.first <= comp <= self.last


@dataclass(frozen=True)
class RemoteFile:
    name: str
    size: int
    uf: str
    competencia: int
    part: str  # "" for a single file; "a", "b", ... (PA) or "1", "2", ... (BI, "_1") for split states
    table: str = "PA"  # file type code


@dataclass(frozen=True)
class FileType:
    """One SIA file type (PA, BI, ATD, ...), files named ``<CODE><UF><YY><MM>[part].dbc``.

    ``part`` is empty for a whole file, or a letter (``PASP2605a.dbc``) or ``_<n>``
    (``BISP2605_1.dbc``) when DATASUS splits a large state into several files."""
    code: str                 # 2-3 capital letters, as in the file names
    name: str                 # what DATASUS calls it
    eras: tuple[Era, ...]     # oldest first, not overlapping
    parquet_ratio: float = 0.37  # Parquet size / .dbc size, for disk estimates (PA, May/2026)

    def __post_init__(self):
        if not re.fullmatch(r"[A-Z]{2,3}", self.code):
            raise ValueError(f"file type code must be 2-3 capital letters, got {self.code!r}")
        # The UF is always exactly two letters right before four digits, so one code can
        # never match another's files (AM vs AMP, AB vs ABO): the lengths would not add up.
        object.__setattr__(self, "_re", re.compile(
            rf"^{self.code}([A-Z]{{2}})(\d{{2}})(\d{{2}})(?:([A-Z])|_(\d{{1,2}}))?\.DBC$", re.IGNORECASE))

    @property
    def first(self) -> int:
        return self.eras[0].first

    @property
    def last(self) -> int:
        return self.eras[-1].last

    @property
    def views(self) -> list[str]:
        return [e.view for e in self.eras]

    def era_for(self, comp: int) -> Era:
        for era in self.eras:
            if era.covers(comp):
                return era
        raise ValueError(f"{self.code} has no layout for {comp}")

    def parse(self, name: str, size: int = 0) -> RemoteFile | None:
        """'PASP2605b.dbc' -> RemoteFile(uf='SP', competencia=202605, part='b', table='PA');
        'BISP2605_2.dbc' -> part='2'."""
        m = self._re.match(name)
        if not m:
            return None
        uf = m.group(1).upper()
        if uf not in STATES:
            return None
        yy, mm = int(m.group(2)), int(m.group(3))
        if not 1 <= mm <= 12:
            return None
        year = 1900 + yy if yy >= 90 else 2000 + yy
        part = (m.group(4) or m.group(5) or "").lower()
        return RemoteFile(name, size, uf, year * 100 + mm, part, self.code)


# ------------------------------------------------------------------ registry
# One entry per SIA file type. To add one, see docs/development.md
# ("Adding a new SIA file type").
PA = FileType("PA", "Produção Ambulatorial", (
    Era("pa_legacy", FTP_LEGACY_DIR, 199407, 200712, dictionary.PA_LEGACY,
        quantity_cols=dictionary.PA_QUANTITY_COLS, value_cols=dictionary.PA_VALUE_COLS),
    Era("pa", FTP_CURRENT_DIR, 200801, 999912, dictionary.PA,
        quantity_cols=dictionary.PA_QUANTITY_COLS, value_cols=dictionary.PA_VALUE_COLS),
))

BI = FileType("BI", "BPA Individualizado", (
    Era("bi", FTP_CURRENT_DIR, 200801, 999912, dictionary.BI,
        quantity_cols=dictionary.BI_QUANTITY_COLS, value_cols=dictionary.BI_VALUE_COLS),
), parquet_ratio=0.43)  # AC May/2026: 0.41; SP Aug/2026 part 1: 0.45

AM = FileType("AM", "APAC Medicamentos", (
    Era("am", FTP_CURRENT_DIR, 200801, 999912, dictionary.AM,
        quantity_cols=dictionary.AM_QUANTITY_COLS, value_cols=dictionary.AM_VALUE_COLS),
), parquet_ratio=0.5)  # AC May/2026: 0.57; SP Jul/2025 (largest file): 0.47

AQ = FileType("AQ", "APAC Quimioterapia", (
    Era("aq", FTP_CURRENT_DIR, 200801, 999912, dictionary.AQ,
        quantity_cols=dictionary.AQ_QUANTITY_COLS, value_cols=dictionary.AQ_VALUE_COLS),
), parquet_ratio=0.45)  # SP Jul/2025 (largest file): 0.44; SC 2024-2026: 0.48

AR = FileType("AR", "APAC Radioterapia", (
    Era("ar", FTP_CURRENT_DIR, 200801, 999912, dictionary.AR,
        quantity_cols=dictionary.AR_QUANTITY_COLS, value_cols=dictionary.AR_VALUE_COLS),
), parquet_ratio=0.8)  # all 5,491 files: 0.81 (tiny files, ~20 KB Parquet overhead each)

AD = FileType("AD", "APAC Laudos Diversos", (
    Era("ad", FTP_CURRENT_DIR, 200801, 999912, dictionary.AD,
        quantity_cols=dictionary.AD_QUANTITY_COLS, value_cols=dictionary.AD_VALUE_COLS),
), parquet_ratio=0.58)  # all 6,046 files: 1.90 GB Parquet / 3.25 GB .dbc

ATD = FileType("ATD", "APAC Tratamento Dialítico", (
    Era("atd", FTP_CURRENT_DIR, 201408, 999912, dictionary.ATD,
        quantity_cols=dictionary.ATD_QUANTITY_COLS, value_cols=dictionary.ATD_VALUE_COLS),
), parquet_ratio=0.75)  # all 3,911 files: 0.79 GB Parquet / 1.06 GB .dbc

AN = FileType("AN", "APAC Nefrologia", (  # discontinued: replaced by ATD (data ends Jul/2014)
    Era("an", FTP_CURRENT_DIR, 200801, 201410, dictionary.AN,
        quantity_cols=dictionary.AN_QUANTITY_COLS, value_cols=dictionary.AN_VALUE_COLS),
), parquet_ratio=0.66)  # all 2,145 files: 0.30 GB Parquet / 0.46 GB .dbc

PS = FileType("PS", "RAAS Psicossocial", (
    Era("ps", FTP_CURRENT_DIR, 201211, 999912, dictionary.PS,
        quantity_cols=dictionary.PS_QUANTITY_COLS, value_cols=dictionary.PS_VALUE_COLS),
), parquet_ratio=0.62)  # all 4,421 files: 2.05 GB Parquet / 3.31 GB .dbc

SAD = FileType("SAD", "RAAS Atenção Domiciliar", (  # discontinued: last file Oct/2018
    Era("sad", FTP_CURRENT_DIR, 201204, 201810, dictionary.SAD,
        quantity_cols=dictionary.SAD_QUANTITY_COLS, value_cols=dictionary.SAD_VALUE_COLS),
), parquet_ratio=0.89)  # all 1,088 files: 47.3 MB Parquet / 53.4 MB .dbc (tiny files)

AB = FileType("AB", "APAC Cirurgia Bariátrica", (  # follow-up; data ends Apr/2017, + a copy of ABO Jan-Jul/2025
    Era("ab", FTP_CURRENT_DIR, 200801, 202507, dictionary.AB,
        quantity_cols=dictionary.AB_QUANTITY_COLS, value_cols=dictionary.AB_VALUE_COLS),
), parquet_ratio=1.2)  # all 635 files: 19.3 MB Parquet / 16.1 MB .dbc (tiny files, ~25 KB each)

ABO = FileType("ABO", "APAC Acompanhamento Pós-Cirurgia Bariátrica", (  # the same APACs as AB, from 2014
    Era("abo", FTP_CURRENT_DIR, 201401, 999912, dictionary.ABO,
        quantity_cols=dictionary.ABO_QUANTITY_COLS, value_cols=dictionary.ABO_VALUE_COLS),
), parquet_ratio=1.38)  # all 1,621 files: 53.7 MB Parquet / 38.9 MB .dbc (tiny files, ~24 KB each)

REGISTRY: dict[str, FileType] = {ft.code: ft for ft in (PA, BI, AM, AQ, AR, AD, ATD, AN, PS, SAD, AB, ABO)}
DEFAULT_TABLES = ("PA",)  # what the CLI uses when --table is not given


def file_type(code: str) -> FileType:
    return REGISTRY[code.upper()]


def all_eras() -> list[Era]:
    return [era for ft in REGISTRY.values() for era in ft.eras]


def parse_name(name: str, size: int = 0) -> RemoteFile | None:
    """Parse a file name of any registered type ('PASP2605b.dbc', ...); None if none matches."""
    for ft in REGISTRY.values():
        rf = ft.parse(name, size)
        if rf:
            return rf
    return None


@dataclass(frozen=True)
class Partition:
    """Everything DATASUS publishes for one file type, state and month (one or more files)."""
    uf: str
    competencia: int
    files: tuple[RemoteFile, ...]
    table: str = "PA"  # file type code

    @property
    def file_type(self) -> FileType:
        return REGISTRY[self.table]

    @property
    def era(self) -> Era:
        return self.file_type.era_for(self.competencia)

    @property
    def size(self) -> int:
        return sum(f.size for f in self.files)

    @property
    def key(self) -> str:
        """Manifest key: 'PA/SP/202605'."""
        return f"{self.table}/{self.uf}/{self.competencia}"

    @property
    def label(self) -> str:
        """For messages: 'PA SP 2026-05'."""
        return f"{self.table} {self.uf} {self.competencia // 100}-{self.competencia % 100:02d}"

    def signature(self) -> dict[str, int]:
        return {f.name: f.size for f in self.files}


def _part_order(f: RemoteFile) -> tuple[int, str]:
    return len(f.part), f.part  # '', 'a', 'b', ... / '1', '2', ..., '10'


def group(files: list[RemoteFile]) -> list[Partition]:
    """Group files into partitions (one per file type, state and month).

    When the FTP holds both a whole file and split parts for the same month (BI SP/MG/RJ
    2023-05 to 2024-02 have ``BISP2305.dbc`` *and* ``BISP2305_1.dbc``, ``_2``), the parts
    are the newer, complete publication and the whole file is dropped: keeping both would
    count every row twice."""
    by: dict[tuple[str, str, int], list[RemoteFile]] = defaultdict(list)
    for f in files:
        by[(f.table, f.uf, f.competencia)].append(f)
    out = []
    for (table, uf, comp), fs in sorted(by.items(), key=lambda kv: (kv[0][0], kv[0][2], kv[0][1])):
        if any(f.part for f in fs):
            fs = [f for f in fs if f.part]
        out.append(Partition(uf, comp, tuple(sorted(fs, key=_part_order)), table))
    return out


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


def wanted_dirs(types: list[FileType], start: int, end: int) -> dict[str, list[Era]]:
    """FTP folders to list for these file types and months, with the eras each one serves."""
    out: dict[str, list[Era]] = defaultdict(list)
    for ft in types:
        for era in ft.eras:
            if era.first <= end and era.last >= start:
                out[era.ftp_dir].append(era)
    return dict(out)


def match_listing(names: list[tuple[str, int]], types: list[FileType], eras: list[Era]) -> list[RemoteFile]:
    """Pick out of one folder listing the files of the given types whose month is in one of `eras`."""
    out: dict[str, RemoteFile] = {}
    for name, size in names:
        for ft in types:
            rf = ft.parse(name, size)
            # each folder should only hold its own era; ignore strays.
            # The FTP sometimes lists X.DBC and X.dbc: keep one.
            if rf and any(e in ft.eras and e.covers(rf.competencia) for e in eras):
                out.setdefault(rf.name.upper(), rf)
                break
    return list(out.values())


def list_remote(types: list[FileType] | None = None, start: int = 0, end: int = 999912,
                retries: int = 5) -> list[RemoteFile]:
    """List the files of the given file types (default: all registered) with months in range.

    Each FTP folder holds every file type, so each needed folder is listed only once."""
    types = list(REGISTRY.values()) if types is None else types
    for attempt in range(1, retries + 1):
        try:
            return _list_remote(types, start, end)
        except (*ftplib.all_errors, EOFError):
            if attempt == retries:
                raise
            backoff(attempt)
    return []


def _list_remote(types: list[FileType], start: int, end: int) -> list[RemoteFile]:
    dirs = wanted_dirs(types, start, end)
    if not dirs:
        return []
    out: list[RemoteFile] = []
    with connect(timeout=180) as ftp:
        for ftp_dir, eras in dirs.items():
            lines: list[str] = []
            ftp.cwd(ftp_dir)
            ftp.retrlines("LIST", lines.append)
            names = [p for p in map(_parse_list_line, lines) if p]
            out += match_listing(names, types, eras)
    return out


def select(partitions: list[Partition], states: set[str] | None, start: int, end: int,
           tables: set[str] | None = None) -> list[Partition]:
    return [
        p for p in partitions
        if start <= p.competencia <= end and (states is None or p.uf in states)
        and (tables is None or p.table in tables)
    ]


# ---------------------------------------------------------------- arguments
def parse_tables(value: str | None) -> list[FileType]:
    """'pa,bi' / 'PA BI' / 'all' -> file types in registry order (None or '' -> the default, PA)."""
    if value is None or not value.strip():
        return [REGISTRY[c] for c in DEFAULT_TABLES]
    if value.strip().lower() in ("all", "todos"):
        return list(REGISTRY.values())
    wanted: set[str] = set()
    for tok in re.split(r"[,\s]+", value.strip()):
        if not tok:
            continue
        if tok.upper() not in REGISTRY:
            raise ValueError(f"unknown table {tok!r} (available: {', '.join(c.lower() for c in REGISTRY)}, or all)")
        wanted.add(tok.upper())
    return [ft for code, ft in REGISTRY.items() if code in wanted]


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
