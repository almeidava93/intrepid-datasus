# amp — APAC Acompanhamento Multiprofissional (chronic kidney disease before dialysis), Mar/2016 onward

**Source:** `AMPufaamm.dbc` files in `ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados`
(e.g. `AMPSP2605.dbc`). No state is split into parts. Careful: `AMPA2605.dbc`, `AMPE…`, `AMPI…`,
`AMPB…` and `AMPR…` are **AM** (medicines) files of Pará, Pernambuco, Piauí, Paraíba and Paraná;
AMP files have the state after the `P` (`AMPPA2605.dbc`). `datasus` matches the full name, so it
never mixes them.
**Coverage:** Mar/2016 to the latest month DATASUS has released (Aug/2026 when this was written), but
only in the states that bill it: **14 states**, each from its own start month. RO alone until
Sep/2017 (the 2016 files are RO's, and there is no Jul/2016 file); 12–13 states a year from 2022.
A missing state-month means nothing was billed there: 13 states (AC, AL, AM, AP, CE, ES, GO, MT,
PB, PI, RN, RR, TO) have no AMP file at all, and RJ only Aug/2026.
**Size on the FTP** (Nov/2026): 903 files, **12.4 MB** of `.dbc`, 204,061 rows, 157,018 APACs,
R$ 12.5 M. The largest file (`AMPMG2603.dbc`) has 1,469 rows; the median file 72. Parquet takes about
**1.85×** the `.dbc` size (23.0 MB): the files are so small (14 KB) that Parquet's per-file overhead
dominates.
**Fetch:** `uv run datasus fetch -T amp -s SP -f 2025`, or everything with `-s all -f 201603 -t 202608`
(in Nov/2026, three parallel fetches of different year ranges took 8 minutes).

AMP holds the APACs of the **multiprofessional follow-up of chronic kidney disease (CKD) before
dialysis** (*acompanhamento multiprofissional em doença renal crônica*): per SIGTAP, the
multiprofessional follow-up and the diagnostic tests of a patient whose kidneys are failing but who
does not dialyse yet. There are two procedures, both FAEC:

| `AP_PRIPAL` | SIGTAP name | Rows | Price |
|---|---|---|---|
| `0301130051` | *Acompanhamento multiprofissional em DRC estágio 04 pré-diálise* (CKD stage 4, eGFR 15–29) | 119,841 (59%) | R$ 61 → 122 |
| `0301130060` | *Acompanhamento multiprofissional em DRC estágio 05 pré-diálise* (stage 5, eGFR below 15, not on dialysis) | 84,220 (41%) | R$ 61 → 122 |

Besides the 46 `AP_` columns shared by every APAC type, AMP has 19 `AMP_` columns from the
multiprofessional *laudo*: referral for a fistula or a catheter, height, weight, vaccinations
(influenza, dT, pneumococcal, hepatitis B), phosphorus, albumin, PTH, HIV/HCV/HBsAg, and the use of
ACE inhibitors and ARBs. **But the columns are named after the dialysis laudo of
[ATD](atd.md), and each holds the field that follows its namesake's position**, so almost every
column name is wrong: see [laudo columns](#laudo-columns-amp_).

When the kidneys fail, the same patient (same encoded ID) goes on to dialysis in **[ATD](atd.md)**,
gets a fistula in **[ACF](acf.md)** and catheters in **[AD](ad.md)**: see
[AMP, dialysis and the fistula](#amp-dialysis-and-the-fistula).

Read [APAC file types](apac.md) first: it explains authorisation, validity, continuation and the
patient identifier, and describes the `AP_` columns.

## One row is one patient-month of follow-up

Each row is one month of follow-up of one patient on one APAC. The two stages are billed
differently (from 2019; until 2018 the other way round):

- **Stage 4** APACs are **single** (`AP_TPAPAC = 3`, `AP_MOTSAI = 15`, discharge with return): one
  row per APAC, a new APAC at each visit, typically one to three months apart (three months is the
  most common gap).
- **Stage 5** APACs run for **three months**: an initial row (`1`) and two continuations (`2`,
  `AP_MOTSAI = 21`), under the same `AP_AUTORIZ`. 57% of stage 5 APACs have the three rows.

So count patients or patient-months, not APACs, when comparing the stages. From 2022, 7–14% of rows a
year are late billings (`AP_CMP` before `AP_MVM`); group by `AP_CMP` for a series by month of care.

Rows by year of the file (= the header row counts of all 903 files), and states billing:

| 2016 (Mar–Dec) | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (Jan–Aug) |
|---|---|---|---|---|---|---|---|---|---|---|
| 26 | 354 | 1,643 | 3,337 | 3,867 | 8,341 | 17,201 | 30,131 | 43,737 | 55,321 | 40,103 |
| 1 state | 4 | 5 | 7 | 8 | 9 | 12 | 11 | 12 | 12 | 13 |

A young, fast-growing table: rows doubled each year to 2023 as states joined. SP (26%), MG (24%) and
SC (19%) have 70% of the rows; then BA, PR, PE, RS, MA, MS, DF, PA, RO, SE and RJ. It is **not a
national series**: most states bill no AMP at all. The 180,712 rows with a patient ID are 34,946
distinct patients (encoded `AP_CNSPCN`), followed for a median of 5 months (first to last row); 4,333
had both stages, and 3,263 went from stage 4 to stage 5. Patients are 51% men; the median age on the rows is 69,
and 73% of rows are of patients aged 60 or older.

## How amp relates to pa (double counting)

**Every `amp` row is one `pa` row with `PA_DOCORIG = 'P'` and `PA_PROC_ID` `0301130051` or
`0301130060`** (`PA_TPFIN = '04'`, FAEC), and `AP_VL_AP` equals the sum of `PA_VALAPR` over the APAC's
`pa` rows. And the other way round, every such `pa` row is in `amp`. Join on `AP_AUTORIZ = PA_AUTORIZ`
**and** `AP_CMP = PA_CMP`, within the same `competencia` and `uf`.

| | RO 2016-05 | SE 2019-01 | MS 2021-12 | AC 2026-05 | RO 2015-12 |
|---|---|---|---|---|---|
| `amp` rows | 11 | 26 | 39 | no file | before AMP |
| … with exactly one `pa` `P` row, same procedure and value | 11 | 26 | 39 | | |
| `pa` `P` rows with `PA_PROC_ID` `0301130051`/`0301130060` | 11 | 26 | 39 | 0 | 0 |
| `pa` `S` rows of these APACs | 0 | 0 | 55 | | |
| `SUM(AP_VL_AP)` = `SUM(PA_VALAPR)` | R$ 0 | R$ 1,586 | R$ 2,379 | | |

The 55 `S` rows of MS (Dec/2021) are the follow-up's laboratory tests (urea, creatinine, calcium,
potassium, blood count, ...) recorded at R$ 0, so the APAC's value is its `P` row. `AP_TIPPRE`,
`AP_TPUPS`, `AP_SEXO`, `AP_MUNPCN` and `AP_CIDPRI` (`0000` in both) equal `pa`'s columns on every
matched row; `pa`'s `PA_NAT_JUR` is filled where `AP_NATJUR` is empty.

The procedures exist only in AMP among the APAC tables: they are not in [AD](ad.md) (checked in MS,
Jan/2016–Aug/2026), and `pa` has none before AMP starts (RO, Dec/2015) or in a state without AMP
files (AC, May/2026).

!!! danger "Never add `amp` to `pa`"
    Each AMP row is already a `pa` row.

## AMP, dialysis and the fistula

`AP_CNSPCN` is encoded the same way in AMP, [ATD](atd.md), [ACF](acf.md) and [AD](ad.md), so it follows
a patient from pre-dialysis follow-up to dialysis. AMP starts in Mar/2016, after [AN](an.md) ended
(Jul/2014), so it never overlaps AN. The counts below use **MS and SC** (ATD and ACF fetched for
Aug/2014–Aug/2026; AD for MS from Jan/2016) and the AMP patients first seen until Mar/2024 (while the
patient ID was complete; see [patients](#patients)). That is 3,620 patients.

**Who is in AMP.** 3.9% were already in ATD (on dialysis) before their first AMP month: the rest are
true pre-dialysis patients. By Aug/2026, 30.6% had started dialysis (ATD). The stage matters: of the
patients first seen in 2019–2022 and not yet on dialysis, **64% of those with a stage 5 row started
dialysis later (51% within two years)**, against 11% of the stage-4-only patients.

**Referral for a fistula.** The laudo's *encaminhado para FAV* flag (the first character of
`AMP_DTINI`) is `S` at some point for 12% of the patients. Of the patients first seen in 2019–2023:

| Referred for a fistula | Patients | With an ACF fistula, ever | … made after the first AMP month and before dialysis | Started dialysis (ATD) |
|---|---|---|---|---|
| yes | 365 | 91.8% | 68.8% | 76.7% |
| no | 2,552 | 22.0% | 13.6% | 26.5% |

The fistula follows the referral closely: of the referred patients whose ACF fistula came after the
first referral and before dialysis, 78% had it in the month of that referral and 93% within a month. **AMP patients start
dialysis with a fistula far more often than other patients**: at their first ATD month,
`ATD_ACEVAS` is a fistula (`1`) for 43% (and for 73% of those with an ACF fistula before dialysis),
a short-term catheter for 34% and a long-term catheter for 23%. Among all new haemodialysis patients,
only about 1 in 10 has an ACF fistula by the month dialysis starts (see
[ACF, dialysis and AD](acf.md#acf-dialysis-and-ad)).

**Few dialysis patients come through AMP.** Of the new dialysis patients in MS (first ATD month in
2020–2024, dialysis started within three months), 1.5–3% had an AMP row before; in SC the share rose
from 1% (2020) to 9% (2022), 15% (2023) and 18% (2024). AMP is a small programme, not the route of
most patients into dialysis.

**After dialysis starts**, 15% of the AMP rows of MS and SC are of patients already in ATD: the
follow-up is billed for some months after the first dialysis (or the patient briefly dialysed before).

**Catheter referral and AD.** The *encaminhado para implante de cateter* flag (`AMP_DTCLI`) is rare
(4% of rows, 2.5% of the MS patients) and does not predict an AD catheter: none of the 15 MS patients
referred (first seen 2018–2024) has an AD access APAC afterwards, while 37 others had a Tenckhoff
catheter (`0418010080`, peritoneal dialysis) and 12 a long-term haemodialysis catheter (`0418010048`).

## amp vs amp_raw

`amp_raw` holds every column as text exactly as DATASUS publishes it. `amp` is the same data with
`AP_VL_AP` cast to `DOUBLE` (with `TRY_CAST`). Everything else stays text: the laudo columns are
packed fields and lab values typed with commas (see below).

## Columns

The shared `AP_` columns are described on the [APAC page](apac.md#shared-columns); all 46 are in
AMP under their usual names. Source of the layout: the AMP laudo's *parte variável* (part 19,
*Acompanhamento Multiprofissional em D.R.C.*) in DATASUS's *Layout da interface texto do APAC e do
SIA — layout interno* (Apr/2014), which gives the fields, their positions and their codes. The
*Informe Técnico SIASUS* (Jul/2019) has no AMP section, and `TAB_SIA.zip` (`SIASUS/200801_/Auxiliar`,
Oct/2026) has no TabWin definition for AMP. Values were checked on every row (204,061).

### What the shared columns hold in AMP

| Column | Notes for AMP |
|---|---|
| `AP_PRIPAL` | `0301130051` (stage 4) 59%, `0301130060` (stage 5) 41%. Never `NULL`. |
| `AP_VL_AP` | R$ **0.00 until Oct/2018**, **61.00** from Nov/2018, **122.00** from Mar/2026 (late bills of earlier months keep 61.00). 0.00 on some rows from 2019 too: 3–8% a year in 2019–2023, 11–14% in 2024–2026. Per row (month): sum over the rows of an APAC. |
| `AP_TPAPAC` | `3` 58%, `2` 23%, `1` 19%: see [one row](#one-row-is-one-patient-month-of-follow-up). |
| `AP_TPATEN` | **Always `11`**. |
| `AP_DTINIC`, `AP_DTFIM` | Two months apart (a three-month validity) on 72% of rows, including most single stage 4 APACs; the same month on 25%; eleven months apart on 3%. |
| `AP_MOTSAI` | `15` (discharge with return for follow-up) 40%, `21` (continues, nature of the disease) 35%, `18` 9%, `12` 7%, `51` (closed administratively) 7%, `26`, `11`, `31`; 144 deaths. |
| `AP_CIDPRI`, `AP_CIDSEC` | **Always `0000`**. |
| `AP_CIDCAS` | `0000` on 92%; otherwise `N180` (end-stage kidney disease) 7.7%, `N189`, `N188`, `N083`, `N139`, `I120`, ... |
| `AP_TPUPS` | `36` specialised clinic 60%, `05` general hospital 22%, `04` polyclinic 10%, `39` diagnostic support unit 5%, `07` specialised hospital 3%. |
| `AP_TIPPRE` | **Always `00`**. |
| `AP_CATEND` | `01` (elective) 99.9%. |
| `AP_CONDIC` | `PG` 53%, `EP` 47%. |
| `AP_APACANT` | Zeros on 98% (12 or 13 zeros); another APAC number on 2%. |
| `AP_MNDIF` | **Always `1`** (wrong, as in the other APAC types); compare `AP_MUNPCN` with `AP_UFMUN` (different on 41% of rows). `AP_UFDIF` is correct (`1` on 0.4%). |
| `AP_COIDADE` | `4` (years) 99.7%; 301 rows in days or months (`2`, `3`), probably typing errors, and 219 of 100 or more. |
| `AP_RACACOR` | `01` white 57%, `03` brown 31%, `02` black 8%, `04` 3%, `99` 2%, `05` 57 rows (`AP_ETNIA` filled on those). |
| `AP_CNSPCN` | Encoded. See [patients](#patients). |
| `AP_NATJUR` | In the files from **Aug/2016** (the last column), but **always empty** (`NULL`). |

### Laudo columns (`AMP_`)

The 19 `AMP_` columns are named after the 19 columns of ATD's dialysis laudo (`ATD_CARACT` …
`ATD_SEPERI`, with `AMP_DTINI` for `ATD_DTPDR`), with their widths. They hold the multiprofessional
laudo, but **each column holds the laudo field that comes after the one it should**: the column for
the start date holds the next 8 characters (the two referrals, height and weight); the next column
the catheter referral; and so on. Fields wider than their column lose characters: the start date is
lost, and the haemoglobin keeps only its first character. The mapping was checked on every row:
`AMP_DTCLI`, `AMP_ACEVAS` and `AMP_MAISNE` always equal the 2nd, 3rd and 6th characters of
`AMP_DTINI`. The values match the laudo's codes (`R`/`N` for vaccination and anti-HBs, `S`/`N`/`I`
for the vaccines and medicines, `P`/`N` for the serologies), and the lab medians are plausible for
CKD: phosphorus 4.0 mg/dL, albumin 4.0 g/dL, PTH ~130 pg/mL.

| Column | Width | Name suggests | What it holds (laudo part 19 field) | Values |
|---|---|---|---|---|
| `AMP_CARACT` | 1 | characteristic of the treatment | the same: 1 new case, 2 continuing, 3 in transit, 4 change of facility (`APA_CARACT`) | `2` on 99.9%: not informative. |
| `AMP_DTINI` | 8 | start date | **referred for a fistula** (pos. 1, `S`/`N`), **referred for a catheter** (pos. 2), **height** cm (pos. 3–5), **weight** kg (pos. 6–8) (`APA_ENCFAV`, `APA_ENCCAT`, `APA_ALTURA`, `APA_PESO`). The laudo's start of treatment (`APA_DTINIC`) is not in the file. | `NN170070`, `SN178566`, `NN000000` (not informed), `NN0  0`; trailing spaces trimmed (`NN15053` = 150 cm, 53 kg). Fistula referral on 9% of stage 4 and 27% of stage 5 rows; it peaked at 21% of rows in 2022. Height 100–220 cm on 67% of rows (median 165), weight 25–250 kg on 60% (median 70). |
| `AMP_DTCLI` | 8 | start at this facility | referred for a **catheter** implant (`APA_ENCCAT`), 1 character | `S` 4%, `N`. Always the 2nd character of `AMP_DTINI`. |
| `AMP_ACEVAS` | 1 | vascular access | first digit of the **height** | `1`, `0` (not informed). |
| `AMP_MAISNE` | 1 | followed by a nephrologist | first digit of the **weight** | `0` 76% (not informed, or a weight typed with a leading zero, `070`), `7`, `6`, `5`, `1`, ... |
| `AMP_SITINI` | 1 | situation at the start of dialysis | **vaccination status** (`APA_SITVAC`) | `R` up to date 42%, `N` not up to date. |
| `AMP_SITTRA` | 1 | transplant situation | **anti-HBs** (hepatitis B vaccine response, `APA_ANTHBS`) | `R` reactive 22%, `N` not reactive 62%, `NULL` 16%. The layout asks for it only when vaccination is up to date (`R`: always filled), but 72% of the `N`-status rows have it too. |
| `AMP_SEAPTO` | 1 | on the transplant list | vaccinated against **influenza** (`APA_INFLUE`) | `S` 24% (2023–2026), `N`, `I` unknown 21%. |
| `AMP_HB` | 4 | haemoglobin | vaccinated with **dT** (diphtheria, tetanus; `APA_DIFTET`) | `S` 23% (2023–2026), `N`, `I` 22%. |
| `AMP_FOSFOR` | 4 | phosphorus | vaccinated against **pneumococcus** (`APA_PNEUMO`) | `S` 17% (2023–2026), `N`, `I` 27%. |
| `AMP_KTVSEM` | 4 | Kt/V | first character of the **haemoglobin** (`APA_HB`) only | `0` 55% (not informed or a leading zero), `1` 35% (10–19 g/dL), `9`, `8`, ...; `,` and letters on 1%. The rest of the value is lost. |
| `AMP_TRU` | 4 | urea reduction ratio | **phosphorus**, mg/dL (`APA_FOSFOR`) | As typed (`04,1`, `4`, `0000`, `000,`): above zero on 50% of rows, median 4.0. |
| `AMP_ALBUMI` | 4 | albumin | **albumin**, g/dL (`APA_ALBUMI`, optional) | Above zero on 42%, median 4.0; `NULL` on 17%. |
| `AMP_PTH` | 4 | PTH | **PTH**, pg/mL (`APA_PTH`, optional) | Above zero on 46%, median ~130; `NULL` on 17%. |
| `AMP_HIV` | 1 | anti-HIV | the same (`APA_HIV`) | `P` 0.4%, `N`; `NULL` 9%. |
| `AMP_HCV` | 1 | anti-HCV | the same (`APA_HCV`) | `P` 0.3%, `N`; `NULL` 9%. |
| `AMP_HBSAG` | 1 | HBsAg | the same (`APA_HBSAG`) | `P` 0.2%, `N`; `NULL` 9%. |
| `AMP_INTERC` | 1 | admitted to hospital | uses an **ACE inhibitor** (IECA, `APA_IECA`) | `S` 8% (2023–2026), `N`, `I` 24%. |
| `AMP_SEPERI` | 1 | peritonitis | uses an **angiotensin receptor blocker** (ARB, BRA, `APA_BRA`) | `S` 17% (2023–2026), `N`, `I` 24%. |

To read the laudo, unpack `AMP_DTINI` and rename the rest:

```sql
SELECT AP_AUTORIZ, AP_CMP, AP_PRIPAL,
       substr(AMP_DTINI, 1, 1) = 'S'                       AS encaminhado_fav,
       AMP_DTCLI = 'S'                                     AS encaminhado_cateter,
       TRY_CAST(NULLIF(substr(AMP_DTINI, 3, 3), '000') AS INT)       AS altura_cm,
       TRY_CAST(NULLIF(trim(substr(AMP_DTINI, 6, 3)), '000') AS INT) AS peso_kg,
       AMP_SITINI  AS situacao_vacinal,  AMP_SITTRA AS anti_hbs,
       AMP_SEAPTO  AS influenza,         AMP_HB     AS dupla_adulto,  AMP_FOSFOR AS pneumococica,
       TRY_CAST(NULLIF(replace(AMP_TRU,    ',', '.'), '') AS DOUBLE) AS fosforo,
       TRY_CAST(NULLIF(replace(AMP_ALBUMI, ',', '.'), '') AS DOUBLE) AS albumina,
       TRY_CAST(NULLIF(replace(AMP_PTH,    ',', '.'), '') AS DOUBLE) AS pth,
       AMP_HIV, AMP_HCV, AMP_HBSAG,
       AMP_INTERC  AS ieca,              AMP_SEPERI AS bra
FROM amp;
```

(A height or weight of `0` or an absurd value means not informed; a lab value of 0 too.)

### Added by this package

| Column | Type | Meaning |
|---|---|---|
| `_ARQUIVO_ORIGEM` | text | DATASUS file the row came from (`AMPSP2605.dbc`). |
| `competencia` | `INTEGER` | Partition: month of the file (`YYYYMM`); equals `AP_MVM`. |
| `uf` | text | Partition: state of the file (the facility's state). |

## Patients

The encoded CNS (`AP_CNSPCN`) is filled on every row until Mar/2024. Since then a growing share is
`NULL` or the placeholder `{{{{{{{{{{{{{{{`, as in ATD, ACF and the other APAC types (see
[APAC](apac.md)):

| until Mar/2024 | Apr–Oct/2024 | Nov/2024–Feb/2026 | Mar/2026 | Apr/2026 | May/2026 | Jun/2026 | Jul/2026 | Aug/2026 |
|---|---|---|---|---|---|---|---|---|
| 0% | 0–1.4% | 4–7% | 9.0% | 18.7% | 73.1% | 88.9% | 99.0% | **99.6%** |

In Jan–Aug/2026 it is missing on 39% (MS, PA) to 72% (PE, PR) of each state's rows (and on all the
few rows of SE and RJ). Exclude both values
(`AP_CNSPCN IS NOT NULL AND AP_CNSPCN <> '{{{{{{{{{{{{{{{'`) and don't follow patients from 2026 on;
count rows, which are complete.

## Joins

- `AP_PRIPAL` → `procedimentos.codigo` (two codes: `0301130051`, `0301130060`).
- `AP_CIDCAS` → `cid10.codigo` (`AP_CIDPRI` and `AP_CIDSEC` are always `0000`).
- `uf` → `ufs.uf`; `LEFT(AP_MUNPCN, 2)` → `ufs.ibge` (patient's state of residence).
- `AP_AUTORIZ`, `AP_CMP` → `pa.PA_AUTORIZ`, `pa.PA_CMP` (same `competencia` and `uf`).
- `AP_CNSPCN` → `atd.AP_CNSPCN` (the patient's later dialysis), `acf.AP_CNSPCN` (fistula),
  `ad.AP_CNSPCN` (catheters, grafts), until about Mar/2026.
- No professional (CBO) column, so no join to `ocupacoes`.

## Known quirks and layout changes

- **One DBF layout, two column sets.** 64 columns (record 299 bytes) in the RO files of Mar–Jun/2016;
  65 with `AP_NATJUR` last (303 bytes) from Aug/2016. Checked on the header of **every** file.
  `AP_VL_AP` is a numeric (`N`) field 20 wide; everything else is text.
- **The laudo columns are misnamed and shifted** (named after ATD's laudo, each holding the next
  field): see [laudo columns](#laudo-columns-amp_). The start-of-treatment date and most of the
  haemoglobin are lost; height and weight are packed into `AMP_DTINI`.
- **`AP_NATJUR` always empty**, although the column is there from Aug/2016.
- **Two procedures**: `AP_TPATEN` always `11`, `AP_TIPPRE` always `00`, `AP_CIDPRI`/`AP_CIDSEC`
  always `0000`, `AP_MNDIF` always `1` (wrong).
- **Value 0 until Oct/2018**, then R$ 61, then R$ 122 from Mar/2026.
- **Few states, each with its own start**: not a national series; see the coverage above.
- **Patient ID missing from 2026**, 99.6% in Aug/2026; see [patients](#patients).
- **Conversion size.** The largest file (1,469 rows) converts in under a second.

## Examples

```sql
-- Patients in follow-up per year and stage (to 2025: the patient ID is complete until early 2026)
SELECT LEFT(AP_CMP, 4) AS ano, AP_PRIPAL,
       COUNT(*) AS linhas,
       COUNT(DISTINCT AP_CNSPCN) FILTER (AP_CNSPCN <> '{{{{{{{{{{{{{{{') AS pacientes,
       ROUND(100 * AVG((substr(AMP_DTINI, 1, 1) = 'S')::INT), 1) AS pct_encaminhado_fav
FROM amp WHERE AP_CMP < '202601' GROUP BY ALL ORDER BY 1, 2;

-- Pre-dialysis patients referred for a fistula: did they get one (ACF) before dialysis (ATD)?
WITH a AS (SELECT AP_CNSPCN, MIN(strptime(AP_CMP, '%Y%m')) AS primeiro_amp,
                  bool_or(substr(AMP_DTINI, 1, 1) = 'S') AS encaminhado_fav
           FROM amp WHERE AP_CNSPCN <> '{{{{{{{{{{{{{{{' AND competencia <= 202403 GROUP BY 1),
     f AS (SELECT AP_CNSPCN, MIN(strptime(AP_CMP, '%Y%m')) AS fav FROM acf GROUP BY 1),
     d AS (SELECT AP_CNSPCN, MIN(strptime(AP_CMP, '%Y%m')) AS dialise FROM atd GROUP BY 1)
SELECT encaminhado_fav, COUNT(*) AS pacientes,
       ROUND(100 * AVG(COALESCE(fav >= primeiro_amp AND (dialise IS NULL OR fav <= dialise), false)::INT), 1)
           AS pct_fav_antes_da_dialise,
       ROUND(100 * AVG(COALESCE(dialise >= primeiro_amp, false)::INT), 1) AS pct_iniciou_dialise
FROM a LEFT JOIN f USING (AP_CNSPCN) LEFT JOIN d USING (AP_CNSPCN)
WHERE dialise IS NULL OR dialise >= primeiro_amp   -- not yet on dialysis when first seen
GROUP BY 1;

-- Vaccination and labs of stage 5 patients by state, 2025
SELECT uf, COUNT(*) AS linhas,
       ROUND(100 * AVG((AMP_SITINI = 'R')::INT), 1) AS pct_vacinacao_regular,
       ROUND(100 * AVG((AMP_SEAPTO = 'S')::INT), 1) AS pct_influenza,
       MEDIAN(TRY_CAST(replace(AMP_TRU, ',', '.') AS DOUBLE))
           FILTER (TRY_CAST(replace(AMP_TRU, ',', '.') AS DOUBLE) > 0) AS fosforo_mediano
FROM amp WHERE AP_PRIPAL = '0301130060' AND AP_CMP LIKE '2025%'
GROUP BY 1 ORDER BY 2 DESC;
```
