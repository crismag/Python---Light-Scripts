"""
pdf_tools/helpers.py — standalone reference module of reusable PDF utility functions.

This file is a *study and copy reference* — it is NOT imported by any sibling script.
Copy individual functions into your own scripts as needed.

Covers:
  - draw_page_header()        : branded page header on a reportlab canvas
  - draw_page_footer()        : page-numbered footer on a reportlab canvas
  - draw_data_table()         : simple grid table on a canvas (no Platypus required)
  - apply_text_watermark()    : diagonal text watermark overlaid on an existing PDF
  - safe_merge_pdfs()         : merge a list of PDF paths into one output

Demo (self-test):
    python pdf_tools/helpers.py
"""

from __future__ import annotations

import io
import tempfile
from collections.abc import Sequence
from pathlib import Path

import pypdf
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as rl_canvas

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = letter  # 612 x 792 pts
MARGIN = 0.75 * inch


# ---------------------------------------------------------------------------
# Header / footer
# ---------------------------------------------------------------------------


def draw_page_header(
    c: rl_canvas.Canvas,
    title: str,
    subtitle: str = "",
    page_width: float = PAGE_W,
    y_top: float = PAGE_H - MARGIN,
    accent_color: tuple[float, float, float] = (0.15, 0.35, 0.65),
) -> None:
    """
    Draw a branded page header at the top of the current canvas page.

    Draws a filled rectangle accent bar, the document title in white, and an
    optional subtitle in dark grey below the bar.

    Args:
        c:            Active reportlab Canvas.
        title:        Primary heading text.
        subtitle:     Optional secondary heading (printed below bar in grey).
        page_width:   Page width in points (default: US Letter).
        y_top:        Top y-coordinate of the header block.
        accent_color: RGB tuple (0-1) for the header bar background.
    """
    bar_h = 28.0
    bar_y = y_top - bar_h

    # Accent bar
    r, g, b = accent_color
    c.setFillColorRGB(r, g, b)
    c.rect(MARGIN, bar_y, page_width - 2 * MARGIN, bar_h, stroke=0, fill=1)

    # Title text (white, inside bar)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN + 8, bar_y + 8, title)

    # Subtitle below bar
    if subtitle:
        c.setFillColorRGB(0.3, 0.3, 0.3)
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN + 8, bar_y - 14, subtitle)


def draw_page_footer(
    c: rl_canvas.Canvas,
    page_number: int,
    total_pages: int | None = None,
    left_text: str = "",
    page_width: float = PAGE_W,
    y_bottom: float = MARGIN,
) -> None:
    """
    Draw a page footer with a horizontal rule, left annotation, and page number.

    Args:
        c:            Active reportlab Canvas.
        page_number:  Current page number (1-based).
        total_pages:  Total pages for "Page N of M" display; None shows "Page N".
        left_text:    Text to display on the left side of the footer.
        page_width:   Page width in points.
        y_bottom:     Bottom margin y-coordinate.
    """
    rule_y = y_bottom + 18
    # Horizontal rule
    c.setStrokeColorRGB(0.7, 0.7, 0.7)
    c.setLineWidth(0.5)
    c.line(MARGIN, rule_y, page_width - MARGIN, rule_y)

    # Left text
    c.setFillColorRGB(0.45, 0.45, 0.45)
    c.setFont("Helvetica", 8)
    if left_text:
        c.drawString(MARGIN, rule_y - 12, left_text)

    # Page number (right-aligned)
    if total_pages is not None:
        pg_text = f"Page {page_number} of {total_pages}"
    else:
        pg_text = f"Page {page_number}"
    c.drawRightString(page_width - MARGIN, rule_y - 12, pg_text)


# ---------------------------------------------------------------------------
# Data table
# ---------------------------------------------------------------------------


def draw_data_table(
    c: rl_canvas.Canvas,
    headers: Sequence[str],
    rows: Sequence[Sequence[str]],
    x: float,
    y: float,
    col_widths: Sequence[float] | None = None,
    row_height: float = 18.0,
    header_color: tuple[float, float, float] = (0.15, 0.35, 0.65),
    alt_row_color: tuple[float, float, float] = (0.94, 0.96, 1.0),
    font_size: float = 9.0,
) -> float:
    """
    Draw a simple grid table on the canvas and return the y-coordinate below it.

    Args:
        c:             Active reportlab Canvas.
        headers:       Column header strings.
        rows:          Sequence of row sequences (strings).
        x:             Left x-coordinate of the table.
        y:             Top y-coordinate of the table.
        col_widths:    Per-column widths in points; None auto-distributes to 6.5 in total.
        row_height:    Height of each row in points.
        header_color:  RGB fill for the header row background.
        alt_row_color: RGB fill for alternating body rows.
        font_size:     Font size for body text.

    Returns:
        y-coordinate immediately below the last drawn row.
    """
    n_cols = len(headers)
    if col_widths is None:
        total_w = PAGE_W - 2 * MARGIN
        col_widths = [total_w / n_cols] * n_cols

    pad = 4.0

    def draw_row(
        row_y: float,
        texts: Sequence[str],
        bg: tuple[float, float, float] | None,
        bold: bool = False,
        text_color: tuple[float, float, float] = (0.1, 0.1, 0.1),
    ) -> None:
        total_w = sum(col_widths)
        if bg:
            c.setFillColorRGB(*bg)
            c.rect(x, row_y - row_height, total_w, row_height, stroke=0, fill=1)

        c.setStrokeColorRGB(0.75, 0.75, 0.75)
        c.setLineWidth(0.4)
        cx = x
        for w in col_widths:
            c.rect(cx, row_y - row_height, w, row_height, stroke=1, fill=0)
            cx += w

        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, font_size)
        c.setFillColorRGB(*text_color)
        cx = x
        for i, text in enumerate(texts):
            c.drawString(cx + pad, row_y - row_height + pad + 2, str(text)[: 60])
            cx += col_widths[i]

    # Header row
    draw_row(y, headers, header_color, bold=True, text_color=(1.0, 1.0, 1.0))
    cur_y = y - row_height

    for idx, row in enumerate(rows):
        bg = alt_row_color if idx % 2 == 1 else None
        padded = list(row) + [""] * (n_cols - len(row))
        draw_row(cur_y, padded[:n_cols], bg)
        cur_y -= row_height

    return cur_y


# ---------------------------------------------------------------------------
# Watermark
# ---------------------------------------------------------------------------


def apply_text_watermark(
    input_pdf: str | Path,
    output_pdf: str | Path,
    text: str = "CONFIDENTIAL",
    font_size: float = 60.0,
    opacity: float = 0.12,
    angle: float = 45.0,
) -> Path:
    """
    Overlay a diagonal text watermark on every page of an existing PDF.

    Builds a one-page watermark PDF in memory with reportlab, then uses pypdf
    to merge (overlay) it onto each page of the input document.

    Args:
        input_pdf:  Path to the source PDF.
        output_pdf: Path for the watermarked output (must not equal input_pdf).
        text:       Watermark string.
        font_size:  Font size for the watermark text in points.
        opacity:    Alpha for the watermark (0 = invisible, 1 = opaque).
        angle:      Rotation angle in degrees (default 45 for diagonal).

    Returns:
        Path to the written output PDF.

    Raises:
        ValueError: If output_pdf resolves to the same path as input_pdf.
    """
    input_pdf = Path(input_pdf).resolve()
    output_pdf = Path(output_pdf).resolve()
    if input_pdf == output_pdf:
        raise ValueError("output_pdf must differ from input_pdf to avoid overwriting the source.")

    # Build in-memory watermark page (A4/letter agnostic — use Letter for stamp)
    wm_buf = io.BytesIO()
    reader = pypdf.PdfReader(str(input_pdf))
    first_page = reader.pages[0]
    pw = float(first_page.mediabox.width)
    ph = float(first_page.mediabox.height)

    c = rl_canvas.Canvas(wm_buf, pagesize=(pw, ph))
    c.setFont("Helvetica-Bold", font_size)
    c.setFillAlpha(opacity)
    c.setFillColorRGB(0.4, 0.4, 0.4)

    c.saveState()
    c.translate(pw / 2, ph / 2)
    c.rotate(angle)
    text_w = c.stringWidth(text, "Helvetica-Bold", font_size)
    c.drawString(-text_w / 2, -font_size / 2, text)
    c.restoreState()
    c.save()

    wm_buf.seek(0)
    wm_reader = pypdf.PdfReader(wm_buf)
    wm_page = wm_reader.pages[0]

    writer = pypdf.PdfWriter()
    for page in reader.pages:
        page.merge_page(wm_page)
        writer.add_page(page)

    output_pdf.parent.mkdir(parents=True, exist_ok=True)
    with open(output_pdf, "wb") as fh:
        writer.write(fh)

    return output_pdf


# ---------------------------------------------------------------------------
# Safe merge
# ---------------------------------------------------------------------------


def safe_merge_pdfs(
    input_paths: Sequence[str | Path],
    output_path: str | Path,
    force: bool = False,
) -> Path:
    """
    Merge a list of PDF files into a single output PDF.

    Safety rules:
      - Raises FileNotFoundError if any input does not exist.
      - Raises ValueError if output_path resolves to any of the input paths.
      - Raises FileExistsError if output already exists and force=False.

    Args:
        input_paths: Ordered list of PDF paths to merge.
        output_path: Destination path for the merged PDF.
        force:       Overwrite existing output if True.

    Returns:
        Path to the written output PDF.
    """
    output_path = Path(output_path).resolve()
    resolved_inputs: list[Path] = []

    for p in input_paths:
        rp = Path(p).resolve()
        if not rp.exists():
            raise FileNotFoundError(f"Input PDF not found: {rp}")
        if rp == output_path:
            raise ValueError(f"Output path must not be one of the inputs: {rp}")
        resolved_inputs.append(rp)

    if output_path.exists() and not force:
        raise FileExistsError(
            f"Output already exists: {output_path}  (pass force=True to overwrite)"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    writer = pypdf.PdfWriter()
    for rp in resolved_inputs:
        reader = pypdf.PdfReader(str(rp))
        for page in reader.pages:
            writer.add_page(page)

    with open(output_path, "wb") as fh:
        writer.write(fh)

    return output_path


# ---------------------------------------------------------------------------
# Self-demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    out_dir = Path(tempfile.mkdtemp(prefix="pdf_helpers_demo_"))
    print(f"Writing demo PDFs to: {out_dir}")

    # --- Demo 1: header + footer + table ---
    demo1_path = out_dir / "demo_header_footer_table.pdf"
    c = rl_canvas.Canvas(str(demo1_path), pagesize=letter)

    headers = ["Server", "Region", "CPU %", "Memory %", "Status"]
    rows = [
        ["web-01", "us-east-1", "62.4", "78.1", "Healthy"],
        ["db-primary", "us-east-1", "34.7", "88.5", "Healthy"],
        ["worker-01", "us-east-1", "78.3", "55.2", "Warning"],
        ["cache-01", "us-east-1", "12.8", "94.3", "Healthy"],
    ]
    col_w = [120, 90, 60, 80, 70]

    draw_page_header(c, "Infrastructure Status Report", subtitle="Generated by helpers.py demo")
    draw_data_table(c, headers, rows, x=MARGIN, y=PAGE_H - MARGIN - 60, col_widths=col_w)
    draw_page_footer(c, page_number=1, total_pages=1, left_text="Acme Corp — Confidential")
    c.save()

    reader_check = pypdf.PdfReader(str(demo1_path))
    print(f"  demo_header_footer_table.pdf — {len(reader_check.pages)} page(s) OK")

    # --- Demo 2: watermark ---
    demo2_input = out_dir / "to_watermark.pdf"
    c2 = rl_canvas.Canvas(str(demo2_input), pagesize=letter)
    c2.setFont("Helvetica", 14)
    c2.drawString(MARGIN, PAGE_H / 2, "This page will receive a watermark.")
    c2.showPage()
    c2.drawString(MARGIN, PAGE_H / 2, "Page two — also watermarked.")
    c2.save()

    demo2_out = out_dir / "watermarked.pdf"
    apply_text_watermark(demo2_input, demo2_out, text="DRAFT")
    r2 = pypdf.PdfReader(str(demo2_out))
    print(f"  watermarked.pdf — {len(r2.pages)} page(s) OK")

    # --- Demo 3: safe merge ---
    pdfs_to_merge = [demo1_path, demo2_out]
    merged = out_dir / "merged.pdf"
    safe_merge_pdfs(pdfs_to_merge, merged)
    r3 = pypdf.PdfReader(str(merged))
    expected = len(pypdf.PdfReader(str(demo1_path)).pages) + len(r2.pages)
    print(f"  merged.pdf — {len(r3.pages)} pages (expected {expected}) OK")

    print("All helpers demo completed successfully.")
    sys.exit(0)
