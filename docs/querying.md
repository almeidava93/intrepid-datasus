# Querying

```bash
uv run datasus query "SELECT uf, SUM(PA_QTDAPR) AS procedimentos, SUM(PA_VALAPR) AS valor
                      FROM pa WHERE competencia BETWEEN 202501 AND 202512
                      GROUP BY uf ORDER BY procedimentos DESC"

uv run datasus query -F my_query.sql -o result.csv     # also .parquet / .json
uv run datasus query --format csv "SELECT ..." > out.csv
uv run datasus shell                                    # interactive SQL prompt
uv run datasus schema                                   # columns + descriptions (pa)
uv run datasus schema --legacy                          # columns of pa_legacy
uv run datasus status                                   # what's stored locally (pa)
uv run datasus status -T all                            # ... for every table
uv run datasus remove -s RR -f 2026                     # delete local data (pa)
```

Tables available in SQL (full column reference in the [Tables](tables/index.md) tab):

| Table | Contents |
|---|---|
| `pa` | 2008 onward (SIGTAP procedure codes). Quantities as `BIGINT`, values as `DOUBLE`. |
| `pa_legacy` | 1994–2007 (old layout and procedure table — different columns). |
| `pa_raw`, `pa_legacy_raw` | Same, every column as text, exactly as DATASUS publishes it. |
| `bi`, `bi_raw` | BPA Individualizado (`-T bi`, 2008 onward): one row per patient appointment, with age, sex, residence and diagnosis. Same rows as `pa WHERE PA_DOCORIG = 'I'` — don't add the two. |
| `am`, `am_raw` | APAC Medicamentos (`-T am`, 2008 onward): one row per APAC for a high-cost medicine per month, with patient, diagnosis, validity and continuation. Same APACs as `pa WHERE PA_DOCORIG = 'P' AND PA_TPFIN = '02'` — don't add the two. |
| `aq`, `aq_raw` | APAC Quimioterapia (`-T aq`, 2008 onward): one row per chemotherapy/hormone therapy APAC per month, with cancer ICD-10, stage, lymph nodes, treatment purpose, scheme and dates. Same APACs as `pa WHERE PA_DOCORIG = 'P'` with procedures `030402`–`030408` — don't add the two. |
| `ar`, `ar_raw` | APAC Radioterapia (`-T ar`, 2008 onward): one row per radiotherapy APAC per month, with cancer ICD-10, stage, treatment purpose, treated areas, number of fields/insertions and dates. Same APACs as `pa WHERE PA_DOCORIG = 'P'` with procedures `030401` — don't add the two. |
| `ad`, `ad_raw` | APAC Laudos Diversos (`-T ad`, 2008 onward): one row per APAC per month for the procedures with no laudo of their own: cataract and other eye surgery, eye injections, cardiac catheterisation, hearing diagnosis and aids, transplant follow-up, PET-CT, wheelchairs, and (until 2012) CAPS mental health care. Same APACs as some of the `pa WHERE PA_DOCORIG = 'P'` rows — don't add the two. |
| `atd`, `atd_raw` | APAC Tratamento Dialítico (`-T atd`, Aug/2014 onward; AN before): one row per dialysis APAC per month — in practice one patient on chronic dialysis per month — with dialysis type, vascular access, transplant status, lab values (haemoglobin, phosphorus, albumin, PTH, Kt/V, URR) and serology. Same APACs as `pa WHERE PA_DOCORIG = 'P' AND PA_PROC_ID LIKE '0305%'` — don't add the two. |
| `an`, `an_raw` | APAC Nefrologia (`-T an`, Jan/2008 to Jul/2014; ATD after): the dialysis APACs before ATD, one row per APAC per month — about one patient on chronic dialysis per month — with first-dialysis date, height, weight, diuresis, glucose, transplant list, URR, albumin, haemoglobin and serology. Same APACs as `pa WHERE PA_DOCORIG = 'P' AND PA_PROC_ID LIKE '0305%'` until May/2014 — don't add the two. |
| `ps`, `ps_raw` | RAAS Psicossocial (`-T ps`, Nov/2012 onward): CAPS psychosocial care, one row per action line of a patient's monthly RAAS (`QTDPCN = '1'` marks one row per patient-month), with diagnosis, drugs used, street situation, origin, days in care. Same rows as `pa WHERE PA_DOCORIG = 'B'` (R$ 0) — don't add the two. |
| `sad`, `sad_raw` | RAAS Atenção Domiciliar (`-T sad`, Apr/2012 to Oct/2018, in practice to Jun/2016; later home care is in SISAB, not on the FTP): Melhor em Casa home-care teams, one row per action line of a patient's monthly RAAS (`QTDPCN = '1'` marks one row per patient-month), with diagnosis, team, origin, destination, days in care. Same rows as `pa WHERE PA_DOCORIG = 'A'` (R$ 0) — don't add the two. |
| `ufs` | State code, IBGE code, name and region — join on `uf`. |
| `procedimentos` | SIGTAP procedure names, group, complexity, funding, price — join `PA_PROC_ID = codigo`. |
| `cid10`, `ocupacoes` | ICD-10 and CBO (occupation) names — join on `PA_CIDPRI` / `PA_CBOCOD`. |
| `sigtap_*` | Every SIGTAP table (e.g. `sigtap_rl_procedimento_cid`); `…_all` keeps every version. |
