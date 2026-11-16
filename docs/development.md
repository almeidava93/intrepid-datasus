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
(`<CODE><UF><YY><MM>[part].dbc`, where `part` is a letter, `PASP2605a.dbc`, or `_<n>`,
`BISP2605_1.dbc`; matched per code so `AM` never claims `AMP` files and `AB`
never claims `ABO` files), which FTP folders to list (each folder is listed once, whatever
the number of file types), the `--table/-T` choices, the local layout, the manifest keys
(`<CODE>/<UF>/<YYYYMM>`, e.g. `PA/SP/202605`) and the views. Store, fetch and query code
contain no per-type logic; adding a file type should not need changes there.

`catalog.group` turns files into one partition per type, state and month. If the FTP has
both a whole file and split parts for the same month (BI SP/MG/RJ 2023-05 to 2024-02), it
keeps only the parts, which are the newer publication; keeping both would double the month.

The manifest used to key PA entries as `SP/202605`; `Store.manifest()` reads such keys as
PA, and the next write saves them in the new form.

## Adding a new SIA file type

Every file type sub-issue of #3 follows these steps. `BI` is used as the example.

1. **Check the FTP.** List the folder and look at **every** name starting with your code,
   not only the ones the current pattern accepts: BI splits states as `_1`, `_2`, `_3`
   (PA uses `a`, `b`, ...), and some months have a whole file *and* parts. If you find a
   new naming scheme, extend the regex in `FileType.__post_init__` and add tests. Note the
   first and last month, gaps, and the real total size (the sizes in issue #3 missed BI's
   `_N` files: 146.6 GB listed, 188 GB real). A name prefix also catches other types: files
   starting with `AM` include every AMP file *and* the AM files of Pará, Paraíba,
   Pernambuco, Piauí and Paraná (`AMPA2605.dbc`, `AMPE2605.dbc`), so split the listing
   with the full pattern (`<CODE><UF><YY><MM>`, a real UF), not with `startswith`.

   You don't need to download files to see their columns: a `.dbc` starts with the
   uncompressed DBF header (record count at bytes 4–8, then 32-byte field descriptors up
   to `0x0D`). Read the first 4 KB of a file with `ftp.transfercmd("RETR ...")`, close the
   data socket *and* the control connection (`ftp.abort()` hangs on this server), and
   parse it. Do this for one file per year (and the month where columns change): if the
   columns change, the file type needs one era per layout. For a small type, probe every
   month of one state, not just January: **Dec/2011** files of every type then published
   (AM, AQ, AR, AD, AN, BI) carry `AP_NATJUR` / `NAT_JUR` for that one month (empty in AN),
   which a January-only probe misses. Add it to the field-list test of your type. A column only *added* over time
   (BI's `NAT_JUR`) needs no new era; the views read with `union_by_name` and older months
   show `NULL`. The same trick gives row counts, e.g. to compare a whole file with its parts.
   The header does not show changes in *meaning*: also look at the main procedure codes and
   rows per APAC by year once the data is fetched (AR: new SIGTAP codes from May/2019 turned
   one row per APAC-month into one row per treatment, with the same columns; AD: CAPS mental
   health care, 60% of its rows, moved to RAAS in Jan/2013). Group the procedures by SIGTAP
   subgroup (`LEFT(AP_PRIPAL, 4)`, or `procedimentos.subgrupo`) per year. Also count
   `AP_PRIPAL IS NULL`: AD blanks it on APACs billed late with a code that was just retired.
   The header does not show a change of *content* in the type's own columns either: AB's
   `AB_` columns hold the old bariatric laudo until Mar/2013 and the new laudo, cut at the old
   field positions, from Apr/2013 (`AB_PROCAIH = '0407010173'` becomes `'30 30 NNSN'`). Look at
   the top values of every own column by year, and compare them with the field positions of
   the *parte variável* in the interface layout. Two types can also publish the same APACs:
   every AB row from 2014 is also in ABO (which has more states), so compare a new type with its
   siblings on `AP_AUTORIZ`/`AP_CMP` before saying what it covers.
   Columns are not always in the same order across types: in ATD, `AP_NATJUR` comes *after*
   the type's own columns (last), so copy the field list from the probe, not from another type.
   The Informe Técnico often lists columns without their codes; the facilities' import layout
   (*Layout da interface texto do APAC e do SIA*, Apr/2014, one *parte variável* per laudo:
   18 = dialysis, 19 = multiprofessional CKD follow-up) has the code lists.

    ```python
    import struct
    from intrepid_datasus import catalog

    def probe(name, folder=catalog.FTP_CURRENT_DIR):
        """(row count, [(column, DBF type, width), ...]) of a .dbc, from its first 8 KB."""
        ftp = catalog.connect()
        ftp.cwd(folder)
        ftp.voidcmd("TYPE I")
        sock = ftp.transfercmd("RETR " + name)
        buf = b""
        while len(buf) < 8192 and (chunk := sock.recv(8192 - len(buf))):
            buf += chunk
        sock.close()
        ftp.sock.close()  # not ftp.abort(): it hangs on this server
        nrec = struct.unpack("<I", buf[4:8])[0]
        fields, i = [], 32
        while buf[i] != 0x0D:
            f = buf[i:i + 32]
            fields.append((f[:11].split(b"\0")[0].decode().strip(), chr(f[11]), f[16]))
            i += 32
        return nrec, fields

    for yy in range(8, 27):
        n, cols = probe(f"AMSP{yy:02d}01.dbc")
        print(yy, n, len(cols))
    ```

   Some fields are numeric (`N`, e.g. APAC's `AP_VL_AP`); the converter reads every field as
   text anyway, so this needs no special handling. Field names can be padded with spaces
   instead of `\0` (PS: `'TIPPRE  '`): the converter strips them, so the column is `TIPPRE`.
   Look at the raw names (`repr`) when you probe. For a type with few files, probe **every**
   file (SAD: 1,088 headers in ~8 min with 6 threads) and group them by column set: SAD has
   three (43 columns, + `CO_INE` from Jan/2015, + `NAT_JUR` in Oct/2014 and from Jul/2016).
   Also sum the header row counts by year: SAD files go on until Oct/2018, but rows fall from
   1.55 M (2015) to 5 k (2017), so the real series ends in mid-2016. AB has a hole instead: files
   until Apr/2017, none for 2017-05 to 2024-12, then Jan–Jul/2025 again. Probing every month of one state also
   shows months with *no* file (PS: AC has 159 of 166 months, AP 150): there, a missing
   state-month means no production, not a failed download.
2. **Dictionary** (`dictionary.py`): add `BI = {**PARTITION, "COL": "description", ...}`
   with **every** column of the file, plus `BI_QUANTITY_COLS` and `BI_VALUE_COLS` (columns
   to cast; leave empty tuples if none). Cite the official layout document in a comment
   above the dict (DATASUS *Informe Técnico SIASUS* or the file type's layout PDF in
   `SIASUS/200801_/Doc`). The Informe Técnico is a PDF: `pdftotext -layout` (mingw/poppler)
   then `iconv -f latin1` gives text, but the layout tables come out with the description
   column shifted against the field names, so map descriptions by order.

   **APAC types** (AM, AQ, AR, AD, ATD, AN, AB, ABO, ACF, AMP) share 46 `AP_` columns.
   Build the dict with `dictionary.apac("AQ", {...own columns...})`: it adds `PARTITION` and
   `APAC_COMMON`, and entries in `own` override shared ones (use that for values specific
   to the type). Columns the type renames or lacks go in `without=(...)` (ABO renames
   `AP_TIPPRE`, `AP_TPATEN`, `AP_DTOCOR`, `AP_APACANT`). Use `APAC_QUANTITY_COLS` (empty)
   and `APAC_VALUE_COLS` (`AP_VL_AP`). If a shared description turns out wrong for every
   type, fix it in `APAC_COMMON`, not in one type's dict.

   **RAAS types** (PS, SAD) have no `AP_` columns and no APAC number. They share 40 columns
   (`CNES_EXEC`, `CNS_PAC`, `PA_PROC_ID`, `PA_QTDAPR`, ...): build the dict with
   `dictionary.raas("SAD", {...own columns...})`, which adds `PARTITION` and `RAAS_COMMON`
   (including `NAT_JUR`; drop it with `without=` if the type never has it). Use
   `RAAS_QUANTITY_COLS` (`PA_QTDPRO`, `PA_QTDAPR`) and `RAAS_VALUE_COLS` (empty: RAAS files
   have no value column). What a RAAS is: `docs/tables/raas.md`.
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
      and that a few real file names parse (`BIAC2605.dbc`, a split one like `BISP2605_1.dbc`)
      while names of other types do not;
    - a conversion test: write a tiny DBF with the type's real column names using the
      `make_dbf` fixture from `tests/conftest.py`, convert it with `convert.dbf_to_parquet`,
      publish it into a `Store` and check the `<code>` view casts the quantity/value columns;
    - a test that the dictionary has exactly the file's columns (plus `PARTITION`), so
      `datasus schema` never shows a column without a description;
    - keep `uv run pytest` green. The `FAKE` registry in `test_registry.py` may already
      use your code; it shadows the real entry only inside those tests, so leave it, and
      don't use its `registry` fixture in tests of the real entry. `tests/test_bi.py` is
      a complete example; `tests/test_am.py` is the one for APAC types (it also checks the
      shared `AP_` columns and that `AMPA2605.dbc` is AM, not AMP), and `tests/test_aq.py`
      shows a type whose files have three column sets (63, 64 and 74 columns) in one era;
      `tests/test_ar.py` is the shortest APAC example (two column sets), and `tests/test_atd.py`
      the one for a type that starts later than 2008 (it checks `era_for` before its first month);
      `tests/test_an.py` is the one for a discontinued type (real last month, one odd month
      with an extra column); `tests/test_ps.py` is the one for RAAS types (shared RAAS
      columns, a space-padded field name, a column present in one odd month and again later),
      and `tests/test_sad.py` the one for a discontinued RAAS type with three column sets;
      `tests/test_ab.py` is the one for an APAC type with a gap in its files and an extra column
      in Dec/2011 and again from Jul/2016.
5. **Docs:**
    - a page `docs/tables/<code>.md` (copy the structure of `bi.md`, or `am.md` for an APAC
      type: link to [APAC file types](tables/apac.md) for the `AP_` columns and only list
      what they hold in your type, then describe your own columns; mark the type as
      supported in the table at the top of `apac.md`): what the table is,
      what one row is, period covered, download size, every column with meaning and codes,
      joins to `procedimentos`, `cid10`, `ocupacoes`, `ufs`, overlap with PA
      (double-counting risk), known quirks and layout changes, and 2–3 example queries;
    - add it to the `Tables` section of `mkdocs.yml` `nav`;
    - in `docs/tables/index.md`, add a row to the *SIA file types* table and to the top
      table, and extend the join diagram if the table joins the lookups;
    - add the views to the table list in `docs/querying.md` and `README.md`;
    - for overlap with PA, fetch the same state-month of PA and compare row counts and
      `SUM`s against `pa WHERE PA_DOCORIG = ...` (BI equals `PA_DOCORIG = 'I'` exactly).
      For APAC types, join on `AP_AUTORIZ = PA_AUTORIZ` **and** `AP_CMP = PA_CMP` (same
      `competencia`, `uf`): a file can hold the same APAC twice, for the current month and
      billed late for an earlier one (AQ). Each APAC row should be one `PA_DOCORIG = 'P'`
      row, and `AP_VL_AP` the sum of `PA_VALAPR` over its `P` and `S` rows (AM: exact, and
      AM = `P` rows with `PA_TPFIN = '02'`; AQ: exact, and AQ = `P` rows with `PA_PROC_ID`
      from `0304020000` to `0304089999`; AR: exact, `P` rows with `PA_PROC_ID LIKE '030401%'`,
      checked on a month before and after its 2019 procedure change; AD: exact, but no `pa`
      column picks its rows out, and some APACs, such as glaucoma follow-up, are not in AD
      either; ATD: exact, and ATD = `P` rows with `PA_PROC_ID LIKE '0305%'`, from Aug/2014;
      AN: exact, the same selection until May/2014, checked in 2008, 2011 and 2014).
      RAAS types have no authorisation number: their rows are `PA_DOCORIG = 'B'` (PS) or
      `'A'` (SAD); compare `COUNT(*)` and `SUM(PA_QTDAPR)` grouped by facility
      (`CNES_EXEC = PA_CODUNI`), care month (`DT_ATEND = PA_CMP`) and `PA_PROC_ID`
      (PS: see `docs/tables/ps.md`).
      For a type that replaced another (ATD after AN), compare the months around the switch
      with `pa` too: Jun–Jul/2014 dialysis is in `pa` but mostly in neither AN nor ATD.
      Check whether some other column of `pa` (`PA_TPFIN`, the procedure group) picks out
      exactly your type's rows, and list by procedure subgroup the `P` rows that are in no
      APAC table yet;
    - for APAC types, check `AP_CNSPCN` by month and state (`NULL` and `{{{{{{{{{{{{{{{`)
      before writing anything about patients: from Nov/2025 it is missing on most AR rows
      (95% in Aug/2026), on 2–22% of AQ rows (SC, 2026), on 67% of AD rows in Aug/2026
      (rising since Apr/2024), on 96% of ATD rows in Aug/2026 (2% in 2024, 15% in Mar/2026,
      then a jump from May/2026), on none in AM or AN (2008–2014);
    - don't trust a shared column to behave as in another type: `AP_CIDPRI` is always
      `0000` in ATD but filled in AN, and `AP_TPATEN` is a different fixed code in each type.
      SAD's `TPUPS` holds the provider type (`pa`'s `PA_TIPPRE`), not the facility type it holds
      in PS: compare a shared column with its `pa` counterpart on the overlap months.
      Count the values of each shared column once on the full history;
    - check `uv run mkdocs build --strict` (needs `uv sync --group docs`).
6. **Check for real** with one small state-month, and paste the output in the PR:

    ```bash
    uv run datasus -d /tmp/check available -T bi -s AC -f 2026
    uv run datasus -d /tmp/check fetch -T bi -s AC -f 202605 -y
    uv run datasus -d /tmp/check query "SELECT uf, competencia, COUNT(*) FROM bi GROUP BY ALL"
    uv run datasus -d /tmp/check schema -T bi     # no column should lack a description
    uv run datasus -d /tmp/check status -T all
    ```

    For a big type, also convert one large file (the biggest SP part) and record download
    and conversion time, peak RAM, temporary DBF size and the Parquet ratio. BI: a 172 MB
    part with 4.7 M rows took 1.9 GB of RAM and a 1.2 GB temporary DBF. AM: the largest
    file (82 MB, 1.37 M rows) took 28 s and about 1.2 GB of RAM; AQ's (10.5 MB, 102 k
    rows), 7 s and 0.4 GB. For a type with many tiny files the Parquet ratio is high,
    because each file has about 20 KB of overhead (AR: 0.81 over its 5,491 files; SAD: 0.89,
    files of ~49 KB; AB: **1.2**, files of ~25 KB, so Parquet is larger than the `.dbc`), and
    small files can take up to 30 s each on the FTP (AR, every month: about 35 min). To fetch
    a whole history faster, run two or three fetches of different year ranges into separate
    stores (`-d`) at once, then move the `data/<key>/competencia=*` folders into one store and
    merge the `manifest.json` dicts (AD: 6,046 files in 26 min this way). The temporary DBF is
    (record length × rows): the record length is 1 + the sum of the field widths from the
    header probe.

7. **PR** against `main` (or the previous sub-issue's branch while its PR is open) with `Closes #<sub-issue>` in the body, saying which state-month
   was checked.
8. **Clean up.** Once the PR is open and the numbers are in the docs, delete every data
   store you created for the checks (the `-d` folders of steps 5 and 6, merged history
   stores, downloaded files): they are only test data, disks are small, and the sessions of
   issue #3 run one after another. Keep the scripts and the numbers in your notes, not the data.

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
