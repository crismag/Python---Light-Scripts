"""
generators/simple_pdf.py — BEGINNER: generate a basic PDF from a title and body text.

The body text can be supplied directly via --text, read from a plain-text file via
--text-file, or both (file content is appended after the inline text). Long paragraphs
are wrapped automatically; page breaks are inserted as needed.

Example commands:
    python generators/simple_pdf.py --title "Hello World" --text "My first PDF." \\
        --output out/hello.pdf

    python generators/simple_pdf.py --title "Meeting Notes" --text-file notes.txt \\
        --author "Jane Smith" --output out/notes.pdf

    python generators/simple_pdf.py --title "Report" --text-file notes.txt \\
        --output out/report.pdf --force
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = letter
MARGIN = 0.85 * inch


# ---------------------------------------------------------------------------
# Core generation function
# ---------------------------------------------------------------------------


def generate_simple_pdf(
    output_path: Path,
    title: str,
    body_text: str,
    author: str = "",
    subject: str = "",
) -> None:
    """
    Build and write a simple single-column PDF with a title and body paragraphs.

    The body_text is split on blank lines to form separate paragraphs. Each
    paragraph is reflowed to fit the page width automatically.

    Args:
        output_path: Destination .pdf path (parent dirs will be created).
        title:       Document title shown at the top of the first page.
        body_text:   Body content; blank lines separate paragraphs.
        author:      Optional author name written to PDF metadata.
        subject:     Optional subject written to PDF metadata.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=title,
        author=author,
        subject=subject,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontSize=22,
        spaceAfter=6,
        textColor=colors.HexColor("#1a3a6b"),
        fontName="Helvetica-Bold",
    )

    author_style = ParagraphStyle(
        "CustomAuthor",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=4,
        textColor=colors.HexColor("#555555"),
        fontName="Helvetica-Oblique",
    )

    body_style = ParagraphStyle(
        "CustomBody",
        parent=styles["BodyText"],
        fontSize=11,
        leading=16,
        spaceAfter=10,
        fontName="Helvetica",
    )

    story: list = []

    # Title
    story.append(Paragraph(title, title_style))

    # Author line
    if author:
        story.append(Paragraph(f"Author: {author}", author_style))

    # Horizontal rule
    story.append(Spacer(1, 6))
    story.append(HRFlowable(width="100%", thickness=1.2, color=colors.HexColor("#1a3a6b")))
    story.append(Spacer(1, 12))

    # Body paragraphs — split on blank lines
    raw_paragraphs = body_text.strip().split("\n\n") if body_text.strip() else ["(no content)"]
    for raw in raw_paragraphs:
        # Collapse internal newlines to spaces within a paragraph
        cleaned = " ".join(line.strip() for line in raw.strip().splitlines() if line.strip())
        if cleaned:
            story.append(Paragraph(cleaned, body_style))

    doc.build(story)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="simple_pdf.py",
        description="Generate a basic PDF from a title and body text.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--title", required=True, help="Document title (shown at top of first page)")
    p.add_argument("--text", default="", help="Body text supplied directly on the command line")
    p.add_argument(
        "--text-file",
        metavar="FILE",
        help="Path to a plain-text file whose content becomes the body",
    )
    p.add_argument("--author", default="", help="Author name written to PDF metadata")
    p.add_argument("--subject", default="", help="Subject written to PDF metadata")
    p.add_argument("--output", required=True, metavar="PDF", help="Output PDF path")
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite the output file if it already exists",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output = Path(args.output)

    if output.exists() and not args.force:
        print(
            f"ERROR: output already exists: {output}\n"
            "       Pass --force to overwrite.",
            file=sys.stderr,
        )
        return 1

    # Assemble body text
    parts: list[str] = []
    if args.text:
        parts.append(args.text)
    if args.text_file:
        tf = Path(args.text_file)
        if not tf.exists():
            print(f"ERROR: text file not found: {tf}", file=sys.stderr)
            return 1
        parts.append(tf.read_text(encoding="utf-8"))

    body = "\n\n".join(parts) if parts else "(no content provided)"

    generate_simple_pdf(
        output_path=output,
        title=args.title,
        body_text=body,
        author=args.author,
        subject=args.subject,
    )

    print(f"PDF written: {output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
