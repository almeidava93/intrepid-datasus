# Lookup tables

Friendly tables that turn the codes in `pa` into names. `ufs` is always there; the others
are built from SIGTAP and appear after `uv run datasus sigtap fetch`.

## ufs

Built into the package, no download needed. 27 rows.

| Column | Type | Meaning |
|---|---|---|
| `uf` | text | State abbreviation (`SP`). Joins the `uf` partition of `pa`, `pa_legacy`, `bi`, `am`. |
| `ibge` | text | 2-digit IBGE state code (`35`). Matches the first two digits of `PA_UFMUN`, `PA_MUNPCN`, `PA_GESTAO` (and `UFMUN`, `MUNPAC`, `GESTAO` in `bi`; `AP_UFMUN`, `AP_MUNPCN`, `AP_GESTAO` in `am`). |
| `nome` | text | State name (`São Paulo`). |
| `regiao` | text | Region: `Norte`, `Nordeste`, `Sudeste`, `Sul`, `Centro-Oeste`. |

```sql
-- by region of the patient's residence ('999999' = not informed drops out of the join)
SELECT u.regiao, SUM(PA_QTDAPR) FROM pa
JOIN ufs u ON u.ibge = LEFT(pa.PA_MUNPCN, 2)
WHERE competencia = 202505 GROUP BY 1;
```

## procedimentos

One row per SIGTAP procedure code, with its hierarchy, complexity, funding and price, taken
from the most recent SIGTAP version you fetched that contains the code. Join with
`pa.PA_PROC_ID = procedimentos.codigo`.

| Column | Type | Meaning | Source in SIGTAP |
|---|---|---|---|
| `codigo` | text | 10-digit procedure code. | `tb_procedimento.CO_PROCEDIMENTO` |
| `nome` | text | Procedure name. | `NO_PROCEDIMENTO` |
| `grupo_cod` | text | Group code (first 2 digits). | |
| `grupo` | text | Group name (e.g. *Procedimentos clínicos*). | `tb_grupo` |
| `subgrupo` | text | Subgroup name (digits 1–4). | `tb_sub_grupo` |
| `forma_organizacao` | text | Form of organisation (digits 1–6). | `tb_forma_organizacao` |
| `complexidade` | text | `Não se aplica`, `Atenção Básica`, `Média Complexidade`, `Alta Complexidade`. | `TP_COMPLEXIDADE` |
| `financiamento_cod` | text | Funding code (same codes as `PA_TPFIN`). | `CO_FINANCIAMENTO` |
| `financiamento` | text | Funding name (e.g. *Média e Alta Complexidade (MAC)*). | `tb_financiamento` |
| `sexo` | text | Sex allowed: `M`, `F`, `I` (both), `N` (not applicable). | `TP_SEXO` |
| `idade_minima_meses` | integer | Minimum age, **in months**. `9999` = age not required. | `VL_IDADE_MINIMA` |
| `idade_maxima_meses` | integer | Maximum age, **in months**. `1571` (≈ 130 years) is the usual "any age"; `9999` = age not required. | `VL_IDADE_MAXIMA` |
| `valor_ambulatorial` | double | Outpatient service value, R$ (`SA`). | `VL_SA / 100` |
| `valor_hospitalar` | double | Hospital service value, R$ (`SH`). | `VL_SH / 100` |
| `valor_profissional` | double | Professional service value, R$ (`SP`). | `VL_SP / 100` |
| `primeira_versao` | integer | First fetched SIGTAP version (`YYYYMM`) that has the code. | |
| `ultima_versao` | integer | Last fetched version that has the code. | |
| `ativo` | boolean | The code is in the most recent version you fetched. | |

SIGTAP procedure groups (first 2 digits):

| Code | Group |
|---|---|
| `01` | Ações de promoção e prevenção em saúde |
| `02` | Procedimentos com finalidade diagnóstica |
| `03` | Procedimentos clínicos |
| `04` | Procedimentos cirúrgicos |
| `05` | Transplantes de órgãos, tecidos e células |
| `06` | Medicamentos |
| `07` | Órteses, próteses e materiais especiais |
| `08` | Ações complementares da atenção à saúde |
| `09` | Procedimentos para Ofertas de Cuidados Integrados |

!!! tip "Old and retired codes"
    Fetch several versions (`datasus sigtap fetch --from 2008 --yearly`) so codes retired
    years ago still get a name. With `--yearly`, `primeira_versao` / `ultima_versao` are
    precise only to the year.

## cid10

ICD-10 codes as used by SUS (`sigtap_cid`). Join `pa.PA_CIDPRI`, `PA_CIDSEC` or
`PA_CIDCAS` to `codigo`.

| Column | Type | Meaning |
|---|---|---|
| `codigo` | text | ICD-10 code without the dot (`J189`). |
| `nome` | text | Description. |
| `sexo` | text | Sex the code applies to (`M`, `F`, `I` both). |
| `ativo` | boolean | In the most recent version fetched. |

## ocupacoes

CBO occupations (`sigtap_ocupacao`). Join `pa.PA_CBOCOD` to `codigo`.

| Column | Type | Meaning |
|---|---|---|
| `codigo` | text | 6-digit CBO code (`225125` = clinical physician). |
| `nome` | text | Occupation name. |
| `ativo` | boolean | In the most recent version fetched. |

```sql
SELECT o.nome, SUM(PA_QTDAPR) qtd
FROM pa JOIN ocupacoes o ON o.codigo = pa.PA_CBOCOD
WHERE competencia = 202505 GROUP BY 1 ORDER BY 2 DESC LIMIT 15;
```
