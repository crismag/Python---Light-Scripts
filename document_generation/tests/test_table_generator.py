"""Tests for document_generation/markdown/table_generator.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Make table_generator importable
sys.path.insert(0, str(Path(__file__).parent.parent / "markdown"))

import table_generator as tg  # noqa: E402

# ---------------------------------------------------------------------------
# Unit tests for internal helpers
# ---------------------------------------------------------------------------


class TestBuildMdTable:
    def test_basic_output(self) -> None:
        rows = [{"host": "srv-01", "role": "web"}, {"host": "srv-02", "role": "db"}]
        table = tg._build_md_table(rows, ["host", "role"])
        lines = table.splitlines()
        assert len(lines) == 4  # header + separator + 2 data rows
        assert "srv-01" in table
        assert "srv-02" in table

    def test_separator_row(self) -> None:
        rows  = [{"x": "a"}]
        table = tg._build_md_table(rows, ["x"])
        lines = table.splitlines()
        # Second line should be the separator
        assert all(c in "-| " for c in lines[1])

    def test_empty_rows_returns_placeholder(self) -> None:
        result = tg._build_md_table([], ["col"])
        assert result == "_No data._"

    def test_column_width_matches_widest_value(self) -> None:
        rows  = [{"name": "short"}, {"name": "a very long name"}]
        table = tg._build_md_table(rows, ["name"])
        # All rows should be the same width (padded)
        lines = table.splitlines()
        widths = [len(line) for line in lines]
        assert len(set(widths)) == 1


# ---------------------------------------------------------------------------
# Integration: load_records
# ---------------------------------------------------------------------------


class TestLoadRecords:
    def test_json_list(self, tmp_path: Path) -> None:
        f = tmp_path / "data.json"
        f.write_text(json.dumps([{"a": 1}, {"a": 2}]))
        records = tg.load_records(f, key=None)
        assert len(records) == 2
        assert records[0]["a"] == 1

    def test_json_object_with_key(self, tmp_path: Path) -> None:
        f = tmp_path / "proj.json"
        f.write_text(json.dumps({"team": [{"name": "Alice"}, {"name": "Bob"}]}))
        records = tg.load_records(f, key="team")
        assert len(records) == 2
        assert records[0]["name"] == "Alice"

    def test_csv(self, tmp_path: Path) -> None:
        f = tmp_path / "data.csv"
        f.write_text("host,role\nsrv-01,web\nsrv-02,db\n")
        records = tg.load_records(f, key=None)
        assert records[0]["host"] == "srv-01"

    def test_unsupported_extension_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "data.txt"
        f.write_text("hello")
        with pytest.raises(ValueError, match="Unsupported"):
            tg.load_records(f, key=None)


# ---------------------------------------------------------------------------
# Integration: generate_table (end-to-end with tmp files)
# ---------------------------------------------------------------------------


class TestGenerateTable:
    def test_csv_to_markdown(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "inv.csv"
        csv_file.write_text("hostname,role,status\nprod-01,web,online\nprod-02,db,online\n")
        out_file = tmp_path / "out.md"
        tg.generate_table(csv_file, out_file, force=True)
        content = out_file.read_text()
        assert "prod-01" in content
        assert "prod-02" in content
        assert "|" in content

    def test_json_list_to_markdown(self, tmp_path: Path) -> None:
        json_file = tmp_path / "data.json"
        json_file.write_text(json.dumps([{"name": "Alice", "role": "dev"}, {"name": "Bob", "role": "ops"}]))
        out_file  = tmp_path / "out.md"
        tg.generate_table(json_file, out_file, force=True)
        content = out_file.read_text()
        assert "Alice" in content
        assert "Bob" in content

    def test_with_title(self, tmp_path: Path) -> None:
        json_file = tmp_path / "data.json"
        json_file.write_text(json.dumps([{"x": "y"}]))
        out_file  = tmp_path / "out.md"
        tg.generate_table(json_file, out_file, title="My Table", force=True)
        content = out_file.read_text()
        assert "# My Table" in content

    def test_with_columns_subset(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("a,b,c\n1,2,3\n")
        out_file = tmp_path / "out.md"
        tg.generate_table(csv_file, out_file, columns=["a", "c"], force=True)
        content = out_file.read_text()
        assert "b" not in content
        assert "a" in content and "c" in content

    def test_no_overwrite_without_force(self, tmp_path: Path) -> None:
        json_file = tmp_path / "data.json"
        json_file.write_text(json.dumps([{"k": "v"}]))
        out_file = tmp_path / "out.md"
        out_file.write_text("existing content")
        with pytest.raises(SystemExit):
            tg.generate_table(json_file, out_file, force=False)

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("col\nval\n")
        out_file = tmp_path / "nested" / "deep" / "out.md"
        tg.generate_table(csv_file, out_file, force=True)
        assert out_file.exists()


# ---------------------------------------------------------------------------
# CLI via main()
# ---------------------------------------------------------------------------


class TestCLI:
    def test_main_csv(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("name,age\nAlice,30\nBob,25\n")
        out_file = tmp_path / "out.md"
        tg.main([str(csv_file), str(out_file)])
        assert out_file.exists()
        content = out_file.read_text()
        assert "Alice" in content

    def test_main_force_flag(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("x\n1\n")
        out_file = tmp_path / "out.md"
        out_file.write_text("original")
        tg.main([str(csv_file), str(out_file), "--force"])
        # File was overwritten
        assert out_file.read_text() != "original"

    def test_main_with_title(self, tmp_path: Path) -> None:
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("col\nval\n")
        out_file = tmp_path / "out.md"
        tg.main([str(csv_file), str(out_file), "--title", "Test Heading"])
        assert "# Test Heading" in out_file.read_text()
