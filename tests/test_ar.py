"""AR (APAC Radioterapia): registry entry, dictionary, conversion and typed view."""
import pytest

from intrepid_datasus import catalog as c, convert, dictionary, query
from intrepid_datasus.store import Store

# The 74 columns of a real file (ARSP2605.dbc), with their DBF widths. AP_VL_AP is a numeric
# (N) field in the DBF (20 wide here, 12 in AM/AQ); the converter reads every field as text.
# Files before Jul/2016 have the same columns without AP_NATJUR (73).
AR_OWN = [
    ("AR_SMRD", 3), ("AR_CID10", 4), ("AR_LINFIN", 1), ("AR_ESTADI", 1), ("AR_GRAHIS", 2),
    ("AR_DTIDEN", 8), ("AR_TRANTE", 1), ("AR_CIDINI1", 4), ("AR_DTINI1", 8), ("AR_CIDINI2", 4),
    ("AR_DTINI2", 8), ("AR_CIDINI3", 4), ("AR_DTINI3", 8), ("AR_CONTTR", 1), ("AR_DTINTR", 8),
    ("AR_FINALI", 1), ("AR_CIDTR1", 4), ("AR_CIDTR2", 4), ("AR_CIDTR3", 4), ("AR_NUMC1", 3),
    ("AR_INIAR1", 8), ("AR_INIAR2", 8), ("AR_INIAR3", 8), ("AR_FIMAR1", 8), ("AR_FIMAR2", 8),
    ("AR_FIMAR3", 8), ("AR_NUMC2", 3), ("AR_NUMC3", 3),
]
AR_FIELDS = [
    ("AP_MVM", 6), ("AP_CONDIC", 2), ("AP_GESTAO", 6), ("AP_CODUNI", 7), ("AP_AUTORIZ", 13),
    ("AP_CMP", 6), ("AP_PRIPAL", 10), ("AP_VL_AP", 20), ("AP_UFMUN", 6), ("AP_TPUPS", 2),
    ("AP_TIPPRE", 2), ("AP_MN_IND", 1), ("AP_CNPJCPF", 14), ("AP_CNPJMNT", 14), ("AP_CNSPCN", 15),
    ("AP_COIDADE", 1), ("AP_NUIDADE", 2), ("AP_SEXO", 1), ("AP_RACACOR", 2), ("AP_MUNPCN", 6),
    ("AP_UFNACIO", 3), ("AP_CEPPCN", 8), ("AP_UFDIF", 1), ("AP_MNDIF", 1), ("AP_DTINIC", 8),
    ("AP_DTFIM", 8), ("AP_TPATEN", 2), ("AP_TPAPAC", 1), ("AP_MOTSAI", 2), ("AP_OBITO", 1),
    ("AP_ENCERR", 1), ("AP_PERMAN", 1), ("AP_ALTA", 1), ("AP_TRANSF", 1), ("AP_DTOCOR", 8),
    ("AP_CODEMI", 10), ("AP_CATEND", 2), ("AP_APACANT", 13), ("AP_UNISOL", 7), ("AP_DTSOLIC", 8),
    ("AP_DTAUT", 8), ("AP_CIDCAS", 4), ("AP_CIDPRI", 4), ("AP_CIDSEC", 4), ("AP_ETNIA", 4),
    *AR_OWN, ("AP_NATJUR", 4),
]
FIELDS_2008 = [f for f in AR_FIELDS if f[0] != "AP_NATJUR"]  # 73 columns, until Jun/2016


def row(fields=AR_FIELDS, **kw):
    base = {name: "" for name, _ in AR_FIELDS}
    base.update(AP_MVM="202605", AP_CMP="202605", AP_CODUNI="2077485", AP_AUTORIZ="3526201234567",
                AP_PRIPAL="0304010421", AP_VL_AP="             2853.00", AP_UFMUN="355030", AP_TPATEN="04",
                AP_TPAPAC="1", AP_DTINIC="20260504", AP_DTFIM="20260731", AP_CIDPRI="C504",
                AR_CID10="C504", AR_ESTADI="2", AR_LINFIN="N", AR_DTIDEN="20251110", AR_CONTTR="N",
                AR_DTINTR="20260504", AR_FINALI="2", AR_CIDTR1="C504", AR_NUMC1="025",
                AR_INIAR1="20260504", AR_FIMAR1="20260605", AP_NATJUR="1023")
    base.update(kw)
    return [base[name] for name, _ in fields]


def test_ar_layout():
    assert len(AR_FIELDS) == 74 and len(FIELDS_2008) == 73
    assert sum(w for _, w in AR_FIELDS) + 1 == 387  # record length of ARSP2605.dbc
    assert sum(w for _, w in FIELDS_2008) + 1 == 383  # record length of ARSP1606.dbc


def test_ar_registered():
    ar = c.REGISTRY["AR"]
    assert ar is c.AR and list(c.REGISTRY)[:5] == ["PA", "BI", "AM", "AQ", "AR"] and c.DEFAULT_TABLES == ("PA",)
    assert [(e.key, e.ftp_dir, e.first, e.last) for e in ar.eras] == [("ar", c.FTP_CURRENT_DIR, 200801, 999912)]
    assert ar.eras[0].quantity_cols == () and ar.eras[0].value_cols == ("AP_VL_AP",)
    assert c.parse_tables("ar") == [ar] and c.parse_tables("aq,ar") == [c.AQ, ar]
    assert c.parse_tables("all")[:5] == [c.PA, c.BI, c.AM, c.AQ, ar]
    with pytest.raises(ValueError):
        ar.era_for(200712)


def test_ar_dictionary_covers_every_column():
    cols = {name for name, _ in AR_FIELDS} | {"competencia", "uf", "_ARQUIVO_ORIGEM"}
    assert set(dictionary.AR) == cols
    assert all(desc.strip() and "TODO" not in desc for desc in dictionary.AR.values())
    ap = {name for name, _ in AR_FIELDS if name.startswith("AP_")}
    assert ap == set(dictionary.APAC_COMMON)  # every shared APAC column, none renamed
    assert dictionary.AR["AP_MVM"] == dictionary.APAC_COMMON["AP_MVM"]
    assert "always 04" in dictionary.AR["AP_TPATEN"] and "ARSP2605.dbc" in dictionary.AR["_ARQUIVO_ORIGEM"]


@pytest.mark.parametrize("name,uf,comp", [
    ("ARAC2605.dbc", "AC", 202605),
    ("ARSP0801.DBC", "SP", 200801),
    ("ARAP2605.dbc", "AP", 202605),  # AP has only 9 AR files
    ("ARPA2101.dbc", "PA", 202101),
])
def test_ar_names(name, uf, comp):
    rf = c.parse_name(name, 5)
    assert (rf.table, rf.uf, rf.competencia, rf.part) == ("AR", uf, comp, "")


@pytest.mark.parametrize("name", [
    "ARXX2605.dbc", "ARSP2613.dbc", "ARSP2605.dbf", "AQSP2605.dbc", "ABSP2605.dbc",
])
def test_ar_rejects(name):
    assert c.AR.parse(name) is None


def test_ar_conversion_and_view(make_dbf, tmp_path):
    store = Store(tmp_path / "data")
    p = c.group([c.parse_name("ARSP2605.dbc", 10)])[0]
    built = store.tmp / "b"
    built.mkdir(parents=True)
    dbf = make_dbf("ARSP2605.dbf", AR_FIELDS, [
        row(),
        row(AP_CMP="202604", AP_TPAPAC="2", AP_VL_AP="              713.25"),  # late billing of April
        row(AP_AUTORIZ="3526209999999", AP_VL_AP="x"),  # malformed: NULL in the typed view, kept in _raw
    ])
    assert convert.dbf_to_parquet(dbf, built / "ARSP2605.parquet", origin="ARSP2605.dbc") == 3
    store.record(p, 3, store.publish(p, built))

    con = query.connect(store)
    assert {"ar", "ar_raw"} <= set(query.views(con))
    types = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                             "WHERE table_name = 'ar'").fetchall())
    assert types["AP_VL_AP"] == "DOUBLE" and types["competencia"] == "INTEGER"
    assert types["AR_NUMC1"] == types["AR_FINALI"] == types["AR_INIAR1"] == "VARCHAR"
    assert con.execute("SELECT SUM(AP_VL_AP), COUNT(*) FILTER (WHERE AP_VL_AP IS NULL), "
                       "COUNT(DISTINCT (AP_AUTORIZ, AP_CMP)), MIN(uf), MIN(competencia), MIN(_ARQUIVO_ORIGEM) "
                       "FROM ar").fetchone() == (3566.25, 1, 3, "SP", 202605, "ARSP2605.dbc")
    assert con.execute("SELECT AP_VL_AP FROM ar_raw WHERE AP_VL_AP = 'x'").fetchone() == ("x",)
    assert con.execute("SELECT AP_PRIPAL, AR_FINALI, AR_NUMC1, AR_CIDTR1 FROM ar "
                       "WHERE AP_CMP = '202605' LIMIT 1").fetchone() == ("0304010421", "2", "025", "C504")


def test_ar_natjur_added_in_one_view(make_dbf, tmp_path):
    """73 columns until Jun/2016, 74 (AP_NATJUR) since: one era, NULL before."""
    store = Store(tmp_path / "data")
    for name, fields in (("ARSP1606", FIELDS_2008), ("ARSP1607", AR_FIELDS)):
        p = c.group([c.parse_name(name + ".dbc", 10)])[0]
        built = store.tmp / name
        built.mkdir(parents=True)
        convert.dbf_to_parquet(make_dbf(name + ".dbf", fields, [row(fields)]), built / (name + ".parquet"),
                               name + ".dbc")
        store.record(p, 1, store.publish(p, built))
    con = query.connect(store)
    assert con.execute("SELECT competencia, AP_NATJUR, AR_NUMC1 FROM ar ORDER BY 1").fetchall() == [
        (201606, None, "025"), (201607, "1023", "025")]
