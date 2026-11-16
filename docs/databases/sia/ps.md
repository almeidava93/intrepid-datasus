# ps — RAAS Psicossocial (CAPS psychosocial care), Nov/2012 onward

**Source:** `PSufaamm.dbc` files in `ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados`
(e.g. `PSSP2605.dbc`). No split files.
**Coverage:** Nov/2012 (first files: 6 states, ~1,000 rows) to the latest month DATASUS has
released. 24 states from Jan/2013, all 27 for the first time in May/2013; a state with no RAAS that month
has no file (AC has 159 of the 166 months, AP 150).
**Size on the FTP** (Nov/2026): 4,421 files, **3.3 GB** of `.dbc`, 171.4 M rows. Parquet
takes 2.05 GB (0.62× the `.dbc`). The largest file is `PSSP2508.dbc` (10.7 MB, ~400 k rows).
**Fetch:** `uv run datasus fetch -T ps -s AC -f 2026`.

PS holds the care delivered by **CAPS** (*Centros de Atenção Psicossocial*: 99.3% of rows
come from facilities of CNES type `70`), recorded on the RAAS (*Registro das Ações
Ambulatoriais de Saúde*) for psychosocial care. Read [RAAS file types](raas.md) first: it
explains what a RAAS is (one care episode per patient and facility, re-recorded every month
with that month's actions) and describes the columns PS shares with SAD (home care).

## What is in PS

Every row is one action line of a CAPS patient's monthly RAAS: one SIGTAP procedure of
subgroup `030108` (*atendimento/acompanhamento psicossocial*), with its quantity. Whole
history, Nov/2012–Aug/2026:

| Procedure | SIGTAP name (short) | Rows | % rows | Approved qty |
|---|---|---|---|---|
| `0301080208` | Individual care in a CAPS | 73.7 M | 43.0% | 83.3 M |
| `0301080216` | Group care in a CAPS | 30.7 M | 17.9% | 39.0 M |
| `0301080194` | Day-time stay (*acolhimento diurno*) | 20.3 M | 11.8% | 26.0 M |
| `0301080224` | Family care | 13.4 M | 7.8% | 14.5 M |
| `0301080283` | Expressive and communicative practices | 9.8 M | 5.7% | 11.9 M |
| `0301080348` | Psychosocial rehabilitation | 5.6 M | 3.3% | 6.4 M |
| `0301080275` | Body practices | 5.1 M | 3.0% | 7.1 M |
| `0301080291` | Crisis care | 3.6 M | 2.1% | 4.3 M |
| `0301080240` | Home care for CAPS patients and families | 3.0 M | 1.7% | 3.4 M |
| `0301080356` | Promoting contractuality in the community | 2.7 M | 1.6% | 3.2 M |
| `0301080020` | Night stay (*acolhimento noturno*) | 2.2 M | 1.3% | 2.9 M |
| `0301080046` | Follow-up in a therapeutic residence | 0.8 M | 0.4% | 0.8 M |
| `0301080038` | Third-shift stay | 0.6 M | 0.3% | 0.9 M |
| 10 others | (residential care for adults/children, a few BPA codes billed by mistake) | 26 k | 0.0% | |

The diagnosis (`CIDPRI`) is almost always ICD-10 chapter F: `F99`, `F20`/`F200`
(schizophrenia), `F102`/`F192` (alcohol / multiple-drug dependence), `F29`, `F32`, `F31`.

### Growth

| Year | Rows | Patient-months (RAAS) | Distinct patients | Approved actions | Facilities | Rows per RAAS |
|---|---|---|---|---|---|---|
| 2013 | 6.7 M | 1.74 M | 491 k | 8.8 M | 1,754 | 3.84 |
| 2015 | 9.1 M | 2.34 M | 637 k | 11.9 M | 2,061 | 3.89 |
| 2017 | 10.7 M | 2.82 M | 833 k | 13.5 M | 2,387 | 3.80 |
| 2019 | 14.3 M | 3.84 M | 1.13 M | 17.0 M | 2,522 | 3.72 |
| 2020 | 10.1 M | 3.40 M | 1.07 M | 11.9 M | 2,568 | 2.96 |
| 2021 | 11.8 M | 3.97 M | 1.26 M | 13.5 M | 2,642 | 2.96 |
| 2023 | 16.4 M | 4.96 M | 1.54 M | 18.7 M | 2,726 | 3.32 |
| 2025 | 19.5 M | 5.72 M | 1.77 M | 21.8 M | 2,884 | 3.42 |

The number of CAPS and of patients grew every year except 2020 (pandemic: fewer group
actions per patient, so fewer rows per RAAS).

## One row is one action line, not a patient

A RAAS is one **episode-month**: facility (`CNES_EXEC`), patient (`CNS_PAC`), start of the
episode (`DT_INICIO`) and month of care (`DT_ATEND`). Each has 3–4 rows, one per action
line; the episode's fields (patient, diagnosis, origin, drugs, ...) are repeated on each.
**Exactly one row of every episode-month** has `QTDATE = '1'` and `QTDPCN = '1'`; on that
row, and only on it, `INICIO` and `FIM` are the first and last days in care in that month
(`YYYYMMDD`) and `PERMANEN` is the number of days (`FIM - INICIO + 1`). The other rows have
`'0'` and `NULL`s. Checked on every row of Jun/2013, Jun/2019 and Jun/2026 (143 k, 310 k
and 470 k episode-months).

| You want | Use |
|---|---|
| Patients in care in a month (RAAS) | `SUM(QTDPCN::INT)`, or `COUNT(*) WHERE QTDPCN = '1'` |
| Distinct patients over a period | `COUNT(DISTINCT CNS_PAC)` (excluding `'{{{{{{{{{{{{{{{'`, see [patients](#patients)) |
| Actions (procedures) | `SUM(PA_QTDAPR)`, not `COUNT(*)` |
| Days in care | `SUM(PERMANEN::INT) WHERE QTDPCN = '1'` |

`PA_QTDAPR` is `0` on 5–11% of rows (actions rejected in processing); `PA_QTDPRO` is what
the facility submitted.

## How ps relates to pa (double counting)

**Every row of `ps` is also in `pa`**: the rows with `PA_DOCORIG = 'B'` (RAAS Psicossocial),
with **no value** (`PA_VALAPR = 0`: CAPS are paid by a fixed monthly incentive, not per
procedure). There is no RAAS number in `pa`, so compare by facility, care month and
procedure: `CNES_EXEC = PA_CODUNI`, `DT_ATEND = PA_CMP`, `PA_PROC_ID`, within the same
`competencia` and `uf`.

| State-month | `ps` rows | `pa` `B` rows | `ps` `SUM(PA_QTDAPR)` | `pa` `B` | Keys equal |
|---|---|---|---|---|---|
| SE 2013-06 | 8,257 | 8,257 | 7,757 | 7,757 | 142 of 142 |
| AC 2014-10 | 505 | 505 | 538 | 538 | 11 of 11 |
| AC 2019-05 | 1,868 | 1,868 | 2,680 | 2,680 | 28 of 28 |
| AC 2026-05 | 1,802 | 1,802 | 1,945 | 1,945 | 27 of 27 |
| SE 2026-05 | 27,748 | 27,748 | 25,952 | 25,952 | 211 of 211 |

Rows, `PA_QTDPRO` and `PA_QTDAPR` are equal for every (facility, care month, procedure) key.
`PA_DOCORIG = 'B'` selects PS exactly; no other `pa` column is needed.

| You want | Use |
|---|---|
| All outpatient production, including CAPS | `pa` only |
| CAPS RAAS actions | `ps`, or `pa WHERE PA_DOCORIG = 'B'` |
| Patients, diagnosis, drugs, street situation, days in care | `ps` |

!!! danger "Never add `ps` to `pa`"
    Summing quantities over `pa` and `ps` counts every RAAS action twice. Values are not
    affected (RAAS rows are R$ 0 in `pa`), but procedure counts are.

**Not all CAPS work is in PS.** CAPS also report some actions on BPA, which are `pa` rows
with `PA_DOCORIG = 'C'` or `'I'` and are not in `ps`: initial reception (`0301080232`,
BPA-I), matrix support for primary care teams (`0301080305`), harm reduction (`0301080313`),
intersectoral network actions (`0301080259`), group psychotherapy, and consultations
(`030101`, `030110`). In SE May/2026, CAPS (`PA_TPUPS = '70'`) had 27,748 `B` rows, 928 `C`
rows (7,358 procedures) and 616 `I` rows. For a full picture of CAPS production, query
`pa WHERE PA_TPUPS = '70'`; for patients, `ps`.

## From AD to PS (2013)

Until Dec/2012, CAPS care was billed on **APAC**, in [AD](ad.md) (APAC Laudos Diversos):
monthly follow-up codes by intensity (`0301080054`…`0301080135`: intensive, semi-intensive
and non-intensive, for mental disorders, alcohol/drugs, children), one APAC per patient per
month (`AP_TPUPS = '70'`). From Jan/2013 it is recorded on the RAAS, in PS, with different
codes (one per kind of action: individual, group, family, day-time stay, ...). The intensity
codes were retired.

| Month | AD CAPS (`030108`) rows | AD patients | AD facilities | PS patient-months | PS patients | PS facilities | States in PS |
|---|---|---|---|---|---|---|---|
| 2012-06 | 266,904 | 246,359 | 1,564 | | | | |
| 2012-11 | 245,060 | 229,543 | 1,450 | 862 | 932 | 43 | 6 |
| 2012-12 | 219,386 | 204,692 | 1,343 | 1,201 | 1,126 | 57 | 7 |
| 2013-01 | 61 | 61 | 6 | 91,725 | 91,101 | 930 | 24 |
| 2013-03 | – | – | – | 130,478 | 122,272 | 1,231 | 26 |
| 2013-06 | – | – | – | 143,024 | 136,112 | 1,279 | 26 |
| 2013-10 | – | – | – | 169,640 | 163,795 | 1,430 | 26 |
| 2014-10 | – | – | – | 192,753 | 186,492 | 1,611 | 26 |
| 2017-12 | – | – | – | 234,964 | 223,501 | 2,017 | 27 |
| 2018-12 | – | – | – | 271,703 | 260,620 | 2,197 | 27 |

What this means for a continuous series:

- **The switch was abrupt in AD and slow in PS.** AD's CAPS APACs stop in Jan/2013 (67 late
  rows in Jan–Feb/2013); PS reached AD's 2012 level of ~205–250 k patients a month only in
  2017–2018. In Jan/2013 AC, AP and DF had no PS file (AC started in May/2013), and the
  CAPS that did report recorded fewer patients (930 facilities, against 1,343 in AD). The drop from 205 k
  (AD, Dec/2012) to 92 k (PS, Jan/2013) is under-reporting in the new system, not less
  care: CAPS are paid by a fixed incentive, so a missed RAAS costs them nothing.
- **Same patient identifier.** AD's `AP_CNSPCN` and PS's `CNS_PAC` use the same encoding:
  of the 288 k patients in AD CAPS APACs in Oct–Dec/2012, 155 k (54%) are in PS in 2013,
  185 k (64%) by 2016. 1,178 of the 1,343 facilities billing CAPS APACs in Dec/2012 report
  PS by Jun/2013.
- **Comparable unit: patient-months.** One AD CAPS APAC row ≈ one patient-month (1.07 rows
  per patient in Dec/2012); in PS use `SUM(QTDPCN::INT)`. Don't compare AD rows with PS rows
  (one PS patient-month has 3–4 rows), nor procedure codes (the 2012 and 2013 code sets
  don't overlap).

```sql
-- CAPS patients per month across the 2012/2013 change (needs ad and ps fetched)
SELECT competencia, COUNT(DISTINCT AP_CNSPCN) AS pacientes, 'AD (APAC)' AS fonte
FROM ad WHERE AP_PRIPAL LIKE '030108%' AND competencia BETWEEN 201201 AND 201212
GROUP BY 1
UNION ALL
SELECT competencia, SUM(QTDPCN::INT), 'PS (RAAS)'
FROM ps WHERE competencia BETWEEN 201301 AND 201412
GROUP BY 1
ORDER BY 1;
```

## Patients

`CNS_PAC` is the encoded CNS, the same encoding as the APAC types. It is never `NULL`; a
missing CNS shows as `'{{{{{{{{{{{{{{{'` (the encoded blank). That placeholder is rare
until 2024 and grows since, much less than in the APAC types:

| Months | Rows without CNS |
|---|---|
| Nov/2012 – Mar/2024 | 0.00% |
| Apr/2024 – Dec/2024 | 0.05–0.6% |
| 2025 | 0.5% (Jan) → 3.1% (Dec) |
| 2026 | 3.4% (Jan), 5.4% (Apr), 2.0% (Jun), 5.1% (Aug) |

By state in Aug/2026: MA 31%, PB 28%, PA 19%, AM 11%, CE 8%, RJ 7%, MG 7%; under 2% in SP,
RS, SC, DF, ES, MS. Exclude the placeholder when counting distinct patients
(`CNS_PAC <> '{{{{{{{{{{{{{{{'`); `SUM(QTDPCN::INT)` counts those RAAS anyway.

## ps vs ps_raw

`ps_raw` holds every column as text exactly as DATASUS publishes it. `ps` is the same data
with `PA_QTDPRO`/`PA_QTDAPR` cast to `BIGINT` (with `TRY_CAST`). Everything else stays text,
including `QTDATE`, `QTDPCN` and `PERMANEN` (cast them: `QTDPCN::INT`) and dates.

## Columns

The shared RAAS columns are described on [RAAS file types](raas.md#shared-columns); `datasus
schema -T ps` lists them all with descriptions. Values below are from the whole history
(171.4 M rows).

### What the columns hold

| Column | In PS |
|---|---|
| `CNES_EXEC` | 3,122 facilities; ~2,900 report in 2026. |
| `TPUPS` | `70` CAPS 99.3%, `36` specialised clinic 0.5%, `07` specialised hospital 0.1%. |
| `CONDIC` | `PG` 93%, `EP` 4%, `MN` 3%. |
| `MN_IND` | `M` 99%, `U` 1% (not the `I` of the layout). |
| `DT_ATEND` | Differs from `DT_PROCESS` on 7.5% of rows (late reports: 9–10% a year until 2020, 4–6% since 2023), up to 93 months earlier. |
| `SEXOPAC` | `M` 56%, `F` 44%. |
| `RACACOR` | `03` brown 37%, `01` white 36%, `99` not informed 15%, `02` black 7%, `04` yellow 5%, `05` indigenous 0.1%. |
| `MOT_COB` | `21` (continues) 96%, `28` 2%, `12` 0.7%, `18` 0.7%, `11`, `15`, `31`. |
| `DESTINOPAC` | `00` (stays in care) 98.5%, `03` 0.8% (with `MOT_COB = 18`), `02` 0.5% (with `12`), `01` 0.1% (with `11`), `04` (with `31`, transfer), `05`, `06`. |
| `DT_FIM` | Filled on 2.2% of rows: the episodes that end (`DESTINOPAC <> '00'`). |
| `DT_MOTCOB` | Filled on 0.5% only, with junk (`00000000`, `18991230`, `F`); use `DT_FIM`. |
| `CATEND` | `01` elective on ~100%. |
| `CIDASSOC` | `NULL` on 86% of rows. |
| `ORIGEM_PAC` | `01` 51%, `02` 37%, `05` 3.4%, `04` 3.1%, `03` 2.7%, `06` 2.4%. No code list in the Informe. |
| `COB_ESF` / `CNES_ESF` | `S` on 38% of rows; `CNES_ESF` filled on those. |
| `DT_INICIO` | Start of the episode. 2.2% of rows have `20130101` and 1.6% `20130102`: patients carried over from the APAC era were registered with the first days of the RAAS. |
| `INICIO`, `FIM`, `PERMANEN` | `YYYYMMDD` (not `DDMMAAAA`, as the Informe says), on the `QTDPCN = '1'` rows only (29% of rows); `PERMANEN` `31` / `30` on most of them. |
| `PA_SRV` / `PA_CLASS_S` | Always `115` (psychosocial care); class `002` on 99.5%. |
| `NAT_JUR` | `1244` municipality 67%, `1031` municipal executive body 13%, `1023` state executive body 2%. `NULL` before Jul/2016, except Oct/2014. |

### PS-only columns

| Column | Size | Official description | Notes |
|---|---|---|---|
| `TIPPRE` | 2 | Provider type. | Real codes until Dec/2013 (`50` on 92% of rows, `61`, `40`, `60`, `20`, `30`); `00` on more rows from Jan/2014, and only `00` from Nov/2015. The DBF field name is `'TIPPRE  '` (space-padded); `datasus` strips it. |
| `SIT_RUA` | 1 (3 in the files) | Patient lives on the street: `S` yes, `N` no. | `S` on 2.4% of rows (2.2–3.1% every year). Asked again every month. |
| `TP_DROGA` | 3 | Type of drug: `A` alcohol, `C` crack, `O` other. | Letters combined: `A` 8%, `O` 6%, `AO` 3.5%, `ACO` 3.1%, `C`, `AC`, `CO` 0.7% each; a few `A O`, `N`, `NNN`. `NULL` (no drug use informed) on 77% of rows: 98% in 2013, then 72–82%. |
| `LOC_REALIZ` | 1 | Place: `C` CAPS, `T` community (*território*). | `T` on 2.1% of rows; 36% of home visits (`0301080240`) and 41% of therapeutic-residence follow-up (`0301080046`). |

### Added by this package

| Column | Type | Meaning |
|---|---|---|
| `_ARQUIVO_ORIGEM` | text | DATASUS file the row came from (`PSSP2605.dbc`). |
| `competencia` | `INTEGER` | Partition: month of the file (`YYYYMM`) = `DT_PROCESS`. |
| `uf` | text | Partition: state of the file. |

## Joins

| From | To | Note |
|---|---|---|
| `PA_PROC_ID` | `procedimentos.codigo` | All in SIGTAP subgroup `030108`. |
| `CIDPRI`, `CIDASSOC` | `cid10.codigo` | 3- and 4-character codes both join. |
| `uf` | `ufs.uf` | State of the facility. |
| `LEFT(MUNPAC, 2)` | `ufs.ibge` | State where the patient lives. |
| `CNES_EXEC`, `DT_ATEND`, `PA_PROC_ID` | `pa` (`PA_CODUNI`, `PA_CMP`, `PA_PROC_ID`, `PA_DOCORIG = 'B'`) | Totals only; no row key. |
| `CNS_PAC` | `ad.AP_CNSPCN` (2012), other APAC types | Same patient encoding. |

`ps` has no occupation (CBO) column: the professional of each action is recorded on the
RAAS but not published.

## Known quirks and layout changes

- **One layout.** 44 columns; **`NAT_JUR`** appended (45) in the **Oct/2014** files of every
  state and from Jul/2016 on (checked on every month of SP). It is `NULL` in the other
  months. The record is 227 bytes (231 with `NAT_JUR`).
- **The Informe's names differ from the files** for four columns: `QT_APRES` / `QT_APROV`
  are `PA_QTDPRO` / `PA_QTDAPR`, `SERV` is `PA_SRV`, `CLASS` is `PA_CLASS_S`. It also gives
  `DT_PROCESS` 14 characters (6 in the files) and the `INICIO`/`FIM` format as `DDMMAAAA`
  (`YYYYMMDD` in the files).
- **The space-padded field name** `'TIPPRE  '`: tools that read DBF names literally get a
  column with two trailing spaces; `datasus` strips it.
- **Nov–Dec/2012** are pilot months (6–7 states, ~1–7 k rows, 77% `LOC_REALIZ = 'T'`).
  24 states report from Jan/2013, all 27 for the first time in May/2013; see [From AD to PS](#from-ad-to-ps-2013).
  Since then the only gaps are AC (Feb–Apr and Jun/2013) and AP (13 months of 2013–2015,
  and Dec/2023).
- **The latest month is incomplete** in some states (Aug/2026: 354 k patient-months against
  ~485 k in Jul/2026).

## Examples

```sql
-- CAPS patient-months, distinct patients and actions per year
SELECT competencia // 100 AS ano,
       SUM(QTDPCN::INT) AS pacientes_mes,
       COUNT(DISTINCT CNS_PAC) FILTER (WHERE CNS_PAC <> '{{{{{{{{{{{{{{{') AS pacientes,
       SUM(PA_QTDAPR) AS acoes
FROM ps WHERE competencia BETWEEN 201301 AND 202512
GROUP BY 1 ORDER BY 1;

-- What CAPS do: actions by procedure, with names, in 2025
SELECT p.nome, SUM(PA_QTDAPR) AS acoes,
       ROUND(100.0 * SUM(PA_QTDAPR) / SUM(SUM(PA_QTDAPR)) OVER (), 1) AS pct
FROM ps JOIN procedimentos p ON p.codigo = ps.PA_PROC_ID
WHERE competencia BETWEEN 202501 AND 202512
GROUP BY 1 ORDER BY 2 DESC;

-- Main diagnoses of CAPS patients in SP, May/2026 (one count per RAAS)
SELECT COALESCE(c.nome, ps.CIDPRI) AS diagnostico, SUM(QTDPCN::INT) AS pacientes_mes
FROM ps LEFT JOIN cid10 c ON c.codigo = ps.CIDPRI
WHERE competencia = 202605 AND uf = 'SP'
GROUP BY 1 ORDER BY 2 DESC LIMIT 10;

-- Patients using crack, and living on the street, per state in 2025
SELECT uf,
       COUNT(DISTINCT CNS_PAC) FILTER (WHERE TP_DROGA LIKE '%C%') AS crack,
       COUNT(DISTINCT CNS_PAC) FILTER (WHERE SIT_RUA = 'S') AS situacao_de_rua
FROM ps WHERE competencia BETWEEN 202501 AND 202512 AND CNS_PAC <> '{{{{{{{{{{{{{{{'
GROUP BY 1 ORDER BY 2 DESC;
```
