# intrepid-datasus

**Download Brazil's public health data from DATASUS and query it with SQL on your own
machine.**

DATASUS publishes the records of Brazil's public health system (SUS) as thousands of
compressed files on an FTP server, one per state and month, in an old database format.
intrepid-datasus downloads the ones you ask for, keeps them up to date, converts them to
Parquet, and gives you ready-made SQL tables with documented columns and name lookups.

```bash
uv run datasus fetch -s SP -f 2025
uv run datasus query "SELECT SUM(PA_QTDAPR) FROM pa WHERE competencia = 202505"
```

## Databases

| Database | What it covers | Status |
|---|---|---|
| [**SIA/SUS**](databases/sia/index.md) | Outpatient care paid by SUS: consultations, exams, medicines, chemotherapy, dialysis, mental health, ... Every state, every month since Jul/1994. | Available |
| SIH, SIM, SINASC, CNES, SINAN | Hospital admissions, deaths, births, facilities, notifiable diseases | Planned |

See [DATASUS databases](databases/index.md) for what each one records and how they connect.

## Where to start

<div class="grid cards" markdown>

- **New here?** — [Getting started](getting-started.md): install, fetch one month, run
  your first queries, in ten minutes.
- **What do the codes mean?** — [Key concepts](concepts.md): competência, UF, CNES,
  SIGTAP, CID-10, and how the data is stored.
- **Which table answers my question?** — [SIA overview](databases/sia/index.md#which-table-do-i-need).
- **Show me queries.** — [SQL cookbook](databases/sia/examples.md): spending, top
  procedures, patient travel, cancer screening, telehealth, CAPS, dialysis, ...
- **Avoid wrong answers.** — [Pitfalls](databases/sia/data-notes.md).
- **Every column.** — one page per table, e.g. [`pa`](databases/sia/pa.md).

</div>

## Why this tool

- **Complete.** Reads the FTP directly and handles files DATASUS splits into parts
  (`PASP2605a.dbc`, `…b`, …). The Kaggle copy
  ([rafatrindade/sia-producao-ambulatorial](https://www.kaggle.com/datasets/rafatrindade/sia-producao-ambulatorial))
  skips them, so it misses **São Paulo from 2013 and Rio de Janeiro / Minas Gerais from
  2021**, about half of all procedures in recent months.
- **Fast and light.** Parquet + DuckDB: a national month (~70M rows) needs a few GB of RAM.
- **Up to date.** Re-running a fetch only downloads what is new or was **revised by
  DATASUS**.
- **Documented.** Every column of every table, checked against real files, with the traps
  that produce wrong numbers.

Data: Ministério da Saúde / DATASUS. Cite DATASUS when publishing results.
