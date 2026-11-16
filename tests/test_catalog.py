import pytest

from intrepid_datasus import catalog as c


@pytest.mark.parametrize("name,uf,comp,part", [
    ("PASP2605a.dbc", "SP", 202605, "a"),
    ("PAAC0001.dbc", "AC", 200001, ""),
    ("PARJ9407.DBC", "RJ", 199407, ""),
    ("PAPA2512.dbc", "PA", 202512, ""),  # Pará: state code equals the prefix
    ("pamg2101C.DBC", "MG", 202101, "c"),
])
def test_parse_name(name, uf, comp, part):
    rf = c.parse_name(name, 10)
    assert (rf.uf, rf.competencia, rf.part, rf.size) == (uf, comp, part, 10)


@pytest.mark.parametrize("name", ["PAXX2605.dbc", "PASP2613.dbc", "ABOSP2605.dbc", "PASP2605.dbf", "PASP26051.dbc"])
def test_parse_name_rejects(name):
    assert c.PA.parse(name) is None


def test_group_and_select():
    files = [c.parse_name(n, s) for n, s in [
        ("PASP2605b.dbc", 2), ("PASP2605a.dbc", 1), ("PAAC2605.dbc", 5), ("PAAC2604.dbc", 7)]]
    parts = c.group(files)
    assert [(p.uf, p.competencia) for p in parts] == [("AC", 202604), ("AC", 202605), ("SP", 202605)]
    sp = parts[-1]
    assert [f.part for f in sp.files] == ["a", "b"] and sp.size == 3 and sp.key == "PA/SP/202605" and sp.label == "PA SP 2026-05"
    assert sp.signature() == {"PASP2605a.dbc": 1, "PASP2605b.dbc": 2}
    assert [p.key for p in c.select(parts, {"AC"}, 202605, 202605)] == ["PA/AC/202605"]
    assert len(c.select(parts, None, 202601, 202612)) == 3


# The columns of the last legacy files (PAAC0701.dbc; 20 in 1994, 24 in 2001, 27 from 2003, 28 from 2004).
PA_LEGACY_2007 = [
    "PA_CONDIC", "PA_GESTAO", "PA_CODUNI", "PA_DATREF", "PA_CODPRO", "PA_DOCORIG", "PA_CODESP", "PA_TIPPRO",
    "PA_TIPATE", "PA_FXETAR", "PA_QTDPRO", "PA_QTDAPR", "PA_INDICA", "PA_TIPPRE", "PA_DATPR", "PA_VALPRO",
    "PA_VALAPR", "PA_UFMUN", "PA_MUNAT", "PA_NUMAPA", "PA_CODOCO", "PA_CIDPRI", "PA_CIDSEC", "PA_MORFOL",
    "PA_CNPJ_CC", "PA_RCB", "PA_RCBDF", "PA_NH",
]


def test_pa_legacy_dictionary_covers_every_column():
    from intrepid_datasus import dictionary
    cols = set(PA_LEGACY_2007) | {"competencia", "uf", "_ARQUIVO_ORIGEM"}
    assert cols <= set(dictionary.PA_LEGACY)
    assert all(dictionary.PA_LEGACY[k].strip() for k in cols)


def test_era_for():
    assert c.PA.era_for(200712).key == "pa_legacy"
    assert c.PA.era_for(200801).key == "pa"


def test_parse_states():
    assert c.parse_states("all") is None
    assert c.parse_states(None) is None
    assert c.parse_states("sp, rj MG") == {"SP", "RJ", "MG"}
    assert c.parse_states("Sul") == {"PR", "SC", "RS"}
    assert c.parse_states("centro-oeste,SP") == {"MS", "MT", "GO", "DF", "SP"}
    with pytest.raises(ValueError):
        c.parse_states("XX")


def test_parse_period_and_months():
    assert c.parse_period("2023", is_end=False) == 202301
    assert c.parse_period("2023", is_end=True) == 202312
    assert c.parse_period("2023-05", is_end=False) == 202305
    with pytest.raises(ValueError):
        c.parse_period("202313", is_end=False)
    assert c.months(202311, 202402) == [202311, 202312, 202401, 202402]


def test_parse_list_line():
    assert c._parse_list_line("10-30-26  09:48PM            169954126 PAPR2604a.dbc") == ("PAPR2604a.dbc", 169954126)
    assert c._parse_list_line("10-30-26  09:48PM       <DIR>          sub") is None
    assert c._parse_list_line("-rw-r--r--   1 ftp ftp  1234 Oct 30 21:48 PAAC2605.dbc") == ("PAAC2605.dbc", 1234)
