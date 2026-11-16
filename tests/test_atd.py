"""ATD (APAC Tratamento Dialítico): registry entry, dictionary, conversion and typed view."""
import pytest

from intrepid_datasus import catalog as c, convert, dictionary, query
from intrepid_datasus.store import Store

# The 65 columns of a real file (ATDSP2608.dbc), with their DBF widths: the 45 shared APAC
# columns, 19 ATD_ columns, then AP_NATJUR (last). AP_VL_AP is a numeric (N) field 20 wide;
# the converter reads every field as text. Files before Jul/2016 have no AP_NATJUR (64 columns).
ATD_FIELDS = [
    ("AP_MVM", 6), ("AP_CONDIC", 2), ("AP_GESTAO", 6), ("AP_CODUNI", 7), ("AP_AUTORIZ", 13),
    ("AP_CMP", 6), ("AP_PRIPAL", 10), ("AP_VL_AP", 20), ("AP_UFMUN", 6), ("AP_TPUPS", 2),
    ("AP_TIPPRE", 2), ("AP_MN_IND", 1), ("AP_CNPJCPF", 14), ("AP_CNPJMNT", 14), ("AP_CNSPCN", 15),
    ("AP_COIDADE", 1), ("AP_NUIDADE", 2), ("AP_SEXO", 1), ("AP_RACACOR", 2), ("AP_MUNPCN", 6),
    ("AP_UFNACIO", 3), ("AP_CEPPCN", 8), ("AP_UFDIF", 1), ("AP_MNDIF", 1), ("AP_DTINIC", 8),
    ("AP_DTFIM", 8), ("AP_TPATEN", 2), ("AP_TPAPAC", 1), ("AP_MOTSAI", 2), ("AP_OBITO", 1),
    ("AP_ENCERR", 1), ("AP_PERMAN", 1), ("AP_ALTA", 1), ("AP_TRANSF", 1), ("AP_DTOCOR", 8),
    ("AP_CODEMI", 10), ("AP_CATEND", 2), ("AP_APACANT", 13), ("AP_UNISOL", 7), ("AP_DTSOLIC", 8),
    ("AP_DTAUT", 8), ("AP_CIDCAS", 4), ("AP_CIDPRI", 4), ("AP_CIDSEC", 4), ("AP_ETNIA", 4),
    ("ATD_CARACT", 1), ("ATD_DTPDR", 8), ("ATD_DTCLI", 8), ("ATD_ACEVAS", 1), ("ATD_MAISNE", 1),
    ("ATD_SITINI", 1), ("ATD_SITTRA", 1), ("ATD_SEAPTO", 1), ("ATD_HB", 4), ("ATD_FOSFOR", 4),
    ("ATD_KTVSEM", 4), ("ATD_TRU", 4), ("ATD_ALBUMI", 4), ("ATD_PTH", 4), ("ATD_HIV", 1),
    ("ATD_HCV", 1), ("ATD_HBSAG", 1), ("ATD_INTERC", 1), ("ATD_SEPERI", 1),
    ("AP_NATJUR", 4),
]
FIELDS_2014 = [f for f in ATD_FIELDS if f[0] != "AP_NATJUR"]  # 64 columns, Aug/2014 to Jun/2016


def row(fields=ATD_FIELDS, **kw):
    base = {name: "" for name, _ in ATD_FIELDS}
    base.update(AP_MVM="202605", AP_CMP="202605", AP_CODUNI="2077485", AP_AUTORIZ="3526201234567",
                AP_PRIPAL="0305010107", AP_VL_AP="             3112.38", AP_UFMUN="355030", AP_TPATEN="10",
                AP_TPAPAC="2", AP_DTINIC="20260501", AP_DTFIM="20260731", AP_CIDPRI="N180",
                ATD_CARACT="2", ATD_DTPDR="20190415", ATD_DTCLI="20190912", ATD_ACEVAS="1",
                ATD_SITTRA="1", ATD_SEAPTO="1", ATD_HB="12.3", ATD_FOSFOR="05.5", ATD_KTVSEM="1.38",
                ATD_TRU="69.5", ATD_ALBUMI="03.9", ATD_PTH="1325", ATD_HIV="N", ATD_HCV="N",
                ATD_HBSAG="N", ATD_INTERC="N", ATD_SEPERI="N", AP_NATJUR="2062")
    base.update(kw)
    return [base[name] for name, _ in fields]


def test_atd_layout():
    assert len(ATD_FIELDS) == 65 and len(FIELDS_2014) == 64
    assert ATD_FIELDS[-1][0] == "AP_NATJUR"  # appended after the ATD_ columns, not with the AP_ ones
    assert sum(w for _, w in ATD_FIELDS) + 1 == 303  # record length of ATDSP2608.dbc
    assert sum(w for _, w in FIELDS_2014) + 1 == 299  # record length of ATDSP1408.dbc / ATDSP1606.dbc


def test_atd_registered():
    atd = c.REGISTRY["ATD"]
    assert atd is c.ATD and list(c.REGISTRY)[:7] == ["PA", "BI", "AM", "AQ", "AR", "AD", "ATD"]
    assert c.DEFAULT_TABLES == ("PA",)
    assert [(e.key, e.ftp_dir, e.first, e.last) for e in atd.eras] == [("atd", c.FTP_CURRENT_DIR, 201408, 999912)]
    assert atd.eras[0].quantity_cols == () and atd.eras[0].value_cols == ("AP_VL_AP",)
    assert c.parse_tables("atd") == [atd] and c.parse_tables("ad,atd") == [c.AD, atd]
    assert c.parse_tables("all")[:7] == [c.PA, c.BI, c.AM, c.AQ, c.AR, c.AD, atd]
    assert atd.era_for(201408).key == "atd"
    with pytest.raises(ValueError):
        atd.era_for(201407)  # dialysis before Aug/2014 is in AN


def test_atd_dictionary_covers_every_column():
    cols = {name for name, _ in ATD_FIELDS} | {"competencia", "uf", "_ARQUIVO_ORIGEM"}
    assert set(dictionary.ATD) == cols
    assert all(desc.strip() and "TODO" not in desc for desc in dictionary.ATD.values())
    own = {name for name, _ in ATD_FIELDS if name.startswith("ATD_")}
    assert len(own) == 19 and {name for name, _ in ATD_FIELDS} - own == set(dictionary.APAC_COMMON)
    assert dictionary.ATD["AP_MVM"] == dictionary.APAC_COMMON["AP_MVM"]
    assert dictionary.ATD["AP_PRIPAL"] != dictionary.APAC_COMMON["AP_PRIPAL"]  # ATD-specific notes
    assert "ATDSP2605.dbc" in dictionary.ATD["_ARQUIVO_ORIGEM"]


@pytest.mark.parametrize("name,uf,comp", [
    ("ATDAC2605.dbc", "AC", 202605),
    ("ATDSP1408.DBC", "SP", 201408),
    ("ATDAP2608.dbc", "AP", 202608),
    ("ATDTO1607.dbc", "TO", 201607),
])
def test_atd_names(name, uf, comp):
    rf = c.parse_name(name, 5)
    assert (rf.table, rf.uf, rf.competencia, rf.part) == ("ATD", uf, comp, "")


@pytest.mark.parametrize("name", [
    "ATDXX2605.dbc", "ATDSP2613.dbc", "ATDSP2605.dbf", "ATSP2605.dbc", "ADSP2605.dbc", "ANSP1408.dbc",
])
def test_atd_rejects(name):
    assert c.ATD.parse(name) is None


def test_ad_does_not_claim_atd():
    assert c.AD.parse("ATDSP2605.dbc") is None and c.parse_name("ATDSP2605.dbc", 1).table == "ATD"


def test_atd_conversion_and_view(make_dbf, tmp_path):
    store = Store(tmp_path / "data")
    p = c.group([c.parse_name("ATDSP2605.dbc", 10)])[0]
    built = store.tmp / "b"
    built.mkdir(parents=True)
    dbf = make_dbf("ATDSP2605.dbf", ATD_FIELDS, [
        row(),
        row(AP_CMP="202604", AP_PRIPAL="0305010166", AP_VL_AP="             2849.70",  # late billing of April
            ATD_ACEVAS="3", ATD_HB="07,8", ATD_PTH="", ATD_SEPERI="S"),  # comma decimal, no PTH
        row(AP_AUTORIZ="3526209999999", AP_VL_AP="x"),  # malformed: NULL in the typed view, kept in _raw
    ])
    assert convert.dbf_to_parquet(dbf, built / "ATDSP2605.parquet", origin="ATDSP2605.dbc") == 3
    store.record(p, 3, store.publish(p, built))

    con = query.connect(store)
    assert {"atd", "atd_raw"} <= set(query.views(con))
    types = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                             "WHERE table_name = 'atd'").fetchall())
    assert types["AP_VL_AP"] == "DOUBLE" and types["competencia"] == "INTEGER"
    # lab values stay text: their format varies (12.3, 07,8, 0123, 0000), see docs/databases/sia/atd.md
    assert types["ATD_HB"] == types["ATD_PTH"] == types["ATD_CARACT"] == types["AP_NATJUR"] == "VARCHAR"
    assert con.execute("SELECT ROUND(SUM(AP_VL_AP), 2), COUNT(*) FILTER (WHERE AP_VL_AP IS NULL), "
                       "COUNT(DISTINCT (AP_AUTORIZ, AP_CMP)), MIN(uf), MIN(competencia), MIN(_ARQUIVO_ORIGEM) "
                       "FROM atd").fetchone() == (5962.08, 1, 3, "SP", 202605, "ATDSP2605.dbc")
    assert con.execute("SELECT AP_VL_AP FROM atd_raw WHERE AP_VL_AP = 'x'").fetchone() == ("x",)
    assert con.execute("SELECT AP_PRIPAL, ATD_ACEVAS, ATD_HB, ATD_PTH, ATD_SEPERI FROM atd "
                       "WHERE AP_CMP = '202604'").fetchone() == ("0305010166", "3", "07,8", None, "S")


def test_atd_natjur_added_in_one_view(make_dbf, tmp_path):
    """64 columns until Jun/2016, 65 (AP_NATJUR, appended after the ATD_ columns) since."""
    store = Store(tmp_path / "data")
    for name, fields in (("ATDSP1606", FIELDS_2014), ("ATDSP1607", ATD_FIELDS)):
        p = c.group([c.parse_name(name + ".dbc", 10)])[0]
        built = store.tmp / name
        built.mkdir(parents=True)
        convert.dbf_to_parquet(make_dbf(name + ".dbf", fields, [row(fields)]), built / (name + ".parquet"),
                               name + ".dbc")
        store.record(p, 1, store.publish(p, built))
    con = query.connect(store)
    assert con.execute("SELECT competencia, AP_NATJUR, ATD_KTVSEM FROM atd ORDER BY 1").fetchall() == [
        (201606, None, "1.38"), (201607, "2062", "1.38")]
