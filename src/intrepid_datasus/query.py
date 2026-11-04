"""DuckDB views over the local Parquet store.

Views:
    pa          2008 onward, numbers cast (quantities BIGINT, values DOUBLE)
    pa_legacy   1994-2007, same casting
    pa_raw / pa_legacy_raw   everything as text, exactly as stored
    ufs         state code, IBGE code, name and region
"""
from __future__ import annotations

from pathlib import Path

import duckdb

from .catalog import ERAS, STATES
from .store import Store

QUANTITY_COLS = ["PA_QTDPRO", "PA_QTDAPR"]
VALUE_COLS = [
    "PA_VALPRO", "PA_VALAPR", "PA_DIF_VAL", "NU_VPA_TOT", "NU_PA_TOT",
    "PA_VL_CF", "PA_VL_CL", "PA_VL_INC", "PA_VL_CRD",
]


def _sql_path(p: Path) -> str:
    return str(p.resolve()).replace("\\", "/").replace("'", "''")


def connect(store: Store, memory_limit: str | None = None, threads: int | None = None) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute("SET preserve_insertion_order = false")  # lower memory for large scans
    if memory_limit:
        con.execute(f"SET memory_limit = '{memory_limit}'")
    if threads:
        con.execute(f"SET threads = {int(threads)}")
    spill = store.root / ".duckdb_tmp"
    con.execute(f"SET temp_directory = '{_sql_path(spill)}'")

    for era in ERAS:
        d = store.era_dir(era)
        if not d.is_dir() or next(d.glob("competencia=*/uf=*/*.parquet"), None) is None:
            continue
        glob = _sql_path(d) + "/competencia=*/uf=*/*.parquet"
        con.execute(
            f"CREATE VIEW {era.view}_raw AS SELECT * FROM read_parquet('{glob}', "
            "hive_partitioning = true, union_by_name = true, "
            "hive_types = {'competencia': 'INTEGER', 'uf': 'VARCHAR'})"
        )
        cols = {r[0] for r in con.execute(f"DESCRIBE {era.view}_raw").fetchall()}
        casts = [f"TRY_CAST({c} AS BIGINT) AS {c}" for c in QUANTITY_COLS if c in cols]
        casts += [f"TRY_CAST({c} AS DOUBLE) AS {c}" for c in VALUE_COLS if c in cols]
        replace = f" REPLACE ({', '.join(casts)})" if casts else ""
        con.execute(f"CREATE VIEW {era.view} AS SELECT *{replace} FROM {era.view}_raw")

    rows = ", ".join(f"('{uf}', '{ibge}', '{name.replace(chr(39), chr(39) * 2)}', '{reg}')"
                     for uf, (ibge, name, reg) in STATES.items())
    con.execute(f"CREATE TABLE ufs AS SELECT * FROM (VALUES {rows}) t(uf, ibge, nome, regiao)")
    return con


def views(con: duckdb.DuckDBPyConnection) -> list[str]:
    return [r[0] for r in con.execute(
        "SELECT table_name FROM information_schema.tables ORDER BY table_name").fetchall()]


def copy_to(con: duckdb.DuckDBPyConnection, sql: str, out: Path, fmt: str) -> None:
    """Write a query result straight to a file (streams; works for huge results)."""
    options = {"parquet": "FORMAT parquet, COMPRESSION zstd", "csv": "FORMAT csv, HEADER true",
               "json": "FORMAT json, ARRAY true"}[fmt]
    con.execute(f"COPY ({clean(sql)}) TO '{_sql_path(out)}' ({options})")


def clean(sql: str) -> str:
    return sql.strip().rstrip(";").strip()
