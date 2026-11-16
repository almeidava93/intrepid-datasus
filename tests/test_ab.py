"""AB (APAC Cirurgia Bariátrica, post-surgery follow-up): registry entry, dictionary, conversion and view."""
import pytest

from intrepid_datasus import catalog as c, convert, dictionary, query
from intrepid_datasus.store import Store

# The 57 columns of a real file (ABSP0801.dbc ... ABSP1606.dbc), with their DBF widths: the 45
# shared APAC columns, then 12 AB_ columns. Every one of the 635 headers was probed: the Dec/2011
# files (ABSP1112.dbc) and those from Jul/2016 to the last one (ABSP2507.dbc) also have AP_NATJUR,
# appended last (58 columns). AP_VL_AP is a numeric (N) field 20 wide.
AB_FIELDS = [
    ("AP_MVM", 6), ("AP_CONDIC", 2), ("AP_GESTAO", 6), ("AP_CODUNI", 7), ("AP_AUTORIZ", 13),
    ("AP_CMP", 6), ("AP_PRIPAL", 10), ("AP_VL_AP", 20), ("AP_UFMUN", 6), ("AP_TPUPS", 2),
    ("AP_TIPPRE", 2), ("AP_MN_IND", 1), ("AP_CNPJCPF", 14), ("AP_CNPJMNT", 14), ("AP_CNSPCN", 15),
    ("AP_COIDADE", 1), ("AP_NUIDADE", 2), ("AP_SEXO", 1), ("AP_RACACOR", 2), ("AP_MUNPCN", 6),
    ("AP_UFNACIO", 3), ("AP_CEPPCN", 8), ("AP_UFDIF", 1), ("AP_MNDIF", 1), ("AP_DTINIC", 8),
    ("AP_DTFIM", 8), ("AP_TPATEN", 2), ("AP_TPAPAC", 1), ("AP_MOTSAI", 2), ("AP_OBITO", 1),
    ("AP_ENCERR", 1), ("AP_PERMAN", 1), ("AP_ALTA", 1), ("AP_TRANSF", 1), ("AP_DTOCOR", 8),
    ("AP_CODEMI", 10), ("AP_CATEND", 2), ("AP_APACANT", 13), ("AP_UNISOL", 7), ("AP_DTSOLIC", 8),
    ("AP_DTAUT", 8), ("AP_CIDCAS", 4), ("AP_CIDPRI", 4), ("AP_CIDSEC", 4), ("AP_ETNIA", 4),
    ("AB_IMC", 3), ("AB_PROCAIH", 10), ("AB_DTCIRUR", 8), ("AB_NUMAIH", 13), ("AB_PRCAIH2", 10),
    ("AB_PRCAIH3", 10), ("AB_NUMAIH2", 13), ("AB_DTCIRG2", 8), ("AB_MESACOM", 2), ("AB_ANOACOM", 4),
    ("AB_PONTBAR", 1), ("AB_TABBARR", 1),
]
FIELDS_NATJUR = AB_FIELDS + [("AP_NATJUR", 4)]  # Dec/2011, and Jul/2016 to Jul/2025


def row(fields=AB_FIELDS, **kw):
    base = {name: "" for name, _ in FIELDS_NATJUR}
    base.update(AP_MVM="201606", AP_CMP="201606", AP_CODUNI="2087057", AP_AUTORIZ="3516201234567",
                AP_PRIPAL="0301120056", AP_VL_AP="               40.00", AP_UFMUN="353870", AP_TPUPS="05",
                AP_TPATEN="05", AP_TPAPAC="1", AP_MNDIF="1", AP_DTINIC="20160601", AP_DTFIM="20160831",
                AP_CIDPRI="0000", AP_CIDSEC="0000", AP_CIDCAS="0000",
                # new (post-Mar/2013) laudo packed into the old columns, as DATASUS publishes it
                AB_IMC="32", AB_PROCAIH="30 30 NNSN", AB_DTCIRUR="20150310", AB_NUMAIH="3515101234567",
                AB_PRCAIH2="SSNNNN", AB_PRCAIH3="NNSNSN", AB_NUMAIH2="N   N   N   N", AB_MESACOM="12",
                AB_ANOACOM="2016", AB_PONTBAR="E", AB_TABBARR="6", AP_NATJUR="3999")
    base.update(kw)
    return [base[name] for name, _ in fields]


def test_ab_layout():
    assert len(AB_FIELDS) == 57 and len(FIELDS_NATJUR) == 58
    assert sum(w for _, w in AB_FIELDS) + 1 == 331  # record length of ABSP0801.dbc ... ABSP1606.dbc
    assert sum(w for _, w in FIELDS_NATJUR) + 1 == 335  # ABSP1112.dbc, ABSP1607.dbc ... ABSP2507.dbc


def test_ab_registered():
    ab = c.REGISTRY["AB"]
    assert ab is c.AB and list(c.REGISTRY)[:11] == [
        "PA", "BI", "AM", "AQ", "AR", "AD", "ATD", "AN", "PS", "SAD", "AB"]
    assert c.DEFAULT_TABLES == ("PA",)
    # last file month: data stops in Apr/2017, then Jan-Jul/2025 (a copy of ABO)
    assert [(e.key, e.ftp_dir, e.first, e.last) for e in ab.eras] == [("ab", c.FTP_CURRENT_DIR, 200801, 202507)]
    assert ab.eras[0].quantity_cols == () and ab.eras[0].value_cols == ("AP_VL_AP",)
    assert c.parse_tables("ab") == [ab] and c.parse_tables("an,ab") == [c.AN, ab]
    assert ab.era_for(200801).key == ab.era_for(201704).key == ab.era_for(202507).key == "ab"
    for month in (200712, 202508):
        with pytest.raises(ValueError):
            ab.era_for(month)


def test_ab_dictionary_covers_every_column():
    cols = {name for name, _ in FIELDS_NATJUR} | {"competencia", "uf", "_ARQUIVO_ORIGEM"}
    assert set(dictionary.AB) == cols
    assert all(desc.strip() and "TODO" not in desc for desc in dictionary.AB.values())
    own = {name for name, _ in AB_FIELDS if name.startswith("AB_")}
    assert len(own) == 12 and {name for name, _ in FIELDS_NATJUR} - own == set(dictionary.APAC_COMMON)
    assert dictionary.AB["AP_MVM"] == dictionary.APAC_COMMON["AP_MVM"]
    assert "0301120056" in dictionary.AB["AP_PRIPAL"]
    # the packed columns describe both laudos
    assert all("Mar/2013" in dictionary.AB[k] and "Apr/2013" in dictionary.AB[k]
               for k in ("AB_PROCAIH", "AB_PRCAIH2", "AB_PRCAIH3", "AB_NUMAIH2", "AB_PONTBAR"))
    assert "Dec/2011" in dictionary.AB["AP_NATJUR"]
    assert "ABSP2605.dbc" not in dictionary.AB["_ARQUIVO_ORIGEM"]


@pytest.mark.parametrize("name,uf,comp", [
    ("ABSP0801.dbc", "SP", 200801),
    ("ABPR1704.DBC", "PR", 201704),
    ("ABPE1112.dbc", "PE", 201112),  # Pernambuco: not ABO
    ("ABAC2507.dbc", "AC", 202507),
])
def test_ab_names(name, uf, comp):
    rf = c.parse_name(name, 5)
    assert (rf.table, rf.uf, rf.competencia, rf.part) == ("AB", uf, comp, "")


@pytest.mark.parametrize("name", [
    "ABOSP1606.dbc",  # ABO (post-bariatric follow-up, own type)
    "ABOPR2507.dbc", "ABXX1606.dbc", "ABSP1613.dbc", "ABSP1606.dbf", "ASP1606.dbc", "AMSP1606.dbc",
])
def test_ab_rejects(name):
    assert c.AB.parse(name) is None


def test_others_do_not_claim_ab():
    assert all(ft.parse("ABSP1606.dbc") is None for ft in c.REGISTRY.values() if ft is not c.AB)


def test_ab_conversion_and_view(make_dbf, tmp_path):
    store = Store(tmp_path / "data")
    p = c.group([c.parse_name("ABSP1606.dbc", 10)])[0]
    built = store.tmp / "b"
    built.mkdir(parents=True)
    dbf = make_dbf("ABSP1606.dbf", AB_FIELDS, [
        row(),
        row(AP_AUTORIZ="3516209999998", AP_CMP="201605", AP_TPAPAC="2", AP_VL_AP="                0.00",
            AB_PROCAIH="NNNS", AB_PRCAIH2="N", AB_PRCAIH3="NNNNNN000"),  # late, continuation, R$ 0
        row(AP_AUTORIZ="3516209999999", AP_VL_AP="x"),  # malformed: NULL in the typed view, kept in _raw
    ])
    assert convert.dbf_to_parquet(dbf, built / "ABSP1606.parquet", origin="ABSP1606.dbc") == 3
    store.record(p, 3, store.publish(p, built))

    con = query.connect(store)
    assert {"ab", "ab_raw"} <= set(query.views(con))
    types = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                             "WHERE table_name = 'ab'").fetchall())
    assert types["AP_VL_AP"] == "DOUBLE" and types["competencia"] == "INTEGER"
    assert types["AB_IMC"] == types["AB_PROCAIH"] == types["AB_DTCIRUR"] == "VARCHAR"
    assert con.execute("SELECT ROUND(SUM(AP_VL_AP), 2), COUNT(*) FILTER (WHERE AP_VL_AP IS NULL), "
                       "MIN(uf), MIN(competencia), MIN(_ARQUIVO_ORIGEM) FROM ab").fetchone() == (
        40.0, 1, "SP", 201606, "ABSP1606.dbc")
    assert con.execute("SELECT AP_VL_AP FROM ab_raw WHERE AP_VL_AP = 'x'").fetchone() == ("x",)
    # the leading blanks of the packed fields are stripped; the docs' lpad/rpad recipe restores them
    assert con.execute("""
        SELECT SUBSTR(lpad(AB_PROCAIH, 10, ' '), 7, 4), SUBSTR(rpad(' ' || AB_PRCAIH2, 10, ' '), 2, 2)
        FROM ab WHERE AP_CMP = '201605'""").fetchone() == ("NNNS", "N ")
    assert con.execute("SELECT TRIM(SUBSTR(lpad(AB_PROCAIH, 10, ' '), 4, 3)) FROM ab "
                       "WHERE AP_TPAPAC = '1' LIMIT 1").fetchone() == ("30",)


def test_ab_natjur_in_dec_2011_and_from_jul_2016(make_dbf, tmp_path):
    """57 columns, 58 (AP_NATJUR, appended after the AB_ columns) in Dec/2011 and from Jul/2016."""
    store = Store(tmp_path / "data")
    for name, fields in (("ABSP1111", AB_FIELDS), ("ABSP1112", FIELDS_NATJUR), ("ABSP1606", AB_FIELDS),
                         ("ABSP1607", FIELDS_NATJUR)):
        p = c.group([c.parse_name(name + ".dbc", 10)])[0]
        built = store.tmp / name
        built.mkdir(parents=True)
        convert.dbf_to_parquet(make_dbf(name + ".dbf", fields, [row(fields)]), built / (name + ".parquet"),
                               name + ".dbc")
        store.record(p, 1, store.publish(p, built))
    con = query.connect(store)
    assert con.execute("SELECT competencia, AP_NATJUR, AB_IMC FROM ab ORDER BY 1").fetchall() == [
        (201111, None, "32"), (201112, "3999", "32"), (201606, None, "32"), (201607, "3999", "32")]
