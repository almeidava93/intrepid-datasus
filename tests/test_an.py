"""AN (APAC Nefrologia): registry entry, dictionary, conversion and typed view."""
import pytest

from intrepid_datasus import catalog as c, convert, dictionary, query
from intrepid_datasus.store import Store

# The 60 columns of a real file (ANSP0801.dbc ... ANSP1409.dbc), with their DBF widths: the 45
# shared APAC columns, then 15 AN_ columns. AP_VL_AP is a numeric (N) field 20 wide; the
# converter reads every field as text. The Dec/2011 files of every state (ANSP1112.dbc) also
# have AP_NATJUR, appended last (61 columns).
AN_FIELDS = [
    ("AP_MVM", 6), ("AP_CONDIC", 2), ("AP_GESTAO", 6), ("AP_CODUNI", 7), ("AP_AUTORIZ", 13),
    ("AP_CMP", 6), ("AP_PRIPAL", 10), ("AP_VL_AP", 20), ("AP_UFMUN", 6), ("AP_TPUPS", 2),
    ("AP_TIPPRE", 2), ("AP_MN_IND", 1), ("AP_CNPJCPF", 14), ("AP_CNPJMNT", 14), ("AP_CNSPCN", 15),
    ("AP_COIDADE", 1), ("AP_NUIDADE", 2), ("AP_SEXO", 1), ("AP_RACACOR", 2), ("AP_MUNPCN", 6),
    ("AP_UFNACIO", 3), ("AP_CEPPCN", 8), ("AP_UFDIF", 1), ("AP_MNDIF", 1), ("AP_DTINIC", 8),
    ("AP_DTFIM", 8), ("AP_TPATEN", 2), ("AP_TPAPAC", 1), ("AP_MOTSAI", 2), ("AP_OBITO", 1),
    ("AP_ENCERR", 1), ("AP_PERMAN", 1), ("AP_ALTA", 1), ("AP_TRANSF", 1), ("AP_DTOCOR", 8),
    ("AP_CODEMI", 10), ("AP_CATEND", 2), ("AP_APACANT", 13), ("AP_UNISOL", 7), ("AP_DTSOLIC", 8),
    ("AP_DTAUT", 8), ("AP_CIDCAS", 4), ("AP_CIDPRI", 4), ("AP_CIDSEC", 4), ("AP_ETNIA", 4),
    ("AN_DTPDR", 8), ("AN_ALTURA", 3), ("AN_PESO", 3), ("AN_DIURES", 4), ("AN_GLICOS", 4),
    ("AN_ACEVAS", 1), ("AN_ULSOAB", 1), ("AN_TRU", 4), ("AN_INTFIS", 2), ("AN_CNCDO", 1),
    ("AN_ALBUMI", 2), ("AN_HCV", 1), ("AN_HBSAG", 1), ("AN_HIV", 1), ("AN_HB", 2),
]
FIELDS_2011_12 = AN_FIELDS + [("AP_NATJUR", 4)]  # Dec/2011 only


def row(fields=AN_FIELDS, **kw):
    base = {name: "" for name, _ in FIELDS_2011_12}
    base.update(AP_MVM="201205", AP_CMP="201205", AP_CODUNI="2077485", AP_AUTORIZ="3512201234567",
                AP_PRIPAL="0305010107", AP_VL_AP="             2195.24", AP_UFMUN="355030", AP_TPATEN="10",
                AP_TPAPAC="2", AP_DTINIC="20120501", AP_DTFIM="20120731", AP_CIDPRI="N180",
                AN_DTPDR="20090415", AN_TRU="0070", AN_INTFIS="00", AN_CNCDO="S", AN_ALBUMI="39",
                AN_HCV="N", AN_HBSAG="N", AN_HIV="N", AN_HB="11", AP_NATJUR="2062")
    base.update(kw)
    return [base[name] for name, _ in fields]


def test_an_layout():
    assert len(AN_FIELDS) == 60 and len(FIELDS_2011_12) == 61
    assert sum(w for _, w in AN_FIELDS) + 1 == 286  # record length of ANSP0801.dbc / ANSP1409.dbc
    assert sum(w for _, w in FIELDS_2011_12) + 1 == 290  # record length of ANSP1112.dbc


def test_an_registered():
    an = c.REGISTRY["AN"]
    assert an is c.AN and list(c.REGISTRY)[:8] == ["PA", "BI", "AM", "AQ", "AR", "AD", "ATD", "AN"]
    assert c.DEFAULT_TABLES == ("PA",)
    # discontinued: last file month, not 999912 (real data ends Jul/2014, then late bills)
    assert [(e.key, e.ftp_dir, e.first, e.last) for e in an.eras] == [("an", c.FTP_CURRENT_DIR, 200801, 201410)]
    assert an.eras[0].quantity_cols == () and an.eras[0].value_cols == ("AP_VL_AP",)
    assert c.parse_tables("an") == [an] and c.parse_tables("atd,an") == [c.ATD, an]
    assert c.parse_tables("all")[:8] == [c.PA, c.BI, c.AM, c.AQ, c.AR, c.AD, c.ATD, an]
    assert an.era_for(200801).key == an.era_for(201410).key == "an"
    with pytest.raises(ValueError):
        an.era_for(201411)  # dialysis from Aug/2014 is in ATD
    with pytest.raises(ValueError):
        an.era_for(200712)


def test_an_dictionary_covers_every_column():
    cols = {name for name, _ in FIELDS_2011_12} | {"competencia", "uf", "_ARQUIVO_ORIGEM"}
    assert set(dictionary.AN) == cols
    assert all(desc.strip() and "TODO" not in desc for desc in dictionary.AN.values())
    own = {name for name, _ in AN_FIELDS if name.startswith("AN_")}
    assert len(own) == 15 and {name for name, _ in FIELDS_2011_12} - own == set(dictionary.APAC_COMMON)
    assert dictionary.AN["AP_MVM"] == dictionary.APAC_COMMON["AP_MVM"]
    assert dictionary.AN["AP_PRIPAL"] != dictionary.APAC_COMMON["AP_PRIPAL"]  # AN-specific notes
    assert "ANSP2605.dbc" not in dictionary.AN["_ARQUIVO_ORIGEM"]  # example names a month AN has
    assert "Dec/2011" in dictionary.AN["AP_NATJUR"]


@pytest.mark.parametrize("name,uf,comp", [
    ("ANAC0801.dbc", "AC", 200801),
    ("ANSP1407.DBC", "SP", 201407),
    ("ANPA1112.dbc", "PA", 201112),  # Pará: not confused with another type's prefix
    ("ANRR1410.dbc", "RR", 201410),
])
def test_an_names(name, uf, comp):
    rf = c.parse_name(name, 5)
    assert (rf.table, rf.uf, rf.competencia, rf.part) == ("AN", uf, comp, "")


@pytest.mark.parametrize("name", [
    "ANXX1405.dbc", "ANSP1413.dbc", "ANSP1405.dbf", "ASP1405.dbc", "ATDSP1408.dbc", "AMSP1405.dbc",
])
def test_an_rejects(name):
    assert c.AN.parse(name) is None


def test_others_do_not_claim_an():
    assert all(ft.parse("ANSP1405.dbc") is None for ft in c.REGISTRY.values() if ft is not c.AN)


def test_an_conversion_and_view(make_dbf, tmp_path):
    store = Store(tmp_path / "data")
    p = c.group([c.parse_name("ANSP1205.dbc", 10)])[0]
    built = store.tmp / "b"
    built.mkdir(parents=True)
    dbf = make_dbf("ANSP1205.dbf", AN_FIELDS, [
        row(),
        row(AP_CMP="201204", AP_TPAPAC="1", AP_VL_AP="             2504.70",  # late billing of April,
            AN_ALTURA="168", AN_PESO="072", AN_DIURES="0500", AN_GLICOS="0098",  # first dialysis
            AN_ACEVAS="S", AN_ULSOAB="N", AN_TRU="", AN_CNCDO=""),
        row(AP_AUTORIZ="3512209999999", AP_VL_AP="x"),  # malformed: NULL in the typed view, kept in _raw
    ])
    assert convert.dbf_to_parquet(dbf, built / "ANSP1205.parquet", origin="ANSP1205.dbc") == 3
    store.record(p, 3, store.publish(p, built))

    con = query.connect(store)
    assert {"an", "an_raw"} <= set(query.views(con))
    types = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                             "WHERE table_name = 'an'").fetchall())
    assert types["AP_VL_AP"] == "DOUBLE" and types["competencia"] == "INTEGER"
    # lab and body measures stay text, as in ATD
    assert types["AN_HB"] == types["AN_PESO"] == types["AN_TRU"] == "VARCHAR"
    assert con.execute("SELECT ROUND(SUM(AP_VL_AP), 2), COUNT(*) FILTER (WHERE AP_VL_AP IS NULL), "
                       "COUNT(DISTINCT (AP_AUTORIZ, AP_CMP)), MIN(uf), MIN(competencia), MIN(_ARQUIVO_ORIGEM) "
                       "FROM an").fetchone() == (4699.94, 1, 3, "SP", 201205, "ANSP1205.dbc")
    assert con.execute("SELECT AP_VL_AP FROM an_raw WHERE AP_VL_AP = 'x'").fetchone() == ("x",)
    assert con.execute("SELECT AP_TPAPAC, AN_ALTURA, AN_PESO, AN_ACEVAS, AN_TRU FROM an "
                       "WHERE AP_CMP = '201204'").fetchone() == ("1", "168", "072", "S", None)


def test_an_natjur_in_dec_2011_only(make_dbf, tmp_path):
    """60 columns, except the Dec/2011 files: 61 (AP_NATJUR, appended after the AN_ columns)."""
    store = Store(tmp_path / "data")
    for name, fields in (("ANSP1111", AN_FIELDS), ("ANSP1112", FIELDS_2011_12), ("ANSP1201", AN_FIELDS)):
        p = c.group([c.parse_name(name + ".dbc", 10)])[0]
        built = store.tmp / name
        built.mkdir(parents=True)
        convert.dbf_to_parquet(make_dbf(name + ".dbf", fields, [row(fields)]), built / (name + ".parquet"),
                               name + ".dbc")
        store.record(p, 1, store.publish(p, built))
    con = query.connect(store)
    assert con.execute("SELECT competencia, AP_NATJUR, AN_HB FROM an ORDER BY 1").fetchall() == [
        (201111, None, "11"), (201112, "2062", "11"), (201201, None, "11")]
