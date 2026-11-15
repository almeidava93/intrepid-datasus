# an — APAC Nefrologia (chronic dialysis), Jan/2008 to Jul/2014

**Source:** `ANufaamm.dbc` files in `ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados`
(e.g. `ANSC1305.dbc`). No state is split into parts.
**Coverage:** Jan/2008 to Oct/2014 on the FTP (82 months; every state, with a few months
missing for small states: RR 73 files, AC 77), but **the real data ends in Jul/2014**:
Aug–Oct/2014 hold only 280 late billings. **Discontinued:** from Aug/2014 dialysis APACs are
in [ATD](atd.md); see [from AN to ATD](atd.md#from-an-to-atd-2014).
**Size on the FTP** (Nov/2026): 2,145 files, about **0.46 GB** of `.dbc`, 6.53 M rows,
R$ 13.1 bn. The largest files (SP) have about 22,000 rows a month; small states a few hundred.
Parquet takes about 0.66× the `.dbc` size (0.30 GB for everything).
**Fetch:** `uv run datasus fetch -T an -s SC -f 2013`, or the whole history with
`-s all -f 2008 -t 201410`. In Nov/2026, three fetches of different year ranges into
separate stores, run in parallel with `-w 8`, took 11 minutes for every file.

Each row is **one dialysis APAC billed in one month**, and in practice **one patient on
chronic dialysis in one month**, as in ATD. Besides the 45 `AP_` columns shared by every
APAC type, AN has 15 `AN_` columns from the old nephrology *laudo*: date of the first
dialysis, height, weight, diuresis and glucose at the start, whether the patient has a
vascular access, abdominal ultrasound, urea reduction ratio, fistula interventions, the
transplant waiting list, albumin, haemoglobin and serology (HIV, HCV, HBsAg).

Read [APAC file types](apac.md) first: it explains authorisation, validity, monthly
continuation and the patient identifier, and describes the `AP_` columns.

## What is in AN

Only dialysis, every year: every row has a SIGTAP procedure of sub-group `030501`
(*tratamento dialítico*), checked for each year 2008–2014. No other nephrology care
(fistula surgery, transplant follow-up, pre-dialysis care) is in AN.

| `AP_PRIPAL` | Procedure | Rows 2008–2014 | % | Median `AP_VL_AP`, May/2014 |
|---|---|---|---|---|
| `0305010107` | Haemodialysis (max. 3 sessions a week) | 5.98 M | 91.5% | R$ 2,387 |
| `0305010166` | Home peritoneal dialysis (CAPD/APD), monthly follow-up | 470 k | 7.2% | R$ 2,701 |
| `0305010115` | Haemodialysis, patient with positive serology for HIV and/or hepatitis B/C | 42 k | 0.6% | R$ 3,493 |
| `0305010182` | Peritoneal dialysis training (9 days) | 20 k | 0.3% | R$ 665 |
| `0305010069` | *Hemodiálise I* (max. 3 sessions a week), retired code, until Sep/2012 | 14 k | 0.2% | |
| `0305010026` | Intermittent peritoneal dialysis (max. 2 sessions a week) | 7 k | 0.1% | R$ 1,105 |
| `0305010204` | Paediatric haemodialysis (max. 4 sessions a week), from Jan/2014 | 859 | 0.0% | R$ 4,620 |
| `0305010085` | *Hemodiálise I* in an HIV patient, retired code, until Sep/2012 | 333 | 0.0% | |

`AP_PRIPAL` is never `NULL`. Peritoneal dialysis (`0305010166`, `0305010182`, `0305010026`)
fell from 8.4% of rows (2008) to 6.8% (2014).

Rows per month grow steadily: 69,900 in Jan/2008, 80,700 in May/2010, 90,800 in May/2013,
95,800 in May/2014, then 69,358 in Jun/2014 and 23,485 in Jul/2014 (see
[the 2014 gap](#jun-and-jul2014-are-mostly-missing)). The value per row went from R$ 1,740
(2008) to R$ 2,260 (2014).

## One row is one APAC-month, about one patient-month

As in ATD, a dialysis APAC is valid for three months (`AP_DTINIC` to `AP_DTFIM`, median
90 days) and billed every month: `AP_TPAPAC = 1` in the first month (36% of rows every year),
`2` in the next two (64%), then a new APAC. So rows per APAC are 2.5–2.7 a year.
`(AP_AUTORIZ, AP_CMP)` is unique within a file except for 89 pairs in 2008 (twice each).
Across files, 598 APAC-months are billed in two different file months (554 of them first
billed in 2008, 34 in 2014): when you group by `AP_CMP` over several files, count
`DISTINCT (AP_AUTORIZ, AP_CMP)` rather than rows.

A patient normally has one row a month: in May/2014, 95,830 rows were 93,274 patients
(Jan/2008: 69,863 rows, 68,564 patients).

- **APACs:** `COUNT(*)` for one month; `COUNT(DISTINCT AP_AUTORIZ)` over several.
- **Patients on dialysis in a month:** `COUNT(DISTINCT AP_CNSPCN)` for that month. The
  encoded CNS is filled on every row except 58 (2008–2012), so unlike ATD after 2024 it
  can be used throughout.
- **Sessions:** not in AN; `PA_QTDAPR` of the APAC's `P` row in `pa`.
- 1.2–2.2% of rows a year are late billings (`AP_CMP` earlier than `AP_MVM`). For a series
  by month of care, group by `AP_CMP`.
- **New patients:** about 5% of rows a month have `AN_DTPDR` in the month of care (49,000
  in 2013).

## How an relates to pa (double counting)

**Every `an` row is one `pa` row with `PA_DOCORIG = 'P'`** (same procedure), and `AP_VL_AP`
equals `SUM(PA_VALAPR)` over the APAC's `P` and `S` rows. Join on `AP_AUTORIZ = PA_AUTORIZ`
**and** `AP_CMP = PA_CMP`, within the same `competencia` and `uf`. And the other way round,
**every `pa` `P` row with a `0305…` procedure is in `an`** until May/2014, so before
Jun/2014 `pa WHERE PA_DOCORIG = 'P' AND PA_PROC_ID LIKE '0305%'` selects exactly the `an`
rows. `PA_TPFIN` is always `04` (FAEC) on them.

| | SE 2008-01 | SE 2011-06 | AC 2011-12 | AC 2014-04/05, SE 2014-04/05 | DF 2014-07 |
|---|---|---|---|---|---|
| `an` rows | 555 | 776 | 220 | exact (checked for ATD) | 311 |
| … with exactly one `pa` `P` row, same procedure | 555 | 776 | 220 | | 311 |
| … `AP_VL_AP` = `SUM(PA_VALAPR)` over `P` + `S` | 555 | 776 | 220 | | 311 |
| `pa` `P` rows with `PA_PROC_ID LIKE '0305%'` | 555 | 776 | 220 | | **1,164** |
| `SUM(AP_VL_AP)` | R$ 952,166.65 | R$ 1,481,847.83 | R$ 436,637.59 | | R$ 748,318.13 |

The secondary procedures (`S` rows) of a dialysis APAC are only in `pa`: the lab tests
(`0202…`: urea, creatinine, potassium, haemoglobin, serology, ...) and dialysis materials
(`0702…`).

!!! danger "Never add `an` to `pa`"
    `an`'s APACs and values are already in `pa`. `AP_VL_AP` is the value of the whole APAC
    (sessions plus secondary procedures): summing it with `pa`'s `S` rows counts them twice.

## Jun and Jul/2014 are mostly missing

AN shrinks in Jun/2014 and almost disappears in Jul/2014 in **every state**, while ATD only
starts in Aug/2014, but dialysis did not stop: `pa` has those months complete (DF Jul/2014:
1,164 dialysis `P` rows in `pa`, 311 in AN; AC and SE in [the ATD page](atd.md#from-an-to-atd-2014)).
AN rows by month of care (`AP_CMP`), all files:

| State | 2014-05 | 2014-06 | 2014-07 | Jul / May |
|---|---|---|---|---|
| SE | 978 | 842 | 91 | 9% |
| BA | 5,821 | 5,071 | 583 | 10% |
| MG | 12,221 | 9,527 | 2,076 | 17% |
| RJ | 9,962 | 6,606 | 2,778 | 28% |
| SP | 21,975 | 15,574 | 6,208 | 28% |
| AM | 876 | 614 | 342 | 39% |
| Brazil | 95,390 | 69,597 | 24,110 | 25% |

**Workaround:** for Jun–Jul/2014 use `pa` (`PA_DOCORIG = 'P' AND PA_PROC_ID LIKE '0305%'`),
which has every APAC but none of the `AN_` columns; or use `pa` for the whole period if APAC
counts, sessions and values are enough. The rest of the switch — no APAC in both files,
94% of AN's Jul/2014 patients in ATD in Aug/2014 with the same encoded `AP_CNSPCN`, and which
clinical items exist in both layouts — is on [the ATD page](atd.md#from-an-to-atd-2014).

## Patients

`AP_CNSPCN` (encoded) is complete (58 empty rows in 6.5 M). 57–58% men, median age 53
(2008) to 55 (2014) years; 99.9% of ages in years. Deaths (`AP_OBITO = 1`, `AP_MOTSAI` 41–43)
are 1.3% of rows a year (about 13,000 a year). Hepatitis C positivity fell from 5.6% of rows
(2008) to 3.0% (2014); HBsAg about 1%, HIV about 0.7%.

## an vs an_raw

`an_raw` holds every column as text exactly as DATASUS publishes it. `an` is the same data
with `AP_VL_AP` cast to `DOUBLE` (with `TRY_CAST`). Everything else stays text, including
codes with leading zeros, dates (`AN_DTPDR = '20090415'`) and the measurements, which are
typed in several formats (see [measurements](#measurements)).

## Columns

The shared `AP_` columns are described on the [APAC page](apac.md#shared-columns). The
official description is the DATASUS *Informe Técnico SIASUS* (Jul/2019), section 3.4.3,
*Layout do arquivo de APAC de nefrologia: ANUFMM.DBF* (60 columns). The meanings below come
from the DATASUS *Layout da interface texto do APAC e do SIA – layout interno* (Apr/2014),
part 09 (*parte variável de Nefrologia*), the same document as ATD's part 18. It marks each
field as filled on the first dialysis only (\*), on later months only (\*\*), or on both
(\*\*\*). Values were checked on every file (Jan/2008–Oct/2014, 6.53 M rows).

### What the shared columns hold in AN

| Column | Notes for AN |
|---|---|
| `AP_PRIPAL` | The dialysis procedure, see [what is in AN](#what-is-in-an). Never `NULL`. |
| `AP_CIDPRI` | **Filled, unlike ATD**: `N180` (end-stage kidney disease) on 98% of rows, then `N189`, `I120`, `N039`, `N083`, `I10`. Never `0000`. |
| `AP_CIDSEC` | Usually the underlying disease: `N189` 34%, `N180` 15%, `0000` 13%, `I10` hypertension 9%, `N188` 9%, `I120` hypertensive kidney disease 5%, `E142` diabetic nephropathy 2%. |
| `AP_CIDCAS` | `0000` on 76% of rows; otherwise `N180` (23%). |
| `AP_TPATEN` | **Always `02`** (ATD has `10`). |
| `AP_TPAPAC` | `2` 64%, `1` 35%, `3` 0.3% (93% of them PD training, `0305010182`). |
| `AP_DTINIC`, `AP_DTFIM` | Three months (median 90 days). |
| `AP_VL_AP` | = sessions plus secondary procedures in `pa`. 0 on 0.7% of rows. |
| `AP_MOTSAI` | `21` (continues, nature of the disease) 95%; `31` transfer 1.6%; `41`/`43` death 1.2%; `28`, `26`, `18`, `51`, `12`, `15`. |
| `AP_CATEND` | `01` (elective) 91%, `NULL` 5.5%, `02` (urgent) 3%. |
| `AP_TPUPS` | `36` specialised clinic 59%, `05` general hospital 31%, `39` 8.5%. |
| `AP_CODEMI` | `M…` (municipal) 60%, `E…` (state) 35%, `S…`, `U…`. |
| `AP_UNISOL`, `AP_APACANT` | `AP_UNISOL` equals `AP_CODUNI` on 90% of rows; `AP_APACANT` is zeros on 72%. |
| `AP_MNDIF` | **Always `1`** (wrong, as in the other APAC types); compare `AP_MUNPCN` with `AP_UFMUN` (different on 38% of rows). `AP_UFDIF` is correct (`1` on 1.0%). |
| `AP_CNSPCN` | Encoded; complete (see [patients](#patients)). |
| `AP_NATJUR` | Only in the Dec/2011 files (as in every APAC type and BI that month), as the last column, and **empty on every row**. `NULL` in every other month. |

### Nephrology columns (`AN_`)

"Filled" below is what the files show: the layout's first-dialysis fields are filled on
every `AP_TPAPAC = 1` row *and* on 77% of continuation rows, and its later-month fields on
every `AP_TPAPAC = 2` row and on 44% of initial rows; the other rows have `NULL`. So a
`NULL` means "not asked on this laudo", and a zero means "not measured or not informed".

| Column | Width | Meaning | Codes and values |
|---|---|---|---|
| `AN_DTPDR` | 8 | Date of the first dialysis ever (`YYYYMMDD`) | (\*) `NULL` on 15% of rows (12–21% a year). About 5% of rows a month have it in the month of care (new patients). |
| `AN_ALTURA` | 3 | Height, cm | (\*) `165`, `160`, `170`, ...; zero on 21%. |
| `AN_PESO` | 3 | Weight, kg | (\*) `60`, `070`, ...; zero on 20%. |
| `AN_DIURES` | 4 | Residual diuresis, mL/24 h | (\*) zero on about half the rows (anuric, or not informed); `1000`, `500`, `100`, ... |
| `AN_GLICOS` | 4 | Blood glucose, mg/dL | (\*) zero on 30%; `80`, `100`, `90`, ... |
| `AN_ACEVAS` | 1 | Has a vascular access | (\*) `S` yes (56%), `N` no (31%). Only yes/no, **not the type** (ATD's `ATD_ACEVAS` is fistula / short-term / long-term catheter). In 2014, 1,501 rows have `2`: probably ATD's code typed into the old laudo. |
| `AN_ULSOAB` | 1 | Abdominal ultrasound done | (\*) `S`, `N` (mostly `N`). |
| `AN_TRU` | 4 | Urea reduction ratio (URR), % | (\*\*) Integer (`69`, `0070`); decimal comma on 1% of rows in 2014; zero on 30%; plausible (20–100) on 57%. Median 69. |
| `AN_INTFIS` | 2 | Number of interventions on the arteriovenous fistula | (\*\*) Mostly `0`/`00` and `1`/`01`; `NULL` on 35–37% of rows (also on 24% of continuation rows). |
| `AN_CNCDO` | 1 | On the transplant waiting list (CNCDO) | (\*\*) `S` yes, `N` no. `S` fell from 39% of rows (2008) to 28% (2014). |
| `AN_ALBUMI` | 2 | Serum albumin, g% (= g/dL) | (\*\*\*) See [measurements](#measurements). |
| `AN_HCV` | 1 | Anti-HCV antibodies | (\*\*\*) `P` positive, `N` negative; always filled. |
| `AN_HBSAG` | 1 | HBsAg | (\*\*\*) `P`, `N`; always filled. |
| `AN_HIV` | 1 | Anti-HIV antibodies | (\*\*\*) `P`, `N`; always filled. |
| `AN_HB` | 2 | Haemoglobin, g% (= g/dL) | (\*\*\*) See [measurements](#measurements). |

### Measurements

The measurement columns are text. Their formats did not change between 2008 and 2014
(same shares every year), unlike ATD's lab values in 2021.

- **`AN_HB`** is a whole number of g/dL (`11`, `10`, `09`): plausible (3–20) on 74% of rows,
  zero on 18%, and 21–99 on 7% (`93`, `99`: probably 9.3 without the point, or a filler).
  Median 11. A few typos (`9,`, `0N`, `##`, `NN`).
- **`AN_ALBUMI`** mixes two scales: about 53% of rows are one non-zero digit (`4`, `04`, `3`:
  g/dL, rounded) and about 20% are tenths without the point (`39` = 3.9 g/dL); zero (25%)
  is not measured. Read 1–6 as g/dL and 10–60 as tenths.
- **`AN_TRU`**, **`AN_ALTURA`**, **`AN_PESO`**, **`AN_DIURES`**, **`AN_GLICOS`** are whole
  numbers with or without leading zeros; zero = not informed.

```sql
-- Haemoglobin and albumin (g/dL) of haemodialysis patients by year, plausible values only
SELECT competencia // 100 AS ano,
       MEDIAN(hb) FILTER (hb BETWEEN 3 AND 20) AS hb_mediana,
       MEDIAN(CASE WHEN alb BETWEEN 1 AND 6 THEN alb WHEN alb BETWEEN 10 AND 60 THEN alb / 10 END) AS albumina_mediana
FROM (SELECT competencia, TRY_CAST(AN_HB AS INT) AS hb, TRY_CAST(AN_ALBUMI AS DOUBLE) AS alb
      FROM an WHERE AP_PRIPAL IN ('0305010107', '0305010115'))
GROUP BY 1 ORDER BY 1;
```

### Added by this package

| Column | Type | Meaning |
|---|---|---|
| `_ARQUIVO_ORIGEM` | text | DATASUS file the row came from (`ANSP1405.dbc`). |
| `competencia` | `INTEGER` | Partition: month of the file (`YYYYMM`); equals `AP_MVM`. |
| `uf` | text | Partition: state of the file (the dialysis facility's state). |

## Joins

- `AP_PRIPAL` → `procedimentos.codigo` (procedure name and SIGTAP price). The retired
  codes `0305010069` and `0305010085` are only in SIGTAP versions up to 2012 (fetch one with
  `datasus sigtap fetch -f 201208` and use the `sigtap_*_all` views).
- `AP_CIDPRI`, `AP_CIDSEC` → `cid10.codigo`.
- `uf` → `ufs.uf`; `LEFT(AP_MUNPCN, 2)` → `ufs.ibge` (patient's state of residence).
- `AP_AUTORIZ`, `AP_CMP` → `pa.PA_AUTORIZ`, `pa.PA_CMP` (same `competencia` and `uf`) for the
  sessions (`PA_QTDAPR`), lab tests and values.
- `AP_CNSPCN` → `atd.AP_CNSPCN` (same patient from Aug/2014) and the other APAC tables.
- No professional (CBO) column, so no join to `ocupacoes`.

## Known quirks and layout changes

- **One layout, 2008–2014.** 60 columns (45 `AP_` + 15 `AN_`), record of 286 bytes, on every
  SP file Jan/2008–Sep/2014 (header probe; `ANSP1410` does not exist). The Dec/2011 files of
  every state have a 61st column, `AP_NATJUR`, appended last (290 bytes) and empty; the view
  reads it with `union_by_name`, so it is `NULL` everywhere. `AP_VL_AP` is a numeric (`N`)
  field 20 wide. The procedure mix, `AP_TPAPAC`, rows per APAC and the measurement formats
  are the same every year.
- **Discontinued in 2014**, with Jun–Jul/2014 mostly missing: see
  [above](#jun-and-jul2014-are-mostly-missing). Aug–Oct/2014 files hold only late bills
  (259, 19 and 2 rows, care months May–Jul/2014).
- `AP_TPATEN` is always `02`; `AP_MNDIF` is always `1` (wrong).
- `AN_ACEVAS` is yes/no, not the access type.
- **Conversion size.** The largest file (SP, about 22,000 rows) needs a 6 MB temporary DBF
  and converts in about a second.

## Examples

```sql
-- Patients on chronic dialysis per month, by type, 2008 to May/2014
SELECT competencia,
       COUNT(DISTINCT AP_CNSPCN) FILTER (AP_PRIPAL IN ('0305010107', '0305010115', '0305010069', '0305010085', '0305010204')) AS hemodialise,
       COUNT(DISTINCT AP_CNSPCN) FILTER (AP_PRIPAL IN ('0305010166', '0305010026')) AS dialise_peritoneal
FROM an
WHERE competencia <= 201405
GROUP BY 1 ORDER BY 1;

-- Underlying kidney disease (AP_CIDSEC) of patients starting dialysis, 2013
SELECT a.AP_CIDSEC, c.nome, COUNT(DISTINCT a.AP_CNSPCN) AS pacientes
FROM an a LEFT JOIN cid10 c ON c.codigo = a.AP_CIDSEC
WHERE a.competencia BETWEEN 201301 AND 201312 AND a.AN_DTPDR LIKE a.AP_CMP || '%'
GROUP BY ALL ORDER BY pacientes DESC LIMIT 10;

-- A continuous dialysis series across the AN -> ATD switch, from pa (fetch -T pa)
SELECT PA_CMP, COUNT(*) AS apacs, SUM(PA_QTDAPR) AS sessoes
FROM pa
WHERE competencia BETWEEN 201301 AND 201512 AND PA_DOCORIG = 'P' AND PA_PROC_ID LIKE '0305%'
GROUP BY 1 ORDER BY 1;
```
