# ab — APAC Cirurgia Bariátrica (follow-up after bariatric surgery), Jan/2008 to Apr/2017

**Source:** `ABufaamm.dbc` files in `ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados`
(e.g. `ABSP1606.dbc`). No state is split into parts. Careful: [ABO](abo.md) files also start with `AB`
(`ABOSP1606.dbc`); `datasus` matches the full name, so it never mixes them.
**Coverage:** 635 files: Jan/2008 to Apr/2017 (110 months, 544 files: none for Nov–Dec/2016), then
**again Jan–Jul/2025** (7 months, 91 files), nothing in between. The 2025 files are an exact copy of ABO for those
months (see [AB and ABO](#ab-and-abo)). Few states: SP from 2008, RS from Oct/2008, PR from
2009, PE from Jun/2009, TO from 2010, SC from Apr/2010; RN from 2016; MG and DF in Dec/2011 only (MG again in 2025);
16 states in 2025.
**Size on the FTP** (Nov/2026): 635 files, **16.1 MB** of `.dbc`, 231,034 rows, R$ 6.6 M. The
largest file (`ABPR1509.dbc`) has 2,824 rows. Parquet takes about **1.2×** the `.dbc` size
(19.3 MB): the files are so small (25 KB) that Parquet's per-file overhead dominates.
**Fetch:** `uv run datasus fetch -T ab -s SP -f 2016`, or everything with
`-s all -f 2008 -t 202507` (in Nov/2026, three parallel fetches of different year ranges took
5 minutes).

Despite its name, AB is **not the surgery**. Every row is procedure `0301120056`,
*acompanhamento de paciente pós-cirurgia bariátrica por equipe multiprofissional*: one month of
**outpatient follow-up after bariatric surgery** by the hospital's multiprofessional team
(R$ 40 a month). The surgery itself (gastric bypass, sleeve, ...) is a **hospital admission**,
billed on an AIH in **SIH/SUS**, not in SIA: AB only gives its date, its procedure and its AIH
number. Besides the 45 shared `AP_` columns, AB has 12 `AB_` columns from the follow-up *laudo*:
BMI, the surgery, months of follow-up, and — from Apr/2013 — weight lost, comorbidities, habits
and plastic surgery after weight loss, **packed into the old columns** (see
[two laudos in one layout](#two-laudos-in-one-layout)).

Read [APAC file types](apac.md) first: it explains authorisation, validity, monthly
continuation and the patient identifier, and describes the `AP_` columns.

## AB and ABO

DATASUS publishes the same follow-up APACs in two file types:

| | AB | [ABO](abo.md) (*Acompanhamento Pós-Cirurgia Bariátrica*) |
|---|---|---|
| Months | Jan/2008 – Apr/2017, Jan–Jul/2025 | Jan/2014 – Aug/2026 |
| Layout | old laudo's columns (`AB_PROCAIH`, `AB_PONTBAR`, ...), new laudo packed into them from Apr/2013 | new laudo in its own columns (`AP_COMORB`, `AP_CID_C1`…, `AP_MEDICAM`, ...), plus the old `AB_` names |
| States 2014–2017 | PR, SP, PE, SC, RS, TO, RN | the same **plus MG, ES, CE, BA** |

Where both exist, **every AB row is also in ABO** (same `AP_AUTORIZ`, `AP_CMP`, state and file
month; checked for Jan/2014, Jun/2016, Apr/2017, Jan/2025 and Jul/2025). In Jan–Jul/2025 the two
files are identical row for row (2,980 rows in Jan, 2,544 in Jul). In 2014–2017 ABO has more:
1,799 vs 1,734 rows in Jan/2014, 4,246 vs 4,034 in Jun/2016, 4,876 vs 4,307 in Apr/2017,
the difference being whole states (MG, ES, CE, BA) that AB lacks. AB has no files for Nov–Dec/2016
(ABO: 4,633 and 5,040 rows) and stops in Apr/2017 while ABO goes on (5,804 rows in May/2017).
Over Jan/2014–Apr/2017 and Jan–Jul/2025, all 145,425 AB rows are in ABO.

So:

- **Before Jan/2014, AB is the only source** of these APACs.
- **From Jan/2014, use ABO** for counts: it is complete. Never add AB and ABO. For one series,
  split on the file month (`ab WHERE competencia < 201401`, then all of `abo`), not on `AP_CMP`:
  both types bill late months of 2013 in their 2014 files (see
  [abo](abo.md#ab-and-abo)).
- AB still has fields that ABO drops: ABO's `AB_IMC` (BMI) is empty on every row and the % of
  excess weight and kg lost are gone, while AB keeps them in `AB_IMC` and `AB_PROCAIH`.
  ABO, on the other hand, has the surgery as a SIGTAP code and the comorbidities and habits in
  their own columns (two of them swapped, see [abo](abo.md#quirks-of-the-laudo-columns)). Join the
  two on `AP_AUTORIZ`, `AP_CMP`, `competencia` and `uf` to get both.

The *pre*-surgery follow-up (`0301120080`, *acompanhamento pré-cirurgia bariátrica*) is not in AB,
nor in ABO: only `pa` has it.

## One row is one APAC-month, about one patient-month

A follow-up APAC is valid up to three months (`AP_DTINIC` to `AP_DTFIM`, median 87 days) and
billed every month: `AP_TPAPAC = 1` in the first month (49% of rows), `2` after (50%), `3` for a
single month (2008–2012 only, 1,977 rows), and one `4` row (Jul/2025, without procedure). The
231,034 rows are 118,226 APACs (1, 2 or 3 rows each: 57,468 / 8,708 / 52,050) and about 39,000
patients (encoded `AP_CNSPCN`). `(AP_AUTORIZ, AP_CMP)` is unique over the whole history. 13% of
rows are late billings (`AP_CMP` before `AP_MVM`); group by `AP_CMP` for a series by month of care.
By month of care there is about one row per patient (1.00–1.07 rows per `(AP_CNSPCN, AP_CMP)`
every year), but one file can hold several months of the same patient: `ABTO1606.dbc` has 41 rows
for 19 patients, billed for Mar–Jun/2016.

Rows by year of the file, all states:

| 2008 | 2009 | 2010 | 2011 | 2012 | 2013 | 2014 | 2015 | 2016 | 2017 (Jan–Apr) | 2018–2024 | 2025 (Jan–Jul) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 657 | 5,015 | 12,268 | 20,768 | 23,563 | 23,338 | 31,453 | 39,208 | 38,171 | 16,811 | — | 19,782 |

PR and SP are 85% of all rows. Patients are 88% women; mean age 41.

## How ab relates to pa (double counting)

**Every `ab` row is one `pa` row with `PA_DOCORIG = 'P'` and `PA_PROC_ID = '0301120056'`**, and
`AP_VL_AP` equals that row's `PA_VALAPR`: these APACs have no secondary procedures. And the other
way round, every such `pa` `P` row is in `ab`, in the states and months AB covers. Join on
`AP_AUTORIZ = PA_AUTORIZ` **and** `AP_CMP = PA_CMP`, within the same `competencia` and `uf`.
`PA_TPFIN` is always `04` (FAEC).

| | TO 2013-01 | RN 2016-03 | TO 2016-06 | AC 2025-04 |
|---|---|---|---|---|
| `ab` rows | 24 | 13 | 41 | 13 |
| … with exactly one `pa` `P` row, same procedure | 24 | 13 | 41 | 13 |
| `pa` `P` rows with `PA_PROC_ID = '0301120056'` | 24 | 13 | 41 | 13 |
| `SUM(AP_VL_AP)` = `SUM(PA_VALAPR)` | R$ 590.70 | R$ 520.00 | R$ 1,640.00 | R$ 520.00 |

`AP_TIPPRE`, `AP_TPUPS` and `AP_SEXO` equal `pa`'s `PA_TIPPRE`, `PA_TPUPS` and `PA_SEXO` on every
matched row. `AP_NATJUR` is `NULL` in AB in Mar/2016 while `pa` has `PA_NAT_JUR`: AB only has the
column from Jul/2016.

In states AB lacks (MG, ES, ... in 2014–2017), `pa` still has the `0301120056` rows: they are in
ABO. Other `030112…` follow-up codes in `pa` (neonatal screening, pre-bariatric `0301120080`)
are not in AB.

!!! danger "Never add `ab` to `pa`, or to `abo`"
    Each AB row is already a `pa` row, and from 2014 an ABO row too.

## Two laudos in one layout

The DBF columns of AB never changed (57, plus `AP_NATJUR`). They follow the **old follow-up
laudo** of Portaria SAS 493/2007, used until care month Mar/2013. From **Apr/2013** facilities
fill the **new post-bariatric laudo** (Portarias GM/MS 424 and 425/2013), and DATASUS kept
cutting the new text at the old field positions. So, from `AP_CMP = '201304'` on, the same column
holds a different field. The switch is clean: every row until Mar/2013 is old, every row from
Apr/2013 is new, in every state. `AB_PONTBAR` tells them apart: `'0'`/`'1'` = old, `'E'` = new.

Positions are those of the *parte variável* in DATASUS's *Layout da interface texto do APAC e do
SIA* (Apr/2014); the first 21 characters are the record type, month and APAC number.

| Column | Pos. | Old laudo (until Mar/2013) | New laudo (from Apr/2013) |
|---|---|---|---|
| `AB_IMC` | 22–24 | BMI | BMI |
| `AB_PROCAIH` | 25–34 | SIGTAP code of the surgery (AIH procedure) | 25–27 % of excess weight lost; 28–30 kg lost; 31–34 four S/N: gastrectomy with/without duodenal switch, sleeve gastrectomy, gastroplasty with intestinal bypass, vertical banded gastroplasty |
| `AB_DTCIRUR` | 35–42 | Date of surgery | Date of surgery |
| `AB_NUMAIH` | 43–55 | AIH number of the surgery | AIH number of the surgery |
| `AB_PRCAIH2` | 56–65 | Second surgery's code | 56 blank; 57 any comorbidity; 58 hypertension (I10); 59 diabetes (O243); 60 dyslipidaemia (E780); 61 arthrosis (M199); 62 sleep apnoea (G473); 63–65 other comorbidity, ICD-10 (first 3 characters) |
| `AB_PRCAIH3` | 66–75 | Third surgery's code | 66 other comorbidity (4th character); 67 uses medicines; 68 physical activity; 69 multivitamins; 70 weight regain; 71 healthy-diet adherence; 72 abdominal dermolipectomy (`0413040054`); 73–75 its months after surgery |
| `AB_NUMAIH2` | 76–88 | Second AIH number | 76 mammoplasty (`0413040089`) + 77–79 months; 80 brachial dermolipectomy (`0413040062`) + 81–83; 84 crural dermolipectomy (`0413040070`) + 85–87; 88 circumferential abdominal dermolipectomy (`0414040267`) |
| `AB_DTCIRG2` | 89–96 | Second surgery's date | 89–91 months for 88; 92–96 blank |
| `AB_MESACOM` | 97–98 | Months of follow-up | Months of follow-up |
| `AB_ANOACOM` | 99–102 | Year of follow-up | Year of follow-up |
| `AB_PONTBAR` | 103 | BAROS score | Main diagnosis, ICD-10, 1st character (always `E`) |
| `AB_TABBARR` | 104 | BAROS table | Main diagnosis, 2nd character (always `6`) |

The new laudo's secondary diagnosis and the last two characters of the main one are lost. S/N
flags are `S` = yes, `N` = no. The converter strips blanks at both ends of each value, so put
the padding back before cutting by position: `lpad(AB_PROCAIH, 10, ' ')`,
`rpad(' ' || AB_PRCAIH2, 10, ' ')`, and for `AB_PRCAIH3` add the leading blank only when the value
starts with `S` or `N` (position 66, a CID character, is usually blank). This view does it:

```sql
CREATE OR REPLACE TEMP VIEW ab_novo AS
SELECT *,
  TRY_CAST(TRIM(SUBSTR(p1, 1, 3)) AS INT) AS pct_excesso_peso_perdido,
  TRY_CAST(TRIM(SUBSTR(p1, 4, 3)) AS INT) AS kg_perdidos,
  SUBSTR(p1, 7, 1) = 'S' AS gastrectomia_desvio_duodenal,
  SUBSTR(p1, 8, 1) = 'S' AS sleeve,
  SUBSTR(p1, 9, 1) = 'S' AS bypass,
  SUBSTR(p1, 10, 1) = 'S' AS banda_vertical,
  SUBSTR(p2, 2, 1) = 'S' AS comorbidade,
  SUBSTR(p2, 3, 1) = 'S' AS hipertensao,
  SUBSTR(p2, 4, 1) = 'S' AS diabetes,
  SUBSTR(p2, 5, 1) = 'S' AS dislipidemia,
  SUBSTR(p2, 6, 1) = 'S' AS artrose,
  SUBSTR(p2, 7, 1) = 'S' AS apneia,
  NULLIF(TRIM(SUBSTR(p2, 8, 3) || SUBSTR(p3, 1, 1)), '') AS outra_comorbidade_cid,
  SUBSTR(p3, 2, 1) = 'S' AS usa_medicamentos,
  SUBSTR(p3, 3, 1) = 'S' AS atividade_fisica,
  SUBSTR(p3, 4, 1) = 'S' AS polivitaminico,
  SUBSTR(p3, 5, 1) = 'S' AS reganho_peso,
  SUBSTR(p3, 6, 1) = 'S' AS adesao_dieta,
  SUBSTR(p3, 7, 1) = 'S' AS dermolipectomia_abdominal,
  SUBSTR(p4, 1, 1) = 'S' AS mamoplastia,
  SUBSTR(p4, 5, 1) = 'S' AS dermolipectomia_braquial,
  SUBSTR(p4, 9, 1) = 'S' AS dermolipectomia_crural,
  SUBSTR(p4, 13, 1) = 'S' AS dermolipectomia_circunferencial
FROM (
  SELECT *,
    lpad(AB_PROCAIH, 10, ' ') AS p1,
    rpad(' ' || COALESCE(AB_PRCAIH2, ''), 10, ' ') AS p2,
    rpad(CASE WHEN regexp_matches(COALESCE(AB_PRCAIH3, ''), '^[SN]') THEN ' ' || AB_PRCAIH3
              ELSE COALESCE(AB_PRCAIH3, '') END, 10, ' ') AS p3,
    rpad(COALESCE(AB_NUMAIH2, ''), 13, ' ') AS p4
  FROM ab WHERE AB_PONTBAR = 'E');
```

What the new-laudo rows hold (162,353 rows, Apr/2013–Jul/2025):

- **Surgery:** bypass (`NNSN`) 88%, none marked 5%, vertical banded gastroplasty 3%, gastrectomy
  with/without duodenal switch 3%, sleeve 1%.
- **Weight lost:** `0`/`000`/blank on 38% of rows. 4,795 rows have `040`/`701` in the two fields:
  the facility typed the start of the procedure code `0407010173` there; treat them as missing.
- **Comorbidities:** `S` on 9.7% of rows; hypertension 5.7%, diabetes 2.4%, dyslipidaemia 1.9%,
  arthrosis 1.6%, apnoea 1.3%. When "any comorbidity" is `N`, the following flags are usually
  blank (stripped). The "other" ICD-10: E660, E668, E039, G473, Z988, ...
- **Habits:** medicines 12%, physical activity 14%, multivitamins 53%, weight regain 3%,
  healthy-diet adherence 54%.
- **Plastic surgery:** abdominal dermolipectomy 0.7%, mammoplasty 0.2%, brachial 0.2%,
  crural 0.1%, circumferential 0.03%.

Old-laudo rows (68,680, Jan/2008–Mar/2013): `AB_PROCAIH` is the surgery code — `0407010173`
gastroplasty with intestinal bypass 90%, `0407010122` gastrectomy 5%, `0407010181` vertical
banded gastroplasty 2%, plus 4% typos (`4070010173`, `0033022046`, `0301120056`, ...).
The second and third surgery columns are empty (or zeros) on 99.8% of rows. `AB_PONTBAR` is `0`
(37%) or `1` (63%) and `AB_TABBARR` `0`–`4`; the layout calls them *pontuação* and *tabela de
Barros* (the BAROS outcome score) but lists no codes.

## ab vs ab_raw

`ab_raw` holds every column as text exactly as DATASUS publishes it. `ab` is the same data
with `AP_VL_AP` cast to `DOUBLE` (with `TRY_CAST`). Everything else stays text: BMI, dates and
the packed `AB_` fields.

## Columns

The shared `AP_` columns are described on the [APAC page](apac.md#shared-columns). The column
list is that of the DATASUS *Informe Técnico SIASUS* (Jul/2019), APAC section; the positions and
codes come from the DATASUS *Layout da interface texto do APAC e do SIA – layout interno*
(Apr/2014), *parte variável* "Procedimentos de Cirurgia Bariátrica" (until Mar/2013) and
"Acompanh. PÓS Cirurgia Bariátrica" (after Mar/2013). Values were checked on every file
(231,034 rows).

### What the shared columns hold in AB

| Column | Notes for AB |
|---|---|
| `AP_PRIPAL` | **Always `0301120056`** (follow-up after bariatric surgery); `NULL` on one row (Jul/2025, `AP_TPAPAC = 4`). |
| `AP_VL_AP` | R$ 40.00 (R$ 39.38 until Mar/2013, R$ 37.50 in early 2008) or **0.00 on 28% of rows** (mostly continuation months, `AP_TPAPAC = 2`). |
| `AP_TPATEN` | **Always `05`**. |
| `AP_TPAPAC` | `1` 49%, `2` 50%, `3` 0.9% (2008–2012), `4` one row. |
| `AP_MOTSAI` | `21` (continues, nature of the disease) 83%; `18`, `15` (discharge with return), `12` (improved), `28`, `11`, `51`. No deaths but one (`AP_OBITO = 1`). |
| `AP_CIDPRI`, `AP_CIDSEC` | **Always `0000`**. |
| `AP_CIDCAS` | `0000` on 89%; otherwise `E668`, `E660`, `E669` (obesity), a few `M199`, `G473`, `I10`, `O243`. |
| `AP_TPUPS` | `05` general hospital 98%, `07` specialised hospital 2%. |
| `AP_TIPPRE` | Same codes as `pa`'s `PA_TIPPRE` (matched rows equal): `61`, `00`, `40`, `60`, `30`, `20`, `22` until 2017; always `00` in 2025. |
| `AP_CODEMI` | `M…` (municipal) 55%, `E…` (state) 41%, `S…` 4%. |
| `AP_UNISOL` | Equals `AP_CODUNI` on 90–95% of rows; `0000000` on 6% (2025: 16%). |
| `AP_CATEND` | `01` (elective) 99.5%. |
| `AP_APACANT` | Zeros (13 or 12 digits) on 94%. |
| `AP_MNDIF` | **Always `1`** (wrong, as in the other APAC types); compare `AP_MUNPCN` with `AP_UFMUN` (different on 60% of rows). `AP_UFDIF` is correct (`1` on 2%). |
| `AP_CNSPCN` | Encoded. See [patients](#patients). |
| `AP_NATJUR` | `NULL` except in the **Dec/2011** files (present but empty on all 2,241 rows) and from **Jul/2016** (filled). It is the last column of the file. |
| `AP_COIDADE` | Always `4` (years), seven `5`. |

### Follow-up columns (`AB_`)

Each has two readings, see [two laudos in one layout](#two-laudos-in-one-layout).

| Column | Width | Until Mar/2013 | From Apr/2013 | Values |
|---|---|---|---|---|
| `AB_IMC` | 3 | BMI, kg/m² | same | Whole number, `'32'` or `'032'`. Plausible (15–99) on 84% of rows; `0` on 8%; `NULL` on 5%; 150–999 on 3%, which are BMI × 10 (`'345'` = 34.5). Most rows 25–45. |
| `AB_PROCAIH` | 10 | Surgery's SIGTAP code | % excess weight lost, kg lost, surgery S/N ×4 | see above |
| `AB_DTCIRUR` | 8 | Date of the surgery (`YYYYMMDD`) | same | Filled on every row but one; surgeries from 1992 to 2025, a median of 9 months before the month of care (2008–2016). In 2025, surgeries of 2023–2025. |
| `AB_NUMAIH` | 13 | AIH number of the surgery | same | 13 digits; zeros on 205 rows. Links to SIH, which this package does not fetch. |
| `AB_PRCAIH2` | 10 | Second surgery's code | comorbidity flags | `NULL` on most old rows. |
| `AB_PRCAIH3` | 10 | Third surgery's code | habits, abdominal dermolipectomy | |
| `AB_NUMAIH2` | 13 | Second AIH | plastic surgery after weight loss | `'N   N   N   N'` = none. |
| `AB_DTCIRG2` | 8 | Second surgery's date | months of circumferential dermolipectomy | Mostly `NULL`, `'000'`. |
| `AB_MESACOM` | 2 | Months of follow-up | same | `01`–`24` and more, also `1`, `2` (no leading zero); `00` 3%; `NULL` 29%. |
| `AB_ANOACOM` | 4 | Year of follow-up | same | Calendar year (`2015`) on most new rows; `0`, `01`–`05` (year since surgery) on others; `NULL` 52%. |
| `AB_PONTBAR` | 1 | BAROS score (`0`, `1`) | `E` (diagnosis E66x) | Tells the two readings apart. |
| `AB_TABBARR` | 1 | BAROS table (`0`–`4`) | `6` (diagnosis E66x) | |

### Added by this package

| Column | Type | Meaning |
|---|---|---|
| `_ARQUIVO_ORIGEM` | text | DATASUS file the row came from (`ABSP1606.dbc`). |
| `competencia` | `INTEGER` | Partition: month of the file (`YYYYMM`); equals `AP_MVM`. |
| `uf` | text | Partition: state of the file (the hospital's state). |

## Patients

The encoded CNS (`AP_CNSPCN`) is usable for most of the history, with a gap in 2009–2011 and
another in 2025. Share of rows with it empty or the placeholder `{{{{{{{{{{{{{{{`:

| 2008 | 2009 | 2010 | 2011 | 2012 | 2013–2017 | 2025 |
|---|---|---|---|---|---|---|
| 0% | 8.1% | 3.6% | 2.1% | 0.2% | 0% | **16.6%** |

In 2009–2010 the placeholders are mostly PR (397 of 477 PR rows in 2009); in Dec/2011 all 26 MG
rows. In 2025 the gap is `NULL` (2,616 rows) plus placeholders (658): every CE row, 30% of SP
rows, 25% of MG, 23% of RS; 10–25% a month. Same pattern as the other APAC types in 2024–2026 (see
[APAC](apac.md)). `AP_CNSPCN` joins the other APAC tables for the same patient (e.g. ABO after
Apr/2017).

## Joins

- `AP_PRIPAL` → `procedimentos.codigo` (one code: `0301120056`). Old-laudo `AB_PROCAIH` →
  `procedimentos.codigo` for the surgery (`0407010173`, `0407010122`, `0407010181`; they are
  hospital procedures, `valor_hospitalar` R$ 2,350 in SIGTAP 2026-11).
- `AP_CIDCAS` → `cid10.codigo`.
- `uf` → `ufs.uf`; `LEFT(AP_MUNPCN, 2)` → `ufs.ibge` (patient's state of residence).
- `AP_AUTORIZ`, `AP_CMP` → `pa.PA_AUTORIZ`, `pa.PA_CMP` (same `competencia` and `uf`); and
  the same keys → ABO from Jan/2014.
- `AB_NUMAIH` → the AIH number of the surgery in SIH/SUS (`RD` files, not handled here).
- No professional (CBO) column, so no join to `ocupacoes`.

## Known quirks and layout changes

- **One DBF layout, two column sets.** 57 columns (record 331 bytes); 58 with `AP_NATJUR` last
  (335 bytes) in Dec/2011 and Jul/2016–Apr/2017 and 2025. Checked on the header of **every** file.
  `AP_VL_AP` is a numeric (`N`) field 20 wide.
- **Two laudos in the same columns**, switching at care month Apr/2013, see
  [two laudos in one layout](#two-laudos-in-one-layout).
- **The series stops in Apr/2017** and the type comes back for Jan–Jul/2025 only, as a copy of
  ABO. Use ABO from 2014. The registry still covers Jan/2008–Jul/2025, the months with files.
- **Not every state**: 7 states until 2017, while ABO also has MG, ES, CE and BA from 2014.
- `AP_TPATEN` always `05`; `AP_MNDIF` always `1` (wrong); `AP_CIDPRI` always `0000`;
  `AP_VL_AP` 0 on a third of rows; one row with `AP_TPAPAC = 4` and no procedure.
- **Conversion size.** The largest file (2,824 rows) converts in under a second.

## Examples

```sql
-- Follow-up patients and APACs per year (AB alone before 2014; use ABO from 2014)
SELECT LEFT(AP_CMP, 4) AS ano, uf, COUNT(DISTINCT AP_AUTORIZ) AS apacs,
       COUNT(DISTINCT AP_CNSPCN) FILTER (AP_CNSPCN <> '{{{{{{{{{{{{{{{') AS pacientes
FROM ab WHERE AP_CMP < '201401'
GROUP BY ALL ORDER BY ALL;

-- Type of bariatric surgery of the patients followed up, old laudo (2008 to Mar/2013)
SELECT a.AB_PROCAIH, p.nome, COUNT(DISTINCT a.AP_CNSPCN) AS pacientes
FROM ab a LEFT JOIN procedimentos p ON p.codigo = a.AB_PROCAIH
WHERE a.AB_PONTBAR IN ('0', '1')
GROUP BY ALL ORDER BY pacientes DESC LIMIT 5;

-- Weight lost and comorbidities by months since surgery, new laudo (needs the ab_novo view above)
SELECT LEAST(date_diff('month', strptime(AB_DTCIRUR, '%Y%m%d'), strptime(AP_CMP, '%Y%m')) // 6 * 6, 36) AS meses,
       COUNT(*) AS linhas,
       MEDIAN(kg_perdidos) FILTER (kg_perdidos BETWEEN 1 AND 300 AND p1 NOT LIKE '040701%') AS kg_perdidos_mediana,
       ROUND(100 * AVG(hipertensao::INT), 1) AS pct_hipertensao,
       ROUND(100 * AVG(diabetes::INT), 1) AS pct_diabetes
FROM ab_novo
WHERE AP_CMP < '201401'
GROUP BY 1 ORDER BY 1;
```
