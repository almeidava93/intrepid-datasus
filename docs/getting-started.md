# Getting started

This page takes you from nothing to your first answers in about ten minutes. It uses
**Acre** (`AC`), a small state, so downloads are a few MB.

## 1. Install

You need [uv](https://docs.astral.sh/uv/) (it installs the right Python for you).

```bash
git clone https://github.com/almeidava93/intrepid-datasus.git
cd intrepid-datasus
uv sync
uv run datasus --help
```

## 2. See what is published

```bash
uv run datasus available -s AC -f 2025
```

This lists the files on the DATASUS FTP for Acre in 2025, with their sizes. Nothing is
downloaded.

## 3. Fetch one month, and the procedure names

```bash
uv run datasus fetch -s AC -f 202505
uv run datasus sigtap fetch
```

The first command downloads the SIA production file (PA) for Acre, May/2025, and stores it
as Parquet under `./data`. The second downloads SIGTAP, the table that turns procedure
codes (`0301010064`) into names (*consulta médica em atenção primária*).

```bash
uv run datasus status          # what you have locally
```

## 4. Ask your first questions

Open the interactive SQL prompt:

```bash
uv run datasus shell
```

How many procedures did SUS pay for in Acre that month, and how much did it pay?

```sql
SELECT SUM(PA_QTDAPR) AS procedimentos, ROUND(SUM(PA_VALAPR)) AS valor_rs
FROM pa
WHERE competencia = 202505 AND uf = 'AC';
```

Which procedures were most frequent?

```sql
SELECT p.nome, SUM(PA_QTDAPR) AS procedimentos
FROM pa JOIN procedimentos p ON p.codigo = pa.PA_PROC_ID
WHERE competencia = 202505
GROUP BY 1 ORDER BY 2 DESC LIMIT 10;
```

What are the most common diagnoses among patients with individual records?

```sql
SELECT c.nome AS diagnostico, SUM(PA_QTDAPR) AS procedimentos
FROM pa JOIN cid10 c ON c.codigo = pa.PA_CIDPRI
WHERE competencia = 202505 AND PA_DOCORIG IN ('I', 'P') AND PA_CIDPRI <> '0000'
GROUP BY 1 ORDER BY 2 DESC LIMIT 10;
```

Type `.tables` to list every table, `.schema pa` to list its columns, and `.quit` to
leave. Or, from the terminal, `uv run datasus schema` prints every column of `pa` with
its description.

!!! warning "Three things to remember"
    1. **Sum `PA_QTDAPR`**, don't count rows: one row can be thousands of procedures.
    2. **About half of the procedures have no patient data** (age, sex, diagnosis). Those
       are the `PA_DOCORIG = 'C'` rows.
    3. **Filter on `competencia` and `uf`**: they decide which files are read, so queries
       stay fast.

    The full list is in [Pitfalls](databases/sia/data-notes.md).

## 5. Run a query from a file, save the result

```bash
uv run datasus query -F my_query.sql -o result.csv     # also .parquet or .json
```

## Where to go next

- **Which table answers my question?** [SIA overview](databases/sia/index.md#which-table-do-i-need)
- **Ready-made queries** for meaningful questions: [SQL cookbook](databases/sia/examples.md)
- **What the codes mean** (competência, CNES, SIGTAP, CID-10, ...): [Key concepts](concepts.md)
- **More data:** more states and months, other file types: [Fetching data](guide/fetching.md)
- **Use Python, R or another tool** instead of the CLI: [Querying](guide/querying.md#from-python-r-or-other-tools)
