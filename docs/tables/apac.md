# APAC file types — what an APAC is, and the shared `AP_` columns

An **APAC** (*Autorização de Procedimentos Ambulatoriais*) is a prior authorisation for a
high-cost or long outpatient treatment: specialised medicines, chemotherapy, radiotherapy,
dialysis, bariatric surgery follow-up, and so on. DATASUS publishes the APACs billed each
month in one file type per kind of request form (*laudo*):

| Code | Laudo | Table | Status |
|---|---|---|---|
| AM | Medicines (Componente Especializado da Assistência Farmacêutica) | [`am`](am.md) | supported |
| AQ | Chemotherapy (oncology) | [`aq`](aq.md) | supported |
| AR | Radiotherapy (oncology) | [`ar`](ar.md) | supported |
| AD | Diverse requests (*laudos diversos*): eye, cardiology, hearing, ostomy, orthopaedic aids, transplant follow-up, ... | [`ad`](ad.md) | supported |
| ATD | Dialysis (from Aug/2014) | [`atd`](atd.md) | supported |
| AN | Nephrology: dialysis, Jan/2008 to Jul/2014 (late bills to Oct/2014; replaced by ATD, see [the transition](atd.md#from-an-to-atd-2014)) | [`an`](an.md) | supported |
| AB | Bariatric surgery follow-up | | planned |
| ABO | Post-bariatric surgery follow-up | | planned |
| ACF | Arteriovenous fistula creation | | planned |
| AMP | Multiprofessional follow-up | | planned |

Files are named `<CODE><UF><YY><MM>.dbc` (`AMSP2605.dbc`, `ATDSP2605.dbc`). Careful when
listing the FTP by prefix: `AMPA2605.dbc` is **AM for Pará**, not AMP; AMP files have the
state after the `P` (`AMPSP2605.dbc`). `datasus` matches the full pattern, so it never mixes them.

## How an APAC works

- **Request and authorisation.** A facility (`AP_UNISOL`) fills in a *laudo* for a patient
  on `AP_DTSOLIC`; the authorising body (`AP_CODEMI`, usually the state health secretariat)
  authorises it on `AP_DTAUT` and gives it a 13-digit number, `AP_AUTORIZ`
  (`UFAATsssssssd`: state, year, type, sequence, check digit).
- **Validity period.** An APAC is valid from `AP_DTINIC` to `AP_DTFIM`, up to three months
  (competências). In AM, an APAC starting in May/2026 ends on 31/Jul/2026.
- **Monthly billing and continuation.** The executing facility (`AP_CODUNI`) bills the APAC
  every month of its validity, so **the same APAC appears in up to three monthly files**,
  with the same `AP_AUTORIZ` and `AP_DTINIC`: `AP_TPAPAC = 1` in the first month,
  `2` (continuation) in the following ones, or `3` for a single-month APAC. After that, a
  new APAC is issued if treatment goes on. (AC, Mar–May/2026, AM: 3,215 of the 4,766 May
  APACs had already been billed in April under the same number.) Some types bill a whole
  treatment as one single APAC instead: radiotherapy (AR) since 2019 is always `3`, one row
  per treatment (see [ar](ar.md#one-row-per-treatment-since-2019)).
- **Exit.** `AP_MOTSAI` gives the reason the APAC ends or continues; the flags
  `AP_OBITO`, `AP_ALTA`, `AP_TRANSF`, `AP_ENCERR`, `AP_PERMAN` repeat it as 0/1, and
  `AP_DTOCOR` is the date of the event, which replaces the end of validity.
- **Patient.** Every APAC is for one identified patient: encoded national health card
  (`AP_CNSPCN`), age, sex, race/colour, nationality, postcode and municipality of residence.
  One patient can hold several APACs at once (one per medicine in AM).

## What one row is, and the link to `pa`

In the APAC files, **one row is one APAC billed in one month**: the main procedure
(`AP_PRIPAL`), the diagnosis and the approved value of the whole APAC (`AP_VL_AP`).

The same APACs are in `pa`, with one row **per procedure** of the APAC:
`PA_DOCORIG = 'P'` for the main procedure and `'S'` for each secondary one, with their
quantities (`PA_QTDAPR`) and values. Join on the authorisation number within the same
month and state:

```sql
SELECT a.AP_AUTORIZ, a.AP_VL_AP, p.PA_DOCORIG, p.PA_PROC_ID, p.PA_QTDAPR, p.PA_VALAPR
FROM am a
JOIN pa p ON p.PA_AUTORIZ = a.AP_AUTORIZ AND p.PA_CMP = a.AP_CMP
         AND p.competencia = a.competencia AND p.uf = a.uf
WHERE a.competencia = 202605 AND a.uf = 'AC' AND p.PA_DOCORIG IN ('P', 'S');
```

Join on `AP_CMP = PA_CMP` too: a month's file can hold the same APAC twice, once for the
current month and once billed late for an earlier one (AQ, SC May/2026: 6,195 of 22,109 rows
have `AP_CMP` before `AP_MVM`). `(AP_AUTORIZ, AP_CMP)` is unique within a file.

Checked for AM, AQ, AR and AD, AC May/2026 (and SC for AQ and AR, SE for AD): every APAC row is exactly one `pa` row
with `PA_DOCORIG = 'P'`, and `AP_VL_AP` equals the sum of `PA_VALAPR` over the APAC's `P`
and `S` rows. The APAC
files carry no quantity column, so for quantities use `pa`.

!!! danger "Don't add APAC tables to `pa`"
    APAC production is already in `pa`. Summing `pa` and an APAC table counts it twice.
    Use the APAC table for what `pa` lacks: one row per authorisation, validity dates,
    continuation, exit reason, the request, and the laudo's own clinical fields.

## Counting

- **APACs billed in a month:** `COUNT(*)` (one row per APAC per month).
- **Distinct authorisations over several months:** `COUNT(DISTINCT AP_AUTORIZ)`; counting
  rows over a quarter counts most APACs up to three times.
- **Patients:** `COUNT(DISTINCT AP_CNSPCN)`. The CNS is encoded by DATASUS (non-digit
  characters), consistently within the data, so it identifies a patient across months and
  APAC types but cannot be linked to other systems. In AQ, AR, AD and ATD it is **empty or a
  placeholder** (`{{{{{{{{{{{{{{{`) on a growing share of rows since 2024 (see
  [aq](aq.md#following-a-patient); in AR 95% of all rows by Aug/2026, see
  [ar](ar.md#following-a-patient); in AD 67% in Aug/2026, see
  [ad](ad.md#patients); in ATD 96% in Aug/2026, see [atd](atd.md#patients)); check the
  type's page before counting patients.

## Shared columns

Every APAC file type has these columns, with the same names and meaning (plus its own
columns, prefixed with its code: `AM_PESO`, `AQ_ESTADI`, ...). They are described once
here; each table page notes the values seen in that type. Source: DATASUS, *Informe Técnico
SIASUS* (Jul/2019), section 3.4, *Layout dos arquivos de APAC*. Sizes are those of the AM
files and can differ slightly between types.

### Facility, management and time

| Column | Size | Official description | Notes |
|---|---|---|---|
| `AP_MVM` | 6 | Processing month (`AAAAMM`). | Equals the `competencia` partition; = `PA_MVM`. |
| `AP_CONDIC` | 2 | Type of management the state or municipality is qualified for. | `EP`, `PG`. |
| `AP_GESTAO` | 6 | IBGE state + municipality code of the manager, or `UF0000` under state management. | |
| `AP_CODUNI` | 7 | CNES code of the executing facility. | = `PA_CODUNI`. |
| `AP_CMP` | 6 | Month the care was delivered (`AAAAMM`). | Can be earlier than `AP_MVM` (late billing); = `PA_CMP`. |
| `AP_UFMUN` | 6 | State + municipality of the facility. | IBGE, no check digit. |
| `AP_TPUPS` | 2 | Facility type. | CNES codes (`43` pharmacy, `36` specialised clinic, `05` general hospital). |
| `AP_TIPPRE` | 2 | Provider type. | |
| `AP_MN_IND` | 1 | Facility maintained (*mantido*) / individual. | `M` / `I`. |
| `AP_CNPJCPF` | 14 | CNPJ of the executing facility. | |
| `AP_CNPJMNT` | 14 | CNPJ of the maintaining body, or zeros. | |
| `AP_NATJUR` | 4 | Legal nature code (*natureza jurídica*). | From Jul/2016; `NULL` before. Not listed for every type in the 2019 Informe, but present in the files. |

### The authorisation

| Column | Size | Official description | Notes |
|---|---|---|---|
| `AP_AUTORIZ` | 13 | APAC number, `UFAATsssssssd`. | Key of the APAC; repeats in continuation months. Joins `PA_AUTORIZ`. |
| `AP_PRIPAL` | 10 | Main procedure of the APAC. | SIGTAP; join `procedimentos.codigo`. |
| `AP_VL_AP` | 12 | Total approved value of the APAC. | `DOUBLE` in the typed view; nominal R$. |
| `AP_TPATEN` | 2 | APAC type of care (*tipo de atendimento*). | One value per file type (`06` in AM, `03` in AQ, `04` in AR, `00` in AD). |
| `AP_TPAPAC` | 1 | APAC is `1` initial, `2` continuation, `3` single. | |
| `AP_DTINIC` | 8 | Start of validity (`AAAAMMDD`). | |
| `AP_DTFIM` | 8 | End of validity (`AAAAMMDD`). | Up to 3 months after the start. |
| `AP_CATEND` | 2 | Type of care (*caráter de atendimento*). | `01` elective, `02` urgent, `03`–`06` accidents / external causes. |
| `AP_APACANT` | 13 | Number of the previous APAC. | Mostly zeros: continuations keep the same `AP_AUTORIZ`. |
| `AP_UNISOL` | 7 | CNES code of the requesting facility. | Zeros when not informed. |
| `AP_DTSOLIC` | 8 | Request date (`AAAAMMDD`). | |
| `AP_DTAUT` | 8 | Authorisation date (`AAAAMMDD`). | |
| `AP_CODEMI` | 10 | Issuing body (*órgão emissor*). | `E` + state code + 7 digits (`E350000001`) = state health secretariat; `M` + IBGE municipality + `0001` (`M355030001`) = municipal health secretariat; `S…` and `U…` are other bodies. |

### Exit and continuation

| Column | Size | Official description | Notes |
|---|---|---|---|
| `AP_MOTSAI` | 2 | Reason for exit or continuation (*motivo de saída / permanência*). | `11`–`18` discharge (11 cured, 12 improved, 14 on request, 15 with return for follow-up, 16 evasion, 18 other), `21` continues because of the disease, `22` continues because of a complication, `26` continues with a change of procedure, `28` continues for other reasons, `31` transfer, `41`–`43` death, `51` closed administratively. |
| `AP_OBITO` | 1 | Death indicator. | `1` = yes. |
| `AP_ENCERR` | 1 | Closure indicator. | `1` = yes. |
| `AP_PERMAN` | 1 | Continuation indicator. | `1` = patient continues. |
| `AP_ALTA` | 1 | Discharge indicator. | `1` = yes. |
| `AP_TRANSF` | 1 | Transfer indicator. | `1` = yes. |
| `AP_DTOCOR` | 8 | Date of the event that replaces the end of validity. | Filled when `AP_PERMAN = 0`. |

### Patient

| Column | Size | Official description | Notes |
|---|---|---|---|
| `AP_CNSPCN` | 15 | Patient's CNS (national health card). | **Encoded by DATASUS**; usable to count distinct patients, not to link. |
| `AP_COIDADE` | 1 | Age code (unit of `AP_NUIDADE`). | `2` days, `3` months, `4` years, `5` 100 years or more (age = 100 + `AP_NUIDADE`). |
| `AP_NUIDADE` | 2 | Age, in the unit of `AP_COIDADE`. | |
| `AP_SEXO` | 1 | Sex. | `M`, `F`. |
| `AP_RACACOR` | 2 | Race/colour: `01` white, `02` black, `03` brown (*parda*), `04` yellow, `05` indigenous, `99` no information. | |
| `AP_ETNIA` | 4 | Indigenous ethnicity. | Only when `AP_RACACOR = '05'`. |
| `AP_MUNPCN` | 6 | State + municipality where the **patient lives**. | Join the first 2 digits to `ufs.ibge`. |
| `AP_UFNACIO` | 3 | Nationality code. | `010` = Brazilian. |
| `AP_CEPPCN` | 8 | Postcode (CEP) of the patient. | |
| `AP_UFDIF` | 2 | Patient's state differs from the facility's: `0` same, `1` different. | |
| `AP_MNDIF` | 2 | Patient's municipality differs from the facility's: `0` same, `1` different. | **Always `1` in AM, AQ, AR, AD, ATD and AN** even when they are equal; compare `AP_MUNPCN` with `AP_UFMUN` instead. |

### Diagnosis

| Column | Size | Official description | Notes |
|---|---|---|---|
| `AP_CIDPRI` | 4 | Main ICD-10 diagnosis. | No dot; join `cid10.codigo`. |
| `AP_CIDSEC` | 4 | Secondary ICD-10 diagnosis. | `0000` = none. |
| `AP_CIDCAS` | 4 | ICD-10 of associated causes. | `0000` = none. |

## Layouts

The Informe Técnico (Jul/2019) says the APAC layouts have not changed since Jan/2008. The
only change seen in the shared columns is `AP_NATJUR`, added in Jul/2016 (AM, AQ, AR and AD; the
views show `NULL` before). It is also in the **Dec/2011** files, and only in that month before
Jul/2016, in every APAC type then published (AM, AQ, AR, AD, AN; and BI's `NAT_JUR`). Types can also gain columns of their own (AQ: `AQ_MED01`–`AQ_MED10`
from Jan/2021). Header checks in Nov/2026 found the 46 `AP_` columns above in AM, AQ, AR, AD, ATD,
ACF and AMP (AN, which ended in 2014, has all but `AP_NATJUR`, except in Dec/2011). ABO renames a few of them
(`AP_TPPRE`, `AP_TPATEND`, `AP_DTOOCOR`, `AP_APACAN`) and adds comorbidity fields.
