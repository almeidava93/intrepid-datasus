# bi — BPA Individualizado (patient-level outpatient production), 2008 onward

**Source:** `BIufaamm.dbc` files in `ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados`
(e.g. `BIAC2605.dbc`). Large states are split into `BISP2605_1.dbc`, `_2`, `_3` (note the
underscore and digit; PA uses letters).
**Coverage:** Jan/2008 to the latest month DATASUS has released, all 27 states.
**Size on the FTP** (Nov/2026): 6,224 files, about **188 GB** of `.dbc` (São Paulo alone:
~43 GB). Parquet takes about 0.4–0.45× the `.dbc` size.
**Fetch:** `uv run datasus fetch -T bi -s AC -f 2026`.

Each row is one appointment recorded on a BPA-I (*Boletim de Produção Ambulatorial
Individualizado*): one procedure delivered to one identified patient, with the patient's
age, sex, race/colour, municipality of residence and main diagnosis (ICD-10). The BPA-I was
created by Portaria SAS/MS nº 709 of 27/Dec/2007, when the old BPA was split into a
consolidated form (BPA-C, totals only) and this individual one.

!!! warning "Sum quantities, don't count rows"
    Most rows have `QT_APROV = 1`, but not all (the same patient can get several units of a
    procedure on one line). Use `SUM(QT_APROV)` for procedure counts.

## How bi relates to pa (double counting)

**Every row of `bi` is also in `pa`**: it is the PA row with `PA_DOCORIG = 'I'`, published
again with the patient columns that PA leaves out (date of birth, encoded patient CNS, age
unit). PA itself already has age, sex, race, diagnosis and residence for those rows.

Checked on AC, May/2026: `bi` has 137,929 rows, `SUM(QT_APROV)` = 156,365 and
`SUM(VL_APROV)` = R$ 4,240,290; `pa WHERE PA_DOCORIG = 'I'` has exactly the same 137,929
rows, 156,365 procedures and R$ 4,240,290, and the totals agree procedure by procedure
(337 of 337 `PROC_ID`s).

| You want | Use |
|---|---|
| All outpatient production (BPA-C + BPA-I + APAC + RAAS) | `pa` only |
| Only individualised BPA production | `bi`, or `pa WHERE PA_DOCORIG = 'I'` |
| Date of birth, age in days/months, distinct patients | `bi` |

!!! danger "Never add `bi` to `pa`"
    `SUM` over `pa` plus `SUM` over `bi` counts every BPA-I procedure twice. In AC May/2026
    BPA-I was 8% of approved PA procedures (156,365 of 1,942,973) but 31% of the approved
    value (R$ 4.24 M of R$ 13.59 M).

The other PA instruments have no `bi` rows: BPA-C (`C`, no patient data), APAC (`P`/`S`,
their own APAC file types such as AQ, AR, AM) and RAAS (`A`/`B`, file types SAD and PS).

## bi vs bi_raw

`bi_raw` holds every column as text exactly as DATASUS publishes it. `bi` is the same data
with `QT_APRES`/`QT_APROV` cast to `BIGINT` and `VL_APRES`/`VL_APROV` to `DOUBLE` (with
`TRY_CAST`). Everything else stays text, including codes with leading zeros
(`TPFIN = '06'`) and dates (`DT_ATEND = '202605'`, `DTNASC = '19730331'`).

## Columns

The *Official description* column translates the DATASUS *Informe Técnico SIASUS*
(Jul/2019), section 5.2, *Layout do arquivo de BPA-I: BIUFAAMM.DBF*. Sizes are those of the
DBF field. Values in *Notes* were checked on AC, May/2026. The PA column with the same
content is given where there is one.

### Facility and management

| Column | Type | Size | Official description | Notes |
|---|---|---|---|---|
| `CODUNI` | text | 7 | Facility code in CNES. | = `PA_CODUNI`. |
| `GESTAO` | text | 6 | IBGE state + municipality code of the manager, or `UF0000` under state management. | e.g. `120000` = Acre state. |
| `CONDIC` | text | 2 | Type of management the state or municipality is qualified for. | Values seen: `EP`, `PG`. |
| `UFMUN` | text | 6 | State + municipality where the **facility** is located. | IBGE code without check digit. |
| `TPUPS` | text | 2 | Facility type. | CNES codes, e.g. `73` emergency unit, `05` general hospital, `02` health centre, `39` diagnostic unit, `36` specialised clinic. |
| `TIPPRE` | text | 2 | Provider type. | Only `00` seen. |
| `MN_IND` | text | 1 | Facility maintained (*mantido*) / individual. | `M` / `I`. |
| `CNPJCPF` | text | 14 | CNPJ of the executing facility. | |
| `CNPJMNT` | text | 14 | CNPJ of the maintaining body, or zeros. | |
| `CNPJ_CC` | text | 14 | CNPJ of the body paid by credit assignment (*cessão de crédito*), or zeros. | |
| `NAT_JUR` | text | 4 | Legal nature code (*natureza jurídica*). | From Jul/2016 only; `NULL` before. IBGE CONCLA table. |

### Time

| Column | Type | Size | Official description | Notes |
|---|---|---|---|---|
| `DT_PROCESS` | text | 6 | Processing month (`AAAAMM`). | Equals the `competencia` partition; = `PA_MVM`. |
| `DT_ATEND` | text | 6 | Month of the appointment (`AAAAMM`). | Can be earlier (late reports: 2.5% of rows in AC May/2026); = `PA_CMP`. |

### Procedure and funding

| Column | Type | Size | Official description | Notes |
|---|---|---|---|---|
| `PROC_ID` | text | 10 | Outpatient procedure code. | SIGTAP; join `procedimentos.codigo`. |
| `TPFIN` | text | 2 | Funding type. | `01` PAB, `04` FAEC, `05` MAC incentive, `06` MAC, `07` health surveillance. |
| `SUBFIN` | text | 4 | Funding subtype. | |
| `COMPLEX` | text | 1 | Procedure complexity. | `0` not applicable, `1` primary care, `2` medium, `3` high. = `PA_NIVCPL`. |
| `AUTORIZ` | text | 13 | BPA-I authorisation number (`UFAATsssssssd`). Optional, not validated. | Mostly zeros: don't use it as a key. |
| `CATEND` | text | 2 | Type of care (*caráter de atendimento*). | `01` elective, `02` urgent, `03`–`06` work accident / traffic / other external causes. |

### Professional

| Column | Type | Size | Official description | Notes |
|---|---|---|---|---|
| `CNSPROF` | text | 15 | CNS (national health card) of the executing professional. | = `PA_CNSMED`. |
| `CBOPROF` | text | 6 | Professional's occupation (CBO). | Join `ocupacoes.codigo`. = `PA_CBOCOD`. |

### Patient

| Column | Type | Size | Official description | Notes |
|---|---|---|---|---|
| `CNS_PAC` | text | 15 | Patient's CNS. | **Encoded by DATASUS** (not the real number; shows as non-digit characters) and empty on about half the rows. Rows with the same value presumably belong to the same patient, so it can be used to count distinct patients within the data, but not to link to other systems. |
| `DTNASC` | text | 8 | Patient's date of birth. | `AAAAMMDD`. |
| `TPIDADEPAC` | text | 1 | Unit of the patient's age, computed from the date of birth. | `2` days, `3` months, `4` years, `5` 100 years or more (age = 100 + `IDADEPAC`), `9` not informed (`IDADEPAC = '99'`). |
| `IDADEPAC` | text | 2 | Patient's age, in the unit of `TPIDADEPAC`. | Two digits: ages of 100+ use `TPIDADEPAC = '5'`. |
| `SEXOPAC` | text | 1 | Patient sex. | `M`, `F`; `I` (not informed) is rare. |
| `RACACOR` | text | 2 | Race/colour: `01` white, `02` black, `03` brown (*parda*), `04` yellow, `05` indigenous, `99` no information. | |
| `ETNIA` | text | 4 | Indigenous ethnicity (Portaria SAS 508/2010, annex I). | Only when `RACACOR = '05'`, from Oct/2010. |
| `MUNPAC` | text | 6 | State + municipality where the **patient lives** (or of the facility when the patient is not identified). | Join the first 2 digits to `ufs.ibge`. |
| `UFDIF` | text | 1 | Patient's state differs from the facility's: `0` same, `1` different. | |
| `MNDIF` | text | 1 | Patient's municipality differs from the facility's: `0` same, `1` different. | |

### Diagnosis

| Column | Type | Size | Official description | Notes |
|---|---|---|---|---|
| `CIDPRI` | text | 4 | Main ICD-10 diagnosis. | No dot (`K297`). `0000` = not informed: 57% of rows in AC May/2026. Join `cid10.codigo`. |

### Quantities and values

Values are in nominal R$ (not inflation adjusted).

| Column | Type in `bi` | Official description | Notes |
|---|---|---|---|
| `QT_APRES` | `BIGINT` | Quantity produced (submitted). | = `PA_QTDPRO`. |
| `QT_APROV` | `BIGINT` | Quantity approved. | **The column to sum**; = `PA_QTDAPR`. |
| `VL_APRES` | `DOUBLE` | Value produced (submitted). | = `PA_VALPRO`. |
| `VL_APROV` | `DOUBLE` | Value approved. | = `PA_VALAPR`. |

### Added by this package

| Column | Type | Meaning |
|---|---|---|
| `_ARQUIVO_ORIGEM` | text | DATASUS file the row came from (`BISP2605_2.dbc`). |
| `competencia` | `INTEGER` | Partition: month of the file (`YYYYMM`). |
| `uf` | text | Partition: state of the file. |

## Known quirks and layout changes

- **One layout since 2008.** 35 columns until Jun/2016; `NAT_JUR` added from Jul/2016
  (36 columns). Older months have `NULL` there. The 2019 Informe numbers the fields 1–35
  and 37 (there is no field 36).
- **Split files use `_1`, `_2`, `_3`.** São Paulo, Minas Gerais and Rio de Janeiro are split
  from May/2023, about 5 million rows per part.
- **Whole file and parts for the same month.** For SP, MG and RJ, May/2023 to Feb/2024, the
  FTP holds both `BISP2305.dbc` and `BISP2305_1.dbc` + `_2`. The parts are the newer
  publication (equal or more rows: RJ Feb/2024 has 6,013,496 rows in the whole file and
  6,126,859 in the parts), so `datasus` fetches the parts and ignores the whole file.
  Loading both would duplicate the month.
- **Large conversions.** Measured on `BISP2608_1.dbc` (172 MB, 4,742,266 rows): 20 s
  download, 44 s conversion, a 1.16 GB temporary DBF and a peak of **1.9 GB of RAM** in the
  worker; the Parquet file was 78 MB (0.45× the `.dbc`). Each `fetch` worker
  (`--workers`, default 3) converts one file at a time, so plan about 2 GB of RAM and
  1.2 GB of temporary disk per worker when fetching SP, MG or RJ. One full SP month in 2026
  is ~550 MB of `.dbc` in three parts, ~14 million rows.
- Patient CNS is encoded (see above), and `AUTORIZ` is mostly zeros.

## Examples

```sql
-- Age pyramid of patients seen for hypertension (ICD-10 I10) in 2025, by sex
SELECT SEXOPAC,
       CASE WHEN TPIDADEPAC = '4' THEN (CAST(IDADEPAC AS INT) // 10) * 10
            WHEN TPIDADEPAC IN ('2', '3') THEN 0
            WHEN TPIDADEPAC = '5' THEN 100 END AS faixa,
       SUM(QT_APROV) AS qtd
FROM bi
WHERE competencia BETWEEN 202501 AND 202512 AND CIDPRI LIKE 'I10%'
GROUP BY ALL ORDER BY SEXOPAC, faixa;

-- Most frequent diagnoses with names (informed ones only)
SELECT c.nome, SUM(QT_APROV) AS qtd
FROM bi JOIN cid10 c ON c.codigo = bi.CIDPRI
WHERE competencia = 202605 AND uf = 'AC' AND CIDPRI <> '0000'
GROUP BY 1 ORDER BY 2 DESC LIMIT 20;

-- Where patients come from: residence state of patients treated in SP
SELECT u.nome AS estado_residencia, SUM(QT_APROV) AS qtd
FROM bi JOIN ufs u ON u.ibge = LEFT(bi.MUNPAC, 2)
WHERE competencia = 202605 AND bi.uf = 'SP' AND UFDIF = '1'
GROUP BY 1 ORDER BY 2 DESC;
```
