"""DuckDB views over the local Parquet store.

Views, for every era of every file type in ``catalog.REGISTRY`` that has local data:
    <era>       numbers cast (the era's quantity columns BIGINT, value columns DOUBLE)
    <era>_raw   everything as text, exactly as stored
    e.g. pa (2008 onward), pa_legacy (1994-2007), pa_raw, pa_legacy_raw
    ufs         state code, IBGE code, name and region
    procedimentos, cid10, ocupacoes, sigtap_*   SIGTAP lookups (after `datasus sigtap fetch`)
"""
from __future__ import annotations

from pathlib import Path

import duckdb

from .catalog import STATES, all_eras
from .sigtap import SigtapStore
from .store import Store

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

    for era in all_eras():
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
        casts = [f"TRY_CAST({c} AS BIGINT) AS {c}" for c in era.quantity_cols if c in cols]
        casts += [f"TRY_CAST({c} AS DOUBLE) AS {c}" for c in era.value_cols if c in cols]
        replace = f" REPLACE ({', '.join(casts)})" if casts else ""
        con.execute(f"CREATE VIEW {era.view} AS SELECT *{replace} FROM {era.view}_raw")

    rows = ", ".join(f"('{uf}', '{ibge}', '{name.replace(chr(39), chr(39) * 2)}', '{reg}')"
                     for uf, (ibge, name, reg) in STATES.items())
    con.execute(f"CREATE TABLE ufs AS SELECT * FROM (VALUES {rows}) t(uf, ibge, nome, regiao)")
    _sigtap_views(con, store)
    return con


def _sigtap_views(con: duckdb.DuckDBPyConnection, store: Store) -> None:
    """sigtap_<table>_all: every fetched version (column competencia).
    sigtap_<table>: for tb_* tables, the most recent row of each code (with first/last
    version seen and whether it is still active); for rl_* tables, the latest version.
    Plus friendly views: procedimentos, cid10, ocupacoes."""
    st = SigtapStore(store.root)
    tables = st.tables()
    if not tables:
        return
    base = _sql_path(st.dir)
    for t in tables:
        short = t[3:] if t.startswith("tb_") else t
        con.execute(
            f"CREATE VIEW sigtap_{short}_all AS SELECT * FROM read_parquet('{base}/competencia=*/{t}.parquet', "
            "hive_partitioning = true, union_by_name = true, hive_types = {'competencia': 'INTEGER'})"
        )
        cols = [r[0] for r in con.execute(f"DESCRIBE sigtap_{short}_all").fetchall()]
        keys = []
        for c in cols:
            if not c.startswith("CO_"):
                break
            keys.append(c)
        if t.startswith("tb_") and keys:
            k = ", ".join(keys)
            con.execute(f"""CREATE VIEW sigtap_{short} AS
                SELECT * EXCLUDE (competencia, rn, first_seen, last_seen),
                       first_seen AS primeira_versao, last_seen AS ultima_versao,
                       last_seen = (SELECT MAX(competencia) FROM sigtap_{short}_all) AS ativo
                FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY {k} ORDER BY competencia DESC) rn,
                             MIN(competencia) OVER (PARTITION BY {k}) first_seen,
                             MAX(competencia) OVER (PARTITION BY {k}) last_seen
                      FROM sigtap_{short}_all)
                WHERE rn = 1""")
        else:
            con.execute(f"""CREATE VIEW sigtap_{short} AS SELECT * EXCLUDE (competencia)
                FROM sigtap_{short}_all WHERE competencia = (SELECT MAX(competencia) FROM sigtap_{short}_all)""")

    have = set(tables)
    if "tb_procedimento" in have:
        pcols = {r[0] for r in con.execute("DESCRIBE sigtap_procedimento").fetchall()}

        def lookup(table: str, sql: str) -> str:
            return sql if table in have else "NULL"

        def col(name: str, sql: str) -> str:
            return sql if name in pcols else "NULL"

        con.execute(f"""CREATE VIEW procedimentos AS
            SELECT p.CO_PROCEDIMENTO AS codigo, p.NO_PROCEDIMENTO AS nome,
                   LEFT(p.CO_PROCEDIMENTO, 2) AS grupo_cod,
                   {lookup('tb_grupo', 'g.NO_GRUPO')} AS grupo,
                   {lookup('tb_sub_grupo', 's.NO_SUB_GRUPO')} AS subgrupo,
                   {lookup('tb_forma_organizacao', 'f.NO_FORMA_ORGANIZACAO')} AS forma_organizacao,
                   {col('TP_COMPLEXIDADE', '''CASE p.TP_COMPLEXIDADE WHEN '0' THEN 'Não se aplica'
                        WHEN '1' THEN 'Atenção Básica' WHEN '2' THEN 'Média Complexidade'
                        WHEN '3' THEN 'Alta Complexidade' ELSE p.TP_COMPLEXIDADE END''')} AS complexidade,
                   {col('CO_FINANCIAMENTO', 'p.CO_FINANCIAMENTO')} AS financiamento_cod,
                   {lookup('tb_financiamento', 'fi.NO_FINANCIAMENTO')} AS financiamento,
                   {col('TP_SEXO', 'p.TP_SEXO')} AS sexo,
                   {col('VL_IDADE_MINIMA', 'TRY_CAST(p.VL_IDADE_MINIMA AS INTEGER)')} AS idade_minima_meses,
                   {col('VL_IDADE_MAXIMA', 'TRY_CAST(p.VL_IDADE_MAXIMA AS INTEGER)')} AS idade_maxima_meses,
                   {col('VL_SA', 'TRY_CAST(p.VL_SA AS DOUBLE) / 100')} AS valor_ambulatorial,
                   {col('VL_SH', 'TRY_CAST(p.VL_SH AS DOUBLE) / 100')} AS valor_hospitalar,
                   {col('VL_SP', 'TRY_CAST(p.VL_SP AS DOUBLE) / 100')} AS valor_profissional,
                   p.primeira_versao, p.ultima_versao, p.ativo
            FROM sigtap_procedimento p
            {"LEFT JOIN sigtap_grupo g ON g.CO_GRUPO = LEFT(p.CO_PROCEDIMENTO, 2)" if 'tb_grupo' in have else ""}
            {"LEFT JOIN sigtap_sub_grupo s ON s.CO_GRUPO || s.CO_SUB_GRUPO = LEFT(p.CO_PROCEDIMENTO, 4)" if 'tb_sub_grupo' in have else ""}
            {"LEFT JOIN sigtap_forma_organizacao f ON f.CO_GRUPO || f.CO_SUB_GRUPO || f.CO_FORMA_ORGANIZACAO = LEFT(p.CO_PROCEDIMENTO, 6)" if 'tb_forma_organizacao' in have else ""}
            {"LEFT JOIN sigtap_financiamento fi ON fi.CO_FINANCIAMENTO = p.CO_FINANCIAMENTO" if 'tb_financiamento' in have else ""}""")
    if "tb_cid" in have:
        con.execute("CREATE VIEW cid10 AS SELECT CO_CID AS codigo, NO_CID AS nome, TP_SEXO AS sexo, ativo FROM sigtap_cid")
    if "tb_ocupacao" in have:
        con.execute("CREATE VIEW ocupacoes AS SELECT CO_OCUPACAO AS codigo, NO_OCUPACAO AS nome, ativo FROM sigtap_ocupacao")


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
