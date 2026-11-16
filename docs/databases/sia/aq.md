# aq — APAC Quimioterapia (chemotherapy), 2008 onward

**Source:** `AQufaamm.dbc` files in `ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados`
(e.g. `AQAC2605.dbc`). No state is split into parts.
**Coverage:** Jan/2008 to the latest month DATASUS has released (Aug/2026 when this was
written), all 27 states. Some states miss months: RR has 194 of the 224 months, AP 216,
AC 222, PI and RO 223; the other 22 states are complete.
**Size on the FTP** (Nov/2026): 6,006 files, about **5.1 GB** of `.dbc`, growing every year
(136 MB for 2008, 419 MB for 2025). The largest file, `AQSP2507.dbc`, is 10.5 MB with
101,669 rows. Parquet takes about 0.45× the `.dbc` size.
**Fetch:** `uv run datasus fetch -T aq -s SC -f 2024`.

Each row is **one APAC for cancer drug treatment billed in one month**: chemotherapy,
hormone therapy, targeted therapy and the related special procedures delivered by a
licensed oncology facility (CACON/UNACON). Besides the shared APAC fields (patient,
validity, exit reason) the row carries the *laudo de quimioterapia*: the cancer (ICD-10),
stage, lymph node invasion, histological grade, date of the pathology diagnosis, previous
treatments, the start date and planned length of the treatment, the scheme (drug names)
and, from 2022, the drug codes.

Read [APAC file types](apac.md) first: it explains authorisation, validity, monthly
continuation and the patient identifier, and describes the 46 `AP_` columns shared with
the other APAC tables. Radiotherapy is a separate file type (AR), not in this table.

!!! warning "Rows are APAC-months, not patients or treatments"
    An AQ APAC is valid for three months and appears in each monthly file, and a treatment
    that goes on gets a **new APAC every three months**. SC, 2024–2025: 471,969 rows,
    176,924 APACs, 43,607 patients. Count `DISTINCT AP_CNSPCN` for patients (after removing
    the empty ones, see [following a patient](#following-a-patient)), `DISTINCT AP_AUTORIZ`
    for authorisations. There is **no quantity column**; the doses given are not in the data.

## How aq relates to pa (double counting)

**Every `aq` row is one `pa` row with `PA_DOCORIG = 'P'`** (the APAC's main procedure), and
these are exactly the `P` rows whose procedure is in SIGTAP `0304020000`–`0304089999`
(chemotherapy forms 02 to 08 of subgroup *Tratamento em oncologia*; `030401` is radiotherapy,
in AR). Secondary procedures of the same APAC (granulocyte colony-stimulating factor
`0304080012`, osteolysis inhibitor `0304080071`, intrathecal chemotherapy `0304080055`) are
in `pa` only, as `PA_DOCORIG = 'S'` rows with the same `PA_AUTORIZ`.

Join on **both** `AP_AUTORIZ = PA_AUTORIZ` and `AP_CMP = PA_CMP`. A monthly file holds the
same APAC twice when last month's billing arrives late: in AC, May/2026, 501 rows but 468
APAC numbers; `(AP_AUTORIZ, AP_CMP)` is unique.

Checked on AC and SC, May/2026:

| | AC | SC |
|---|---|---|
| `aq` rows | 501 | 22,109 |
| `pa` `P` rows with procedure `030402`–`030408` | 501 | 22,105 |
| `aq` rows with exactly one `P` row (same procedure) | 501 | 22,105 |
| `aq` rows where `AP_VL_AP` = `SUM(PA_VALAPR)` over the `P` and `S` rows | 501 | 22,105 |
| `SUM(AP_VL_AP)` | R$ 773,254.67 | R$ 12,607,431.72 |

The 4 SC rows missing from `pa` are late billings of March and April with `AP_VL_AP = 0`.
`PA_TPFIN` does not single AQ out: its rows are `06` (MAC) or `04` (FAEC).

| You want | Use |
|---|---|
| All outpatient production, including chemotherapy | `pa` only |
| Chemotherapy spending by procedure | `pa WHERE PA_PROC_ID BETWEEN '0304020000' AND '0304089999'` (or `aq.AP_VL_AP`, which includes the secondary procedures) |
| Patients, cancer site, stage, purpose, scheme, treatment dates | `aq` |
| Both | join `aq` to `pa` on `AP_AUTORIZ` = `PA_AUTORIZ` and `AP_CMP` = `PA_CMP` |

!!! danger "Never add `aq` to `pa`"
    `aq`'s value and APACs are already in `pa`. `AP_VL_AP` is the value of the whole APAC
    (main plus secondary procedures): summing it with `pa`'s `S` rows counts them twice.

## aq vs aq_raw

`aq_raw` holds every column as text exactly as DATASUS publishes it. `aq` is the same data
with `AP_VL_AP` cast to `DOUBLE` (with `TRY_CAST`). Everything else stays text, including
codes with leading zeros (`AP_PRIPAL = '0304050121'`, `AQ_TOTMPL = '060'`, `AQ_MED01 = '011'`)
and dates (`AQ_DTINTR = '20251020'`).

## Columns

The `AP_` columns are described on the [APAC page](apac.md#shared-columns). The *Official
description* column translates the DATASUS *Informe Técnico SIASUS* (Jul/2019), section
3.4.4, *Layout do arquivo de APAC de quimioterapia: AQUFAAMM.DBF*. Values in *Notes* were
checked on SC (2008–2026), AC and RJ (2025–2026) and SP (Jul/2025).

### Shared APAC columns: what they hold in AQ

| Column | Notes for AQ |
|---|---|
| `AP_PRIPAL` | The chemotherapy procedure, SIGTAP `030402`–`030408`. Its 6-digit prefix is the **purpose of the treatment** (table below); the name gives the tumour and often the stage or the **line** (*1ª linha*, *2ª linha*: 77 of the 163 codes). Join `procedimentos.codigo`; all but 16 of 51,929 rows joined the Nov/2026 SIGTAP. |
| `AP_CIDPRI` | **The cancer**, ICD-10, always filled: `C` codes (96%) or `D` (in-situ and uncertain behaviour, e.g. `D471`). Most frequent in SC: C504, C61, C500, C509, C501. Every code joined `cid10`. |
| `AP_CIDSEC` | `0000` on about 5 of 6 rows; when filled, mostly the same code as `AP_CIDPRI` (sometimes a metastasis, `C795` bone). |
| `AP_CIDCAS` | Almost always `0000`. |
| `AP_TPATEN` | Always `03`. |
| `AP_TPAPAC` | `1` in the first month of each APAC, `2` in its 2nd and 3rd month; `4` (345 of 1.7 M rows) and `3` are rare. A treatment that goes on gets a new APAC every three months, starting at `1` again: **`1` does not mean a new patient or treatment.** |
| `AP_DTINIC`, `AP_DTFIM` | Three-month validity (an APAC from 04/Mar ends on 31/May). |
| `AP_VL_AP` | Value of the APAC in the month, = main + secondary procedures in `pa`. 0 on about 1 row in 10 (SC: 10%; SP: 9%). |
| `AP_MOTSAI` | `21` (continues) on 97% of rows; also `18`, `12`, `15` (discharge), `26` (continues with a change of procedure), `41`/`42` (death), `51` (administrative closure), `31` (transfer). The flags `AP_OBITO`, `AP_ALTA`, `AP_TRANSF`, `AP_ENCERR`, `AP_PERMAN` agree with it. |
| `AP_CATEND` | `01` (elective); `02` (urgent) on 0.3%. |
| `AP_TPUPS` | `05` general hospital or `07` specialised hospital. |
| `AP_UNISOL` | Always the executing facility (`AP_UNISOL` = `AP_CODUNI`). |
| `AP_CODEMI` | `E…` (state secretariat), `M…` (municipal secretariat, e.g. `M420910001`), also `S…`/`U…`. |
| `AP_MNDIF` | **Always `1`** (wrong, as in AM); compare `AP_MUNPCN` with `AP_UFMUN`. `AP_UFDIF` is correct. |
| `AP_APACANT` | Zeros on 98% of rows. Successive APACs of one treatment are **not** chained by it. |
| `AP_CNSPCN` | Encoded, but **empty or `{{{{{{{{{{{{{{{` on a growing share of rows** from 2024: see [following a patient](#following-a-patient). |
| `AP_NATJUR` | From Jul/2016 (`NULL` before). |

#### Purpose of the treatment: the procedure's form (`SUBSTR(AP_PRIPAL, 1, 6)`)

| Prefix | SIGTAP *forma de organização* | Meaning | SC, May/2026 rows |
|---|---|---|---|
| `030402` | Quimioterapia paliativa - adulto | Palliative (advanced/metastatic disease); most "1ª/2ª linha" codes | 6,655 |
| `030403` | Quimioterapia para controle temporário de doença - adulto | Temporary disease control (leukaemias, myeloma, lymphomas, ...) | 2,170 |
| `030404` | Quimioterapia prévia (neoadjuvante/citorredutora) - adulto | Before surgery or radiotherapy | 1,673 |
| `030405` | Quimioterapia adjuvante (profilática) - adulto | After surgery, to prevent recurrence; includes years of hormone therapy for breast cancer | 10,767 |
| `030406` | Quimioterapia curativa - adulto | Curative intent (e.g. Hodgkin, germ cell tumours) | 531 |
| `030407` | Quimioterapia de tumores de criança e adolescente | Children and adolescents | 232 |
| `030408` | Quimioterapia - procedimentos especiais | Special procedures as the main one | 81 |

The **line** of treatment has no column of its own: it is in the procedure name
(`QUIMIOTERAPIA DO ADENOCARCINOMA DE COLON AVANÇADO -1ª LINHA`, `... - 2ª LINHA`), so filter
`procedimentos.nome LIKE '%2ª LINHA%'` (or `SEGUNDA LINHA`) after joining.

### Columns specific to AQ

| Column | Type | Size | Official description | Notes |
|---|---|---|---|---|
| `AQ_CID10` | text | 4 | ICD-10 — topography. | Equals `AP_CIDPRI` whenever filled. Filled on most rows until Feb/2022, then on only about 1 row in 6. **Use `AP_CIDPRI`.** |
| `AQ_LINFIN` | text | 1 | Regional lymph nodes invaded (`S` yes, `N` no, `3` not assessable). | SC, May/2026: `S` 78%, `3` 12%, `N` 10%. |
| `AQ_ESTADI` | text | 1 | Stage — UICC (`0`, `1`, `2`, `3`, `4`). | Empty on about 1 row in 8 (haematological cancers, mostly). SC: `4` 35%, `3` 22%, `2` 17%, `1` 13%. Recorded at the APAC request: the stage of the treatment's laudo, not updated each month. |
| `AQ_GRAHIS` | text | 2 | Histopathological grade. | Loosely coded: `1`–`4`, `0`, `9`, `10`–`12`, `G1`–`G4`, `GX`, `X`, `-`, ... Not usable as a clean code without cleaning. |
| `AQ_DTIDEN` | text | 8 | Date of the pathological identification of the case (`AAAAMMDD`). | The diagnosis date. Can change between APACs of the same patient (11% of SC patients over two years). |
| `AQ_TRANTE` | text | 1 | Previous treatments (`S` yes, `N` no). | `0` (not informed) on most rows since 2013 (72% in 2026). |
| `AQ_CIDINI1` | text | 4 | ICD-10 of the 1st previous treatment. | Empty when none. Joins `cid10`. |
| `AQ_DTINI1` | text | 8 | Start date of the 1st previous treatment (`AAAAMMDD`). | Empty or zeros when none. |
| `AQ_CIDINI2`, `AQ_DTINI2` | text | 4, 8 | ICD-10 and start date of the 2nd previous treatment. | |
| `AQ_CIDINI3`, `AQ_DTINI3` | text | 4, 8 | ICD-10 and start date of the 3rd previous treatment. | |
| `AQ_CONTTR` | text | 1 | Continuity of treatment (`S` yes, `N` no). | Not reliable as a "new treatment" flag: some facilities send `N` on every renewal (SC, 2025: 2,347 breast cancer patients had four `N` APACs in the year). |
| `AQ_DTINTR` | text | 8 | Start date of the requested treatment (`AAAAMMDD`). | Usually kept across the successive APACs of one treatment (the example below keeps `20230404` for two years), and a new date marks a new treatment. Some facilities change it at every renewal; 345 SC rows are not valid dates (`40260215`). |
| `AQ_ESQU_P1` | text | 5 | Scheme (abbreviation), first 5 positions. | Free text, any case: `ANAST`, `tamox`, `FOLFO`, `TMX`, `HT`, ... |
| `AQ_TOTMPL` | text | 3 | Total months planned. | `006`, `012`, `060` (5 years of hormone therapy), ... |
| `AQ_TOTMAU` | text | 3 | Total months authorised. | Months authorised so far for the treatment: grows by 3 with each new APAC (`009`, `012`, `015`, ...); `000` on many rows. |
| `AQ_ESQU_P2` | text | 10 | Scheme (abbreviation), last 10 positions. | Continues `AQ_ESQU_P1`: `AQ_ESQU_P1 \|\| AQ_ESQU_P2` gives `ANASTROZOL`, `TAMOXIFENO`, `FOLFOX`, ... |
| `AQ_MED01` … `AQ_MED10` | text | 3 each | *Not in the 2019 Informe.* | Codes of the antineoplastic drugs of the scheme, from SIA's oncology drug list. The columns exist from Jan/2021 but are empty until Feb/2022; from Mar/2022 `AQ_MED01` is always filled, `AQ_MED02` on 1 row in 4, `AQ_MED05` rarely. The package has no table for these codes; from `AQ_ESQU`, the most frequent are `011` anastrozole, `037` tamoxifen, `003`/`004` goserelin/leuprorelin, `090` hydroxyurea, `165` triptorelin, `105` imatinib, `028` capecitabine, `097` letrozole, `145` trastuzumab, `077` exemestane, `085` gemcitabine. |

### Added by this package

| Column | Type | Meaning |
|---|---|---|
| `_ARQUIVO_ORIGEM` | text | DATASUS file the row came from (`AQSP2605.dbc`). |
| `competencia` | `INTEGER` | Partition: month of the file (`YYYYMM`); equals `AP_MVM`. |
| `uf` | text | Partition: state of the file (the treating facility's state). |

## Following a patient

`AP_CNSPCN` (encoded CNS) is the same value for the same patient across months, APACs,
facilities and APAC types, so you can build a patient's treatment history. In SC, 2024–2025,
the 43,607 patients had on average 4.1 APACs over 10.7 months; 97% of the gaps between two
months of treatment were one month. A typical adjuvant breast cancer patient looks like this:

| `AP_CMP` | `AP_AUTORIZ` | `AP_TPAPAC` | `AP_PRIPAL` | `AQ_DTINTR` | `AQ_ESTADI` | `AQ_TOTMPL` / `AQ_TOTMAU` |
|---|---|---|---|---|---|---|
| 202401 | …0658120 | 1 | 0304050121 (adjuvant hormone therapy, stage II) | 20230404 | 2 | 060 / 009 |
| 202402, 202403 | …0658120 | 2 | same | same | 2 | 060 / 009 |
| 202404 | …1406020 | 1 | same | same | 2 | 060 / 012 |
| … every 3 months a new APAC … | | | | | | |
| 202510 | …1868935 | 1 | same | same | 2 | 060 / 030 |
| 202511 | …1699711 | 1 | 0304020133 (palliative) | **20251105** | **4** | 012 / 000 |

The palliative APAC in Nov/2025 (new procedure form, new treatment start date, stage 4)
marks progression to metastatic disease; for a month both APACs are billed.

**How to do it:**

- Order a patient's rows by `AP_CMP` (the month of care), not `competencia`: late billings
  put an earlier month in a later file. Deduplicate on `(AP_AUTORIZ, AP_CMP)` if you read
  rows from overlapping files.
- A **treatment** is best identified by (`AP_CNSPCN`, `AQ_DTINTR`), or by a run of APACs with
  the same procedure form; **purpose changes** show up as a new `AP_PRIPAL` prefix. SC
  breast cancer, 2024–2025: 1,088 patients went from neoadjuvant (`030404`) to adjuvant
  (`030405`), 459 from adjuvant to palliative (`030402`), 170 from neoadjuvant to palliative.
- **Exit:** `AP_MOTSAI` `41`–`43` (death) is final: only 9 of 1,306 such rows were followed
  by a later APAC of the same patient. Discharge and closure codes are not: after `12`, `15`,
  `18` or `51`, 68–79% of the rows were followed by another APAC of the patient within the
  period, and 95% after `26` (change of procedure).
  Deaths outside treatment are not recorded here; this is not a survival dataset.

**Caveats:**

- **Missing patient IDs.** `AP_CNSPCN` is empty (`NULL`) or the placeholder
  `{{{{{{{{{{{{{{{` (the code of a blank CNS) on a share of rows that grows from 2024. SC:
  about 1% or less until 2025, 14% in May/2026, 22% in Jul/2026. RJ: 8–17% in 2025, 34% in
  Aug/2026. SP, Jul/2025: 15%. AC: none in 2025, a third in Jan/2026, over 90% from Apr/2026. These rows cannot be followed
  (and the placeholder would merge them all into one "patient"): always add
  `AP_CNSPCN IS NOT NULL AND AP_CNSPCN <> '{{{{{{{{{{{{{{{'`, and check the share for your
  states and months before counting patients. AM has no such gap (AC, May/2026: none empty).
- **Censoring.** Patients seen in the first months of your window may have started earlier,
  and those in the last months may continue: to find *new* patients, fetch at least a year
  before the period you count, and treat the last months as incomplete (late billing adds
  rows for up to a few months).
- **Several states.** A patient treated in another state appears in that state's file: fetch
  every state the patient could have used (`AP_UFDIF = '1'` on about 1% of SC rows).
- **Concurrent APACs.** 1.4% of patient-months have two or more APACs (two drugs, e.g. hormone
  therapy plus trastuzumab, or the overlap month of a change of treatment). Count patients,
  not rows.
- **Inconsistent laudo fields.** Over two years, 10% of SC patients changed `AP_CIDPRI`
  (2.2% at the 3-character level, e.g. C50 to C79), 6.7% `AQ_ESTADI`, 11% `AQ_DTIDEN` and 36%
  had more than one `AQ_DTINTR`; 0.1% changed sex. Take the first value of a treatment
  (`arg_min(..., AP_CMP)`) and say so.
- A handful of APAC numbers (39 in SC, 2024–2025) carry two different `AP_CNSPCN`.
- Doses and cycles are not in the data; only that the APAC was billed in the month.

## Joins

- `AP_PRIPAL` → `procedimentos.codigo` (procedure name, purpose, line, SIGTAP price).
- `AP_CIDPRI`, `AP_CIDSEC`, `AQ_CID10`, `AQ_CIDINI1`–`3` → `cid10.codigo`.
- `uf` → `ufs.uf`; `LEFT(AP_MUNPCN, 2)` → `ufs.ibge` (patient's state of residence).
- `AP_AUTORIZ`, `AP_CMP` → `pa.PA_AUTORIZ`, `pa.PA_CMP` (same `competencia` and `uf`) for the
  secondary procedures and their values.
- No professional (CBO) column, so no join to `ocupacoes`. `AQ_MED01`–`10` have no lookup table.

## Known quirks and layout changes

- **One layout since 2008, three column sets.** 63 columns until Jun/2016; `AP_NATJUR` added
  from Jul/2016 (64); `AQ_MED01`–`AQ_MED10` added from Jan/2021 (74; empty until Feb/2022).
  The view reads all months together and shows `NULL` for columns a month lacks. Checked on
  one SP file per year 2008–2026 and the change months in SP, RJ and MG.
- In Mar/2022 `AQ_MED01`–`10` start to be filled and `AQ_CID10` mostly stops: probably a new
  version of the laudo form. Use `AP_CIDPRI` for the cancer in every period.
- `AP_VL_AP` is a numeric (`N`) field in the DBF; the converter reads it as text and the typed
  view casts it.
- `AP_MNDIF` is always `1` (wrong). `AQ_TRANTE` is mostly `0`, `AQ_GRAHIS` is loosely coded and
  `AQ_CONTTR` is unreliable (see above).
- **Conversion size.** `AQSP2507.dbc` (10.5 MB, 101,669 rows, the largest file): 7 s to download
  and convert, peak about 0.4 GB of RAM, 4.6 MB of Parquet (0.44×). The temporary DBF is
  357 bytes per row (about 36 MB here).

## Examples

```sql
-- Patients in treatment by cancer, in a month (excluding rows without a patient ID)
SELECT c.nome AS cancer, COUNT(DISTINCT AP_CNSPCN) AS pacientes, COUNT(*) AS apac_meses
FROM aq JOIN cid10 c ON c.codigo = aq.AP_CIDPRI
WHERE competencia = 202505 AND uf = 'SC'
  AND AP_CNSPCN IS NOT NULL AND AP_CNSPCN <> '{{{{{{{{{{{{{{{'
GROUP BY 1 ORDER BY pacientes DESC LIMIT 10;

-- APACs and value by purpose of the treatment
SELECT CASE SUBSTR(AP_PRIPAL, 1, 6)
         WHEN '030402' THEN 'paliativa' WHEN '030403' THEN 'controle temporário'
         WHEN '030404' THEN 'prévia (neoadjuvante)' WHEN '030405' THEN 'adjuvante'
         WHEN '030406' THEN 'curativa' WHEN '030407' THEN 'criança/adolescente'
         ELSE 'procedimento especial' END AS finalidade,
       COUNT(DISTINCT AP_AUTORIZ) AS apacs, ROUND(SUM(AP_VL_AP)) AS valor
FROM aq WHERE uf = 'SC' AND competencia = 202605
GROUP BY 1 ORDER BY valor DESC;

-- Stage at first treatment of breast cancer patients first seen in 2025
-- (2024 fetched too, so that patients already in treatment are excluded)
WITH p AS (
  SELECT AP_CNSPCN, MIN(AP_CMP) AS primeiro_mes, arg_min(AQ_ESTADI, AP_CMP) AS estadio
  FROM aq
  WHERE uf = 'SC' AND competencia BETWEEN 202401 AND 202512
    AND AP_CIDPRI LIKE 'C50%'
    AND AP_CNSPCN IS NOT NULL AND AP_CNSPCN <> '{{{{{{{{{{{{{{{'
  GROUP BY 1)
SELECT estadio, COUNT(*) AS pacientes, ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS pct
FROM p WHERE primeiro_mes >= '202501'
GROUP BY 1 ORDER BY 1;

-- Changes of purpose (e.g. neoadjuvant -> adjuvant, adjuvant -> palliative) per patient
WITH m AS (
  SELECT DISTINCT AP_CNSPCN, AP_CMP, AP_AUTORIZ, SUBSTR(AP_PRIPAL, 1, 6) AS finalidade
  FROM aq
  WHERE uf = 'SC' AND competencia BETWEEN 202401 AND 202512 AND AP_CIDPRI LIKE 'C50%'
    AND AP_CNSPCN IS NOT NULL AND AP_CNSPCN <> '{{{{{{{{{{{{{{{'),
t AS (
  SELECT AP_CNSPCN, finalidade,
         LAG(finalidade) OVER (PARTITION BY AP_CNSPCN ORDER BY AP_CMP, AP_AUTORIZ) AS anterior
  FROM m)
SELECT anterior, finalidade, COUNT(DISTINCT AP_CNSPCN) AS pacientes
FROM t WHERE anterior <> finalidade
GROUP BY ALL ORDER BY pacientes DESC;
```
