# acf — APAC Confecção de Fístula (arteriovenous fistula for haemodialysis), Aug/2014 onward

**Source:** `ACFufaamm.dbc` files in `ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados`
(e.g. `ACFSP1606.dbc`). No state is split into parts.
**Coverage:** Aug/2014 to the latest month DATASUS has released (Aug/2026 when this was written):
145 months. 22 states have a file every month; AC 127, AP 92, RR 100, TO 142, DF 144. A missing
state-month means no fistula was billed there. Before Aug/2014 the same procedure was billed on
**[AD](ad.md)** APACs: see [before Aug/2014](#before-aug2014-fistulas-are-in-ad).
**Size on the FTP** (Nov/2026): 3,795 files, **32.4 MB** of `.dbc`, 411,479 rows, R$ 291.7 M. The
largest file (`ACFSP1908.dbc`) has 673 rows; the median file 68. Parquet takes about **2.3×** the
`.dbc` size (75.7 MB): the files are so small (8.5 KB) that Parquet's per-file overhead dominates.
**Fetch:** `uv run datasus fetch -T acf -s SP -f 2024`, or everything with `-s all -f 201408`
(in Nov/2026, three parallel fetches of different year ranges took 43 minutes: the FTP needs up to
30 s per file, however small).

ACF holds one APAC per **surgical creation of an arteriovenous fistula** (FAV, *fístula
arteriovenosa*): a vein joined to an artery in the arm, which after a few weeks becomes the
patient's access for **haemodialysis**. Every row is procedure `0418010030`, *confecção de fístula
arteriovenosa p/ hemodiálise*, done as an outpatient procedure by a vascular surgeon, mostly in
dialysis clinics or hospitals. Besides the 46 `AP_` columns shared by every APAC type, ACF has 10
`ACF_` columns from the fistula *laudo*: previous duplex scan, previous catheter, previous fistula,
phlebitis, haematomas, visible vein, pulse, vein and artery diameter, and thrill.

The patient's dialysis is in **[ATD](atd.md)** (and [AN](an.md) before Aug/2014), with the same
encoded patient ID; fistulas with a graft and dialysis catheters are in **[AD](ad.md)**. See
[ACF, dialysis and AD](#acf-dialysis-and-ad).

Read [APAC file types](apac.md) first: it explains authorisation, validity, continuation and the
patient identifier, and describes the `AP_` columns.

## One row is one fistula surgery

Every APAC is **single** (`AP_TPAPAC = 3`): it is authorised, done and billed once. `AP_AUTORIZ` is
unique over the whole history (411,479 numbers for 411,479 rows), so **one row is one surgery**.
`AP_DTOCOR`, the date of the exit, is always in the month of care, and `AP_MOTSAI` is a discharge
(`1x`) on 92% of rows. 6% of rows a year are late billings (`AP_CMP` before `AP_MVM`); group by `AP_CMP`
for a series by month of surgery.

Rows by year of the file (= the header row counts of all 3,795 files):

| 2014 (Aug–Dec) | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (Jan–Aug) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 13,061 | 31,466 | 31,519 | 32,496 | 33,924 | 35,531 | 33,542 | 33,106 | 34,189 | 36,817 | 36,801 | 35,917 | 23,110 |

A steady 2,600–3,100 fistulas a month, with no fall in 2020. SP (19%), MG (13%), BA, RJ, PE, RS and
PR have two thirds. The 395,629 rows with a patient ID (Aug/2014–Aug/2026) are 258,265 distinct
patients (encoded `AP_CNSPCN`): 65% had one fistula, 23% two, 8% three, 4% four or more. Patients
are 59% men; 45% are 60 or older (median age 58).

## How acf relates to pa (double counting)

**Every `acf` row is one `pa` row with `PA_DOCORIG = 'P'` and `PA_PROC_ID = '0418010030'`**, and
`AP_VL_AP` equals that row's `PA_VALAPR`: these APACs have no secondary procedures (`S` rows). And
the other way round, every such `pa` row is in `acf`. Join on `AP_AUTORIZ = PA_AUTORIZ` **and**
`AP_CMP = PA_CMP`, within the same `competencia` and `uf`. `PA_TPFIN` is always `04` (FAEC).

| | SE 2014-08 | SE 2016-06 | SE 2022-01 | SE 2026-05 | AC 2026-05 |
|---|---|---|---|---|---|
| `acf` rows | 16 | 21 | 25 | 43 | 9 |
| … with exactly one `pa` `P` row, same procedure and value | 16 | 21 | 25 | 43 | 9 |
| `pa` `P` rows with `PA_PROC_ID = '0418010030'` | 16 | 21 | 25 | 43 | 9 |
| `pa` `S` rows of these APACs | 0 | 0 | 0 | 0 | 0 |
| `SUM(AP_VL_AP)` = `SUM(PA_VALAPR)` | R$ 9,600 | R$ 12,600 | R$ 15,000 | R$ 36,945.60 | R$ 7,975.77 |

`AP_TIPPRE`, `AP_TPUPS`, `AP_SEXO`, `AP_MUNPCN` and `AP_CIDPRI` (`0000` in both) equal `pa`'s
`PA_TIPPRE`, `PA_TPUPS`, `PA_SEXO`, `PA_MUNPCN` and `PA_CIDPRI` on every matched row, and
`AP_NATJUR` equals `PA_NAT_JUR` from Jul/2016.

The other vascular-access procedures (`041801…`) are **not** in ACF, though they are billed on APACs
too (`PA_DOCORIG = 'P'`, FAEC): the fistula with a PTFE graft (`0418010013`), the fistula with an
autologous graft (`0418010021`), the long-term haemodialysis catheter (`0418010048`) and the
Tenckhoff catheter for peritoneal dialysis (`0418010080`) are **AD** APACs. The short-term
double-lumen catheter (`0418010064`) is a secondary procedure (`S` row) of the dialysis APACs, so
only in `pa`.

!!! danger "Never add `acf` to `pa`"
    Each ACF row is already a `pa` row.

## Before Aug/2014: fistulas are in AD

ACF starts in Aug/2014, with ATD. Before that, `0418010030` was billed on **AD** APACs (it is not in
[AN](an.md), which holds only dialysis): in SE, `pa` and `ad` both have 11 fistulas in May/2013 and
11 in Dec/2013. As with dialysis, the switch left a hole: in Jun/2014 `ad` has 2 of the 18 fistulas
in `pa`, in Jul/2014 none of 14; `acf` starts in Aug/2014 (16 of 16) and `ad` has had none since.
For a fistula series before Aug/2014, or for Jun–Jul/2014, use `pa`:

```sql
SELECT PA_CMP, COUNT(*) AS fistulas FROM pa
WHERE PA_DOCORIG = 'P' AND PA_PROC_ID = '0418010030'
GROUP BY 1 ORDER BY 1;
```

## ACF, dialysis and AD

`AP_CNSPCN` is encoded the same way in ACF, [ATD](atd.md) and [AD](ad.md), so it follows a patient
from fistula to dialysis. Counts below use the years with a complete patient ID (2015–2023; see
[patients](#patients)) and the whole ATD history (Aug/2014–Aug/2026).

**Most fistulas are made on patients already on dialysis.** Of the 196,835 patients whose first ACF
fistula was in 2015–2023, 94.7% are in ATD. Taking the first dialysis date of ATD (`ATD_DTPDR`), the
first fistula came:

| before dialysis started | in the month it started | 1–3 months after | 4–12 months | 13–36 months | more than 36 months |
|---|---|---|---|---|---|
| 8.3% | 10.1% | 41.1% | 18.3% | 8.3% | 13.9% |

The patients start haemodialysis on a catheter and get a fistula in the following months. In ATD's
own access column (`ATD_ACEVAS`) the same patients go from 33% fistula and 56% short-term catheter
the month before their ACF fistula to 59% fistula three months after and 71% a year after.

**Share of dialysis patients with a fistula.** Of the patients who started **haemodialysis** in a
year (`ATD_DTPDR`, first ATD month within three months of it), the share with an ACF fistula:

| Start of dialysis | Patients | Before the start | By the month of the start | Within 3 months | Within 12 months | Ever (to Aug/2026) | `ATD_ACEVAS = 1` ever |
|---|---|---|---|---|---|---|---|
| 2015 | 29,776 | 3.3% | 10.3% | 35.7% | 44.3% | 48.4% | 65.2% |
| 2017 | 30,514 | 4.5% | 11.8% | 37.8% | 47.4% | 51.1% | 64.9% |
| 2019 | 33,355 | 5.2% | 11.7% | 38.2% | 48.4% | 51.9% | 64.2% |
| 2021 | 37,673 | 4.7% | 9.8% | 33.4% | 42.8% | 46.2% | 56.2% |
| 2023 | 36,407 | 5.3% | 10.2% | 35.8% | 48.0% | 50.4% | 56.0% |

So only about **1 in 10 new haemodialysis patients had a fistula made by the month they started**,
and half get one in an ACF APAC at all. ATD reports a fistula as the access for more (56–65%):
fistulas made before Aug/2014, in hospital (SIH), privately, or in a state the patient no longer
dialyses in are not in ACF. Among all patients on haemodialysis in Jun/2023 (116,535), 61.2% had an
ACF fistula between Aug/2014 and that month, and ATD gave a fistula as the access for 65.9%. Of the new
peritoneal dialysis patients, only 3–7% ever have an ACF fistula. The 5% of ACF patients never in ATD
may have had a fistula ahead of a dialysis that had not started by Aug/2026, or dialyse outside SUS.

**AD: catheters and grafts.** The procedures for a patient whose fistula failed or could not be
made are AD APACs. In SE, ES, AL and RN (AD fetched for Aug/2014–Aug/2026), 2015–2023:

| AD procedure | APACs | Patients with an ACF fistula | … made before | … first one after (within 6 months) | Patients in ATD |
|---|---|---|---|---|---|
| `0418010048` long-term haemodialysis catheter | 5,147 | 67.3% | 51.8% | 12.3% (7.3%) | 96.2% |
| `0418010013` fistula with a PTFE graft | 1,015 | 62.3% | 51.5% | 9.4% (3.1%) | 95.2% |
| `0418010021` fistula with an autologous graft | 1,945 | 15.9% | 5.7% | 10.1% (1.2%) | 77.0% |

Half the long-term catheters and PTFE grafts go to patients who already had an ACF fistula (a
failed or exhausted access); `0418010013` is a fistula, not a catheter. And 17% of the ACF patients
of those states (2016–2023) had a long-term catheter APAC in AD. Long-term catheters in those
four states grew from 227 (2015) to 1,535 (2025), while ACF fistulas there stayed at 2,000–2,900 a year.

## acf vs acf_raw

`acf_raw` holds every column as text exactly as DATASUS publishes it. `acf` is the same data with
`AP_VL_AP` cast to `DOUBLE` (with `TRY_CAST`). Everything else stays text, the diameters included
(see below).

## Columns

The shared `AP_` columns are described on the [APAC page](apac.md#shared-columns); all 46 are in
ACF under their usual names. Source of the layout: DATASUS *Informe Técnico SIASUS* (Jul/2019),
section 3.4.7 *Layout do arquivo de APAC de confecção de fístula arteriovenosa*; code values from
the laudo's *parte variável* (part 20) in the *Layout da interface texto do APAC e do SIA*
(Apr/2014) and DATASUS's TabWin definition `APAC_Confeccao_de_Fistula.DEF` (in `TAB_SIA.zip`,
`SIASUS/200801_/Auxiliar`, Oct/2026). Values were checked on every row (411,479).

### What the shared columns hold in ACF

| Column | Notes for ACF |
|---|---|
| `AP_PRIPAL` | **Always `0418010030`** (fistula for haemodialysis); `NULL` on 205 rows of CE, Sep/2025 (value R$ 859.20 all the same). |
| `AP_VL_AP` | R$ **600.00** until Jun/2022, **859.20** (SIGTAP 2026) from Jul/2022: 96% of rows. Also 915.76 (SP, MG, BA, RS, AM, ...: 2–6% of rows from 2022), multiples of the price (1,718.40, 4,296.00, 1,200.00, 1,800.00: probably more than one fistula on one APAC), and 0 on 1,832 rows. Never `NULL`. |
| `AP_TPAPAC` | **Always `3`** (single). |
| `AP_TPATEN` | **Always `12`**. |
| `AP_DTINIC`, `AP_DTFIM` | The same day on 42% of rows; at most three months apart. `AP_DTINIC` is in the month of care on all but 1,684 rows. |
| `AP_DTOCOR` | Always filled, always in the month of care: the day of the surgery or of the exit. |
| `AP_MOTSAI` | `18` (discharge, other reasons) 68% (61% in 2014, 75% in 2023), `12` (improved) 13%, `15` (discharge with return) 7%, `51` (closed administratively) 5%, `11` (cured) 4%, `26` (change of procedure) 3% (5% in 2014, 1% in 2026), `31` transfer, 67 deaths. The flags `AP_ALTA`, `AP_ENCERR`, `AP_PERMAN`, `AP_TRANSF`, `AP_OBITO` agree with it. |
| `AP_CIDPRI`, `AP_CIDSEC` | **Always `0000`**. |
| `AP_CIDCAS` | `0000` on 89%; otherwise `N180` (end-stage kidney disease) 9.4%, `N189`, `N188`, `I10`, `I120`, `E142`, `B182` (hepatitis C), ... |
| `AP_TPUPS` | `36` specialised clinic 58%, `05` general hospital 35%, `39` diagnostic support unit 5%, `04`, `07`. |
| `AP_TIPPRE` | `00` 90%; `20`, `61`, `40`, `22`, `60`, `30`, `50`. |
| `AP_CATEND` | `01` (elective) 95%, `02` (urgent) 4%, `06`. |
| `AP_CONDIC` | `PG` 61%, `EP` 38%, `MN` 2%. |
| `AP_CODEMI` | `M…` (municipal) 58%, `E…` (state) 39%, `S…`, `U…`. |
| `AP_UNISOL` | Equals `AP_CODUNI` on 92% of rows; `0000000` on 7%. |
| `AP_APACANT` | Zeros on 95%; `NULL` on 2,615 rows; another APAC number on 16,297. |
| `AP_MNDIF` | **Always `1`** (wrong, as in the other APAC types); compare `AP_MUNPCN` with `AP_UFMUN` (different on 44% of rows). `AP_UFDIF` is correct (`1` on 0.9%). |
| `AP_COIDADE` | `4` (years) 99.9%; 216 rows in days or months (`2`, `3`), probably typing errors (a fistula for haemodialysis in a baby), and 47 rows of 100 or more. |
| `AP_RACACOR` | `03` brown 42%, `01` white 37%, `02` black 10%, `99` 8%, `04` 2%, `05` 408 rows. `AP_ETNIA` is filled on those 408. |
| `AP_CNSPCN` | Encoded. See [patients](#patients). |
| `AP_NATJUR` | `NULL` except in the **Oct/2014** files and from **Jul/2016** (filled on every row). It is the last column of the file, as in ABO and SAD. |

### Laudo columns (`ACF_`)

Every one is filled on every row. The seven flags are `S`/`N` in the files, though the TabWin
definition reads them with a `1`/`0` table (`SIMNAO2.CNV`), so TabWin shows them empty.

| Column | Width | Meaning | Values |
|---|---|---|---|
| `ACF_DUPLEX` | 1 | Previous duplex (Doppler) ultrasound of the arm vessels | `S` on 17–21% of rows every year. |
| `ACF_USOCAT` | 1 | Previous use of a venous catheter or other venous accesses | `S` 50–54% (2014–2019), 63% from 2022. 89% of the `S` patients were in ATD before the fistula month, 73% of the `N` ones. |
| `ACF_PREFAV` | 1 | Previous arteriovenous fistula | `S` 37% (2014), 45% (2020), 60–62% from 2022. 43% of the `S` rows (2018–2023) have an earlier ACF fistula for the same patient, and so do 29% of the `N` rows: read it as the surgeon's note, not a count. |
| `ACF_FLEBIT` | 1 | Phlebitis | `S` 10–12% (2014–2017), 6–7% from 2024. |
| `ACF_HEMATO` | 1 | Haematomas | `S` 8–10% (2014–2017), 5% from 2025. |
| `ACF_VEIAVI` | 1 | Visible vein | `S` 49–51% until 2019, 65–69% from 2022. |
| `ACF_PULSO` | 1 | Presence of pulse | `S` 57–62% until 2020, 74–77% from 2022. |
| `ACF_VEIDIA` | 4 | Diameter of the vein, mm | Text as typed: `0`, `0000`, `3`, `0003`, `02,5`, `2 5`, ... (1.8% with a decimal comma or point; 33 unreadable, like `1S`). **0 on 37–38% of rows until 2018, 57–59% from 2022**: not measured. Otherwise median 3 mm, but `10`, `20`, `25` are common too (probably typed without the comma). |
| `ACF_ARTDIA` | 4 | Diameter of the artery, mm | Same format and the same zeros. Equal to `ACF_VEIDIA` on **75% of rows**, so mostly not two real measurements. |
| `ACF_FREMIT` | 1 | Thrill (*frêmito*) over the fistula's path | `1`–`4`: `1` 28%, `2` 13%, `3` 45%, `4` 13%. The interface layout says only *presença de frêmito no trajeto da FAV (1 a 4)*; no document found gives the labels. `1` goes with the poorest vessels (pulse 38%, visible vein 28%, median vein 1 mm), `3` with the best (pulse 87%, visible vein 83%, previous fistula 76%). `3` rose from 33% (2014) to 57% (2025). |

The layout's last laudo field, *presença de pulso sem frêmito* (`APA_PULFRE`, `S`/`N`), has **no
column** in the files, although the TabWin definition still reads one (`ACF_PULFRE`).

### Added by this package

| Column | Type | Meaning |
|---|---|---|
| `_ARQUIVO_ORIGEM` | text | DATASUS file the row came from (`ACFSP1606.dbc`). |
| `competencia` | `INTEGER` | Partition: month of the file (`YYYYMM`); equals `AP_MVM`. |
| `uf` | text | Partition: state of the file (the facility's state). |

## Patients

The encoded CNS (`AP_CNSPCN`) is filled on every row until Mar/2024. Since Apr/2024 a growing share
is `NULL` or the placeholder `{{{{{{{{{{{{{{{`, as in ATD and the other APAC types (see [APAC](apac.md)):

| until Mar/2024 | 2024 | Jan/2025 | Jul/2025 | Jan/2026 | Apr/2026 | May/2026 | Jun/2026 | Jul/2026 | Aug/2026 |
|---|---|---|---|---|---|---|---|---|---|
| 0% | 2.7% | 7.6% | 11.9% | 15.5% | 21.1% | 59.5% | 68.1% | 85.4% | **89.1%** |

From 2024 it is missing on 25–29% of the rows of SE, AM, CE, RJ and AC, on 21% of SP and on 4–6% of
RR, ES and PI. Exclude both values (`AP_CNSPCN IS NOT NULL AND AP_CNSPCN <> '{{{{{{{{{{{{{{{'`) and
don't follow patients from mid-2024 on; count rows, which are complete and are one surgery each.

## Joins

- `AP_PRIPAL` → `procedimentos.codigo` (one code: `0418010030`).
- `AP_CIDCAS` → `cid10.codigo` (`AP_CIDPRI` and `AP_CIDSEC` are always `0000`).
- `uf` → `ufs.uf`; `LEFT(AP_MUNPCN, 2)` → `ufs.ibge` (patient's state of residence).
- `AP_AUTORIZ`, `AP_CMP` → `pa.PA_AUTORIZ`, `pa.PA_CMP` (same `competencia` and `uf`).
- `AP_CNSPCN` → `atd.AP_CNSPCN` and `an.AP_CNSPCN` (the patient's dialysis), `ad.AP_CNSPCN`
  (catheters and grafts), until about Mar/2024.
- No professional (CBO) column, so no join to `ocupacoes`.

## Known quirks and layout changes

- **One DBF layout, two column sets.** 55 columns (record 264 bytes); 56 with `AP_NATJUR` last
  (268 bytes) in Oct/2014 and from Jul/2016 (the same Oct/2014 one-off as SAD and ABO). Checked on
  the header of **every** file. `AP_VL_AP` is a numeric (`N`) field 20 wide; the diameters are text.
- **One procedure, single APACs**: `AP_PRIPAL` always `0418010030` (205 `NULL`), `AP_TPAPAC` always
  `3`, `AP_TPATEN` always `12`, `AP_CIDPRI`/`AP_CIDSEC` always `0000`, `AP_MNDIF` always `1` (wrong).
- **Diameters mostly unusable**, see [laudo columns](#laudo-columns-acf_): zero on half the rows,
  vein = artery on three quarters, mixed formats.
- **`ACF_FREMIT` is a 1–4 code without published labels**, and the layout's *pulse without thrill*
  flag is missing.
- **Before Aug/2014** the fistulas are in AD, with a gap in Jun–Jul/2014; see
  [before Aug/2014](#before-aug2014-fistulas-are-in-ad).
- **Patient ID missing from Apr/2024**, 89% in Aug/2026; see [patients](#patients).
- **Conversion size.** The largest file (673 rows) converts in under a second.

## Examples

```sql
-- Fistulas per year of surgery, and their patients (to 2023: the patient ID is complete)
SELECT LEFT(AP_CMP, 4) AS ano, COUNT(*) AS fistulas,
       COUNT(DISTINCT AP_CNSPCN) FILTER (AP_CNSPCN <> '{{{{{{{{{{{{{{{') AS pacientes,
       ROUND(100 * AVG((ACF_PREFAV = 'S')::INT), 1) AS pct_fav_previa
FROM acf GROUP BY 1 ORDER BY 1;

-- New haemodialysis patients with a fistula made by the month dialysis started
WITH f AS (SELECT AP_CNSPCN, MIN(strptime(AP_CMP, '%Y%m')) AS primeira_fav FROM acf
           WHERE AP_CNSPCN <> '{{{{{{{{{{{{{{{' GROUP BY 1),
     d AS (SELECT AP_CNSPCN, MIN(TRY_STRPTIME(ATD_DTPDR, '%Y%m%d')) AS inicio FROM atd
           WHERE AP_CNSPCN <> '{{{{{{{{{{{{{{{' AND AP_PRIPAL IN ('0305010107', '0305010115')
           GROUP BY 1)
SELECT year(inicio) AS ano, COUNT(*) AS pacientes,
       ROUND(100 * AVG(COALESCE(primeira_fav <= date_trunc('month', inicio), false)::INT), 1) AS pct_fav_ate_inicio
FROM d LEFT JOIN f USING (AP_CNSPCN)
WHERE year(inicio) BETWEEN 2015 AND 2023
GROUP BY 1 ORDER BY 1;

-- Fistulas, long-term catheters and grafts by state and year (fistulas are acf, the rest ad)
SELECT uf, LEFT(AP_CMP, 4) AS ano, '0418010030' AS proc, COUNT(*) AS apacs FROM acf GROUP BY ALL
UNION ALL
SELECT uf, LEFT(AP_CMP, 4), AP_PRIPAL, COUNT(*) FROM ad
WHERE AP_PRIPAL IN ('0418010013', '0418010021', '0418010048') AND competencia >= 201408 GROUP BY ALL
ORDER BY 1, 2, 3;
```
