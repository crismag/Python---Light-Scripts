"""
report_builders/engineering_report.py — SHOWCASE: multi-section engineering/audit report PDF.

Generates a polished, multi-page report containing:
  - Cover page with title, project details, and a decorative accent bar
  - Auto-generated Table of Contents (section number + title + page)
  - Multiple body sections with formatted headers and body text
  - A data table (infrastructure metrics)
  - A simple bar chart drawn with reportlab Drawing / VerticalBarChart
  - Page-numbered header and footer on every non-cover page

The report is driven by a built-in data set so it runs standalone with no input files.
Pass --output to choose the destination path.

Example commands:
    python report_builders/engineering_report.py --output out/engineering_report.pdf

    python report_builders/engineering_report.py \\
        --title "Q1 Infrastructure Audit" --project "Acme Corp" \\
        --output out/q1_audit.pdf --force
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
PAGE_W, PAGE_H = letter
MARGIN = 0.85 * inch
CONTENT_W = PAGE_W - 2 * MARGIN
CONTENT_H = PAGE_H - 2 * MARGIN

NAVY = colors.HexColor("#1a3a6b")
STEEL = colors.HexColor("#2e6da4")
LIGHT = colors.HexColor("#eef2fb")
GRID = colors.HexColor("#c0c8d8")
GOLD = colors.HexColor("#c8922a")
WHITE = colors.white
DARK = colors.HexColor("#1a1a1a")
MID = colors.HexColor("#555555")

# ---------------------------------------------------------------------------
# Built-in sample data
# ---------------------------------------------------------------------------

SECTIONS = [
    {
        "title": "Executive Summary",
        "body": (
            "This report presents the findings of the Q1 2024 infrastructure audit conducted "
            "across all production zones. Overall system health is rated GOOD, with two worker "
            "nodes flagged for elevated CPU utilisation requiring immediate attention.\n\n"
            "Uptime metrics across the web tier exceeded the 99.5 % SLA target. Database "
            "replication lag remained within acceptable thresholds throughout the quarter. "
            "Cache hit rates averaged 97.2 %, reducing upstream database pressure significantly."
        ),
    },
    {
        "title": "Scope & Methodology",
        "body": (
            "The audit covered 15 production hosts across two AWS regions (us-east-1 and "
            "us-west-2). Metrics were collected via Prometheus at 15-second intervals and "
            "aggregated to hourly means for trend analysis.\n\n"
            "Each host was classified into one of five tiers: Web, Database, Cache, Worker, "
            "and Load Balancer. Thresholds for each tier were agreed with the Platform team "
            "prior to the audit period. Any metric exceeding its tier threshold for more than "
            "30 consecutive minutes was logged as a finding."
        ),
    },
    {
        "title": "Infrastructure Metrics",
        "body": (
            "The table below summarises mean resource utilisation per host for the audit period. "
            "Hosts with a Status of Warning exceeded at least one tier threshold. No hosts "
            "entered a Critical state during Q1."
        ),
    },
    {
        "title": "CPU Utilisation — Bar Chart",
        "body": (
            "The chart below visualises mean CPU utilisation for a representative sample of "
            "hosts. Worker nodes show the highest utilisation, which is consistent with the "
            "batch workloads processed during Q1. Web nodes remain well below the 80 % "
            "warning threshold."
        ),
    },
    {
        "title": "Findings & Recommendations",
        "body": (
            "Finding 1 — Worker CPU saturation: worker-01 and worker-02 sustained CPU "
            "utilisation above 78 % for extended periods. Recommendation: scale the worker "
            "fleet horizontally by two additional nodes before Q2 batch peak.\n\n"
            "Finding 2 — Database memory pressure: db-primary memory utilisation reached "
            "88.5 %, approaching the 90 % warning threshold. Recommendation: review query "
            "plans for the top-10 slowest queries and evaluate upgrading the instance type "
            "from r6g.2xlarge to r6g.4xlarge.\n\n"
            "Finding 3 — Cache memory headroom: cache-01 memory at 94.3 %. "
            "Recommendation: enable Redis maxmemory-policy allkeys-lru to prevent eviction "
            "storms and schedule a capacity review."
        ),
    },
    {
        "title": "Conclusion",
        "body": (
            "The Q1 2024 infrastructure audit confirmed that the majority of production "
            "systems are operating within defined SLA parameters. Three actionable findings "
            "were identified, all with clear remediation paths. The Platform team should "
            "prioritise the worker-fleet horizontal scale-out before the Q2 scheduled "
            "batch processing window commences on 1 April 2024.\n\n"
            "The next audit is scheduled for end of Q2 2024. All findings from this report "
            "will be tracked in the internal issue tracker under project INFRA-AUDIT."
        ),
    },
]

TABLE_HEADERS = ["Host", "Region", "CPU %", "Mem %", "Disk %", "RPS", "Status"]
TABLE_ROWS = [
    ["web-01", "us-east-1", "62.4", "78.1", "45.2", "1423", "Healthy"],
    ["web-02", "us-east-1", "58.9", "71.3", "43.7", "1387", "Healthy"],
    ["db-primary", "us-east-1", "34.7", "88.5", "72.6", "412", "Healthy"],
    ["db-replica-1", "us-east-1", "18.3", "82.1", "71.9", "388", "Healthy"],
    ["cache-01", "us-east-1", "12.8", "94.3", "15.4", "8241", "Healthy"],
    ["worker-01", "us-east-1", "78.3", "55.2", "28.9", "0", "Warning"],
    ["worker-02", "us-east-1", "81.6", "58.7", "31.2", "0", "Warning"],
    ["lb-01", "us-east-1", "8.4", "22.1", "12.3", "2810", "Healthy"],
]

CHART_HOSTS = ["web-01", "web-02", "db-primary", "cache-01", "worker-01", "worker-02", "lb-01"]
CHART_CPU = [62.4, 58.9, 34.7, 12.8, 78.3, 81.6, 8.4]


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------


def _make_styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()

    def s(name: str, **kw: Any) -> ParagraphStyle:
        return ParagraphStyle(name, parent=base["Normal"], **kw)

    return {
        "toc_title": s("toc_title", fontName="Helvetica-Bold", fontSize=14, textColor=NAVY, spaceAfter=6),
        "toc_entry": s("toc_entry", fontName="Helvetica", fontSize=10, textColor=DARK, leading=18),
        "section_h": s(
            "section_h", fontName="Helvetica-Bold", fontSize=13, textColor=NAVY, spaceBefore=6, spaceAfter=4
        ),
        "body": s("body", fontName="Helvetica", fontSize=10, leading=15, textColor=DARK, spaceAfter=8),
        "caption": s("caption", fontName="Helvetica-Oblique", fontSize=8.5, textColor=MID, spaceAfter=10),
    }


# ---------------------------------------------------------------------------
# Page templates
# ---------------------------------------------------------------------------


class _ReportDoc(BaseDocTemplate):
    """BaseDocTemplate subclass with cover + body page templates and running header/footer."""

    def __init__(self, filename: str, report_title: str, project: str, **kw: Any) -> None:
        super().__init__(filename, **kw)
        self._report_title = report_title
        self._project = project
        self._toc_entries: list[tuple[int, str]] = []  # (section_num, title)

        # Cover frame — full page, no header/footer
        cover_frame = Frame(MARGIN, MARGIN, CONTENT_W, CONTENT_H, id="cover")
        cover_tpl = PageTemplate(id="Cover", frames=[cover_frame])

        # Body frame — leaves room for header (top) and footer (bottom)
        body_frame = Frame(
            MARGIN,
            MARGIN + 24,
            CONTENT_W,
            CONTENT_H - 48,
            id="body",
        )
        body_tpl = PageTemplate(
            id="Body",
            frames=[body_frame],
            onPage=self._draw_body_chrome,
        )

        self.addPageTemplates([cover_tpl, body_tpl])

    def _draw_body_chrome(self, canvas: Any, doc: Any) -> None:
        """Header bar + footer rule on every body page."""
        # Header bar
        bar_h = 22
        canvas.setFillColor(NAVY)
        canvas.rect(MARGIN, PAGE_H - MARGIN - bar_h, CONTENT_W, bar_h, stroke=0, fill=1)
        canvas.setFillColor(WHITE)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawString(MARGIN + 6, PAGE_H - MARGIN - bar_h + 7, self._report_title)
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(PAGE_W - MARGIN - 6, PAGE_H - MARGIN - bar_h + 7, self._project)

        # Footer
        footer_y = MARGIN + 8
        canvas.setStrokeColor(GRID)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN, footer_y, PAGE_W - MARGIN, footer_y)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(colors.HexColor("#888888"))
        canvas.drawString(MARGIN, footer_y - 11, "Confidential — Internal Use Only")
        canvas.drawRightString(PAGE_W - MARGIN, footer_y - 11, f"Page {doc.page}")


# ---------------------------------------------------------------------------
# Chart builder
# ---------------------------------------------------------------------------


def _build_bar_chart(hosts: list[str], values: list[float], chart_w: float = 420) -> Drawing:
    """Return a reportlab Drawing containing a labelled VerticalBarChart."""
    chart_h_px = 160
    d = Drawing(chart_w, chart_h_px + 30)

    bc = VerticalBarChart()
    bc.x = 40
    bc.y = 30
    bc.width = chart_w - 60
    bc.height = chart_h_px
    bc.data = [values]

    bc.bars[0].fillColor = STEEL
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = 100
    bc.valueAxis.valueStep = 20
    bc.valueAxis.labels.fontName = "Helvetica"
    bc.valueAxis.labels.fontSize = 7
    bc.categoryAxis.categoryNames = hosts
    bc.categoryAxis.labels.fontName = "Helvetica"
    bc.categoryAxis.labels.fontSize = 7
    bc.categoryAxis.labels.angle = 30
    bc.categoryAxis.labels.dy = -12

    # Warning threshold line (80 %)
    from reportlab.graphics.shapes import Line
    warn_y = bc.y + (80 / 100) * bc.height
    warn_line = Line(bc.x, warn_y, bc.x + bc.width, warn_y)
    warn_line.strokeColor = colors.HexColor("#d94040")
    warn_line.strokeWidth = 1
    warn_line.strokeDashArray = [4, 3]
    d.add(warn_line)

    d.add(bc)

    # Legend label for threshold line
    lbl = String(bc.x + bc.width + 4, warn_y - 3, "80 % threshold", fontName="Helvetica", fontSize=7)
    lbl.fillColor = colors.HexColor("#d94040")
    d.add(lbl)

    return d


# ---------------------------------------------------------------------------
# Core report builder
# ---------------------------------------------------------------------------


def build_engineering_report(
    output_path: Path,
    report_title: str = "Infrastructure Audit Report",
    project: str = "Acme Corp — Q1 2024",
    author: str = "Platform Engineering Team",
    date_str: str = "2024-03-31",
) -> None:
    """
    Build and write the engineering report PDF.

    Args:
        output_path:  Destination .pdf path.
        report_title: Main report title shown on cover and header.
        project:      Project / company name.
        author:       Author shown on cover page.
        date_str:     Report date shown on cover page.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    st = _make_styles()

    doc = _ReportDoc(
        str(output_path),
        report_title=report_title,
        project=project,
        pagesize=letter,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN + 28,
        bottomMargin=MARGIN + 28,
        title=report_title,
        author=author,
    )

    story: list = []

    # ================================================================
    # COVER PAGE
    # ================================================================
    story.append(Spacer(1, 1.6 * inch))

    # Top accent bar
    story.append(HRFlowable(width="100%", thickness=6, color=NAVY, spaceAfter=0))
    story.append(HRFlowable(width="100%", thickness=2, color=GOLD, spaceAfter=16))

    cover_title_style = ParagraphStyle(
        "CoverTitle",
        fontName="Helvetica-Bold",
        fontSize=28,
        textColor=NAVY,
        leading=34,
        spaceAfter=8,
    )
    cover_sub_style = ParagraphStyle(
        "CoverSub",
        fontName="Helvetica",
        fontSize=14,
        textColor=MID,
        spaceAfter=6,
    )
    cover_meta_style = ParagraphStyle(
        "CoverMeta",
        fontName="Helvetica",
        fontSize=10,
        textColor=MID,
        spaceAfter=4,
    )

    story.append(Paragraph(report_title, cover_title_style))
    story.append(Paragraph(project, cover_sub_style))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRID, spaceAfter=12))
    story.append(Paragraph(f"Author: {author}", cover_meta_style))
    story.append(Paragraph(f"Date: {date_str}", cover_meta_style))
    story.append(Paragraph("Classification: Confidential — Internal Use Only", cover_meta_style))
    story.append(Spacer(1, 0.6 * inch))
    story.append(HRFlowable(width="100%", thickness=2, color=GOLD, spaceAfter=0))
    story.append(HRFlowable(width="100%", thickness=6, color=NAVY, spaceAfter=0))

    # Switch to body template
    story.append(NextPageTemplate("Body"))
    story.append(PageBreak())

    # ================================================================
    # TABLE OF CONTENTS (static — known section order)
    # ================================================================
    story.append(Paragraph("Table of Contents", st["toc_title"]))
    story.append(HRFlowable(width="100%", thickness=1, color=NAVY, spaceAfter=8))

    toc_items = [(i + 1, sec["title"]) for i, sec in enumerate(SECTIONS)]
    for num, title in toc_items:
        story.append(Paragraph(f"{num}.   {title}", st["toc_entry"]))

    story.append(PageBreak())

    # ================================================================
    # BODY SECTIONS
    # ================================================================
    for sec_idx, section in enumerate(SECTIONS, start=1):
        sec_title = f"{sec_idx}.  {section['title']}"
        body_text = section["body"]

        # Section heading + rule (keep together with at least one body para)
        heading_block: list = [
            Paragraph(sec_title, st["section_h"]),
            HRFlowable(width="100%", thickness=0.8, color=STEEL, spaceAfter=6),
        ]

        # Body paragraphs
        for para_text in body_text.split("\n\n"):
            para_text = para_text.strip()
            if para_text:
                heading_block.append(Paragraph(para_text, st["body"]))

        story.append(KeepTogether(heading_block[:3]))  # keep heading + first para together
        for item in heading_block[3:]:
            story.append(item)

        # Section 3: insert the data table
        if sec_idx == 3:
            col_w = [
                CONTENT_W * 0.17,
                CONTENT_W * 0.12,
                CONTENT_W * 0.09,
                CONTENT_W * 0.09,
                CONTENT_W * 0.09,
                CONTENT_W * 0.09,
                CONTENT_W * 0.10,
            ]
            tbl_data = [TABLE_HEADERS] + TABLE_ROWS
            warn_rows = [i + 1 for i, r in enumerate(TABLE_ROWS) if r[-1] == "Warning"]

            ts_cmds = [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUND", (0, 1), (-1, -1), [WHITE, LIGHT]),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("GRID", (0, 0), (-1, -1), 0.35, GRID),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
            for wr in warn_rows:
                ts_cmds.append(("TEXTCOLOR", (6, wr), (6, wr), colors.HexColor("#c0392b")))
                ts_cmds.append(("FONTNAME", (6, wr), (6, wr), "Helvetica-Bold"))

            tbl = Table(tbl_data, colWidths=col_w, repeatRows=1)
            tbl.setStyle(TableStyle(ts_cmds))
            story.append(tbl)
            story.append(
                Paragraph(
                    "Table 1 — Mean resource utilisation per host (Q1 2024 audit period).",
                    st["caption"],
                )
            )

        # Section 4: insert the bar chart
        if sec_idx == 4:
            chart_drawing = _build_bar_chart(CHART_HOSTS, CHART_CPU, chart_w=int(CONTENT_W))
            story.append(chart_drawing)
            story.append(
                Paragraph(
                    "Figure 1 — Mean CPU utilisation by host (%). Red dashed line = 80 % warning threshold.",
                    st["caption"],
                )
            )

        story.append(Spacer(1, 6))

    doc.build(story)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="engineering_report.py",
        description=(
            "Generate a polished multi-section engineering/audit report PDF with "
            "cover page, TOC, data table, and bar chart."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--output", required=True, metavar="PDF", help="Output PDF path")
    p.add_argument(
        "--title",
        default="Infrastructure Audit Report",
        help="Report title (default: 'Infrastructure Audit Report')",
    )
    p.add_argument(
        "--project",
        default="Acme Corp — Q1 2024",
        help="Project / organisation name shown on cover and header",
    )
    p.add_argument("--author", default="Platform Engineering Team", help="Author name for cover page")
    p.add_argument("--date", default="2024-03-31", metavar="YYYY-MM-DD", help="Report date")
    p.add_argument("--force", action="store_true", help="Overwrite output if it already exists")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output_path = Path(args.output)

    if output_path.exists() and not args.force:
        print(
            f"ERROR: output already exists: {output_path}\n       Pass --force to overwrite.",
            file=sys.stderr,
        )
        return 1

    build_engineering_report(
        output_path=output_path,
        report_title=args.title,
        project=args.project,
        author=args.author,
        date_str=args.date,
    )

    print(f"Engineering report written: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
