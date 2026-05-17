"""
extractors/pdf_text_extract.py — INTERMEDIATE: extract text and metadata from a PDF.

Reads every page of a PDF with pypdf, extracts the text content and the document
metadata (title, author, subject, creator, dates), and writes the result to either:
  - A plain .txt file (default / --format txt): pages separated by a header line.
  - A structured .json file (--format json): {"metadata": {...}, "pages": [{"page":1, "text":"..."}, ...]}.

Example commands:
    python extractors/pdf_text_extract.py report.pdf --output out/text.txt

    python extractors/pdf_text_extract.py report.pdf --output out/meta.json --format json

    python extractors/pdf_text_extract.py report.pdf --output out/text.txt \\
        --pages 1-3 --force
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import pypdf

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_page_range(spec: str, n_pages: int) -> list[int]:
    """
    Parse a page-range spec like "1-3,5,7-9" into a sorted list of 0-based indices.

    Args:
        spec:    Comma-separated page numbers / ranges (1-based, inclusive).
        n_pages: Total page count of the document.

    Returns:
        Sorted list of 0-based page indices.
    """
    indices: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if re.fullmatch(r"\d+", part):
            p = int(part)
            if not (1 <= p <= n_pages):
                raise ValueError(f"Page {p} out of range (1-{n_pages}).")
            indices.add(p - 1)
        else:
            m = re.fullmatch(r"(\d+)-(\d+)", part)
            if not m:
                raise ValueError(f"Invalid page spec: '{part}'. Use '3' or '2-5'.")
            s, e = int(m.group(1)), int(m.group(2))
            if s > e or s < 1 or e > n_pages:
                raise ValueError(f"Range {s}-{e} out of bounds (1-{n_pages}).")
            indices.update(range(s - 1, e))
    return sorted(indices)


def _extract_metadata(reader: pypdf.PdfReader) -> dict[str, Any]:
    """
    Extract document metadata from a pypdf PdfReader into a plain dict.

    Args:
        reader: Open PdfReader instance.

    Returns:
        Dict with keys: title, author, subject, creator, producer, creation_date,
        mod_date, n_pages.
    """
    meta = reader.metadata or {}

    def _get(key: str) -> str:
        val = meta.get(key, "")
        return str(val) if val else ""

    return {
        "title": _get("/Title"),
        "author": _get("/Author"),
        "subject": _get("/Subject"),
        "creator": _get("/Creator"),
        "producer": _get("/Producer"),
        "creation_date": _get("/CreationDate"),
        "mod_date": _get("/ModDate"),
        "n_pages": len(reader.pages),
    }


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------


def extract_text(
    input_path: Path,
    output_path: Path,
    fmt: str = "txt",
    page_indices: list[int] | None = None,
) -> dict[str, Any]:
    """
    Extract text and metadata from a PDF and write the result to output_path.

    Args:
        input_path:   Source PDF path.
        output_path:  Destination path (.txt or .json).
        fmt:          Output format: "txt" or "json".
        page_indices: 0-based page indices to extract; None means all pages.

    Returns:
        Dict with "metadata" and "pages" keys (same structure as JSON output).

    Raises:
        FileNotFoundError: If input_path does not exist.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Input PDF not found: {input_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    reader = pypdf.PdfReader(str(input_path))
    metadata = _extract_metadata(reader)

    indices = page_indices if page_indices is not None else list(range(len(reader.pages)))
    pages: list[dict[str, Any]] = []
    for idx in indices:
        text = reader.pages[idx].extract_text() or ""
        pages.append({"page": idx + 1, "text": text.strip()})

    result: dict[str, Any] = {"metadata": metadata, "pages": pages}

    if fmt == "json":
        output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        lines: list[str] = [
            f"File: {input_path.name}",
            f"Pages extracted: {len(pages)} / {metadata['n_pages']}",
            "",
            "=== METADATA ===",
        ]
        for k, v in metadata.items():
            if v:
                lines.append(f"  {k}: {v}")
        for pg in pages:
            lines.append("")
            lines.append(f"{'=' * 40} Page {pg['page']} {'=' * 40}")
            lines.append(pg["text"] or "(no text)")
        output_path.write_text("\n".join(lines), encoding="utf-8")

    return result


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pdf_text_extract.py",
        description="Extract text and metadata from a PDF to a .txt or .json file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("input", metavar="PDF", help="Source PDF file")
    p.add_argument("--output", required=True, metavar="FILE", help="Output .txt or .json path")
    p.add_argument(
        "--format",
        choices=["txt", "json"],
        default="txt",
        dest="fmt",
        help="Output format: 'txt' (default) or 'json'",
    )
    p.add_argument(
        "--pages",
        default="",
        metavar="SPEC",
        help=(
            "Comma-separated page numbers/ranges to extract, e.g. '1-3,5,7-9' "
            "(default: all pages)"
        ),
    )
    p.add_argument("--force", action="store_true", help="Overwrite output if it already exists")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        return 1

    if output_path.exists() and not args.force:
        print(
            f"ERROR: output already exists: {output_path}\n       Pass --force to overwrite.",
            file=sys.stderr,
        )
        return 1

    # Parse optional page filter
    page_indices: list[int] | None = None
    if args.pages:
        try:
            reader_tmp = pypdf.PdfReader(str(input_path))
            n_pages = len(reader_tmp.pages)
            page_indices = _parse_page_range(args.pages, n_pages)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

    try:
        result = extract_text(
            input_path=input_path,
            output_path=output_path,
            fmt=args.fmt,
            page_indices=page_indices,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    meta = result["metadata"]
    n_extracted = len(result["pages"])
    print(
        f"Extracted {n_extracted} page(s) from '{input_path.name}' "
        f"(total: {meta['n_pages']}) → {output_path}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
