"""SAD (RAAS Atenção Domiciliar): registry entry, dictionary, conversion and typed view."""
import pytest

from intrepid_datasus import catalog as c, convert, dictionary, query
from intrepid_datasus.store import Store

# The 43 columns of a real file (SADSP1204.dbc ... SADSP1412.dbc), with their DBF widths, in file
# order (every one of the 1,088 files probed). CO_INE is appended from Jan/2015 (44 columns,
# SADSP1501.dbc ... SADSP1606.dbc) and NAT_JUR after it (45) in Oct/2014 and from Jul/2016 to the
# last file (SADMA1810.dbc).
SAD_FIELDS = [
    ("CNES_EXEC", 7), ("GESTAO", 6), ("CONDIC", 2), ("UFMUN", 6), ("TPUPS", 2), ("MN_IND", 1),
    ("CNPJCPF", 14), ("CNPJMNT", 14), ("DT_PROCESS", 6), ("DT_ATEND", 6), ("CNS_PAC", 15),
    ("DTNASC", 8), ("TPIDADEPAC", 1), ("IDADEPAC", 2), ("NACION_PAC", 2), ("SEXOPAC", 1),
    ("RACACOR", 2), ("ETNIA", 2), ("MUNPAC", 6), ("MOT_COB", 2), ("DT_MOTCOB", 8), ("CATEND", 2),
    ("CIDPRI", 4), ("CIDASSOC", 4), ("ORIGEM_PAC", 2), ("DT_INICIO", 8), ("DT_FIM", 8), ("COB_ESF", 1),
    ("CNES_ESF", 7), ("DESTINOPAC", 2), ("PA_PROC_ID", 10), ("PA_QTDPRO", 11), ("PA_QTDAPR", 11),
    ("PA_SRV", 3), ("PA_CLASS_S", 3), ("PA_EQUIPE", 12), ("PA_TP_EQP", 2), ("PA_CID", 4),
    ("INICIO", 8), ("FIM", 8), ("PERMANEN", 4), ("QTDATE", 4), ("QTDPCN", 4),
]
FIELDS_INE = SAD_FIELDS + [("CO_INE", 10)]  # Jan/2015 - Jun/2016
FIELDS_NATJUR = FIELDS_INE + [("NAT_JUR", 4)]  # Oct/2014, and Jul/2016 - Oct/2018
NAMES = [name for name, _ in FIELDS_NATJUR]
SAD_ONLY = {"PA_EQUIPE", "PA_TP_EQP", "PA_CID", "CO_INE"}


def row(fields=SAD_FIELDS, **kw):
    base = dict.fromkeys(NAMES, "")
    base.update(CNES_EXEC="2077485", UFMUN="355030", TPUPS="05", DT_PROCESS="201505",
                DT_ATEND="201505", CNS_PAC="{{{{{{{{{{{{{{{", PA_PROC_ID="0301050074", PA_QTDPRO="3",
                PA_QTDAPR="3", PA_SRV="113", PA_CLASS_S="001", PA_EQUIPE="000000012345", PA_TP_EQP="22",
                PA_CID="I64", CIDPRI="I64", QTDATE="0001", QTDPCN="0001", CO_INE="0000123456",
                NAT_JUR="1244")
    base.update(kw)
    return [base[name] for name, _ in fields]


def test_sad_layout():
    assert len(SAD_FIELDS) == 43 and len(FIELDS_INE) == 44 and len(FIELDS_NATJUR) == 45
    assert sum(w for _, w in SAD_FIELDS) + 1 == 236  # record length of SADSP1204.dbc ... SADSP1412.dbc
    assert sum(w for _, w in FIELDS_INE) + 1 == 246  # SADSP1501.dbc ... SADSP1606.dbc
    assert sum(w for _, w in FIELDS_NATJUR) + 1 == 250  # SADSP1410.dbc, SADSP1607.dbc ... SADMA1810.dbc


def test_sad_registered():
    sad = c.REGISTRY["SAD"]
    assert sad is c.SAD and list(c.REGISTRY)[:10] == [
        "PA", "BI", "AM", "AQ", "AR", "AD", "ATD", "AN", "PS", "SAD"]
    assert c.DEFAULT_TABLES == ("PA",)
    assert [(e.key, e.ftp_dir, e.first, e.last) for e in sad.eras] == [
        ("sad", c.FTP_CURRENT_DIR, 201204, 201810)]
    assert sad.eras[0].quantity_cols == ("PA_QTDPRO", "PA_QTDAPR") and sad.eras[0].value_cols == ()
    assert c.parse_tables("sad") == [sad] and c.parse_tables("ps,sad") == [c.PS, sad]
    assert sad.era_for(201204).key == sad.era_for(201810).key == "sad"
    for month in (201203, 201811):  # first file Apr/2012; discontinued after Oct/2018
        with pytest.raises(ValueError):
            sad.era_for(month)


def test_sad_dictionary_covers_every_column():
    cols = set(NAMES) | {"competencia", "uf", "_ARQUIVO_ORIGEM"}
    assert set(dictionary.SAD) == cols
    assert all(desc.strip() and "TODO" not in desc for desc in dictionary.SAD.values())
    # every SAD column except its own four is a shared RAAS column, the same set as in PS
    assert set(NAMES) - SAD_ONLY == set(dictionary.RAAS_COMMON)
    assert not SAD_ONLY & set(dictionary.PS)
    assert not any(k.startswith("AP_") for k in dictionary.SAD)  # RAAS, not APAC
    assert dictionary.SAD["DT_PROCESS"] == dictionary.PS["DT_PROCESS"] == dictionary.RAAS_COMMON["DT_PROCESS"]
    assert "Oct/2014" in dictionary.SAD["NAT_JUR"] and "Jan/2015" in dictionary.SAD["CO_INE"]


@pytest.mark.parametrize("name,uf,comp", [
    ("SADAC1307.dbc", "AC", 201307),
    ("SADSP1204.DBC", "SP", 201204),
    ("SADMA1810.dbc", "MA", 201810),  # the last file
    ("SADPE1410.dbc", "PE", 201410),
    ("SADDF1505.dbc", "DF", 201505),
])
def test_sad_names(name, uf, comp):
    rf = c.parse_name(name, 5)
    assert (rf.table, rf.uf, rf.competencia, rf.part) == ("SAD", uf, comp, "")


@pytest.mark.parametrize("name", [
    "SADXX1405.dbc", "SADSP1413.dbc", "SADSP1405.dbf", "PSSP1405.dbc", "SASP1405.dbc", "SADDSP1405.dbc",
])
def test_sad_rejects(name):
    assert c.SAD.parse(name) is None


def test_others_do_not_claim_sad():
    assert all(ft.parse("SADSP1405.dbc") is None for ft in c.REGISTRY.values() if ft is not c.SAD)


def test_sad_conversion_and_view(make_dbf, tmp_path):
    store = Store(tmp_path / "data")
    p = c.group([c.parse_name("SADSP1505.dbc", 10)])[0]
    built = store.tmp / "b"
    built.mkdir(parents=True)
    dbf = make_dbf("SADSP1505.dbf", FIELDS_INE, [
        row(FIELDS_INE),
        row(FIELDS_INE, DT_ATEND="201504", PA_PROC_ID="0301050023", PA_QTDPRO="2", PA_QTDAPR="1",
            QTDATE="0000", QTDPCN="0000"),
        row(FIELDS_INE, PA_QTDPRO="x"),  # malformed: NULL in the typed view, kept in _raw
    ])
    assert convert.dbf_to_parquet(dbf, built / "SADSP1505.parquet", origin="SADSP1505.dbc") == 3
    store.record(p, 3, store.publish(p, built))

    con = query.connect(store)
    assert {"sad", "sad_raw"} <= set(query.views(con))
    types = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                             "WHERE table_name = 'sad'").fetchall())
    assert types["PA_QTDPRO"] == types["PA_QTDAPR"] == "BIGINT" and types["competencia"] == "INTEGER"
    assert types["QTDATE"] == types["PA_EQUIPE"] == types["CO_INE"] == "VARCHAR"
    assert con.execute("SELECT SUM(PA_QTDPRO), SUM(PA_QTDAPR), COUNT(*) FILTER (WHERE PA_QTDPRO IS NULL), "
                       "MIN(uf), MIN(competencia), MIN(_ARQUIVO_ORIGEM), MIN(CO_INE) FROM sad").fetchone() == (
        5, 7, 1, "SP", 201505, "SADSP1505.dbc", "0000123456")
    assert con.execute("SELECT PA_QTDPRO FROM sad_raw WHERE PA_QTDPRO = 'x'").fetchone() == ("x",)
    assert con.execute("SELECT PA_PROC_ID FROM sad WHERE DT_ATEND = '201504'").fetchone() == ("0301050023",)


def test_sad_column_sets(make_dbf, tmp_path):
    """43 columns until Dec/2014, + CO_INE from Jan/2015, + NAT_JUR in Oct/2014 and from Jul/2016."""
    store = Store(tmp_path / "data")
    for name, fields in (("SADSP1409", SAD_FIELDS), ("SADSP1410", FIELDS_NATJUR), ("SADSP1411", SAD_FIELDS),
                         ("SADSP1501", FIELDS_INE), ("SADSP1607", FIELDS_NATJUR)):
        p = c.group([c.parse_name(name + ".dbc", 10)])[0]
        built = store.tmp / name
        built.mkdir(parents=True)
        convert.dbf_to_parquet(make_dbf(name + ".dbf", fields, [row(fields)]), built / (name + ".parquet"),
                               name + ".dbc")
        store.record(p, 1, store.publish(p, built))
    con = query.connect(store)
    assert con.execute("SELECT competencia, CO_INE, NAT_JUR, PA_EQUIPE FROM sad ORDER BY 1").fetchall() == [
        (201409, None, None, "000000012345"), (201410, "0000123456", "1244", "000000012345"),
        (201411, None, None, "000000012345"), (201501, "0000123456", None, "000000012345"),
        (201607, "0000123456", "1244", "000000012345")]
