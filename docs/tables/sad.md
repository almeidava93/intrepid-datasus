# sad — RAAS Atenção Domiciliar (home care), Apr/2012 to Oct/2018

**Source:** `SADufaamm.dbc` files in `ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados`
(e.g. `SADSP1505.dbc`). No split files.
**Coverage:** Apr/2012 to Oct/2018, **discontinued**. In practice the series ends in
**Jun/2016**: the home-care teams moved to another system from Aug/2015 (see
[After SAD](#after-sad-where-home-care-data-went)), and the 2017–2018 files hold one procedure
from 4–5 facilities. 25 states have at least one file (none from ES or RR; MT only Jun–Nov/2015, SE only Oct/2014–Oct/2015);
a state with no RAAS that month has no file.
**Size on the FTP** (Nov/2026): 1,088 files, **53 MB** of `.dbc`, 3.52 M rows. Parquet takes
47 MB (0.89× the `.dbc`: the files are tiny, ~49 KB on average). The largest is
`SADSP1505.dbc` (0.86 MB, 58.7 k rows).
**Fetch:** `uv run datasus fetch -T sad -s all -f 2012 -t 2018` (the whole history, 15–20 min: the files are small but each takes a few seconds on the FTP).

SAD holds the care delivered at home by the teams of the **Programa Melhor em Casa**
(*Serviço de Atenção Domiciliar*): EMAD (multiprofessional home-care teams) and EMAP
(support teams), recorded on the RAAS (*Registro das Ações Ambulatoriais de Saúde*) for home
care, created by Portaria SAS/MS 276/2012 from Apr/2012. Read [RAAS file types](raas.md)
first: it explains what a RAAS is (one care episode per patient and facility, re-recorded
every month with that month's actions) and describes the columns SAD shares with PS.

## What is in SAD

Every row is one action line of a home-care patient's monthly RAAS: one SIGTAP procedure,
with its quantity. 69 procedure codes over the history; the main ones:

| Procedure | SIGTAP name (short) | Rows | % rows | Approved qty |
|---|---|---|---|---|
| `0301010137` | Home consultation (*consulta/atendimento domiciliar*) | 672 k | 19.1% | 750 k |
| `0301050023` | Home care by a multiprofessional team | 473 k | 13.4% | 558 k |
| `0301050058` | Home care by a mid-level professional | 457 k | 13.0% | 510 k |
| `0101030010` | Home visit by a mid-level professional | 390 k | 11.1% | 436 k |
| `0301050147` | Home visit by a higher-level professional | 367 k | 10.4% | 411 k |
| `0401010023` | Wound dressing grade I (retired from SIGTAP after May/2015) | 200 k | 5.7% | 284 k |
| `0214010015` | Capillary glucose | 139 k | 4.0% | 158 k |
| `0302050027` | Physiotherapy, motor disorders | 126 k | 3.6% | 140 k |
| `0301050031` | Home care by a multiprofessional team in specialised care | 114 k | 3.2% | 117 k |
| `0101030029` | Home/institutional visit by a higher-level professional | 94 k | 2.7% | 110 k |
| `0401010015` | Wound dressing grade II | 92 k | 2.6% | 134 k |
| 58 others | lab sample collection, respiratory and neuro physiotherapy, rehabilitation, parenteral antibiotics, medication, oxygen therapy, bladder catheter, post-death visit, ... | 399 k | 11.3% | |

Patients are mostly old and bedridden: 68% of patient-months are of people aged 60 or more,
and the main diagnoses (`CIDPRI`) are stroke and its sequelae (`I69`, `I694`, `I64`),
hypertension (`I10`), Alzheimer's disease (`G30`), COPD (`J44`), femur fracture (`S72`),
pressure ulcers (`L89`), cerebral palsy (`G80`) and paraplegia (`G82`).

### By year

| Year | Rows | Patient-months (RAAS) | Distinct patients | Approved actions | Facilities | States | Rows per RAAS |
|---|---|---|---|---|---|---|---|
| 2012 (Apr–Dec) | 135 k | 24,243 | 10,185 | 158 k | 113 | 18 | 5.6 |
| 2013 | 541 k | 81,030 | 27,818 | 619 k | 249 | 23 | 6.7 |
| 2014 | 1.13 M | 152,691 | 47,397 | 1.31 M | 426 | 24 | 7.4 |
| 2015 | 1.55 M | 199,458 | 57,458 | 1.78 M | 464 | 25 | 7.8 |
| 2016 | 159 k | 20,041 | 10,711 | 201 k | 211 | 21 | 7.9 |
| 2017 | 4.9 k | 1,488 | 641 | 6.0 k | 8 | 5 | 3.3 |
| 2018 (Jan–Oct) | 1.2 k | 383 | 170 | 291 | 4 | 3 | 3.0 |

SP has 39% of all rows, then RJ 10%, BA 8%, PE 7%, PR 7%, MG 6%. Whole history: 116,283
distinct patients, 135,173 episodes (facility, patient, start date), 524 facilities.

## One row is one action line, not a patient

Same structure as [PS](ps.md#one-row-is-one-action-line-not-a-patient). A RAAS is one
**episode-month**: facility (`CNES_EXEC`), patient (`CNS_PAC`), start of the episode
(`DT_INICIO`) and month of care (`DT_ATEND`). Each has 5–8 rows (7.8 in 2015), one per action
line. **One row of every episode-month** has `QTDATE = '1'` and `QTDPCN = '1'`; on that row,
and only on it, `INICIO` and `FIM` are the first and last days in care in that month
(`YYYYMMDD`, not the `DDMMAAAA` of the Informe) and `PERMANEN` is the number of days.
Checked on every row: of the 480,285 episode-months, none has two such rows and 951 (0.2%)
have none; `QTDATE` and `QTDPCN` differ on 951 rows; 966 summary rows lack `INICIO` or
`PERMANEN`, and `PERMANEN = FIM - INICIO + 1` on all others but 38.

| You want | Use |
|---|---|
| Patients in care in a month (RAAS) | `SUM(QTDPCN::INT)`, or `COUNT(*) WHERE QTDPCN = '1'` |
| Distinct patients over a period | `COUNT(DISTINCT CNS_PAC)` (never the encoded blank in SAD) |
| Actions (procedures) | `SUM(PA_QTDAPR)`, not `COUNT(*)` |
| Days in home care | `SUM(PERMANEN::INT) WHERE QTDPCN = '1'` |
| Teams | `PA_EQUIPE` until Jul/2015, `CO_INE` from Aug/2015 (see [quirks](#known-quirks-and-layout-changes)) |

## How sad relates to pa (double counting)

**Every row of `sad` is also in `pa`**: the rows with `PA_DOCORIG = 'A'` (RAAS Atenção
Domiciliar), with **no value** (`PA_VALAPR = 0`: the teams are paid by a fixed monthly
incentive). There is no RAAS number in `pa`, so compare by facility, care month and
procedure: `CNES_EXEC = PA_CODUNI`, `DT_ATEND = PA_CMP`, `PA_PROC_ID`, within the same
`competencia` and `uf`.

| State-month | `sad` rows | `pa` `A` rows | `sad` `SUM(PA_QTDAPR)` | `pa` `A` | Keys equal |
|---|---|---|---|---|---|
| SE 2014-10 (45 columns) | 47 | 47 | 47 | 47 | 9 of 9 |
| AC 2015-05 | 1,414 | 1,414 | 1,668 | 1,668 | 22 of 22 |
| AC 2016-05 | 1,042 | 1,042 | 1,146 | 1,146 | 10 of 10 |
| MA 2016-06 | 21 | 21 | 25 | 25 | 2 of 2 |
| MA 2017-06 | 254 | 254 | 479 | 479 | 2 of 2 |
| PI 2018-04 | 268 | 268 | 0 | 0 | 3 of 3 |
| MA 2018-10 (last file) | 33 | 33 | 33 | 33 | 2 of 2 |

Rows, `PA_QTDPRO` and `PA_QTDAPR` are equal for every (facility, care month, procedure) key.
`PA_DOCORIG = 'A'` selects SAD exactly.

!!! danger "Never add `sad` to `pa`"
    Summing quantities over `pa` and `sad` counts every RAAS action twice. Values are not
    affected (RAAS rows are R$ 0 in `pa`), but procedure counts are.

**Not all home care is in SAD**, even before 2016: the same SIGTAP home-care procedures
(`030105…`, `0301010137`, `010103…`) are also billed on BPA by other services, as `pa` rows
with `PA_DOCORIG = 'C'` or `'I'`. Primary care units bill `0301050058` on BPA-C (SE Oct/2014:
316 `C` rows, 11,289 procedures, 235 facilities, against 47 SAD rows), and hospital home-care
programmes bill `0301050023`, `0301050031` and `0301050147` on BPA-I. For all home-care
production of a month, query `pa`; for patients, teams and diagnoses (until 2016), `sad`.

## After SAD: where home care data went

The RAAS-AD was replaced by the **e-SUS Atenção Domiciliar** module of e-SUS AB, whose data go
to **SISAB** (*Sistema de Informação em Saúde para a Atenção Básica*), not to SIA:
Portaria GM/MS 1.653 of 2 Oct 2015, which added home care to the SISAB Portaria
(GM/MS 1.412/2013). The Ministry's technical note on checking home-care production
(CGAD/DAHU/SAS, *Nota Técnica 008/2016*, replaced by *Nota Técnica 15/2025*) says the home-care
services' records "were incorporated into e-SUS AB, through the e-SUS AD module, replacing the
use of RAAS". The files show the switch:

- **Aug/2015:** the team code (`PA_EQUIPE`, `PA_TP_EQP`) is replaced by the INE (`CO_INE`).
- **Jan/2016:** rows fall from 113 k (Dec/2015) to 46 k; **Jun/2016:** 281 rows from 9 states.
- **2017–Oct/2018:** only `0101030029` (home visit by a higher-level professional) from 2 MA,
  2 GO, 2 SP, 1 PI and 1 CE facilities. The last file is `SADMA1810.dbc` (33 rows).

After that, **no `PA_DOCORIG = 'A'` rows in `pa`** (checked: AC 2019-05, MA 2019-05,
MA 2024-05). What remains in `pa` is the BPA home-care billing described above: in MA
May/2019, 148 `C` rows (7,853 procedures, mostly `0301050058` from 109 primary care units) and
648 `I` rows from 3 hospitals; in May/2024, 26 `C` rows and 820 `I` rows. That is not the
Melhor em Casa programme's production, which since 2016 is only in SISAB (public reports at
`sisab.saude.gov.br`, no individual records on the DATASUS FTP). **For home care after mid-2016
this package has no source.**

```sql
-- Home-care rows in pa by record instrument, per month (needs pa fetched)
SELECT competencia, PA_DOCORIG, COUNT(*) AS linhas, SUM(PA_QTDAPR) AS procedimentos
FROM pa
WHERE PA_DOCORIG = 'A' OR PA_PROC_ID LIKE '030105%'
GROUP BY ALL ORDER BY 1, 2;
```

## sad vs sad_raw

`sad_raw` holds every column as text exactly as DATASUS publishes it. `sad` is the same data
with `PA_QTDPRO`/`PA_QTDAPR` cast to `BIGINT` (with `TRY_CAST`). Everything else stays text,
including `QTDATE`, `QTDPCN` and `PERMANEN` (cast them: `QTDPCN::INT`) and dates.

## Columns

The shared RAAS columns are described on [RAAS file types](raas.md#shared-columns); `datasus
schema -T sad` lists them all with descriptions. Values below are from the whole history
(3.52 M rows).

### What the columns hold

| Column | In SAD |
|---|---|
| `CNES_EXEC` | 524 facilities; 464 in 2015. |
| `TPUPS` | **Not the facility type**: it holds the provider type (*tipo de prestador*), the value of `pa`'s `PA_TIPPRE`: `50` 77%, `00` 12%, `40` 8%, `30` 2%, `61` 1%. The facility type is `PA_TPUPS` in `pa` (`02` health centre, `05` general hospital). |
| `CONDIC` | `PG` 70%, `MN` 20%, `EP` 10%, `PA` 0.7%. |
| `MN_IND` | `M` 97%, `U` 3%. |
| `DT_ATEND` | Differs from `DT_PROCESS` on 12% of rows (late reports). |
| `CNS_PAC` | Never `NULL`, never the encoded blank `'{{{{{{{{{{{{{{{'`. |
| `TPIDADEPAC` / `IDADEPAC` | Years on 97.5% of rows; ages 76–84 are the commonest. |
| `SEXOPAC` | `F` 53%, `M` 47%. |
| `RACACOR` | `01` white 39%, `99` not informed 29%, `03` brown 26%, `02` black 6%, `04` yellow 0.7%. |
| `ETNIA` | Practically always `NULL`. |
| `MOT_COB` | `21` (continues) 88%, `11` cured 2.9%, `18` other discharge 2.4%, `12` improved 2.2%, `41` death 1.7%, `31` transfer 1.3%, `51` closed administratively 0.9%, `28` 0.3%. |
| `DESTINOPAC` | `00` (stays in care) 89%; the others close the episode and come with a matching `MOT_COB`: `01`–`11` (cured), `02`–`12` (improved), `03`–`18` (other discharge), `04`/`05`–`31` (transfer), `06`–`41` (death). No code names in the Informe. |
| `DT_FIM` | Filled on 11% of rows (the closing months; 13 k rows with `DESTINOPAC = '00'` have one too). |
| `DT_MOTCOB` | Filled on 0.4%; use `DT_FIM`. |
| `CATEND` | `01` elective on 99.8%. |
| `CIDPRI` | `NULL` on 10% of rows. See [What is in SAD](#what-is-in-sad). |
| `CIDASSOC` | `NULL` on 68%; `I10` hypertension 7%, `L89` 4%, diabetes (`E10`, `E11`, `E14`). |
| `ORIGEM_PAC` | `02` 55%, `03` 23%, `05` 15%, `01` 6%, `04` 0.7%. No code list in the Informe, nor in Portaria SAS 276/2012. |
| `COB_ESF` / `CNES_ESF` | `S` on 36% of rows; `CNES_ESF` filled on those. |
| `INICIO`, `FIM`, `PERMANEN` | `YYYYMMDD`, on the `QTDPCN = '1'` rows only (13.6% of rows); `PERMANEN` `31` / `30` on most. |
| `PA_SRV` / `PA_CLASS_S` | `113` (home care) on all but 9 rows (`126`); class `003` 93%, `004` 7%. |
| `PA_QTDAPR` | Equal to `PA_QTDPRO` on all but 19 rows; `0` on 0.7%, and on every PI row of 2017–2018. |
| `NAT_JUR` | Only in the Oct/2014 files (filled) and from Jul/2016 (9,079 rows): `1031` municipal executive body, `1201` public fund (e.g. municipal health fund), `1023`, `1244`. |

### SAD-only columns

| Column | Size | Official description | Notes |
|---|---|---|---|
| `PA_EQUIPE` | 12 | Team code (only for the RAAS instrument). | CNES team code, filled on every row until Jul/2015; then almost always `NULL` (69% in Aug/2015, 92–100% from Sep/2015), replaced by `CO_INE`. 778 teams. |
| `PA_TP_EQP` | 2 | Team type (only for the RAAS instrument). | `22` EMAD (56% of rows), `23` EMAP (10%), `46` EMAD type II (from 2013, 2%). `NULL` on 32%: 2–52% a month in 2012, 8–18% from 2014 to Jul/2015, then on almost every row. |
| `PA_CID` | 4 | ICD-10 of the procedure. | Filled on 39% of rows; differs from `CIDPRI` on 16% of those. |
| `CO_INE` | 10 | Not in the Informe. | National team identifier (INE). Column from Jan/2015 (and in the Oct/2014 files, empty there); filled from Aug/2015 (80% of rows), 97–100% from Sep/2015. |

### Added by this package

| Column | Type | Meaning |
|---|---|---|
| `_ARQUIVO_ORIGEM` | text | DATASUS file the row came from (`SADSP1505.dbc`). |
| `competencia` | `INTEGER` | Partition: month of the file (`YYYYMM`) = `DT_PROCESS`. |
| `uf` | text | Partition: state of the file. |

## Joins

| From | To | Note |
|---|---|---|
| `PA_PROC_ID` | `procedimentos.codigo` | `0401010023` (wound dressing grade I) was retired after May/2015: fetch that SIGTAP version (`datasus sigtap fetch -f 201505`) to name it. |
| `CIDPRI`, `CIDASSOC`, `PA_CID` | `cid10.codigo` | 3- and 4-character codes both join. |
| `uf` | `ufs.uf` | State of the facility. |
| `LEFT(MUNPAC, 2)` | `ufs.ibge` | State where the patient lives. |
| `CNES_EXEC`, `DT_ATEND`, `PA_PROC_ID` | `pa` (`PA_CODUNI`, `PA_CMP`, `PA_PROC_ID`, `PA_DOCORIG = 'A'`) | Totals only; no row key. |

`sad` has no occupation (CBO) column: the professional of each action is recorded on the
RAAS but not published (`pa` has `PA_CBOCOD` for the same rows).

## Known quirks and layout changes

- **One layout, three column sets** (every one of the 1,088 files probed): 43 columns
  (record 236 bytes) from Apr/2012 to Dec/2014; **`CO_INE`** appended (44, 246 bytes) from
  Jan/2015; **`NAT_JUR`** appended after it (45, 250 bytes) in the **Oct/2014** files of every
  state and from Jul/2016 to the end. Missing columns are `NULL` in the view.
- **`TPUPS` is the provider type**, not the facility type as in PS (see the table above).
- **The team identifier changes in Aug/2015**: `PA_EQUIPE`/`PA_TP_EQP` until Jul/2015,
  `CO_INE` from Aug/2015. Count teams with `COALESCE(CO_INE, PA_EQUIPE)` only within one
  period: the two codes don't match.
- **The Informe's names and sizes differ from the files**: `PA_CLAS_S` is `PA_CLASS_S`,
  `DESTINO_PAC` is `DESTINOPAC`, `DT_INÍCIO`/`DT_INICIO` (twice) are `DT_INICIO` and `INICIO`,
  `DT_FIM` (twice) are `DT_FIM` and `FIM`, `PERMANENCIA` is `PERMANEN`; `ETNIA` is 2 characters
  (4 in the Informe), `PA_SRV`/`PA_CLASS_S` 3 (4); `CO_INE` and `NAT_JUR` are missing; dates
  are `YYYYMMDD`, not `DDMMAAAA`.
- **Apr/2012** is the first month (5 states: CE, PE, PR, RN, SP); the number of states with a
  file peaks at 25 in Jun, Jul, Sep and Oct/2015, then falls to 9 in Jun/2016 and 1 (MA) from Jul/2018.
- **A long tail after mid-2016** that is not a series: see [After SAD](#after-sad-where-home-care-data-went).
  Don't read the 2016 fall as less home care.

## Examples

```sql
-- Home-care patient-months, patients and actions per month
SELECT competencia,
       SUM(QTDPCN::INT) AS pacientes_mes,
       COUNT(DISTINCT CNS_PAC) AS pacientes,
       SUM(PA_QTDAPR) AS acoes
FROM sad WHERE competencia BETWEEN 201204 AND 201606
GROUP BY 1 ORDER BY 1;

-- Main diagnoses of home-care patients in 2015 (one count per RAAS)
SELECT COALESCE(c.nome, sad.CIDPRI) AS diagnostico, SUM(QTDPCN::INT) AS pacientes_mes
FROM sad LEFT JOIN cid10 c ON c.codigo = sad.CIDPRI
WHERE competencia BETWEEN 201501 AND 201512
GROUP BY 1 ORDER BY 2 DESC LIMIT 15;

-- How episodes end: discharge, transfer, death (closing rows only)
SELECT DESTINOPAC, MOT_COB, COUNT(DISTINCT (CNES_EXEC, CNS_PAC, DT_INICIO)) AS episodios
FROM sad WHERE DESTINOPAC <> '00'
GROUP BY ALL ORDER BY 3 DESC;

-- Actions by team type (EMAD / EMAP), until Jul/2015
SELECT PA_TP_EQP, p.nome, SUM(PA_QTDAPR) AS acoes
FROM sad JOIN procedimentos p ON p.codigo = sad.PA_PROC_ID
WHERE competencia BETWEEN 201401 AND 201507 AND PA_TP_EQP IS NOT NULL
GROUP BY ALL ORDER BY 1, 3 DESC;
```
