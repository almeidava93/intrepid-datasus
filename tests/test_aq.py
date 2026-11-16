"""AQ (APAC Quimioterapia): registry entry, dictionary, conversion and typed view."""
import pytest

from intrepid_datasus import catalog as c, convert, dictionary, query
from intrepid_datasus.store import Store

# The 74 columns of a real file (AQAC2605.dbc), with their DBF widths. AP_VL_AP is a numeric
# (N) field in the DBF; the converter reads every field as text. Files before Jul/2016 lack
# AP_NATJUR, and files before Jan/2021 lack AQ_MED01..AQ_MED10 (63 and 64 columns).
AQ_OWN = [
    ("AQ_CID10", 4), ("AQ_LINFIN", 1), ("AQ_ESTADI", 1), ("AQ_GRAHIS", 2), ("AQ_DTIDEN", 8),
    ("AQ_TRANTE", 1), ("AQ_CIDINI1", 4), ("AQ_DTINI1", 8), ("AQ_CIDINI2", 4), ("AQ_DTINI2", 8),
    ("AQ_CIDINI3", 4), ("AQ_DTINI3", 8), ("AQ_CONTTR", 1), ("AQ_DTINTR", 8), ("AQ_ESQU_P1", 5),
    ("AQ_TOTMPL", 3), ("AQ_TOTMAU", 3), ("AQ_ESQU_P2", 10),
]
AQ_MEDS = [(f"AQ_MED{i:02d}", 3) for i in range(1, 11)]
AQ_FIELDS = [
    ("AP_MVM", 6), ("AP_CONDIC", 2), ("AP_GESTAO", 6), ("AP_CODUNI", 7), ("AP_AUTORIZ", 13),
    ("AP_CMP", 6), ("AP_PRIPAL", 10), ("AP_VL_AP", 12), ("AP_UFMUN", 6), ("AP_TPUPS", 2),
    ("AP_TIPPRE", 2), ("AP_MN_IND", 1), ("AP_CNPJCPF", 14), ("AP_CNPJMNT", 14), ("AP_CNSPCN", 15),
    ("AP_COIDADE", 1), ("AP_NUIDADE", 2), ("AP_SEXO", 1), ("AP_RACACOR", 2), ("AP_MUNPCN", 6),
    ("AP_UFNACIO", 3), ("AP_CEPPCN", 8), ("AP_UFDIF", 1), ("AP_MNDIF", 1), ("AP_DTINIC", 8),
    ("AP_DTFIM", 8), ("AP_TPATEN", 2), ("AP_TPAPAC", 1), ("AP_MOTSAI", 2), ("AP_OBITO", 1),
    ("AP_ENCERR", 1), ("AP_PERMAN", 1), ("AP_ALTA", 1), ("AP_TRANSF", 1), ("AP_DTOCOR", 8),
    ("AP_CODEMI", 10), ("AP_CATEND", 2), ("AP_APACANT", 13), ("AP_UNISOL", 7), ("AP_DTSOLIC", 8),
    ("AP_DTAUT", 8), ("AP_CIDCAS", 4), ("AP_CIDPRI", 4), ("AP_CIDSEC", 4), ("AP_ETNIA", 4),
    *AQ_OWN, *AQ_MEDS, ("AP_NATJUR", 4),
]
FIELDS_2008 = [f for f in AQ_FIELDS if f not in AQ_MEDS and f[0] != "AP_NATJUR"]  # 63 columns
FIELDS_2016 = [f for f in AQ_FIELDS if f not in AQ_MEDS]                         # 64 columns


def row(fields=AQ_FIELDS, **kw):
    base = {name: "" for name, _ in AQ_FIELDS}
    base.update(AP_MVM="202605", AP_CMP="202605", AP_CODUNI="2001063", AP_AUTORIZ="1226200113413",
                AP_PRIPAL="0304050121", AP_VL_AP="      571.50", AP_UFMUN="120040", AP_TPATEN="03",
                AP_TPAPAC="1", AP_DTINIC="20260507", AP_DTFIM="20260731", AP_CIDPRI="C504",
                AQ_ESTADI="2", AQ_LINFIN="S", AQ_DTIDEN="20250918", AQ_CONTTR="S", AQ_DTINTR="20251020",
                AQ_ESQU_P1="ANAST", AQ_ESQU_P2="ROZOL", AQ_TOTMPL="060", AQ_TOTMAU="009", AQ_MED01="011",
                AP_NATJUR="1023")
    base.update(kw)
    return [base[name] for name, _ in fields]


def test_aq_layout():
    assert len(AQ_FIELDS) == 74 and len(FIELDS_2016) == 64 and len(FIELDS_2008) == 63
    assert sum(w for _, w in AQ_FIELDS) + 1 == 357  # record length of AQAC2605.dbc


def test_aq_registered():
    aq = c.REGISTRY["AQ"]
    assert aq is c.AQ and list(c.REGISTRY)[:4] == ["PA", "BI", "AM", "AQ"] and c.DEFAULT_TABLES == ("PA",)
    assert [(e.key, e.ftp_dir, e.first, e.last) for e in aq.eras] == [("aq", c.FTP_CURRENT_DIR, 200801, 999912)]
    assert aq.eras[0].quantity_cols == () and aq.eras[0].value_cols == ("AP_VL_AP",)
    assert c.parse_tables("aq") == [aq] and c.parse_tables("am,aq") == [c.AM, aq]
    assert c.parse_tables("all")[:4] == [c.PA, c.BI, c.AM, aq]
    with pytest.raises(ValueError):
        aq.era_for(200712)


def test_aq_dictionary_covers_every_column():
    cols = {name for name, _ in AQ_FIELDS} | {"competencia", "uf", "_ARQUIVO_ORIGEM"}
    assert set(dictionary.AQ) == cols
    assert all(desc.strip() for desc in dictionary.AQ.values())
    ap = {name for name, _ in AQ_FIELDS if name.startswith("AP_")}
    assert ap == set(dictionary.APAC_COMMON)  # every shared APAC column, none renamed
    assert dictionary.AQ["AP_MVM"] == dictionary.APAC_COMMON["AP_MVM"]
    assert "always 03" in dictionary.AQ["AP_TPATEN"] and "AQSP2605.dbc" in dictionary.AQ["_ARQUIVO_ORIGEM"]


@pytest.mark.parametrize("name,uf,comp", [
    ("AQAC2605.dbc", "AC", 202605),
    ("AQSP0801.DBC", "SP", 200801),
    ("AQSP2507.dbc", "SP", 202507),  # the largest AQ file
    ("AQPA2101.dbc", "PA", 202101),
])
def test_aq_names(name, uf, comp):
    rf = c.parse_name(name, 5)
    assert (rf.table, rf.uf, rf.competencia, rf.part) == ("AQ", uf, comp, "")


@pytest.mark.parametrize("name", [
    "AQXX2605.dbc", "AQSP2613.dbc", "AQSP2605.dbf", "AMSP2605.dbc", "ARSP2605.dbc",
])
def test_aq_rejects(name):
    assert c.AQ.parse(name) is None


def test_aq_conversion_and_view(make_dbf, tmp_path):
    store = Store(tmp_path / "data")
    p = c.group([c.parse_name("AQAC2605.dbc", 10)])[0]
    built = store.tmp / "b"
    built.mkdir(parents=True)
    dbf = make_dbf("AQAC2605.dbf", AQ_FIELDS, [
        row(),
        row(AP_AUTORIZ="1226200067180", AP_CMP="202604", AP_TPAPAC="2", AP_VL_AP="     5674.15",
            AP_PRIPAL="0304030252", AQ_MED01="029", AQ_MED02="120"),  # late billing of April
        row(AP_AUTORIZ="1226200108188", AP_VL_AP="x"),  # malformed: NULL in the typed view, kept in _raw
    ])
    assert convert.dbf_to_parquet(dbf, built / "AQAC2605.parquet", origin="AQAC2605.dbc") == 3
    store.record(p, 3, store.publish(p, built))

    con = query.connect(store)
    assert {"aq", "aq_raw"} <= set(query.views(con))
    types = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                             "WHERE table_name = 'aq'").fetchall())
    assert types["AP_VL_AP"] == "DOUBLE" and types["competencia"] == "INTEGER"
    assert types["AQ_ESTADI"] == types["AQ_TOTMPL"] == types["AQ_MED01"] == "VARCHAR"
    assert con.execute("SELECT SUM(AP_VL_AP), COUNT(*) FILTER (WHERE AP_VL_AP IS NULL), "
                       "COUNT(DISTINCT (AP_AUTORIZ, AP_CMP)), MIN(uf), MIN(competencia), MIN(_ARQUIVO_ORIGEM) "
                       "FROM aq").fetchone() == (6245.65, 1, 3, "AC", 202605, "AQAC2605.dbc")
    assert con.execute("SELECT AP_VL_AP FROM aq_raw WHERE AP_VL_AP = 'x'").fetchone() == ("x",)
    assert con.execute("SELECT AP_PRIPAL, AQ_TOTMPL, AQ_MED01, AQ_ESQU_P1 || AQ_ESQU_P2 FROM aq "
                       "WHERE AP_TPAPAC = '1' LIMIT 1").fetchone() == ("0304050121", "060", "011", "ANASTROZOL")


def test_aq_three_column_sets_in_one_view(make_dbf, tmp_path):
    """63 columns until Jun/2016, 64 (AP_NATJUR) until Dec/2020, 74 (AQ_MED01..10) since: one era,
    and the view shows NULL for the columns a month's file lacks."""
    store = Store(tmp_path / "data")
    for name, fields in (("AQAC1606", FIELDS_2008), ("AQAC2012", FIELDS_2016), ("AQAC2101", AQ_FIELDS)):
        p = c.group([c.parse_name(name + ".dbc", 10)])[0]
        built = store.tmp / name
        built.mkdir(parents=True)
        convert.dbf_to_parquet(make_dbf(name + ".dbf", fields, [row(fields)]), built / (name + ".parquet"),
                               name + ".dbc")
        store.record(p, 1, store.publish(p, built))
    con = query.connect(store)
    assert con.execute("SELECT competencia, AP_NATJUR, AQ_MED01, AQ_ESTADI FROM aq ORDER BY 1").fetchall() == [
        (201606, None, None, "2"), (202012, "1023", None, "2"), (202101, "1023", "011", "2")]
