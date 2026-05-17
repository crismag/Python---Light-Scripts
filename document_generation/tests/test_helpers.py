"""Tests for document_generation/helpers.py — standalone reference module."""

from __future__ import annotations

import json

# ---------------------------------------------------------------------------
# Import this section's helpers under a fully-qualified module name. Each
# section has its own helpers.py; a bare `import helpers` would collide in
# sys.modules when the whole repo's tests run together.
# ---------------------------------------------------------------------------
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import document_generation.helpers as helpers  # noqa: E402

# ---------------------------------------------------------------------------
# render_template
# ---------------------------------------------------------------------------


class TestRenderTemplate:
    def test_simple_substitution(self) -> None:
        result = helpers.render_template("Hello, {{ name }}!", {"name": "World"})
        assert result == "Hello, World!"

    def test_nested_variable(self) -> None:
        ctx = {"version": {"major": 2, "minor": 4}}
        result = helpers.render_template("v{{ version.major }}.{{ version.minor }}", ctx)
        assert result == "v2.4"

    def test_loop(self) -> None:
        tmpl   = "{% for item in items %}- {{ item }}\n{% endfor %}"
        result = helpers.render_template(tmpl, {"items": ["a", "b", "c"]})
        assert "- a" in result
        assert "- b" in result
        assert "- c" in result

    def test_empty_context(self) -> None:
        result = helpers.render_template("static text", {})
        assert result == "static text"

    def test_strict_undefined_raises(self) -> None:
        from jinja2 import UndefinedError
        with pytest.raises(UndefinedError):
            helpers.render_template("{{ missing_var }}", {})


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------


class TestSlugify:
    def test_basic(self) -> None:
        assert helpers.slugify("Table of Contents") == "table-of-contents"

    def test_numbers_preserved(self) -> None:
        assert helpers.slugify("Q2 2026 Report") == "q2-2026-report"

    def test_strips_leading_trailing_hyphens(self) -> None:
        slug = helpers.slugify("  heading  ")
        assert not slug.startswith("-")
        assert not slug.endswith("-")

    def test_lowercases(self) -> None:
        assert helpers.slugify("ALL CAPS") == "all-caps"

    def test_collapse_spaces(self) -> None:
        slug = helpers.slugify("a  b")
        assert "  " not in slug
        assert slug == "a-b"


# ---------------------------------------------------------------------------
# build_md_table
# ---------------------------------------------------------------------------


class TestBuildMdTable:
    def test_basic_table(self) -> None:
        rows = [{"alpha": 1, "beta": 2}, {"alpha": 3, "beta": 4}]
        table = helpers.build_md_table(rows)
        lines = table.splitlines()
        assert lines[0].startswith("|")
        assert lines[1].startswith("|")  # separator
        # Separator line contains hyphens between pipes
        assert all(c in "-| " for c in lines[1])
        assert "---" in lines[1]  # column headers are >= 3 chars so separator is >=3 dashes
        assert len(lines) == 4  # header + sep + 2 data rows

    def test_column_order(self) -> None:
        rows = [{"z": "last", "a": "first"}]
        table = helpers.build_md_table(rows, columns=["a", "z"])
        header_line = table.splitlines()[0]
        assert header_line.index("a") < header_line.index("z")

    def test_empty_rows_raises(self) -> None:
        with pytest.raises(ValueError):
            helpers.build_md_table([])

    def test_custom_columns_subset(self) -> None:
        rows = [{"name": "Alice", "age": 30, "city": "NYC"}]
        table = helpers.build_md_table(rows, columns=["name", "city"])
        assert "age" not in table

    def test_pipe_delimited(self) -> None:
        rows = [{"x": "hello"}]
        table = helpers.build_md_table(rows)
        assert "|" in table


# ---------------------------------------------------------------------------
# build_md_toc
# ---------------------------------------------------------------------------


class TestBuildMdToc:
    def test_h1_and_h2(self) -> None:
        md  = "# Intro\n## Background\n## Goals\n# Architecture"
        toc = helpers.build_md_toc(md)
        assert "[Intro]" in toc
        assert "[Background]" in toc
        assert "[Architecture]" in toc

    def test_indentation_for_h2(self) -> None:
        md  = "# Top\n## Sub"
        toc = helpers.build_md_toc(md)
        lines = toc.splitlines()
        # H1 at column 0, H2 indented
        assert not lines[0].startswith("  ")
        assert lines[1].startswith("  ")

    def test_no_headings(self) -> None:
        assert helpers.build_md_toc("Just a paragraph.") == ""

    def test_anchor_links_present(self) -> None:
        md  = "# Hello World"
        toc = helpers.build_md_toc(md)
        assert "(#hello-world)" in toc


# ---------------------------------------------------------------------------
# load_data_file
# ---------------------------------------------------------------------------


class TestLoadDataFile:
    def test_load_json(self, tmp_path: Path) -> None:
        f = tmp_path / "data.json"
        f.write_text(json.dumps([{"a": 1}, {"a": 2}]))
        result = helpers.load_data_file(f)
        assert isinstance(result, list)
        assert result[0]["a"] == 1

    def test_load_yaml(self, tmp_path: Path) -> None:
        f = tmp_path / "data.yaml"
        f.write_text("key: value\nnum: 42\n")
        result = helpers.load_data_file(f)
        assert result["key"] == "value"
        assert result["num"] == 42

    def test_load_yml_extension(self, tmp_path: Path) -> None:
        f = tmp_path / "data.yml"
        f.write_text("items:\n  - one\n  - two\n")
        result = helpers.load_data_file(f)
        assert "items" in result

    def test_load_csv(self, tmp_path: Path) -> None:
        f = tmp_path / "data.csv"
        f.write_text("name,age\nAlice,30\nBob,25\n")
        result = helpers.load_data_file(f)
        assert isinstance(result, list)
        assert result[0]["name"] == "Alice"
        assert result[1]["age"] == "25"

    def test_unsupported_extension_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "data.txt"
        f.write_text("hello")
        with pytest.raises(ValueError, match="Unsupported"):
            helpers.load_data_file(f)

    def test_file_not_found_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            helpers.load_data_file(tmp_path / "nonexistent.json")
