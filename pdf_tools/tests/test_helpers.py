"""
tests/test_helpers.py — unit tests for pdf_tools/helpers.py.

Covers:
  - safe_merge_pdfs: output page count equals sum of input page counts
  - safe_merge_pdfs: refuses to overwrite existing output without force=True
  - safe_merge_pdfs: raises when output path equals an input path
  - apply_text_watermark: output page count equals input page count
  - apply_text_watermark: raises when output equals input path
  - draw_page_header / draw_page_footer / draw_data_table: produce a valid PDF
"""

# ruff: noqa: S101

from __future__ import annotations

import sys
from pathlib import Path

import pypdf
import pytest
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as rl_canvas

# Import this section's helpers under a fully-qualified module name. Each
# section has its own helpers.py; a bare `import helpers` would collide in
# sys.modules when the whole repo's tests run together.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pdf_tools.helpers as helpers  # noqa: E402

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_simple_pdf(path: Path, n_pages: int = 1) -> Path:
    """Write a minimal multi-page PDF to path and return path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(path), pagesize=letter)
    for i in range(n_pages):
        c.setFont("Helvetica", 12)
        c.drawString(72, 700, f"Page {i + 1}")
        c.showPage()
    c.save()
    return path


# ---------------------------------------------------------------------------
# safe_merge_pdfs tests
# ---------------------------------------------------------------------------


class TestSafeMergePdfs:
    def test_merged_page_count(self, tmp_path: Path) -> None:
        """Merged PDF must have exactly the sum of input page counts."""
        a = _make_simple_pdf(tmp_path / "a.pdf", n_pages=2)
        b = _make_simple_pdf(tmp_path / "b.pdf", n_pages=3)
        out = tmp_path / "merged.pdf"

        helpers.safe_merge_pdfs([a, b], out)

        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == 5

    def test_three_inputs(self, tmp_path: Path) -> None:
        """Works with three inputs; page count sums correctly."""
        pdfs = [_make_simple_pdf(tmp_path / f"doc{i}.pdf", n_pages=i) for i in range(1, 4)]
        out = tmp_path / "all.pdf"
        helpers.safe_merge_pdfs(pdfs, out)
        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == 1 + 2 + 3

    def test_refuses_overwrite_without_force(self, tmp_path: Path) -> None:
        """Raises FileExistsError if output exists and force=False."""
        a = _make_simple_pdf(tmp_path / "a.pdf")
        b = _make_simple_pdf(tmp_path / "b.pdf")
        out = tmp_path / "merged.pdf"
        out.write_bytes(b"placeholder")

        with pytest.raises(FileExistsError):
            helpers.safe_merge_pdfs([a, b], out, force=False)

    def test_force_overwrites(self, tmp_path: Path) -> None:
        """With force=True an existing output is overwritten."""
        a = _make_simple_pdf(tmp_path / "a.pdf", n_pages=1)
        b = _make_simple_pdf(tmp_path / "b.pdf", n_pages=1)
        out = tmp_path / "merged.pdf"
        out.write_bytes(b"old content")

        helpers.safe_merge_pdfs([a, b], out, force=True)
        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == 2

    def test_output_equals_input_raises(self, tmp_path: Path) -> None:
        """Raises ValueError if output is the same file as one of the inputs."""
        a = _make_simple_pdf(tmp_path / "a.pdf")
        b = _make_simple_pdf(tmp_path / "b.pdf")

        with pytest.raises(ValueError, match="must not be one of the inputs"):
            helpers.safe_merge_pdfs([a, b], a)

    def test_missing_input_raises(self, tmp_path: Path) -> None:
        """Raises FileNotFoundError if an input path does not exist."""
        a = _make_simple_pdf(tmp_path / "a.pdf")
        missing = tmp_path / "missing.pdf"
        out = tmp_path / "out.pdf"

        with pytest.raises(FileNotFoundError):
            helpers.safe_merge_pdfs([a, missing], out)


# ---------------------------------------------------------------------------
# apply_text_watermark tests
# ---------------------------------------------------------------------------


class TestApplyTextWatermark:
    def test_page_count_preserved(self, tmp_path: Path) -> None:
        """Watermarked output must have the same page count as input."""
        src = _make_simple_pdf(tmp_path / "src.pdf", n_pages=3)
        out = tmp_path / "watermarked.pdf"

        helpers.apply_text_watermark(src, out, text="DRAFT")

        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == 3

    def test_output_is_valid_pdf(self, tmp_path: Path) -> None:
        """Output file must be readable by pypdf without errors."""
        src = _make_simple_pdf(tmp_path / "src.pdf", n_pages=1)
        out = tmp_path / "wm.pdf"

        helpers.apply_text_watermark(src, out, text="CONFIDENTIAL")

        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) >= 1

    def test_raises_when_output_equals_input(self, tmp_path: Path) -> None:
        """Raises ValueError if output resolves to the same path as input."""
        src = _make_simple_pdf(tmp_path / "src.pdf")

        with pytest.raises(ValueError):
            helpers.apply_text_watermark(src, src, text="X")


# ---------------------------------------------------------------------------
# draw_page_header / draw_page_footer / draw_data_table smoke tests
# ---------------------------------------------------------------------------


class TestCanvasHelpers:
    def test_header_footer_table_produces_valid_pdf(self, tmp_path: Path) -> None:
        """draw_page_header, draw_page_footer, draw_data_table must not raise."""
        out = tmp_path / "canvas_test.pdf"
        c = rl_canvas.Canvas(str(out), pagesize=letter)

        helpers.draw_page_header(c, "Test Title", subtitle="Test subtitle")
        helpers.draw_data_table(
            c,
            headers=["Col A", "Col B", "Col C"],
            rows=[["1", "2", "3"], ["4", "5", "6"]],
            x=helpers.MARGIN,
            y=600,
        )
        helpers.draw_page_footer(c, page_number=1, total_pages=1, left_text="Test Corp")
        c.save()

        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == 1

    def test_multi_page_footer(self, tmp_path: Path) -> None:
        """draw_page_footer works correctly with multi-page 'Page N of M' text."""
        out = tmp_path / "multi_page.pdf"
        c = rl_canvas.Canvas(str(out), pagesize=letter)

        for pg in range(1, 4):
            helpers.draw_page_footer(c, page_number=pg, total_pages=3)
            c.showPage()
        c.save()

        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == 3
