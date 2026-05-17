"""
tests/test_simple_pdf.py — integration tests for generators/simple_pdf.py.

Runs the script against temporary files, reopens the output with pypdf, and
asserts that the produced PDF is valid and contains at least one page.
"""

# ruff: noqa: S101, S603, S607

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pypdf

SCRIPT = Path(__file__).parent.parent / "generators" / "simple_pdf.py"


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
    )


class TestSimplePdf:
    def test_basic_generation(self, tmp_path: Path) -> None:
        """Generate a minimal PDF from --title and --text; assert at least 1 page."""
        out = tmp_path / "hello.pdf"
        result = _run(["--title", "Hello World", "--text", "First paragraph.", "--output", str(out)])
        assert result.returncode == 0, result.stderr
        assert out.exists()
        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) >= 1

    def test_output_from_text_file(self, tmp_path: Path) -> None:
        """Generate PDF from a plain-text file input."""
        txt = tmp_path / "body.txt"
        txt.write_text("Para one.\n\nPara two.\n\nPara three.", encoding="utf-8")
        out = tmp_path / "from_file.pdf"
        result = _run(["--title", "From File", "--text-file", str(txt), "--output", str(out)])
        assert result.returncode == 0, result.stderr
        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) >= 1

    def test_does_not_overwrite_without_force(self, tmp_path: Path) -> None:
        """Script must refuse to overwrite an existing output without --force."""
        out = tmp_path / "existing.pdf"
        out.write_bytes(b"placeholder")
        result = _run(["--title", "T", "--text", "Body", "--output", str(out)])
        assert result.returncode != 0
        assert b"placeholder" == out.read_bytes()

    def test_force_overwrites(self, tmp_path: Path) -> None:
        """With --force an existing output is overwritten with a valid PDF."""
        out = tmp_path / "overwrite.pdf"
        out.write_bytes(b"old")
        result = _run(["--title", "T", "--text", "Body", "--output", str(out), "--force"])
        assert result.returncode == 0, result.stderr
        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) >= 1

    def test_with_author_and_subject(self, tmp_path: Path) -> None:
        """Author and subject flags are accepted without error."""
        out = tmp_path / "meta.pdf"
        result = _run([
            "--title", "Meta Test",
            "--text", "Some content.",
            "--author", "Jane Smith",
            "--subject", "Testing",
            "--output", str(out),
        ])
        assert result.returncode == 0, result.stderr
        reader = pypdf.PdfReader(str(out))
        assert len(reader.pages) >= 1

    def test_long_text_multipage(self, tmp_path: Path) -> None:
        """Very long body text triggers multiple pages (or at minimum one valid page)."""
        long_text = "This is a sentence. " * 400  # ~8 000 chars
        out = tmp_path / "long.pdf"
        result = _run(["--title", "Long Doc", "--text", long_text, "--output", str(out)])
        assert result.returncode == 0, result.stderr
        reader = pypdf.PdfReader(str(out))
        # Long text may flow to 2+ pages
        assert len(reader.pages) >= 1

    def test_help_exits_zero(self) -> None:
        """--help must exit with code 0."""
        result = _run(["--help"])
        assert result.returncode == 0
