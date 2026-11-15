import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from typer.testing import CliRunner

from intrepid_datasus import catalog as c, query
from intrepid_datasus.cli import app
from intrepid_datasus.store import LockedError, Store


def part(name, size=100):
    return c.group([c.parse_name(name, size)])[0]


def add(store: Store, p: c.Partition, rows: list[dict]):
    """Put a fake partition into the store the same way fetch does."""
    built = store.tmp / "b"
    built.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), built / (p.files[0].name[:-4] + ".parquet"))
    nbytes = store.publish(p, built)
    store.record(p, len(rows), nbytes)


@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path / "data")
    add(s, part("PASP2605a.dbc"), [
        {"PA_UFMUN": "355030", "PA_QTDAPR": "10", "PA_VALAPR": "5.50", "PA_PROC_ID": "0301010072"},
        {"PA_UFMUN": "355030", "PA_QTDAPR": "x", "PA_VALAPR": "1.00", "PA_PROC_ID": "0301010072"},
    ])
    add(s, part("PAAC2604.dbc"), [{"PA_UFMUN": "120040", "PA_QTDAPR": "3", "PA_VALAPR": "2", "PA_PROC_ID": "1"}])
    add(s, part("PAAC0312.dbc"), [{"PA_UFMUN": "120040", "PA_QTDAPR": "7", "PA_VALAPR": "9.9", "PA_CODPRO": "07"}])
    return s


def test_store_layout_and_manifest(store):
    assert (store.root / "pa" / "competencia=202605" / "uf=SP" / "PASP2605a.parquet").exists()
    assert (store.root / "pa_legacy" / "competencia=200312" / "uf=AC").is_dir()
    assert store.is_current(part("PASP2605a.dbc"))
    assert not store.is_current(part("PASP2605a.dbc", size=999))  # revised on the FTP
    # re-split into two files -> not current either
    resplit = c.group([c.parse_name("PASP2605a.dbc", 100), c.parse_name("PASP2605b.dbc", 5)])[0]
    assert not store.is_current(resplit)


def test_publish_replaces_old_files(store):
    p = c.group([c.parse_name("PASP2605a.dbc", 1), c.parse_name("PASP2605b.dbc", 1)])[0]
    built = store.tmp / "n"
    built.mkdir(parents=True)
    pq.write_table(pa.table({"PA_QTDAPR": ["1"]}), built / "PASP2605b.parquet")
    store.publish(p, built)
    names = sorted(f.name for f in store.partition_dir("SP", 202605).iterdir())
    assert names == ["PASP2605b.parquet"]


def test_views_cast_numbers_and_partitions(store):
    con = query.connect(store)
    assert {"pa", "pa_raw", "pa_legacy", "pa_legacy_raw", "ufs"} <= set(query.views(con))
    rows = con.execute(
        "SELECT uf, competencia, SUM(PA_QTDAPR), SUM(PA_VALAPR), COUNT(*) FROM pa GROUP BY ALL ORDER BY uf").fetchall()
    assert rows == [("AC", 202604, 3, 2.0, 1), ("SP", 202605, 10, 6.5, 2)]  # 'x' -> NULL, not an error
    assert con.execute("SELECT typeof(PA_QTDAPR), typeof(PA_PROC_ID) FROM pa LIMIT 1").fetchone() == ("BIGINT", "VARCHAR")
    assert con.execute("SELECT PA_CODPRO, PA_VALAPR FROM pa_legacy").fetchall() == [("07", 9.9)]
    assert con.execute("SELECT nome FROM ufs WHERE uf = 'SP'").fetchone() == ("São Paulo",)


def test_lock(store):
    with store.lock():
        with pytest.raises(LockedError):
            with store.lock():
                pass
    with store.lock():  # released
        pass


runner = CliRunner()


def run(store, *args):
    r = runner.invoke(app, ["--data-dir", str(store.root), *args])
    return r


def test_cli_status(store):
    r = run(store, "status")
    assert r.exit_code == 0, r.output
    assert "SP" in r.output and "AC" in r.output
    r = run(store, "status", "--by", "year", "-s", "AC")
    assert "2003" in r.output and "2026" in r.output and "SP" not in r.output


def test_cli_query_table_csv_and_file(store, tmp_path):
    r = run(store, "query", "SELECT uf, SUM(PA_QTDAPR) q FROM pa GROUP BY uf ORDER BY uf;")
    assert r.exit_code == 0, r.output
    assert "SP" in r.output and "10" in r.output
    r = run(store, "query", "--format", "csv", "SELECT uf, SUM(PA_QTDAPR) q FROM pa GROUP BY uf ORDER BY uf")
    assert r.output.splitlines() == ["uf,q", "AC,3", "SP,10"]
    out = tmp_path / "r.parquet"
    r = run(store, "query", "-o", str(out), "SELECT * FROM pa")
    assert r.exit_code == 0, r.output
    assert pq.read_table(out).num_rows == 3


def test_cli_query_error(store):
    r = run(store, "query", "SELECT nope FROM pa")
    assert r.exit_code == 1


def test_cli_schema(store):
    r = run(store, "schema")
    assert r.exit_code == 0 and "PA_QTDAPR" in r.output and "BIGINT" in r.output


def test_cli_remove(store):
    r = run(store, "remove", "-s", "SP", "-f", "2026", "-y")
    assert r.exit_code == 0, r.output
    assert "PA/SP/202605" not in store.manifest()
    assert not store.partition_dir("SP", 202605).exists()
    assert "PA/AC/202604" in store.manifest()


def test_cli_bad_args(store):
    assert run(store, "fetch", "-s", "XX", "-f", "2025").exit_code != 0
    assert run(store, "fetch", "-s", "SP").exit_code != 0  # --from required
    assert run(store, "fetch", "-s", "SP", "-f", "2025", "-t", "2024").exit_code != 0
