"""html/html_report.py — SHOWCASE: produce a polished dashboard-style HTML report.

Reads a JSON or YAML dataset (expects the same schema as sample_project.json or
sample_report.yaml) and generates a self-contained HTML file with:
  - Embedded CSS (no external stylesheet dependency)
  - A table of contents
  - Summary "stat cards"
  - Data tables
  - An inline-SVG horizontal bar chart (no JavaScript, no chart library)

Example commands:
    python document_generation/html/html_report.py \\
        document_generation/examples/sample_project.json \\
        /tmp/project_report.html

    python document_generation/html/html_report.py \\
        document_generation/examples/sample_report.yaml \\
        /tmp/report.html \\
        --force
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Embedded CSS (no external file needed — the HTML is self-contained)
# ---------------------------------------------------------------------------

_EMBEDDED_CSS = """
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 15px; line-height: 1.65; color: #1e2229; background: #f4f5f7;
}
.page-wrapper {
  max-width: 960px; margin: 2rem auto; background: #fff;
  border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,.10); overflow: hidden;
}
.report-header {
  background: linear-gradient(135deg,#1a3a5c 0%,#2563a8 100%);
  color:#fff; padding: 2.5rem 2.5rem 2rem;
}
.report-header h1 { font-size:1.85rem; font-weight:700; margin-bottom:.35rem; }
.report-header .subtitle { font-size:1rem; opacity:.85; margin-bottom:1.25rem; }
.meta-table { border-collapse:collapse; font-size:.875rem; }
.meta-table th,.meta-table td { padding:.2rem 1rem .2rem 0; color:rgba(255,255,255,.9); text-align:left; }
.meta-table th { font-weight:600; color:rgba(255,255,255,.65); min-width:130px; }
.toc { background:#f0f4f9; border-left:4px solid #2563a8; padding:1.5rem 2.5rem; }
.toc h2 {
  font-size:.85rem; text-transform:uppercase; letter-spacing:.08em; color:#5a6a82; margin-bottom:.75rem;
}
.toc ol { padding-left:1.25rem; }
.toc li { margin-bottom:.3rem; }
.toc a { color:#2563a8; text-decoration:none; font-size:.95rem; }
.toc a:hover { text-decoration:underline; }
main { padding: 0 2.5rem 1.5rem; }
.report-section { padding:2rem 0; border-bottom:1px solid #e4e8ef; }
.report-section:last-child { border-bottom:none; }
.report-section h2 { font-size:1.25rem; font-weight:700; color:#1a3a5c; margin-bottom:.85rem; }
.report-section h3 { font-size:.95rem; font-weight:600; color:#3a5a80; text-transform:uppercase;
  letter-spacing:.06em; margin:1.25rem 0 .65rem; }
.report-section p { color:#3d4552; max-width:72ch; margin-bottom:.75rem; }
.cards-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:1rem; margin:1.25rem 0; }
.card { background:#f0f4f9; border-radius:6px; padding:1rem 1.25rem; text-align:center; }
.card-value { font-size:1.75rem; font-weight:700; color:#2563a8; display:block; }
.card-label { font-size:.78rem; color:#6b7a90; text-transform:uppercase; letter-spacing:.05em; }
.data-table { width:100%; border-collapse:collapse; font-size:.9rem; margin-top:.5rem; }
.data-table thead th { background:#1a3a5c; color:#fff; font-weight:600; text-align:left;
  padding:.55rem .85rem; font-size:.82rem; letter-spacing:.03em; }
.data-table tbody tr:nth-child(even) { background:#f4f7fb; }
.data-table tbody td { padding:.5rem .85rem; border-bottom:1px solid #e4e8ef; color:#2d3540; }
.chart-wrap { margin:1.25rem 0; overflow-x:auto; }
.report-footer { background:#f0f4f9; text-align:center; padding:1rem;
  font-size:.8rem; color:#8a99b0; border-top:1px solid #e4e8ef; }
.report-footer code { background:#e0e7f0; padding:.1rem .4rem; border-radius:3px; font-size:.78rem; }
.badge { display:inline-block; padding:.15rem .6rem; border-radius:12px;
  font-size:.78rem; font-weight:600; text-transform:uppercase; }
.badge-online         { background:#d4edda; color:#155724; }
.badge-maintenance    { background:#fff3cd; color:#856404; }
.badge-decommissioning{ background:#f8d7da; color:#721c24; }
.badge-offline        { background:#e2e3e5; color:#383d41; }
"""


# ---------------------------------------------------------------------------
# Self-contained helpers
# ---------------------------------------------------------------------------


def _esc(text: Any) -> str:
    """HTML-escape a value."""
    s = str(text)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _slugify(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    return re.sub(r"-{2,}", "-", s).strip("-")


def _load_data(path: Path) -> Any:
    ext = path.suffix.lower()
    with path.open(encoding="utf-8") as fh:
        if ext == ".json":
            return json.load(fh)
        elif ext in {".yaml", ".yml"}:
            return yaml.safe_load(fh)
        elif ext == ".csv":
            return list(csv.DictReader(fh))
        else:
            raise ValueError(f"Unsupported file type: {ext}")


# ---------------------------------------------------------------------------
# HTML component builders
# ---------------------------------------------------------------------------


def _html_table(rows: list[dict], columns: list[str]) -> str:
    if not rows:
        return "<p><em>No data.</em></p>"
    thead = "".join(f"<th>{_esc(c)}</th>" for c in columns)
    tbody_rows = []
    for row in rows:
        cells = "".join(f"<td>{_esc(row.get(c,''))}</td>" for c in columns)
        tbody_rows.append(f"<tr>{cells}</tr>")
    return (
        '<table class="data-table">'
        f"<thead><tr>{thead}</tr></thead>"
        f"<tbody>{''.join(tbody_rows)}</tbody>"
        "</table>"
    )


def _stat_cards(metrics: dict[str, Any]) -> str:
    cards = []
    for label, value in metrics.items():
        display_label = label.replace("_", " ").title()
        cards.append(
            f'<div class="card">'
            f'<span class="card-value">{_esc(value)}</span>'
            f'<span class="card-label">{_esc(display_label)}</span>'
            f"</div>"
        )
    return f'<div class="cards-grid">{"".join(cards)}</div>'


def _svg_bar_chart(
    items: list[tuple[str, float]],
    title: str = "Chart",
    bar_color: str = "#2563a8",
    width: int = 700,
    bar_height: int = 28,
    gap: int = 6,
) -> str:
    """Build an inline SVG horizontal bar chart.

    Args:
        items:      List of (label, numeric_value) tuples.
        title:      Chart title (shown as SVG <title>).
        bar_color:  Fill colour for bars.
        width:      Total SVG width in pixels.
        bar_height: Height of each bar in pixels.
        gap:        Vertical gap between bars.

    Returns:
        An <svg> string (no external dependencies).
    """
    if not items:
        return "<p><em>No data for chart.</em></p>"

    max_val = max(v for _, v in items) or 1.0
    label_area = 200      # pixels reserved for labels on the left
    chart_area = width - label_area - 60  # right margin for value labels

    row_h = bar_height + gap
    svg_height = len(items) * row_h + 40  # 40px top padding for title space

    rows_svg: list[str] = []
    for idx, (label, value) in enumerate(items):
        y       = 30 + idx * row_h
        bar_w   = int(chart_area * (value / max_val))
        bar_x   = label_area

        # Label (left-aligned, right-padded to label_area)
        rows_svg.append(
            f'<text x="{label_area - 8}" y="{y + bar_height // 2 + 5}" '
            f'text-anchor="end" font-size="12" fill="#3d4552">{_esc(label)}</text>'
        )
        # Bar
        rows_svg.append(
            f'<rect x="{bar_x}" y="{y}" width="{bar_w}" height="{bar_height}" '
            f'rx="3" fill="{bar_color}" />'
        )
        # Value label at end of bar
        val_label = f"{value:,.0f}" if value == int(value) else f"{value:,.2f}"
        rows_svg.append(
            f'<text x="{bar_x + bar_w + 6}" y="{y + bar_height // 2 + 5}" '
            f'font-size="12" fill="#5a6a82">{_esc(val_label)}</text>'
        )

    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{svg_height}" '
        f'role="img" aria-label="{_esc(title)}">'
        f"<title>{_esc(title)}</title>"
        f'<text x="{label_area}" y="18" font-size="13" font-weight="600" fill="#1a3a5c">{_esc(title)}</text>'
        f"{''.join(rows_svg)}"
        f"</svg>"
    )


# ---------------------------------------------------------------------------
# Report builders per data schema
# ---------------------------------------------------------------------------


def _render_project_report(data: dict) -> tuple[str, list[tuple[str, str]]]:
    """Render HTML sections for the project JSON schema.

    Returns:
        (html_string, [(section_id, section_title), ...])
    """
    proj     = data.get("project", {})
    team     = data.get("team", [])
    comps    = data.get("components", [])
    metrics  = data.get("metrics", {})
    deps     = data.get("dependencies", [])
    notes    = data.get("notes", [])

    sections: list[tuple[str, str, str]] = []   # (id, title, html)

    # --- Project Details ---
    kv_rows = [{"Field": k.replace("_", " ").title(), "Value": str(v)} for k, v in proj.items()]
    sections.append(("project-details", "Project Details", _html_table(kv_rows, ["Field", "Value"])))

    # --- Metrics cards + bar chart ---
    if metrics:
        chart_items = [(k.replace("_", " ").title(), float(v)) for k, v in metrics.items()]
        metrics_html = (
            _stat_cards(metrics)
            + '<div class="chart-wrap">'
            + _svg_bar_chart(chart_items, title="Project Metrics")
            + "</div>"
        )
        sections.append(("metrics", "Key Metrics", metrics_html))

    # --- Team ---
    if team:
        sections.append(("team", "Team", _html_table(team, list(team[0].keys()))))

    # --- Components ---
    if comps:
        sections.append(("components", "Components", _html_table(comps, list(comps[0].keys()))))

    # --- Dependencies ---
    if deps:
        sections.append(("dependencies", "Dependencies", _html_table(deps, list(deps[0].keys()))))

    # --- Notes ---
    if notes:
        notes_html = "<ul>" + "".join(f"<li>{_esc(n)}</li>" for n in notes) + "</ul>"
        sections.append(("notes", "Notes", notes_html))

    html_parts = []
    toc_refs   = []
    for sec_id, sec_title, sec_html in sections:
        toc_refs.append((sec_id, sec_title))
        html_parts.append(
            f'<section id="{sec_id}" class="report-section">'
            f"<h2>{_esc(sec_title)}</h2>"
            f"{sec_html}"
            f"</section>"
        )

    return "\n".join(html_parts), toc_refs


def _render_yaml_report(data: dict) -> tuple[str, list[tuple[str, str]]]:
    """Render HTML sections for the YAML report schema."""
    report_sections = data.get("sections", [])
    html_parts = []
    toc_refs   = []

    for idx, section in enumerate(report_sections):
        title   = section.get("title", f"Section {idx+1}")
        content = section.get("content", "").strip()
        sec_id  = f"section-{idx+1}"
        toc_refs.append((sec_id, title))

        inner: list[str] = []
        inner.append(f"<p>{_esc(content).replace(chr(10), '<br>')}</p>")

        metrics = section.get("metrics", [])
        if metrics:
            inner.append("<h3>Key Metrics</h3>")
            inner.append(_html_table(metrics, list(metrics[0].keys())))

        ais = section.get("action_items", [])
        if ais:
            inner.append("<h3>Action Items</h3>")
            inner.append(_html_table(ais, list(ais[0].keys())))

        html_parts.append(
            f'<section id="{sec_id}" class="report-section">'
            f"<h2>{_esc(title)}</h2>"
            f"{''.join(inner)}"
            f"</section>"
        )

    return "\n".join(html_parts), toc_refs


def _render_csv_report(rows: list[dict[str, str]]) -> tuple[str, list[tuple[str, str]]]:
    """Render an inventory table with a bar chart from CSV rows."""
    if not rows:
        return "<p><em>No inventory data.</em></p>", []

    columns = list(rows[0].keys())

    # RAM bar chart (if ram_gb column exists)
    chart_html = ""
    if "ram_gb" in columns and "hostname" in columns:
        chart_items = [
            (r["hostname"], float(r["ram_gb"]))
            for r in rows
            if r.get("ram_gb", "").isdigit()
        ]
        if chart_items:
            chart_html = (
                '<div class="chart-wrap">'
                + _svg_bar_chart(chart_items[:15], title="RAM by Host (GB)", bar_color="#2563a8")
                + "</div>"
            )

    inventory_html = chart_html + _html_table(rows, columns)
    return (
        f'<section id="inventory" class="report-section"><h2>System Inventory</h2>'
        f"{inventory_html}</section>",
        [("inventory", "System Inventory")],
    )


# ---------------------------------------------------------------------------
# Page assembler
# ---------------------------------------------------------------------------


def build_html_report(data: Any, source_path: Path) -> str:
    """Build a complete HTML report string from the loaded data."""
    # Detect schema and render appropriate sections
    if isinstance(data, list):
        # CSV-style
        body_html, toc_refs = _render_csv_report(data)
        title    = "System Inventory Report"
        subtitle = f"Source: {source_path.name}"
        date_str = ""
        authors  = []
    elif isinstance(data, dict) and "project" in data:
        body_html, toc_refs = _render_project_report(data)
        proj     = data.get("project", {})
        title    = proj.get("name", source_path.stem)
        subtitle = proj.get("description", "")
        date_str = proj.get("updated", "")
        authors  = []
    elif isinstance(data, dict) and "report" in data:
        body_html, toc_refs = _render_yaml_report(data)
        report   = data.get("report", {})
        title    = report.get("title", source_path.stem)
        subtitle = report.get("subtitle", "")
        date_str = report.get("date", "")
        authors  = report.get("authors", [])
    else:
        # Generic dict — treat as project-style
        body_html, toc_refs = _render_project_report(data if isinstance(data, dict) else {})
        title    = source_path.stem
        subtitle = ""
        date_str = ""
        authors  = []

    # Build TOC
    toc_items = "".join(
        f'<li><a href="#{sec_id}">{_esc(sec_title)}</a></li>' for sec_id, sec_title in toc_refs
    )
    toc_html = f'<nav class="toc"><h2>Table of Contents</h2><ol>{toc_items}</ol></nav>'

    # Build meta table rows
    meta_rows = []
    if date_str:
        meta_rows.append(f"<tr><th>Date</th><td>{_esc(date_str)}</td></tr>")
    if authors:
        names = ", ".join(a.get("name", str(a)) if isinstance(a, dict) else str(a) for a in authors)
        meta_rows.append(f"<tr><th>Authors</th><td>{_esc(names)}</td></tr>")
    meta_rows.append(f"<tr><th>Source</th><td><code>{_esc(source_path.name)}</code></td></tr>")
    meta_html = f'<table class="meta-table">{"".join(meta_rows)}</table>' if meta_rows else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{_esc(title)}</title>
  <style>{_EMBEDDED_CSS}</style>
</head>
<body>
<div class="page-wrapper">
  <header class="report-header">
    <h1>{_esc(title)}</h1>
    {f'<p class="subtitle">{_esc(subtitle)}</p>' if subtitle else ""}
    {meta_html}
  </header>
  {toc_html}
  <main>
    {body_html}
  </main>
  <footer class="report-footer">
    <p>Generated by <code>html_report.py</code> &mdash; Python Light Scripts</p>
  </footer>
</div>
</body>
</html>
"""


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a polished dashboard-style HTML report from a JSON or YAML file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input",  type=Path, help="Input data file (.json, .yaml, or .csv).")
    parser.add_argument("output", type=Path, help="Output .html file to write.")
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

    data = _load_data(args.input)
    html = build_html_report(data, args.input)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")

    size_kb = args.output.stat().st_size / 1024
    print(f"[ok] HTML report written → {args.output} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
