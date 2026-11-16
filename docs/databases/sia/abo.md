# abo — APAC Acompanhamento Pós-Cirurgia Bariátrica (follow-up after bariatric surgery), Jan/2014 onward

**Source:** `ABOufaamm.dbc` files in `ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados`
(e.g. `ABOSP1606.dbc`). No state is split into parts. Careful: AB files also start with `AB`
(`ABSP1606.dbc`), and `ABOPE…` is ABO for Pernambuco while `ABPE…` is AB; `datasus` matches the
full name, so it never mixes them.
**Coverage:** 1,621 files, **every month from Jan/2014 to Aug/2026** (152 months), 18 states. PR,
SP, MG and RS have a file every month, SC all but one; ES from Feb/2014, PE, CE and TO (until Dec/2018) from
Jan/2014, DF only Feb–Oct/2014, AC from 2015, RN and BA from 2016, MA from Apr/2019, PB from
Dec/2021, AM and SE from 2022, PA from Apr/2025. A missing state-month means no production.
**Size on the FTP** (Nov/2026): 1,621 files, **38.9 MB** of `.dbc`, 551,610 rows, R$ 15.2 M. The
largest file (`ABOPR1811.dbc`) has 4,366 rows. Parquet takes about **1.4×** the `.dbc` size
(53.7 MB): the files are so small (24 KB) that Parquet's per-file overhead dominates.
**Fetch:** `uv run datasus fetch -T abo -s SP -f 2024`, or everything with `-s all -f 2014`
(in Nov/2026, three parallel fetches of different year ranges took 13 minutes).

ABO is the **monthly outpatient follow-up after bariatric surgery**: every row is procedure
`0301120056`, *acompanhamento de paciente pós-cirurgia bariátrica por equipe multiprofissional*
(R$ 40 a month), billed by the hospital that operated. The surgery itself is a **hospital
admission** in **SIH/SUS**; ABO gives its procedure, date and AIH number. It holds **the same APACs
as [AB](ab.md)**, which it replaced: AB has the older years, ABO the complete series from 2014 (see
[AB and ABO](#ab-and-abo)). Besides the shared `AP_` columns, ABO has the post-bariatric *laudo*
decoded into its own columns: the surgery, plastic surgery after weight loss, comorbidities and
habits. **It has no BMI and no weight lost** (always empty), and three of its columns are
mislabelled (see [quirks of the laudo columns](#quirks-of-the-laudo-columns)).

Read [APAC file types](apac.md) first: it explains authorisation, validity, monthly
continuation and the patient identifier, and describes the `AP_` columns.

## AB and ABO

DATASUS publishes the same follow-up APACs in two file types. **Every AB row from Jan/2014 is also
in ABO** (145,425 of 145,425 rows, same `AP_AUTORIZ`, `AP_CMP`, state and file month), with the
same values in every shared field. ABO has more: states AB lacks (MG, ES, CE, DF, BA, AC, ...), the
months AB has no file for (Nov–Dec/2016 and May/2017–Dec/2024), and Aug/2025 on. In
Jan–Jul/2025, AB is an exact copy of ABO.

| | [AB](ab.md) | ABO |
|---|---|---|
| Files | Jan/2008 – Oct/2016, Jan–Apr/2017, Jan–Jul/2025 | Jan/2014 – Aug/2026, every month |
| States | 7 until 2017 (PR, SP, PE, SC, RS, TO, RN) | 18 |
| Laudo | old columns, new laudo packed into them from Apr/2013 | new laudo decoded into its own columns |
| BMI, weight lost | yes (`AB_IMC`, `AB_PROCAIH`) | **no** |

| File year | 2014 | 2015 | 2016 | 2017 | 2025 (Jan–Jul) |
|---|---|---|---|---|---|
| ABO rows | 33,617 | 41,661 | 50,431 | 63,286 | 19,782 |
| … not in AB | 2,164 | 2,453 | 12,260 | 46,475 | 0 |

**Which table for which period:**

- **Before Jan/2014:** `ab` only.
- **From Jan/2014:** `abo` only. Never add `ab` rows of 2014–2017 or 2025 to `abo`.
- For one series from 2008, take `ab` for the **files** before 2014 and `abo` for the rest. Split
  on the file month, `competencia`, **not** on the month of care `AP_CMP`: ABO's 2014 files also
  bill late months of 2013, and so do AB's 2014 files, so a split on `AP_CMP` counts 909
  APAC-months twice. Split on `competencia`, the union has no duplicate `(AP_AUTORIZ, AP_CMP)`.

```sql
SELECT LEFT(AP_CMP, 4) AS ano, COUNT(*) AS apac_meses FROM (
  SELECT AP_CMP FROM ab WHERE competencia < 201401
  UNION ALL
  SELECT AP_CMP FROM abo
) GROUP BY 1 ORDER BY 1;
```

- For BMI and weight lost in 2014–2017, join `ab` on `AP_AUTORIZ`, `AP_CMP`, `competencia` and
  `uf` (AB's states only; from Apr/2013 AB packs them into `AB_IMC` and `AB_PROCAIH`, see
  [ab](ab.md#two-laudos-in-one-layout)). On the matched rows AB has a plausible BMI on 87%.

## One row is one APAC-month, about one patient-month

A follow-up APAC is valid up to three months and billed every month: `AP_TPAPAC = 1` in the
first month (53% of rows), `2` after (47%), and 54 rows with `4` (2021–2026), without procedure
or value. There is no `3` (single). The 551,610 rows are 294,196 APACs (1, 2 or 3 rows each:
149,879 / 31,220 / 113,097) and about 84,000 patients (encoded `AP_CNSPCN`).
`(AP_AUTORIZ, AP_CMP)` is unique over the whole history. 2–25% of rows a year are late billings
(`AP_CMP` before `AP_MVM`); group by `AP_CMP` for a series by month of care. By month of care
there is about one row per patient (1.00–1.06 rows per `(AP_CNSPCN, AP_CMP)` every year).

Rows by year of the file (= the header row counts of all 1,621 files):

| 2014 | 2015 | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (Jan–Aug) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 33,617 | 41,661 | 50,431 | 63,286 | 71,568 | 71,278 | 46,229 | 19,488 | 23,686 | 29,600 | 32,101 | 36,708 | 31,957 |

The fall in 2020–2021 matches the COVID-19 pandemic, when elective surgery was suspended. PR (48%) and SP
(28%) have three quarters of all rows. Patients are 87% women; mean age 41.

## How abo relates to pa (double counting)

**Every `abo` row is one `pa` row with `PA_DOCORIG = 'P'` and `PA_PROC_ID = '0301120056'`**, and
`AP_VL_AP` equals that row's `PA_VALAPR`: these APACs have no secondary procedures (`S` rows).
And the other way round, every such `pa` row is in `abo`. Join on `AP_AUTORIZ = PA_AUTORIZ`
**and** `AP_CMP = PA_CMP`, within the same `competencia` and `uf`. `PA_TPFIN` is always `04`
(FAEC).

| | TO 2016-06 | ES 2016-06 | SE 2023-05 | AC 2025-04 |
|---|---|---|---|---|
| `abo` rows | 41 | 82 | 1 | 13 |
| … with exactly one `pa` `P` row, same procedure and value | 41 | 82 | 1 | 13 |
| `pa` `P` rows with `PA_PROC_ID = '0301120056'` | 41 | 82 | 1 | 13 |
| `pa` `S` rows of these APACs | 0 | 0 | 0 | 0 |
| `SUM(AP_VL_AP)` = `SUM(PA_VALAPR)` | R$ 1,640 | R$ 3,280 | R$ 0 | R$ 520 |

ES is a state AB does not have. `AP_TPPRE`, `AP_TPUPS`, `AP_SEXO` and `AP_MUNPCN` equal `pa`'s
`PA_TIPPRE`, `PA_TPUPS`, `PA_SEXO` and `PA_MUNPCN` on every matched row, and `AP_NATJUR` equals
`PA_NAT_JUR` from Jul/2016. `CO_CIDPRIM` is `0000` where `pa` has `PA_CIDPRI = '1111'`.

The **pre**-surgery follow-up, `0301120080` (*acompanhamento de paciente pré-cirurgia bariátrica
por equipe multiprofissional*, R$ 40, FAEC), is billed on APACs too (`PA_DOCORIG = 'P'`: 167 rows
in AC 2025-04, 5 in SE 2023-05), but it is **not in ABO**, nor in AB: only `pa` has it.

!!! danger "Never add `abo` to `pa`, or to `ab`"
    Each ABO row is already a `pa` row, and AB's rows from 2014 are ABO rows.

## Quirks of the laudo columns

ABO's own columns follow the *parte variável* "Procedimentos de Acompanh. PÓS Cirurgia
Bariátrica" of DATASUS's *Layout da interface texto do APAC e do SIA* (Apr/2014), the same laudo
AB packs into its old columns from Apr/2013. ABO decodes it: S/N flags become SIGTAP or ICD-10
codes (or `NULL`), or `1`/`0`. Compared field by field with AB's packed positions on the 145,424
rows both types publish (2014–2017 and 2025):

| ABO column | Holds | Matches AB |
|---|---|---|
| `AB_PROCAIH` | the surgery's SIGTAP code, decoded from the four surgery flags; `NULL` if none is `S` | every row |
| `AB_PRCAIH2` | `0413040054` abdominal dermolipectomy | every row |
| `AB_PRCAIH3` | **written as `0413040070` (crural) but it is the mammoplasty flag** (`0413040089`) | every row, with mammoplasty |
| `AB_PRCAIH4` | `0413040062` brachial dermolipectomy | every row |
| `AB_PRCAIH5` | `0413040070` crural dermolipectomy | every row |
| `AB_PRCAIH6` | `0413040202` (not a SIGTAP code): circumferential abdominal dermolipectomy (`0413040259`) | every row |
| `AB_T_PRC2`…`6` | months since the bariatric surgery, for each plastic surgery | every row |
| `AP_COMORB`, `AP_CID_C1`…`C5`, `AP_CID_CO` | comorbidities | every row |
| `AP_MEDICAM`, `AP_REG_PES`, `AP_ADESAO` | medicines, weight regain, healthy diet | every row |
| `AP_POLIVIT` | **labelled multivitamins, holds physical activity** (layout position 68) | every row, swapped |
| `AP_ATV_FIS` | **labelled physical activity, holds multivitamins** (position 69) | every row, swapped |
| `AB_MESACOM` | months of follow-up | every row |
| `AB_ANOACOM` | **first character only** of the 4-character year of follow-up | — |
| `AB_IMC` | **always empty**; AB has the BMI | — |

The % of excess weight lost and the kg lost have no column in ABO at all, and `AB_NUMAIH2`,
`AB_DTCIRG2`, `AB_PONTBAR` and `AB_TABBARR` (old-laudo fields kept from AB's layout) are always
empty. The secondary diagnosis and most of the main one of the laudo are lost, as in AB.

On the two swapped flags: the layout has *pratica atividade física* at position 68 and *uso de
polivitamínico* at 69; AB keeps that order, and ABO's `AP_POLIVIT` equals position 68 and
`AP_ATV_FIS` position 69 on every row. So **read `AP_POLIVIT` as physical activity and
`AP_ATV_FIS` as multivitamins**. The values agree: multivitamins (`AP_ATV_FIS`) 50–70% of rows
until 2019, like AB's 53%, physical activity (`AP_POLIVIT`) 10–25%, like AB's 14%. DATASUS's
TabWin definition (`APAC_Pos_Cirurgia_Bariatica.def`) reads them by their labels, so TabWin
tables mix them up too.

## abo vs abo_raw

`abo_raw` holds every column as text exactly as DATASUS publishes it. `abo` is the same data
with `AP_VL_AP` cast to `DOUBLE` (with `TRY_CAST`). Everything else stays text: dates, codes and
flags.

## Columns

The shared `AP_` columns are described on the [APAC page](apac.md#shared-columns). The Informe
Técnico SIASUS (Jul/2019) has **no ABO section**: column names and code tables come from DATASUS's
TabWin definition `APAC_Pos_Cirurgia_Bariatica.def` (in `TAB_SIA.zip`,
`SIASUS/200801_/Auxiliar`, Oct/2026), and the meanings from the laudo's *parte variável* in the
*Layout da interface texto do APAC e do SIA* (Apr/2014). Values were checked on every file
(551,610 rows).

### Shared columns with other names

Six shared columns are named differently in ABO; they mean the same as in the other APAC types.

| ABO | Other APAC types | Notes for ABO |
|---|---|---|
| `AP_TPPRE` | `AP_TIPPRE` | Provider type, same codes as `PA_TIPPRE`: `00`, `61`, `60`, `40`, `30`, `20`, `22` until 2016; **always `00` from 2017**. |
| `AP_TPATEND` | `AP_TPATEN` | **Always `05`** (bariatric surgery). |
| `AP_DTOOCOR` | `AP_DTOCOR` | Date of the exit event, on the 17% of rows with one. |
| `AP_APACAN` | `AP_APACANT` | Previous APAC: zeros (13 or 12 digits) on 95%; `NULL` on 1,051 rows of 2014–2016. |
| `CO_CIDPRIM` | `AP_CIDPRI` | **Always `0000`**. |
| `CO_CIDSEC` | `AP_CIDSEC` | **Always `0000`**. |

Query across APAC types with an alias: `SELECT AP_TPPRE AS AP_TIPPRE FROM abo`.

### What the other shared columns hold in ABO

| Column | Notes for ABO |
|---|---|
| `AP_PRIPAL` | **Always `0301120056`** (follow-up after bariatric surgery); `NULL` on the 54 `AP_TPAPAC = 4` rows. |
| `AP_VL_AP` | R$ 40.00 or **0.00 on 31% of rows** (62% of continuation months, 4% of first months); `NULL` on the 54 `AP_TPAPAC = 4` rows. |
| `AP_TPAPAC` | `1` 53%, `2` 47%, `4` 54 rows. No `3`. |
| `AP_MOTSAI` | `21` (continues, nature of the disease) 82%; `12` (improved) 8%, `18`, `15` (discharge with return), `28`, `11`, `51`. Two deaths (`AP_OBITO = 1`). |
| `AP_CIDCAS` | `0000` on 90%; otherwise `E668`, `E660`, `E669` (obesity), a few `O243`, `M199`, `G473`, `E780`. |
| `AP_TPUPS` | `05` general hospital 99%, `07` specialised hospital. |
| `AP_CODEMI` | `E…` (state) 57%, `M…` (municipal) 41%, `S…`, `U…`. |
| `AP_UNISOL` | Equals `AP_CODUNI` on 85% of rows; `0000000` on 14% (from 2017). |
| `AP_CATEND` | `01` (elective) 99.9%. |
| `AP_CONDIC` | `EP`, `PG`; `MN` on 1,794 rows of 2014–2016. |
| `AP_MNDIF` | **Always `1`** (wrong, as in the other APAC types); compare `AP_MUNPCN` with `AP_UFMUN` (different on 68% of rows). `AP_UFDIF` is correct (`1` on 1.2%). |
| `AP_CNSPCN` | Encoded. See [patients](#patients). |
| `AP_ETNIA` | `NULL` but on 70 rows. |
| `AP_NATJUR` | `NULL` except in the **Oct/2014** files and from **Jul/2016** (filled). It is the last column of the file. ABO has no Dec/2011 files, so not that month's one-off column of the older types. |
| `AP_COIDADE` | Always `4` (years), 16 `5`. |

### Laudo columns

| Column | Width | Meaning | Values |
|---|---|---|---|
| `AB_IMC` | 3 | BMI | **Always `NULL`**. |
| `AB_PROCAIH` | 10 | Bariatric surgery, SIGTAP code | `0407010173` gastroplasty with intestinal bypass 91%, `0407010181` vertical banded gastroplasty 2.5%, `0407010360` sleeve gastrectomy 1.9%, `0407010122` gastrectomy with or without duodenal switch 0.9%; `NULL` (no surgery flag in the laudo) 4%: 3,605 rows of 2014, then from May/2025, 55% of rows in Aug/2026. These are hospital procedures (`valor_hospitalar` R$ 2,350 in SIGTAP 2026-11). |
| `AB_DTCIRUR` | 8 | Date of the bariatric surgery (`YYYYMMDD`) | Filled on every row but the 54 `AP_TPAPAC = 4`; surgeries from 1977 to 2026, a median of 6–10 months before the month of care (15 in 2021). |
| `AB_NUMAIH` | 13 | AIH number of the surgery | Links to SIH, which this package does not fetch. `1000000000000` on 263 rows of 2014–2016. |
| `AB_PRCAIH2` | 10 | Abdominal dermolipectomy after bariatric surgery | `0413040054` if done (1.6% of rows), else `NULL`. |
| `AB_T_PRC2` | 3 | Its months after the bariatric surgery | `036`, `24`, ... ; `'001'` on 7,547 rows (82% of those with the surgery: probably a placeholder); `000` or `NULL` when not done. |
| `AB_PRCAIH3` | 10 | **Mammoplasty** after bariatric surgery (`0413040089`) | Written as `0413040070` if done (0.08%, nearly all women), else `NULL`. |
| `AB_T_PRC3` | 3 | Its months after the bariatric surgery | |
| `AB_PRCAIH4` | 10 | Brachial dermolipectomy | `0413040062` if done (0.08%), else `NULL`. |
| `AB_T_PRC4` | 3 | Its months after the bariatric surgery | |
| `AB_PRCAIH5` | 10 | Crural dermolipectomy | `0413040070` if done (0.06%), else `NULL`. |
| `AB_T_PRC5` | 3 | Its months after the bariatric surgery | |
| `AB_PRCAIH6` | 10 | Circumferential abdominal dermolipectomy (SIGTAP `0413040259`) | Written as `0413040202` (no such code) if done (67 rows), else `NULL`. |
| `AB_T_PRC6` | 3 | Its months after the bariatric surgery | |
| `AB_NUMAIH2` | 13 | (old laudo: second AIH) | **Always `NULL`**. |
| `AB_DTCIRG2` | 8 | (old laudo: second surgery's date) | **Always `NULL`**. |
| `AB_MESACOM` | 2 | Months of follow-up | `01`–`24` and more, also `1`, `2` (no leading zero); `00` 2%; `NULL` 11% (29% in 2014, under 1% in 2021–2022). |
| `AB_ANOACOM` | **1** | Year of follow-up, **first character only** | `2` (a calendar year, `2014`…`2026`) 42%, `0` (`01`–`09`, years since surgery) 34%, `1`–`9` 3%, `NULL` 21%. Practically unusable. |
| `AB_PONTBAR` | 1 | (old laudo: BAROS score) | **Always `NULL`**. |
| `AB_TABBARR` | 1 | (old laudo: BAROS table) | **Always `NULL`**. |
| `AP_COMORB` | 1 | Any comorbidity (`S`/`N`) | `S` on 12%. 18,330 `S` rows name none of the six comorbidities. |
| `AP_CID_C1` | 4 | Hypertension | `I10` if yes (7.3%), else `NULL`. |
| `AP_CID_C2` | 4 | Diabetes mellitus | `O243` if yes (3.2%; the laudo's code, *diabetes in pregnancy* in ICD-10), else `NULL`. |
| `AP_CID_C3` | 4 | Dyslipidaemia | `E780` if yes (2.3%), else `NULL`. |
| `AP_CID_C4` | 4 | Arthrosis | `M199` if yes (2.4%), else `NULL`. |
| `AP_CID_C5` | 4 | Sleep apnoea | `G473` if yes (2.4%), else `NULL`. |
| `AP_CID_CO` | 4 | Other comorbidity, ICD-10 | `NULL` 99%; `E660`, `E668`, `E039`, `F41`, `O243`, ... |
| `AP_MEDICAM` | 1 | Uses medicines (`1`/`0`) | `1` on 8–11% of rows until 2019, 24–26% in 2024–2026. |
| `AP_POLIVIT` | 1 | **Physical activity** (labelled multivitamins) | `1` on 9–19% until 2019, 25% in 2025. |
| `AP_ATV_FIS` | 1 | **Multivitamins** (labelled physical activity) | `1` on 55–72% until 2019, 28% in 2025. |
| `AP_REG_PES` | 1 | Weight regain (`1`/`0`) | `1` on 1–6%. |
| `AP_ADESAO` | 1 | Adheres to a healthy, balanced diet (`1`/`0`) | `1` on 55–72% until 2019, 25–31% from 2024. |

### Added by this package

| Column | Type | Meaning |
|---|---|---|
| `_ARQUIVO_ORIGEM` | text | DATASUS file the row came from (`ABOSP1606.dbc`). |
| `competencia` | `INTEGER` | Partition: month of the file (`YYYYMM`); equals `AP_MVM`. |
| `uf` | text | Partition: state of the file (the hospital's state). |

## Patients

The encoded CNS (`AP_CNSPCN`) is filled on every row until Apr/2024. Since May/2024 a growing share
is `NULL` or the placeholder `{{{{{{{{{{{{{{{`, as in the other APAC types (see [APAC](apac.md)):

| 2014–2023 | 2024 | 2025 | Jan/2026 | Feb/2026 | Jul/2026 | Aug/2026 |
|---|---|---|---|---|---|---|
| 0% | 7.2% | 16.8% | 23% | 39% | 46% | **58%** |

In 2024–2026 it is missing on 95% of CE rows and nearly all PA rows, 28% of SE, 26% of SC, 22% of
SP, 20% of MG, 19% of RS and 13% of PR, and on none in MA, AC, BA and PB. `AP_CNSPCN` joins AB for the same patient
before 2014, and the other APAC tables.

## Joins

- `AP_PRIPAL` → `procedimentos.codigo` (one code: `0301120056`). `AB_PROCAIH` and
  `AB_PRCAIH2`, `4`, `5` → `procedimentos.codigo` for the surgeries (hospital procedures);
  not `AB_PRCAIH3` (wrong code, it is `0413040089`) nor `AB_PRCAIH6` (`0413040202` is no code).
- `AP_CIDCAS`, `AP_CID_C1`…`C5`, `AP_CID_CO` → `cid10.codigo`.
- `uf` → `ufs.uf`; `LEFT(AP_MUNPCN, 2)` → `ufs.ibge` (patient's state of residence).
- `AP_AUTORIZ`, `AP_CMP` → `pa.PA_AUTORIZ`, `pa.PA_CMP` (same `competencia` and `uf`); and the
  same keys → `ab` for 2014–2017 and 2025.
- `AB_NUMAIH` → the AIH number of the surgery in SIH/SUS (`RD` files, not handled here).
- No professional (CBO) column, so no join to `ocupacoes`.

## Known quirks and layout changes

- **One DBF layout, two column sets.** 77 columns (record 403 bytes); 78 with `AP_NATJUR` last
  (407 bytes) in Oct/2014 and from Jul/2016. Checked on the header of **every** file.
  `AP_VL_AP` is a numeric (`N`) field 20 wide.
- **Six shared columns renamed**, see [shared columns with other names](#shared-columns-with-other-names).
- **Laudo columns empty, mislabelled or cut**, see [quirks of the laudo columns](#quirks-of-the-laudo-columns):
  no BMI or weight lost; `AB_PRCAIH3` is mammoplasty; `AP_POLIVIT` and `AP_ATV_FIS` are swapped;
  `AB_ANOACOM` keeps one character.
- **Surgery missing from May/2025**: `AB_PROCAIH` is `NULL` on a growing share of rows (17% in
  Aug/2025, 32% in Dec/2025, 55% in Aug/2026; SP, RS, SC, PA). The laudo marks no surgery there.
- `AP_TPATEND` always `05`; `AP_MNDIF` always `1` (wrong); `CO_CIDPRIM` and `CO_CIDSEC` always
  `0000`; `AP_VL_AP` 0 on a third of rows; 54 rows with `AP_TPAPAC = 4` and no procedure.
- **The same APACs as AB** from 2014, see [AB and ABO](#ab-and-abo).
- **Conversion size.** The largest file (4,366 rows) converts in under a second.

## Examples

```sql
-- Follow-up APACs and patients per year of care (from 2024 the patient count is low: missing CNS)
SELECT LEFT(AP_CMP, 4) AS ano, COUNT(DISTINCT AP_AUTORIZ) AS apacs,
       COUNT(DISTINCT AP_CNSPCN) FILTER (AP_CNSPCN <> '{{{{{{{{{{{{{{{') AS pacientes
FROM abo GROUP BY 1 ORDER BY 1;

-- Type of bariatric surgery of the patients followed up
SELECT a.AB_PROCAIH, p.nome, COUNT(DISTINCT a.AP_CNSPCN) AS pacientes
FROM abo a LEFT JOIN procedimentos p ON p.codigo = a.AB_PROCAIH
WHERE a.AP_CNSPCN <> '{{{{{{{{{{{{{{{'
GROUP BY ALL ORDER BY pacientes DESC;

-- Comorbidities and habits by months since surgery (note the swapped AP_POLIVIT / AP_ATV_FIS)
SELECT LEAST(date_diff('month', strptime(AB_DTCIRUR, '%Y%m%d'), strptime(AP_CMP, '%Y%m')) // 6 * 6, 36) AS meses,
       COUNT(*) AS linhas,
       ROUND(100 * AVG((AP_CID_C1 IS NOT NULL)::INT), 1) AS pct_hipertensao,
       ROUND(100 * AVG((AP_CID_C2 IS NOT NULL)::INT), 1) AS pct_diabetes,
       ROUND(100 * AVG((AP_POLIVIT = '1')::INT), 1) AS pct_atividade_fisica,
       ROUND(100 * AVG((AP_ATV_FIS = '1')::INT), 1) AS pct_polivitaminico
FROM abo
WHERE TRY_STRPTIME(AB_DTCIRUR, '%Y%m%d') IS NOT NULL
GROUP BY 1 ORDER BY 1;
```
