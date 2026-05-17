"""docx/docx_report.py — INTERMEDIATE: generate a formatted .docx report from a JSON dataset.

Reads a JSON file (project summary schema) and produces a Microsoft Word document
with a styled title, section headings, key/value paragraphs, and a formatted table.
Uses python-docx (no Office installation required).

Example commands:
    python document_generation/docx/docx_report.py \\
        document_generation/examples/sample_project.json \\
        /tmp/project_report.docx

    python document_generation/docx/docx_report.py \\
        document_generation/examples/sample_project.json \\
        /tmp/project_report.docx \\
        --force
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH  # noqa: F401  (used via paragraph.alignment)
from docx.oxml.ns import qn
from docx.shared import Pt, RGBColor

# ---------------------------------------------------------------------------
# Styling helpers (self-contained)
# ---------------------------------------------------------------------------

# Brand colour used for headings — deep navy blue
_HEADING_COLOR = RGBColor(0x1A, 0x3A, 0x5C)
_ACCENT_COLOR  = RGBColor(0x25, 0x63, 0xA8)


def _set_cell_bg(cell: Any, hex_color: str = "1A3A5C") -> None:
    """Set a table cell background colour via direct XML manipulation."""
    from docx.oxml import OxmlElement

    tc   = cell._tc
    tcPr = tc.get_or_add_tcPr()
    shd  = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:val"),  "clear")
    tcPr.append(shd)


def _heading(doc: Document, text: str, level: int = 1) -> None:
    """Add a styled heading paragraph."""
    p = doc.add_heading(text, level=level)
    run = p.runs[0] if p.runs else p.add_run(text)
    run.font.color.rgb = _HEADING_COLOR
    run.font.bold      = True


def _kv_paragraph(doc: Document, key: str, value: str) -> None:
    """Add a bold-key: value paragraph."""
    para = doc.add_paragraph()
    run_k = para.add_run(f"{key}: ")
    run_k.bold = True
    run_k.font.color.rgb = _ACCENT_COLOR
    para.add_run(str(value))


# ---------------------------------------------------------------------------
# Core document builder
# ---------------------------------------------------------------------------


def build_docx(data: dict, output_path: Path) -> None:
    """Build and save a .docx report from a project JSON dict.

    Args:
        data:        Parsed project JSON (top-level keys: project, team, components, metrics, ...).
        output_path: Destination .docx file path.
    """
    doc = Document()

    # ---- Title ----
    proj = data.get("project", {})
    title_para = doc.add_heading(proj.get("name", "Project Report"), level=0)
    title_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if title_para.runs:
        title_para.runs[0].font.color.rgb = _HEADING_COLOR

    version_para = doc.add_paragraph(
        f"Version {proj.get('version', 'N/A')}  •  Status: {proj.get('status', 'N/A')}"
    )
    version_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    version_para.runs[0].font.color.rgb = RGBColor(0x5A, 0x6A, 0x82)

    doc.add_paragraph()  # spacer

    # ---- Project Overview ----
    _heading(doc, "Project Overview", level=1)
    overview_fields = [
        "description", "repository", "owner", "language", "python_version", "created", "updated",
    ]
    for field in overview_fields:
        if field in proj:
            _kv_paragraph(doc, field.replace("_", " ").title(), str(proj[field]))

    doc.add_paragraph()

    # ---- Key Metrics ----
    metrics = data.get("metrics", {})
    if metrics:
        _heading(doc, "Key Metrics", level=1)
        for k, v in metrics.items():
            _kv_paragraph(doc, k.replace("_", " ").title(), str(v))
        doc.add_paragraph()

    # ---- Team Table ----
    team = data.get("team", [])
    if team:
        _heading(doc, "Team", level=1)
        columns = list(team[0].keys())
        table   = doc.add_table(rows=1 + len(team), cols=len(columns))
        table.style = "Table Grid"

        # Header row
        hdr_cells = table.rows[0].cells
        for i, col in enumerate(columns):
            hdr_cells[i].text = col.title()
            _set_cell_bg(hdr_cells[i], "1A3A5C")
            run = hdr_cells[i].paragraphs[0].runs[0]
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            run.font.bold      = True
            run.font.size      = Pt(10)

        # Data rows
        for row_idx, member in enumerate(team):
            row_cells = table.rows[row_idx + 1].cells
            for col_idx, col in enumerate(columns):
                row_cells[col_idx].text = str(member.get(col, ""))
                row_cells[col_idx].paragraphs[0].runs[0].font.size = Pt(10)

        doc.add_paragraph()

    # ---- Components Table ----
    components = data.get("components", [])
    if components:
        _heading(doc, "Components", level=1)
        columns = list(components[0].keys())
        table   = doc.add_table(rows=1 + len(components), cols=len(columns))
        table.style = "Table Grid"

        hdr_cells = table.rows[0].cells
        for i, col in enumerate(columns):
            hdr_cells[i].text = col.title()
            _set_cell_bg(hdr_cells[i], "2563A8")
            run = hdr_cells[i].paragraphs[0].runs[0]
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            run.font.bold      = True
            run.font.size      = Pt(10)

        for row_idx, comp in enumerate(components):
            row_cells = table.rows[row_idx + 1].cells
            for col_idx, col in enumerate(columns):
                row_cells[col_idx].text = str(comp.get(col, ""))
                row_cells[col_idx].paragraphs[0].runs[0].font.size = Pt(10)

        doc.add_paragraph()

    # ---- Dependencies Table ----
    deps = data.get("dependencies", [])
    if deps:
        _heading(doc, "Dependencies", level=1)
        columns = list(deps[0].keys())
        table   = doc.add_table(rows=1 + len(deps), cols=len(columns))
        table.style = "Table Grid"

        hdr_cells = table.rows[0].cells
        for i, col in enumerate(columns):
            hdr_cells[i].text = col.title()
            _set_cell_bg(hdr_cells[i], "1A3A5C")
            run = hdr_cells[i].paragraphs[0].runs[0]
            run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            run.font.bold      = True
            run.font.size      = Pt(10)

        for row_idx, dep in enumerate(deps):
            row_cells = table.rows[row_idx + 1].cells
            for col_idx, col in enumerate(columns):
                row_cells[col_idx].text = str(dep.get(col, ""))
                row_cells[col_idx].paragraphs[0].runs[0].font.size = Pt(10)

        doc.add_paragraph()

    # ---- Notes ----
    notes = data.get("notes", [])
    if notes:
        _heading(doc, "Notes", level=1)
        for note in notes:
            doc.add_paragraph(note, style="List Bullet")

    # ---- Footer note ----
    doc.add_paragraph()
    footer_para = doc.add_paragraph("Generated by docx_report.py — Python Light Scripts")
    footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer_para.runs[0].font.color.rgb = RGBColor(0x8A, 0x99, 0xB0)
    footer_para.runs[0].font.size      = Pt(9)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(output_path))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a formatted .docx report from a JSON project dataset.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input",  type=Path, help="Input .json project file.")
    parser.add_argument("output", type=Path, help="Output .docx file to write.")
    parser.add_argument(
        "--force", action="store_true", help="Overwrite the output file if it already exists."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    if args.output.exists() and not args.force:
        print(f"[error] Output file already exists: {args.output}")
        print("        Use --force to overwrite.")
        sys.exit(1)

    if not args.input.exists():
        print(f"[error] Input file not found: {args.input}")
        sys.exit(1)

    with args.input.open(encoding="utf-8") as fh:
        data = json.load(fh)

    build_docx(data, args.output)

    size_kb = args.output.stat().st_size / 1024
    print(f"[ok] DOCX report written → {args.output} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
