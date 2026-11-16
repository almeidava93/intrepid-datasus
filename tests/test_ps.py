"""PS (RAAS Psicossocial): registry entry, dictionary, conversion and typed view."""
import pytest

from intrepid_datasus import catalog as c, convert, dictionary, query
from intrepid_datasus.store import Store

# The 44 columns of a real file (PSSP1211.dbc ... PSSP1606.dbc), with their DBF widths, in file
# order. The DBF field name of TIPPRE is space-padded ("TIPPRE  "); the converter strips it.
# NAT_JUR is appended last (45 columns) in the Oct/2014 files and from Jul/2016 (PSSP2608.dbc).
PS_FIELDS = [
    ("CNES_EXEC", 7), ("GESTAO", 6), ("CONDIC", 2), ("UFMUN", 6), ("TPUPS", 2), ("TIPPRE  ", 2),
    ("MN_IND", 1), ("CNPJCPF", 14), ("CNPJMNT", 14), ("DT_PROCESS", 6), ("DT_ATEND", 6),
    ("CNS_PAC", 15), ("DTNASC", 8), ("TPIDADEPAC", 1), ("IDADEPAC", 2), ("NACION_PAC", 2),
    ("SEXOPAC", 1), ("RACACOR", 2), ("ETNIA", 2), ("MUNPAC", 6), ("MOT_COB", 2), ("DT_MOTCOB", 8),
    ("CATEND", 2), ("CIDPRI", 4), ("CIDASSOC", 4), ("ORIGEM_PAC", 2), ("DT_INICIO", 8), ("DT_FIM", 8),
    ("COB_ESF", 1), ("CNES_ESF", 7), ("DESTINOPAC", 2), ("PA_PROC_ID", 10), ("PA_QTDPRO", 11),
    ("PA_QTDAPR", 11), ("PA_SRV", 3), ("PA_CLASS_S", 3), ("SIT_RUA", 3), ("TP_DROGA", 3),
    ("LOC_REALIZ", 1), ("INICIO", 8), ("FIM", 8), ("PERMANEN", 4), ("QTDATE", 4), ("QTDPCN", 4),
]
FIELDS_NATJUR = PS_FIELDS + [("NAT_JUR", 4)]  # Oct/2014, and Jul/2016 onward
NAMES = [name.strip() for name, _ in FIELDS_NATJUR]
# The columns of a SAD (RAAS Atenção Domiciliar) file that PS shares, for the RAAS helper.
SAD_ONLY = {"PA_EQUIPE", "PA_TP_EQP", "PA_CID"}
PS_ONLY = {"TIPPRE", "SIT_RUA", "TP_DROGA", "LOC_REALIZ"}


def row(fields=PS_FIELDS, **kw):
    base = dict.fromkeys(NAMES, "")
    base.update(CNES_EXEC="2089335", UFMUN="355030", TPUPS="70", TIPPRE="00", DT_PROCESS="201605",
                DT_ATEND="201605", CNS_PAC="{{{{{{{{{{{{{{{", PA_PROC_ID="0301080208", PA_QTDPRO="4",
                PA_QTDAPR="4", PA_SRV="115", PA_CLASS_S="001", CIDPRI="F200", LOC_REALIZ="C",
                QTDATE="0004", QTDPCN="0001", NAT_JUR="1244")
    base.update(kw)
    return [base[name.strip()] for name, _ in fields]


def test_ps_layout():
    assert len(PS_FIELDS) == 44 and len(FIELDS_NATJUR) == 45
    assert sum(w for _, w in PS_FIELDS) + 1 == 227  # record length of PSSP1211.dbc / PSSP1606.dbc
    assert sum(w for _, w in FIELDS_NATJUR) + 1 == 231  # PSSP1410.dbc, PSSP1607.dbc ... PSSP2608.dbc


def test_ps_registered():
    ps = c.REGISTRY["PS"]
    assert ps is c.PS and list(c.REGISTRY)[:9] == ["PA", "BI", "AM", "AQ", "AR", "AD", "ATD", "AN", "PS"]
    assert c.DEFAULT_TABLES == ("PA",)
    assert [(e.key, e.ftp_dir, e.first, e.last) for e in ps.eras] == [("ps", c.FTP_CURRENT_DIR, 201211, 999912)]
    assert ps.eras[0].quantity_cols == ("PA_QTDPRO", "PA_QTDAPR") and ps.eras[0].value_cols == ()
    assert c.parse_tables("ps") == [ps] and c.parse_tables("ad,ps") == [c.AD, ps]
    assert ps.era_for(201211).key == ps.era_for(202608).key == "ps"
    with pytest.raises(ValueError):
        ps.era_for(201210)  # CAPS care was in AD until Dec/2012


def test_ps_dictionary_covers_every_column():
    cols = set(NAMES) | {"competencia", "uf", "_ARQUIVO_ORIGEM"}
    assert set(dictionary.PS) == cols
    assert all(desc.strip() and "TODO" not in desc for desc in dictionary.PS.values())
    # every PS column except its own four is a shared RAAS column; SAD adds three of its own
    assert set(NAMES) - PS_ONLY == set(dictionary.RAAS_COMMON)
    assert not SAD_ONLY & set(dictionary.RAAS_COMMON)
    assert not any(k.startswith("AP_") for k in dictionary.PS)  # RAAS, not APAC
    assert dictionary.PS["DT_PROCESS"] == dictionary.RAAS_COMMON["DT_PROCESS"]
    assert "Oct/2014" in dictionary.PS["NAT_JUR"]


@pytest.mark.parametrize("name,uf,comp", [
    ("PSAC1301.dbc", "AC", 201301),
    ("PSSP1211.DBC", "SP", 201211),
    ("PSPA2608.dbc", "PA", 202608),  # Pará
    ("PSPE1410.dbc", "PE", 201410),
])
def test_ps_names(name, uf, comp):
    rf = c.parse_name(name, 5)
    assert (rf.table, rf.uf, rf.competencia, rf.part) == ("PS", uf, comp, "")


@pytest.mark.parametrize("name", [
    "PSXX1405.dbc", "PSSP1413.dbc", "PSSP1405.dbf", "PASP1405.dbc", "SADSP1405.dbc", "PSSSP1405.dbc",
])
def test_ps_rejects(name):
    assert c.PS.parse(name) is None


def test_others_do_not_claim_ps():
    assert all(ft.parse("PSSP1405.dbc") is None for ft in c.REGISTRY.values() if ft is not c.PS)


def test_ps_conversion_and_view(make_dbf, tmp_path):
    store = Store(tmp_path / "data")
    p = c.group([c.parse_name("PSSP1605.dbc", 10)])[0]
    built = store.tmp / "b"
    built.mkdir(parents=True)
    dbf = make_dbf("PSSP1605.dbf", PS_FIELDS, [
        row(),
        row(DT_ATEND="201604", PA_PROC_ID="0301080259", PA_QTDPRO="2", PA_QTDAPR="1", LOC_REALIZ="T"),
        row(PA_QTDPRO="x"),  # malformed: NULL in the typed view, kept in _raw
    ])
    assert convert.dbf_to_parquet(dbf, built / "PSSP1605.parquet", origin="PSSP1605.dbc") == 3
    store.record(p, 3, store.publish(p, built))

    con = query.connect(store)
    assert {"ps", "ps_raw"} <= set(query.views(con))
    types = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                             "WHERE table_name = 'ps'").fetchall())
    assert "TIPPRE" in types and "TIPPRE  " not in types  # padded DBF name stripped
    assert types["PA_QTDPRO"] == types["PA_QTDAPR"] == "BIGINT" and types["competencia"] == "INTEGER"
    assert types["QTDATE"] == types["PERMANEN"] == "VARCHAR"
    assert con.execute("SELECT SUM(PA_QTDPRO), SUM(PA_QTDAPR), COUNT(*) FILTER (WHERE PA_QTDPRO IS NULL), "
                       "MIN(uf), MIN(competencia), MIN(_ARQUIVO_ORIGEM), MIN(TIPPRE) FROM ps").fetchone() == (
        6, 9, 1, "SP", 201605, "PSSP1605.dbc", "00")
    assert con.execute("SELECT PA_QTDPRO FROM ps_raw WHERE PA_QTDPRO = 'x'").fetchone() == ("x",)
    assert con.execute("SELECT LOC_REALIZ FROM ps WHERE DT_ATEND = '201604'").fetchone() == ("T",)


def test_ps_natjur_months(make_dbf, tmp_path):
    """44 columns, 45 (NAT_JUR last) in Oct/2014 and from Jul/2016."""
    store = Store(tmp_path / "data")
    for name, fields in (("PSSP1409", PS_FIELDS), ("PSSP1410", FIELDS_NATJUR), ("PSSP1411", PS_FIELDS),
                         ("PSSP1607", FIELDS_NATJUR)):
        p = c.group([c.parse_name(name + ".dbc", 10)])[0]
        built = store.tmp / name
        built.mkdir(parents=True)
        convert.dbf_to_parquet(make_dbf(name + ".dbf", fields, [row(fields)]), built / (name + ".parquet"),
                               name + ".dbc")
        store.record(p, 1, store.publish(p, built))
    con = query.connect(store)
    assert con.execute("SELECT competencia, NAT_JUR, TIPPRE FROM ps ORDER BY 1").fetchall() == [
        (201409, None, "00"), (201410, "1244", "00"), (201411, None, "00"), (201607, "1244", "00")]
