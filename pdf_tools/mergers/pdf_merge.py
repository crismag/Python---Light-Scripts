"""
mergers/pdf_merge.py — INTERMEDIATE: merge multiple PDFs into one output file.

Accepts two or more PDF paths as positional arguments and writes them concatenated
into --output. By default refuses to overwrite an existing output; pass --force to
allow it. The input files are never modified and the output path must not coincide
with any input path.

Example commands:
    python mergers/pdf_merge.py a.pdf b.pdf c.pdf --output out/merged.pdf

    python mergers/pdf_merge.py cover.pdf body.pdf appendix.pdf \\
        --output report_final.pdf --force
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pypdf

# ---------------------------------------------------------------------------
# Core merge function
# ---------------------------------------------------------------------------


def merge_pdfs(
    input_paths: list[Path],
    output_path: Path,
    force: bool = False,
) -> int:
    """
    Merge a list of PDF files into a single output PDF.

    Args:
        input_paths: Ordered list of source PDF paths (must exist).
        output_path: Destination path for the merged PDF.
        force:       If True, overwrite an existing output file.

    Returns:
        Total number of pages in the merged output.

    Raises:
        FileNotFoundError: If any input path does not exist.
        ValueError:        If output_path resolves to one of the input paths.
        FileExistsError:   If output_path exists and force is False.
    """
    output_path = output_path.resolve()
    resolved: list[Path] = []

    for p in input_paths:
        rp = p.resolve()
        if not rp.exists():
            raise FileNotFoundError(f"Input PDF not found: {rp}")
        if rp == output_path:
            raise ValueError(
                f"Output path must not be one of the input files: {rp}\n"
                "This guard prevents accidentally overwriting a source document."
            )
        resolved.append(rp)

    if output_path.exists() and not force:
        raise FileExistsError(
            f"Output already exists: {output_path}\n"
            "Pass --force (or force=True) to overwrite."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = pypdf.PdfWriter()
    total_pages = 0

    for rp in resolved:
        reader = pypdf.PdfReader(str(rp))
        for page in reader.pages:
            writer.add_page(page)
            total_pages += 1

    with open(output_path, "wb") as fh:
        writer.write(fh)

    return total_pages


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pdf_merge.py",
        description="Merge two or more PDF files into a single output PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "inputs",
        nargs="+",
        metavar="PDF",
        help="Two or more input PDF files (in merge order)",
    )
    p.add_argument("--output", required=True, metavar="PDF", help="Output merged PDF path")
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output file if it already exists",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if len(args.inputs) < 2:
        print("ERROR: provide at least two input PDFs to merge.", file=sys.stderr)
        return 1

    input_paths = [Path(p) for p in args.inputs]
    output_path = Path(args.output)

    try:
        total = merge_pdfs(input_paths, output_path, force=args.force)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except (ValueError, FileExistsError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(
        f"Merged {len(input_paths)} PDF(s) → {output_path}  "
        f"({total} total pages)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
