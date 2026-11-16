"""BI (BPA Individualizado): registry entry, `_1`/`_2` split files, conversion and typed view."""
import pytest

from intrepid_datasus import catalog as c, convert, dictionary, query
from intrepid_datasus.store import Store

# The 36 columns of a real file (BIAC2605.dbc), with their DBF widths. Files before
# Jul/2016 have the same columns without NAT_JUR.
BI_FIELDS = [
    ("CODUNI", 7), ("GESTAO", 6), ("CONDIC", 2), ("UFMUN", 6), ("TPUPS", 2), ("TIPPRE", 2),
    ("MN_IND", 1), ("CNPJCPF", 14), ("CNPJMNT", 14), ("CNPJ_CC", 14), ("DT_PROCESS", 6),
    ("DT_ATEND", 6), ("PROC_ID", 10), ("TPFIN", 2), ("SUBFIN", 4), ("COMPLEX", 1),
    ("AUTORIZ", 13), ("CNSPROF", 15), ("CBOPROF", 6), ("CIDPRI", 4), ("CATEND", 2),
    ("CNS_PAC", 15), ("DTNASC", 8), ("TPIDADEPAC", 1), ("IDADEPAC", 2), ("SEXOPAC", 1),
    ("RACACOR", 2), ("MUNPAC", 6), ("QT_APRES", 11), ("QT_APROV", 11), ("VL_APRES", 20),
    ("VL_APROV", 20), ("UFDIF", 1), ("MNDIF", 1), ("ETNIA", 4), ("NAT_JUR", 4),
]


def row(**kw):
    base = {name: "" for name, _ in BI_FIELDS}
    base.update(CODUNI="2001063", UFMUN="120040", DT_PROCESS="202605", DT_ATEND="202605",
                PROC_ID="0301010072", TPIDADEPAC="4", IDADEPAC="53", SEXOPAC="F",
                MUNPAC="120040", QT_APRES="1", QT_APROV="1", VL_APRES="12.47", VL_APROV="12.47")
    base.update(kw)
    return [base[name] for name, _ in BI_FIELDS]


def test_bi_registered():
    bi = c.REGISTRY["BI"]
    assert bi is c.BI and list(c.REGISTRY)[:2] == ["PA", "BI"] and c.DEFAULT_TABLES == ("PA",)
    assert [(e.key, e.ftp_dir, e.first, e.last) for e in bi.eras] == [("bi", c.FTP_CURRENT_DIR, 200801, 999912)]
    assert bi.eras[0].quantity_cols == ("QT_APRES", "QT_APROV")
    assert bi.eras[0].value_cols == ("VL_APRES", "VL_APROV")
    assert c.parse_tables("bi") == [bi] and c.parse_tables("all")[:2] == [c.PA, bi]
    with pytest.raises(ValueError):
        bi.era_for(200712)


def test_bi_dictionary_covers_every_column():
    cols = {name for name, _ in BI_FIELDS} | {"competencia", "uf", "_ARQUIVO_ORIGEM"}
    assert set(dictionary.BI) == cols
    assert all(desc.strip() for desc in dictionary.BI.values())


@pytest.mark.parametrize("name,uf,comp,part", [
    ("BIAC2605.dbc", "AC", 202605, ""),
    ("BIAC0801.DBC", "AC", 200801, ""),
    ("BISP2605_1.dbc", "SP", 202605, "1"),
    ("BISP2508_3.dbc", "SP", 202508, "3"),
    ("BIPA2401.dbc", "PA", 202401, ""),
])
def test_bi_names(name, uf, comp, part):
    rf = c.parse_name(name, 5)
    assert (rf.table, rf.uf, rf.competencia, rf.part) == ("BI", uf, comp, part)
    assert c.PA.parse(name) is None


@pytest.mark.parametrize("name", [
    "PASP2605.dbc", "BISP2605_.dbc", "BISP2605_a.dbc", "BISP2605-1.dbc", "BIXX2605.dbc",
    "BISP2613.dbc", "BISP2605.dbf",
])
def test_bi_rejects(name):
    assert c.BI.parse(name) is None


def test_numbered_parts_sort_numerically():
    files = [c.parse_name(n, 1) for n in ("BISP2605_10.dbc", "BISP2605_2.dbc", "BISP2605_1.dbc")]
    (p,) = c.group(files)
    assert [f.part for f in p.files] == ["1", "2", "10"]


def test_whole_file_dropped_when_parts_exist():
    """BI SP/MG/RJ 2023-05..2024-02: the FTP has BISP2305.dbc and BISP2305_1/_2.dbc."""
    files = [c.parse_name(n, s) for n, s in [
        ("BISP2305.dbc", 362), ("BISP2305_1.dbc", 222), ("BISP2305_2.dbc", 137), ("BIAC2305.dbc", 1)]]
    ac, sp = c.group(files)
    assert [f.name for f in sp.files] == ["BISP2305_1.dbc", "BISP2305_2.dbc"] and sp.size == 359
    assert [f.name for f in ac.files] == ["BIAC2305.dbc"]


def test_match_listing_keeps_bi_parts():
    listing = [("BISP2605_1.dbc", 1), ("BISP2605_2.dbc", 2), ("PASP2605a.dbc", 3), ("BIAC2605.dbc", 4)]
    got = c.match_listing(listing, [c.PA, c.BI], [c.PA.eras[1], c.BI.eras[0]])
    assert sorted((f.table, f.name) for f in got) == [
        ("BI", "BIAC2605.dbc"), ("BI", "BISP2605_1.dbc"), ("BI", "BISP2605_2.dbc"), ("PA", "PASP2605a.dbc")]


def test_bi_conversion_and_view(make_dbf, tmp_path):
    store = Store(tmp_path / "data")
    p = c.group([c.parse_name("BIAC2605.dbc", 10)])[0]
    built = store.tmp / "b"
    built.mkdir(parents=True)
    dbf = make_dbf("BIAC2605.dbf", BI_FIELDS, [
        row(),
        row(QT_APRES="3", QT_APROV="2", VL_APRES="30.00", VL_APROV="20.00", CIDPRI="I10"),
        row(QT_APROV="x"),  # malformed: NULL in the typed view, kept in _raw
    ])
    assert convert.dbf_to_parquet(dbf, built / "BIAC2605.parquet", origin="BIAC2605.dbc") == 3
    store.record(p, 3, store.publish(p, built))

    con = query.connect(store)
    assert {"bi", "bi_raw"} <= set(query.views(con))
    types = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                             "WHERE table_name = 'bi'").fetchall())
    assert types["QT_APROV"] == "BIGINT" and types["VL_APROV"] == "DOUBLE"
    assert types["PROC_ID"] == "VARCHAR" and types["competencia"] == "INTEGER"
    assert con.execute("SELECT SUM(QT_APROV), SUM(VL_APROV), COUNT(*) FILTER (WHERE QT_APROV IS NULL), "
                       "MIN(uf), MIN(competencia), MIN(_ARQUIVO_ORIGEM) FROM bi").fetchone() == (
        3, 12.47 * 2 + 20.0, 1, "AC", 202605, "BIAC2605.dbc")
    assert con.execute("SELECT QT_APROV FROM bi_raw WHERE QT_APROV = 'x'").fetchone() == ("x",)
    assert con.execute("SELECT PROC_ID FROM bi LIMIT 1").fetchone() == ("0301010072",)  # leading zero kept


def test_bi_rows_without_nat_jur(make_dbf, tmp_path):
    """Files before Jul/2016 lack NAT_JUR; the view still works and shows NULL there."""
    store = Store(tmp_path / "data")
    for name, fields in (("BIAC1601", BI_FIELDS[:-1]), ("BIAC2605", BI_FIELDS)):
        p = c.group([c.parse_name(name + ".dbc", 10)])[0]
        built = store.tmp / name
        built.mkdir(parents=True)
        rows = [row(NAT_JUR="1023")[: len(fields)]]
        convert.dbf_to_parquet(make_dbf(name + ".dbf", fields, rows), built / (name + ".parquet"), name + ".dbc")
        store.record(p, 1, store.publish(p, built))
    con = query.connect(store)
    assert con.execute("SELECT competencia, NAT_JUR FROM bi ORDER BY 1").fetchall() == [
        (201601, None), (202605, "1023")]
