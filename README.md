# intrepid-datasus

**Download Brazil's public health data from DATASUS and query it with SQL on your own
machine.**

DATASUS publishes the records of Brazil's public health system (SUS) as thousands of
compressed files on an FTP server, one per state and month. This tool downloads the ones
you ask for, keeps them up to date, converts them to Parquet and gives you documented SQL
tables (DuckDB) with name lookups.

📖 **Documentation: <https://almeidava93.github.io/intrepid-datasus/>**

| Database | What it covers | Status |
|---|---|---|
| **SIA/SUS** | Outpatient care paid by SUS: consultations, exams, medicines, chemotherapy, radiotherapy, dialysis, mental health (CAPS), home care, ... All 14 file types, every state, every month since Jul/1994. | Available |
| SIH, SIM, SINASC, CNES, SINAN | Hospital admissions, deaths, births, facilities, notifiable diseases | Planned |

## Quick start

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync
uv run datasus available -s AC -f 2025      # what's on the FTP (nothing is downloaded)
uv run datasus fetch -s AC -f 202505        # one state, one month of outpatient production
uv run datasus sigtap fetch                 # procedure, diagnosis and occupation names
uv run datasus shell                        # interactive SQL
```

```sql
-- The 10 most frequent procedures
SELECT p.nome, SUM(PA_QTDAPR) AS procedimentos
FROM pa JOIN procedimentos p ON p.codigo = pa.PA_PROC_ID
WHERE competencia = 202505
GROUP BY 1 ORDER BY 2 DESC LIMIT 10;
```

Then:

- [Getting started](docs/getting-started.md): the ten-minute tutorial.
- [Key concepts](docs/concepts.md): competência, UF, CNES, SIGTAP, CID-10, and how data is stored.
- [SIA overview](docs/databases/sia/index.md): which table answers which question.
- [SQL cookbook](docs/databases/sia/examples.md): spending, top procedures, patient travel,
  cancer screening, telehealth, CAPS, dialysis, ...
- [Pitfalls](docs/databases/sia/data-notes.md): read before you count.
- [Fetching](docs/guide/fetching.md) and [Querying](docs/guide/querying.md) (CLI, Python, R).

## Why not the Kaggle copy?

[rafatrindade/sia-producao-ambulatorial](https://www.kaggle.com/datasets/rafatrindade/sia-producao-ambulatorial)
skips files DATASUS splits into parts (`PASP2605a.dbc`, `…b`, …), so it is missing
**São Paulo from 2013 and Rio de Janeiro / Minas Gerais from 2021**, about half of all
procedures in recent months. This tool reads the FTP directly and handles split files.

## Development

```bash
uv run pytest
uv sync --group docs && uv run mkdocs serve   # docs preview
```

Pull requests run the tests and a strict docs build; merges to `main` publish the docs to
GitHub Pages. See [Development](docs/contributing/development.md) and
[Adding a database](docs/contributing/adding-a-database.md).

Data: Ministério da Saúde / DATASUS. Cite DATASUS when publishing results.
