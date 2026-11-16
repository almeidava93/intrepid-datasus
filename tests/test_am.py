"""AM (APAC Medicamentos): registry entry, shared APAC dictionary, conversion and typed view."""
import pytest

from intrepid_datasus import catalog as c, convert, dictionary, query
from intrepid_datasus.store import Store

# The 51 columns of a real file (AMAC2605.dbc), with their DBF widths. AP_VL_AP is a numeric
# (N) field in the DBF; the converter reads every field as text. Files before Jul/2016 have
# the same columns without AP_NATJUR.
AM_FIELDS = [
    ("AP_MVM", 6), ("AP_CONDIC", 2), ("AP_GESTAO", 6), ("AP_CODUNI", 7), ("AP_AUTORIZ", 13),
    ("AP_CMP", 6), ("AP_PRIPAL", 10), ("AP_VL_AP", 12), ("AP_UFMUN", 6), ("AP_TPUPS", 2),
    ("AP_TIPPRE", 2), ("AP_MN_IND", 1), ("AP_CNPJCPF", 14), ("AP_CNPJMNT", 14), ("AP_CNSPCN", 15),
    ("AP_COIDADE", 1), ("AP_NUIDADE", 2), ("AP_SEXO", 1), ("AP_RACACOR", 2), ("AP_MUNPCN", 6),
    ("AP_UFNACIO", 3), ("AP_CEPPCN", 8), ("AP_UFDIF", 2), ("AP_MNDIF", 2), ("AP_DTINIC", 8),
    ("AP_DTFIM", 8), ("AP_TPATEN", 2), ("AP_TPAPAC", 1), ("AP_MOTSAI", 2), ("AP_OBITO", 1),
    ("AP_ENCERR", 1), ("AP_PERMAN", 1), ("AP_ALTA", 1), ("AP_TRANSF", 1), ("AP_DTOCOR", 8),
    ("AP_CODEMI", 10), ("AP_CATEND", 2), ("AP_APACANT", 13), ("AP_UNISOL", 7), ("AP_DTSOLIC", 8),
    ("AP_DTAUT", 8), ("AP_CIDCAS", 4), ("AP_CIDPRI", 4), ("AP_CIDSEC", 4), ("AP_ETNIA", 4),
    ("AM_PESO", 3), ("AM_ALTURA", 3), ("AM_TRANSPL", 1), ("AM_QTDTRAN", 2), ("AM_GESTANT", 1),
    ("AP_NATJUR", 4),
]


def row(**kw):
    base = {name: "" for name, _ in AM_FIELDS}
    base.update(AP_MVM="202605", AP_CMP="202605", AP_CODUNI="2001063", AP_AUTORIZ="1226200113413",
                AP_PRIPAL="0604040040", AP_VL_AP="       30.97", AP_UFMUN="120040", AP_TPAPAC="1",
                AP_DTINIC="20260507", AP_DTFIM="20260731", AP_CIDPRI="J450", AM_PESO="086")
    base.update(kw)
    return [base[name] for name, _ in AM_FIELDS]


def test_am_registered():
    am = c.REGISTRY["AM"]
    assert am is c.AM and list(c.REGISTRY)[:3] == ["PA", "BI", "AM"] and c.DEFAULT_TABLES == ("PA",)
    assert [(e.key, e.ftp_dir, e.first, e.last) for e in am.eras] == [("am", c.FTP_CURRENT_DIR, 200801, 999912)]
    assert am.eras[0].quantity_cols == () and am.eras[0].value_cols == ("AP_VL_AP",)
    assert c.parse_tables("am") == [am] and c.parse_tables("all")[:3] == [c.PA, c.BI, am]
    with pytest.raises(ValueError):
        am.era_for(200712)


def test_am_dictionary_covers_every_column():
    cols = {name for name, _ in AM_FIELDS} | {"competencia", "uf", "_ARQUIVO_ORIGEM"}
    assert set(dictionary.AM) == cols
    assert all(desc.strip() for desc in dictionary.AM.values())


def test_apac_common_is_shared():
    """Every AP_ column of AM comes from APAC_COMMON, so later APAC types can reuse it."""
    ap = [name for name, _ in AM_FIELDS if name.startswith("AP_")]
    assert set(ap) == set(dictionary.APAC_COMMON)
    assert dictionary.AM["AP_MVM"] == dictionary.APAC_COMMON["AP_MVM"]
    assert dictionary.AM["AP_PRIPAL"] != dictionary.APAC_COMMON["AP_PRIPAL"]  # AM-specific wording
    d = dictionary.apac("XX", {"AP_TPPRE": "renamed"}, without=("AP_TIPPRE",))
    assert "AP_TIPPRE" not in d and d["AP_TPPRE"] == "renamed" and "XXSP2605.dbc" in d["_ARQUIVO_ORIGEM"]
    assert {"competencia", "uf", "_ARQUIVO_ORIGEM"} <= set(d)


@pytest.mark.parametrize("name,uf,comp", [
    ("AMAC2605.dbc", "AC", 202605),
    ("AMSP0801.DBC", "SP", 200801),
    ("AMPA2605.dbc", "PA", 202605),  # AM for Pará, not AMP
    ("AMPE1607.dbc", "PE", 201607),
])
def test_am_names(name, uf, comp):
    rf = c.parse_name(name, 5)
    assert (rf.table, rf.uf, rf.competencia, rf.part) == ("AM", uf, comp, "")


@pytest.mark.parametrize("name", [
    "AMPSP2605.dbc", "AMPPA2605.dbc",  # AMP (multiprofessional follow-up) files
    "AMXX2605.dbc", "AMSP2613.dbc", "AMSP2605.dbf", "PASP2605.dbc", "AQSP2605.dbc",
])
def test_am_rejects(name):
    assert c.AM.parse(name) is None


def test_am_conversion_and_view(make_dbf, tmp_path):
    store = Store(tmp_path / "data")
    p = c.group([c.parse_name("AMAC2605.dbc", 10)])[0]
    built = store.tmp / "b"
    built.mkdir(parents=True)
    dbf = make_dbf("AMAC2605.dbf", AM_FIELDS, [
        row(),
        row(AP_AUTORIZ="1226200112478", AP_VL_AP="        0.00", AP_TPAPAC="2", AP_PRIPAL="0604610017"),
        row(AP_AUTORIZ="1226200108188", AP_VL_AP="x"),  # malformed: NULL in the typed view, kept in _raw
    ])
    assert convert.dbf_to_parquet(dbf, built / "AMAC2605.parquet", origin="AMAC2605.dbc") == 3
    store.record(p, 3, store.publish(p, built))

    con = query.connect(store)
    assert {"am", "am_raw"} <= set(query.views(con))
    types = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                             "WHERE table_name = 'am'").fetchall())
    assert types["AP_VL_AP"] == "DOUBLE"
    assert types["AP_PRIPAL"] == "VARCHAR" and types["AM_PESO"] == "VARCHAR" and types["competencia"] == "INTEGER"
    assert con.execute("SELECT SUM(AP_VL_AP), COUNT(*) FILTER (WHERE AP_VL_AP IS NULL), COUNT(DISTINCT AP_AUTORIZ), "
                       "MIN(uf), MIN(competencia), MIN(_ARQUIVO_ORIGEM) FROM am").fetchone() == (
        30.97, 1, 3, "AC", 202605, "AMAC2605.dbc")
    assert con.execute("SELECT AP_VL_AP FROM am_raw WHERE AP_VL_AP = 'x'").fetchone() == ("x",)
    assert con.execute("SELECT AP_PRIPAL, AM_PESO FROM am LIMIT 1").fetchone() == ("0604040040", "086")  # zeros kept


def test_am_rows_without_natjur(make_dbf, tmp_path):
    """Files before Jul/2016 lack AP_NATJUR; the view still works and shows NULL there."""
    store = Store(tmp_path / "data")
    for name, fields in (("AMAC1606", AM_FIELDS[:-1]), ("AMAC1607", AM_FIELDS)):
        p = c.group([c.parse_name(name + ".dbc", 10)])[0]
        built = store.tmp / name
        built.mkdir(parents=True)
        rows = [row(AP_NATJUR="1023")[: len(fields)]]
        convert.dbf_to_parquet(make_dbf(name + ".dbf", fields, rows), built / (name + ".parquet"), name + ".dbc")
        store.record(p, 1, store.publish(p, built))
    con = query.connect(store)
    assert con.execute("SELECT competencia, AP_NATJUR FROM am ORDER BY 1").fetchall() == [
        (201606, None), (201607, "1023")]
