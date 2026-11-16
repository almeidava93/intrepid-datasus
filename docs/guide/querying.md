# Querying

The data is queried with SQL, in the [DuckDB dialect](https://duckdb.org/docs/sql/introduction).
Every table is a view over the local Parquet files; nothing is loaded in advance.

## From the command line

```bash
uv run datasus shell                                    # interactive SQL prompt
uv run datasus query "SELECT uf, SUM(PA_QTDAPR) AS procedimentos
                      FROM pa WHERE competencia = 202505
                      GROUP BY uf ORDER BY procedimentos DESC"
uv run datasus query -F my_query.sql -o result.csv     # also .parquet / .json
uv run datasus query --format csv "SELECT ..." > out.csv
```

In the shell, end each statement with `;`. Shell commands: `.tables`, `.schema <table>`,
`.quit`.

| Option of `query` | Meaning |
|---|---|
| `--file/-F` | Read the SQL from a file. |
| `--output/-o` | Write the full result to `.csv`, `.parquet` or `.json`. |
| `--format` | `table` (default), `csv` or `json` on screen. |
| `--max-rows` | Rows shown on screen (default 50). |
| `--memory-limit 8GB` | Cap DuckDB's memory; large queries spill to `<data-dir>/.duckdb_tmp`. |

`shell` takes `--max-rows` and `--memory-limit` too.

## Finding your way around

```bash
uv run datasus status -T all        # which tables, states and months you have
uv run datasus schema -T aq         # every column of a table, with descriptions
uv run datasus sigtap search hemodialise   # procedure codes by name
```

```sql
-- every table and view available right now
SELECT table_name FROM information_schema.tables ORDER BY 1;
-- columns of a table
DESCRIBE pa;
```

Which table to use for which question: [SIA overview](../databases/sia/index.md#which-table-do-i-need).
Ready-made queries: [SQL cookbook](../databases/sia/examples.md).

## SQL tips for this data

- **Filter on `competencia` and `uf`.** Only the matching files are read.
- **Codes are text.** `PA_TPFIN = '06'`, `PA_PROC_ID LIKE '0305%'` (a SIGTAP code prefix
  selects a group, subgroup or form of organisation).
- **Dates are text** (`'20250513'`, `'202505'`): `strptime(AP_DTINIC, '%Y%m%d')` gives a
  date; `competencia // 100` gives the year and `competencia % 100` the month.
- **Shares of a total:** `100.0 * SUM(x) / SUM(SUM(x)) OVER ()`.
- **Several conditional sums in one pass:** `SUM(PA_QTDAPR) FILTER (WHERE PA_SEXO = 'F')`.
- **Top N per group:** `QUALIFY ROW_NUMBER() OVER (PARTITION BY uf ORDER BY qtd DESC) <= 3`.
- **Years as columns:** `PIVOT (...) ON ano USING SUM(PA_QTDAPR)`.
- **`GROUP BY ALL`** groups by every non-aggregated column.
- **`LEFT JOIN` the lookups** when you want to keep codes that have no name.

## From Python, R or other tools

The data is plain Parquet in Hive-style folders, `data/<table>/competencia=YYYYMM/uf=XX/*.parquet`,
so any tool that reads Parquet can use it.

**Python, with the same views as the CLI:**

```python
from pathlib import Path
from intrepid_datasus.query import connect
from intrepid_datasus.store import Store

con = connect(Store(Path("data")), memory_limit="8GB")
df = con.sql("""
    SELECT uf, SUM(PA_QTDAPR) AS procedimentos
    FROM pa WHERE competencia = 202505 GROUP BY 1
""").df()                       # pandas DataFrame; .pl() for Polars
```

**Python or R, reading the Parquet directly with DuckDB:**

```python
import duckdb
duckdb.sql("""
    SELECT uf, SUM(TRY_CAST(PA_QTDAPR AS BIGINT)) AS procedimentos
    FROM read_parquet('data/pa/*/*/*.parquet', hive_partitioning = true, union_by_name = true)
    WHERE competencia = 202505 GROUP BY 1
""").df()
```

```r
library(arrow); library(dplyr)
pa <- open_dataset("data/pa", unify_schemas = TRUE)
pa |> filter(competencia == 202505) |>
  group_by(uf) |> summarise(procedimentos = sum(as.integer(PA_QTDAPR))) |> collect()
```

Read directly, every column is text (the typed views are built by intrepid-datasus): cast
quantities and values before summing.

## Performance

A full national month of PA (~70 million rows) is queried in about a second on a laptop and
needs a few GB of RAM. For years of data, filter on `competencia`, select only the columns
you need, and set `--memory-limit` if the machine is shared.
