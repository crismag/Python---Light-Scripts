"""
generators/table_report.py — INTERMEDIATE: paginated PDF table report from CSV or JSON.

Reads a CSV file (auto-detected headers) or a JSON file containing a list of objects,
then renders the data as a paginated table with column headers, alternating row shading,
and page numbers in the footer.

Example commands:
    python generators/table_report.py \\
        --input examples/sample_metrics.csv --output out/metrics_report.pdf

    python generators/table_report.py \\
        --input examples/sample_invoice.json --output out/invoice_table.pdf \\
        --title "Invoice Line Items" --force

    python generators/table_report.py \\
        --input data.csv --output report.pdf --columns Name,Value,Status
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Page geometry
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = letter
MARGIN = 0.75 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

# ---------------------------------------------------------------------------
# Colours
# ---------------------------------------------------------------------------
ACCENT = colors.HexColor("#1a3a6b")
HEADER_BG = ACCENT
HEADER_FG = colors.white
ALT_ROW = colors.HexColor("#eef2fb")
GRID = colors.HexColor("#c0c8d8")


# ---------------------------------------------------------------------------
# Data loading helpers (private)
# ---------------------------------------------------------------------------


def _load_csv(path: Path, columns: list[str] | None) -> tuple[list[str], list[list[str]]]:
    """Return (headers, rows) from a CSV file."""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        all_headers = reader.fieldnames or []
        if columns:
            headers = [c for c in columns if c in all_headers]
        else:
            headers = list(all_headers)
        rows = [[str(row.get(h, "")) for h in headers] for row in reader]
    return headers, rows


def _load_json(path: Path, columns: list[str] | None) -> tuple[list[str], list[list[str]]]:
    """Return (headers, rows) from a JSON file that is a list of objects or a dict with a list."""
    raw: Any = json.loads(path.read_text(encoding="utf-8"))

    # Unwrap common shapes: {"items": [...]} or {"line_items": [...]} etc.
    if isinstance(raw, dict):
        # Find the first key whose value is a non-empty list of dicts
        for v in raw.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                raw = v
                break
        else:
            # Flatten the dict itself into a single-row table
            raw = [raw]

    if not isinstance(raw, list) or not raw:
        raise ValueError("JSON file must contain a list of objects (or a dict with such a list).")

    all_headers = list(raw[0].keys()) if isinstance(raw[0], dict) else []
    if columns:
        headers = [c for c in columns if c in all_headers]
    else:
        headers = all_headers

    rows = [[str(item.get(h, "")) if isinstance(item, dict) else "" for h in headers] for item in raw]
    return headers, rows


# ---------------------------------------------------------------------------
# PDF canvas callback for footer
# ---------------------------------------------------------------------------


class _FooterCanvas(SimpleDocTemplate):
    """SimpleDocTemplate subclass that draws a page-number footer on every page."""

    def __init__(self, *args: Any, report_title: str = "", **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._report_title = report_title

    def handle_pageBegin(self) -> None:  # type: ignore[override]
        super().handle_pageBegin()

    def handle_pageEnd(self) -> None:  # type: ignore[override]
        self._draw_footer()
        super().handle_pageEnd()

    def _draw_footer(self) -> None:
        c = self.canv
        rule_y = MARGIN - 4
        c.setStrokeColor(GRID)
        c.setLineWidth(0.5)
        c.line(MARGIN, rule_y, PAGE_W - MARGIN, rule_y)
        c.setFont("Helvetica", 7.5)
        c.setFillColor(colors.HexColor("#888888"))
        if self._report_title:
            c.drawString(MARGIN, rule_y - 11, self._report_title)
        c.drawRightString(PAGE_W - MARGIN, rule_y - 11, f"Page {self.page}")


# ---------------------------------------------------------------------------
# Core report builder
# ---------------------------------------------------------------------------


def build_table_report(
    output_path: Path,
    headers: list[str],
    rows: list[list[str]],
    title: str = "Data Report",
    subtitle: str = "",
    max_col_w: float = 150.0,
) -> None:
    """
    Render headers + rows as a paginated PDF table report.

    Args:
        output_path: Destination PDF path.
        headers:     Column header strings.
        rows:        Table row data (list of string lists).
        title:       Report title shown on every page header.
        subtitle:    Optional subtitle below the title.
        max_col_w:   Maximum width per column in points.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = _FooterCanvas(
        str(output_path),
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN + 10,
        bottomMargin=MARGIN + 10,
        report_title=title,
        title=title,
    )

    title_style = ParagraphStyle(
        "RTitle",
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=ACCENT,
        spaceAfter=2,
    )
    sub_style = ParagraphStyle(
        "RSub",
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#555555"),
        spaceAfter=6,
    )
    meta_style = ParagraphStyle(
        "RMeta",
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#888888"),
        spaceAfter=0,
    )

    story: list = []
    story.append(Paragraph(title, title_style))
    if subtitle:
        story.append(Paragraph(subtitle, sub_style))
    story.append(Paragraph(f"{len(rows)} records", meta_style))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT, spaceAfter=8))

    # Build table data
    table_data = [headers] + rows

    # Auto column widths: proportional to header length, capped at max_col_w
    raw_widths = [max(len(h) * 7.5, 40) for h in headers]
    total_raw = sum(raw_widths)
    if total_raw > CONTENT_W:
        scale = CONTENT_W / total_raw
        col_widths = [min(w * scale, max_col_w) for w in raw_widths]
        # Distribute any leftover
        leftover = CONTENT_W - sum(col_widths)
        if leftover > 0:
            col_widths[-1] += leftover
    else:
        extra = (CONTENT_W - total_raw) / len(raw_widths)
        col_widths = [w + extra for w in raw_widths]

    # Table style
    ts = TableStyle(
        [
            # Header row
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), HEADER_FG),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 8.5),
            ("ROWBACKGROUND", (0, 1), (-1, -1), [colors.white, ALT_ROW]),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.35, GRID),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("REPEATROWS", (0, 0), (0, 0)),  # repeat header on new pages
        ]
    )

    tbl = Table(table_data, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(ts)
    story.append(tbl)

    doc.build(story)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="table_report.py",
        description="Render a CSV or JSON list of records as a paginated PDF table report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--input",
        required=True,
        metavar="FILE",
        help="Input CSV or JSON file (JSON must be a list of objects or dict with a list value)",
    )
    p.add_argument("--output", required=True, metavar="PDF", help="Output PDF path")
    p.add_argument("--title", default="", help="Report title (default: derived from filename)")
    p.add_argument("--subtitle", default="", help="Optional subtitle line")
    p.add_argument(
        "--columns",
        default="",
        metavar="COL1,COL2,...",
        help="Comma-separated column names to include (default: all)",
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

    columns = [c.strip() for c in args.columns.split(",") if c.strip()] if args.columns else None
    suffix = input_path.suffix.lower()

    try:
        if suffix == ".csv":
            headers, rows = _load_csv(input_path, columns)
        elif suffix == ".json":
            headers, rows = _load_json(input_path, columns)
        else:
            print(f"ERROR: unsupported file type '{suffix}'. Use .csv or .json", file=sys.stderr)
            return 1
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"ERROR loading input: {exc}", file=sys.stderr)
        return 1

    if not headers:
        print("ERROR: no columns found in input file.", file=sys.stderr)
        return 1

    title = args.title or input_path.stem.replace("_", " ").title()
    subtitle = args.subtitle or f"Source: {input_path.name}"

    build_table_report(
        output_path=output_path,
        headers=headers,
        rows=rows,
        title=title,
        subtitle=subtitle,
    )

    print(f"Table report written: {output_path}  ({len(rows)} rows, {len(headers)} columns)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
