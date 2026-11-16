# SQL cookbook

Queries that answer real questions about SUS outpatient care. Copy one into
`uv run datasus shell` (or save it to a file and run `uv run datasus query -F file.sql`),
then change the months, states or codes.

**What you need fetched.** The `pa` recipes use one month for the whole country
(`uv run datasus fetch -s all -f 202505`) and the procedure names
(`uv run datasus sigtap fetch`). Recipes that compare years use **May of every year**
(`competencia % 100 = 5`), so fetch May of the years you want
(`for y in 2019 2020 ...: datasus fetch -s all -f ${y}05`), or change the filter to the
months you have. With a single small state (`-s AC`) every query still runs, just on less
data. The numbers quoted below come from a run on May 2019–2026, all states.

!!! tip "Make every query fast"
    Always filter on `competencia` (and `uf` when you can). They are partition columns,
    so DuckDB only reads the files for those months and states.

Before you trust a number, read [Pitfalls](data-notes.md): sum `PA_QTDAPR`, never count rows;
half of the procedures have no patient data; never add a specialised table to `pa`.

## The big picture

### How much outpatient care does SUS pay for, and how is it changing?

```sql
SELECT competencia,
       SUM(PA_QTDAPR)                 AS procedimentos,
       ROUND(SUM(PA_VALAPR) / 1e6, 1) AS valor_milhoes_rs
FROM pa
WHERE competencia % 100 = 5          -- May of every fetched year
GROUP BY 1 ORDER BY 1;
```

About 320 million procedures in May/2019, 215 million in May/2020 (the first COVID-19
wave), and 460 million in May/2026. Values are nominal: adjust for inflation before
comparing years.

### Which states produce the most, and how much is paid?

```sql
SELECT u.regiao, u.nome AS estado,
       SUM(PA_QTDAPR)                 AS procedimentos,
       ROUND(SUM(PA_VALAPR) / 1e6, 1) AS valor_milhoes_rs
FROM pa JOIN ufs u USING (uf)
WHERE competencia = 202505
GROUP BY ALL ORDER BY procedimentos DESC;
```

To compare states fairly, divide by population (not included; IBGE publishes yearly
estimates per state and municipality).

### How much of it has patient data?

```sql
SELECT CASE PA_DOCORIG WHEN 'C' THEN 'BPA-C (totals, no patient)'
                       WHEN 'I' THEN 'BPA-I (per patient)'
                       WHEN 'P' THEN 'APAC main procedure'
                       WHEN 'S' THEN 'APAC secondary procedure'
                       WHEN 'B' THEN 'RAAS psychosocial (CAPS)'
                       WHEN 'A' THEN 'RAAS home care' END AS instrumento,
       SUM(PA_QTDAPR) AS procedimentos,
       ROUND(100.0 * SUM(PA_QTDAPR) / SUM(SUM(PA_QTDAPR)) OVER (), 1) AS pct_procedimentos,
       ROUND(100.0 * SUM(PA_VALAPR) / SUM(SUM(PA_VALAPR)) OVER (), 1) AS pct_valor
FROM pa
WHERE competencia = 202505
GROUP BY 1 ORDER BY procedimentos DESC;
```

In May/2025 BPA-C was 51% of procedures but 31% of the value; APACs were 26% of
procedures and 35% of the value.

## What is done

### The 20 most frequent procedures

```sql
SELECT p.nome, p.complexidade, SUM(PA_QTDAPR) AS procedimentos
FROM pa JOIN procedimentos p ON p.codigo = pa.PA_PROC_ID
WHERE competencia = 202505
GROUP BY ALL ORDER BY procedimentos DESC LIMIT 20;
```

Medicines (one tablet = one unit) fill a third of the list. Add
`AND PA_PROC_ID NOT LIKE '06%'` to see care only.

### Where does the money go?

```sql
SELECT p.nome,
       ROUND(SUM(PA_VALAPR) / 1e6, 1) AS valor_milhoes_rs,
       ROUND(100.0 * SUM(PA_VALAPR) / SUM(SUM(PA_VALAPR)) OVER (), 2) AS pct_do_total
FROM pa JOIN procedimentos p ON p.codigo = pa.PA_PROC_ID
WHERE competencia = 202505
GROUP BY 1 ORDER BY valor_milhoes_rs DESC LIMIT 15;
```

Haemodialysis alone was 12.8% of the outpatient value in May/2025.

### Volume and value by procedure group and complexity

```sql
SELECT p.grupo, p.complexidade,
       SUM(PA_QTDAPR)                 AS procedimentos,
       ROUND(SUM(PA_VALAPR) / 1e6, 1) AS valor_milhoes_rs
FROM pa JOIN procedimentos p ON p.codigo = pa.PA_PROC_ID
WHERE competencia = 202505
GROUP BY ALL ORDER BY 1, 2;
```

### By funding source

```sql
SELECT f.NO_FINANCIAMENTO AS financiamento,
       SUM(PA_QTDAPR)                 AS procedimentos,
       ROUND(SUM(PA_VALAPR) / 1e6, 1) AS valor_milhoes_rs
FROM pa LEFT JOIN sigtap_financiamento f ON f.CO_FINANCIAMENTO = pa.PA_TPFIN
WHERE competencia = 202505
GROUP BY 1 ORDER BY 3 DESC;
```

Primary care (PAB) procedures show R$ 0: they are funded per capita, not per procedure.

### The three most frequent high-complexity procedures in each state

```sql
SELECT uf, p.nome, SUM(PA_QTDAPR) AS procedimentos
FROM pa JOIN procedimentos p ON p.codigo = pa.PA_PROC_ID
WHERE competencia = 202505
  AND p.complexidade = 'Alta Complexidade'
  AND p.grupo_cod <> '06'                       -- leave medicines out
GROUP BY 1, 2
QUALIFY ROW_NUMBER() OVER (PARTITION BY uf ORDER BY procedimentos DESC) <= 3
ORDER BY uf, procedimentos DESC;
```

`QUALIFY` filters on a window function, like `HAVING` does on an aggregate.

### Which kinds of care fell most in the first COVID-19 wave?

```sql
SELECT p.grupo,
       SUM(PA_QTDAPR) FILTER (WHERE competencia = 201905) AS mai_2019,
       SUM(PA_QTDAPR) FILTER (WHERE competencia = 202005) AS mai_2020,
       ROUND(100.0 * mai_2020 / mai_2019 - 100, 1)        AS variacao_pct
FROM pa JOIN procedimentos p ON p.codigo = pa.PA_PROC_ID
WHERE competencia IN (201905, 202005)
GROUP BY 1 ORDER BY variacao_pct;
```

Surgical procedures fell 58% between May/2019 and May/2020; medicines rose 19%.

## Who is treated

These use identified records only (BPA-I, APAC, RAAS). See
[pitfall 2](data-notes.md#2-about-half-of-all-procedures-have-no-patient).

### Age and sex

```sql
SELECT CASE WHEN TRY_CAST(PA_IDADE AS INT) >= 80 THEN '80+'
            ELSE LPAD(CAST(TRY_CAST(PA_IDADE AS INT) // 10 * 10 AS VARCHAR), 2, '0')
                 || '-' || CAST(TRY_CAST(PA_IDADE AS INT) // 10 * 10 + 9 AS VARCHAR)
       END AS faixa_etaria,
       SUM(PA_QTDAPR) FILTER (WHERE PA_SEXO = 'F') AS mulheres,
       SUM(PA_QTDAPR) FILTER (WHERE PA_SEXO = 'M') AS homens
FROM pa
WHERE competencia = 202505
  AND PA_DOCORIG IN ('I', 'P', 'S')
  AND PA_IDADE <> '999'
GROUP BY 1 ORDER BY 1;
```

### Race/colour

```sql
SELECT CASE PA_RACACOR WHEN '01' THEN 'Branca' WHEN '02' THEN 'Preta'
                       WHEN '03' THEN 'Parda'  WHEN '04' THEN 'Amarela'
                       WHEN '05' THEN 'Indígena' ELSE 'Sem informação' END AS raca_cor,
       SUM(PA_QTDAPR) AS procedimentos,
       ROUND(100.0 * SUM(PA_QTDAPR) / SUM(SUM(PA_QTDAPR)) OVER (), 1) AS pct
FROM pa
WHERE competencia = 202505 AND PA_DOCORIG IN ('I', 'P', 'S')
GROUP BY 1 ORDER BY procedimentos DESC;
```

### The most frequent diagnoses

```sql
SELECT c.codigo, c.nome AS diagnostico, SUM(PA_QTDAPR) AS procedimentos
FROM pa JOIN cid10 c ON c.codigo = pa.PA_CIDPRI
WHERE competencia = 202505
  AND PA_DOCORIG IN ('I', 'P')                  -- one row per appointment / APAC
  AND PA_CIDPRI <> '0000'
GROUP BY ALL ORDER BY procedimentos DESC LIMIT 15;
```

Group by chapter or category instead with `LEFT(PA_CIDPRI, 3)` (`cid10` has the
3-character categories too: `C50` = breast cancer).

### Which professionals deliver the care?

```sql
SELECT o.nome AS ocupacao, SUM(PA_QTDAPR) AS procedimentos
FROM pa JOIN ocupacoes o ON o.codigo = pa.PA_CBOCOD
WHERE competencia = 202505
GROUP BY 1 ORDER BY 2 DESC LIMIT 15;
```

## Where care happens

### How often do patients travel outside their municipality?

```sql
SELECT CASE PA_NIVCPL WHEN '1' THEN '1 Atenção básica'
                      WHEN '2' THEN '2 Média complexidade'
                      WHEN '3' THEN '3 Alta complexidade'
                      ELSE '0 Não se aplica' END AS complexidade,
       SUM(PA_QTDAPR) AS procedimentos,
       ROUND(100.0 * SUM(PA_QTDAPR) FILTER (WHERE PA_MUNPCN <> PA_UFMUN)
             / SUM(PA_QTDAPR), 1) AS pct_fora_do_municipio
FROM pa
WHERE competencia = 202505
  AND PA_DOCORIG IN ('I', 'P', 'S')
  AND PA_MUNPCN <> '999999'
  AND PA_PROC_ID NOT LIKE '06%'                 -- medicines are dispensed centrally
GROUP BY 1 ORDER BY 1;
```

In May/2025, 5% of identified primary care was delivered outside the patient's
municipality, 18% of medium complexity and 40% of high complexity.

### Interstate flows for high-complexity care

```sql
SELECT r.nome AS estado_residencia, a.nome AS estado_atendimento,
       SUM(PA_QTDAPR) AS procedimentos,
       ROUND(SUM(PA_VALAPR) / 1e6, 2) AS valor_milhoes_rs
FROM pa
JOIN ufs r ON r.ibge = LEFT(pa.PA_MUNPCN, 2)    -- patient's state ('999999' drops out)
JOIN ufs a ON a.uf = pa.uf                      -- facility's state
WHERE competencia = 202505
  AND PA_NIVCPL = '3'
  AND r.uf <> a.uf
GROUP BY ALL ORDER BY procedimentos DESC LIMIT 15;
```

### The largest facilities in a state

```sql
SELECT PA_CODUNI AS cnes, PA_UFMUN AS municipio_ibge,
       SUM(PA_QTDAPR)                 AS procedimentos,
       ROUND(SUM(PA_VALAPR) / 1e6, 2) AS valor_milhoes_rs
FROM pa
WHERE competencia = 202505 AND uf = 'BA'
GROUP BY ALL ORDER BY valor_milhoes_rs DESC LIMIT 10;
```

Facility names are in CNES (planned); until then look a code up at
[cnes.datasus.gov.br](https://cnes.datasus.gov.br/).

## Public health topics

### Breast cancer screening: mammograms in the target age group

The Ministry of Health recommends screening mammography every two years for women aged
50–69. Procedure `0204030188` is *mamografia bilateral para rastreamento*.

```sql
SELECT u.nome AS estado,
       SUM(PA_QTDAPR) AS mamografias_rastreamento,
       ROUND(100.0 * SUM(PA_QTDAPR) FILTER (WHERE TRY_CAST(PA_IDADE AS INT) BETWEEN 50 AND 69)
             / SUM(PA_QTDAPR), 1) AS pct_50_a_69_anos
FROM pa JOIN ufs u USING (uf)
WHERE competencia BETWEEN 202501 AND 202512
  AND PA_PROC_ID = '0204030188'
  AND PA_SEXO = 'F'
GROUP BY 1 ORDER BY 2 DESC;
```

About a third of screening mammograms are done outside the recommended age group.

### Cancer screening before, during and after COVID-19

```sql
SELECT competencia // 100 AS ano,
       SUM(PA_QTDAPR) FILTER (WHERE PA_PROC_ID = '0204030188') AS mamografia_rastreamento,
       SUM(PA_QTDAPR) FILTER (WHERE PA_PROC_ID IN ('0203010086', '0203010019')) AS citopatologico_colo_utero
FROM pa
WHERE competencia % 100 = 5
  AND PA_PROC_ID IN ('0204030188', '0203010086', '0203010019')
GROUP BY 1 ORDER BY 1;
```

Both fell by over 80% in May/2020 and were back at 2019 levels by May/2022.

### Telehealth adoption

```sql
PIVOT (
  SELECT competencia // 100 AS ano, p.nome, PA_QTDAPR
  FROM pa JOIN procedimentos p ON p.codigo = pa.PA_PROC_ID
  WHERE competencia % 100 = 5
    AND (p.nome ILIKE 'teleconsulta%' OR p.nome ILIKE 'teleatendimento%')
) ON ano USING SUM(PA_QTDAPR) GROUP BY nome ORDER BY nome;
```

`PIVOT` turns the years into columns. Find other codes with
`uv run datasus sigtap search tele`.

### Mental health: CAPS activity by state

```sql
SELECT u.nome AS estado,
       COUNT(DISTINCT PA_CODUNI)      AS caps,
       SUM(PA_QTDAPR)                 AS acoes,
       ROUND(SUM(PA_VALAPR) / 1e6, 2) AS valor_milhoes_rs
FROM pa JOIN ufs u USING (uf)
WHERE competencia = 202505
  AND PA_TPUPS = '70'                           -- facility type: CAPS
GROUP BY 1 ORDER BY acoes DESC;
```

For patients, diagnoses, drug use and homelessness, use [`ps`](ps.md#examples).

### Haemodialysis sessions and patients by state

```sql
SELECT u.nome AS estado,
       SUM(PA_QTDAPR)            AS sessoes,
       COUNT(DISTINCT PA_AUTORIZ) AS apacs      -- about one APAC per patient per month
FROM pa JOIN ufs u USING (uf)
WHERE competencia = 202505
  AND PA_PROC_ID IN ('0305010107', '0305010115')
  AND PA_DOCORIG IN ('P', 'S')
GROUP BY 1 ORDER BY sessoes DESC;
```

For dialysis type, vascular access and lab values, use [`atd`](atd.md#examples).

## Billing and data quality

### How much of what was submitted was rejected?

```sql
SELECT uf,
       SUM(PA_QTDPRO) AS apresentados,
       SUM(PA_QTDAPR) AS aprovados,
       ROUND(100.0 * (1 - SUM(PA_QTDAPR) / SUM(PA_QTDPRO)), 1)              AS pct_glosado,
       ROUND(100.0 * (1 - SUM(PA_VALAPR) / NULLIF(SUM(PA_VALPRO), 0)), 1)   AS pct_valor_glosado
FROM pa
WHERE competencia = 202505
GROUP BY 1 ORDER BY pct_glosado DESC;
```

### How much of a month's file is late reporting?

```sql
SELECT PA_CMP AS mes_atendimento,
       SUM(PA_QTDAPR) AS procedimentos,
       ROUND(100.0 * SUM(PA_QTDAPR) / SUM(SUM(PA_QTDAPR)) OVER (), 2) AS pct
FROM pa
WHERE competencia = 202505
GROUP BY 1 ORDER BY 1 DESC;
```

## Specialised tables

These need the file type fetched (`-T bi`, `-T aq`, ...). Patient identifiers in the APAC
and RAAS tables are encoded and often missing on recent rows; read the table page before
counting patients.

### Distinct patients and procedures per patient (BPA-I)

```sql
SELECT uf,
       COUNT(DISTINCT CNS_PAC) AS pacientes,
       SUM(QT_APROV)           AS procedimentos,
       ROUND(SUM(QT_APROV) / COUNT(DISTINCT CNS_PAC), 1) AS procedimentos_por_paciente
FROM bi
WHERE competencia = 202605
  AND COALESCE(TRIM(CNS_PAC), '') <> ''         -- CNS is empty on about half of the rows
GROUP BY 1 ORDER BY pacientes DESC;
```

### Chemotherapy by cancer site

```sql
SELECT LEFT(AP_CIDPRI, 3) AS cid, c.nome AS cancer,
       COUNT(*) AS apacs,                       -- one row = one APAC in one month
       ROUND(SUM(AP_VL_AP) / 1e6, 2) AS valor_milhoes_rs
FROM aq LEFT JOIN cid10 c ON c.codigo = LEFT(aq.AP_CIDPRI, 3)
WHERE competencia = 202605
GROUP BY 1, 2 ORDER BY apacs DESC LIMIT 15;
```

### Dialysis patients by age group and sex

```sql
SELECT CASE WHEN idade < 18 THEN '0-17' WHEN idade < 40 THEN '18-39'
            WHEN idade < 60 THEN '40-59' WHEN idade < 75 THEN '60-74' ELSE '75+' END AS faixa,
       COUNT(*) FILTER (WHERE AP_SEXO = 'F') AS mulheres,
       COUNT(*) FILTER (WHERE AP_SEXO = 'M') AS homens
FROM (SELECT AP_SEXO,
             CASE AP_COIDADE WHEN '4' THEN TRY_CAST(AP_NUIDADE AS INT)
                             WHEN '5' THEN 100 + TRY_CAST(AP_NUIDADE AS INT)
                             ELSE 0 END AS idade       -- '2' days, '3' months
      FROM atd WHERE competencia = 202605)
GROUP BY 1 ORDER BY 1;
```

### High-cost medicines: patients and spending per drug

```sql
SELECT p.nome AS medicamento,
       COUNT(DISTINCT AP_CNSPCN)       AS pacientes,
       ROUND(SUM(AP_VL_AP) / 1e6, 2)   AS valor_milhoes_rs,
       ROUND(SUM(AP_VL_AP) / COUNT(DISTINCT AP_CNSPCN), 2) AS valor_por_paciente
FROM am JOIN procedimentos p ON p.codigo = am.AP_PRIPAL
WHERE competencia = 202605
GROUP BY 1 ORDER BY valor_milhoes_rs DESC LIMIT 15;
```

### CAPS patients living on the street, by state

```sql
SELECT uf,
       SUM(QTDPCN::INT)                                   AS pacientes_mes,
       SUM(QTDPCN::INT) FILTER (WHERE SIT_RUA = 'S')      AS em_situacao_de_rua,
       ROUND(100.0 * em_situacao_de_rua / pacientes_mes, 1) AS pct
FROM ps
WHERE competencia = 202605
GROUP BY 1 ORDER BY pct DESC;
```

### More recipes on the table pages

| Question | Recipe |
|---|---|
| Age pyramid of patients seen for hypertension; where patients come from | [bi](bi.md#examples) |
| New patients per year on a medicine; units dispensed | [am](am.md#examples) |
| Stage at diagnosis of breast cancer; changes of treatment purpose | [aq](aq.md#examples) |
| Radiotherapy by site and purpose; chemoradiation for cervical cancer | [ar](ar.md#examples) |
| What AD holds; cataract surgery per month and patients aged 60+ | [ad](ad.md#examples) |
| Haemoglobin of haemodialysis patients; vascular access; transplant list | [atd](atd.md#examples) |
| Dialysis before 2014; a continuous series across the AN → ATD switch | [an](an.md#examples) |
| Pre-dialysis CKD: patients per stage; did referred patients get a fistula before dialysis? | [amp](amp.md#examples) |
| Fistulas per year; new haemodialysis patients with a fistula; fistulas vs catheters and grafts | [acf](acf.md#examples) |
| Bariatric follow-up: patients per year, type of surgery, comorbidities by months since surgery | [abo](abo.md#examples), [ab](ab.md#examples) |
| CAPS patients, diagnoses, drug use | [ps](ps.md#examples) |
| Home care: patient-months, diagnoses, how episodes end | [sad](sad.md#examples) |
| Production before 2008 | [pa_legacy](pa_legacy.md) |
| Procedure rules, prices over time, old-code mapping | [SIGTAP](../../lookups/sigtap.md#examples) |

## Exporting and reusing results

```bash
# CSV, Parquet or JSON, from a file or an inline query
uv run datasus query -F mamografias.sql -o mamografias.csv
uv run datasus query --format csv "SELECT ..." > out.csv
```

Inside the shell, DuckDB's `COPY` writes any query to a file:

```sql
COPY (SELECT uf, SUM(PA_QTDAPR) AS qtd FROM pa WHERE competencia = 202505 GROUP BY 1)
TO 'producao_por_uf.csv' (HEADER);
```

To adjust values for inflation, put an index in a CSV (`ano,fator`, with the factor that
brings each year to today's R$) and join it:

```sql
SELECT competencia // 100 AS ano,
       ROUND(SUM(PA_VALAPR) / 1e6, 1)           AS valor_nominal_milhoes,
       ROUND(SUM(PA_VALAPR) * ANY_VALUE(i.fator) / 1e6, 1) AS valor_real_milhoes
FROM pa JOIN read_csv('ipca.csv') i ON i.ano = competencia // 100
WHERE competencia % 100 = 5
GROUP BY 1 ORDER BY 1;
```
