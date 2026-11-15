# Procedure names (SIGTAP)

The PA files only have codes. SIGTAP, the SUS procedure table, has the names, groups,
prices and rules. DATASUS publishes one version per month since Jan/2008 (~2 MB each).

```bash
uv run datasus sigtap fetch                       # latest version
uv run datasus sigtap fetch --from 2008 --yearly  # one per year: names for retired codes too
uv run datasus sigtap search teleconsulta         # find codes by name (accents ignored) or code prefix
uv run datasus sigtap available
```

```sql
SELECT p.nome, SUM(PA_QTDAPR) qtd
FROM pa JOIN procedimentos p ON p.codigo = pa.PA_PROC_ID
WHERE competencia = 202605 GROUP BY 1 ORDER BY 2 DESC LIMIT 20;
```

For each code the views keep the most recent description from the versions you fetched,
plus `primeira_versao` / `ultima_versao` (first/last version it appears in) and `ativo`.
With `--yearly`, those dates are only precise to the year. Procedure codes in `pa_legacy`
(1994–2007) use the old SIA table and are not in SIGTAP.

Every row also has `competencia` (YYYYMM, the file's month) and `uf` (state). Filtering on
them is fast: only the matching files are read.

You can also use the Parquet files from Python, R or any other tool:
`data/pa/competencia=YYYYMM/uf=XX/*.parquet` (Hive-style partitions).
