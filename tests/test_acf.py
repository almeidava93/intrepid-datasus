"""ACF (APAC Confecção de Fístula): registry entry, dictionary, conversion and view."""
import pytest

from intrepid_datasus import catalog as c, convert, dictionary, query
from intrepid_datasus.store import Store

# The 55 columns of a real file (ACFSP1408.dbc ... ACFSP1606.dbc), with their DBF widths: the 45 shared
# APAC columns under their usual names, then 10 ACF_ columns. Every one of the 3,795 headers was probed:
# the Oct/2014 files (ACFSP1410.dbc) and those from Jul/2016 on also have AP_NATJUR, appended last
# (56 columns). AP_VL_AP is a numeric (N) field 20 wide; ACF_VEIDIA/ACF_ARTDIA are text (C) 4 wide.
ACF_FIELDS = [
    ("AP_MVM", 6), ("AP_CONDIC", 2), ("AP_GESTAO", 6), ("AP_CODUNI", 7), ("AP_AUTORIZ", 13), ("AP_CMP", 6),
    ("AP_PRIPAL", 10), ("AP_VL_AP", 20), ("AP_UFMUN", 6), ("AP_TPUPS", 2), ("AP_TIPPRE", 2), ("AP_MN_IND", 1),
    ("AP_CNPJCPF", 14), ("AP_CNPJMNT", 14), ("AP_CNSPCN", 15), ("AP_COIDADE", 1), ("AP_NUIDADE", 2),
    ("AP_SEXO", 1), ("AP_RACACOR", 2), ("AP_MUNPCN", 6), ("AP_UFNACIO", 3), ("AP_CEPPCN", 8),
    ("AP_UFDIF", 1), ("AP_MNDIF", 1), ("AP_DTINIC", 8), ("AP_DTFIM", 8), ("AP_TPATEN", 2), ("AP_TPAPAC", 1),
    ("AP_MOTSAI", 2), ("AP_OBITO", 1), ("AP_ENCERR", 1), ("AP_PERMAN", 1), ("AP_ALTA", 1), ("AP_TRANSF", 1),
    ("AP_DTOCOR", 8), ("AP_CODEMI", 10), ("AP_CATEND", 2), ("AP_APACANT", 13), ("AP_UNISOL", 7),
    ("AP_DTSOLIC", 8), ("AP_DTAUT", 8), ("AP_CIDCAS", 4), ("AP_CIDPRI", 4), ("AP_CIDSEC", 4),
    ("AP_ETNIA", 4), ("ACF_DUPLEX", 1), ("ACF_USOCAT", 1), ("ACF_PREFAV", 1), ("ACF_FLEBIT", 1),
    ("ACF_HEMATO", 1), ("ACF_VEIAVI", 1), ("ACF_PULSO", 1), ("ACF_VEIDIA", 4), ("ACF_ARTDIA", 4),
    ("ACF_FREMIT", 1),
]
FIELDS_NATJUR = ACF_FIELDS + [("AP_NATJUR", 4)]  # Oct/2014, and Jul/2016 onward
OWN = ["ACF_DUPLEX", "ACF_USOCAT", "ACF_PREFAV", "ACF_FLEBIT", "ACF_HEMATO", "ACF_VEIAVI", "ACF_PULSO",
       "ACF_VEIDIA", "ACF_ARTDIA", "ACF_FREMIT"]


def row(fields=ACF_FIELDS, **kw):
    base = {name: "" for name, _ in FIELDS_NATJUR}
    base.update(AP_MVM="201606", AP_CMP="201606", AP_CODUNI="2077485", AP_AUTORIZ="3516201234567",
                AP_PRIPAL="0418010030", AP_VL_AP="              600.00", AP_UFMUN="355030", AP_TPUPS="05",
                AP_TIPPRE="00", AP_TPATEN="11", AP_TPAPAC="3", AP_MNDIF="1", AP_DTINIC="20160601",
                AP_DTFIM="20160630", AP_CIDCAS="N180", AP_CIDPRI="0000", AP_CIDSEC="0000", ACF_DUPLEX="N",
                ACF_USOCAT="S", ACF_PREFAV="N", ACF_FLEBIT="N", ACF_HEMATO="N", ACF_VEIAVI="S", ACF_PULSO="S",
                ACF_VEIDIA="0003", ACF_ARTDIA="0003", ACF_FREMIT="1", AP_NATJUR="2062")
    base.update(kw)
    return [base[name] for name, _ in fields]


def test_acf_layout():
    assert len(ACF_FIELDS) == 55 and len(FIELDS_NATJUR) == 56
    assert sum(w for _, w in ACF_FIELDS) + 1 == 264  # record length of ACFSP1408.dbc ... ACFSP1606.dbc
    assert sum(w for _, w in FIELDS_NATJUR) + 1 == 268  # ACFSP1410.dbc, ACFSP1607.dbc ... ACFSP2608.dbc
    assert [n for n, _ in ACF_FIELDS[-10:]] == OWN


def test_acf_registered():
    acf = c.REGISTRY["ACF"]
    assert acf is c.ACF and list(c.REGISTRY)[:13] == [
        "PA", "BI", "AM", "AQ", "AR", "AD", "ATD", "AN", "PS", "SAD", "AB", "ABO", "ACF"]
    assert c.DEFAULT_TABLES == ("PA",)
    assert [(e.key, e.ftp_dir, e.first, e.last) for e in acf.eras] == [("acf", c.FTP_CURRENT_DIR, 201408, 999912)]
    assert acf.eras[0].quantity_cols == () and acf.eras[0].value_cols == ("AP_VL_AP",)
    assert c.parse_tables("acf") == [acf] and c.parse_tables("atd,acf") == [c.ATD, acf]
    assert acf.era_for(201408).key == acf.era_for(202608).key == "acf"
    with pytest.raises(ValueError):
        acf.era_for(201407)  # fistula creation before Aug/2014 is in AD


def test_acf_dictionary_covers_every_column():
    cols = {name for name, _ in FIELDS_NATJUR} | {"competencia", "uf", "_ARQUIVO_ORIGEM"}
    assert set(dictionary.ACF) == cols
    assert all(desc.strip() and "TODO" not in desc for desc in dictionary.ACF.values())
    # every shared AP_ column, under its usual name; nothing renamed or missing
    shared = set(dictionary.APAC_COMMON)
    assert {name for name, _ in FIELDS_NATJUR} & shared == shared
    assert {name for name, _ in FIELDS_NATJUR} - shared == set(OWN)
    assert dictionary.ACF["AP_MVM"] == dictionary.APAC_COMMON["AP_MVM"]
    assert "0418010030" in dictionary.ACF["AP_PRIPAL"]
    assert "0418010013" in dictionary.ACF["AP_PRIPAL"] and "0418010048" in dictionary.ACF["AP_PRIPAL"]
    assert "Oct/2014" in dictionary.ACF["AP_NATJUR"]
    assert "ACFSP2605.dbc" in dictionary.ACF["_ARQUIVO_ORIGEM"]
    # the checked quirks are documented
    assert "Always 3" in dictionary.ACF["AP_TPAPAC"] and "Always 12" in dictionary.ACF["AP_TPATEN"]
    assert "no labels" in dictionary.ACF["ACF_FREMIT"] and "not measured" in dictionary.ACF["ACF_VEIDIA"]
    assert "AD" in dictionary.ACF["AP_PRIPAL"] and "Always '0000'" in dictionary.ACF["AP_CIDPRI"]
    assert all("S" in dictionary.ACF[n] and "N" in dictionary.ACF[n] for n in OWN[:7])


@pytest.mark.parametrize("name,uf,comp", [
    ("ACFSP1408.dbc", "SP", 201408),
    ("ACFAC2608.DBC", "AC", 202608),
    ("ACFPE1112.dbc", "PE", 201112),  # name parses; the era starts in Aug/2014
])
def test_acf_names(name, uf, comp):
    rf = c.parse_name(name, 5)
    assert (rf.table, rf.uf, rf.competencia, rf.part) == ("ACF", uf, comp, "")


@pytest.mark.parametrize("name", [
    "ACSP1606.dbc", "ACFXX1606.dbc", "ACFSP1613.dbc", "ACFSP1606.dbf", "ADSP1606.dbc", "ABOSP1606.dbc",
])
def test_acf_rejects(name):
    assert c.ACF.parse(name) is None


def test_others_do_not_claim_acf():
    assert all(ft.parse("ACFSP1606.dbc") is None for ft in c.REGISTRY.values() if ft is not c.ACF)


def test_acf_conversion_and_view(make_dbf, tmp_path):
    store = Store(tmp_path / "data")
    p = c.group([c.parse_name("ACFSP1606.dbc", 10)])[0]
    built = store.tmp / "b"
    built.mkdir(parents=True)
    dbf = make_dbf("ACFSP1606.dbf", ACF_FIELDS, [
        row(),
        row(AP_AUTORIZ="3516209999998", AP_CMP="201605", ACF_DUPLEX="S", ACF_VEIDIA="2,5",  # late, comma
            ACF_ARTDIA="", ACF_FREMIT="4"),
        row(AP_AUTORIZ="3516209999999", AP_VL_AP="x"),  # malformed: NULL in the typed view, kept in _raw
    ])
    assert convert.dbf_to_parquet(dbf, built / "ACFSP1606.parquet", origin="ACFSP1606.dbc") == 3
    store.record(p, 3, store.publish(p, built))

    con = query.connect(store)
    assert {"acf", "acf_raw"} <= set(query.views(con))
    types = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                             "WHERE table_name = 'acf'").fetchall())
    assert types["AP_VL_AP"] == "DOUBLE" and types["competencia"] == "INTEGER"
    # the diameters stay text: their format varies (0003, 3, 2,5), see docs/databases/sia/acf.md
    assert types["ACF_VEIDIA"] == types["ACF_ARTDIA"] == types["ACF_FREMIT"] == types["ACF_DUPLEX"] == "VARCHAR"
    assert con.execute("SELECT ROUND(SUM(AP_VL_AP), 2), COUNT(*) FILTER (WHERE AP_VL_AP IS NULL), "
                       "MIN(uf), MIN(competencia), MIN(_ARQUIVO_ORIGEM) FROM acf").fetchone() == (
        1200.0, 1, "SP", 201606, "ACFSP1606.dbc")
    assert con.execute("SELECT AP_VL_AP FROM acf_raw WHERE AP_VL_AP = 'x'").fetchone() == ("x",)
    assert con.execute("SELECT ACF_DUPLEX, ACF_VEIDIA, ACF_ARTDIA, ACF_FREMIT FROM acf WHERE AP_CMP = '201605'"
                       ).fetchone() == ("S", "2,5", None, "4")


def test_acf_natjur_in_oct_2014_and_from_jul_2016(make_dbf, tmp_path):
    """55 columns, 56 (AP_NATJUR, appended last) in Oct/2014 and from Jul/2016."""
    store = Store(tmp_path / "data")
    for name, fields in (("ACFSP1409", ACF_FIELDS), ("ACFSP1410", FIELDS_NATJUR), ("ACFSP1606", ACF_FIELDS),
                         ("ACFSP1607", FIELDS_NATJUR)):
        p = c.group([c.parse_name(name + ".dbc", 10)])[0]
        built = store.tmp / name
        built.mkdir(parents=True)
        convert.dbf_to_parquet(make_dbf(name + ".dbf", fields, [row(fields)]), built / (name + ".parquet"),
                               name + ".dbc")
        store.record(p, 1, store.publish(p, built))
    con = query.connect(store)
    assert con.execute("SELECT competencia, AP_NATJUR, ACF_VEIDIA FROM acf ORDER BY 1").fetchall() == [
        (201409, None, "0003"), (201410, "2062", "0003"), (201606, None, "0003"), (201607, "2062", "0003")]
