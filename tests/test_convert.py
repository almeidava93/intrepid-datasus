import pyarrow.parquet as pq
import pytest

from intrepid_datasus import convert


FIELDS = [("PA_UFMUN", 6), ("PA_QTDAPR", 5), ("PA_VALAPR", 10), ("PA_NOME", 8)]


def test_dbf_to_parquet_roundtrip(make_dbf, tmp_path):
    dbf = make_dbf(fields=FIELDS, rows=[
        ["350000", "    3", "     12.50", "São"],
        ["330000", "", "0.00", "  "],
        ["310000", "1", "1", "deleted"],
    ], deleted={2})
    out = tmp_path / "x.parquet"
    n = convert.dbf_to_parquet(dbf, out, origin="PASP2605a.dbc")
    assert n == 2  # deleted record dropped
    t = pq.read_table(out).to_pylist()
    assert t[0] == {"PA_UFMUN": "350000", "PA_QTDAPR": "3", "PA_VALAPR": "12.50",
                    "PA_NOME": "São", "_ARQUIVO_ORIGEM": "PASP2605a.dbc"}
    assert t[1]["PA_QTDAPR"] is None and t[1]["PA_NOME"] is None  # blanks become NULL
    assert not list(tmp_path.glob("*.tmp"))


def test_chunking(make_dbf, tmp_path, monkeypatch):
    monkeypatch.setattr(convert, "CHUNK", 2)
    dbf = make_dbf(fields=FIELDS[:1], rows=[[str(i)] for i in range(5)])
    out = tmp_path / "x.parquet"
    assert convert.dbf_to_parquet(dbf, out, "f") == 5
    f = pq.ParquetFile(out)
    assert f.metadata.num_row_groups == 3
    assert [r["PA_UFMUN"] for r in f.read().to_pylist()] == ["0", "1", "2", "3", "4"]


def test_empty_file(make_dbf, tmp_path):
    dbf = make_dbf(fields=FIELDS, rows=[])
    out = tmp_path / "x.parquet"
    assert convert.dbf_to_parquet(dbf, out, "f") == 0
    assert pq.read_schema(out).names == [n for n, _ in FIELDS] + ["_ARQUIVO_ORIGEM"]


def test_truncated_file_uses_real_size(make_dbf, tmp_path):
    dbf = make_dbf(fields=FIELDS[:1], rows=[["1"], ["2"], ["3"]])
    data = dbf.read_bytes()
    dbf.write_bytes(data[:-1 - 7])  # drop the EOF marker and the last record
    assert convert.dbf_to_parquet(dbf, tmp_path / "x.parquet", "f") == 2


def test_bad_header(make_dbf):
    dbf = make_dbf(fields=FIELDS[:1], rows=[["1"]])
    data = bytearray(dbf.read_bytes())
    data[10] += 1  # record length no longer matches the fields
    dbf.write_bytes(bytes(data))
    with pytest.raises(ValueError):
        convert.read_dbf_header(dbf)
