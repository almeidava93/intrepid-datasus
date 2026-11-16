# pa_legacy — outpatient production, 1994–2007

**Source:** `PAufaamm.dbc` files in `ftp.datasus.gov.br/dissemin/publicos/SIASUS/199407_200712/Dados`.
**Coverage:** Jul/1994 to Dec/2007.
**Fetch:** `uv run datasus fetch -s SP -f 2003` (the CLI picks the folder by month).

Before Jan/2008 SIA/SUS used its own procedure table, replaced by SIGTAP
(*Portaria GM/MS nº 321/2007*). The files have a different, smaller layout, so they live in
their own table. **Do not `UNION` `pa` and `pa_legacy` on procedure codes**: `PA_CODPRO` is
not a SIGTAP code and does not join `procedimentos`.

`pa_legacy_raw` is the same data with every column as text; `pa_legacy` casts
`PA_QTDPRO`/`PA_QTDAPR` to `BIGINT` and `PA_VALPRO`/`PA_VALAPR` to `DOUBLE`.

!!! note "No official layout for these files"
    The DATASUS documentation folder for 1994–2007 (`199407_200712/Doc`) is empty, and the
    2019 *Informe Técnico* only covers 2008 onward. Columns shared with `pa` are described
    from that Informe; the rest are this package's best reading of the names and should be
    checked against the data before you rely on them.

## Columns

| Column | Type in `pa_legacy` | Meaning | Same as in `pa`? |
|---|---|---|---|
| `PA_CONDIC` | text | Management condition of the state/municipality. | Yes |
| `PA_GESTAO` | text | Managing authority (state code + `0000`, or municipality). | Yes |
| `PA_CODUNI` | text | Facility code (6 digits in this period, pre-CNES numbering). | Similar |
| `PA_DATREF` | text | Reference month (`AAMM`). | — |
| `PA_CODPRO` | text | Procedure code, old SIA table (not SIGTAP). | — |
| `PA_DOCORIG` | text | Record instrument (BPA / APAC). | Similar |
| `PA_CODESP` | text | Specialty code. | — |
| `PA_TIPPRO` | text | Procedure type. | — |
| `PA_TIPATE` | text | Type of care. | — |
| `PA_FXETAR` | text | Patient age band (code). | — |
| `PA_QTDPRO` | `BIGINT` | Quantity produced (submitted). | Yes |
| `PA_QTDAPR` | `BIGINT` | Quantity approved. Sum this. | Yes |
| `PA_INDICA` | text | Production status. | Yes |
| `PA_TIPPRE` | text | Provider type. | Yes |
| `PA_DATPR` | text | Processing month (`AAMM`). | — |
| `PA_VALPRO` | `DOUBLE` | Value produced (submitted), nominal currency of the time. | Yes |
| `PA_VALAPR` | `DOUBLE` | Value approved, nominal currency of the time. | Yes |
| `PA_UFMUN` | text | Municipality of the facility. | Yes |
| `PA_MUNAT` | text | Municipality of care. | — |
| `PA_NUMAPA` | text | APAC number. | — |
| `PA_CODOCO` | text | Occurrence code. | Yes |
| `PA_CIDPRI` | text | Main diagnosis (ICD-10). | Yes |
| `PA_CIDSEC` | text | Secondary diagnosis (ICD-10). | Yes |
| `PA_MORFOL` | text | Tumour morphology (oncology APAC). | — |
| `PA_CNPJ_CC` | text | CNPJ for credit assignment (from 2003). | Yes |
| `PA_RCB` | text | Undocumented, from 2003; looks like the month the production was received (`AAAAMM`: `200702` on every row of AC, Jan/2007). | — |
| `PA_RCBDF` | text | Undocumented, from 2003 (`0` on every row of AC, Jan/2007). | — |
| `PA_NH` | text | Undocumented, from 2004: a code `01`–`08`, probably the facility's hierarchy level (*nível de hierarquia*). | — |
| `_ARQUIVO_ORIGEM` | text | DATASUS file the row came from. | Yes |
| `competencia` | `INTEGER` | Partition: month of the file (`YYYYMM`). | Yes |
| `uf` | text | Partition: state of the file. | Yes |

Values are nominal reais (the files start with the Real, in Jul/1994). Adjust for
inflation before comparing years.

## Example

```sql
SELECT competencia // 100 AS ano, SUM(PA_QTDAPR) AS qtd
FROM pa_legacy GROUP BY 1 ORDER BY 1;
```
