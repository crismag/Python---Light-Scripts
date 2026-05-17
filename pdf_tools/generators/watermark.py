"""
generators/watermark.py — INTERMEDIATE: stamp a diagonal text watermark on every page.

Builds a single-page watermark PDF in memory with reportlab (transparent diagonal text),
then uses pypdf to overlay it on every page of the input document. The input file is
never modified; the watermarked result is written to --output.

Example commands:
    python generators/watermark.py input.pdf --text "CONFIDENTIAL" --output out/marked.pdf

    python generators/watermark.py report.pdf --text "DRAFT" --angle 35 \\
        --opacity 0.15 --font-size 72 --output out/draft_report.pdf --force
"""

from __future__ import annotations

import argparse
import io
import sys
from pathlib import Path

import pypdf
from reportlab.pdfgen import canvas as rl_canvas

# ---------------------------------------------------------------------------
# Core watermark logic
# ---------------------------------------------------------------------------


def _build_watermark_page(
    page_width: float,
    page_height: float,
    text: str,
    font_size: float,
    opacity: float,
    angle: float,
    color_rgb: tuple[float, float, float],
) -> io.BytesIO:
    """
    Render a single watermark page to an in-memory BytesIO buffer.

    The text is centred on the page and rotated by `angle` degrees.

    Args:
        page_width:  Target page width in points.
        page_height: Target page height in points.
        text:        Watermark string.
        font_size:   Font size in points.
        opacity:     Fill alpha (0=invisible, 1=opaque).
        angle:       Rotation angle in degrees.
        color_rgb:   RGB tuple (0-1 range) for the text colour.

    Returns:
        BytesIO buffer containing the rendered watermark PDF page.
    """
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(page_width, page_height))

    c.saveState()
    c.setFont("Helvetica-Bold", font_size)
    c.setFillAlpha(opacity)
    r, g, b = color_rgb
    c.setFillColorRGB(r, g, b)
    c.translate(page_width / 2, page_height / 2)
    c.rotate(angle)
    text_w = c.stringWidth(text, "Helvetica-Bold", font_size)
    c.drawString(-text_w / 2, -font_size / 3, text)
    c.restoreState()
    c.save()

    buf.seek(0)
    return buf


def apply_watermark(
    input_path: Path,
    output_path: Path,
    text: str = "CONFIDENTIAL",
    font_size: float = 64.0,
    opacity: float = 0.12,
    angle: float = 45.0,
    color_rgb: tuple[float, float, float] = (0.35, 0.35, 0.35),
) -> int:
    """
    Overlay a text watermark on every page of a PDF and write to output_path.

    Args:
        input_path:  Source PDF (never modified).
        output_path: Destination path for the watermarked PDF.
        text:        Watermark string.
        font_size:   Font size in points.
        opacity:     Watermark alpha (transparency).
        angle:       Rotation in degrees (45 = diagonal).
        color_rgb:   Watermark text colour as (R, G, B) each in [0, 1].

    Returns:
        Number of pages watermarked.

    Raises:
        ValueError: If output_path resolves to the same path as input_path.
    """
    if input_path.resolve() == output_path.resolve():
        raise ValueError("output_path must differ from input_path.")

    reader = pypdf.PdfReader(str(input_path))
    n_pages = len(reader.pages)

    # Build a watermark page sized to match the first page (covers most docs)
    first = reader.pages[0]
    pw = float(first.mediabox.width)
    ph = float(first.mediabox.height)

    wm_buf = _build_watermark_page(pw, ph, text, font_size, opacity, angle, color_rgb)
    wm_reader = pypdf.PdfReader(wm_buf)
    wm_page = wm_reader.pages[0]

    writer = pypdf.PdfWriter()
    for page in reader.pages:
        page.merge_page(wm_page)
        writer.add_page(page)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as fh:
        writer.write(fh)

    return n_pages


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="watermark.py",
        description="Stamp a diagonal text watermark across every page of a PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("input", metavar="INPUT_PDF", help="Source PDF file")
    p.add_argument("--text", default="CONFIDENTIAL", help="Watermark text (default: CONFIDENTIAL)")
    p.add_argument("--output", required=True, metavar="PDF", help="Output PDF path")
    p.add_argument(
        "--font-size",
        type=float,
        default=64.0,
        metavar="PT",
        help="Watermark font size in points (default: 64)",
    )
    p.add_argument(
        "--opacity",
        type=float,
        default=0.12,
        metavar="0-1",
        help="Watermark opacity 0=invisible 1=solid (default: 0.12)",
    )
    p.add_argument(
        "--angle",
        type=float,
        default=45.0,
        metavar="DEG",
        help="Rotation angle in degrees (default: 45)",
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

    if not (0.0 < args.opacity <= 1.0):
        print("ERROR: --opacity must be in range (0, 1]", file=sys.stderr)
        return 1

    try:
        n = apply_watermark(
            input_path=input_path,
            output_path=output_path,
            text=args.text,
            font_size=args.font_size,
            opacity=args.opacity,
            angle=args.angle,
        )
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Watermarked {n} page(s) — written to: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
