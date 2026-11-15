# Things to know about the data

- **Sum `PA_QTDAPR`, don't count rows.** One row can stand for thousands of procedures.
- **Half of all procedures have no patient data.** Consolidated reports (`PA_DOCORIG = 'C'`)
  have no age, sex, diagnosis or residence (`PA_SEXO = '0'`, `PA_MUNPCN = '999999'`).
- `PA_UFMUN` is where the **facility** is; `PA_MUNPCN` is where the **patient lives**.
- `competencia` is the processing month (`PA_MVM`); `PA_CMP` is when care happened and
  includes late reports from earlier months.
- Values are nominal R$ — adjust for inflation (e.g. IPCA) before comparing years.
- "Not informed" codes: `PA_CIDPRI = '0000'`, `PA_IDADE = '999'`, `PA_RACACOR = '00'`/`'99'`.
- Official layout and code tables: [DATASUS – Transferência de arquivos](https://datasus.saude.gov.br/transferencia-de-arquivos/) (SIA → Documentação).
