# Tables overview

Every table below is available in `datasus query` and `datasus shell`. They are DuckDB
views over the local Parquet store, so a table only exists once its data has been fetched:

| Table | Needs | Rows are | Page |
|---|---|---|---|
| `pa` | `datasus fetch` (2008 onward) | one line of outpatient production | [pa](pa.md) |
| `pa_raw` | same | same, every column as text | [pa](pa.md#pa-vs-pa_raw) |
| `pa_legacy` | `datasus fetch` (1994–2007) | one line of outpatient production, old layout | [pa_legacy](pa_legacy.md) |
| `pa_legacy_raw` | same | same, every column as text | [pa_legacy](pa_legacy.md) |
| `ufs` | nothing (built in) | one state | [Lookups](lookups.md#ufs) |
| `procedimentos` | `datasus sigtap fetch` | one SIGTAP procedure code | [Lookups](lookups.md#procedimentos) |
| `cid10` | `datasus sigtap fetch` | one ICD-10 code | [Lookups](lookups.md#cid10) |
| `ocupacoes` | `datasus sigtap fetch` | one CBO occupation code | [Lookups](lookups.md#ocupacoes) |
| `sigtap_<table>` | `datasus sigtap fetch` | latest row of each code / latest relationship | [SIGTAP tables](sigtap.md) |
| `sigtap_<table>_all` | `datasus sigtap fetch` | every row of every fetched version | [SIGTAP tables](sigtap.md) |

To see what exists in your own store, and every column with its description:

```bash
uv run datasus status     # which states and months are stored locally
uv run datasus schema     # columns of each table, with descriptions
uv run datasus query "SELECT table_name FROM information_schema.tables ORDER BY 1"
```

## How the tables fit together

```text
                       ufs (uf)
                         │
pa ── PA_PROC_ID ──► procedimentos (codigo) ──► sigtap_rl_procedimento_* (CO_PROCEDIMENTO)
 │ ── PA_CIDPRI  ──► cid10 (codigo)
 │ ── PA_CBOCOD  ──► ocupacoes (codigo)
 └─── uf         ──► ufs (uf)
```

`pa_legacy` joins `ufs` the same way, but **not** the SIGTAP lookups: its procedure codes
(`PA_CODPRO`) belong to the old SIA table that SIGTAP replaced in Jan/2008.

## Partition columns

Both `pa` and `pa_legacy` have two extra columns that are not in the DATASUS files. They
come from the folder layout (`data/pa/competencia=YYYYMM/uf=XX/`):

| Column | Type | Meaning |
|---|---|---|
| `competencia` | `INTEGER` | Month of the file, `YYYYMM` (equals `PA_MVM`, the processing month). |
| `uf` | `VARCHAR` | State of the file, e.g. `SP`. |

Filter on them whenever you can: DuckDB then reads only the matching files.

```sql
SELECT SUM(PA_QTDAPR) FROM pa WHERE competencia = 202505 AND uf = 'SP';
```

The column `_ARQUIVO_ORIGEM` records the original DATASUS file of each row
(e.g. `PASP2505a.dbc`), useful when a state is split into several parts.

## Sources

- **PA layout (2008 onward):** DATASUS, *Informe Técnico SIASUS* (Jul/2019), section 2.3,
  `ftp://ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Doc/Informe_Tecnico_SIASUS_2019_07.pdf`.
- **SIGTAP:** the layout files (`*_layout.txt`) shipped inside each
  `TabelaUnificada_YYYYMM_v*.zip` at `ftp://ftp2.datasus.gov.br/public/sistemas/tup/downloads`,
  and the online browser at [sigtap.datasus.gov.br](http://sigtap.datasus.gov.br/).
- **General portal:** [DATASUS – Transferência de arquivos](https://datasus.saude.gov.br/transferencia-de-arquivos/).

DATASUS publishes no layout document for the 1994–2007 files on its FTP; see the caveat on
the [pa_legacy](pa_legacy.md) page.
