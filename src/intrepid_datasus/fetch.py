"""Download one file type's state-month from the FTP and turn it into a local Parquet partition."""
from __future__ import annotations

import ftplib
import shutil
import time
from dataclasses import dataclass
from pathlib import Path

import pyarrow.parquet as pq

from .catalog import Partition, RemoteFile, backoff, connect
from .convert import dbc_to_parquet, unlink_retry
from .store import Store


@dataclass
class Result:
    partition: Partition
    rows: int
    nbytes: int
    seconds: float


def _download(ftp: ftplib.FTP, f: RemoteFile, dest: Path) -> None:
    have = dest.stat().st_size if dest.exists() else 0
    if f.size and have == f.size:
        return
    if f.size and have > f.size:
        dest.unlink()
        have = 0
    with open(dest, "ab") as fh:
        ftp.retrbinary(f"RETR {f.name}", fh.write, blocksize=1 << 20, rest=have or None)
    if f.size and dest.stat().st_size != f.size:
        raise RuntimeError(f"{f.name}: got {dest.stat().st_size:,} bytes, expected {f.size:,}")


def download_partition(p: Partition, dest_dir: Path, retries: int = 5) -> list[Path]:
    """Download every file of a partition, resuming partial files between retries."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    pending = list(p.files)
    for attempt in range(1, retries + 1):
        try:
            with connect(timeout=300) as ftp:
                ftp.cwd(p.era.ftp_dir)
                ftp.voidcmd("TYPE I")
                while pending:
                    _download(ftp, pending[0], dest_dir / pending[0].name)
                    pending.pop(0)
            break
        except (*ftplib.all_errors, EOFError, RuntimeError):
            if attempt == retries:
                raise
            backoff(attempt)
    return [dest_dir / f.name for f in p.files]


def build_partition(p: Partition, root: str, keep_dbc: bool = False) -> Result:
    """Worker entry point (runs in a subprocess). Does not touch the manifest."""
    t0 = time.time()
    store = Store(Path(root))
    stage = store.staging_dir(p)
    dl, built = stage / "dbc", stage / "parquet"
    if built.exists():
        shutil.rmtree(built)
    built.mkdir(parents=True)

    rows = 0
    for dbc in download_partition(p, dl):
        rows += dbc_to_parquet(dbc, built / (dbc.stem + ".parquet"))
        if not keep_dbc:
            unlink_retry(dbc)
    # sanity check before replacing anything
    for f in built.glob("*.parquet"):
        pq.ParquetFile(f)
    if keep_dbc:
        keep = store.root / "dbc" / p.era.key
        keep.mkdir(parents=True, exist_ok=True)
        for f in dl.glob("*.dbc"):
            shutil.move(str(f), keep / f.name)

    nbytes = store.publish(p, built)
    shutil.rmtree(stage, ignore_errors=True)
    return Result(p, rows, nbytes, time.time() - t0)
