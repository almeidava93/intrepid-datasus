"""The SIA file-type registry, filename parsing for 2- and 3-letter codes, and --table."""
import json

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from typer.testing import CliRunner

from intrepid_datasus import catalog as c, query
from intrepid_datasus.cli import app
from intrepid_datasus.store import Store

CUR, OLD = c.FTP_CURRENT_DIR, c.FTP_LEGACY_DIR


def ft(code, first=200801, last=999912, **kw):
    return c.FileType(code, f"test {code}", (c.Era(code.lower(), CUR, first, last, {"X": "a column"}, **kw),))


# Codes whose prefixes collide (AM/AMP, AB/ABO, AD/ATD) or look like states (AM, PA).
FAKE = {code: ft(code) for code in ("BI", "AM", "AMP", "AB", "ABO", "AD", "ATD")}


@pytest.fixture
def registry(monkeypatch):
    """Register fake file types next to PA for the duration of a test."""
    for code, t in FAKE.items():
        monkeypatch.setitem(c.REGISTRY, code, t)
    return c.REGISTRY


def test_pa_is_registered_with_its_two_eras():
    assert c.REGISTRY["PA"] is c.PA and c.DEFAULT_TABLES == ("PA",)
    assert [(e.key, e.view, e.ftp_dir, e.first, e.last) for e in c.PA.eras] == [
        ("pa_legacy", "pa_legacy", OLD, 199407, 200712), ("pa", "pa", CUR, 200801, 999912)]
    assert c.PA.views == ["pa_legacy", "pa"] and (c.PA.first, c.PA.last) == (199407, 999912)
    assert "PA_QTDAPR" in c.PA.eras[1].quantity_cols and "PA_VALAPR" in c.PA.eras[0].value_cols
    assert "PA_PROC_ID" in c.PA.eras[1].dictionary and "PA_CODPRO" in c.PA.eras[0].dictionary
    with pytest.raises(ValueError):
        c.PA.era_for(199406)


@pytest.mark.parametrize("code", ["P", "PAXX", "pa", "P1"])
def test_bad_codes_are_rejected(code):
    with pytest.raises(ValueError):
        c.FileType(code, "x", ())


@pytest.mark.parametrize("name,table,uf,comp,part", [
    ("BIAC2605.dbc", "BI", "AC", 202605, ""),
    ("AMAM2605.dbc", "AM", "AM", 202605, ""),      # code equals a state
    ("AMPSP2605.dbc", "AMP", "SP", 202605, ""),    # AM + 'PS...' must not match
    ("AMPPA1603b.DBC", "AMP", "PA", 201603, "b"),
    ("ABOAC1401.dbc", "ABO", "AC", 201401, ""),    # AB + 'OA...' must not match
    ("ABRJ0801.dbc", "AB", "RJ", 200801, ""),
    ("ATDMG2512a.dbc", "ATD", "MG", 202512, "a"),
    ("ADPA2605.dbc", "AD", "PA", 202605, ""),
    ("PASP2605a.dbc", "PA", "SP", 202605, "a"),
])
def test_parse_name_any_type(registry, name, table, uf, comp, part):
    rf = c.parse_name(name, 7)
    assert (rf.table, rf.uf, rf.competencia, rf.part, rf.size) == (table, uf, comp, part, 7)
    # and no other registered type claims it
    assert [t.code for t in registry.values() if t.parse(name)] == [table]


@pytest.mark.parametrize("code,name", [
    ("AM", "AMPSP2605.dbc"), ("AB", "ABOSP2605.dbc"), ("ABO", "ABSP2605.dbc"),
    ("BI", "BIXX2605.dbc"), ("BI", "BISP2613.dbc"), ("ATD", "ATDSP2605.dbf"), ("PA", "BIAC2605.dbc"),
])
def test_type_rejects_other_names(registry, code, name):
    assert registry[code].parse(name) is None


def test_group_keeps_tables_apart(registry):
    files = [c.parse_name(n, 1) for n in ("PAAC2605.dbc", "BIAC2605.dbc", "BIAC2605b.dbc")]
    parts = c.group(files)
    assert [(p.key, len(p.files)) for p in parts] == [("BI/AC/202605", 2), ("PA/AC/202605", 1)]
    assert parts[0].era.key == "bi" and parts[1].era.key == "pa"
    assert [p.table for p in c.select(parts, None, 0, 999912, {"PA"})] == ["PA"]


def test_wanted_dirs_and_listing_match(registry):
    assert c.wanted_dirs([c.PA], 2025_01, 2025_12) == {CUR: [c.PA.eras[1]]}
    assert set(c.wanted_dirs([c.PA], 2007_01, 2008_12)) == {OLD, CUR}
    assert c.wanted_dirs([registry["BI"]], 1999_01, 2005_12) == {}

    listing = [("PAAC2605.dbc", 1), ("PAAC2605.DBC", 1), ("BIAC2605.dbc", 2), ("AMPAC2605.dbc", 3),
               ("PAAC0712.dbc", 4), ("README.txt", 5), ("CDAC2605.dbc", 6)]
    got = c.match_listing(listing, [c.PA, registry["AMP"]], [c.PA.eras[1], registry["AMP"].eras[0]])
    # PA 2007 is a stray in the 2008+ folder; BI wasn't asked for; the duplicate .DBC is dropped
    assert sorted((f.table, f.name) for f in got) == [("AMP", "AMPAC2605.dbc"), ("PA", "PAAC2605.dbc")]


def test_parse_tables(registry):
    assert c.parse_tables(None) == [c.PA] and c.parse_tables("") == [c.PA]
    assert c.parse_tables("pa") == [c.PA]
    assert [t.code for t in c.parse_tables("bi, PA atd")] == ["PA", "BI", "ATD"]  # registry order
    assert [t.code for t in c.parse_tables("all")] == list(registry)
    with pytest.raises(ValueError, match="unknown table"):
        c.parse_tables("pa,xx")


# ------------------------------------------------------------------ store
def add(store, p, rows):
    built = store.tmp / "b"
    built.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.Table.from_pylist(rows), built / (p.files[0].name[:-4] + ".parquet"))
    store.record(p, len(rows), store.publish(p, built))


def part(name, size=100):
    return c.group([c.parse_name(name, size)])[0]


def test_old_pa_manifest_keys_still_work(tmp_path):
    """Stores written before the registry keyed PA entries as 'SP/202605'."""
    s = Store(tmp_path)
    p = part("PASP2605.dbc")
    add(s, p, [{"PA_QTDAPR": "1"}])
    old = {k.split("/", 1)[1]: {x: y for x, y in v.items() if x != "table"} for k, v in s.manifest().items()}
    s.manifest_path.write_text(json.dumps(old), encoding="utf-8")
    assert list(json.loads(s.manifest_path.read_text())) == ["SP/202605"]

    assert s.manifest()["PA/SP/202605"]["table"] == "PA"
    assert s.is_current(p)
    assert s.remove(["PA/SP/202605"]) > 0
    assert s.manifest() == {} and not s.partition_dir("SP", 202605).exists()


@pytest.fixture
def store(tmp_path, registry):
    s = Store(tmp_path / "data")
    add(s, part("PASP2605.dbc"), [{"PA_QTDAPR": "10"}])
    add(s, part("PAAC0312.dbc"), [{"PA_QTDAPR": "7"}])
    add(s, part("BIAC2605.dbc"), [{"X": "1"}, {"X": "2"}])
    add(s, part("ATDAC2605.dbc"), [{"X": "3"}])
    return s


def test_each_table_has_its_folder_and_views(store):
    assert (store.root / "bi" / "competencia=202605" / "uf=AC" / "BIAC2605.parquet").exists()
    assert (store.root / "atd" / "competencia=202605" / "uf=AC").is_dir()
    assert (store.root / "pa" / "competencia=202605" / "uf=SP").is_dir()
    con = query.connect(store)
    assert {"pa", "pa_raw", "pa_legacy", "bi", "bi_raw", "atd", "atd_raw"} <= set(query.views(con))
    assert con.execute("SELECT uf, competencia, COUNT(*) FROM bi GROUP BY ALL").fetchall() == [("AC", 202605, 2)]


runner = CliRunner()


def run(store, *args):
    return runner.invoke(app, ["--data-dir", str(store.root), *args])


def test_cli_status_by_table(store):
    r = run(store, "status")  # default: PA only
    assert r.exit_code == 0, r.output
    assert "pa (" in r.output and "bi (" not in r.output
    r = run(store, "status", "--table", "bi,atd")
    assert "bi (" in r.output and "atd (" in r.output and "pa (" not in r.output
    r = run(store, "status", "-T", "all")
    assert all(f"{t} (" in r.output for t in ("pa", "bi", "atd"))
    r = run(store, "status", "-T", "xx")
    assert r.exit_code != 0 and "unknown table" in r.output


def test_cli_remove_by_table(store):
    r = run(store, "remove", "-T", "bi", "-f", "2026", "-y")
    assert r.exit_code == 0, r.output
    m = store.manifest()
    assert "BI/AC/202605" not in m and {"PA/SP/202605", "ATD/AC/202605", "PA/AC/200312"} <= set(m)
    assert not store.partition_dir("AC", 202605, "BI").exists()
    r = run(store, "remove", "-f", "2026", "-y")  # default PA: leaves ATD alone
    assert "PA/SP/202605" not in store.manifest() and "ATD/AC/202605" in store.manifest()


def test_cli_schema_by_table(store):
    r = run(store, "schema", "-T", "bi")
    assert r.exit_code == 0, r.output
    assert "View bi" in r.output and "a column" in r.output and "View pa" not in r.output
    r = run(store, "schema", "-T", "bi", "--legacy")
    assert "only one layout" in r.output and "View bi" in r.output
    r = run(store, "schema", "--legacy")
    assert "View pa_legacy" in r.output and "BIGINT" in r.output and "View bi" not in r.output


def test_cli_fetch_and_available_pass_tables(store, monkeypatch):
    seen = []

    def fake_list(types, start, end):
        seen.append(([t.code for t in types], start, end))
        return [f for f in (c.parse_name(n, 10) for n in ("PAAC2605.dbc", "BIAC2605.dbc", "BIAC2605b.dbc"))
                if f.table in {t.code for t in types}]

    monkeypatch.setattr(c, "list_remote", fake_list)
    r = run(store, "fetch", "-s", "AC", "-f", "202605", "--dry-run")
    assert r.exit_code == 0, r.output
    assert seen[-1] == (["PA"], 202605, 202605)
    assert "PA AC 2026-05" in r.output and "BIAC" not in r.output
    r = run(store, "fetch", "-T", "pa,bi", "-s", "AC", "-f", "202605", "--dry-run")
    assert seen[-1][0] == ["PA", "BI"]
    # BI AC 2026-05 is stored but its files changed (now split in two): refetched
    assert "BI AC 2026-05" in r.output and "BIAC2605b.dbc" in r.output
    r = run(store, "available", "-T", "bi", "-s", "AC")
    assert r.exit_code == 0, r.output
    assert seen[-1] == (["BI"], 0, 999912) and "bi (test BI)" in r.output
