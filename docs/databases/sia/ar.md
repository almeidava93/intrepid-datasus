# ar — APAC Radioterapia (radiotherapy), 2008 onward

**Source:** `ARufaamm.dbc` files in `ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados`
(e.g. `ARSC2605.dbc`). No state is split into parts.
**Coverage:** Jan/2008 to the latest month DATASUS has released (Aug/2026 when this was
written). A state has a file only in months its radiotherapy services billed something:
AP has files only from Dec/2025 (9 months), AC 172 of the 224 months, TO 187, SE 208, PA
and DF 221, AM, MT and RO 222, PI 223; the other 17 states are complete.
**Size on the FTP** (Nov/2026): 5,491 files, about **0.36 GB** of `.dbc`. Files are small
(the largest, `ARSP1304.dbc`, has 6,195 rows; most states have a few hundred a month).
Parquet takes about 0.8× the `.dbc` size, because each tiny file carries a fixed overhead of about 20 KB.
**Fetch:** `uv run datasus fetch -T ar -s SC -f 2024`, or the whole history with `-s all -f 2008 -t 2026`
(about 35 minutes, almost all of it FTP round trips).

Each row is **one APAC for radiotherapy** delivered by a licensed oncology facility
(CACON/UNACON with a radiotherapy service): external beam (cobalt, linear accelerator),
brachytherapy, stereotactic radiotherapy and radiosurgery. Besides the shared APAC fields
(patient, validity, exit reason), the row carries the *laudo de radioterapia*. This gives
the cancer (ICD-10), stage, lymph node invasion, histological grade, diagnosis date and
previous treatments, the same fields as in [AQ](aq.md). It also gives the **purpose** of
the radiotherapy, and up to three **treated areas**, each with its topography, start and
end dates and number of fields or insertions.

Read [APAC file types](apac.md) first: it explains authorisation, validity, monthly
continuation and the patient identifier, and describes the 46 `AP_` columns shared with
the other APAC tables. Chemotherapy is a separate file type, [AQ](aq.md); see
[AR and AQ](#ar-and-aq-the-same-patients) for how the two relate.

## One row per treatment since 2019

In **May/2019** SIGTAP replaced the radiotherapy procedures. That changes what a row is:

| | Jan/2008 – Apr/2019 | May/2019 onward |
|---|---|---|
| Procedures (`AP_PRIPAL`) | per technique, priced **per field, insertion or session**: `0304010294` linear accelerator photons + electrons (per field), `0304010286` photons only, `0304010090` cobalt therapy, `0304010073` HDR brachytherapy (per insertion), `0304010219` radiosurgery, ... | **one code per treatment and body site**, priced for the whole course: `0304010413` breast, `0304010456` prostate, `0304010537` metastases/myeloma, `0304010375` digestive tract, `0304010367` head and neck, `0304010421` gynaecological, `0304010430` gynaecological brachytherapy, ... |
| One APAC | up to three months of one technique, billed every month (`AP_TPAPAC` `1` then `2`) | the whole treatment, billed **once** (`AP_TPAPAC = 3`) |
| Rows per APAC | about 2 (2018: 289,230 rows, 148,750 APACs) | exactly 1 (2025: 176,753 rows and APACs) |
| Treated areas | up to 3 (`AR_CIDTR2` filled on 10–16% of rows) | only the 1st; `AR_CIDTR2`/`3` empty |
| Fields/insertions (`AR_NUMC1`–`3`) | filled | always empty |
| Planning, masks, imaging checks | secondary procedures in `pa` (`0304010189` complex planning, `0304010154` mask, `0304010081` image verification, ...) | included in the treatment price |

Old codes still appear until Aug/2019 as late billings, so treat **2019 as a transition
year**. Rows dropped by half and value per row went up, but the volume of care did not change:
don't compare row counts across 2019. Compare patients, or treatments from May/2019 on.
The SIGTAP price of the new codes is the value of the treatment (`0304010413` breast R$
5,904; `0304010456` prostate R$ 5,838; `0304010537` metastases R$ 1,729), and `AP_VL_AP`
equals it on almost every row.

!!! warning "Rows are not patients"
    Since 2019 a row is one treatment of one patient. A patient can have more than one
    (SC, Jan/2024–Oct/2025: 14,868 treatments of 13,515 patients; 9% had two or more,
    often a later treatment of metastases). Before 2019 a row is one APAC-month. Count
    `DISTINCT AP_CNSPCN` for patients, after removing the empty ones (see
    [following a patient](#following-a-patient)).

## How ar relates to pa (double counting)

**Every `ar` row is one `pa` row with `PA_DOCORIG = 'P'`** (the APAC's main procedure), and
these are exactly the `P` rows whose procedure starts with `030401` (*Radioterapia*,
subgroup *Tratamento em oncologia*; `030402`–`030408` are chemotherapy, in [AQ](aq.md)).
Other procedures of the same APAC are in `pa` only, as `PA_DOCORIG = 'S'` rows with the same
`PA_AUTORIZ`: before 2019 the planning, masks, collimation and image checks; since then
mostly narcosis for brachytherapy (`0304010340`) and lodging for patients (`0802010334`).

Join on **both** `AP_AUTORIZ = PA_AUTORIZ` and `AP_CMP = PA_CMP`, as for the other APAC
tables. Since Aug/2019 each APAC number appears only once in the whole table (8 exceptions
in 1.09 M rows), even though 12% of rows are billed late (`AP_CMP` before `AP_MVM`).

Checked on AC and SC, May/2026, and SE, May/2018 (old procedures):

| | AC 2026-05 | SC 2026-05 | SE 2018-05 |
|---|---|---|---|
| `ar` rows | 37 | 873 | 108 |
| `pa` `P` rows with procedure `030401…` | 37 | 873 | 108 |
| `ar` rows with exactly one `P` row (same procedure) | 37 | 873 | 108 |
| `ar` rows where `AP_VL_AP` = `SUM(PA_VALAPR)` over the `P` and `S` rows | 37 | 873 | 108 |
| `SUM(AP_VL_AP)` | R$ 157,809.00 | R$ 4,251,780.10 | R$ 82,368.00 |

`PA_TPFIN` does not single AR out: its rows are `04` (FAEC), like part of AQ. Fields and
sessions given per month (`PA_QTDAPR` of the old per-field codes, e.g. 1,884 field
applications in SE, May/2018) are in `pa` only.

| You want | Use |
|---|---|
| All outpatient production, including radiotherapy | `pa` only |
| Radiotherapy spending by procedure | `pa WHERE PA_PROC_ID LIKE '030401%'` (or `ar.AP_VL_AP`, which includes the secondary procedures) |
| Fields/sessions billed before 2019 | `pa` (`PA_QTDAPR`) |
| Patients, cancer site, stage, purpose, treated area, treatment dates | `ar` |
| Both | join `ar` to `pa` on `AP_AUTORIZ` = `PA_AUTORIZ` and `AP_CMP` = `PA_CMP` |

!!! danger "Never add `ar` to `pa`"
    `ar`'s value and APACs are already in `pa`. `AP_VL_AP` is the value of the whole APAC
    (main plus secondary procedures): summing it with `pa`'s `S` rows counts them twice.

## ar vs ar_raw

`ar_raw` holds every column as text exactly as DATASUS publishes it. `ar` is the same data
with `AP_VL_AP` cast to `DOUBLE` (with `TRY_CAST`). Everything else stays text, including
codes with leading zeros (`AP_PRIPAL = '0304010413'`, `AR_NUMC1 = '025'`) and dates
(`AR_INIAR1 = '20260504'`).

## Columns

The `AP_` columns are described on the [APAC page](apac.md#shared-columns). The *Official
description* column translates the DATASUS *Informe Técnico SIASUS* (Jul/2019), section
3.4.5, *Layout do arquivo de APAC de radioterapia: ARUFAAMM.DBF*. Values in *Notes* were
checked on every file (Jan/2008–Aug/2026, 4.08 M rows); shares quoted "since 2024" are from
Jan/2024–Aug/2026 (465,016 rows).

### Shared APAC columns: what they hold in AR

| Column | Notes for AR |
|---|---|
| `AP_PRIPAL` | The radiotherapy procedure, always `030401…`; see [one row per treatment](#one-row-per-treatment-since-2019) for the two sets of codes. Since 2019 the code names the **body site** treated. The most frequent in 2025 were breast (`0304010413`, 23%), prostate (`0304010456`, 16%), metastases/myeloma (`0304010537`), digestive tract (`0304010375`), head and neck (`0304010367`), gynaecological (`0304010421`) and gynaecological brachytherapy (`0304010430`). Join `procedimentos.codigo`; for codes before 2019, fetch old SIGTAP versions (`datasus sigtap fetch --from 2008 --yearly`). |
| `AP_CIDPRI` | **The cancer**, ICD-10, always filled. Most frequent since 2025: `C61` prostate, `C509` breast, `C795` bone metastasis, `C539` cervix, `C793` brain metastasis, `C20` rectum. Metastases (`C77`–`C79`) are coded as such: the primary cancer is not in the row. |
| `AP_CIDSEC`, `AP_CIDCAS` | `0000` on about 94% and 99% of rows. |
| `AP_TPATEN` | Always `04`. |
| `AP_TPAPAC` | Before May/2019 `1` (first month) or `2` (later months), `3` on 0.3%. Since 2020 **always `3`** (single APAC = whole treatment). |
| `AP_DTINIC`, `AP_DTFIM` | Validity, up to three months (median 73 days since 2024). The irradiation dates are in `AR_INIAR1`/`AR_FIMAR1`. |
| `AP_VL_AP` | Value of the APAC in the month, = main + secondary procedures in `pa`. Since 2019 the treatment price (above); 0 on 0.4% of rows since 2024 (4.5% over the whole history). |
| `AP_MOTSAI` | Since 2024: `18` (other discharge) 35%, `12` (improved) 33%, `15` (discharge with return for follow-up) 21%, `26` (change of procedure) 5%, `51` (administrative closure) 4%, `11` (cured) 1%, `41`–`43` (death) 0.5%. Before 2019 `21` (continues) was the most frequent (from one month to the next). |
| `AP_CATEND` | `01` (elective); `02` (urgent) on 1%; empty on 2%. |
| `AP_TPUPS` | `05` general hospital, `07` specialised hospital; also `36` (specialised clinic) and `39`. |
| `AP_UNISOL` | Equals `AP_CODUNI` on about 82% of rows: a patient can be referred by another facility. |
| `AP_APACANT` | Zeros on 85% of rows. |
| `AP_CODEMI` | `M…` (municipal secretariat) 59%, `E…` (state) 36%, also `S…`/`U…`. |
| `AP_MNDIF` | **Always `1`** (33 exceptions in 4 M rows; wrong, as in AM and AQ); compare `AP_MUNPCN` with `AP_UFMUN`. `AP_UFDIF` is correct (`1` on 3%). |
| `AP_CNSPCN` | Encoded, but **empty or `{{{{{{{{{{{{{{{` on most rows since Nov/2025**: see [following a patient](#following-a-patient). |
| `AP_NATJUR` | From Jul/2016 (`NULL` before). |

### Columns specific to AR

The laudo fields `AR_CID10` … `AR_DTINTR` are the same as AQ's `AQ_CID10` … `AQ_DTINTR`.
They are filled about as well, with one difference: `AR_TRANTE` is usable.

| Column | Type | Size | Official description | Notes |
|---|---|---|---|---|
| `AR_SMRD` | text | 3 | *Not described in the layout.* | **Always empty.** |
| `AR_CID10` | text | 4 | ICD-10 — topography. | Equals `AP_CIDPRI` on 98% of the rows where it is filled; empty on about 1 row in 4 (25% since 2024, 0% in 2008–2009). **Use `AP_CIDPRI`.** |
| `AR_LINFIN` | text | 1 | Regional lymph nodes invaded (`S` yes, `N` no, `3` not assessable). | Since 2024: `N` 66%, `S` 20%, `3` 13%. |
| `AR_ESTADI` | text | 1 | Stage — UICC (`0`, `1`, `2`, `3`, `4`). | Since 2024: `3` 26%, `2` 22%, `1` 13%, `4` 13%, `0` 5%, empty 21% (metastasis treatments, skin, benign disease). The stage at the laudo. |
| `AR_GRAHIS` | text | 2 | Histopathological grade. | Loosely coded: `0`–`12`, `00`–`06`, `G1`–`G4`, `GX`, `X`, `XX`, `II`, ... Not usable as a clean code without cleaning. |
| `AR_DTIDEN` | text | 8 | Date of the pathological identification of the case (`AAAAMMDD`). | The diagnosis date. |
| `AR_TRANTE` | text | 1 | Previous treatments (`S` yes, `N` no). | Since 2024: `N` 64%, `S` 17%, empty 18%; a few `C` in 2009–2012. Unlike AQ (mostly `0`), it is filled. |
| `AR_CIDINI1` | text | 4 | ICD-10 of the 1st previous treatment. | Filled on 14% of rows since 2024. Joins `cid10`. |
| `AR_DTINI1` | text | 8 | Start date of the 1st previous treatment (`AAAAMMDD`). | Empty or zeros when none. |
| `AR_CIDINI2`, `AR_DTINI2` | text | 4, 8 | ICD-10 and start date of the 2nd previous treatment. | |
| `AR_CIDINI3`, `AR_DTINI3` | text | 4, 8 | ICD-10 and start date of the 3rd previous treatment. | |
| `AR_CONTTR` | text | 1 | Continuity of treatment (`S` yes, `N` no). | `N` on 88% of rows since 2024 (each treatment is its own APAC). |
| `AR_DTINTR` | text | 8 | Start date of the requested treatment (`AAAAMMDD`). | Equals `AR_INIAR1` on 82% of rows since 2024. |
| `AR_FINALI` | text | 1 | Purpose of the treatment: `1` radical, `2` adjuvant, `3` pain relief (*antiálgica*), `4` palliative, `5` prior (neoadjuvant), `6` to stop bleeding (*anti-hemorrágica*). | Since May/2019: `1` 40%, `2` 35%, `4` 17%, `5` 4%, `3` 3%, `6` 2%, `7` 0.2%. Before, also `0`, `8`, `9` and `C` (rare). `7`–`9` and `0` are not in the layout. Since 2020, breast radiotherapy (`0304010413`) is 80% `2`, prostate (`0304010456`) 72% `1`, metastases (`0304010537`) 64% `4` and 18% `3`. |
| `AR_CIDTR1` | text | 4 | Topography (ICD-10) of the 1st area. | The site irradiated. Equals `AP_CIDPRI` on 98.5% of rows (the rest mostly another subsite, `C508` vs `C509`). Joins `cid10`. |
| `AR_CIDTR2`, `AR_CIDTR3` | text | 4 | Topography of the 2nd / 3rd area. | Before 2019, filled on 10–16% (`AR_CIDTR2`) of rows, e.g. breast plus regional nodes (`C773`). **Always empty since 2020.** |
| `AR_NUMC1` | text | 3 | Number of fields/insertions, 1st area. | Before 2019 only. Written two ways: the number of fields or insertions (`004`, `002`, `4`; brachytherapy `1`–`4`), or the total field applications planned (`120` = 4 fields × 30 sessions, `144`, `105`). Teletherapy codes have both: median 40–60, 10th percentile 3–4. **Always empty since 2020.** |
| `AR_NUMC2`, `AR_NUMC3` | text | 3 | Number of fields/insertions, 2nd / 3rd area. | `000` or empty when no such area. Always empty since 2020. |
| `AR_INIAR1` | text | 8 | Start date, 1st area (`AAAAMMDD`). | Start of the irradiation. Since 2024 the median time to `AR_FIMAR1` is 57 days (10%: 8 days, 90%: 89 days): it is the **planned** course within the APAC's validity, not the real last session. Empty on some rows before 2019 (8% in 2008). |
| `AR_INIAR2`, `AR_INIAR3` | text | 8 | Start date, 2nd / 3rd area. | Empty since 2020. |
| `AR_FIMAR1` | text | 8 | End date, 1st area (`AAAAMMDD`). | Can be after `AP_DTFIM` (7%) or before `AR_INIAR1` (901 rows since 2020). |
| `AR_FIMAR2`, `AR_FIMAR3` | text | 8 | End date, 2nd / 3rd area. | Empty since 2020. |

### Added by this package

| Column | Type | Meaning |
|---|---|---|
| `_ARQUIVO_ORIGEM` | text | DATASUS file the row came from (`ARSP2605.dbc`). |
| `competencia` | `INTEGER` | Partition: month of the file (`YYYYMM`); equals `AP_MVM`. |
| `uf` | text | Partition: state of the file (the treating facility's state). |

## Following a patient

`AP_CNSPCN` (encoded CNS) is the same value for the same patient across AR, AQ and the other
APAC types. Since 2019, a patient's radiotherapy history is simply their `ar` rows ordered
by `AR_INIAR1`: one row per treatment, with its site (`AP_PRIPAL`, `AR_CIDTR1`), purpose
(`AR_FINALI`), dates and exit (`AP_MOTSAI`). In SC, Jan/2024–Oct/2025, 91% of the 13,515
patients had one treatment, 8% two and 1% three or more. Among patients with two or more, 40% of
the second treatments were of a metastasis (`C77`–`C79`).

Before 2019 a treatment spans several rows: the same `AP_AUTORIZ` in two or three monthly
files (`AP_TPAPAC` `1` then `2`), with the same `AR_INIAR1`. Deduplicate on `AP_AUTORIZ`
and take the first month's laudo.

!!! danger "Patient IDs are missing on most rows since Nov/2025"
    `AP_CNSPCN` is empty (`NULL`) or the placeholder `{{{{{{{{{{{{{{{` (a blank CNS) on a
    share of rows that started in mid-2024 and **jumped in Nov/2025**. It is far worse than
    in AQ:

    | Months | All states | SP | SC | RJ | MG |
    |---|---|---|---|---|---|
    | Jan–Apr/2024 | 0% | | | | |
    | Jun–Oct/2025 | 13–21% | 12% (Jun) | 0% (Jun) | 16% (Jun) | 11% (Jun) |
    | Jan/2026 | 71% | 77% | 78% | 38% | 62% |
    | Aug/2026 | **95%** | 98% | 100% | 77% | 97% |

    Jan–Aug/2026 by state: 100% in RN, AM, CE and AP, over 80% in most states, below 25% only
    in MT, PI and TO. In the same months, AQ in SC was at 2–22%. So the cause is in the
    radiotherapy billing, not in the patient register.
    These rows cannot be followed or counted as patients (the placeholder would merge them
    into one "patient"). Add `AP_CNSPCN IS NOT NULL AND AP_CNSPCN <> '{{{{{{{{{{{{{{{'`, and
    **don't count radiotherapy patients from Nov/2025 on**. Count treatments (rows)
    instead, which are complete.

Other caveats, as for [AQ](aq.md#following-a-patient):

- **Censoring.** Treatments that started before your window were billed before it. Late
  billing adds rows for a few months, so treat the last months as incomplete.
- **Several states.** A patient treated in another state appears in that state's file
  (`AP_UFDIF = '1'` on 3% of rows).
- Deaths outside treatment are not recorded; this is not a survival dataset.

## AR and AQ: the same patients

Radiotherapy and chemotherapy APACs of one patient carry the same `AP_CNSPCN`, so they can
be joined. There is no APAC number in common: an AR APAC is never an AQ APAC. In SC,
radiotherapy of Jan/2024–Oct/2025 (before the CNS gap), against AQ of the same months
(for the breast sequence, AQ through Aug/2026):

- **75%** of the 13,515 radiotherapy patients also had a chemotherapy APAC. By cancer:
  breast 92%, rectum 91%, cervix 85%, oesophagus 86%, prostate 79% (hormone therapy),
  lung 78%, metastases (`C79`) 77%; skin 6%.
- **Concurrent treatment** (an AQ month inside the AR irradiation months,
  `AP_CMP BETWEEN LEFT(AR_INIAR1, 6) AND LEFT(AR_FIMAR1, 6)`): 59% of the 14,868
  treatments. Cervix: 691 of 909 patients (chemoradiation, AQ purpose `030404`). Rectum and
  oesophagus: mostly `030404` too.
- **Sequence for adjuvant breast radiotherapy** (`AR_FINALI = '2'`, 3,563 patients): before
  it, 890 had neoadjuvant chemotherapy (`030404`) and 2,230 adjuvant (`030405`). During and
  after it, most continued adjuvant hormone therapy (`030405`: 2,556 during, 2,895 after).
- The cancer agrees: on the same month, 77% of AR/AQ pairs had the same 3-character
  `AP_CIDPRI`. Most of the rest are metastasis codes in AR (`C795`) against the primary in
  AQ (`C61`, `C50`).

A typical breast cancer patient (SC):

| Month | Table | `AP_AUTORIZ` | `AP_PRIPAL` | Stage | Dates |
|---|---|---|---|---|---|
| 202401–202403 | aq | …2899323, …0964216 | `0304040185` neoadjuvant chemotherapy | 1 → 3 | treatment from 20231201, then 20240301 |
| 202405–202408 | aq | …1382205, …1512852 | `0304050318` + `0304050113` adjuvant (two schemes) | 3 | from 20240510 / 20240603 |
| 202408 | **ar** | …0850840 | `0304010413` breast radiotherapy, `AR_FINALI = 2` (adjuvant) | 3 | irradiation 20240801–20240831 |
| 202409–202608 | aq | a new APAC every 3 months | `0304050113` adjuvant hormone therapy | 3 | from 20240603 |

The radiotherapy laudo (`AR_DTINTR = 20240627`) was issued a month before the irradiation.

## Joins

- `AP_PRIPAL` → `procedimentos.codigo` (procedure name, site, SIGTAP price). Codes before
  May/2019 need older SIGTAP versions.
- `AP_CIDPRI`, `AP_CIDSEC`, `AR_CID10`, `AR_CIDTR1`–`3`, `AR_CIDINI1`–`3` → `cid10.codigo`.
- `uf` → `ufs.uf`; `LEFT(AP_MUNPCN, 2)` → `ufs.ibge` (patient's state of residence).
- `AP_AUTORIZ`, `AP_CMP` → `pa.PA_AUTORIZ`, `pa.PA_CMP` (same `competencia` and `uf`) for the
  secondary procedures and their values.
- `AP_CNSPCN` → `aq.AP_CNSPCN` (and the other APAC tables) for the same patient.
- No professional (CBO) column, so no join to `ocupacoes`.

## Known quirks and layout changes

- **One layout since 2008, two column sets.** 73 columns until Jun/2016; `AP_NATJUR` added
  from Jul/2016 (74). The view reads all months together and shows `NULL` for it before.
  Checked on one SP file per year 2008–2026, the change months, and recent AC, AP, RJ and
  SC files. `AP_VL_AP` is a numeric (`N`) field 20 wide (12 in AM and AQ); the converter reads
  it as text and the typed view casts it.
- **May/2019: new procedures, one row per treatment** (see
  [above](#one-row-per-treatment-since-2019)). The columns stay, but `AR_NUMC1`–`3` and the
  2nd/3rd treated areas are empty from then on.
- **Nov/2025: patient IDs mostly missing** (see [following a patient](#following-a-patient)).
- `AR_SMRD` is always empty and undocumented. `AP_MNDIF` is always `1` (wrong). `AR_GRAHIS`
  is loosely coded. `AR_FINALI` has values outside the layout (`0`, `7`–`9`).
- **Conversion size.** Files are tiny (`ARSP1304.dbc`, the largest, has 6,195 rows and
  converts in under a second). The temporary DBF is 387 bytes per row. All 5,491 files
  take 292 MB as Parquet (0.81× the `.dbc`).

## Examples

```sql
-- Radiotherapy treatments and value by site and purpose, one year (since 2019 a row = a treatment)
SELECT p.nome AS procedimento,
       CASE AR_FINALI WHEN '1' THEN 'radical' WHEN '2' THEN 'adjuvante' WHEN '3' THEN 'antiálgica'
                      WHEN '4' THEN 'paliativa' WHEN '5' THEN 'prévia' WHEN '6' THEN 'anti-hemorrágica'
                      ELSE 'outra (' || AR_FINALI || ')' END AS finalidade,
       COUNT(*) AS tratamentos, ROUND(SUM(AP_VL_AP)) AS valor
FROM ar JOIN procedimentos p ON p.codigo = ar.AP_PRIPAL
WHERE competencia BETWEEN 202501 AND 202512
GROUP BY ALL ORDER BY tratamentos DESC LIMIT 15;

-- Share of radiotherapy rows without a usable patient ID, by state, in a month
SELECT uf, COUNT(*) AS linhas,
       ROUND(100.0 * COUNT(*) FILTER (WHERE AP_CNSPCN IS NULL OR AP_CNSPCN = '{{{{{{{{{{{{{{{')
             / COUNT(*), 1) AS pct_sem_cns
FROM ar WHERE competencia = 202605
GROUP BY 1 ORDER BY pct_sem_cns DESC;

-- Cervical cancer: radiotherapy patients with chemotherapy during the irradiation
-- (chemoradiation). Fetch both: datasus fetch -T ar,aq -s SC -f 2024 -t 2025
WITH r AS (
  SELECT AP_CNSPCN, LEFT(AR_INIAR1, 6) AS ini, LEFT(AR_FIMAR1, 6) AS fim
  FROM ar
  WHERE uf = 'SC' AND competencia BETWEEN 202401 AND 202510 AND AP_CIDPRI LIKE 'C53%'
    AND AP_CNSPCN IS NOT NULL AND AP_CNSPCN <> '{{{{{{{{{{{{{{{')
SELECT COUNT(DISTINCT r.AP_CNSPCN) AS pacientes_rt,
       COUNT(DISTINCT r.AP_CNSPCN) FILTER (WHERE q.AP_CMP BETWEEN r.ini AND r.fim) AS com_qt_concomitante
FROM r LEFT JOIN aq q ON q.AP_CNSPCN = r.AP_CNSPCN AND q.uf = 'SC';
```
