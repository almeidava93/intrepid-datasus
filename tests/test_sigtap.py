import json
import zipfile

import pytest
from typer.testing import CliRunner

from intrepid_datasus import query, sigtap
from intrepid_datasus.cli import app
from intrepid_datasus.store import Store

PROC_LAYOUT = """Coluna,Tamanho,Inicio,Fim,Tipo
CO_PROCEDIMENTO,10,1,10,VARCHAR2
NO_PROCEDIMENTO,20,11,30,VARCHAR2
TP_COMPLEXIDADE,1,31,31,VARCHAR2
CO_FINANCIAMENTO,2,32,33,VARCHAR2
VL_SA,12,34,45,NUMBER
"""
GRUPO_LAYOUT = "Coluna,Tamanho,Inicio,Fim,Tipo\nCO_GRUPO,2,1,2,VARCHAR2\nNO_GRUPO,10,3,12,VARCHAR2\n"


def proc_line(code, name, cx="1", fin="01", vl="000000001000"):
    return f"{code}{name:<20}{cx}{fin}{vl}".encode("latin-1")


def make_zip(path, procs, grupos=(("03", "Clínicos"),)):
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("tb_procedimento_layout.txt", PROC_LAYOUT)
        z.writestr("tb_procedimento.txt", b"\r\n".join(proc_line(*p) for p in procs) + b"\r\n")
        z.writestr("tb_grupo_layout.txt", GRUPO_LAYOUT)
        z.writestr("tb_grupo.txt", b"\r\n".join(f"{c}{n:<10}".encode("latin-1") for c, n in grupos))
        z.writestr("LEIA_ME.TXT", "ignored")
    return path


def test_parse_layout_and_table():
    layout = sigtap.parse_layout(PROC_LAYOUT)
    assert layout[0] == ("CO_PROCEDIMENTO", 0, 10) and layout[-1] == ("VL_SA", 33, 45)
    t = sigtap.parse_table(proc_line("0301010064", "CONSULTA MÉDICA") + b"\r\n\r\n", layout).to_pylist()
    assert t == [{"CO_PROCEDIMENTO": "0301010064", "NO_PROCEDIMENTO": "CONSULTA MÉDICA",
                  "TP_COMPLEXIDADE": "1", "CO_FINANCIAMENTO": "01", "VL_SA": "000000001000"}]


def test_pick_yearly():
    vs = [sigtap.Version(c, f"TabelaUnificada_{c}_v1.zip", 1) for c in (202301, 202312, 202401, 202405)]
    assert [v.competencia for v in sigtap.pick(vs, 202301, None, yearly=True)] == [202312, 202405]
    assert [v.competencia for v in sigtap.pick(vs, 202312, 202401, yearly=False)] == [202312, 202401]


def test_import_and_views(tmp_path):
    store = Store(tmp_path / "data")
    st = sigtap.SigtapStore(store.root)
    # 2023: two codes; 2024: one renamed, one retired, one new
    for comp, procs in {
        202312: [("0301010064", "CONSULTA OLD"), ("0301010999", "RETIRED CODE")],
        202412: [("0301010064", "CONSULTA NEW"), ("0301010250", "TELECONSULTA", "1", "01", "000000000000")],
    }.items():
        counts = sigtap.import_zip(make_zip(tmp_path / f"{comp}.zip", procs), st.dir / f"competencia={comp}")
        assert counts["tb_procedimento"] == len(procs) and "leia_me" not in counts

    con = query.connect(store)
    assert {"procedimentos", "sigtap_procedimento", "sigtap_procedimento_all", "sigtap_grupo"} <= set(query.views(con))
    rows = con.execute("""SELECT codigo, nome, grupo, complexidade, valor_ambulatorial, primeira_versao, ultima_versao, ativo
                          FROM procedimentos ORDER BY codigo""").fetchall()
    assert rows == [
        ("0301010064", "CONSULTA NEW", "Clínicos", "Atenção Básica", 10.0, 202312, 202412, True),
        ("0301010250", "TELECONSULTA", "Clínicos", "Atenção Básica", 0.0, 202412, 202412, True),
        ("0301010999", "RETIRED CODE", "Clínicos", "Atenção Básica", 10.0, 202312, 202312, False),
    ]
    assert con.execute("SELECT COUNT(*) FROM sigtap_procedimento_all").fetchone() == (4,)


def test_import_rejects_zip_without_procedures(tmp_path):
    p = tmp_path / "bad.zip"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("tb_grupo_layout.txt", GRUPO_LAYOUT)
        z.writestr("tb_grupo.txt", b"03Clinicos  ")
    with pytest.raises(ValueError):
        sigtap.import_zip(p, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_cli_search(tmp_path, monkeypatch):
    from intrepid_datasus import cli
    monkeypatch.setattr(cli.console, "width", 200)
    store = Store(tmp_path / "data")
    st = sigtap.SigtapStore(store.root)
    sigtap.import_zip(make_zip(tmp_path / "z.zip", [("0301010250", "TELECONSULTA APS"), ("0301010064", "CONSULTA")]),
                      st.dir / "competencia=202610")
    r = CliRunner().invoke(app, ["--data-dir", str(store.root), "sigtap", "search", "téléconsulta"])
    assert r.exit_code == 0, r.output
    assert "0301010250" in r.output and "0301010064" not in r.output
    r = CliRunner().invoke(app, ["--data-dir", str(store.root), "sigtap", "search", "030101006"])
    assert "0301010064" in r.output and "0301010250" not in r.output


@pytest.mark.parametrize("name,comp", [("TabelaUnificada_200801.zip", 200801), ("TabelaUnificada_202610_v2610271043.zip", 202610)])
def test_version_names(name, comp):
    m = sigtap.NAME_RE.match(name)
    assert m and int(m.group(1)) == comp


def test_layout_skips_junk_rows():
    text = "Coluna,Tamanho,Inicio,Fim,Tipo\nCO_X,2,1,2,VARCHAR2\nBAD,NULL),NULL),NULL),X\n"
    assert sigtap.parse_layout(text) == [("CO_X", 0, 2)]
