# intrepid-datasus

A command-line tool to **download and query SIA/SUS – Produção Ambulatorial** (outpatient
care paid by Brazil's public health system, SUS), straight from the DATASUS FTP.

- Every state, every month from **Jul/1994** to the latest release.
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

## Fetching data

```bash
# what's on the FTP, and how big (nothing is downloaded)
uv run datasus available -s SP -f 2025

# one state, one year
uv run datasus fetch -s SP -f 2025

# several states, a range of months
uv run datasus fetch -s SP,RJ,MG -f 202401 -t 202406

# a region, or the whole country
uv run datasus fetch -s Nordeste -f 2025
uv run datasus fetch -s all -f 202605

# preview the plan first
uv run datasus fetch -s all -f 2024 --dry-run

# choose the SIA file type(s): pa is the default
uv run datasus fetch -T pa -s AC -f 202605
uv run datasus fetch -T all -s AC -f 202605
```

- `--table/-T`: which SIA file types (tables) to work on: a code like `pa`, several like
  `pa,bi`, or `all`. Default: `pa`, so commands without it behave as they always have.
  `available`, `fetch`, `status`, `schema` and `remove` all take it. Each file type is one
  table family (see [Tables](docs/tables/index.md)); the registered ones are listed in
  `datasus fetch --help`. (`-t` is `--to`; the table flag is a capital `-T`.)
- `--states/-s`: `all` (default), codes like `SP,RJ`, or a region: `Norte`, `Nordeste`,
  `Sudeste`, `Sul`, `Centro-Oeste`.
- `--from/-f`, `--to/-t`: `YYYY` or `YYYYMM`. `--to` defaults to the end of `--from`.
- `--workers/-w` (default 3), `--force`, `--keep-dbc`, `--yes/-y`.

Re-running the same command is safe and cheap: state-months that match the FTP are skipped;
any whose files changed (DATASUS silently revises recent months, and sometimes re-splits
them into parts) are rebuilt. An interrupted run resumes where it stopped.

**Sizes** (May/2026, all 27 states): ~2.7 GB to download, ~1 GB as Parquet, ~71M rows.
A year is roughly 11–13 GB of Parquet. While converting, each worker needs a few GB of
temporary disk.

## Querying

```bash
uv run datasus query "SELECT uf, SUM(PA_QTDAPR) AS procedimentos, SUM(PA_VALAPR) AS valor
                      FROM pa WHERE competencia BETWEEN 202501 AND 202512
                      GROUP BY uf ORDER BY procedimentos DESC"

uv run datasus query -F my_query.sql -o result.csv     # also .parquet / .json
uv run datasus query --format csv "SELECT ..." > out.csv
uv run datasus shell                                    # interactive SQL prompt
uv run datasus schema                                   # columns + descriptions (pa)
uv run datasus schema --legacy                          # columns of pa_legacy
uv run datasus status                                   # what's stored locally (pa)
uv run datasus status -T all                            # ... for every table
uv run datasus remove -s RR -f 2026                     # delete local data (pa)
```

Tables available in SQL:

| Table | Contents |
|---|---|
| `pa` | 2008 onward (SIGTAP procedure codes). Quantities as `BIGINT`, values as `DOUBLE`. |
| `pa_legacy` | 1994–2007 (old layout and procedure table — different columns). |
| `pa_raw`, `pa_legacy_raw` | Same, every column as text, exactly as DATASUS publishes it. |
| `bi`, `bi_raw` | BPA Individualizado (`-T bi`, 2008 onward): one row per patient appointment, with age, sex, residence and diagnosis. Same rows as `pa WHERE PA_DOCORIG = 'I'` — don't add the two. |
| `am`, `am_raw` | APAC Medicamentos (`-T am`, 2008 onward): one row per APAC for a high-cost medicine per month, with patient, diagnosis, validity and continuation. Same APACs as `pa WHERE PA_DOCORIG = 'P' AND PA_TPFIN = '02'` — don't add the two. |
| `aq`, `aq_raw` | APAC Quimioterapia (`-T aq`, 2008 onward): one row per chemotherapy/hormone therapy APAC per month, with cancer ICD-10, stage, lymph nodes, treatment purpose, scheme and dates. Same APACs as `pa WHERE PA_DOCORIG = 'P'` with procedures `030402`–`030408` — don't add the two. |
| `ar`, `ar_raw` | APAC Radioterapia (`-T ar`, 2008 onward): one row per radiotherapy APAC per month, with cancer ICD-10, stage, treatment purpose, treated areas, number of fields/insertions and dates. Same APACs as `pa WHERE PA_DOCORIG = 'P'` with procedures `030401` — don't add the two. |
| `ad`, `ad_raw` | APAC Laudos Diversos (`-T ad`, 2008 onward): one row per APAC per month for the procedures with no laudo of their own: cataract and other eye surgery, eye injections, cardiac catheterisation, hearing diagnosis and aids, transplant follow-up, PET-CT, wheelchairs, and (until 2012) CAPS mental health care. Same APACs as some of the `pa WHERE PA_DOCORIG = 'P'` rows — don't add the two. |
| `atd`, `atd_raw` | APAC Tratamento Dialítico (`-T atd`, Aug/2014 onward; AN before): one row per dialysis APAC per month — in practice one patient on chronic dialysis per month — with dialysis type, vascular access, transplant status, lab values (haemoglobin, phosphorus, albumin, PTH, Kt/V, URR) and serology. Same APACs as `pa WHERE PA_DOCORIG = 'P' AND PA_PROC_ID LIKE '0305%'` — don't add the two. |
| `ufs` | State code, IBGE code, name and region — join on `uf`. |
| `procedimentos` | SIGTAP procedure names, group, complexity, funding, price — join `PA_PROC_ID = codigo`. |
| `cid10`, `ocupacoes` | ICD-10 and CBO (occupation) names — join on `PA_CIDPRI` / `PA_CBOCOD`. |
| `sigtap_*` | Every SIGTAP table (e.g. `sigtap_rl_procedimento_cid`); `…_all` keeps every version. |

## Procedure names (SIGTAP)

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

## Things to know about the data

- **Sum `PA_QTDAPR`, don't count rows.** One row can stand for thousands of procedures.
- **Half of all procedures have no patient data.** Consolidated reports (`PA_DOCORIG = 'C'`)
  have no age, sex, diagnosis or residence (`PA_SEXO = '0'`, `PA_MUNPCN = '999999'`).
- `PA_UFMUN` is where the **facility** is; `PA_MUNPCN` is where the **patient lives**.
- `competencia` is the processing month (`PA_MVM`); `PA_CMP` is when care happened and
  includes late reports from earlier months.
- Values are nominal R$ — adjust for inflation (e.g. IPCA) before comparing years.
- "Not informed" codes: `PA_CIDPRI = '0000'`, `PA_IDADE = '999'`, `PA_RACACOR = '00'`/`'99'`.
- Official layout and code tables: [DATASUS – Transferência de arquivos](https://datasus.saude.gov.br/transferencia-de-arquivos/) (SIA → Documentação).

## Options

- `--data-dir/-d` or the `DATASUS_DATA_DIR` environment variable: where data lives (default `./data`).
- `--memory-limit 8GB` on `query`/`shell` to cap DuckDB's memory; large queries spill to `<data-dir>/.duckdb_tmp`.

## Development

```bash
uv run pytest
uv sync --group docs && uv run mkdocs serve   # docs preview
```

Pull requests run the tests (`.github/workflows/ci.yml`) and a strict docs build
(`.github/workflows/docs.yml`); merges to `main` publish the docs to GitHub Pages.

Source: `src/intrepid_datasus/` — `catalog.py` (FTP listing, states, periods), `convert.py`
(.dbc → Parquet), `store.py` (local layout and manifest), `fetch.py`, `query.py` (DuckDB views),
`dictionary.py` (column descriptions), `cli.py`.

Data: Ministério da Saúde / DATASUS, SIA/SUS. Cite DATASUS when publishing results.
