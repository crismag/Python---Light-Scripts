"""
report_builders/invoice_generator.py — ADVANCED: styled invoice PDF from a JSON spec.

Reads a JSON invoice specification and generates a professional invoice PDF with:
  - Seller and buyer address blocks
  - Invoice metadata (number, date, due date)
  - Itemised line-item table with quantity, unit price, and line total
  - Automatically computed subtotal, tax, and grand total
  - Header bar and page-numbered footer
  - Optional notes and bank / payment details

Example commands:
    python report_builders/invoice_generator.py examples/sample_invoice.json \\
        --output out/invoice.pdf

    python report_builders/invoice_generator.py my_invoice.json \\
        --output invoices/INV-001.pdf --force
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = letter
MARGIN = 0.75 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

NAVY = colors.HexColor("#1a3a6b")
LIGHT_BLUE = colors.HexColor("#eef3fb")
GRID = colors.HexColor("#c8d3e8")
GOLD = colors.HexColor("#c8922a")
DARK = colors.HexColor("#222222")
MID = colors.HexColor("#555555")
WHITE = colors.white


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    def s(name: str, **kw: Any) -> ParagraphStyle:
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    return {
        "h1": s("h1", fontName="Helvetica-Bold", fontSize=20, textColor=NAVY, spaceAfter=2),
        "h2": s("h2", fontName="Helvetica-Bold", fontSize=12, textColor=NAVY, spaceAfter=2),
        "label": s("label", fontName="Helvetica-Bold", fontSize=8, textColor=MID),
        "value": s("value", fontName="Helvetica", fontSize=9, textColor=DARK, spaceAfter=1),
        "small": s("small", fontName="Helvetica", fontSize=8, textColor=MID),
        "note": s("note", fontName="Helvetica-Oblique", fontSize=8.5, textColor=MID, leading=13),
    }


# ---------------------------------------------------------------------------
# Footer callback
# ---------------------------------------------------------------------------


class _InvoiceDoc(SimpleDocTemplate):
    """SimpleDocTemplate that draws a page-number footer."""

    def __init__(self, *args: Any, inv_number: str = "", **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._inv_number = inv_number

    def handle_pageEnd(self) -> None:  # type: ignore[override]
        self._draw_footer()
        super().handle_pageEnd()

    def _draw_footer(self) -> None:
        c = self.canv
        y = MARGIN - 8
        c.setStrokeColor(GRID)
        c.setLineWidth(0.5)
        c.line(MARGIN, y, PAGE_W - MARGIN, y)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.HexColor("#888888"))
        c.drawString(MARGIN, y - 11, f"Invoice {self._inv_number} — Confidential")
        c.drawRightString(PAGE_W - MARGIN, y - 11, f"Page {self.page}")


# ---------------------------------------------------------------------------
# Amount helpers
# ---------------------------------------------------------------------------


def _fmt_money(amount: float, currency: str = "USD") -> str:
    """Format a float as a currency string, e.g. 'USD 1,234.56'."""
    return f"{currency} {amount:,.2f}"


def _compute_totals(line_items: list[dict[str, Any]], tax_rate_pct: float) -> dict[str, float]:
    subtotal = sum(
        float(item.get("quantity", 0)) * float(item.get("unit_price", 0))
        for item in line_items
    )
    tax = round(subtotal * tax_rate_pct / 100, 2)
    grand_total = round(subtotal + tax, 2)
    return {"subtotal": round(subtotal, 2), "tax": tax, "grand_total": grand_total}


# ---------------------------------------------------------------------------
# Core invoice builder
# ---------------------------------------------------------------------------


def build_invoice(output_path: Path, spec: dict[str, Any]) -> None:
    """
    Render a complete invoice PDF from a validated spec dict.

    Args:
        output_path: Destination path (parent dirs created if needed).
        spec:        Parsed invoice JSON; keys: invoice_number, invoice_date, due_date,
                     currency, seller, buyer, line_items, tax_rate_pct, notes, bank.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    inv_number = spec.get("invoice_number", "INV-XXXX")
    inv_date = spec.get("invoice_date", "")
    due_date = spec.get("due_date", "")
    currency = spec.get("currency", "USD")
    seller = spec.get("seller", {})
    buyer = spec.get("buyer", {})
    line_items: list[dict[str, Any]] = spec.get("line_items", [])
    tax_rate_pct = float(spec.get("tax_rate_pct", 0))
    notes = spec.get("notes", "")
    bank = spec.get("bank", {})

    totals = _compute_totals(line_items, tax_rate_pct)
    st = _styles()

    doc = _InvoiceDoc(
        str(output_path),
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN + 16,
        inv_number=inv_number,
        title=f"Invoice {inv_number}",
    )

    story: list = []

    # ---- Header bar --------------------------------------------------------
    header_data = [[
        Paragraph("INVOICE", st["h1"]),
        Paragraph(
            f"<b>Invoice #:</b>  {inv_number}<br/>"
            f"<b>Date:</b>       {inv_date}<br/>"
            f"<b>Due:</b>        {due_date}",
            st["value"],
        ),
    ]]
    header_ts = TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (0, 0), WHITE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 12),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
    ])
    header_tbl = Table(header_data, colWidths=[CONTENT_W * 0.5, CONTENT_W * 0.5])
    header_tbl.setStyle(header_ts)
    story.append(header_tbl)
    story.append(Spacer(1, 14))

    # ---- Seller / Buyer blocks ---------------------------------------------
    def _addr_block(party: dict[str, Any], label: str) -> list[Paragraph]:
        lines: list[Paragraph] = [Paragraph(label, st["label"])]
        lines.append(Paragraph(f"<b>{party.get('name', '')}</b>", st["value"]))
        for key in ("address", "city_state_zip", "email", "phone", "contact"):
            val = party.get(key, "")
            if val:
                lines.append(Paragraph(val, st["value"]))
        return lines

    addr_data = [[_addr_block(seller, "FROM"), _addr_block(buyer, "BILL TO")]]
    addr_ts = TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ])
    addr_tbl = Table(addr_data, colWidths=[CONTENT_W * 0.48, CONTENT_W * 0.48])
    addr_tbl.setStyle(addr_ts)
    story.append(addr_tbl)
    story.append(Spacer(1, 12))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY))
    story.append(Spacer(1, 10))

    # ---- Line items table --------------------------------------------------
    li_headers = ["#", "Description", "Qty", "Unit", "Unit Price", "Total"]
    col_w = [
        CONTENT_W * 0.04,
        CONTENT_W * 0.40,
        CONTENT_W * 0.07,
        CONTENT_W * 0.07,
        CONTENT_W * 0.18,
        CONTENT_W * 0.18,
    ]

    li_data: list[list[Any]] = [li_headers]
    for i, item in enumerate(line_items, start=1):
        qty = float(item.get("quantity", 0))
        price = float(item.get("unit_price", 0))
        total = qty * price
        li_data.append([
            str(i),
            item.get("description", ""),
            f"{qty:g}",
            item.get("unit", ""),
            _fmt_money(price, currency),
            _fmt_money(total, currency),
        ])

    li_ts = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("ROWBACKGROUND", (0, 1), (-1, -1), [WHITE, LIGHT_BLUE]),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("GRID", (0, 0), (-1, -1), 0.4, GRID),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("ALIGN", (2, 0), (2, -1), "CENTER"),   # Qty
        ("ALIGN", (4, 0), (5, -1), "RIGHT"),    # prices
    ])
    li_tbl = Table(li_data, colWidths=col_w, repeatRows=1)
    li_tbl.setStyle(li_ts)
    story.append(li_tbl)
    story.append(Spacer(1, 10))

    # ---- Totals block ------------------------------------------------------
    totals_data = [
        ["", "Subtotal:", _fmt_money(totals["subtotal"], currency)],
        ["", f"Tax ({tax_rate_pct:.1f}%):", _fmt_money(totals["tax"], currency)],
        ["", "Grand Total:", _fmt_money(totals["grand_total"], currency)],
    ]
    totals_col_w = [CONTENT_W * 0.58, CONTENT_W * 0.22, CONTENT_W * 0.18]
    totals_ts = TableStyle([
        ("FONTNAME", (0, 0), (-1, 1), "Helvetica"),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (1, 0), (2, -1), "RIGHT"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("BACKGROUND", (0, 2), (-1, 2), LIGHT_BLUE),
        ("LINEABOVE", (1, 2), (2, 2), 0.8, NAVY),
        ("TEXTCOLOR", (1, 2), (2, 2), NAVY),
    ])
    totals_tbl = Table(totals_data, colWidths=totals_col_w)
    totals_tbl.setStyle(totals_ts)
    story.append(totals_tbl)

    # ---- Notes -------------------------------------------------------------
    if notes:
        story.append(Spacer(1, 14))
        story.append(HRFlowable(width="100%", thickness=0.5, color=GRID))
        story.append(Spacer(1, 6))
        story.append(Paragraph("<b>Notes & Payment Terms</b>", st["label"]))
        story.append(Spacer(1, 3))
        story.append(Paragraph(notes, st["note"]))

    # ---- Bank details ------------------------------------------------------
    if bank:
        story.append(Spacer(1, 8))
        story.append(Paragraph("<b>Bank / Wire Transfer Details</b>", st["label"]))
        for k, v in bank.items():
            story.append(Paragraph(f"{k.replace('_', ' ').title()}: {v}", st["small"]))

    doc.build(story)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="invoice_generator.py",
        description="Generate a styled invoice PDF from a JSON specification.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("spec", metavar="JSON", help="Path to the invoice JSON file")
    p.add_argument("--output", required=True, metavar="PDF", help="Output PDF path")
    p.add_argument("--force", action="store_true", help="Overwrite output if it already exists")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    spec_path = Path(args.spec)
    output_path = Path(args.output)

    if not spec_path.exists():
        print(f"ERROR: spec file not found: {spec_path}", file=sys.stderr)
        return 1

    if output_path.exists() and not args.force:
        print(
            f"ERROR: output already exists: {output_path}\n       Pass --force to overwrite.",
            file=sys.stderr,
        )
        return 1

    try:
        spec: dict[str, Any] = json.loads(spec_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"ERROR: invalid JSON — {exc}", file=sys.stderr)
        return 1

    build_invoice(output_path, spec)
    print(f"Invoice PDF written: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
