"""AD (APAC Laudos Diversos): registry entry, dictionary, conversion and typed view."""
import pytest

from intrepid_datasus import catalog as c, convert, dictionary, query
from intrepid_datasus.store import Store

# The 46 columns of a real file (ADSP2608.dbc), with their DBF widths: only the shared APAC
# columns, no AD_ column. AP_VL_AP is a numeric (N) field 20 wide, as in AR; the converter
# reads every field as text. Files before Jul/2016 have the same columns without AP_NATJUR (45).
AD_FIELDS = [
    ("AP_MVM", 6), ("AP_CONDIC", 2), ("AP_GESTAO", 6), ("AP_CODUNI", 7), ("AP_AUTORIZ", 13),
    ("AP_CMP", 6), ("AP_PRIPAL", 10), ("AP_VL_AP", 20), ("AP_UFMUN", 6), ("AP_TPUPS", 2),
    ("AP_TIPPRE", 2), ("AP_MN_IND", 1), ("AP_CNPJCPF", 14), ("AP_CNPJMNT", 14), ("AP_CNSPCN", 15),
    ("AP_COIDADE", 1), ("AP_NUIDADE", 2), ("AP_SEXO", 1), ("AP_RACACOR", 2), ("AP_MUNPCN", 6),
    ("AP_UFNACIO", 3), ("AP_CEPPCN", 8), ("AP_UFDIF", 1), ("AP_MNDIF", 1), ("AP_DTINIC", 8),
    ("AP_DTFIM", 8), ("AP_TPATEN", 2), ("AP_TPAPAC", 1), ("AP_MOTSAI", 2), ("AP_OBITO", 1),
    ("AP_ENCERR", 1), ("AP_PERMAN", 1), ("AP_ALTA", 1), ("AP_TRANSF", 1), ("AP_DTOCOR", 8),
    ("AP_CODEMI", 10), ("AP_CATEND", 2), ("AP_APACANT", 13), ("AP_UNISOL", 7), ("AP_DTSOLIC", 8),
    ("AP_DTAUT", 8), ("AP_CIDCAS", 4), ("AP_CIDPRI", 4), ("AP_CIDSEC", 4), ("AP_ETNIA", 4),
    ("AP_NATJUR", 4),
]
FIELDS_2008 = [f for f in AD_FIELDS if f[0] != "AP_NATJUR"]  # 45 columns, until Jun/2016


def row(fields=AD_FIELDS, **kw):
    base = {name: "" for name, _ in AD_FIELDS}
    base.update(AP_MVM="202605", AP_CMP="202605", AP_CODUNI="2077485", AP_AUTORIZ="3526201234567",
                AP_PRIPAL="0405050372", AP_VL_AP="              771.60", AP_UFMUN="355030", AP_TPATEN="23",
                AP_TPAPAC="3", AP_DTINIC="20260504", AP_DTFIM="20260531", AP_CIDPRI="H251",
                AP_NATJUR="1023")
    base.update(kw)
    return [base[name] for name, _ in fields]


def test_ad_layout():
    assert len(AD_FIELDS) == 46 and len(FIELDS_2008) == 45
    assert sum(w for _, w in AD_FIELDS) + 1 == 252  # record length of ADSP2608.dbc
    assert sum(w for _, w in FIELDS_2008) + 1 == 248  # record length of ADSP1606.dbc


def test_ad_registered():
    ad = c.REGISTRY["AD"]
    assert ad is c.AD and list(c.REGISTRY)[:6] == ["PA", "BI", "AM", "AQ", "AR", "AD"]
    assert c.DEFAULT_TABLES == ("PA",)
    assert [(e.key, e.ftp_dir, e.first, e.last) for e in ad.eras] == [("ad", c.FTP_CURRENT_DIR, 200801, 999912)]
    assert ad.eras[0].quantity_cols == () and ad.eras[0].value_cols == ("AP_VL_AP",)
    assert c.parse_tables("ad") == [ad] and c.parse_tables("ar,ad") == [c.AR, ad]
    assert c.parse_tables("all")[:6] == [c.PA, c.BI, c.AM, c.AQ, c.AR, ad]
    with pytest.raises(ValueError):
        ad.era_for(200712)


def test_ad_dictionary_covers_every_column():
    cols = {name for name, _ in AD_FIELDS} | {"competencia", "uf", "_ARQUIVO_ORIGEM"}
    assert set(dictionary.AD) == cols
    assert all(desc.strip() and "TODO" not in desc for desc in dictionary.AD.values())
    assert {name for name, _ in AD_FIELDS} == set(dictionary.APAC_COMMON)  # AD = the shared columns only
    assert dictionary.AD["AP_MVM"] == dictionary.APAC_COMMON["AP_MVM"]
    assert dictionary.AD["AP_PRIPAL"] != dictionary.APAC_COMMON["AP_PRIPAL"]  # AD-specific notes
    assert "ADSP2605.dbc" in dictionary.AD["_ARQUIVO_ORIGEM"]


@pytest.mark.parametrize("name,uf,comp", [
    ("ADAC2605.dbc", "AC", 202605),
    ("ADSP0801.DBC", "SP", 200801),
    ("ADAP2608.dbc", "AP", 202608),
    ("ADRR1607.dbc", "RR", 201607),
])
def test_ad_names(name, uf, comp):
    rf = c.parse_name(name, 5)
    assert (rf.table, rf.uf, rf.competencia, rf.part) == ("AD", uf, comp, "")


@pytest.mark.parametrize("name", [
    "ADXX2605.dbc", "ADSP2613.dbc", "ADSP2605.dbf", "ARSP2605.dbc", "AMSP2605.dbc", "ATDSP2605.dbc",
])
def test_ad_rejects(name):
    assert c.AD.parse(name) is None


def test_ad_conversion_and_view(make_dbf, tmp_path):
    store = Store(tmp_path / "data")
    p = c.group([c.parse_name("ADSP2605.dbc", 10)])[0]
    built = store.tmp / "b"
    built.mkdir(parents=True)
    dbf = make_dbf("ADSP2605.dbf", AD_FIELDS, [
        row(),
        row(AP_CMP="202604", AP_PRIPAL="0211060100", AP_VL_AP="               24.24"),  # late billing of April
        row(AP_AUTORIZ="3526209999999", AP_VL_AP="x"),  # malformed: NULL in the typed view, kept in _raw
    ])
    assert convert.dbf_to_parquet(dbf, built / "ADSP2605.parquet", origin="ADSP2605.dbc") == 3
    store.record(p, 3, store.publish(p, built))

    con = query.connect(store)
    assert {"ad", "ad_raw"} <= set(query.views(con))
    types = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                             "WHERE table_name = 'ad'").fetchall())
    assert types["AP_VL_AP"] == "DOUBLE" and types["competencia"] == "INTEGER"
    assert types["AP_PRIPAL"] == types["AP_TPATEN"] == types["AP_NATJUR"] == "VARCHAR"
    assert con.execute("SELECT SUM(AP_VL_AP), COUNT(*) FILTER (WHERE AP_VL_AP IS NULL), "
                       "COUNT(DISTINCT (AP_AUTORIZ, AP_CMP)), MIN(uf), MIN(competencia), MIN(_ARQUIVO_ORIGEM) "
                       "FROM ad").fetchone() == (795.84, 1, 3, "SP", 202605, "ADSP2605.dbc")
    assert con.execute("SELECT AP_VL_AP FROM ad_raw WHERE AP_VL_AP = 'x'").fetchone() == ("x",)
    assert con.execute("SELECT AP_PRIPAL, AP_TPATEN, AP_CIDPRI FROM ad "
                       "WHERE AP_CMP = '202604'").fetchone() == ("0211060100", "23", "H251")


def test_ad_natjur_added_in_one_view(make_dbf, tmp_path):
    """45 columns until Jun/2016, 46 (AP_NATJUR) since: one era, NULL before."""
    store = Store(tmp_path / "data")
    for name, fields in (("ADSP1606", FIELDS_2008), ("ADSP1607", AD_FIELDS)):
        p = c.group([c.parse_name(name + ".dbc", 10)])[0]
        built = store.tmp / name
        built.mkdir(parents=True)
        convert.dbf_to_parquet(make_dbf(name + ".dbf", fields, [row(fields)]), built / (name + ".parquet"),
                               name + ".dbc")
        store.record(p, 1, store.publish(p, built))
    con = query.connect(store)
    assert con.execute("SELECT competencia, AP_NATJUR, AP_PRIPAL FROM ad ORDER BY 1").fetchall() == [
        (201606, None, "0405050372"), (201607, "1023", "0405050372")]
