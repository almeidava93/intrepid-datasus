# Key concepts

The vocabulary you need to read DATASUS data, and how intrepid-datasus stores it. These
apply to every database; each database's own concepts (SIA's forms, APAC, RAAS) are on its
overview page.

## Brazilian health system terms

| Term | Meaning |
|---|---|
| **SUS** | *Sistema Único de Saúde*, Brazil's public, universal health system. DATASUS data covers care that SUS **pays for**, delivered by public or contracted private facilities. |
| **DATASUS** | The Ministry of Health's IT department, which runs the information systems and publishes their data on an FTP server. |
| **Competência** | The reference month of a record, written `YYYYMM` (`202505` = May/2025). In SIA it is the month the production was **processed**, which can be later than the month care happened. |
| **UF** | *Unidade Federativa*: one of the 26 states or the Federal District, by its two-letter code (`SP`, `AC`, `DF`). DATASUS publishes one file per state per month. |
| **Region** | The five macro-regions: Norte, Nordeste, Sudeste, Sul, Centro-Oeste. |
| **IBGE municipality code** | Six digits (the 7-digit IBGE code without its check digit): the first two are the state (`35` = São Paulo), so `355030` is the city of São Paulo. Used for both facility location and patient residence. |
| **CNES** | *Cadastro Nacional de Estabelecimentos de Saúde*, the national registry of health facilities. Every facility has a 7-digit CNES code. |
| **CNS** | *Cartão Nacional de Saúde*, the national health card number of a patient or professional. Patient CNS values are **encoded** by DATASUS: usable to count distinct patients, not to identify or link them. |
| **SIGTAP** | *Tabela de Procedimentos, Medicamentos e OPM do SUS*: the list of every procedure, medicine and device SUS pays for, with a 10-digit code, rules and price. In use since Jan/2008. See [SIGTAP](lookups/sigtap.md). |
| **CID-10** | ICD-10, the International Classification of Diseases, written without the dot (`J189`, `C50`). |
| **CBO** | *Classificação Brasileira de Ocupações*: 6-digit occupation code of the professional who did the procedure (`225125` = clinical physician). |
| **Complexidade** | SIGTAP's level of care of a procedure: *Atenção Básica* (primary care), *Média Complexidade* (medium), *Alta Complexidade* (high). |
| **Financiamento** | How a procedure is funded: PAB (primary care, per capita), MAC (medium and high complexity), FAEC (strategic actions), pharmaceutical care, ... |
| **Glosa** | Production a facility submitted that the audit rejected: the difference between *apresentado* (submitted) and *aprovado* (approved). |

## How data is stored

Every database follows the same pattern, so once you know one you know them all.

### Files and partitions

`datasus fetch` downloads the original `.dbc` files from the DATASUS FTP, converts them to
Parquet, and stores them in Hive-style partitions:

```text
data/
  pa/
    competencia=202505/
      uf=SP/
        PASP2505a.parquet   one Parquet file per original .dbc file
        PASP2505b.parquet
  bi/
  sigtap/
  manifest.json      what was fetched, from which files, when
```

Set another location with `--data-dir/-d` or the `DATASUS_DATA_DIR` environment variable.

### Two partition columns on every table

| Column | Type | Meaning |
|---|---|---|
| `competencia` | `INTEGER` | Month of the file, `YYYYMM`. |
| `uf` | `VARCHAR` | State of the file, e.g. `SP`. |

They come from the folder names, not from DATASUS. **Filter on them whenever you can**:
DuckDB then reads only the matching folders, so a query on one month of one state is
instant even with years of data stored.

```sql
SELECT SUM(PA_QTDAPR) FROM pa WHERE competencia = 202505 AND uf = 'SP';
```

The column `_ARQUIVO_ORIGEM` records the original DATASUS file of each row
(`PASP2505a.dbc`), useful when a state's month is split into several files.

### Typed and raw views

Each table comes in two views over the same files:

| View | Contents |
|---|---|
| `pa`, `bi`, `aq`, ... | Quantities cast to `BIGINT` and money to `DOUBLE`, ready to sum. Everything else stays text. |
| `pa_raw`, `bi_raw`, ... | Every column as text, exactly as DATASUS publishes it. |

Codes stay text on purpose, because leading zeros matter: write `PA_TPFIN = '06'`, not
`PA_TPFIN = 6`. Dates are text too (`'20250513'`); convert with
`strptime(col, '%Y%m%d')` when you need date arithmetic. Malformed numbers become `NULL`
in the typed view instead of failing the query.

### Columns change over time

When DATASUS adds a column, it appears automatically and older months show `NULL`. When a
whole layout changes, the database gets one table per layout (SIA's `pa_legacy` for
1994–2007 and `pa` for 2008 onward).

### Revisions

DATASUS silently revises recently published months, and sometimes splits a file into
parts. Re-running a `datasus fetch` compares each month with the FTP and rebuilds only what
changed, so it is safe and cheap to repeat.

## Reference data

Codes are joined to names through lookup tables shared by all databases: `ufs`,
`procedimentos`, `cid10`, `ocupacoes` and every SIGTAP table. See
[Reference data](lookups/index.md).

## Citing

Data: Ministério da Saúde / DATASUS. Cite DATASUS and the information system (e.g.
*Sistema de Informações Ambulatoriais do SUS – SIA/SUS*) when you publish results.
