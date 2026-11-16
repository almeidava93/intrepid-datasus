"""ABO (APAC Acompanhamento Pós-Cirurgia Bariátrica): registry entry, dictionary, conversion and view."""
import pytest

from intrepid_datasus import catalog as c, convert, dictionary, query
from intrepid_datasus.store import Store

# The 77 columns of a real file (ABOSP1401.dbc ... ABOSP1606.dbc), with their DBF widths. Every one
# of the 1,621 headers was probed: the Oct/2014 files (ABOSP1410.dbc) and those from Jul/2016 on
# also have AP_NATJUR, appended last (78 columns). Six shared APAC columns have other names than in
# the other APAC types (AP_TPPRE, AP_TPATEND, AP_DTOOCOR, AP_APACAN, CO_CIDPRIM, CO_CIDSEC), and
# AB_ANOACOM is 1 wide (4 in AB). AP_VL_AP is a numeric (N) field 20 wide.
ABO_FIELDS = [
    ("AP_MVM", 6), ("AP_CONDIC", 2), ("AP_GESTAO", 6), ("AP_CODUNI", 7), ("AP_AUTORIZ", 13), ("AP_CMP", 6),
    ("AP_PRIPAL", 10), ("AP_VL_AP", 20), ("AP_UFMUN", 6), ("AP_TPUPS", 2), ("AP_TPPRE", 2), ("AP_MN_IND", 1),
    ("AP_CNPJCPF", 14), ("AP_CNPJMNT", 14), ("AP_CNSPCN", 15), ("AP_COIDADE", 1), ("AP_NUIDADE", 2),
    ("AP_SEXO", 1), ("AP_RACACOR", 2), ("AP_MUNPCN", 6), ("AP_UFNACIO", 3), ("AP_CEPPCN", 8),
    ("AP_UFDIF", 1), ("AP_MNDIF", 1), ("AP_DTINIC", 8), ("AP_DTFIM", 8), ("AP_TPATEND", 2), ("AP_TPAPAC", 1),
    ("AP_MOTSAI", 2), ("AP_OBITO", 1), ("AP_ENCERR", 1), ("AP_PERMAN", 1), ("AP_ALTA", 1), ("AP_TRANSF", 1),
    ("AP_DTOOCOR", 8), ("AP_CODEMI", 10), ("AP_CATEND", 2), ("AP_APACAN", 13), ("AP_UNISOL", 7),
    ("AP_DTSOLIC", 8), ("AP_DTAUT", 8), ("AP_CIDCAS", 4), ("CO_CIDPRIM", 4), ("CO_CIDSEC", 4),
    ("AP_ETNIA", 4), ("AB_IMC", 3), ("AB_PROCAIH", 10), ("AB_DTCIRUR", 8), ("AB_NUMAIH", 13),
    ("AB_PRCAIH2", 10), ("AB_T_PRC2", 3), ("AB_PRCAIH3", 10), ("AB_T_PRC3", 3), ("AB_PRCAIH4", 10),
    ("AB_T_PRC4", 3), ("AB_PRCAIH5", 10), ("AB_T_PRC5", 3), ("AB_PRCAIH6", 10), ("AB_T_PRC6", 3),
    ("AB_NUMAIH2", 13), ("AB_DTCIRG2", 8), ("AB_MESACOM", 2), ("AB_ANOACOM", 1), ("AB_PONTBAR", 1),
    ("AB_TABBARR", 1), ("AP_COMORB", 1), ("AP_CID_C1", 4), ("AP_CID_C2", 4), ("AP_CID_C3", 4),
    ("AP_CID_C4", 4), ("AP_CID_C5", 4), ("AP_CID_CO", 4), ("AP_MEDICAM", 1), ("AP_POLIVIT", 1),
    ("AP_ATV_FIS", 1), ("AP_REG_PES", 1), ("AP_ADESAO", 1),
]
FIELDS_NATJUR = ABO_FIELDS + [("AP_NATJUR", 4)]  # Oct/2014, and Jul/2016 onward
RENAMED = {"AP_TIPPRE": "AP_TPPRE", "AP_TPATEN": "AP_TPATEND", "AP_DTOCOR": "AP_DTOOCOR",
           "AP_APACANT": "AP_APACAN", "AP_CIDPRI": "CO_CIDPRIM", "AP_CIDSEC": "CO_CIDSEC"}


def row(fields=ABO_FIELDS, **kw):
    base = {name: "" for name, _ in FIELDS_NATJUR}
    base.update(AP_MVM="201606", AP_CMP="201606", AP_CODUNI="2087057", AP_AUTORIZ="3516201234567",
                AP_PRIPAL="0301120056", AP_VL_AP="               40.00", AP_UFMUN="353870", AP_TPUPS="05",
                AP_TPPRE="00", AP_TPATEND="05", AP_TPAPAC="1", AP_MNDIF="1", AP_DTINIC="20160601",
                AP_DTFIM="20160831", AP_APACAN="0000000000000", AP_CIDCAS="0000", CO_CIDPRIM="0000",
                CO_CIDSEC="0000", AB_PROCAIH="0407010173", AB_DTCIRUR="20150310", AB_NUMAIH="3515101234567",
                AB_T_PRC2="000", AB_MESACOM="12", AB_ANOACOM="2", AP_COMORB="S", AP_CID_C1="I10",
                AP_MEDICAM="1", AP_POLIVIT="0", AP_ATV_FIS="1", AP_REG_PES="0", AP_ADESAO="1",
                AP_NATJUR="3999")
    base.update(kw)
    return [base[name] for name, _ in fields]


def test_abo_layout():
    assert len(ABO_FIELDS) == 77 and len(FIELDS_NATJUR) == 78
    assert sum(w for _, w in ABO_FIELDS) + 1 == 403  # record length of ABOSP1401.dbc ... ABOSP1606.dbc
    assert sum(w for _, w in FIELDS_NATJUR) + 1 == 407  # ABOSP1410.dbc, ABOSP1607.dbc ... ABOSP2608.dbc


def test_abo_registered():
    abo = c.REGISTRY["ABO"]
    assert abo is c.ABO and list(c.REGISTRY)[:12] == [
        "PA", "BI", "AM", "AQ", "AR", "AD", "ATD", "AN", "PS", "SAD", "AB", "ABO"]
    assert c.DEFAULT_TABLES == ("PA",)
    assert [(e.key, e.ftp_dir, e.first, e.last) for e in abo.eras] == [("abo", c.FTP_CURRENT_DIR, 201401, 999912)]
    assert abo.eras[0].quantity_cols == () and abo.eras[0].value_cols == ("AP_VL_AP",)
    assert c.parse_tables("abo") == [abo] and c.parse_tables("ab,abo") == [c.AB, abo]
    assert abo.era_for(201401).key == abo.era_for(202608).key == "abo"
    with pytest.raises(ValueError):
        abo.era_for(201312)


def test_abo_dictionary_covers_every_column():
    cols = {name for name, _ in FIELDS_NATJUR} | {"competencia", "uf", "_ARQUIVO_ORIGEM"}
    assert set(dictionary.ABO) == cols
    assert all(desc.strip() and "TODO" not in desc for desc in dictionary.ABO.values())
    # the shared AP_ columns, six of them under other names
    shared = set(dictionary.APAC_COMMON)
    assert {name for name, _ in FIELDS_NATJUR} & shared == shared - set(RENAMED)
    assert all(new in dictionary.ABO and old not in dictionary.ABO for old, new in RENAMED.items())
    assert all(old in dictionary.ABO[new] for old, new in RENAMED.items() if old not in ("AP_CIDPRI", "AP_CIDSEC"))
    own = {name for name, _ in ABO_FIELDS} - shared - set(RENAMED.values())
    assert len(own) == 32 and len([n for n in own if n.startswith("AB_")]) == 20
    assert dictionary.ABO["AP_MVM"] == dictionary.APAC_COMMON["AP_MVM"]
    assert "0301120056" in dictionary.ABO["AP_PRIPAL"]
    # the checked quirks are documented
    assert "Always empty" in dictionary.ABO["AB_IMC"] and "MAMMOPLASTY" in dictionary.ABO["AB_PRCAIH3"]
    assert "Swapped" in dictionary.ABO["AP_POLIVIT"] and "Swapped" in dictionary.ABO["AP_ATV_FIS"]
    assert "Oct/2014" in dictionary.ABO["AP_NATJUR"]
    assert "ABOSP1606.dbc" in dictionary.ABO["_ARQUIVO_ORIGEM"]


@pytest.mark.parametrize("name,uf,comp", [
    ("ABOSP1401.dbc", "SP", 201401),
    ("ABOPR2608.DBC", "PR", 202608),
    ("ABOPE1112.dbc", "PE", 201112),  # name parses; the era starts in 2014
    ("ABOAC2504.dbc", "AC", 202504),
])
def test_abo_names(name, uf, comp):
    rf = c.parse_name(name, 5)
    assert (rf.table, rf.uf, rf.competencia, rf.part) == ("ABO", uf, comp, "")


@pytest.mark.parametrize("name", [
    "ABSP1606.dbc",  # AB
    "ABPE1606.dbc", "ABOXX1606.dbc", "ABOSP1613.dbc", "ABOSP1606.dbf", "ACFSP1606.dbc",
])
def test_abo_rejects(name):
    assert c.ABO.parse(name) is None


def test_others_do_not_claim_abo():
    assert all(ft.parse("ABOSP1606.dbc") is None for ft in c.REGISTRY.values() if ft is not c.ABO)
    assert c.parse_name("ABOPE1606.dbc", 1).table == "ABO" and c.parse_name("ABPE1606.dbc", 1).table == "AB"


def test_abo_conversion_and_view(make_dbf, tmp_path):
    store = Store(tmp_path / "data")
    p = c.group([c.parse_name("ABOSP1606.dbc", 10)])[0]
    built = store.tmp / "b"
    built.mkdir(parents=True)
    dbf = make_dbf("ABOSP1606.dbf", ABO_FIELDS, [
        row(),
        row(AP_AUTORIZ="3516209999998", AP_CMP="201605", AP_TPAPAC="2", AP_VL_AP="                0.00",
            AB_PRCAIH3="0413040070", AB_T_PRC3="036", AP_COMORB="N", AP_CID_C1=""),  # late, continuation
        row(AP_AUTORIZ="3516209999999", AP_VL_AP="x"),  # malformed: NULL in the typed view, kept in _raw
    ])
    assert convert.dbf_to_parquet(dbf, built / "ABOSP1606.parquet", origin="ABOSP1606.dbc") == 3
    store.record(p, 3, store.publish(p, built))

    con = query.connect(store)
    assert {"abo", "abo_raw"} <= set(query.views(con))
    types = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                             "WHERE table_name = 'abo'").fetchall())
    assert types["AP_VL_AP"] == "DOUBLE" and types["competencia"] == "INTEGER"
    assert types["AB_PROCAIH"] == types["AP_CID_C1"] == types["AP_MEDICAM"] == "VARCHAR"
    assert "AP_TIPPRE" not in types and types["AP_TPPRE"] == "VARCHAR"
    assert con.execute("SELECT ROUND(SUM(AP_VL_AP), 2), COUNT(*) FILTER (WHERE AP_VL_AP IS NULL), "
                       "MIN(uf), MIN(competencia), MIN(_ARQUIVO_ORIGEM) FROM abo").fetchone() == (
        40.0, 1, "SP", 201606, "ABOSP1606.dbc")
    assert con.execute("SELECT AP_VL_AP FROM abo_raw WHERE AP_VL_AP = 'x'").fetchone() == ("x",)
    # empty fields are NULL; the flag columns are text
    assert con.execute("SELECT AB_IMC, AP_CID_C1, AB_PRCAIH3, AB_T_PRC3 FROM abo WHERE AP_CMP = '201605'"
                       ).fetchone() == (None, None, "0413040070", "036")
    assert con.execute("SELECT COUNT(*) FILTER (WHERE AP_CID_C1 = 'I10'), COUNT(*) FILTER (WHERE AP_COMORB = 'S') "
                       "FROM abo").fetchone() == (2, 2)


def test_abo_natjur_in_oct_2014_and_from_jul_2016(make_dbf, tmp_path):
    """77 columns, 78 (AP_NATJUR, appended last) in Oct/2014 and from Jul/2016."""
    store = Store(tmp_path / "data")
    for name, fields in (("ABOSP1409", ABO_FIELDS), ("ABOSP1410", FIELDS_NATJUR), ("ABOSP1606", ABO_FIELDS),
                         ("ABOSP1607", FIELDS_NATJUR)):
        p = c.group([c.parse_name(name + ".dbc", 10)])[0]
        built = store.tmp / name
        built.mkdir(parents=True)
        convert.dbf_to_parquet(make_dbf(name + ".dbf", fields, [row(fields)]), built / (name + ".parquet"),
                               name + ".dbc")
        store.record(p, 1, store.publish(p, built))
    con = query.connect(store)
    assert con.execute("SELECT competencia, AP_NATJUR, AB_PROCAIH FROM abo ORDER BY 1").fetchall() == [
        (201409, None, "0407010173"), (201410, "3999", "0407010173"), (201606, None, "0407010173"),
        (201607, "3999", "0407010173")]
