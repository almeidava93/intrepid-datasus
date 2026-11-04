import struct
from pathlib import Path

import pytest


def write_dbf(path: Path, fields: list[tuple[str, int]], rows: list[list[str]], deleted: set[int] = frozenset()) -> Path:
    """Write a minimal dBase III file with character fields."""
    rlen = 1 + sum(w for _, w in fields)
    hlen = 32 + 32 * len(fields) + 1
    head = bytearray(32)
    head[0] = 0x03
    head[4:12] = struct.pack("<IHH", len(rows), hlen, rlen)
    desc = b""
    for name, width in fields:
        d = bytearray(32)
        d[: len(name)] = name.encode("ascii")
        d[11] = ord("C")
        d[16] = width
        desc += bytes(d)
    body = b""
    for i, row in enumerate(rows):
        body += b"*" if i in deleted else b" "
        for (_, width), value in zip(fields, row):
            body += value.encode("latin-1").ljust(width)[:width]
    path.write_bytes(bytes(head) + desc + b"\x0d" + body + b"\x1a")
    return path


@pytest.fixture
def make_dbf(tmp_path):
    def _make(name="t.dbf", fields=None, rows=None, deleted=frozenset()):
        return write_dbf(tmp_path / name, fields, rows, deleted)
    return _make
