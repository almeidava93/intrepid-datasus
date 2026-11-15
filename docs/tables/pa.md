# pa — outpatient production, 2008 onward

**Source:** `PAufaamm.dbc` files in `ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados`
(e.g. `PASP2505.dbc`; large states are split into `PASP2505a.dbc`, `…b`, …).
**Coverage:** Jan/2008 to the latest month DATASUS has released, all 27 states.
**Fetch:** `uv run datasus fetch -s SP -f 2025`.

Each row is one line of approved outpatient production (*produção ambulatorial*) processed
by SIA/SUS in a given month. What a row stands for depends on the record instrument in
`PA_DOCORIG`:

| `PA_DOCORIG` | Instrument | One row per | Patient data? |
|---|---|---|---|
| `C` | BPA-C — *Boletim de Produção Ambulatorial Consolidado* | procedure × CBO line of the report | **No** |
| `I` | BPA-I — *BPA Individualizado* | appointment | Yes |
| `P` | APAC — main procedure | procedure in the authorisation | Yes |
| `S` | APAC — secondary procedure | procedure in the authorisation | Yes |
| `A` | RAAS-AD — home care (*Atenção Domiciliar*) | procedure | Yes |
| `B` | RAAS-PSI — psychosocial care | procedure | Yes |

The `I` rows are also published, with a few more patient columns, as their own file type:
see [bi](bi.md). Don't add `bi` to `pa`, it would count them twice.

!!! warning "Sum quantities, don't count rows"
    One BPA-C row can represent thousands of procedures. Use `SUM(PA_QTDAPR)`.
    Consolidated (`C`) rows have no age, sex, diagnosis or residence — about half of all
    procedures. See [Things to know about the data](../data-notes.md).

## pa vs pa_raw

`pa_raw` holds every column as text exactly as DATASUS publishes it. `pa` is the same data
with quantity columns cast to `BIGINT` and value columns to `DOUBLE` (with `TRY_CAST`, so a
malformed value becomes `NULL` instead of failing the query). Everything else stays text,
including codes with leading zeros (`PA_TPFIN = '06'`) and dates (`PA_CMP = '202505'`).

## Columns

The *Official description* column translates the DATASUS *Informe Técnico* (2019). Sizes
are those of the original DBF field. Example values were checked on real files.

### Facility and management

| Column | Type | Size | Official description | Notes |
|---|---|---|---|---|
| `PA_CODUNI` | text | 7 | Facility code in CNES (national registry of health facilities). | Join to CNES data. |
| `PA_GESTAO` | text | 6 | IBGE state + municipality code of the managing authority, or `UF0000` when the facility is under state management. | e.g. `350000` = São Paulo state; `355030` = São Paulo city. |
| `PA_CONDIC` | text | 2 | Type of management the state or municipality is qualified for. | Values seen: `EP`, `PG`. The Informe gives no code list. |
| `PA_UFMUN` | text | 6 | State + municipality where the **facility** is located. | IBGE code without the check digit. |
| `PA_REGCT` | text | 4 | Contract rule code. | `0000` = none. |
| `PA_INCOUT` | text | 4 | Increment: other. | |
| `PA_INCURG` | text | 4 | Increment: urgency. | |
| `PA_TPUPS` | text | 2 | Facility type. | CNES codes, e.g. `02` health centre, `05` general hospital, `70` CAPS. |
| `PA_TIPPRE` | text | 2 | Provider type. | |
| `PA_MN_IND` | text | 1 | Facility is maintained (*mantido*) / individual. | `M` / `I`. |
| `PA_CNPJCPF` | text | 14 | Tax ID (CNPJ) of the executing facility. | |
| `PA_CNPJMNT` | text | 14 | CNPJ of the maintaining body, or zeros. | |
| `PA_CNPJ_CC` | text | 14 | CNPJ of the body paid for the production by credit assignment (*cessão de crédito*), or zeros. | |
| `PA_NAT_JUR` | text | 4 | Legal nature code (*natureza jurídica*). | IBGE CONCLA table. |

### Time

| Column | Type | Size | Official description | Notes |
|---|---|---|---|---|
| `PA_MVM` | text | 6 | Processing / movement month (`AAAAMM`). | Equals the `competencia` partition. |
| `PA_CMP` | text | 6 | Month the procedure was performed (`AAAAMM`). | Can be earlier than `PA_MVM` (late reports). |

### Procedure and funding

| Column | Type | Size | Official description | Notes |
|---|---|---|---|---|
| `PA_PROC_ID` | text | 10 | Outpatient procedure code. | SIGTAP code; join `procedimentos.codigo`. First 2 digits = group. |
| `PA_TPFIN` | text | 2 | Funding type of the production. | SIGTAP `sigtap_financiamento`: `01` PAB, `02` pharmacy, `04` FAEC, `05` MAC incentive, `06` MAC, `07` health surveillance, `08` SUS management. |
| `PA_SUBFIN` | text | 4 | Funding subtype. | |
| `PA_NIVCPL` | text | 1 | Procedure complexity. | `0` not applicable, `1` primary care, `2` medium, `3` high. |
| `PA_DOCORIG` | text | 1 | Record instrument. | See the table at the top of this page. |
| `PA_AUTORIZ` | text | 13 | APAC number or BPA-I authorisation number. Optional (not validated) in BPA-I. | Format `UFAATsssssssd`: state, year, type, sequence, check digit. |
| `PA_SRV_C` | text | 6 | Specialised service / classification code (per CNES). | Spelled `PA_SRC_C` in the Informe; the files use `PA_SRV_C`. 3 digits service + 3 classification; see `sigtap_servico_classificacao`. |
| `PA_INE` | text | 10 | National team identifier (INE) of the health team that delivered the action. | |
| `PA_FNTORC` | text | | Budget source. | Not in the 2019 Informe; present in recent files. |

### Professional

| Column | Type | Size | Official description | Notes |
|---|---|---|---|---|
| `PA_CNSMED` | text | 15 | CNS (national health card) of the executing professional. | |
| `PA_CBOCOD` | text | 6 | Professional's occupation code (CBO, Ministry of Labour). | Join `ocupacoes.codigo`. |

### Patient (empty for BPA-C)

| Column | Type | Size | Official description | Notes |
|---|---|---|---|---|
| `PA_IDADE` | text | 3 | Patient age in years. | `999` = not informed. |
| `IDADEMIN` | text | 3 | Minimum patient age allowed for the procedure. | From SIGTAP. |
| `IDADEMAX` | text | 3 | Maximum patient age allowed for the procedure. | From SIGTAP. |
| `PA_FLIDADE` | text | 1 | Age compatibility with SIGTAP: `0` age not required, `1` compatible, `2` outside SIGTAP range, `3` no age, `4` blank. | |
| `PA_SEXO` | text | 1 | Patient sex. | `M`, `F`; `0` = not informed (always for `C`). |
| `PA_RACACOR` | text | 2 | Race/colour: `01` white, `02` black, `03` brown (*parda*), `04` yellow, `05` indigenous, `99` no information. | `00` also appears (BPA-C). |
| `PA_ETNIA` | text | 4 | Patient ethnicity (indigenous people). | |
| `PA_MUNPCN` | text | 6 | State + municipality where the **patient lives**, or of the facility when the patient is not identified (BPA). | In practice BPA-C rows carry `999999`. |
| `PA_UFDIF` | text | 1 | Patient's state differs from the facility's: `0` same, `1` different. | `9` appears for BPA-C. |
| `PA_MNDIF` | text | 1 | Patient's municipality differs from the facility's: `0` same, `1` different. | |
| `PA_CATEND` | text | 2 | Type of care (*caráter de atendimento*), APAC or BPA-I. | `01` elective, `02` urgent, …; `99` for BPA-C. |

### Diagnosis and outcome (APAC / BPA-I)

| Column | Type | Size | Official description | Notes |
|---|---|---|---|---|
| `PA_CIDPRI` | text | 4 | Main ICD-10 diagnosis (APAC or BPA-I). | `0000` = not informed. Join `cid10.codigo`. |
| `PA_CIDSEC` | text | 4 | Secondary ICD-10 diagnosis (APAC). | |
| `PA_CIDCAS` | text | 4 | ICD-10 of associated causes (APAC). | |
| `PA_MOTSAI` | text | 2 | Reason for discharge, or zeros. | |
| `PA_OBITO` | text | 1 | Death indicator (APAC). | |
| `PA_ENCERR` | text | 1 | Closure indicator (APAC). | |
| `PA_PERMAN` | text | 1 | Continuation indicator (APAC). | |
| `PA_ALTA` | text | 1 | Discharge indicator (APAC). | |
| `PA_TRANSF` | text | 1 | Transfer indicator (APAC). | |

### Quantities and values

Values are in nominal R$ (not inflation adjusted).

| Column | Type in `pa` | Official description | Notes |
|---|---|---|---|
| `PA_QTDPRO` | `BIGINT` | Quantity produced (submitted). | |
| `PA_QTDAPR` | `BIGINT` | Quantity approved. | **The column to sum** for counts. |
| `PA_VALPRO` | `DOUBLE` | Value produced (submitted). | |
| `PA_VALAPR` | `DOUBLE` | Value approved. | The column to sum for spending. |
| `PA_DIF_VAL` | `DOUBLE` | Difference between the SIGTAP unit value and the unit value paid by the manager, × approved quantity. | |
| `NU_VPA_TOT` | `DOUBLE` | Unit value of the procedure in the VPA table. | |
| `NU_PA_TOT` | `DOUBLE` | Unit value of the procedure in SIGTAP. | |
| `PA_VL_CF` | `DOUBLE` | Federal complement value. | |
| `PA_VL_CL` | `DOUBLE` | Local complement value. | |
| `PA_VL_INC` | `DOUBLE` | Increment value. | |
| `PA_VL_CRD` | `DOUBLE` | Credit value. | Not in the 2019 Informe; recent files only. |

### Processing flags

| Column | Type | Size | Official description | Notes |
|---|---|---|---|---|
| `PA_INDICA` | text | 1 | Production status: `0` not approved, `5` fully approved, `6` partly approved. | |
| `PA_CODOCO` | text | 1 | Occurrence code. | |
| `PA_FLQT` | text | 1 | Error indicator: quantity produced. | |
| `PA_FLER` | text | 1 | Error indicator: APAC body. | |

### Added by this package

| Column | Type | Meaning |
|---|---|---|
| `_ARQUIVO_ORIGEM` | text | DATASUS file the row came from. |
| `competencia` | `INTEGER` | Partition: month of the file (`YYYYMM`). |
| `uf` | text | Partition: state of the file. |

Columns DATASUS adds over time (like `PA_FNTORC`, `PA_VL_CRD`) appear automatically; older
months simply have `NULL` there.

## Examples

```sql
-- Approved procedures and spending by state, 2025
SELECT u.nome, SUM(PA_QTDAPR) AS qtd, SUM(PA_VALAPR) AS valor
FROM pa JOIN ufs u USING (uf)
WHERE competencia BETWEEN 202501 AND 202512
GROUP BY 1 ORDER BY 2 DESC;

-- Top procedures by complexity, with names
SELECT p.complexidade, p.nome, SUM(PA_QTDAPR) AS qtd
FROM pa JOIN procedimentos p ON p.codigo = pa.PA_PROC_ID
WHERE competencia = 202505
GROUP BY ALL ORDER BY qtd DESC LIMIT 20;

-- Patients treated outside their home municipality (identified records only)
SELECT PA_MNDIF, SUM(PA_QTDAPR) FROM pa
WHERE competencia = 202505 AND PA_DOCORIG <> 'C'
GROUP BY 1;
```
