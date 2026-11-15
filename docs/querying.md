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
| `ufs` | State code, IBGE code, name and region — join on `uf`. |
| `procedimentos` | SIGTAP procedure names, group, complexity, funding, price — join `PA_PROC_ID = codigo`. |
| `cid10`, `ocupacoes` | ICD-10 and CBO (occupation) names — join on `PA_CIDPRI` / `PA_CBOCOD`. |
| `sigtap_*` | Every SIGTAP table (e.g. `sigtap_rl_procedimento_cid`); `…_all` keeps every version. |
