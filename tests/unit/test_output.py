"""Unit tests for output formatting (table, json, csv)."""

import csv
import io
import json

from oxtan.cli.output import (
    format_csv,
    format_json,
    format_table,
    print_results,
    safe_write,
    truncate_cell,
)


def test_truncate_cell():
    assert truncate_cell(None) == "NULL"
    assert truncate_cell("short") == "short"
    assert truncate_cell("a" * 50, max_width=10) == "aaaaaaa..."
    assert truncate_cell(b"binary_data") == "blob(11B)"
    assert truncate_cell("hello\nworld\r") == "hello world "


def test_format_table_aligned():
    columns = ["id", "username", "status"]
    rows = [
        {"id": 1, "username": "alice", "status": "active"},
        {"id": 2, "username": "bob_the_builder", "status": "pending"},
    ]
    table_str = format_table(columns, rows)
    lines = table_str.strip().split("\n")
    assert len(lines) == 4
    assert "id" in lines[0] and "username" in lines[0] and "status" in lines[0]
    assert "-+-" in lines[1]
    assert "alice" in lines[2]
    assert "bob_the_builder" in lines[3]


def test_format_table_empty_preserves_columns():
    columns = ["id", "username"]
    rows = []
    table_str = format_table(columns, rows)
    lines = table_str.strip().split("\n")
    assert len(lines) == 3
    assert "id" in lines[0] and "username" in lines[0]
    assert "-+-" in lines[1]
    assert "(0 rows)" in lines[2]


def test_format_table_nulls_and_unicode_and_wide():
    columns = ["id", "city", "emoji", "notes"]
    rows = [
        {"id": 1, "city": "München", "emoji": "🎉", "notes": None},
        {"id": 2, "city": "Tokyo", "emoji": "🚀", "notes": "w" * 60},
    ]
    table_str = format_table(columns, rows)
    assert "München" in table_str
    assert "🎉" in table_str
    assert "NULL" in table_str
    assert "..." in table_str


def test_format_json():
    rows = [
        {"id": 1, "name": "alice", "active": True, "balance": None},
        {"id": 2, "name": "München 🚀", "active": False, "data": b"blob_val"},
    ]
    json_str = format_json(rows)
    parsed = json.loads(json_str)
    assert parsed[0]["name"] == "alice"
    assert parsed[0]["balance"] is None
    assert parsed[1]["name"] == "München 🚀"
    assert "<blob: 8 bytes>" in parsed[1]["data"]

    # Empty
    assert json.loads(format_json([])) == []


def test_format_csv_with_blobs_and_nulls():
    columns = ["id", "name", "notes", "blob_col"]
    rows = [
        {"id": 1, "name": "alice", "notes": None, "blob_col": b"data"},
        {"id": 2, "name": "bob, jr.", "notes": "some notes", "blob_col": None},
    ]
    csv_str = format_csv(columns, rows)
    lines = csv_str.strip().split("\n")
    assert lines[0] == "id,name,notes,blob_col"
    assert lines[1] == "1,alice,,<blob: 4 bytes>"
    assert lines[2] == '2,"bob, jr.",some notes,'

    # Verify round-trip parsing
    reader = list(csv.reader(io.StringIO(csv_str)))
    assert len(reader) == 3
    assert reader[1][0] == "1"
    assert reader[2][1] == "bob, jr."


def test_safe_write_encoding_fallback():
    class MockLegacyStream:
        def __init__(self, encoding="ascii"):
            self.encoding = encoding
            self.buffer = []

        def write(self, s: str):
            # Test encoding to simulate ascii-only legacy console
            s.encode(self.encoding)
            self.buffer.append(s)

    stream = MockLegacyStream(encoding="ascii")
    # Writing ascii works normally
    safe_write(stream, "plain text\n")
    assert "plain text\n" in stream.buffer

    # Writing emoji/unicode falls back gracefully without raising UnicodeEncodeError
    safe_write(stream, "Hello 🚀 München\n")
    assert len(stream.buffer) == 2
    assert "Hello ? M?nchen" in stream.buffer[1]


def test_print_results_to_streams():
    columns = ["id", "name"]
    rows = [{"id": 1, "name": "alice"}]

    out = io.StringIO()
    err = io.StringIO()
    print_results(columns, rows, fmt="table", quiet=False, out_stream=out, err_stream=err)
    assert "alice" in out.getvalue()
    assert "(1 row)\n" in err.getvalue()

    # Quiet suppresses row counts on stderr
    out_q = io.StringIO()
    err_q = io.StringIO()
    print_results(columns, rows, fmt="table", quiet=True, out_stream=out_q, err_stream=err_q)
    assert "alice" in out_q.getvalue()
    assert err_q.getvalue() == ""
