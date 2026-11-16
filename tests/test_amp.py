"""AMP (APAC Acompanhamento Multiprofissional): registry entry, dictionary, conversion and view."""
import pytest

from intrepid_datasus import catalog as c, convert, dictionary, query
from intrepid_datasus.store import Store

# The 64 columns of a real file (AMPRO1603.dbc ... AMPRO1606.dbc), with their DBF widths: the 45 shared
# APAC columns under their usual names, then 19 AMP_ columns named like ATD's dialysis laudo (AMP_DTINI where
# ATD has ATD_DTPDR). Every one of the 903 headers was probed: from Aug/2016 (AMPRO1608.dbc; there is no
# Jul/2016 file) every file also has AP_NATJUR, appended last (65 columns).
AMP_FIELDS = [
    ("AP_MVM", 6), ("AP_CONDIC", 2), ("AP_GESTAO", 6), ("AP_CODUNI", 7), ("AP_AUTORIZ", 13), ("AP_CMP", 6),
    ("AP_PRIPAL", 10), ("AP_VL_AP", 20), ("AP_UFMUN", 6), ("AP_TPUPS", 2), ("AP_TIPPRE", 2), ("AP_MN_IND", 1),
    ("AP_CNPJCPF", 14), ("AP_CNPJMNT", 14), ("AP_CNSPCN", 15), ("AP_COIDADE", 1), ("AP_NUIDADE", 2),
    ("AP_SEXO", 1), ("AP_RACACOR", 2), ("AP_MUNPCN", 6), ("AP_UFNACIO", 3), ("AP_CEPPCN", 8),
    ("AP_UFDIF", 1), ("AP_MNDIF", 1), ("AP_DTINIC", 8), ("AP_DTFIM", 8), ("AP_TPATEN", 2), ("AP_TPAPAC", 1),
    ("AP_MOTSAI", 2), ("AP_OBITO", 1), ("AP_ENCERR", 1), ("AP_PERMAN", 1), ("AP_ALTA", 1), ("AP_TRANSF", 1),
    ("AP_DTOCOR", 8), ("AP_CODEMI", 10), ("AP_CATEND", 2), ("AP_APACANT", 13), ("AP_UNISOL", 7),
    ("AP_DTSOLIC", 8), ("AP_DTAUT", 8), ("AP_CIDCAS", 4), ("AP_CIDPRI", 4), ("AP_CIDSEC", 4),
    ("AP_ETNIA", 4), ("AMP_CARACT", 1), ("AMP_DTINI", 8), ("AMP_DTCLI", 8), ("AMP_ACEVAS", 1),
    ("AMP_MAISNE", 1), ("AMP_SITINI", 1), ("AMP_SITTRA", 1), ("AMP_SEAPTO", 1), ("AMP_HB", 4),
    ("AMP_FOSFOR", 4), ("AMP_KTVSEM", 4), ("AMP_TRU", 4), ("AMP_ALBUMI", 4), ("AMP_PTH", 4), ("AMP_HIV", 1),
    ("AMP_HCV", 1), ("AMP_HBSAG", 1), ("AMP_INTERC", 1), ("AMP_SEPERI", 1),
]
FIELDS_NATJUR = AMP_FIELDS + [("AP_NATJUR", 4)]  # Aug/2016 onward
OWN = ["AMP_CARACT", "AMP_DTINI", "AMP_DTCLI", "AMP_ACEVAS", "AMP_MAISNE", "AMP_SITINI", "AMP_SITTRA",
       "AMP_SEAPTO", "AMP_HB", "AMP_FOSFOR", "AMP_KTVSEM", "AMP_TRU", "AMP_ALBUMI", "AMP_PTH", "AMP_HIV",
       "AMP_HCV", "AMP_HBSAG", "AMP_INTERC", "AMP_SEPERI"]


def row(fields=AMP_FIELDS, **kw):
    base = {name: "" for name, _ in FIELDS_NATJUR}
    base.update(AP_MVM="201606", AP_CMP="201606", AP_CODUNI="2077485", AP_AUTORIZ="1116201234567",
                AP_PRIPAL="0301130060", AP_VL_AP="              122.00", AP_UFMUN="110020", AP_TPUPS="36",
                AP_TIPPRE="00", AP_TPATEN="11", AP_TPAPAC="1", AP_MNDIF="1", AP_DTINIC="20160601",
                AP_DTFIM="20160831", AP_CIDCAS="0000", AP_CIDPRI="0000", AP_CIDSEC="0000",
                # a real laudo, cut one field late: referred for FAV = S, catheter = N, 170 cm, 78 kg, ...
                AMP_CARACT="2", AMP_DTINI="SN170078", AMP_DTCLI="N", AMP_ACEVAS="1", AMP_MAISNE="0",
                AMP_SITINI="R", AMP_SITTRA="R", AMP_SEAPTO="S", AMP_HB="S", AMP_FOSFOR="N", AMP_KTVSEM="1",
                AMP_TRU="04,1", AMP_ALBUMI="03,9", AMP_PTH="0165", AMP_HIV="N", AMP_HCV="N", AMP_HBSAG="N",
                AMP_INTERC="S", AMP_SEPERI="N", AP_NATJUR="2062")
    base.update(kw)
    return [base[name] for name, _ in fields]


def test_amp_layout():
    assert len(AMP_FIELDS) == 64 and len(FIELDS_NATJUR) == 65
    assert sum(w for _, w in AMP_FIELDS) + 1 == 299  # record length of AMPRO1603.dbc ... AMPRO1606.dbc
    assert sum(w for _, w in FIELDS_NATJUR) + 1 == 303  # AMPRO1608.dbc ... AMPSP2608.dbc
    assert [n for n, _ in AMP_FIELDS[-19:]] == OWN
    # the same 19 laudo columns as ATD, in the same order, but AMP_DTINI where ATD has ATD_DTPDR
    atd_own = [k for k in dictionary.ATD if k.startswith("ATD_")]
    assert [n.replace("AMP_", "ATD_") for n in OWN] == [n.replace("DTPDR", "DTINI") for n in atd_own]


def test_amp_registered():
    amp = c.REGISTRY["AMP"]
    assert amp is c.AMP and list(c.REGISTRY) == [
        "PA", "BI", "AM", "AQ", "AR", "AD", "ATD", "AN", "PS", "SAD", "AB", "ABO", "ACF", "AMP"]
    assert c.DEFAULT_TABLES == ("PA",)
    assert [(e.key, e.ftp_dir, e.first, e.last) for e in amp.eras] == [("amp", c.FTP_CURRENT_DIR, 201603, 999912)]
    assert amp.eras[0].quantity_cols == () and amp.eras[0].value_cols == ("AP_VL_AP",)
    assert c.parse_tables("amp") == [amp] and c.parse_tables("atd,acf,amp") == [c.ATD, c.ACF, amp]
    assert c.parse_tables("all")[-1] is amp
    assert amp.era_for(201603).key == amp.era_for(202608).key == "amp"
    with pytest.raises(ValueError):
        amp.era_for(201602)


def test_amp_dictionary_covers_every_column():
    cols = {name for name, _ in FIELDS_NATJUR} | {"competencia", "uf", "_ARQUIVO_ORIGEM"}
    assert set(dictionary.AMP) == cols
    assert all(desc.strip() and "TODO" not in desc for desc in dictionary.AMP.values())
    # every shared AP_ column, under its usual name; nothing renamed or missing
    shared = set(dictionary.APAC_COMMON)
    assert {name for name, _ in FIELDS_NATJUR} & shared == shared
    assert {name for name, _ in FIELDS_NATJUR} - shared == set(OWN)
    assert dictionary.AMP["AP_MVM"] == dictionary.APAC_COMMON["AP_MVM"]
    assert "0301130051" in dictionary.AMP["AP_PRIPAL"] and "0301130060" in dictionary.AMP["AP_PRIPAL"]
    assert "Aug/2016" in dictionary.AMP["AP_NATJUR"]
    assert "AMPSP2605.dbc" in dictionary.AMP["_ARQUIVO_ORIGEM"]
    assert "Always 11" in dictionary.AMP["AP_TPATEN"] and "Always '0000'" in dictionary.AMP["AP_CIDPRI"]
    # the laudo is cut one field late: every own column says what it really holds
    assert "fistula" in dictionary.AMP["AMP_DTINI"] and "height" in dictionary.AMP["AMP_DTINI"]
    assert "weight" in dictionary.AMP["AMP_DTINI"] and "catheter" in dictionary.AMP["AMP_DTCLI"]
    assert "NOT" in dictionary.AMP["AMP_DTINI"] and "lost" in dictionary.AMP["AMP_DTINI"]
    assert "vaccin" in dictionary.AMP["AMP_SITINI"].lower() and "hepatitis B" in dictionary.AMP["AMP_SITTRA"]
    assert "influenza" in dictionary.AMP["AMP_SEAPTO"].lower() and "tetanus" in dictionary.AMP["AMP_HB"].lower()
    assert "pneumococcal" in dictionary.AMP["AMP_FOSFOR"].lower()
    assert "haemoglobin" in dictionary.AMP["AMP_KTVSEM"].lower() and "phosphorus" in dictionary.AMP["AMP_TRU"]
    assert "ACE inhibitor" in dictionary.AMP["AMP_INTERC"] and "ARB" in dictionary.AMP["AMP_SEPERI"]


@pytest.mark.parametrize("name,uf,comp", [
    ("AMPRO1603.dbc", "RO", 201603),
    ("AMPSP2608.DBC", "SP", 202608),
    ("AMPPA2605.dbc", "PA", 202605),  # AMP for Pará
    ("AMPPE1112.dbc", "PE", 201112),  # name parses; the era starts in Mar/2016
])
def test_amp_names(name, uf, comp):
    rf = c.parse_name(name, 5)
    assert (rf.table, rf.uf, rf.competencia, rf.part) == ("AMP", uf, comp, "")


@pytest.mark.parametrize("name", [
    "AMPXX1606.dbc", "AMPSP1613.dbc", "AMPSP1606.dbf", "AMSP1606.dbc", "ATDSP1606.dbc",
    "AMPA2605.dbc", "AMPE2605.dbc", "AMPI2605.dbc", "AMPB2605.dbc", "AMPR2605.dbc",  # AM of PA, PE, PI, PB, PR
])
def test_amp_rejects(name):
    assert c.AMP.parse(name) is None


@pytest.mark.parametrize("name,uf", [
    ("AMPA2605.dbc", "PA"), ("AMPE2605.dbc", "PE"), ("AMPI2605.dbc", "PI"), ("AMPB2605.dbc", "PB"),
    ("AMPR2605.dbc", "PR"),
])
def test_am_files_of_p_states_stay_am(name, uf):
    rf = c.parse_name(name, 5)
    assert (rf.table, rf.uf) == ("AM", uf)


def test_others_do_not_claim_amp():
    assert all(ft.parse("AMPSP1606.dbc") is None for ft in c.REGISTRY.values() if ft is not c.AMP)


def test_amp_conversion_and_view(make_dbf, tmp_path):
    store = Store(tmp_path / "data")
    p = c.group([c.parse_name("AMPRO1606.dbc", 10)])[0]
    built = store.tmp / "b"
    built.mkdir(parents=True)
    dbf = make_dbf("AMPRO1606.dbf", AMP_FIELDS, [
        row(),
        row(AP_AUTORIZ="1116209999998", AP_CMP="201605", AP_TPAPAC="3", AP_PRIPAL="0301130051",
            AMP_DTINI="NN15053", AMP_ALBUMI="", AMP_PTH=""),  # late, stage 4, weight '53 ' trimmed
        row(AP_AUTORIZ="1116209999999", AP_VL_AP="x"),  # malformed: NULL in the typed view, kept in _raw
    ])
    assert convert.dbf_to_parquet(dbf, built / "AMPRO1606.parquet", origin="AMPRO1606.dbc") == 3
    store.record(p, 3, store.publish(p, built))

    con = query.connect(store)
    assert {"amp", "amp_raw"} <= set(query.views(con))
    types = dict(con.execute("SELECT column_name, data_type FROM information_schema.columns "
                             "WHERE table_name = 'amp'").fetchall())
    assert types["AP_VL_AP"] == "DOUBLE" and types["competencia"] == "INTEGER"
    assert types["AMP_DTINI"] == types["AMP_TRU"] == types["AMP_KTVSEM"] == "VARCHAR"  # packed text
    assert con.execute("SELECT ROUND(SUM(AP_VL_AP), 2), COUNT(*) FILTER (WHERE AP_VL_AP IS NULL), "
                       "MIN(uf), MIN(competencia), MIN(_ARQUIVO_ORIGEM) FROM amp").fetchone() == (
        244.0, 1, "RO", 201606, "AMPRO1606.dbc")
    assert con.execute("SELECT AP_VL_AP FROM amp_raw WHERE AP_VL_AP = 'x'").fetchone() == ("x",)
    # the documented unpacking of AMP_DTINI: FAV referral, catheter referral, height (cm), weight (kg)
    assert con.execute(
        "SELECT substr(AMP_DTINI, 1, 1), substr(AMP_DTINI, 2, 1), TRY_CAST(substr(AMP_DTINI, 3, 3) AS INT), "
        "TRY_CAST(trim(substr(AMP_DTINI, 6, 3)) AS INT), AMP_DTCLI = substr(AMP_DTINI, 2, 1), AMP_ALBUMI "
        "FROM amp WHERE AP_CMP = '201605'").fetchone() == ("N", "N", 150, 53, True, None)


def test_amp_natjur_from_aug_2016(make_dbf, tmp_path):
    """64 columns until Jun/2016, 65 (AP_NATJUR, appended last) from Aug/2016."""
    store = Store(tmp_path / "data")
    for name, fields in (("AMPRO1606", AMP_FIELDS), ("AMPRO1608", FIELDS_NATJUR)):
        p = c.group([c.parse_name(name + ".dbc", 10)])[0]
        built = store.tmp / name
        built.mkdir(parents=True)
        convert.dbf_to_parquet(make_dbf(name + ".dbf", fields, [row(fields)]), built / (name + ".parquet"),
                               name + ".dbc")
        store.record(p, 1, store.publish(p, built))
    con = query.connect(store)
    assert con.execute("SELECT competencia, AP_NATJUR, AMP_DTINI FROM amp ORDER BY 1").fetchall() == [
        (201606, None, "SN170078"), (201608, "2062", "SN170078")]
