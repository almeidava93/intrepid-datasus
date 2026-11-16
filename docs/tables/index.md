# Tables overview

Every table below is available in `datasus query` and `datasus shell`. They are DuckDB
views over the local Parquet store, so a table only exists once its data has been fetched:

| Table | Needs | Rows are | Page |
|---|---|---|---|
| `pa` | `datasus fetch` (2008 onward) | one line of outpatient production | [pa](pa.md) |
| `pa_raw` | same | same, every column as text | [pa](pa.md#pa-vs-pa_raw) |
| `pa_legacy` | `datasus fetch` (1994–2007) | one line of outpatient production, old layout | [pa_legacy](pa_legacy.md) |
| `pa_legacy_raw` | same | same, every column as text | [pa_legacy](pa_legacy.md) |
| `bi` | `datasus fetch -T bi` (2008 onward) | one patient appointment (BPA-I); also in `pa` | [bi](bi.md) |
| `bi_raw` | same | same, every column as text | [bi](bi.md#bi-vs-bi_raw) |
| `am` | `datasus fetch -T am` (2008 onward) | one APAC for high-cost medicines, per month; also in `pa` | [am](am.md), [APAC](apac.md) |
| `am_raw` | same | same, every column as text | [am](am.md#am-vs-am_raw) |
| `aq` | `datasus fetch -T aq` (2008 onward) | one chemotherapy APAC, per month; also in `pa` | [aq](aq.md), [APAC](apac.md) |
| `aq_raw` | same | same, every column as text | [aq](aq.md#aq-vs-aq_raw) |
| `ar` | `datasus fetch -T ar` (2008 onward) | one radiotherapy APAC, per month; also in `pa` | [ar](ar.md), [APAC](apac.md) |
| `ar_raw` | same | same, every column as text | [ar](ar.md#ar-vs-ar_raw) |
| `ad` | `datasus fetch -T ad` (2008 onward) | one APAC of the other (diverse) laudos, per month; also in `pa` | [ad](ad.md), [APAC](apac.md) |
| `ad_raw` | same | same, every column as text | [ad](ad.md#ad-vs-ad_raw) |
| `atd` | `datasus fetch -T atd` (Aug/2014 onward) | one dialysis APAC (patient), per month; also in `pa` | [atd](atd.md), [APAC](apac.md) |
| `atd_raw` | same | same, every column as text | [atd](atd.md#atd-vs-atd_raw) |
| `an` | `datasus fetch -T an` (Jan/2008 to Jul/2014) | one dialysis APAC (patient), per month; also in `pa` | [an](an.md), [APAC](apac.md) |
| `an_raw` | same | same, every column as text | [an](an.md#an-vs-an_raw) |
| `ab` | `datasus fetch -T ab` (Jan/2008 to Apr/2017, Jan–Jul/2025) | one bariatric follow-up APAC (patient), per month; also in `pa` | [ab](ab.md), [APAC](apac.md) |
| `ab_raw` | same | same, every column as text | [ab](ab.md#ab-vs-ab_raw) |
| `ps` | `datasus fetch -T ps` (Nov/2012 onward) | one action line of a CAPS patient's monthly RAAS; also in `pa` | [ps](ps.md), [RAAS](raas.md) |
| `ps_raw` | same | same, every column as text | [ps](ps.md#ps-vs-ps_raw) |
| `sad` | `datasus fetch -T sad` (Apr/2012 to Oct/2018) | one action line of a home-care patient's monthly RAAS; also in `pa` | [sad](sad.md), [RAAS](raas.md) |
| `sad_raw` | same | same, every column as text | [sad](sad.md#sad-vs-sad_raw) |
| `ufs` | nothing (built in) | one state | [Lookups](lookups.md#ufs) |
| `procedimentos` | `datasus sigtap fetch` | one SIGTAP procedure code | [Lookups](lookups.md#procedimentos) |
| `cid10` | `datasus sigtap fetch` | one ICD-10 code | [Lookups](lookups.md#cid10) |
| `ocupacoes` | `datasus sigtap fetch` | one CBO occupation code | [Lookups](lookups.md#ocupacoes) |
| `sigtap_<table>` | `datasus sigtap fetch` | latest row of each code / latest relationship | [SIGTAP tables](sigtap.md) |
| `sigtap_<table>_all` | `datasus sigtap fetch` | every row of every fetched version | [SIGTAP tables](sigtap.md) |

## SIA file types and their tables

DATASUS publishes several SIA/SUS file types, each named `<CODE><UF><YY><MM>[part].dbc`
(`PASP2605a.dbc`, `BIAC2605.dbc`, `BISP2605_1.dbc`, ...). Every file type you can fetch gets its own tables,
named after its code in lowercase: a typed view (`pa`) and a text-only `_raw` view
(`pa_raw`). A file type whose layout changed over time has one pair per layout; PA has two,
`pa` (2008 onward) and `pa_legacy` (1994–2007), and the CLI picks the right one by month.

| Code | `--table` | File type | Tables | Page |
|---|---|---|---|---|
| PA | `pa` (default) | Produção Ambulatorial | `pa`, `pa_raw`, `pa_legacy`, `pa_legacy_raw` | [pa](pa.md), [pa_legacy](pa_legacy.md) |
| BI | `bi` | BPA Individualizado | `bi`, `bi_raw` | [bi](bi.md) |
| AM | `am` | APAC Medicamentos | `am`, `am_raw` | [am](am.md) |
| AQ | `aq` | APAC Quimioterapia | `aq`, `aq_raw` | [aq](aq.md) |
| AR | `ar` | APAC Radioterapia | `ar`, `ar_raw` | [ar](ar.md) |
| AD | `ad` | APAC Laudos Diversos | `ad`, `ad_raw` | [ad](ad.md) |
| ATD | `atd` | APAC Tratamento Dialítico | `atd`, `atd_raw` | [atd](atd.md) |
| AN | `an` | APAC Nefrologia (2008 to Jul/2014) | `an`, `an_raw` | [an](an.md) |
| AB | `ab` | APAC Cirurgia Bariátrica (follow-up after surgery, 2008 to Apr/2017) | `ab`, `ab_raw` | [ab](ab.md) |
| PS | `ps` | RAAS Psicossocial (CAPS, Nov/2012 onward) | `ps`, `ps_raw` | [ps](ps.md) |
| SAD | `sad` | RAAS Atenção Domiciliar (home care, Apr/2012 to Oct/2018) | `sad`, `sad_raw` | [sad](sad.md) |

AM, AQ, AR, AD, ATD, AN and AB are the first of the APAC file types (authorisations for high-cost
treatments: AM, AQ, AR, AD, ATD, AN, AB, ...). What an APAC is, how its months continue and the `AP_` columns they all
share are described once, on the [APAC file types](apac.md) page. PS and SAD are the RAAS file types
(records of continuous care: CAPS, home care), described on [RAAS file types](raas.md).

Choose file types with `--table/-T` in `available`, `fetch`, `status`, `schema` and `remove`
(`-T pa`, `-T pa,bi`, `-T all`). Without it, commands work on PA. More file types are being
added one by one (issue #3 on GitHub).

To see what exists in your own store, and every column with its description:

```bash
uv run datasus status            # which states and months are stored locally (pa)
uv run datasus status -T all     # ... for every file type
uv run datasus schema            # columns of pa, with descriptions (--legacy: pa_legacy)
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

bi ── PROC_ID    ──► procedimentos (codigo)
 │ ── CIDPRI     ──► cid10 (codigo)
 │ ── CBOPROF    ──► ocupacoes (codigo)
 │ ── uf         ──► ufs (uf)
 └─── LEFT(MUNPAC, 2) ──► ufs (ibge)    patient's state of residence

am ── AP_PRIPAL  ──► procedimentos (codigo)    medicine
 │ ── AP_CIDPRI  ──► cid10 (codigo)
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(AP_MUNPCN, 2) ──► ufs (ibge)
 └─── AP_AUTORIZ ──► pa (PA_AUTORIZ, same competencia and uf)

aq ── AP_PRIPAL  ──► procedimentos (codigo)    chemotherapy procedure (purpose, line)
 │ ── AP_CIDPRI, AQ_CIDINI1..3 ──► cid10 (codigo)    cancer, previous treatments
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(AP_MUNPCN, 2) ──► ufs (ibge)
 └─── AP_AUTORIZ, AP_CMP ──► pa (PA_AUTORIZ, PA_CMP, same competencia and uf)

ar ── AP_PRIPAL  ──► procedimentos (codigo)    radiotherapy procedure (site treated)
 │ ── AP_CIDPRI, AR_CIDTR1..3, AR_CIDINI1..3 ──► cid10 (codigo)    cancer, treated areas
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(AP_MUNPCN, 2) ──► ufs (ibge)
 │ ── AP_CNSPCN  ──► aq (AP_CNSPCN)    same patient's chemotherapy
 └─── AP_AUTORIZ, AP_CMP ──► pa (PA_AUTORIZ, PA_CMP, same competencia and uf)

ad ── AP_PRIPAL  ──► procedimentos (codigo)    procedure (grupo/subgrupo say what kind)
 │ ── AP_CIDPRI  ──► cid10 (codigo)
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(AP_MUNPCN, 2) ──► ufs (ibge)
 └─── AP_AUTORIZ, AP_CMP ──► pa (PA_AUTORIZ, PA_CMP, same competencia and uf)

atd ── AP_PRIPAL ──► procedimentos (codigo)    dialysis procedure (haemodialysis, peritoneal)
 │ ── AP_CIDCAS  ──► cid10 (codigo)    the only diagnosis column filled
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(AP_MUNPCN, 2) ──► ufs (ibge)
 │ ── AP_CNSPCN  ──► an (AP_CNSPCN)    same patient before Aug/2014
 └─── AP_AUTORIZ, AP_CMP ──► pa (PA_AUTORIZ, PA_CMP, same competencia and uf)

an ── AP_PRIPAL  ──► procedimentos (codigo)    dialysis procedure
 │ ── AP_CIDPRI  ──► cid10 (codigo)
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(AP_MUNPCN, 2) ──► ufs (ibge)
 │ ── AP_CNSPCN  ──► atd (AP_CNSPCN)    same patient from Aug/2014
 └─── AP_AUTORIZ, AP_CMP ──► pa (PA_AUTORIZ, PA_CMP, same competencia and uf)

ab ── AP_PRIPAL  ──► procedimentos (codigo)    always 0301120056 (follow-up after bariatric surgery)
 │ ── AB_PROCAIH ──► procedimentos (codigo)    the surgery, until Mar/2013
 │ ── AP_CIDCAS  ──► cid10 (codigo)
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(AP_MUNPCN, 2) ──► ufs (ibge)
 └─── AP_AUTORIZ, AP_CMP ──► pa (PA_AUTORIZ, PA_CMP, same competencia and uf)

ps ── PA_PROC_ID ──► procedimentos (codigo)    CAPS action (030108...)
 │ ── CIDPRI     ──► cid10 (codigo)
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(MUNPAC, 2) ──► ufs (ibge)
 │ ── CNS_PAC    ──► ad (AP_CNSPCN)    same patient's CAPS APACs until Dec/2012
 └─── CNES_EXEC, DT_ATEND, PA_PROC_ID ──► pa (PA_CODUNI, PA_CMP, PA_PROC_ID, PA_DOCORIG = 'B'; totals only)

sad ── PA_PROC_ID ──► procedimentos (codigo)    home-care action (0301050..., 0301010137, ...)
 │ ── CIDPRI, PA_CID ──► cid10 (codigo)
 │ ── uf         ──► ufs (uf)
 │ ── LEFT(MUNPAC, 2) ──► ufs (ibge)
 └─── CNES_EXEC, DT_ATEND, PA_PROC_ID ──► pa (PA_CODUNI, PA_CMP, PA_PROC_ID, PA_DOCORIG = 'A'; totals only)
```

`bi` rows are the `pa` rows with `PA_DOCORIG = 'I'`: query one or the other, never both
summed (see [bi](bi.md#how-bi-relates-to-pa-double-counting)). Likewise `am` rows are `pa`
rows with `PA_DOCORIG = 'P'` (see [am](am.md#how-am-relates-to-pa-double-counting)), and so are
`aq` rows (see [aq](aq.md#how-aq-relates-to-pa-double-counting)) and `ar` rows (see
[ar](ar.md#how-ar-relates-to-pa-double-counting)), `ad` rows (see
[ad](ad.md#how-ad-relates-to-pa-double-counting)), `atd` rows (see
[atd](atd.md#how-atd-relates-to-pa-double-counting)), `an` rows (see
[an](an.md#how-an-relates-to-pa-double-counting)) and `ab` rows (see
[ab](ab.md#how-ab-relates-to-pa-double-counting)). `ps` rows are the `pa` rows with
`PA_DOCORIG = 'B'` (see [ps](ps.md#how-ps-relates-to-pa-double-counting)), and `sad` rows the `pa`
rows with `PA_DOCORIG = 'A'` (see [sad](sad.md#how-sad-relates-to-pa-double-counting)).

`pa_legacy` joins `ufs` the same way, but **not** the SIGTAP lookups: its procedure codes
(`PA_CODPRO`) belong to the old SIA table that SIGTAP replaced in Jan/2008.

## Partition columns

Every SIA table (`pa`, `pa_legacy`, and each file type added later) has two extra columns
that are not in the DATASUS files. They come from the folder layout
(`data/<table>/competencia=YYYYMM/uf=XX/`, e.g. `data/pa/competencia=202605/uf=SP/`):

| Column | Type | Meaning |
|---|---|---|
| `competencia` | `INTEGER` | Month of the file, `YYYYMM` (in `pa`, equals `PA_MVM`, the processing month). |
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
- **BI layout:** same Informe Técnico, section 5.2 (*Layout do arquivo de BPA-I*).
- **APAC layouts (AM, ...):** same Informe Técnico, section 3.4 (*Layout dos arquivos de APAC*;
  AD is 3.4.1, AM 3.4.2, AQ 3.4.4, AR 3.4.5, ATD 3.4.8, AN 3.4.3, AB in the same section). RAAS layouts (PS, SAD): section 4 (SAD 4.1, PS 4.2). ATD, AN and AB code lists: DATASUS *Layout da interface texto do APAC e do SIA*
  (Apr/2014), part 18 (ATD), part 09 (AN) and the bariatric parts 11 and 17 (AB; field positions of the old and new laudo).
- **SIGTAP:** the layout files (`*_layout.txt`) shipped inside each
  `TabelaUnificada_YYYYMM_v*.zip` at `ftp://ftp2.datasus.gov.br/public/sistemas/tup/downloads`,
  and the online browser at [sigtap.datasus.gov.br](http://sigtap.datasus.gov.br/).
- **General portal:** [DATASUS – Transferência de arquivos](https://datasus.saude.gov.br/transferencia-de-arquivos/).

DATASUS publishes no layout document for the 1994–2007 files on its FTP; see the caveat on
the [pa_legacy](pa_legacy.md) page.
