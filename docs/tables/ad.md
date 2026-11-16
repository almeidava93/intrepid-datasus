# ad — APAC Laudos Diversos (other APAC procedures), 2008 onward

**Source:** `ADufaamm.dbc` files in `ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados`
(e.g. `ADSC2605.dbc`). No state is split into parts.
**Coverage:** Jan/2008 to the latest month DATASUS has released (Aug/2026 when this was
written). Every state has a file every month (AP and RR miss one month each).
**Size on the FTP** (Nov/2026): 6,046 files, about **3.25 GB** of `.dbc`, 61.4 M rows. The
largest file, `ADSP2607.dbc`, has 110,306 rows; small states have a few hundred to a few
thousand a month. Parquet takes about 0.58× the `.dbc` size (1.90 GB for everything).
**Fetch:** `uv run datasus fetch -T ad -s SC -f 2024`, or the whole history with
`-s all -f 2008 -t 2026`. Speed depends on the FTP (some files take 25–30 s to start): in
Nov/2026 one fetch with `-w 8` did about 25 files a minute, so three fetches of different
year ranges into separate stores, run in parallel, took 26 minutes.

Each row is **one APAC billed in one month** for a procedure that needs an APAC but has no
laudo of its own: the *laudo diverso* (miscellaneous request form). There are **no
`AD_` columns**: the file has only the 46 `AP_` columns shared by every APAC type, so
what a row is about comes entirely from its procedure (`AP_PRIPAL`) and diagnosis
(`AP_CIDPRI`). In practice AD is mostly **eye care** (cataract surgery, retina treatment, OCT),
**hearing** (diagnosis, hearing aids, follow-up), **transplant** follow-up and organ/tissue
donation, **cardiac catheterisation**, PET-CT, orthoses such as wheelchairs, and until 2012
**CAPS mental health** care. See [what is in it](#what-is-in-ad) below.

Read [APAC file types](apac.md) first: it explains authorisation, validity, monthly
continuation and the patient identifier, and describes the `AP_` columns.

## What is in AD

Join `AP_PRIPAL` to `procedimentos` and group by `grupo` / `subgrupo` (the first 2 and 4
digits of the code) to see what kind of care the rows are. Whole history, Jan/2008–Aug/2026
(61.4 M rows, R$ 22.3 bn):

| Subgroup (code) | SIGTAP name | Rows | % rows | R$ M | % value |
|---|---|---|---|---|---|
| `0301` | Consultations / care / follow-up (CAPS until 2012; hearing aid follow-up, burns, home ventilation, rare diseases) | 18.7 M | 30.5% | 2,748 | 12.3% |
| `0405` | Eye surgery (cataract, YAG capsulotomy, laser photocoagulation, glaucoma) | 15.4 M | 25.1% | 9,098 | 40.8% |
| `0211` | Diagnosis in specialties (hearing, cardiac catheterisation, OCT) | 10.3 M | 16.8% | 2,245 | 10.1% |
| `0506` | Pre- and post-transplant follow-up | 9.4 M | 15.3% | 1,189 | 5.3% |
| `0701` | Orthoses, prostheses and special materials (hearing aids, wheelchairs, cochlear implant processors) | 3.1 M | 5.1% | 4,005 | 18.0% |
| `0303` | Clinical treatments (retina treatment with intravitreal medicine, from 2019) | 1.0 M | 1.7% | 602 | 2.7% |
| `0309` | Specialised therapies (extracorporeal lithotripsy) | 0.9 M | 1.5% | 622 | 2.8% |
| `0418` | Nephrology surgery (dialysis access: long-term catheter `0418010048`, Tenckhoff `0418010080`, fistulas with a graft `0418010013`/`0418010021`; plain fistula creation `0418010030` until Jul/2014, then [ACF](acf.md#acf-dialysis-and-ad)) | 0.6 M | 1.1% | 355 | 1.6% |
| `0307` | Dental treatments (dentures: moulding/maintenance) | 0.4 M | 0.7% | 74 | 0.3% |
| `0409` | Genitourinary surgery (vasectomy, ...) | 0.4 M | 0.7% | 134 | 0.6% |
| `0206` | Tomography (PET-CT, from 2015) | 0.3 M | 0.5% | 633 | 2.8% |
| `0504`, `0503`, `0505` | Tissue processing (cornea), donation, tissue/cell transplant | 0.5 M | 0.8% | 498 | 2.2% |
| others | `0414` oral/maxillofacial, `0201`, `0404`, `0408`, `0304` (nuclear medicine), ... | 0.2 M | 0.3% | 77 | 0.3% |
| `NULL` | no procedure (see [quirks](#known-quirks-and-layout-changes)) | 23,613 | 0.0% | 3 | 0.0% |

The largest procedures in 2025 (4.71 M rows, R$ 2.17 bn):

| `AP_PRIPAL` | Procedure | Rows | R$ M |
|---|---|---|---|
| `0405050372` | Phacoemulsification with foldable intraocular lens (cataract) | 1,045,308 | 841.6 |
| `0211060283` | Optical coherence tomography (OCT) | 609,966 | 30.0 |
| `0506010104` | Post-kidney-transplant follow-up | 424,749 | 72.5 |
| `0303050233` | Medical treatment of retinal disease (intravitreal injection) | 316,120 | 187.3 |
| `0405050020` | YAG laser capsulotomy | 277,612 | 42.1 |
| `0301070032` | Follow-up for hearing aid (AASI) fitting | 255,022 | 24.0 |
| `0211020010` | Cardiac catheterisation | 165,081 | 119.6 |
| `0211070319` | Selection and check of hearing aid benefit | 145,656 | 4.6 |
| `0211070092` | Assessment for diagnosis of hearing impairment | 136,923 | 13.4 |
| `0405030045` | Laser photocoagulation | 118,244 | 20.1 |
| `0701030143` | Hearing aid, behind-the-ear, type C | 51,492 | 100.8 |
| `0206010095` | PET-CT | 41,104 | 85.1 |
| `0701010223` | Motorised wheelchair | 8,234 | 45.8 |

Phacoemulsification alone is 22% of the rows and 39% of the value of 2025.

### How the mix changed

Share of rows (and of value) by kind of care, per year. *Hearing* = `021107`, `030107` and
`070103` (diagnosis, follow-up, hearing aids); *transplant* = group `05`; *cataract etc.* =
`040505` (anterior eye surgery).

| Year | Rows | Rows per APAC | CAPS (`030108`) | Cataract etc. | Other eye surgery | Retina injection | OCT | Hearing | Transplant | Cardiac cath. | Other |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2008 | 3.48 M | 1.77 | 61% (40%) | 7% (19%) | 1% | – | – | 12% (18%) | 8% (6%) | 3% (9%) | 7% |
| 2012 | 4.92 M | 1.71 | 62% (35%) | 10% (24%) | 1% | – | – | 11% (18%) | 8% (6%) | 3% (8%) | 5% |
| 2013 | 2.04 M | 1.15 | 0% | 26% (39%) | 4% | – | – | 27% (28%) | 22% (9%) | 7% (10%) | 14% |
| 2018 | 2.52 M | 1.15 | – | 29% (46%) | 4% | – | – | 27% (20%) | 24% (8%) | 5% (7%) | 11% |
| 2020 | 2.00 M | 1.19 | – | 25% (38%) | 4% | 0% | 2% | 24% (22%) | 28% (9%) | 5% (8%) | 12% |
| 2022 | 3.21 M | 1.12 | – | 33% (47%) | 4% | 2% (3%) | 6% (1%) | 22% (19%) | 19% (7%) | 4% (6%) | 10% |
| 2025 | 4.71 M | 1.11 | – | 31% (43%) | 4% | 7% (9%) | 13% (1%) | 17% (15%) | 15% (7%) | 4% (6%) | 9% |

Rows per year: 3.5 M (2008) → 4.9 M (2012) → **2.0 M (2013)** → 2.5 M (2018) → 2.0 M (2020,
pandemic) → 4.7 M (2025). The two changes that matter:

- **Jan/2013: CAPS mental health care left AD.** Until Dec/2012, 61–63% of AD rows were
  monthly follow-up in psychosocial care centres (`030108…`: intensive, semi-intensive and
  non-intensive care, for mental disorders, alcohol/drugs, children). These APACs ran for
  months, which is why rows per APAC were 1.7 until 2012 and 1.1 since. From Jan/2013 that care
  is billed on the RAAS (file type PS, [`ps`](ps.md), from Nov/2012; see
  [From AD to PS](ps.md#from-ad-to-ps-2013) for a continuous series), and AD rows fell from 367 k (Dec/2012)
  to 153 k (Jan/2013). **Don't compare AD totals across 2012/2013.**
- **2019 onward: new eye procedures.** OCT (`0211060283`) and intravitreal retina treatment
  (`0303050233`, anti-VEGF injections) appear in AD from Jan/Feb 2019 and grew to 13% and 7% of rows
  by 2025. Most of the growth since 2021 is eye care; hearing and transplant follow-up
  grew less, so their shares fell.

Smaller changes: post-transplant follow-up was one code for every organ (`0506010023`)
until Aug/2023 and is split by organ since Sep/2023 (`0506010104` kidney, `0506010112`
liver, ...); PET-CT is in AD from Jan/2015; locomotion aids (`070101`, wheelchairs) from
Jul/2013.

## One row is one APAC-month

Most AD procedures are single APACs (`AP_TPAPAC = 3`: 71–78% of rows each year since 2013): one row per
surgery, exam or device. Follow-up procedures run over several months (`1`, then `2`) with
the same `AP_AUTORIZ`: transplant follow-up, retina treatment, burns, home ventilation,
hearing aid follow-up before 2019 and CAPS until 2012. Since 2024, `0506` rows are 38% `1`,
51% `2`; `0303` rows 70% `1`, 30% `2`.

- **APACs:** `COUNT(*)` for one month; `COUNT(DISTINCT AP_AUTORIZ)` over several.
- **Procedures (surgeries, exams, devices):** `COUNT(*)` of the single-APAC codes, or, for
  quantities, `pa` (`PA_QTDAPR`), which also has the secondary procedures.
- **Patients:** `COUNT(DISTINCT AP_CNSPCN)`, but see [patients](#patients).

## How ad relates to pa (double counting)

**Every `ad` row is one `pa` row with `PA_DOCORIG = 'P'`** (the APAC's main procedure,
same code), and `AP_VL_AP` equals `SUM(PA_VALAPR)` over the APAC's `P` and `S` rows. Join on
`AP_AUTORIZ = PA_AUTORIZ` **and** `AP_CMP = PA_CMP`, within the same `competencia` and `uf`;
`(AP_AUTORIZ, AP_CMP)` is unique in every file (one exception: 2 rows in SC, Nov/2022).
Secondary procedures (`S` rows) are in `pa` only: hearing tests with a hearing aid,
OPM materials, transplant lab tests (`0501…`), ...

Checked on five state-months, before and after the CAPS change:

| | AC 2026-05 | SE 2026-05 | SE 2018-05 | SE 2012-01 | ES 2023-09 |
|---|---|---|---|---|---|
| `ad` rows | 943 | 1,755 | 460 | 3,259 | 7,426 |
| … with exactly one `pa` `P` row | 943 | 1,755 | 460 | 3,259 | 7,426 |
| … with the same procedure code | 943 | 1,755 | 460 | 3,259 | 7,263 ¹ |
| … `AP_VL_AP` = `SUM(PA_VALAPR)` over `P` + `S` | 943 | 1,755 | 460 | 3,259 | |
| `SUM(AP_VL_AP)` | R$ 421,269.20 | R$ 959,437.73 | R$ 484,463.81 | R$ 639,743.45 | |

¹ The other 163 have `AP_PRIPAL` `NULL`; `pa` has the retired codes `0506010023`/`0506010040`.

**No column of `pa` picks out the AD rows.** AD holds the APACs that are in no other APAC
file, but not all of them: `PA_TPFIN` is `04` or `06` (as for AQ, AR and dialysis), and
procedure groups are shared. In SE, May/2026, the `pa` `P` rows not in `ad` were AM medicines
(`0604`, 25,704), chemotherapy/radiotherapy (`0304`, 6,097), dialysis (`0305`, 1,559),
glaucoma follow-up (`0303`, 3,151; `030101`, 489), fistula creation (`0418010030`, 43: the
[ACF](acf.md) APACs, which AD held until Jul/2014) and the OCI care packages (`0903`, 61). So glaucoma APACs (`0301010102`, `030305001…`)
and OCI packages (`09…`) are **not** in AD, though they are neither AM, AQ, AR nor dialysis:
look for them in `pa`, or in the file types still to be added.

| You want | Use |
|---|---|
| All outpatient production, including these procedures | `pa` only |
| Value or volume of a procedure | `pa` (`PA_QTDAPR`, `PA_VALAPR`), which also has the secondary procedures |
| Authorisation, validity, exit reason, requesting facility, one row per APAC | `ad` |
| Both | join `ad` to `pa` on `AP_AUTORIZ` = `PA_AUTORIZ` and `AP_CMP` = `PA_CMP` |

!!! danger "Never add `ad` to `pa`"
    `ad`'s APACs and values are already in `pa`. `AP_VL_AP` is the value of the whole APAC
    (main plus secondary procedures): summing it with `pa`'s `S` rows counts them twice.

## Patients

`AP_CNSPCN` is empty (`NULL`) or the placeholder `{{{{{{{{{{{{{{{` on a share of rows that
starts in **Apr/2024** and grows month after month. It was 0.1% before (8,731 of 10.5 M rows
until 2022):

| Month | Jan/2024 | Jun/2024 | Jan/2025 | Jun/2025 | Oct/2025 | Jan/2026 | Apr/2026 | Jun/2026 | Aug/2026 |
|---|---|---|---|---|---|---|---|---|---|
| `NULL` + placeholder | 0.1% | 2.6% | 12.8% | 15.0% | 29.4% | 34.7% | 37.5% | 45.0% | **66.6%** |

By state in Aug/2026: PI 100%, RR 96%, PB 96%, SE 92%, MT 91%, RJ 80%, SP 70%, MG 70%; lowest
SC 36%, PA 37%, DF 43%. It hits every kind of care: OCT 95% and cardiac catheterisation 96%
in Aug/2026, cataract surgery 68%, kidney transplant follow-up 42%. AQ in SC was at 2–22% in
the same months and AR at 95%, so the gap is per type and state, not in the patient register.

Exclude both values (`AP_CNSPCN IS NOT NULL AND AP_CNSPCN <> '{{{{{{{{{{{{{{{'`) before
counting or following patients, and don't count patients from mid-2025 on. Rows (APACs) are
complete. `AP_CNSPCN` is the same encoded value across APAC types, so before the gap an AD
patient can be followed into AM, AQ or AR (e.g. retina treatment and the medicines in AM).

## ad vs ad_raw

`ad_raw` holds every column as text exactly as DATASUS publishes it. `ad` is the same data
with `AP_VL_AP` cast to `DOUBLE` (with `TRY_CAST`). Everything else stays text, including
codes with leading zeros (`AP_PRIPAL = '0405050372'`) and dates (`AP_DTINIC = '20260504'`).

## Columns

AD has only the shared columns; they are described on the [APAC page](apac.md#shared-columns).
The official description is the DATASUS *Informe Técnico SIASUS* (Jul/2019), section 3.4.1,
*Layout do arquivo de laudos diversos: ADUFAAMM.DBF* (45 columns; `AP_NATJUR` is in the files
from Jul/2016 but not in the document). Values below were checked on every file
(Jan/2008–Aug/2026, 61.4 M rows); shares "since 2024" are from Jan/2024–Aug/2026 (12.4 M rows).

### What the shared columns hold in AD

| Column | Notes for AD |
|---|---|
| `AP_PRIPAL` | The procedure: see [what is in AD](#what-is-in-ad). Join `procedimentos.codigo`; with SIGTAP versions from 2008 (`datasus sigtap fetch --from 2008 --yearly`) every code matches except `0303050241` (1,563 rows, 2022). **`NULL` on 23,613 rows**, see [quirks](#known-quirks-and-layout-changes). |
| `AP_CIDPRI` | Always filled. Since 2024: `H360` diabetic retinopathy, `Z940` kidney transplant, `H353` macular degeneration, `H903` bilateral sensorineural hearing loss, `H264`/`H250`/`H269`/`H251`/`H259` cataract, `H401` glaucoma, `Z944` liver transplant, `I200` unstable angina. Until 2012 mostly `F` (mental disorders, CAPS). |
| `AP_CIDSEC`, `AP_CIDCAS` | `0000` on 93% and 92% of rows since 2024. |
| `AP_TPATEN` | **Always `00`** (no specific laudo). |
| `AP_TPAPAC` | `3` (single) 58% of all rows, 71–78% a year since 2013; `1`/`2` for follow-up (see [above](#one-row-is-one-apac-month)). `4` (not in the layout) on 760 rows, all with `AP_PRIPAL` `NULL`. |
| `AP_DTINIC`, `AP_DTFIM` | Single APACs: one month (29–30 days) or the same day (0 days, 10% since 2024); follow-up: up to three months (89–91 days). |
| `AP_VL_AP` | = main + secondary procedures in `pa`. 0 on 6.6% of rows since 2024, mostly transplant follow-up (31% of `0506` rows) and `0301` follow-up (13%). |
| `AP_MOTSAI` | Since 2024: `12` (improved) 38%, `15` (discharge with return for follow-up) 19%, `21` (continues, nature of the disease) 16%, `11` (cured) 11%, `18` (other discharge) 9%, `51` (administrative closure) 2%, `28`, `26`, `41` (death) 0.9%, also `25`, `14`, `24`, `31`, `22`, `42`. |
| `AP_CATEND` | `01` (elective) 99%; `02` (urgent) 1%; `03`–`06` rare. |
| `AP_TPUPS` | Since 2024: `05` general hospital 43%, `36` specialised clinic 25%, `07` specialised hospital 15%, `62` 10%, `04` polyclinic 5%. |
| `AP_UNISOL` | Equals `AP_CODUNI` on 82% of rows since 2024. |
| `AP_APACANT` | Zeros on 73% of rows since 2024 (more often filled than in the other types). |
| `AP_CODEMI` | Since 2024: `M…` (municipal secretariat) 54%, `E…` (state) 40%, `S…` 4%, `U…` 1%. |
| `AP_MNDIF` | **Always `1`** (362 exceptions in 61 M rows; wrong, as in AM, AQ and AR); compare `AP_MUNPCN` with `AP_UFMUN` (different on 40% of rows). `AP_UFDIF` is correct (`1` on 1.8%). |
| `AP_CNSPCN` | Encoded, but **empty or `{{{{{{{{{{{{{{{` on a growing share since Apr/2024**: see [patients](#patients). |
| `AP_NATJUR` | From Jul/2016 (`NULL` before). |

### Added by this package

| Column | Type | Meaning |
|---|---|---|
| `_ARQUIVO_ORIGEM` | text | DATASUS file the row came from (`ADSP2605.dbc`). |
| `competencia` | `INTEGER` | Partition: month of the file (`YYYYMM`); equals `AP_MVM`. |
| `uf` | text | Partition: state of the file (the executing facility's state). |

## Joins

- `AP_PRIPAL` → `procedimentos.codigo` (procedure name, `grupo`, `subgrupo`, SIGTAP price).
  Codes retired before the latest SIGTAP (CAPS `030108…`, `0506010023`) need older SIGTAP
  versions.
- `AP_CIDPRI`, `AP_CIDSEC`, `AP_CIDCAS` → `cid10.codigo`.
- `uf` → `ufs.uf`; `LEFT(AP_MUNPCN, 2)` → `ufs.ibge` (patient's state of residence).
- `AP_AUTORIZ`, `AP_CMP` → `pa.PA_AUTORIZ`, `pa.PA_CMP` (same `competencia` and `uf`) for the
  secondary procedures, quantities and values.
- `AP_CNSPCN` → the other APAC tables (`am`, `aq`, `ar`) for the same patient.
- No professional (CBO) column, so no join to `ocupacoes`.

## Known quirks and layout changes

- **One layout since 2008, two column sets.** 45 columns until Jun/2016; `AP_NATJUR` added
  from Jul/2016 (46). Checked on the header of one SP file per year 2008–2026, the change
  months (`ADSP1606`/`ADSP1607`) and `ADAC2608`. `AP_VL_AP` is a numeric (`N`) field 20 wide,
  as in AR; the record is 252 bytes (248 before Jul/2016).
- **Jan/2013: CAPS care moved to RAAS** (see [how the mix changed](#how-the-mix-changed)):
  the same columns, but 60% of the rows and the multi-month APACs disappear.
- **`AP_PRIPAL` `NULL`** on 23,613 rows: Jan–Mar/2013 (13,283, CAPS diagnoses `F…`: APACs
  billed after their codes left AD), Sep–Nov/2023 (8,440, transplant follow-up after
  `0506010023`/`0506010040` were retired), and a few hundred in other months. `pa` has the
  procedure for these rows (checked on ES, Sep/2023).
- **Patient IDs missing** on a growing share since Apr/2024 (see [patients](#patients)).
- `AP_TPATEN` is always `00`; `AP_MNDIF` is always `1` (wrong); `AP_TPAPAC` has a `4`.
- **Conversion size.** The largest file (`ADSP2607.dbc`, 110,306 rows) needs a 28 MB
  temporary DBF and converts in about a second.

## Examples

```sql
-- What AD holds in a year: APACs and value by SIGTAP group and subgroup
SELECT p.grupo, p.subgrupo, COUNT(*) AS apacs, ROUND(SUM(AP_VL_AP)) AS valor
FROM ad LEFT JOIN procedimentos p ON p.codigo = ad.AP_PRIPAL
WHERE competencia BETWEEN 202501 AND 202512
GROUP BY ALL ORDER BY apacs DESC LIMIT 10;

-- Cataract surgeries per month in one state, and how many were 60 or older
SELECT competencia, COUNT(*) AS cirurgias,
       COUNT(*) FILTER (WHERE AP_COIDADE = '4' AND TRY_CAST(AP_NUIDADE AS INT) >= 60
                           OR AP_COIDADE = '5') AS idosos
FROM ad
WHERE uf = 'SC' AND competencia BETWEEN 202501 AND 202512
  AND AP_PRIPAL IN ('0405050372', '0405050119', '0405050097')  -- phaco (foldable/rigid lens), facectomy
GROUP BY 1 ORDER BY 1;

-- Main and secondary procedures of the AD APACs in a month (fetch both: -T pa,ad)
SELECT LEFT(a.AP_PRIPAL, 4) AS subgrupo_ad, p.PA_DOCORIG, p.PA_PROC_ID,
       SUM(p.PA_QTDAPR) AS qtd, ROUND(SUM(p.PA_VALAPR), 2) AS valor
FROM ad a
JOIN pa p ON p.PA_AUTORIZ = a.AP_AUTORIZ AND p.PA_CMP = a.AP_CMP
         AND p.competencia = a.competencia AND p.uf = a.uf
WHERE a.uf = 'SE' AND a.competencia = 202605
GROUP BY ALL ORDER BY valor DESC LIMIT 15;
```
