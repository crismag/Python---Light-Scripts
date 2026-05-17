"""
mergers/pdf_split.py — INTERMEDIATE: split a PDF into per-page or page-range files.

By default writes one PDF per page into --output-dir. Optionally accepts --ranges
(e.g. 1-3 4-6 8) to split into named multi-page chunks. Page numbers are 1-based.
The input file is never modified; output paths are checked for path-traversal attacks.

Example commands:
    # Per-page split (default)
    python mergers/pdf_split.py report.pdf --output-dir out/pages/

    # Named page-range split
    python mergers/pdf_split.py report.pdf --output-dir out/parts/ --ranges 1-3 4-6 7-10

    # Single pages specified individually
    python mergers/pdf_split.py book.pdf --output-dir out/pages/ --ranges 1 2 3 5 --force
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pypdf

# ---------------------------------------------------------------------------
# Range parsing helpers
# ---------------------------------------------------------------------------


def _parse_range(spec: str, max_page: int) -> tuple[int, int]:
    """
    Parse a page-range specifier like "3" or "2-5" into a (start, end) 1-based inclusive tuple.

    Args:
        spec:     Range string (e.g. "3" or "2-5").
        max_page: Total page count of the source PDF.

    Returns:
        (start, end) where 1 <= start <= end <= max_page.

    Raises:
        ValueError: If the spec is malformed or out of bounds.
    """
    spec = spec.strip()
    if re.fullmatch(r"\d+", spec):
        n = int(spec)
        if not (1 <= n <= max_page):
            raise ValueError(f"Page {n} is out of range (document has {max_page} pages).")
        return n, n
    m = re.fullmatch(r"(\d+)-(\d+)", spec)
    if not m:
        raise ValueError(
            f"Invalid range specifier '{spec}'. Use a page number or 'start-end' (e.g. 2-5)."
        )
    start, end = int(m.group(1)), int(m.group(2))
    if start > end:
        raise ValueError(f"Range start ({start}) must be <= end ({end}).")
    if start < 1 or end > max_page:
        raise ValueError(
            f"Range {start}-{end} is out of bounds (document has {max_page} pages)."
        )
    return start, end


def _safe_output_path(output_dir: Path, filename: str) -> Path:
    """
    Resolve filename inside output_dir and guard against path-traversal.

    Args:
        output_dir: Validated output directory path.
        filename:   Relative filename for the split PDF chunk.

    Returns:
        Absolute path inside output_dir.

    Raises:
        ValueError: If the resolved path escapes output_dir.
    """
    resolved = (output_dir / filename).resolve()
    if not str(resolved).startswith(str(output_dir.resolve())):
        raise ValueError(f"Path traversal detected for filename: {filename!r}")
    return resolved


# ---------------------------------------------------------------------------
# Core split function
# ---------------------------------------------------------------------------


def split_pdf(
    input_path: Path,
    output_dir: Path,
    ranges: list[str] | None = None,
    force: bool = False,
) -> list[Path]:
    """
    Split a PDF by pages or page ranges and write chunks to output_dir.

    Args:
        input_path: Source PDF (never modified).
        output_dir: Directory where split PDFs are written (created if needed).
        ranges:     List of range specs like ["1-3", "4-6", "7"].
                    If None, one file per page is produced.
        force:      Overwrite existing output files if True.

    Returns:
        List of written output paths.

    Raises:
        FileNotFoundError: If input_path does not exist.
        ValueError:        If any range is malformed or out of bounds.
        FileExistsError:   If an output file exists and force is False.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    reader = pypdf.PdfReader(str(input_path))
    n_pages = len(reader.pages)
    stem = input_path.stem
    written: list[Path] = []

    if not ranges:
        # Per-page mode
        for i in range(n_pages):
            filename = f"{stem}_page_{i + 1:04d}.pdf"
            out = _safe_output_path(output_dir, filename)
            if out.exists() and not force:
                raise FileExistsError(
                    f"Output already exists: {out}\nPass --force to overwrite."
                )
            writer = pypdf.PdfWriter()
            writer.add_page(reader.pages[i])
            with open(out, "wb") as fh:
                writer.write(fh)
            written.append(out)
    else:
        # Page-range mode
        parsed = [_parse_range(r, n_pages) for r in ranges]
        for start, end in parsed:
            if start == end:
                filename = f"{stem}_p{start:04d}.pdf"
            else:
                filename = f"{stem}_p{start:04d}-p{end:04d}.pdf"
            out = _safe_output_path(output_dir, filename)
            if out.exists() and not force:
                raise FileExistsError(
                    f"Output already exists: {out}\nPass --force to overwrite."
                )
            writer = pypdf.PdfWriter()
            for pg_num in range(start - 1, end):  # pypdf is 0-indexed
                writer.add_page(reader.pages[pg_num])
            with open(out, "wb") as fh:
                writer.write(fh)
            written.append(out)

    return written


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pdf_split.py",
        description="Split a PDF into per-page or page-range files in an output directory.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("input", metavar="PDF", help="Source PDF file to split")
    p.add_argument(
        "--output-dir",
        required=True,
        metavar="DIR",
        help="Directory to write the split PDF files",
    )
    p.add_argument(
        "--ranges",
        nargs="+",
        metavar="RANGE",
        help=(
            "Page ranges to extract (1-based, inclusive). "
            "Examples: --ranges 1-3 4-6 8  (omit for one-file-per-page)"
        ),
    )
    p.add_argument("--force", action="store_true", help="Overwrite existing output files")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = Path(args.input)
    output_dir = Path(args.output_dir)

    try:
        written = split_pdf(
            input_path=input_path,
            output_dir=output_dir,
            ranges=args.ranges,
            force=args.force,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except (ValueError, FileExistsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Split {input_path.name} → {len(written)} file(s) in: {output_dir}")
    for p in written:
        print(f"  {p.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
