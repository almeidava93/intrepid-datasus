# intrepid-datasus

A command-line tool to **download and query SIA/SUS – Produção Ambulatorial** (outpatient
care paid by Brazil's public health system, SUS), straight from the DATASUS FTP.

- Every state, every month from **Jul/1994** to the latest release.
- Besides PA, **every other SIA/SUS file type** DATASUS publishes (`-T all`): BPA-I (BI), the ten APAC
  types (AM, AQ, AR, AD, ATD, AN, AB, ABO, ACF, AMP: medicines, oncology, dialysis, ...) and the two RAAS
  types (PS, SAD), each in its own tables; see [Tables](tables/index.md).
- Fetch **all or selected states** (or whole regions) over **any range of months**.
- Data is stored locally as Parquet and queried with **SQL (DuckDB)** — fast, and a
  full month (~70M rows) needs only a few GB of RAM.
- Re-running a fetch only downloads what is new or was **revised by DATASUS**.

> Why not the Kaggle copy ([rafatrindade/sia-producao-ambulatorial](https://www.kaggle.com/datasets/rafatrindade/sia-producao-ambulatorial))?
> Its pipeline skips files DATASUS splits into parts (`PASP2605a.dbc`, `…b`, …), so it is
> missing **São Paulo from 2013 and Rio de Janeiro / Minas Gerais from 2021** — about half of
> all procedures in recent months. This tool reads the FTP directly and handles split files.


## Setup

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run datasus --help
```


## Options

- `--data-dir/-d` or the `DATASUS_DATA_DIR` environment variable: where data lives (default `./data`).
- `--memory-limit 8GB` on `query`/`shell` to cap DuckDB's memory; large queries spill to `<data-dir>/.duckdb_tmp`.
