# atd — APAC Tratamento Dialítico (chronic dialysis), Aug/2014 onward

**Source:** `ATDufaamm.dbc` files in `ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados`
(e.g. `ATDSC2605.dbc`). No state is split into parts.
**Coverage:** Aug/2014 to the latest month DATASUS has released (Aug/2026 when this was
written): 145 months, every state every month except AP (141). Before Aug/2014, dialysis
APACs are in **[AN](an.md)** (APAC Nefrologia): see [from AN to ATD](#from-an-to-atd-2014).
**Size on the FTP** (Nov/2026): 3,911 files, about **1.06 GB** of `.dbc`, 16.7 M rows,
R$ 44.8 bn. The largest files (SP) have about 30,000 rows a month; small states a few hundred.
Parquet takes about 0.75× the `.dbc` size (0.79 GB for everything: the files are small, and
each carries some Parquet overhead).
**Fetch:** `uv run datasus fetch -T atd -s SC -f 2024`, or the whole history with
`-s all -f 201408 -t 2026`. In Nov/2026, three fetches of different year ranges into
separate stores, run in parallel with `-w 8`, took 20 minutes for every file.

Each row is **one dialysis APAC billed in one month**, and in practice **one patient on
chronic dialysis in one month**: haemodialysis sessions at a dialysis clinic, or home
peritoneal dialysis. Besides the 46 `AP_` columns shared by every APAC type, ATD has 19
`ATD_` columns from the dialysis *laudo*: whether the patient is a new case, when dialysis
started, the vascular access, transplant status, the month's lab values (haemoglobin,
phosphorus, Kt/V, urea reduction ratio, albumin, PTH), serology (HIV, HCV, HBsAg), and
whether the patient was admitted to hospital or had peritonitis that month.

Read [APAC file types](apac.md) first: it explains authorisation, validity, monthly
continuation and the patient identifier, and describes the `AP_` columns.

## What is in ATD

Only dialysis: every row has a SIGTAP procedure of subgroup `0305` (*tratamento em nefrologia*).

| `AP_PRIPAL` | Procedure | Rows 2014–2026 | % | Median `AP_VL_AP`, May/2026 |
|---|---|---|---|---|
| `0305010107` | Haemodialysis (max. 3 sessions a week) | 15.11 M | 90.6% | R$ 3,292 |
| `0305010166` | Home peritoneal dialysis (CAPD/APD), monthly follow-up | 0.83 M | 5.0% | R$ 3,716 |
| `0305010115` | Haemodialysis, patient with positive serology for HIV and/or hepatitis B/C | 0.67 M | 4.0% | R$ 4,444 |
| `0305010182` | Peritoneal dialysis training (9 days) | 34 k | 0.2% | R$ 665 |
| `0305010204` | Paediatric haemodialysis (max. 4 sessions a week; from Dec/2014) | 28 k | 0.2% | R$ 5,436 |
| `0305010026` | Intermittent peritoneal dialysis (max. 2 sessions a week) | 5 k | 0.0% | R$ 269 |
| `NULL` | no procedure (`AP_TPAPAC = 4`) | 90 | | |

The mix changes slowly: haemodialysis (the three haemodialysis codes) went from 93% of rows
(2014) to 96% (2026), and home peritoneal dialysis fell from 6.6% (2015) to 3.9% (2025).

Rows per year and per month grow steadily: 95,900 in Aug/2014, 105,200 in Jan/2018, 122,300
in Jan/2023, 137,500 in Jan/2026. The value per row went from R$ 2,290 (2014) to R$ 3,175
(2026), following the SIGTAP price of a session.

## One row is one APAC-month, about one patient-month

A dialysis APAC is valid for three months (`AP_DTINIC` to `AP_DTFIM`, 87–91 days on 91% of
rows since 2024) and is billed every month: `AP_TPAPAC = 1` in the first month, `2` in the next two
(35% and 64% of rows every year), then a new APAC with a new number. So **rows per APAC are
2.5** a year, and the same `AP_AUTORIZ` appears in up to three consecutive monthly files.
`(AP_AUTORIZ, AP_CMP)` is unique within a file (one exception: one RJ APAC in Nov/2022–Jan/2023).

A patient normally has one row a month: in May/2023, 122,639 rows were 119,979 patients;
1,928 patients had 2 rows and 347 had 3 or more, mostly a haemodialysis APAC billed twice
(another facility, or a late billing of an earlier month) or peritoneal dialysis plus its
training.

- **APACs:** `COUNT(*)` for one month; `COUNT(DISTINCT AP_AUTORIZ)` over several.
- **Patients on dialysis in a month:** `COUNT(DISTINCT AP_CNSPCN)` for that month — but see
  [patients](#patients) from 2024.
- **Sessions:** not in ATD. The number of sessions is `PA_QTDAPR` of the APAC's `P` row in
  `pa` (about 12 a month for haemodialysis).
- About 1% of rows are late billings (`AP_CMP` earlier than `AP_MVM`). For a series by month
  of care, group by `AP_CMP` instead of `competencia`, after the later files are in.

## How atd relates to pa (double counting)

**Every `atd` row is one `pa` row with `PA_DOCORIG = 'P'`** (the APAC's main procedure, same
code), and `AP_VL_AP` equals `SUM(PA_VALAPR)` over the APAC's `P` and `S` rows. Join on
`AP_AUTORIZ = PA_AUTORIZ` **and** `AP_CMP = PA_CMP`, within the same `competencia` and `uf`.
And the other way round, **every `pa` `P` row with a `0305…` procedure is in `atd`** (from
Aug/2014), so for dialysis APACs, `pa WHERE PA_DOCORIG = 'P' AND PA_PROC_ID LIKE '0305%'`
selects exactly the `atd` rows. `PA_TPFIN` is always `04` (FAEC) on them.

| | AC 2014-08 | SE 2014-08 | SE 2018-05 | ES 2023-09 | AC 2026-05 | SE 2026-05 |
|---|---|---|---|---|---|---|
| `atd` rows | 255 | 974 | 982 | 2,545 | 650 | 1,559 |
| … with exactly one `pa` `P` row, same procedure | 255 | 974 | 982 | 2,545 | 650 | 1,559 |
| … `AP_VL_AP` = `SUM(PA_VALAPR)` over `P` + `S` | 255 | 974 | 982 | 2,545 | 650 | 1,559 |
| `pa` `P` rows with `PA_PROC_ID LIKE '0305%'` | 255 | 974 | 982 | 2,545 | 650 | 1,559 |
| `SUM(AP_VL_AP)` | | | R$ 2,527,626.33 | R$ 7,662,230.70 | R$ 2,337,246.68 | R$ 4,918,784.94 |

The secondary procedures (`S` rows) of a dialysis APAC are only in `pa`: the monthly and
quarterly lab tests (`0202…`: urea, creatinine, potassium, haemoglobin, phosphorus, PTH,
serology, ...), extra sessions (`0305010093`), dialysis materials (`070210…`) and, in some
months, a catheter implant (`0418010064`). Vascular access *surgery* (fistula creation,
`041801003x`) is not in ATD.

| You want | Use |
|---|---|
| Dialysis value or volume (sessions, lab tests) | `pa` (`PA_QTDAPR`, `PA_VALAPR`) |
| Patients, dialysis type, access, transplant status, lab values | `atd` |
| Both | join `atd` to `pa` on `AP_AUTORIZ` = `PA_AUTORIZ` and `AP_CMP` = `PA_CMP` |

!!! danger "Never add `atd` to `pa`"
    `atd`'s APACs and values are already in `pa`. `AP_VL_AP` is the value of the whole APAC
    (sessions plus secondary procedures): summing it with `pa`'s `S` rows counts them twice.

## From AN to ATD (2014)

Dialysis APACs were published as **AN** (*APAC Nefrologia*, its own layout with `AN_`
columns: weight, height, diuresis, glucose, ...) until mid-2014 and as **ATD** since. The
change followed the new rules for chronic kidney disease care of 2014 (Portaria GM/MS
389/2014), which brought a new dialysis *laudo*. The two files hold the same thing — one row
per dialysis APAC per month, the same `0305…` procedures — so they can be put end to end,
with three things to know.

**1. There is no real overlap.** AN files exist up to Oct/2014 and ATD starts in Aug/2014,
but AN after Jul/2014 holds only late billings of May–Jul care:

| File month | AN rows | ATD rows |
|---|---|---|
| 2014-01 … 2014-05 | 94,000–96,000 a month | – |
| 2014-06 | 69,358 | – |
| 2014-07 | 23,485 | – |
| 2014-08 | 259 (care months 2014-05 to 07) | 95,928 |
| 2014-09 | 19 (2014-06/07) | 96,718 |
| 2014-10 | 2 (2014-07) | 96,904 |

None of those 280 late AN rows has an APAC number that appears in ATD, and no ATD APAC
reuses an AN number (0 of 94,864 in Aug/2014), so **no row is in both files**. Patients do
continue across the switch: 21,672 of the 23,125 patients in AN, Jul/2014, are in ATD,
Aug/2014, and 82,600 of the 93,512 patients in ATD, Aug/2014, were in AN in May–Jul/2014
(same encoded `AP_CNSPCN`; the CNS is complete in both files in 2014).

**2. Jun and Jul/2014 are missing from both files.** AN falls to 69 k rows in Jun/2014 and
23 k in Jul/2014, and ATD starts only in Aug/2014, while dialysis went on (about 95 k
patients a month). `pa` has those months complete:

| Care month | AN + ATD rows (all files, by `AP_CMP`) | `pa` dialysis `P` rows, AC | in AN, AC | `pa` dialysis `P` rows, SE | in AN, SE |
|---|---|---|---|---|---|
| 2014-05 | 95,390 | 252 | 252 | 990 | 990 |
| 2014-06 | 69,597 | 253 | 146 | 1,037 | 890 |
| 2014-07 | 24,110 | 257 | 78 | 974 | 91 |
| 2014-08 | 95,852 | 255 | 255 (ATD) | 974 | 974 (ATD) |

Before Jun/2014 every `pa` dialysis APAC is in AN (Apr and May checked), and from Aug/2014
every one is in ATD. The missing Jun/Jul APACs are in `pa` only, as `P` rows with
`PA_PROC_ID LIKE '0305%'`, with no patient columns beyond what `pa` has.

**3. The columns differ.** Only the `AP_` columns and these clinical items exist in both:

| Item | AN | ATD |
|---|---|---|
| First dialysis date | `AN_DTPDR` | `ATD_DTPDR` |
| Urea reduction ratio | `AN_TRU` | `ATD_TRU` |
| Albumin | `AN_ALBUMI` (2 chars, g%) | `ATD_ALBUMI` (4 chars, g/dL) |
| Haemoglobin | `AN_HB` (2 chars, g%) | `ATD_HB` (4 chars, g/dL) |
| HIV, HCV, HBsAg | `AN_HIV`, `AN_HCV`, `AN_HBSAG` | `ATD_HIV`, `ATD_HCV`, `ATD_HBSAG` |
| Vascular access | `AN_ACEVAS` (S/N: has one) | `ATD_ACEVAS` (1 fistula, 2 short-term catheter, 3 long-term catheter) |
| Transplant list | `AN_CNCDO` (S/N) | `ATD_SITTRA` + `ATD_SEAPTO` = 1 |

Phosphorus, Kt/V, PTH, new case, transplant fitness, admissions and peritonitis are ATD
only; weight, height, diuresis, glucose, abdominal ultrasound and fistula interventions are
AN only.

**A continuous dialysis series** (APACs or patients by month of care):

- up to **2014-05**: AN; **2014-06 and 2014-07**: `pa` (`PA_DOCORIG = 'P' AND PA_PROC_ID LIKE
  '0305%'`), or AN for the APACs it has; from **2014-08**: ATD;
- or simply `pa` for the whole period, if APACs (not patient attributes) are enough: it has
  every month, and the same rows as AN (Apr/May checked) and ATD (every month checked).
- Count patients with `AP_CNSPCN` on both sides (same encoding). Group by `AP_CMP`, not by
  file month, so AN's late rows land in their own month; don't add AN's Aug–Oct/2014 rows
  to ATD's as extra patients — they are earlier months.

```sql
-- Dialysis APACs by month of care, 2013-2015, from pa (complete across the AN -> ATD switch)
SELECT PA_CMP, COUNT(*) AS apacs, SUM(PA_QTDAPR) AS sessoes
FROM pa
WHERE competencia BETWEEN 201301 AND 201512 AND PA_DOCORIG = 'P' AND PA_PROC_ID LIKE '0305%'
GROUP BY 1 ORDER BY 1;
```

## Patients

`AP_CNSPCN` (encoded) is complete until Mar/2024. Then it is empty (`NULL`) or the
placeholder `{{{{{{{{{{{{{{{` on a share of rows that grows, and in May–Aug/2026 on most:

| Month | until Mar/2024 | Jul/2024 | Nov/2024 | Jan/2025 | Jul/2025 | Jan/2026 | Mar/2026 | Apr/2026 | May/2026 | Jun/2026 | Jul/2026 | Aug/2026 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `NULL` + placeholder | 0% | 1.9% | 7.1% | 8.8% | 8.4% | 13.3% | 15.0% | 20.1% | 45.6% | 65.5% | **90.5%** | **96.4%** |

By state, in Jan/2026 it ranged from 0% (AL, AP, RN, RR, SE, TO) to 47% (CE); in Aug/2026
from 78% (MT) to 100% (AC, AM, PI, RN, RO, RR, TO). It is per type and state (AD: 67% in
Aug/2026; AM: none), not in the patient register. Exclude both values
(`AP_CNSPCN IS NOT NULL AND AP_CNSPCN <> '{{{{{{{{{{{{{{{'`) before counting or following
patients, and **don't count patients from mid-2024 on**; count rows (APACs) instead, which
are complete and are about one per patient (see [above](#one-row-is-one-apac-month-about-one-patient-month)).

Patient attributes: 58% men, median age 56 (2014) to 59 (2026) years; 99.98% of ages in
years (`AP_COIDADE = 4`). Deaths (`AP_MOTSAI` 41–43, `AP_OBITO = 1`) are 15–18 k a year
(21 k in 2021, 19.6 k in 2020).

## atd vs atd_raw

`atd_raw` holds every column as text exactly as DATASUS publishes it. `atd` is the same data
with `AP_VL_AP` cast to `DOUBLE` (with `TRY_CAST`). Everything else stays text, including
codes with leading zeros, dates (`ATD_DTPDR = '20190415'`) and **the lab values**, whose
format varies too much for one cast (see [lab values](#lab-values)).

## Columns

The shared `AP_` columns are described on the [APAC page](apac.md#shared-columns). The
official description is the DATASUS *Informe Técnico SIASUS* (Jul/2019), section 3.4.8,
*Layout do arquivo de APAC de tratamento dialítico: ATDUFMM.DBF* (65 columns, with
`AP_NATJUR` last); it gives no code lists. The codes below come from the DATASUS *Layout da
interface texto do APAC e do SIA – layout interno* (Apr/2014), part 18 (*parte variável do
laudo de Tratamento Dialítico*), the layout that facilities use to submit the laudo. Values were
checked on every file (Aug/2014–Aug/2026, 16.7 M rows); "since 2024" is Jan/2024–Aug/2026 (4.3 M rows).

### What the shared columns hold in ATD

| Column | Notes for ATD |
|---|---|
| `AP_PRIPAL` | The dialysis procedure, see [what is in ATD](#what-is-in-atd). `NULL` on 90 rows (2015–2026, a few a month), all with `AP_TPAPAC = 4`. |
| `AP_CIDPRI`, `AP_CIDSEC` | **Always `0000`**: ATD has no diagnosis column filled. |
| `AP_CIDCAS` | The only diagnosis: `0000` on 88% of rows since 2024 (76% in 2014). Otherwise `N180` (chronic kidney disease stage 5), `N188`, `N189`, and on the positive-serology procedure `0305010115` the infection: `B182`/`B181` chronic hepatitis C/B, `Z21`/`B24`/`B20` HIV (68% of its rows). |
| `AP_TPATEN` | **Always `10`** (dialysis). |
| `AP_TPAPAC` | `2` 64%, `1` 35% every year; `3` only for PD training; `4` (not in the layout) on 90 rows without a procedure. |
| `AP_DTINIC`, `AP_DTFIM` | Three months (87–91 days on 91% of rows since 2024). |
| `AP_VL_AP` | = sessions plus secondary procedures in `pa`. 0 on 0.7–1% of rows a year. |
| `AP_MOTSAI` | Since 2024: `21` (continues, nature of the disease) 95%; `31` transfer 1.5%; `41`/`43`/`42` death 1.1%; `18`, `28`, `51` (administrative closure), `26` (change of procedure), `15`, `11`, `12`, ... |
| `AP_CATEND` | `01` (elective) 99%. |
| `AP_TPUPS` | Since 2024: `36` specialised clinic 62%, `05` general hospital 30%, `39` 5%. |
| `AP_UNISOL` | Equals `AP_CODUNI` on 93% of rows since 2024. `AP_APACANT` is zeros on 78%. |
| `AP_CODEMI` | Since 2024: `M…` (municipal) 60%, `E…` (state) 37%, `S…`, `U…`. |
| `AP_MNDIF` | **Always `1`** (wrong, as in AM, AQ, AR and AD); compare `AP_MUNPCN` with `AP_UFMUN` (different on 40% of rows). `AP_UFDIF` is correct (`1` on 1.1%). |
| `AP_CNSPCN` | Encoded, but **empty or `{{{{{{{{{{{{{{{` on most rows from May/2026**: see [patients](#patients). |
| `AP_NATJUR` | From Jul/2016 (`NULL` before). It is the last column of the file, after the `ATD_` columns. |

### Dialysis columns (`ATD_`)

| Column | Width | Meaning | Codes and values |
|---|---|---|---|
| `ATD_CARACT` | 1 | Characteristic of the treatment | `1` new case, `2` continuing treatment, `3` patient in transit (dialysing away from home), `4` transfer from another facility. Since 2024: `2` 84%, `1` 14%, `4` 1.7%, `3` 0.5%. `1` was 37% of rows in 2014 and fell to 14–16% from 2022. **Not a reliable incident marker**: on `1` rows since 2024, dialysis had started a median of 8 months before (`ATD_DTPDR`), and within 3 months on only 41%, so facilities keep it from the first laudo. For new patients use `ATD_DTPDR`. |
| `ATD_DTPDR` | 8 | Date of the first dialysis ever (`YYYYMMDD`) | Filled on every row except the 90 rows without a procedure. A few impossible dates (from 1929, or `9999…`). About 3% of rows a month have `ATD_DTPDR` in the month of care: about 45,000 patients start dialysis each year. |
| `ATD_DTCLI` | 8 | Date dialysis started at this facility (`YYYYMMDD`) | Later than `ATD_DTPDR` on 31% of rows since 2024, and on 90% of transfers (`ATD_CARACT = 4`). |
| `ATD_ACEVAS` | 1 | Vascular access | `1` arteriovenous fistula (FAV), `2` short-term catheter, `3` long-term catheter. Filled on every row. On haemodialysis, fistula fell from 77% (2014) to 65% (2026), long-term catheter rose from 7% to 16%, short-term catheter 16–22%. On peritoneal dialysis it is mostly `3` (the Tenckhoff catheter, 62%), but `1`/`2` also occur. |
| `ATD_MAISNE` | 1 | Followed by a nephrologist for more than a year before dialysis | `S` yes, `N` no, `I` unknown. Required only for new cases (`ATD_CARACT = 1`); empty on 75% of the other rows. A few digits (`0`, `1`–`9`) are errors. |
| `ATD_SITINI` | 1 | Situation when dialysis started | `A` outpatient, `H` in hospital, `I` unknown. Required only for new cases. New cases since 2024: `I` 46%, `A` 42%, `H` 12%. |
| `ATD_SITTRA` | 1 | Transplant situation | `1` fit, `2` unfit, `3` refuses, `4` not applicable (new case, under 90 days of dialysis). Since 2024: `1` 36%, `2` 27%, `4` 31%, `3` 5%. `4` is used far beyond the first 90 days: on 67% of `4` rows dialysis had started more than 180 days before. |
| `ATD_SEAPTO` | 1 | If fit for transplant (`ATD_SITTRA = 1`) | `1` on the waiting list (CNCDO), `2` being assessed at a transplant centre, `3` not referred, `4` awaiting a transplant-centre appointment. Among fit patients since 2024: `1` 51%, `2` 20%, `3` 17%, `4` 12%. Empty or `0` otherwise (some rows have a code anyway). |
| `ATD_HB` | 4 | Haemoglobin, g/dL | See [lab values](#lab-values). Median 10.6. |
| `ATD_FOSFOR` | 4 | Serum phosphorus, mg/dL | Median 4.9. |
| `ATD_KTVSEM` | 4 | Kt/V (dialysis dose, no unit) | Optional. Median 1.38, so in practice a per-session (single-pool) Kt/V, although the layout says weekly. Missing (`0`/empty) on 38% of haemodialysis rows and 83% of peritoneal dialysis rows. |
| `ATD_TRU` | 4 | Urea reduction ratio (URR), % | Optional. Median 69. Missing on 33% of haemodialysis rows, 75% of peritoneal ones. |
| `ATD_ALBUMI` | 4 | Serum albumin, g/dL | Optional. Median 3.9. |
| `ATD_PTH` | 4 | Parathyroid hormone (PTH), pg/mL | Optional. Usually a 4-digit integer (`0624` = 624). Median 290. |
| `ATD_HIV` | 1 | Anti-HIV antibodies | `P` positive, `N` negative; optional (empty on 1.5%). Positive on 1.1% of rows since 2024. |
| `ATD_HCV` | 1 | Anti-HCV antibodies (hepatitis C) | Positive on 1.6%. |
| `ATD_HBSAG` | 1 | HBsAg (hepatitis B) | Positive on 0.6%. Patients with any positive serology are billed as `0305010115` (72% of its rows have a `P`). |
| `ATD_INTERC` | 1 | Admitted to hospital this month for a clinical complication | `S` yes (2.7% since 2024), `N` no, `I` unknown (30%, up from 20–22% before 2021). |
| `ATD_SEPERI` | 1 | If on peritoneal dialysis, peritonitis this month | `S`, `N`, `I`. Filled on haemodialysis rows too (`S` on 1.1% of them): use it only with `AP_PRIPAL IN ('0305010166', '0305010182', '0305010026')`, where `S` is 2.7%. |

### Lab values

The six lab columns are text, 4 characters. The layout says "number, decimal point allowed",
and facilities type them in many ways:

| Format (since 2024) | Hb | Phosphorus | Kt/V | URR | Albumin | PTH |
|---|---|---|---|---|---|---|
| decimal, `.` or `,` (`12.3`, `07,8`) | 68% | 69% | 54% | 53% | 60% | 8% |
| `0000`, `0` (not measured) | 19% | 20% | 28% | 25% | 24% | 26% |
| empty | 0% | 0% | 13% | 11% | 8% | 10% |
| digits only (`0010`, `11`, `0624`) | 12% | 11% | 4% | 11% | 8% | 55% |
| other (`N`, `70%`, `-100`, ...) | 0.2% | 0.2% | 0.2% | 0.6% | 0.3% | 0.3% |

**Aug/2021: more decimals.** The share of decimal values jumped in Aug/2021 (Hb 44% → 61% in
one month; 38% in 2021 and 66% in 2022 for the year): before, many more values were bare
digits. Compare lab values across 2021 with care.

Bare digits are ambiguous: Hb `0010` is probably 10 g/dL, albumin `0038` is probably 3.8 g/dL
written without the point, `9999` is a filler. A practical reading is to replace `,` with `.`,
cast, and keep only plausible values; with these ranges, 56–77% of rows since 2024 have a usable value:

| Lab | Unit | Plausible range | Usable since 2024 | Median |
|---|---|---|---|---|
| Hb | g/dL | 3–20 | 76% | 10.6 |
| Phosphorus | mg/dL | 0.5–20 | 77% | 4.9 |
| Albumin | g/dL | 1–6 | 64% | 3.9 |
| Kt/V | – | 0.3–5 | 56% | 1.38 |
| URR | % | 20–95 | 56% | 69.3 |
| PTH | pg/mL | 1–5000 | 62% | 293 |

```sql
-- Haemoglobin of haemodialysis patients by state, May/2026 (plausible values only)
SELECT uf, COUNT(*) AS com_valor, ROUND(MEDIAN(hb), 1) AS hb_mediana,
       ROUND(100 * AVG((hb < 10)::INT), 1) AS pct_hb_abaixo_10
FROM (SELECT uf, TRY_CAST(REPLACE(ATD_HB, ',', '.') AS DOUBLE) AS hb
      FROM atd WHERE competencia = 202605 AND AP_PRIPAL IN ('0305010107', '0305010115'))
WHERE hb BETWEEN 3 AND 20
GROUP BY 1 ORDER BY 1;
```

### Added by this package

| Column | Type | Meaning |
|---|---|---|
| `_ARQUIVO_ORIGEM` | text | DATASUS file the row came from (`ATDSP2605.dbc`). |
| `competencia` | `INTEGER` | Partition: month of the file (`YYYYMM`); equals `AP_MVM`. |
| `uf` | text | Partition: state of the file (the dialysis facility's state). |

## Joins

- `AP_PRIPAL` → `procedimentos.codigo` (procedure name and SIGTAP price per session). Every
  code is in the current SIGTAP.
- `AP_CIDCAS` → `cid10.codigo` (the only diagnosis filled; `AP_CIDPRI` is always `0000`).
- `uf` → `ufs.uf`; `LEFT(AP_MUNPCN, 2)` → `ufs.ibge` (patient's state of residence).
- `AP_AUTORIZ`, `AP_CMP` → `pa.PA_AUTORIZ`, `pa.PA_CMP` (same `competencia` and `uf`) for the
  sessions (`PA_QTDAPR`), lab tests, materials and values.
- `AP_CNSPCN` → AN (same patient before Aug/2014) and the other APAC tables (e.g. `am` for
  the same patient's anaemia or mineral-bone medicines, `ad` for kidney-transplant follow-up).
- No professional (CBO) column, so no join to `ocupacoes`.

## Known quirks and layout changes

- **One layout since Aug/2014, two column sets.** 64 columns until Jun/2016; `AP_NATJUR`
  added from Jul/2016 (65), as the *last* column, after the `ATD_` ones. Checked on the header
  of one SP file per year 2014–2026, the change months (`ATDSP1606`/`ATDSP1607`) and
  `ATDAC2608`. `AP_VL_AP` is a numeric (`N`) field 20 wide; the record is 303 bytes (299
  before Jul/2016). The procedure mix, `AP_TPAPAC` and rows per APAC (2.5) are the same every
  year: no change of meaning like AR's in 2019.
- **AN → ATD in 2014**: Jun/Jul/2014 are missing from both files, see
  [from AN to ATD](#from-an-to-atd-2014).
- **No diagnosis** in `AP_CIDPRI`/`AP_CIDSEC` (always `0000`).
- **Lab values are free text** and changed format in Aug/2021, see [lab values](#lab-values).
- **Patient IDs missing** on most rows from May/2026 (see [patients](#patients)).
- `AP_TPATEN` is always `10`; `AP_MNDIF` is always `1` (wrong); `AP_TPAPAC` has a `4`;
  `ATD_CARACT = 1` (new case) is kept long after the start of dialysis.
- **Conversion size.** The largest file (SP, about 30,000 rows) needs a 9 MB temporary DBF
  and converts in about a second.

## Examples

```sql
-- Patients on chronic dialysis per month, by type (before the CNS gap of 2024-2026)
SELECT competencia,
       COUNT(DISTINCT AP_CNSPCN) FILTER (AP_PRIPAL IN ('0305010107', '0305010115', '0305010204')) AS hemodialise,
       COUNT(DISTINCT AP_CNSPCN) FILTER (AP_PRIPAL IN ('0305010166', '0305010026')) AS dialise_peritoneal
FROM atd
WHERE competencia BETWEEN 201501 AND 202312
  AND AP_CNSPCN IS NOT NULL AND AP_CNSPCN <> '{{{{{{{{{{{{{{{'
GROUP BY 1 ORDER BY 1;

-- Vascular access and transplant list of haemodialysis patients, by state, one month
SELECT uf, COUNT(*) AS pacientes,
       ROUND(100 * AVG((ATD_ACEVAS = '1')::INT), 1) AS pct_fistula,
       ROUND(100 * AVG((ATD_ACEVAS = '2')::INT), 1) AS pct_cateter_curta,
       ROUND(100 * AVG((ATD_SITTRA = '1' AND ATD_SEAPTO = '1')::INT), 1) AS pct_lista_transplante
FROM atd
WHERE competencia = 202605 AND AP_PRIPAL IN ('0305010107', '0305010115')
GROUP BY 1 ORDER BY 1;

-- Sessions and secondary procedures of the dialysis APACs in a month (fetch both: -T pa,atd)
SELECT a.AP_PRIPAL, p.PA_DOCORIG, p.PA_PROC_ID, SUM(p.PA_QTDAPR) AS qtd, ROUND(SUM(p.PA_VALAPR), 2) AS valor
FROM atd a
JOIN pa p ON p.PA_AUTORIZ = a.AP_AUTORIZ AND p.PA_CMP = a.AP_CMP
         AND p.competencia = a.competencia AND p.uf = a.uf
WHERE a.uf = 'SE' AND a.competencia = 202605
GROUP BY ALL ORDER BY valor DESC LIMIT 15;
```
