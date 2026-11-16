# am — APAC Medicamentos (high-cost medicines), 2008 onward

**Source:** `AMufaamm.dbc` files in `ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados`
(e.g. `AMAC2605.dbc`). No state is split into parts. `AMPA2605.dbc` is AM for **Pará**,
not an AMP file.
**Coverage:** Jan/2008 to the latest month DATASUS has released, all 27 states. Some states
miss a few months (e.g. RN has 213 of 224 months up to Aug/2026, RS 215; SP, MG, PR and
others are complete).
**Size on the FTP** (Nov/2026): 5,986 files, about **18.9 GB** of `.dbc`, growing every
year (0.4 GB for 2008, 2.0 GB for 2025). The largest file, `AMSP2507.dbc`, is 82 MB with
1.37 million rows. Parquet takes about 0.5× the `.dbc` size.
**Fetch:** `uv run datasus fetch -T am -s AC -f 2026`.

Each row is **one APAC for medicines billed in one month**: the authorisation through which
a patient receives a medicine of the *Componente Especializado da Assistência Farmacêutica*
(CEAF): biologics for rheumatoid arthritis, somatropin, erythropoietin for kidney disease,
asthma inhalers, immunosuppressants after transplants, and similar. The row has the main
medicine (`AP_PRIPAL`, SIGTAP group 06), the diagnosis (`AP_CIDPRI`), the patient's age,
sex, race, residence, weight and height, and the APAC's validity and continuation status.

Read [APAC file types](apac.md) first: it explains authorisation, validity, monthly
continuation and the patient identifier, and describes the 46 `AP_` columns shared with
the other APAC tables.

!!! warning "Rows are APAC-months, not patients or dispensations"
    An APAC is valid for up to three months and appears in each monthly file, so a
    quarter counts most APACs three times: AC, Mar–May/2026, has 14,025 rows but 7,704
    distinct `AP_AUTORIZ` and 5,278 distinct patients. A patient on two medicines has two
    APACs. Count `DISTINCT AP_AUTORIZ` or `DISTINCT AP_CNSPCN`, depending on the question.
    There is **no quantity column**: units dispensed are only in `pa`.

## How am relates to pa (double counting)

**Every `am` row is one `pa` row with `PA_DOCORIG = 'P'`** (the APAC's main procedure),
and in AM these are exactly the `pa` rows with `PA_DOCORIG = 'P'` and `PA_TPFIN = '02'`
(*Assistência Farmacêutica*). Secondary medicines of the same APAC are in `pa` only,
as `PA_DOCORIG = 'S'` rows with the same `PA_AUTORIZ`.

Checked on AC, May/2026: `am` has 4,766 rows; `pa WHERE PA_DOCORIG = 'P' AND PA_TPFIN = '02'`
has the same 4,766 APACs, and for every one the medicine (`AP_PRIPAL` = `PA_PROC_ID`), the
diagnosis and the month agree. `SUM(AP_VL_AP)` = R$ 191,916.87 = R$ 165,548.71 on the `P`
rows + R$ 26,368.16 on the 1,322 `S` rows, APAC by APAC. That is all the pharmacy-funded
(`PA_TPFIN = '02'`) production in `pa` for the month: 6,088 rows, 218,271 units.

| You want | Use |
|---|---|
| All outpatient production, including these medicines | `pa` only |
| Units dispensed, per medicine (main and secondary) | `pa WHERE PA_TPFIN = '02'` (`PA_QTDAPR`) |
| Patients, APACs, validity, continuation, weight/height, pregnancy, transplants | `am` |
| Both: units per patient or diagnosis | join `am` to `pa` on `AP_AUTORIZ` = `PA_AUTORIZ` (example below) |

!!! danger "Never add `am` to `pa`"
    `am`'s value and APACs are already in `pa`. Also, `AP_VL_AP` is the value of the
    **whole APAC** (main plus secondary medicines): summing it with `pa`'s `S` rows counts
    the secondaries twice.

## am vs am_raw

`am_raw` holds every column as text exactly as DATASUS publishes it. `am` is the same data
with `AP_VL_AP` cast to `DOUBLE` (with `TRY_CAST`). Everything else stays text, including
codes with leading zeros (`AP_PRIPAL = '0604040040'`, `AM_PESO = '086'`) and dates
(`AP_DTINIC = '20260507'`).

## Columns

The `AP_` columns are described on the [APAC page](apac.md#shared-columns). The *Official
description* column translates the DATASUS *Informe Técnico SIASUS* (Jul/2019), section
3.4.2, *Layout do arquivo de APAC de medicamentos: AMUFAAMM.DBF*. Values in *Notes* were
checked on AC, May/2026, and SP, Jul/2025.

### Shared APAC columns: what they hold in AM

| Column | Notes for AM |
|---|---|
| `AP_PRIPAL` | The main medicine; always SIGTAP subgroup `0604` (*Componente Especializado*). Join `procedimentos.codigo` for its name. A few codes have left SIGTAP (e.g. `0604690045`, 1,983 SP rows in Jul/2025) and don't join the latest version. |
| `AP_VL_AP` | Value of the whole APAC. **0 on about 9 rows in 10** (AC: 89%; SP: 88%): mostly medicines with no SIGTAP price because the Ministry buys them centrally (somatropin, infliximab, golimumab). Not a measure of medicine spending. |
| `AP_CIDPRI` | Always informed (no `0000`); every code joined `cid10`. Most frequent in AC: M068, N180, E230, M45, J450. |
| `AP_CIDSEC`, `AP_CIDCAS` | Always `0000`. |
| `AP_TPATEN` | Always `06`. |
| `AP_TPAPAC` | `1` initial (about 1/3) or `2` continuation (2/3); no `3`. |
| `AP_TPUPS` | The dispensing unit: `43` pharmacy (95% in SP), `36` specialised clinic. |
| `AP_CODUNI` | The dispensing pharmacy. Few per state: AC has one. |
| `AP_MOTSAI` | Mostly `21` (continues); in SP also `28` (continues, other reasons), `18`, `11`, `31`, `16`, `41`. |
| `AP_CATEND` | Always `01` (elective). |
| `AP_MNDIF` | **Always `1`**, even when `AP_MUNPCN` = `AP_UFMUN`: compare those two instead. `AP_UFDIF` is correct. |
| `AP_APACANT` | Always zeros. |
| `AP_UNISOL` | Zeros on 94% of SP rows; filled in AC. |
| `AP_CODEMI` | `E` + state code + `0000001` (state secretariat) in AC; SP also has `S35…` bodies (17%). |
| `AP_CNSPCN` | Encoded; never empty. |
| `AP_UFNACIO` | `010` (Brazilian) on 99.7% of SP rows. |

### Columns specific to AM

| Column | Type | Size | Official description | Notes |
|---|---|---|---|---|
| `AM_PESO` | text | 3 | Patient's weight in kg. | Zero-padded (`070`). |
| `AM_ALTURA` | text | 3 | Patient's height in cm. | Zero-padded (`169`). |
| `AM_TRANSPL` | text | 1 | Indicates whether the patient had a transplant. | `S` / `N`; `S` on 0.4% of SP rows. |
| `AM_QTDTRAN` | text | 2 | Number of transplants. | `00` when `AM_TRANSPL = 'N'`; `01`–`03`. |
| `AM_GESTANT` | text | 1 | Pregnancy indicator (`S` yes, `N` no). | |

### Added by this package

| Column | Type | Meaning |
|---|---|---|
| `_ARQUIVO_ORIGEM` | text | DATASUS file the row came from (`AMSP2605.dbc`). |
| `competencia` | `INTEGER` | Partition: month of the file (`YYYYMM`); equals `AP_MVM`. |
| `uf` | text | Partition: state of the file (the dispensing facility's state). |

## Joins

- `AP_PRIPAL` → `procedimentos.codigo` (medicine name, SIGTAP price).
- `AP_CIDPRI` → `cid10.codigo`.
- `uf` → `ufs.uf`; `LEFT(AP_MUNPCN, 2)` → `ufs.ibge` (patient's state of residence).
- `AP_AUTORIZ` → `pa.PA_AUTORIZ` (same `competencia` and `uf`) for quantities and secondary medicines.
- No professional (CBO) column, so no join to `ocupacoes`.

## Known quirks and layout changes

- **One layout since 2008.** 50 columns until Jun/2016; `AP_NATJUR` added from Jul/2016
  (51 columns), like BI's `NAT_JUR`. The 2019 Informe lists the 50 and not `AP_NATJUR`.
  Checked on one SP file per year, 2008–2026.
- `AP_VL_AP` is a numeric (`N`) field in the DBF, unlike the text fields of PA and BI. The
  converter reads it as text like every other field; the typed view casts it.
- `AP_MNDIF` is wrong (always `1`); `AP_VL_AP` is mostly 0 (see above).
- **Conversion size.** `AMSP2507.dbc` (82 MB, 1,374,147 rows, the largest file): 28 s to
  download and convert, peak about 1.2 GB of RAM, 38.6 MB of Parquet (0.47×). The
  temporary DBF is 256 bytes per row (about 350 MB here).

## Examples

```sql
-- Patients receiving each medicine, by state, in a month
SELECT am.uf, p.nome AS medicamento, COUNT(DISTINCT AP_CNSPCN) AS pacientes
FROM am JOIN procedimentos p ON p.codigo = am.AP_PRIPAL
WHERE competencia = 202605
GROUP BY ALL ORDER BY pacientes DESC LIMIT 20;

-- Units dispensed per medicine (main and secondary), with patients, joining pa
SELECT pr.nome AS medicamento, SUM(p.PA_QTDAPR) AS unidades,
       COUNT(DISTINCT a.AP_CNSPCN) AS pacientes
FROM am a
JOIN pa p ON p.PA_AUTORIZ = a.AP_AUTORIZ AND p.competencia = a.competencia
         AND p.uf = a.uf AND p.PA_DOCORIG IN ('P', 'S')
JOIN procedimentos pr ON pr.codigo = p.PA_PROC_ID
WHERE a.competencia = 202605 AND a.uf = 'AC'
GROUP BY 1 ORDER BY pacientes DESC;

-- New patients per year for rheumatoid arthritis (ICD-10 M05/M06): first APAC per patient
-- (meaningful only with every month since 2008 fetched for the states queried)
SELECT first_month // 100 AS ano, COUNT(*) AS novos_pacientes
FROM (SELECT AP_CNSPCN, MIN(competencia) AS first_month
      FROM am WHERE AP_CIDPRI LIKE 'M05%' OR AP_CIDPRI LIKE 'M06%'
      GROUP BY 1)
GROUP BY 1 ORDER BY 1;
```
