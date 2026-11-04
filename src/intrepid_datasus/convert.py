"""Convert DATASUS .dbc files (compressed DBF) to Parquet.

All columns are kept as text, exactly as DATASUS publishes them (codes keep their
leading zeros). Numeric columns are cast when queried; see query.py.
"""
from __future__ import annotations

import os
import struct
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

CHUNK = 1_000_000  # records per Parquet row group
ORIGIN_COL = "_ARQUIVO_ORIGEM"


def read_dbf_header(path: Path) -> tuple[int, int, int, list[tuple[str, int, int]]]:
    """Return (records, header_len, record_len, [(field, offset, width), ...])."""
    with open(path, "rb") as fh:
        nrec, hlen, rlen = struct.unpack("<IHH", fh.read(32)[4:12])
        fields, off = [], 1  # byte 0 of every record is the deletion flag
        while True:
            d = fh.read(32)
            if not d or d[0] == 0x0D:
                break
            fields.append((d[:11].split(b"\x00")[0].decode("ascii"), off, d[16]))
            off += d[16]
    if off != rlen:
        raise ValueError(f"{path.name}: field widths add up to {off}, record length is {rlen}")
    # trust the file size over the header count if they disagree (truncated files)
    nrec = min(nrec, max(0, (path.stat().st_size - hlen) // rlen)) if rlen else 0
    return nrec, hlen, rlen, fields


def dbf_to_parquet(dbf: Path, out: Path, origin: str) -> int:
    """Stream a DBF file into Parquet; returns the number of rows written."""
    nrec, hlen, rlen, fields = read_dbf_header(dbf)
    schema = pa.schema([(name, pa.string()) for name, _, _ in fields] + [(ORIGIN_COL, pa.string())])
    tmp = out.with_name(out.name + ".tmp")
    written = 0
    with pq.ParquetWriter(tmp, schema, compression="zstd") as writer:
        if nrec:
            mm = np.memmap(dbf, dtype=np.uint8, mode="r", offset=hlen, shape=(nrec, rlen))
            try:
                for s in range(0, nrec, CHUNK):
                    block = np.ascontiguousarray(mm[s : s + CHUNK])
                    block = block[block[:, 0] != ord("*")]  # drop deleted records
                    cols = {}
                    for name, o, width in fields:
                        raw = block[:, o : o + width].copy().view(f"S{width}").ravel()
                        ser = pd.Series(raw, dtype=object).str.decode("latin-1").str.strip()
                        cols[name] = pa.array(ser.where(ser != "", None), type=pa.string())
                    cols[ORIGIN_COL] = pa.array([origin] * len(block), type=pa.string())
                    writer.write_table(pa.table(cols, schema=schema))
                    written += len(block)
            finally:
                del mm
        else:
            writer.write_table(schema.empty_table())
    os.replace(tmp, out)  # a file only gets its final name once complete
    return written


def unlink_retry(path: Path, tries: int = 6) -> None:
    """Windows can briefly lock a file that was just closed (WinError 32); retry."""
    for i in range(tries):
        try:
            path.unlink(missing_ok=True)
            return
        except PermissionError:
            time.sleep(0.2 * (i + 1))
    path.unlink(missing_ok=True)


def dbc_to_parquet(dbc: Path, out: Path) -> int:
    from pyreaddbc import dbc2dbf  # imported here so tests can run without it

    dbf = out.with_name(out.stem + ".dbf.tmp")
    try:
        dbc2dbf(str(dbc), str(dbf))
        return dbf_to_parquet(dbf, out, origin=dbc.name)
    except Exception as e:
        raise RuntimeError(f"{dbc.name}: could not convert ({type(e).__name__}: {e})") from e
    finally:
        unlink_retry(dbf)
