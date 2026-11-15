# Development

```bash
uv run pytest
```

Source: `src/intrepid_datasus/` — `catalog.py` (registry of SIA file types, FTP listing, states, periods), `convert.py`
(.dbc → Parquet), `store.py` (local layout and manifest), `fetch.py`, `query.py` (DuckDB views),
`dictionary.py` (column descriptions), `cli.py`.

## How file types are modelled

Each SIA file type (PA, BI, AQ, ATD, ...) is one `FileType` in `catalog.REGISTRY`. A file
type has one or more `Era`s, one per file layout over time, oldest first, not overlapping.
Each era is one FTP folder, one local folder and one pair of DuckDB views:

| `Era` field | Meaning | PA example |
|---|---|---|
| `key` | local folder `data/<key>/` and view names `<key>`, `<key>_raw` | `pa`, `pa_legacy` |
| `ftp_dir` | FTP folder with the files | `FTP_CURRENT_DIR` (`200801_/Dados`) |
| `first`, `last` | months covered (`YYYYMM`, inclusive; `999912` = still published) | `200801`–`999912` |
| `dictionary` | `{column: description}` from `dictionary.py` | `dictionary.PA` |
| `quantity_cols`, `value_cols` | text columns cast to `BIGINT` / `DOUBLE` in the typed view | `PA_QTDAPR`, `PA_VALAPR` |

Everything else is derived from the registry: the filename pattern
(`<CODE><UF><YY><MM>[part].dbc`, matched per code so `AM` never claims `AMP` files and `AB`
never claims `ABO` files), which FTP folders to list (each folder is listed once, whatever
the number of file types), the `--table/-T` choices, the local layout, the manifest keys
(`<CODE>/<UF>/<YYYYMM>`, e.g. `PA/SP/202605`) and the views. Store, fetch and query code
contain no per-type logic; adding a file type should not need changes there.

The manifest used to key PA entries as `SP/202605`; `Store.manifest()` reads such keys as
PA, and the next write saves them in the new form.

## Adding a new SIA file type

Every file type sub-issue of #3 follows these steps. `BI` is used as the example.

1. **Check the FTP.** Download one small file, e.g. `BIAC2605.dbc` from
   `ftp.datasus.gov.br/dissemin/publicos/SIASUS/200801_/Dados`, and read its columns with
   `convert.read_dbf_header` (after decompressing, as `convert.dbc_to_parquet` does). Do
   the same for an early month and a few years in between: if the columns change, the
   file type needs one era per layout. Note the first and last month on the FTP and whether
   large states are split (`a`, `b`, ...).
2. **Dictionary** (`dictionary.py`): add `BI = {**PARTITION, "COL": "description", ...}`
   with **every** column of the file, plus `BI_QUANTITY_COLS` and `BI_VALUE_COLS` (columns
   to cast; leave empty tuples if none). Cite the official layout document in a comment
   above the dict (DATASUS *Informe Técnico SIASUS* or the file type's layout PDF in
   `SIASUS/200801_/Doc`).
3. **Registry** (`catalog.py`): define the file type and add it to `REGISTRY`, keeping the
   order of issue #3 (it is the order of `-T all`, `--help` and the status tables):

    ```python
    BI = FileType("BI", "BPA Individualizado", (
        Era("bi", FTP_CURRENT_DIR, 200801, 999912, dictionary.BI,
            quantity_cols=dictionary.BI_QUANTITY_COLS, value_cols=dictionary.BI_VALUE_COLS),
    ))

    REGISTRY: dict[str, FileType] = {ft.code: ft for ft in (PA, BI)}
    ```

    - The era `key` is the lowercase code (`bi`). If there are several layouts, the latest
      keeps the plain code and older ones get a suffix, as PA does (`pa_legacy`), or a
      year range (`bi_2008_2013`) when there are more than two.
    - A type that stopped being published (AN, SAD) gets its real last month, not `999912`.
    - Set `parquet_ratio` (Parquet bytes / `.dbc` bytes) from the real fetch in step 6 if
      it differs much from the default 0.37.
    - Do not change `DEFAULT_TABLES`: PA stays the default.
4. **Tests** (`tests/test_registry.py`, no network):
    - a `test_<code>_registered` test checking the code, eras (`key`, `ftp_dir`, months),
      and that a few real file names parse (`BIAC2605.dbc`, a split one like `BISP2605b.dbc`)
      while names of other types do not;
    - a conversion test: write a tiny DBF with the type's real column names using the
      `make_dbf` fixture from `tests/conftest.py`, convert it with `convert.dbf_to_parquet`,
      publish it into a `Store` and check the `<code>` view casts the quantity/value columns;
    - keep `uv run pytest` green. The `FAKE` registry in `test_registry.py` may already
      use your code; it shadows the real entry only inside those tests, so leave it.
5. **Docs:**
    - a page `docs/tables/<code>.md` (copy the structure of `pa.md`): what the table is,
      what one row is, period covered, download size, every column with meaning and codes,
      joins to `procedimentos`, `cid10`, `ocupacoes`, `ufs`, overlap with PA
      (double-counting risk), known quirks and layout changes, and 2–3 example queries;
    - add it to the `Tables` section of `mkdocs.yml` `nav`;
    - in `docs/tables/index.md`, add a row to the *SIA file types* table and to the top
      table, and extend the join diagram if the table joins the lookups;
    - add the views to the table list in `docs/querying.md` and `README.md`;
    - check `uv run mkdocs build --strict` (needs `uv sync --group docs`).
6. **Check for real** with one small state-month, and paste the output in the PR:

    ```bash
    uv run datasus -d /tmp/check available -T bi -s AC -f 2026
    uv run datasus -d /tmp/check fetch -T bi -s AC -f 202605 -y
    uv run datasus -d /tmp/check query "SELECT uf, competencia, COUNT(*) FROM bi GROUP BY ALL"
    uv run datasus -d /tmp/check schema -T bi     # no column should lack a description
    uv run datasus -d /tmp/check status -T all
    ```

7. **PR** against `main` with `Closes #<sub-issue>` in the body, saying which state-month
   was checked.

## Data source

Data: Ministério da Saúde / DATASUS, SIA/SUS. Cite DATASUS when publishing results.

## CI/CD

- **CI** (`.github/workflows/ci.yml`): runs the test suite on Python 3.11–3.13 (Linux) and
  3.12 (Windows), and builds the sdist/wheel, on every pull request and push to `main`.
- **Docs** (`.github/workflows/docs.yml`): builds this site with `mkdocs build --strict` on
  every pull request; on pushes to `main` it deploys to GitHub Pages.
- `main` is protected: changes go through a pull request with one approving review.

## Docs

```bash
uv sync --group docs
uv run mkdocs serve      # live preview at http://127.0.0.1:8000
```
