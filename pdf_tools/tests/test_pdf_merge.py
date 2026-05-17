"""
tests/test_pdf_merge.py — integration tests for mergers/pdf_merge.py.

Runs the script against temporary PDF files generated with reportlab, reopens
the merged output with pypdf, and asserts that page counts are correct.
"""

# ruff: noqa: S101, S603, S607

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pypdf
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as rl_canvas

SCRIPT = Path(__file__).parent.parent / "mergers" / "pdf_merge.py"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_pdf(path: Path, n_pages: int = 1) -> Path:
    """Write a minimal PDF with n_pages pages to path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    c = rl_canvas.Canvas(str(path), pagesize=letter)
    for i in range(n_pages):
        c.setFont("Helvetica", 12)
        c.drawString(72, 700, f"Page {i + 1} of {path.name}")
        c.showPage()
    c.save()
    return path


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPdfMerge:
    def test_basic_two_file_merge(self, tmp_path: Path) -> None:
        """Merging two PDFs produces output with the combined page count."""
        a = _make_pdf(tmp_path / "a.pdf", n_pages=2)
        b = _make_pdf(tmp_path / "b.pdf", n_pages=3)
        out = tmp_path / "merged.pdf"

        result = _run([str(a), str(b), "--output", str(out)])
        assert result.returncode == 0, result.stderr

        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == 5

    def test_three_file_merge(self, tmp_path: Path) -> None:
        """Merging three PDFs accumulates all pages in order."""
        pdfs = [_make_pdf(tmp_path / f"p{i}.pdf", n_pages=i) for i in range(1, 4)]
        out = tmp_path / "all.pdf"
        result = _run([str(p) for p in pdfs] + ["--output", str(out)])
        assert result.returncode == 0, result.stderr
        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == 1 + 2 + 3

    def test_refuses_overwrite_without_force(self, tmp_path: Path) -> None:
        """Script must exit non-zero if output exists and --force is not given."""
        a = _make_pdf(tmp_path / "a.pdf")
        b = _make_pdf(tmp_path / "b.pdf")
        out = tmp_path / "merged.pdf"
        out.write_bytes(b"old")

        result = _run([str(a), str(b), "--output", str(out)])
        assert result.returncode != 0
        assert out.read_bytes() == b"old"

    def test_force_overwrites(self, tmp_path: Path) -> None:
        """With --force the existing output is replaced with a valid PDF."""
        a = _make_pdf(tmp_path / "a.pdf", n_pages=1)
        b = _make_pdf(tmp_path / "b.pdf", n_pages=2)
        out = tmp_path / "merged.pdf"
        out.write_bytes(b"stale")

        result = _run([str(a), str(b), "--output", str(out), "--force"])
        assert result.returncode == 0, result.stderr
        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) == 3

    def test_missing_input_fails(self, tmp_path: Path) -> None:
        """Script must exit non-zero if an input file does not exist."""
        a = _make_pdf(tmp_path / "a.pdf")
        missing = tmp_path / "missing.pdf"
        out = tmp_path / "merged.pdf"

        result = _run([str(a), str(missing), "--output", str(out)])
        assert result.returncode != 0

    def test_single_input_fails(self, tmp_path: Path) -> None:
        """Script requires at least two inputs; one input must fail."""
        a = _make_pdf(tmp_path / "a.pdf")
        out = tmp_path / "merged.pdf"

        result = _run([str(a), "--output", str(out)])
        assert result.returncode != 0

    def test_output_not_input(self, tmp_path: Path) -> None:
        """Script must refuse if output path equals one of the inputs."""
        a = _make_pdf(tmp_path / "a.pdf", n_pages=1)
        b = _make_pdf(tmp_path / "b.pdf", n_pages=1)

        # Output = a (one of the inputs)
        result = _run([str(a), str(b), "--output", str(a)])
        assert result.returncode != 0

    def test_help_exits_zero(self) -> None:
        """--help must exit with code 0."""
        result = _run(["--help"])
        assert result.returncode == 0
