"""
tests/test_pdf_gutter_adjust.py — tests for transformers/pdf_gutter_adjust.py.

Combines unit tests on the shift / page-selection logic with integration tests
that run the script against temporary PDFs generated with reportlab.
"""

# ruff: noqa: S101, S603, S607

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pypdf
import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as rl_canvas

SCRIPT = Path(__file__).parent.parent / "transformers" / "pdf_gutter_adjust.py"


def _load_module():
    """Import pdf_gutter_adjust.py as a module for direct unit testing."""
    spec = importlib.util.spec_from_file_location("pdf_gutter_adjust", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclass field resolution can see the module.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


mod = _load_module()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_pdf(path: Path, n_pages: int = 4) -> Path:
    """Write a minimal multi-page PDF to path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(path), pagesize=letter)
    for i in range(n_pages):
        c.setFont("Helvetica", 12)
        c.drawString(72, 700, f"Page {i + 1}")
        c.showPage()
    c.save()
    return path


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args], capture_output=True, text=True
    )


def _options(**kwargs):
    return mod.PdfGutterAdjustOptions(**kwargs)


def _adjuster(**kwargs):
    return mod.PdfGutterAdjuster(_options(**kwargs))


# ---------------------------------------------------------------------------
# Unit tests — geometry
# ---------------------------------------------------------------------------


class TestUnitConversion:
    def test_inches_to_points(self) -> None:
        assert mod.PdfGutterAdjuster._convert_to_points(0.25, "in") == pytest.approx(18.0)

    def test_points_passthrough(self) -> None:
        assert mod.PdfGutterAdjuster._convert_to_points(18, "pt") == 18.0

    def test_millimetres_to_points(self) -> None:
        assert mod.PdfGutterAdjuster._convert_to_points(25.4, "mm") == pytest.approx(72.0)


class TestPageShift:
    def test_recto_odd_page_moves_right(self) -> None:
        """With first page right-hand, page 1 (odd) shifts in +X."""
        adj = _adjuster(input_pdf=Path("x.pdf"), shift_amount=0.25, unit="in")
        shift_x, shift_y = adj._get_page_shift(1)
        assert shift_x == pytest.approx(18.0)
        assert shift_y == 0.0

    def test_recto_even_page_moves_left(self) -> None:
        """Page 2 (even) shifts in -X for a right-hand first page."""
        adj = _adjuster(input_pdf=Path("x.pdf"), shift_amount=0.25, unit="in")
        shift_x, _ = adj._get_page_shift(2)
        assert shift_x == pytest.approx(-18.0)

    def test_first_page_left_inverts_directions(self) -> None:
        """A left-hand first page makes odd pages move left, even pages right."""
        adj = _adjuster(
            input_pdf=Path("x.pdf"),
            shift_amount=0.25,
            unit="in",
            odd_page_direction="left",
            even_page_direction="right",
        )
        assert adj._get_page_shift(1)[0] == pytest.approx(-18.0)
        assert adj._get_page_shift(2)[0] == pytest.approx(18.0)

    def test_explicit_axis_override_wins(self) -> None:
        """shift_x_odd overrides the direction-derived shift for odd pages."""
        adj = _adjuster(
            input_pdf=Path("x.pdf"),
            shift_amount=0.25,
            unit="pt",
            shift_x_odd=5,
            shift_y_odd=3,
        )
        assert adj._get_page_shift(1) == (5.0, 3.0)

    def test_direction_none_yields_zero(self) -> None:
        adj = _adjuster(
            input_pdf=Path("x.pdf"),
            shift_amount=0.25,
            unit="in",
            odd_page_direction="none",
        )
        assert adj._get_page_shift(1)[0] == 0.0


# ---------------------------------------------------------------------------
# Unit tests — page selection
# ---------------------------------------------------------------------------


class TestPageSelection:
    def test_parse_mixed_spec(self) -> None:
        result = mod.PdfGutterAdjuster._parse_page_selection("1-3,7,10-12")
        assert result == {1, 2, 3, 7, 10, 11, 12}

    def test_parse_none_and_empty(self) -> None:
        assert mod.PdfGutterAdjuster._parse_page_selection(None) is None
        assert mod.PdfGutterAdjuster._parse_page_selection("  ") is None

    def test_parse_invalid_raises(self) -> None:
        with pytest.raises(mod.PdfGutterAdjustError):
            mod.PdfGutterAdjuster._parse_page_selection("1-x")

    def test_parse_reversed_range_raises(self) -> None:
        with pytest.raises(mod.PdfGutterAdjustError):
            mod.PdfGutterAdjuster._parse_page_selection("9-2")

    def test_should_process_respects_range_and_skip(self) -> None:
        adj = _adjuster(
            input_pdf=Path("x.pdf"), page_range="1-10", skip_pages="3,4"
        )
        adj._validate_options()
        assert adj._should_process_page(2) is True
        assert adj._should_process_page(3) is False
        assert adj._should_process_page(11) is False

    def test_only_pages_restricts(self) -> None:
        adj = _adjuster(input_pdf=Path("x.pdf"), only_pages="5,6")
        adj._validate_options()
        assert adj._should_process_page(5) is True
        assert adj._should_process_page(7) is False


# ---------------------------------------------------------------------------
# Integration tests — running the script
# ---------------------------------------------------------------------------


class TestCli:
    def test_basic_run_preserves_page_count_and_size(self, tmp_path: Path) -> None:
        src = _make_pdf(tmp_path / "book.pdf", n_pages=6)
        out = tmp_path / "out.pdf"
        result = _run([str(src), str(out), "--shift", "0.25"])
        assert result.returncode == 0, result.stderr

        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == 6
        # MediaBox unchanged (preserve_boxes default).
        assert float(reader.pages[0].mediabox.width) == pytest.approx(letter[0])
        assert float(reader.pages[0].mediabox.height) == pytest.approx(letter[1])

    def test_refuses_existing_output_without_overwrite(self, tmp_path: Path) -> None:
        src = _make_pdf(tmp_path / "book.pdf")
        out = tmp_path / "out.pdf"
        out.write_bytes(b"old")
        result = _run([str(src), str(out), "--shift", "0.25"])
        assert result.returncode != 0
        assert out.read_bytes() == b"old"

    def test_overwrite_allows_replacement(self, tmp_path: Path) -> None:
        src = _make_pdf(tmp_path / "book.pdf", n_pages=3)
        out = tmp_path / "out.pdf"
        out.write_bytes(b"stale")
        result = _run([str(src), str(out), "--shift", "0.25", "--overwrite"])
        assert result.returncode == 0, result.stderr
        assert len(pypdf.PdfReader(str(out)).pages) == 3

    def test_missing_input_fails(self, tmp_path: Path) -> None:
        result = _run([str(tmp_path / "nope.pdf"), str(tmp_path / "o.pdf")])
        assert result.returncode != 0
        assert "does not exist" in result.stderr

    def test_non_pdf_input_fails(self, tmp_path: Path) -> None:
        bad = tmp_path / "notes.txt"
        bad.write_text("hi")
        result = _run([str(bad), str(tmp_path / "o.pdf")])
        assert result.returncode != 0

    def test_invalid_page_range_fails(self, tmp_path: Path) -> None:
        src = _make_pdf(tmp_path / "book.pdf")
        result = _run(
            [str(src), str(tmp_path / "o.pdf"), "--page-range", "5-1"]
        )
        assert result.returncode != 0

    def test_dry_run_writes_nothing(self, tmp_path: Path) -> None:
        src = _make_pdf(tmp_path / "book.pdf")
        out = tmp_path / "out.pdf"
        result = _run([str(src), str(out), "--shift", "0.25", "--dry-run"])
        assert result.returncode == 0, result.stderr
        assert not out.exists()
        assert "dry-run" in result.stdout

    def test_derived_output_name_with_suffix(self, tmp_path: Path) -> None:
        src = _make_pdf(tmp_path / "book.pdf", n_pages=2)
        result = _run([str(src), "--shift", "0.25", "--suffix", "_wide"])
        assert result.returncode == 0, result.stderr
        assert (tmp_path / "book_wide.pdf").exists()

    def test_batch_mode_processes_folder(self, tmp_path: Path) -> None:
        in_dir = tmp_path / "pdfs"
        out_dir = tmp_path / "adjusted"
        _make_pdf(in_dir / "a.pdf", n_pages=2)
        _make_pdf(in_dir / "b.pdf", n_pages=3)
        result = _run(
            ["--batch-dir", str(in_dir), "--output-dir", str(out_dir), "--shift", "0.25"]
        )
        assert result.returncode == 0, result.stderr
        assert (out_dir / "a_gutter_adjusted.pdf").exists()
        assert (out_dir / "b_gutter_adjusted.pdf").exists()

    def test_batch_empty_folder_fails(self, tmp_path: Path) -> None:
        in_dir = tmp_path / "empty"
        in_dir.mkdir()
        result = _run(
            ["--batch-dir", str(in_dir), "--output-dir", str(tmp_path / "o")]
        )
        assert result.returncode != 0

    def test_help_exits_zero(self) -> None:
        assert _run(["--help"]).returncode == 0
