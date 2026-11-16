# RAAS file types — what a RAAS is, and the shared columns

The **RAAS** (*Registro das Ações Ambulatoriais de Saúde*) is the record SUS facilities use
for care that goes on month after month with the same patient: psychosocial care in
**CAPS** (*Centros de Atenção Psicossocial*) and **home care** (*Atenção Domiciliar*).
It replaced the APAC for those kinds of care in 2012–2013, with no authorisation step:
the facility registers the patient once and then records what it did each month.
DATASUS publishes one file type per RAAS:

| Code | RAAS | Table | Status |
|---|---|---|---|
| PS | Psychosocial care (*Atenção Psicossocial*): CAPS, from Nov/2012 | [`ps`](ps.md) | supported |
| SAD | Home care (*Atenção Domiciliar*), Apr/2012 to Oct/2018 | | planned |

Files are named `<CODE><UF><YY><MM>.dbc` (`PSSP2605.dbc`, `SADSP1801.dbc`). States with no
RAAS production in a month have no file that month (PS: 4,421 files over 166 months, not
166 × 27).

## How a RAAS works

The DATASUS RAAS software (manual: *Manual Operacional RAAS*, Ministério da Saúde, v1.5,
built on RAAS 01.40) records:

- **One care episode per patient and facility** (*atendimento*), identified by the month,
  the facility (`CNES_EXEC`), the patient's encoded CNS (`CNS_PAC`) and the start date
  (`DT_INICIO`). The first month is the *initial* record, where the facility gives the
  patient's origin (`ORIGEM_PAC`), the main diagnosis (`CIDPRI`) and the Family Health
  coverage (`COB_ESF`, `CNES_ESF`). Later months are *continuations*: the software copies
  those fields forward, so they keep the values of the first month.
- **Destination.** `DESTINOPAC = '00'` (*permanência*) means the patient stays in care and
  the record is reopened next month; any other code closes the episode and needs an end
  date (`DT_FIM`).
- **Actions of the month.** Each month the facility lists the actions done (`PA_PROC_ID`,
  SIGTAP procedures whose *instrumento de registro* is `09 - RAAS (Atenção Psicossocial)`
  or `08 - RAAS (Atenção Domiciliar)`), each with a quantity, a date, the professional and
  CBO. The same action can appear on several lines (different days or professionals).

DATASUS publishes the **action lines**: one row per line, with the episode's fields repeated
on each. The professional's CNS and CBO, and the day of the action, are **not** in the
published files. So one row is neither a patient nor a month: count patients with
`COUNT(DISTINCT CNS_PAC)` and procedures with `SUM(PA_QTDAPR)`.

There is no authorisation number. To find the same rows in `pa`, use the facility, month
and procedure (see [How RAAS reaches pa](#how-raas-reaches-pa)).

## How RAAS reaches pa

SIA turns every RAAS action line into a PA row (Informe Técnico SIASUS, section 2): with
`PA_DOCORIG = 'B'` for RAAS Psicossocial and `'A'` for RAAS Atenção Domiciliar. The PA row
has no patient CNS and no RAAS identifier, but the same facility (`PA_CODUNI = CNES_EXEC`),
processing and care months (`PA_MVM`, `PA_CMP` = `DT_PROCESS`, `DT_ATEND`) and procedure
(`PA_PROC_ID`). Compare totals by those keys, not row by row. **RAAS rows in `pa` carry no
value** (`PA_VALAPR = 0`): CAPS and home-care teams are paid by fixed monthly incentives,
not by procedure, so the RAAS files have no value column either.

## Shared columns

PS and SAD use the same 40 columns, without the `AP_` prefix of the APAC files and with the
procedure and quantity columns named as in PA (`PA_PROC_ID`, `PA_QTDPRO`, `PA_QTDAPR`).
In `datasus` they are one dictionary, `dictionary.RAAS_COMMON`, used by
`dictionary.raas(code, own)`. Each type adds its own columns:

| Type | Own columns |
|---|---|
| PS | `TIPPRE`, `SIT_RUA`, `TP_DROGA`, `LOC_REALIZ` |
| SAD | `PA_EQUIPE`, `PA_TP_EQP`, `PA_CID` (team, team type, diagnosis of the action) |

| Column | Size | Official description (Informe Técnico SIASUS, Jul/2019, section 4) |
|---|---|---|
| `CNES_EXEC` | 7 | Facility (CNES) that delivered the care. = `PA_CODUNI`. |
| `GESTAO` | 6 | State + municipality of the manager, or `UF0000` under state management. |
| `CONDIC` | 2 | Type of management the state or municipality is qualified for. |
| `UFMUN` | 6 | State + municipality of the **facility**. |
| `TPUPS` | 2 | Facility type (CNES). |
| `MN_IND` | 1 | Facility maintained (*mantido*) / individual. |
| `CNPJCPF` | 14 | CNPJ of the facility. |
| `CNPJMNT` | 14 | CNPJ of the maintaining body, or zeros. |
| `DT_PROCESS` | 6 | Processing month (`AAAAMM`); = `competencia`, `PA_MVM`. |
| `DT_ATEND` | 6 | Month of care (`AAAAMM`); = `PA_CMP`. |
| `CNS_PAC` | 15 | Patient's CNS, encoded by DATASUS. |
| `DTNASC` | 8 | Patient's date of birth. |
| `TPIDADEPAC` | 1 | Unit of the age (days, months, years), computed from the date of birth. |
| `IDADEPAC` | 2 | Patient's age. |
| `NACION_PAC` | 2 | Patient's nationality. |
| `SEXOPAC` | 1 | Patient's sex. |
| `RACACOR` | 2 | Race/colour: `01` white, `02` black, `03` brown, `04` yellow, `05` indigenous, `99` no information. |
| `ETNIA` | 4 (2 in the files) | Indigenous ethnicity (when `RACACOR = '05'`). |
| `MUNPAC` | 6 | State + municipality where the **patient lives**. |
| `MOT_COB` | 2 | Reason for exit/continuation (*motivo de saída/permanência*). |
| `DT_MOTCOB` | 8 | Date of the discharge, transfer or death. |
| `CATEND` | 2 | Type of care (*caráter de atendimento*). |
| `CIDPRI` | 4 | Main diagnosis (ICD-10). |
| `CIDASSOC` | 4 | Associated causes (ICD-10). |
| `ORIGEM_PAC` | 2 | Origin of the patient. |
| `DT_INICIO` | 8 | Start date (of the episode). |
| `DT_FIM` | 8 | End date (of the episode). |
| `COB_ESF` | 1 | The patient's area is covered by the Family Health Strategy (ESF). |
| `CNES_ESF` | 7 | CNES of the area's Family Health unit. |
| `DESTINOPAC` | 2 | Destination of the patient. |
| `PA_PROC_ID` | 10 | Procedure (*ação realizada*). |
| `PA_QTDPRO` | 11 | Quantity produced (submitted). The Informe calls it `QT_APRES` in PS. |
| `PA_QTDAPR` | 11 | Quantity approved. The Informe calls it `QT_APROV` in PS. |
| `PA_SRV` | 3 | Specialised service code. The Informe calls it `SERV` in PS. |
| `PA_CLASS_S` | 3 | Service classification. The Informe calls it `CLASS` in PS (`PA_CLAS_S` in SAD). |
| `INICIO` | 8 | Start date of the care (`DDMMAAAA` per the Informe). |
| `FIM` | 8 | End date of the care (`DDMMAAAA` per the Informe). |
| `PERMANEN` | 4 | Length of stay in care (*permanência*). |
| `QTDATE` | 4 | Number of care contacts (*quantidade de atendimentos*). |
| `QTDPCN` | 4 | Number of patients. |

Plus `NAT_JUR` (legal nature, 4), appended last from Jul/2016 (and, in PS, in the Oct/2014
files only).

What each column holds in practice differs from the official text in several places (the
dates are `YYYYMMDD`, not `DDMMAAAA`; `INICIO`…`QTDPCN` are only filled on some
procedures): see the page of each type, [ps](ps.md#what-the-columns-hold).
