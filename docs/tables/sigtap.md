# SIGTAP tables

SIGTAP (*Sistema de Gerenciamento da Tabela de Procedimentos, Medicamentos e OPM do SUS*)
is the SUS procedure table. DATASUS publishes one version per month since Jan/2008 as
`TabelaUnificada_YYYYMM_v*.zip` on `ftp2.datasus.gov.br/public/sistemas/tup/downloads`.
Each zip has ~40 fixed-width text tables, each with its own `*_layout.txt`; this package
imports **every table in the zip**, all columns as text.

```bash
uv run datasus sigtap fetch                       # latest version
uv run datasus sigtap fetch --from 2008 --yearly  # one version per year
```

## Naming: two views per table

For each SIGTAP file `tb_X` or `rl_X` you get:

| View | Contents |
|---|---|
| `sigtap_X_all` | Every row of every version you fetched, plus `competencia` (the version, `YYYYMM`). |
| `sigtap_X` | **Code tables (`tb_*`)**: one row per code — the most recent description — plus `primeira_versao`, `ultima_versao` and `ativo`. **Relationship tables (`rl_*`)**: the latest version only. |

The `tb_` prefix is dropped (`tb_procedimento` → `sigtap_procedimento`); `rl_` is kept
(`rl_procedimento_cid` → `sigtap_rl_procedimento_cid`).

Common column conventions: `CO_*` code, `NO_*` name, `DS_*` long description, `TP_*` type
flag, `VL_*` value, `QT_*` quantity, `DT_COMPETENCIA` version of the row (`YYYYMM`).
Money columns (`VL_SA`, `VL_SH`, `VL_SP`) are **integers in centavos** — divide by 100
(the `procedimentos` view already does).

## Code tables (`tb_*`)

| View | Key | What it lists |
|---|---|---|
| `sigtap_procedimento` | `CO_PROCEDIMENTO` | Procedures: name, complexity, sex, age limits, values, funding. Friendly version: [`procedimentos`](lookups.md#procedimentos). |
| `sigtap_descricao` | `CO_PROCEDIMENTO` | Long text description of each procedure (`DS_PROCEDIMENTO`). |
| `sigtap_grupo` | `CO_GRUPO` | Procedure groups (digits 1–2). |
| `sigtap_sub_grupo` | `CO_GRUPO`, `CO_SUB_GRUPO` | Subgroups (digits 3–4). |
| `sigtap_forma_organizacao` | `CO_GRUPO`, `CO_SUB_GRUPO`, `CO_FORMA_ORGANIZACAO` | Forms of organisation (digits 5–6). |
| `sigtap_financiamento` | `CO_FINANCIAMENTO` | Funding types (same codes as `pa.PA_TPFIN`). |
| `sigtap_rubrica` | `CO_RUBRICA` | Budget headings (*rubricas*), mostly within FAEC. |
| `sigtap_registro` | `CO_REGISTRO` | Record instruments: `01` BPA-C, `02` BPA-I, `03`–`05` AIH, `06`/`07` APAC main/secondary, `08`/`09` RAAS, `10` e-SUS APS. |
| `sigtap_modalidade` | `CO_MODALIDADE` | Care modalities (outpatient, hospital, day hospital, …). |
| `sigtap_cid` | `CO_CID` | ICD-10 codes with sex, `TP_AGRAVO` (notifiable condition flag) and staging fields. Friendly version: [`cid10`](lookups.md#cid10). |
| `sigtap_ocupacao` | `CO_OCUPACAO` | CBO occupations. Friendly version: [`ocupacoes`](lookups.md#ocupacoes). |
| `sigtap_habilitacao` | `CO_HABILITACAO` | Facility accreditations (*habilitações*) required for some procedures. |
| `sigtap_grupo_habilitacao` | `NU_GRUPO_HABILITACAO` | Groups of accreditations. |
| `sigtap_servico` | `CO_SERVICO` | Specialised services (CNES). |
| `sigtap_servico_classificacao` | `CO_SERVICO`, `CO_CLASSIFICACAO` | Classifications within each service (match `pa.PA_SRV_C`). |
| `sigtap_tipo_leito` | `CO_TIPO_LEITO` | Bed types. |
| `sigtap_detalhe` | `CO_DETALHE` | Procedure details (extra rules attached to procedures). |
| `sigtap_descricao_detalhe` | `CO_DETALHE` | Long description of each detail. |
| `sigtap_regra_condicionada` | `CO_REGRA_CONDICIONADA` | Conditional rules. |
| `sigtap_rede_atencao` | `CO_REDE_ATENCAO` | Care networks (*Redes de Atenção*). |
| `sigtap_componente_rede` | `CO_COMPONENTE_REDE` | Components of each care network. |
| `sigtap_renases` | `CO_RENASES` | RENASES (national list of SUS actions and services). |
| `sigtap_tuss` | `CO_TUSS` | TUSS codes (private health insurance terminology). |
| `sigtap_sia_sih` | `CO_PROCEDIMENTO_SIA_SIH` | Procedures of the **old** SIA/SIH tables (`TP_PROCEDIMENTO`: `A` outpatient, `H` hospital). |

Extra columns on every `tb_*` view:

| Column | Meaning |
|---|---|
| `primeira_versao` | First fetched version (`YYYYMM`) containing the code. |
| `ultima_versao` | Last fetched version containing the code. |
| `ativo` | `true` if the code is in the most recent fetched version. |

## Relationship tables (`rl_*`)

All are keyed by `CO_PROCEDIMENTO` (except where noted) and describe the rules SIA/SIH
apply when validating production.

| View | Links a procedure to | Notable columns |
|---|---|---|
| `sigtap_rl_procedimento_cid` | ICD-10 codes allowed | `CO_CID`, `ST_PRINCIPAL` (`S` = may be main diagnosis) |
| `sigtap_rl_procedimento_ocupacao` | CBO occupations allowed to perform it | `CO_OCUPACAO` |
| `sigtap_rl_procedimento_registro` | Record instruments it can be reported on | `CO_REGISTRO` |
| `sigtap_rl_procedimento_modalidade` | Care modalities | `CO_MODALIDADE` |
| `sigtap_rl_procedimento_habilitacao` | Required accreditations | `CO_HABILITACAO`, `NU_GRUPO_HABILITACAO` |
| `sigtap_rl_procedimento_servico` | Required specialised service/classification | `CO_SERVICO`, `CO_CLASSIFICACAO` |
| `sigtap_rl_procedimento_leito` | Bed types | `CO_TIPO_LEITO` |
| `sigtap_rl_procedimento_detalhe` | Details/rules | `CO_DETALHE` |
| `sigtap_rl_procedimento_incremento` | Percentage increments by accreditation | `CO_HABILITACAO`, `VL_PERCENTUAL_SH/SA/SP` |
| `sigtap_rl_procedimento_compativel` | Compatible secondary procedures | `CO_PROCEDIMENTO_PRINCIPAL`, `CO_PROCEDIMENTO_COMPATIVEL`, `TP_COMPATIBILIDADE`, `QT_PERMITIDA` |
| `sigtap_rl_excecao_compatibilidade` | Exceptions to the compatibility rules | `CO_PROCEDIMENTO_RESTRICAO`, … |
| `sigtap_rl_procedimento_origem` | Procedure it originates from | `CO_PROCEDIMENTO_ORIGEM` |
| `sigtap_rl_procedimento_sia_sih` | Equivalent code in the old SIA/SIH tables | `CO_PROCEDIMENTO_SIA_SIH`, `TP_PROCEDIMENTO` |
| `sigtap_rl_procedimento_comp_rede` | Care network components | `CO_COMPONENTE_REDE` |
| `sigtap_rl_procedimento_regra_cond` | Conditional rules | `CO_REGRA_CONDICIONADA` |
| `sigtap_rl_procedimento_renases` | RENASES items | `CO_RENASES` |
| `sigtap_rl_procedimento_tuss` | TUSS codes | `CO_TUSS` |

Tables vary a little between versions (some appear only in later years); `union_by_name`
fills missing columns with `NULL`. A version whose minor table cannot be parsed is still
imported without that table; `tb_procedimento` is mandatory.

## Examples

```sql
-- Which diagnoses can justify a procedure?
SELECT c.codigo, c.nome
FROM sigtap_rl_procedimento_cid r JOIN cid10 c ON c.codigo = r.CO_CID
WHERE r.CO_PROCEDIMENTO = '0303010037' AND r.ST_PRINCIPAL = 'S';

-- How did a procedure's outpatient price change over the versions you fetched?
SELECT competencia, TRY_CAST(VL_SA AS DOUBLE) / 100 AS valor
FROM sigtap_procedimento_all WHERE CO_PROCEDIMENTO = '0301010064' ORDER BY 1;

-- Map a 2008+ code back to the old SIA code used in pa_legacy
SELECT * FROM sigtap_rl_procedimento_sia_sih WHERE CO_PROCEDIMENTO = '0301010064';
```

Or search names from the terminal: `uv run datasus sigtap search teleconsulta`.
