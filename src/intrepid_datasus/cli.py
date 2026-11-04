"""datasus — download and query SIA/SUS outpatient production (Produção Ambulatorial)."""
from __future__ import annotations

import re
import shutil
import sys
import time
from collections import defaultdict
from decimal import Decimal
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.table import Table

from . import catalog, dictionary, query as q
from .catalog import ERAS, LEGACY, CURRENT, Partition
from .store import LockedError, Store, default_root

app = typer.Typer(
    help=__doc__,
    no_args_is_help=True,
    add_completion=False,
    rich_markup_mode="rich",
    context_settings={"help_option_names": ["-h", "--help"]},
)
console = Console()
err = Console(stderr=True)

# Parquet is ~37% of the .dbc download size (measured on May/2026).
PARQUET_RATIO = 0.37

StatesOpt = Annotated[str, typer.Option(
    "--states", "-s",
    help="States: 'all', codes like 'SP,RJ', or a region (Norte, Nordeste, Sudeste, Sul, Centro-Oeste).",
)]
FromOpt = Annotated[Optional[str], typer.Option("--from", "-f", help="First month: YYYYMM or YYYY.")]
ToOpt = Annotated[Optional[str], typer.Option("--to", "-t", help="Last month: YYYYMM or YYYY (default: same as --from).")]


# ------------------------------------------------------------------ helpers
def _store(ctx: typer.Context) -> Store:
    return ctx.obj


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1000 or unit == "TB":
            return f"{n:,.0f} {unit}" if unit in ("B", "KB") else f"{n:,.1f} {unit}"
        n /= 1000
    return str(n)


def fmt_comp(c: int) -> str:
    return f"{c // 100}-{c % 100:02d}"


def _range(start: str | None, end: str | None, *, required: bool) -> tuple[int, int]:
    try:
        if start is None:
            if required:
                raise typer.BadParameter("give a month or year with --from (e.g. --from 2025 or --from 202605)")
            return LEGACY.first, CURRENT.last
        s = catalog.parse_period(start, is_end=False)
        e = catalog.parse_period(end, is_end=True) if end else catalog.parse_period(start, is_end=True)
    except ValueError as ex:
        raise typer.BadParameter(str(ex)) from None
    if e < s:
        raise typer.BadParameter("--to is before --from")
    return s, e


def _states(value: str) -> set[str] | None:
    try:
        return catalog.parse_states(value)
    except ValueError as ex:
        raise typer.BadParameter(str(ex)) from None


def _eras_for(start: int, end: int) -> tuple[catalog.Era, ...]:
    return tuple(e for e in ERAS if start <= e.last and end >= e.first)


def _remote(states: set[str] | None, start: int, end: int) -> list[Partition]:
    with console.status("Listing files on ftp.datasus.gov.br ..."):
        files = catalog.list_remote(_eras_for(start, end))
    return catalog.select(catalog.group(files), states, start, end)


@app.callback()
def main(
    ctx: typer.Context,
    data_dir: Annotated[Optional[Path], typer.Option(
        "--data-dir", "-d", envvar="DATASUS_DATA_DIR",
        help="Where data is stored (default: ./data, or $DATASUS_DATA_DIR).",
    )] = None,
):
    # Windows consoles with legacy code pages can't print characters like ✓; don't crash on them.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            # files and pipes get UTF-8 (so accents survive `> out.csv`); terminals keep their encoding
            stream.reconfigure(errors="replace", **({} if stream.isatty() else {"encoding": "utf-8"}))
    ctx.obj = Store(data_dir or default_root())


# ---------------------------------------------------------------- available
@app.command()
def available(
    states: StatesOpt = "all",
    start: FromOpt = None,
    end: ToOpt = None,
    by: Annotated[str, typer.Option(help="Group rows by 'state' or 'year'.")] = "state",
):
    """Show what DATASUS has on the FTP (nothing is downloaded)."""
    s, e = _range(start, end, required=False)
    parts = _remote(_states(states), s, e)
    if not parts:
        console.print("No files match.")
        return
    key = (lambda p: p.uf) if by == "state" else (lambda p: p.competencia // 100)
    groups: dict = defaultdict(list)
    for p in parts:
        groups[key(p)].append(p)

    t = Table(title="Available on DATASUS FTP", show_footer=True)
    t.add_column("State" if by == "state" else "Year", footer="Total")
    t.add_column("Months", justify="right", footer=f"{len({p.competencia for p in parts}):,}")
    t.add_column("From")
    t.add_column("To")
    t.add_column("Files", justify="right", footer=f"{sum(len(p.files) for p in parts):,}")
    t.add_column("Download", justify="right", footer=human(sum(p.size for p in parts)))
    for k in sorted(groups):
        g = groups[k]
        comps = sorted({p.competencia for p in g})
        t.add_row(str(k), f"{len(comps):,}", fmt_comp(comps[0]), fmt_comp(comps[-1]),
                  f"{sum(len(p.files) for p in g):,}", human(sum(p.size for p in g)))
    console.print(t)
    console.print(f"Estimated local size as Parquet: ~{human(sum(p.size for p in parts) * PARQUET_RATIO)}")


# -------------------------------------------------------------------- fetch
@app.command()
def fetch(
    ctx: typer.Context,
    states: StatesOpt = "all",
    start: FromOpt = None,
    end: ToOpt = None,
    workers: Annotated[int, typer.Option("--workers", "-w", min=1, max=8,
        help="State-months processed in parallel. Each needs a few GB of temporary disk.")] = 3,
    force: Annotated[bool, typer.Option(help="Re-download even if the local copy is current.")] = False,
    keep_dbc: Annotated[bool, typer.Option(help="Keep the raw .dbc files in <data-dir>/dbc.")] = False,
    dry_run: Annotated[bool, typer.Option("--dry-run", "-n", help="Show the plan and exit.")] = False,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Don't ask for confirmation.")] = False,
):
    """Download state-months from DATASUS and convert them to Parquet.

    Re-running is safe: up-to-date state-months are skipped, and ones DATASUS has
    revised (file sizes changed, or re-split into parts) are rebuilt.

    Examples:  datasus fetch -s SP -f 2025      datasus fetch -s all -f 202401 -t 202406
    """
    store = _store(ctx)
    s, e = _range(start, end, required=True)
    parts = _remote(_states(states), s, e)
    if not parts:
        console.print("Nothing on the FTP matches those states and months.")
        raise typer.Exit()

    todo = parts if force else [p for p in parts if not store.is_current(p)]
    download = sum(p.size for p in todo)
    console.print(
        f"[bold]{len(parts):,}[/] state-months match: {len(parts) - len(todo):,} already up to date, "
        f"[bold]{len(todo):,}[/] to fetch ({sum(len(p.files) for p in todo):,} files, {human(download)} download, "
        f"~{human(download * PARQUET_RATIO)} on disk)."
    )
    if not todo:
        raise typer.Exit()

    store.root.mkdir(parents=True, exist_ok=True)
    free = shutil.disk_usage(store.root).free
    need = download * PARQUET_RATIO + min(workers, len(todo)) * 5e9  # + temporary .dbf files
    if free < need:
        err.print(f"[yellow]Warning:[/] {human(free)} free in {store.root.resolve()}, "
                  f"this needs roughly {human(need)} (including temporary files).")
    if dry_run:
        for p in todo[:50]:
            console.print(f"  {p.uf} {fmt_comp(p.competencia)}  {', '.join(f.name for f in p.files)}  {human(p.size)}")
        if len(todo) > 50:
            console.print(f"  ... and {len(todo) - 50:,} more")
        raise typer.Exit()
    if not yes and not typer.confirm("Proceed?", default=True):
        raise typer.Abort()

    from .fetch import build_partition

    failed: list[tuple[Partition, str]] = []
    done_bytes = 0
    t0 = time.time()
    try:
        with store.lock():
            shutil.rmtree(store.tmp, ignore_errors=True)  # leftovers from interrupted runs
            # biggest first keeps the workers busy until the end
            queue = sorted(todo, key=lambda p: -p.size)
            with ProcessPoolExecutor(max_workers=workers) as pool:
                running = {}
                try:
                    while queue or running:
                        while queue and len(running) < workers:
                            p = queue.pop(0)
                            running[pool.submit(build_partition, p, str(store.root), keep_dbc)] = p
                        finished, _ = wait(running, return_when=FIRST_COMPLETED)
                        for fut in finished:
                            p = running.pop(fut)
                            n_done = len(todo) - len(queue) - len(running)
                            try:
                                r = fut.result()
                            except Exception as ex:
                                failed.append((p, str(ex)))
                                err.print(f"[red]✗[/] {p.uf} {fmt_comp(p.competencia)}: {ex}")
                                continue
                            store.record(p, r.rows, r.nbytes)
                            done_bytes += p.size
                            rate = done_bytes / max(time.time() - t0, 1)
                            left = (download - done_bytes) / rate if rate else 0
                            console.print(
                                f"[green]✓[/] [{n_done}/{len(todo)}] {p.uf} {fmt_comp(p.competencia)}: "
                                f"{r.rows:,} rows, {human(r.nbytes)} ({r.seconds:.0f}s)"
                                + (f"  — ~{left / 60:.0f} min left" if queue or running else "")
                            )
                except KeyboardInterrupt:
                    err.print("\n[yellow]Interrupted.[/] Finished state-months are saved; run the same command to continue.")
                    pool.shutdown(wait=False, cancel_futures=True)
                    raise typer.Exit(130)
    except LockedError as ex:
        err.print(f"[red]{ex}[/]")
        raise typer.Exit(1)

    console.print(f"Done in {(time.time() - t0) / 60:.1f} min: {len(todo) - len(failed):,} fetched, {len(failed):,} failed.")
    if failed:
        err.print("Run the same command again to retry the failures.")
        raise typer.Exit(1)


# ------------------------------------------------------------------- status
@app.command()
def status(
    ctx: typer.Context,
    states: StatesOpt = "all",
    start: FromOpt = None,
    end: ToOpt = None,
    by: Annotated[str, typer.Option(help="Group rows by 'state', 'year' or 'month'.")] = "state",
):
    """Show what is stored locally."""
    store = _store(ctx)
    st = _states(states)
    s, e = _range(start, end, required=False)
    entries = [v for v in store.manifest().values()
               if s <= v["competencia"] <= e and (st is None or v["uf"] in st)]
    if not entries:
        console.print(f"No data in {store.root.resolve()} for that selection. Try: datasus fetch --help")
        return

    keyf = {"state": lambda v: v["uf"], "year": lambda v: v["competencia"] // 100,
            "month": lambda v: v["competencia"]}.get(by)
    if keyf is None:
        raise typer.BadParameter("--by must be state, year or month")
    groups: dict = defaultdict(list)
    for v in entries:
        groups[keyf(v)].append(v)

    t = Table(title="Local data", caption=str(store.root.resolve()), show_footer=True)
    t.add_column({"state": "State", "year": "Year", "month": "Month"}[by], footer="Total")
    if by == "month":
        t.add_column("States", justify="right")
    else:
        t.add_column("Months", justify="right")
        t.add_column("From")
        t.add_column("To")
        t.add_column("Gaps", justify="right", footer="")
    t.add_column("Rows", justify="right", footer=f"{sum(v['rows'] for v in entries):,}")
    t.add_column("Size", justify="right", footer=human(sum(v["bytes"] for v in entries)))
    for k in sorted(groups):
        g = groups[k]
        rows, size = f"{sum(v['rows'] for v in g):,}", human(sum(v["bytes"] for v in g))
        if by == "month":
            t.add_row(fmt_comp(k), str(len({v["uf"] for v in g})), rows, size)
            continue
        comps = sorted({v["competencia"] for v in g})
        gaps = 0
        if by == "state":
            expected = [c for c in catalog.months(comps[0], comps[-1])]
            gaps = len(expected) - len(comps)
        t.add_row(str(k), str(len(comps)), fmt_comp(comps[0]), fmt_comp(comps[-1]),
                  str(gaps) if by == "state" else "", rows, size)
    console.print(t)
    if by == "state":
        console.print("[dim]Gaps = months missing between From and To for that state.[/]")


# ------------------------------------------------------------------- schema
@app.command()
def schema(
    ctx: typer.Context,
    legacy: Annotated[bool, typer.Option("--legacy", help="Show the 1994-2007 layout (view pa_legacy).")] = False,
):
    """List the columns of the 'pa' view (or 'pa_legacy') with short descriptions."""
    era = LEGACY if legacy else CURRENT
    desc = dictionary.LEGACY if legacy else dictionary.CURRENT
    con = q.connect(_store(ctx))
    if era.view in q.views(con):
        cols = [(r[0], r[1]) for r in con.execute(f"DESCRIBE {era.view}").fetchall()]
    else:
        console.print(f"[dim]No local data for {era.view} yet; showing the documented layout.[/]")
        cols = [(c, "") for c in desc]
    t = Table(title=f"View {era.view}")
    t.add_column("Column", style="bold")
    t.add_column("Type")
    t.add_column("Description")
    for name, typ in cols:
        t.add_row(name, typ, desc.get(name, ""))
    console.print(t)


# -------------------------------------------------------------------- query
def _print_result(con, sql: str, max_rows: int) -> None:
    t0 = time.time()
    cur = con.execute(sql)
    if cur.description is None:
        console.print(f"[dim]OK ({time.time() - t0:.2f}s)[/]")
        return
    names = [d[0] for d in cur.description]
    rows = cur.fetchmany(max_rows + 1)
    more = len(rows) > max_rows
    plain = [bool(_ID_LIKE.search(n)) for n in names]
    t = Table(show_lines=False)
    for i, n in enumerate(names):
        numeric = bool(rows) and isinstance(rows[0][i], (int, float, Decimal)) and not isinstance(rows[0][i], bool)
        t.add_column(n, justify="right" if numeric and not plain[i] else "left")
    for r in rows[:max_rows]:
        t.add_row(*[_cell(v, p) for v, p in zip(r, plain)])
    console.print(t)
    note = f"first {max_rows} rows shown (use --max-rows or -o FILE for more)" if more else f"{len(rows)} rows"
    console.print(f"[dim]{note} — {time.time() - t0:.2f}s[/]")


# Columns that hold codes or months: print them as-is, without thousands separators.
_ID_LIKE = re.compile(r"competencia|versao|^ano|year|^mes|month|cod|_id$|^id|cnes|ibge|mun|cid|cbo|uf", re.I)


def _cell(v, plain: bool = False) -> str:
    if v is None:
        return "[dim]NULL[/]"
    if plain or isinstance(v, bool):
        return str(v)
    if isinstance(v, (float, Decimal)):
        return f"{v:,.2f}"
    if isinstance(v, int):
        return f"{v:,}"
    return str(v)


def _stream(con, sql: str, fmt: str) -> None:
    """Print a full result as CSV or JSON lines, batch by batch (keeps integer types)."""
    import csv
    import json

    reader = con.sql(sql).to_arrow_reader(100_000)
    writer = csv.writer(sys.stdout, lineterminator="\n")
    if fmt == "csv":
        writer.writerow(reader.schema.names)
    for batch in reader:
        names = batch.schema.names
        for row in batch.to_pylist():
            if fmt == "csv":
                writer.writerow(["" if row[n] is None else row[n] for n in names])
            else:
                sys.stdout.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    sys.stdout.flush()


@app.command("query")
def query_cmd(
    ctx: typer.Context,
    sql: Annotated[Optional[str], typer.Argument(help="SQL to run. Tables: pa, pa_legacy, pa_raw, pa_legacy_raw, ufs.")] = None,
    file: Annotated[Optional[Path], typer.Option("--file", "-F", help="Read the SQL from a file.")] = None,
    output: Annotated[Optional[Path], typer.Option("--output", "-o", help="Write the full result to a file (.csv, .parquet, .json).")] = None,
    fmt: Annotated[Optional[str], typer.Option("--format", help="table (default), csv or json on screen; or force the file format.")] = None,
    max_rows: Annotated[int, typer.Option(help="Rows shown on screen.")] = 50,
    memory_limit: Annotated[Optional[str], typer.Option(help="DuckDB memory limit, e.g. 8GB.")] = None,
):
    """Run SQL (DuckDB dialect) on the local data.

    Example:
      datasus query "SELECT uf, SUM(PA_QTDAPR) qtd FROM pa WHERE competencia = 202605 GROUP BY uf ORDER BY qtd DESC"
    """
    if file:
        sql = file.read_text(encoding="utf-8")
    if not sql:
        raise typer.BadParameter("give SQL as an argument or with --file")
    sql = q.clean(sql)
    con = q.connect(_store(ctx), memory_limit=memory_limit)
    try:
        if output:
            kind = fmt or output.suffix.lstrip(".").lower()
            if kind not in ("csv", "parquet", "json"):
                raise typer.BadParameter("output must end in .csv, .parquet or .json (or pass --format)")
            t0 = time.time()
            q.copy_to(con, sql, output, kind)
            console.print(f"Wrote {output} ({human(output.stat().st_size)}, {time.time() - t0:.1f}s)")
        elif fmt in ("csv", "json"):
            _stream(con, sql, fmt)
        else:
            _print_result(con, sql, max_rows)
    except Exception as ex:
        if isinstance(ex, (typer.Exit, typer.BadParameter)):
            raise
        err.print(f"[red]{type(ex).__name__}:[/] {ex}")
        if "pa" in str(ex) and "does not exist" in str(ex):
            err.print("No local data for that table yet. Fetch some first: datasus fetch --help")
        raise typer.Exit(1)


# -------------------------------------------------------------------- shell
@app.command()
def shell(
    ctx: typer.Context,
    max_rows: Annotated[int, typer.Option(help="Rows shown per result.")] = 50,
    memory_limit: Annotated[Optional[str], typer.Option(help="DuckDB memory limit, e.g. 8GB.")] = None,
):
    """Interactive SQL prompt. End statements with ';'. Commands: .tables  .schema <table>  .quit"""
    con = q.connect(_store(ctx), memory_limit=memory_limit)
    console.print("Tables: " + ", ".join(q.views(con)) + "\nEnd each statement with ';'. Type .quit to exit.")
    buf: list[str] = []
    while True:
        try:
            line = input("datasus> " if not buf else "   ...> ")
        except (EOFError, KeyboardInterrupt):
            console.print()
            return
        stripped = line.strip()
        if not buf and stripped.startswith("."):
            cmd, _, arg = stripped.partition(" ")
            if cmd in (".quit", ".exit", ".q"):
                return
            if cmd == ".tables":
                console.print(", ".join(q.views(con)))
            elif cmd == ".schema" and arg:
                _safe(lambda: _print_result(con, f"DESCRIBE {arg.strip()}", 500))
            else:
                console.print(".tables | .schema <table> | .quit")
            continue
        buf.append(line)
        if stripped.endswith(";"):
            sql = q.clean("\n".join(buf))
            buf.clear()
            if sql:
                _safe(lambda: _print_result(con, sql, max_rows))


def _safe(fn) -> None:
    try:
        fn()
    except KeyboardInterrupt:
        err.print("[yellow]cancelled[/]")
    except Exception as ex:
        err.print(f"[red]{type(ex).__name__}:[/] {ex}")


# ------------------------------------------------------------------- remove
@app.command()
def remove(
    ctx: typer.Context,
    states: StatesOpt = "all",
    start: FromOpt = None,
    end: ToOpt = None,
    yes: Annotated[bool, typer.Option("--yes", "-y", help="Don't ask for confirmation.")] = False,
):
    """Delete local state-months (nothing on DATASUS is touched)."""
    store = _store(ctx)
    st = _states(states)
    s, e = _range(start, end, required=True)
    keys = [k for k, v in store.manifest().items()
            if s <= v["competencia"] <= e and (st is None or v["uf"] in st)]
    if not keys:
        console.print("Nothing stored locally matches.")
        return
    size = sum(store.manifest()[k]["bytes"] for k in keys)
    console.print(f"{len(keys):,} state-months, {human(size)}.")
    if not yes and not typer.confirm("Delete them?", default=False):
        raise typer.Abort()
    try:
        with store.lock():
            freed = store.remove(keys)
    except LockedError as ex:
        err.print(f"[red]{ex}[/]")
        raise typer.Exit(1)
    console.print(f"Removed {len(keys):,} state-months ({human(freed)}).")


# ------------------------------------------------------------------- sigtap
sigtap_app = typer.Typer(
    help="SIGTAP procedure table: names, groups, prices and rules for every procedure code.",
    no_args_is_help=True,
)
app.add_typer(sigtap_app, name="sigtap")


def _sigtap_versions(start: str | None, end: str | None, yearly: bool):
    from . import sigtap

    try:
        s = catalog.parse_period(start, is_end=False) if start else None
        e = catalog.parse_period(end, is_end=True) if end else (catalog.parse_period(start, is_end=True) if start and not yearly else None)
    except ValueError as ex:
        raise typer.BadParameter(str(ex)) from None
    with console.status("Listing SIGTAP versions on ftp2.datasus.gov.br ..."):
        versions = sigtap.list_versions()
    if not versions:
        err.print("[red]No SIGTAP versions found on the FTP.[/]")
        raise typer.Exit(1)
    if s is None and e is None:
        return versions, [versions[-1]]  # default: the latest version only
    return versions, sigtap.pick(versions, s, e, yearly)


@sigtap_app.command("fetch")
def sigtap_fetch(
    ctx: typer.Context,
    start: FromOpt = None,
    end: ToOpt = None,
    yearly: Annotated[bool, typer.Option(help="Only the last version of each year in the range.")] = False,
    force: Annotated[bool, typer.Option(help="Re-download versions already stored.")] = False,
):
    """Download SIGTAP versions (about 2 MB each). Default: the latest version.

    Codes are retired over time, so to name every code in older data fetch past
    versions too, e.g.:  datasus sigtap fetch --from 2008 --yearly
    """
    from .sigtap import SigtapStore

    st = SigtapStore(_store(ctx).root)
    _, chosen = _sigtap_versions(start, end, yearly)
    todo = [v for v in chosen if force or not st.has(v)]
    console.print(f"{len(chosen)} version(s) selected, {len(chosen) - len(todo)} already stored, "
                  f"{len(todo)} to fetch ({human(sum(v.size for v in todo))}).")
    failed = 0
    for v in todo:
        try:
            counts = st.fetch(v)
        except Exception as ex:
            failed += 1
            err.print(f"[red]✗[/] {fmt_comp(v.competencia)}: {ex}")
            continue
        console.print(f"[green]✓[/] {fmt_comp(v.competencia)}: {counts.get('tb_procedimento', 0):,} procedures, "
                      f"{len(counts)} tables")
    if failed:
        raise typer.Exit(1)


@sigtap_app.command("available")
def sigtap_available(
    ctx: typer.Context,
    start: FromOpt = None,
    end: ToOpt = None,
):
    """List SIGTAP versions on the FTP and which ones are stored locally."""
    from .sigtap import SigtapStore

    st = SigtapStore(_store(ctx).root)
    versions, _ = _sigtap_versions(None, None, False)
    s = catalog.parse_period(start, is_end=False) if start else 0
    e = catalog.parse_period(end, is_end=True) if end else 999912
    stored = st.index()
    by_year: dict[int, list] = defaultdict(list)
    for v in versions:
        if s <= v.competencia <= e:
            by_year[v.competencia // 100].append(v)
    t = Table(title="SIGTAP versions")
    for c in ("Year", "Versions", "From", "To", "Stored locally"):
        t.add_column(c)
    for y in sorted(by_year):
        vs = by_year[y]
        have = [fmt_comp(v.competencia) for v in vs if str(v.competencia) in stored]
        t.add_row(str(y), str(len(vs)), fmt_comp(vs[0].competencia), fmt_comp(vs[-1].competencia),
                  ", ".join(have) if have else "-")
    console.print(t)


@sigtap_app.command("search")
def sigtap_search(
    ctx: typer.Context,
    text: Annotated[str, typer.Argument(help="Words in the name (accents and case ignored) or a code prefix, e.g. 'teleconsulta' or 030101.")],
    max_rows: Annotated[int, typer.Option(help="Rows shown.")] = 50,
):
    """Find procedures by name or code."""
    con = q.connect(_store(ctx))
    if "procedimentos" not in q.views(con):
        err.print("No SIGTAP data yet. Run: datasus sigtap fetch")
        raise typer.Exit(1)
    if text.isdigit():
        where = f"codigo LIKE '{text}%'"
    else:
        words = [w.replace("'", "''") for w in text.split()]
        where = " AND ".join(f"strip_accents(lower(nome)) LIKE '%' || strip_accents(lower('{w}')) || '%'" for w in words)
    _print_result(con, f"""SELECT codigo, nome, complexidade, financiamento, valor_ambulatorial,
        primeira_versao, ultima_versao, ativo FROM procedimentos WHERE {where} ORDER BY codigo""", max_rows)


if __name__ == "__main__":
    app()
