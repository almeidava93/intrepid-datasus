"""SIGTAP — the SUS procedure table (Tabela Unificada de Procedimentos).

DATASUS publishes one version per month (Jan/2008 onward) as a zip of fixed-width
text files, each with a companion ``<table>_layout.txt`` (column, width, start, end,
type). Every table is stored as Parquet, all columns as text:

    <root>/sigtap/competencia=202610/tb_procedimento.parquet
    <root>/sigtap/versions.json

Codes are retired over time, so names for older data may only exist in older
versions; query.py builds views that keep the most recent description of each code.
"""
from __future__ import annotations

import csv
import io
import json
import os
import re
import shutil
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from .catalog import _parse_list_line, backoff, connect

FTP_HOST = "ftp2.datasus.gov.br"
FTP_DIR = "/public/sistemas/tup/downloads"
NAME_RE = re.compile(r"^TabelaUnificada_(\d{6})(?:_v(\d+))?\.zip$", re.IGNORECASE)  # early files have no _v


@dataclass(frozen=True)
class Version:
    competencia: int
    name: str
    size: int


def list_versions(retries: int = 5) -> list[Version]:
    for attempt in range(1, retries + 1):
        try:
            lines: list[str] = []
            with connect(host=FTP_HOST) as ftp:
                ftp.cwd(FTP_DIR)
                ftp.retrlines("LIST", lines.append)
            break
        except Exception:
            if attempt == retries:
                raise
            backoff(attempt)
    by: dict[int, Version] = {}
    for line in lines:
        parsed = _parse_list_line(line)
        if not parsed:
            continue
        m = NAME_RE.match(parsed[0])
        if m:
            v = Version(int(m.group(1)), parsed[0], parsed[1])
            # if a month is ever republished, keep the newest build
            if v.competencia not in by or v.name > by[v.competencia].name:
                by[v.competencia] = v
    return sorted(by.values(), key=lambda v: v.competencia)


def pick(versions: list[Version], start: int | None, end: int | None, yearly: bool) -> list[Version]:
    """Versions in [start, end]; with yearly, the last one of each year."""
    vs = [v for v in versions if (start is None or v.competencia >= start) and (end is None or v.competencia <= end)]
    if yearly:
        last: dict[int, Version] = {}
        for v in vs:
            last[v.competencia // 100] = v
        vs = sorted(last.values(), key=lambda v: v.competencia)
    return vs


# ------------------------------------------------------------------ parsing
def parse_layout(text: str) -> list[tuple[str, int, int]]:
    """'Coluna,Tamanho,Inicio,Fim,Tipo' CSV -> [(column, start0, end0_exclusive)]."""
    rows = list(csv.reader(io.StringIO(text.strip())))
    out = []
    for r in rows[1:]:
        if len(r) < 4 or not r[0].strip():
            continue
        try:
            out.append((r[0].strip(), int(r[2]) - 1, int(r[3])))
        except ValueError:  # some old layouts have junk rows (e.g. 'NULL)'); skip them
            continue
    return out


def parse_table(data: bytes, layout: list[tuple[str, int, int]]) -> pa.Table:
    """Fixed-width latin-1 lines -> table of text columns (blank -> NULL)."""
    cols: dict[str, list] = {name: [] for name, _, _ in layout}
    for raw in data.split(b"\n"):
        line = raw.rstrip(b"\r")
        if not line.strip():
            continue
        for name, s, e in layout:
            v = line[s:e].decode("latin-1").strip()
            cols[name].append(v or None)
    return pa.table({k: pa.array(v, type=pa.string()) for k, v in cols.items()})


def import_zip(zpath: Path, out_dir: Path) -> dict[str, int]:
    """Convert every table in a SIGTAP zip; returns {table: rows}."""
    tmp = out_dir.with_name(".tmp-" + out_dir.name)  # outside the competencia=* glob
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True)
    counts: dict[str, int] = {}
    with zipfile.ZipFile(zpath) as z:
        names = {Path(n).name.lower(): n for n in z.namelist()}
        for lname, member in names.items():
            if not lname.endswith("_layout.txt"):
                continue
            table = lname[: -len("_layout.txt")]
            if table + ".txt" not in names:
                continue
            try:
                layout = parse_layout(z.read(member).decode("latin-1"))
                if not layout:
                    raise ValueError("empty layout")
                t = parse_table(z.read(names[table + ".txt"]), layout)
            except Exception as e:
                if table == "tb_procedimento":
                    raise ValueError(f"{zpath.name}: cannot read tb_procedimento ({e})") from e
                continue  # skip a broken minor table rather than the whole version
            pq.write_table(t, tmp / f"{table}.parquet", compression="zstd")
            counts[table] = t.num_rows
    if "tb_procedimento" not in counts:
        raise ValueError(f"{zpath.name}: no tb_procedimento table found")
    if out_dir.exists():
        shutil.rmtree(out_dir)
    os.replace(tmp, out_dir)
    return counts


# -------------------------------------------------------------------- store
class SigtapStore:
    def __init__(self, root: Path):
        self.dir = Path(root) / "sigtap"
        self.index_path = self.dir / "versions.json"

    def index(self) -> dict[str, dict]:
        if not self.index_path.exists():
            return {}
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def has(self, v: Version) -> bool:
        e = self.index().get(str(v.competencia))
        return bool(e) and e["file"] == v.name and (self.dir / f"competencia={v.competencia}").is_dir()

    def fetch(self, v: Version, retries: int = 5) -> dict[str, int]:
        self.dir.mkdir(parents=True, exist_ok=True)
        zpath = self.dir / v.name
        for attempt in range(1, retries + 1):
            try:
                with connect(host=FTP_HOST) as ftp, open(zpath, "wb") as fh:
                    ftp.cwd(FTP_DIR)
                    ftp.retrbinary(f"RETR {v.name}", fh.write, blocksize=1 << 20)
                if v.size and zpath.stat().st_size != v.size:
                    raise OSError(f"{v.name}: incomplete download")
                break
            except Exception:
                if attempt == retries:
                    raise
                backoff(attempt)
        try:
            counts = import_zip(zpath, self.dir / f"competencia={v.competencia}")
        finally:
            for i in range(6):  # Windows may hold the zip briefly
                try:
                    zpath.unlink(missing_ok=True)
                    break
                except PermissionError:
                    time.sleep(0.2 * (i + 1))
        idx = self.index()
        idx[str(v.competencia)] = {
            "file": v.name, "tables": counts,
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        tmp = self.index_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(idx, indent=1, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.index_path)
        return counts

    def tables(self) -> list[str]:
        names: set[str] = set()
        for d in self.dir.glob("competencia=*"):
            if d.is_dir():
                names |= {f.stem for f in d.glob("*.parquet")}
        return sorted(names)
