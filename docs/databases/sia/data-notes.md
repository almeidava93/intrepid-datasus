# Pitfalls: things to know before you count

SIA is billing data. It was built to pay facilities, not to answer research questions, and
a few of its habits produce wrong answers if you don't know them. The first five matter for
almost every query.

## 1. Sum quantities, don't count rows

One `pa` row can stand for thousands of procedures: a BPA-C line says "this facility did
1,200 blood pressure checks this month". Always sum the approved quantity.

```sql
-- Wrong: counts report lines
SELECT COUNT(*) FROM pa WHERE competencia = 202505;
-- Right: counts procedures
SELECT SUM(PA_QTDAPR) FROM pa WHERE competencia = 202505;
```

For money, sum `PA_VALAPR` (approved value). `PA_QTDPRO` / `PA_VALPRO` are what was
*submitted*, before the audit rejected part of it.

In the APAC tables (`am`, `aq`, `atd`, ...) a row **is** one authorisation in one month,
so `COUNT(*)` is right there; in the RAAS tables (`ps`, `sad`) count patient-months with
`SUM(QTDPCN::INT)`. Each table page has a *Counting* or *One row is* section.

## 2. About half of all procedures have no patient

Procedures reported on BPA-C (`PA_DOCORIG = 'C'`) are totals: no age, sex, diagnosis or
residence (`PA_SEXO = '0'`, `PA_MUNPCN = '999999'`, `PA_IDADE = '999'`). In May/2025 they
were 51% of all approved procedures.

Any breakdown by patient characteristic covers only the identified records
(`PA_DOCORIG IN ('I', 'P', 'S', 'A', 'B')`). Say so when you report it.

```sql
SELECT PA_DOCORIG, SUM(PA_QTDAPR) AS procedimentos,
       ROUND(100.0 * SUM(PA_QTDAPR) / SUM(SUM(PA_QTDAPR)) OVER (), 1) AS pct
FROM pa WHERE competencia = 202505
GROUP BY 1 ORDER BY 2 DESC;
```

## 3. Never add `pa` to a specialised table

`bi`, the APAC tables and the RAAS tables re-publish records that are already in `pa`.
Adding them double counts. See [Joins and double counting](joins.md).

## 4. Know which month you are looking at

- `competencia` (= `PA_MVM`) is the month the record was **processed**. It is the
  partition: filtering on it is fast.
- `PA_CMP` is the month the care **happened**. A month's file includes late reports from
  up to a few months earlier (in May/2025, 2.2% of procedures).

For "how much was done in March", group by `PA_CMP` and fetch a few months after March
too. For "what was paid in March", use `competencia`. DATASUS also **revises** recent
months after publishing them; re-run `datasus fetch` to pick up revisions.

Seasonality is strong (holidays, the number of working days, epidemics). Compare the same
month across years, or full years.

## 5. Facility location vs patient residence

- `PA_UFMUN`: municipality of the **facility** (where care was delivered).
- `PA_MUNPCN`: municipality where the **patient lives** (identified records only).
- `uf` (partition): the state whose file the row came from, i.e. the facility's state.

Rates per inhabitant should use the patient's residence; a facility in a regional hub
serves people from many municipalities.

## More things to know

- **Values are nominal R$.** Adjust for inflation (e.g. IPCA) before comparing years.
  Many primary-care procedures have a unit value of R$ 0: they are funded per capita (PAB),
  not per procedure, so SIA values say little about primary care spending.
- **Not informed codes:** `PA_CIDPRI = '0000'`, `PA_IDADE = '999'`, `PA_RACACOR = '99'`
  (or `'00'` on BPA-C), `PA_MUNPCN = '999999'`. Exclude them from distributions.
- **Codes are text.** Compare with quotes: `PA_TPFIN = '06'`, not `= 6`. Leading zeros
  matter.
- **Rejected lines are in the file.** `PA_INDICA = '0'` rows were not approved and have
  `PA_QTDAPR = 0`; summing `PA_QTDAPR` handles them.
- **Procedure codes changed in 2008.** `pa` (2008 →) uses SIGTAP codes; `pa_legacy`
  (1994–2007) uses the old SIA table. A series across 2008 needs a code mapping
  (`sigtap_rl_procedimento_sia_sih`) and care.
- **Medicines dominate counts.** Group `06` (medicines) is a third of all approved units
  (one tablet = one unit). Exclude `PA_PROC_ID LIKE '06%'` when you mean "care".
- **Coverage is SUS only.** Private and insurance-paid care is not here.
- Official layouts and code tables: [DATASUS – Transferência de arquivos](https://datasus.saude.gov.br/transferencia-de-arquivos/)
  (SIA → Documentação). Sources for each table are listed on [Joins](joins.md#sources).
