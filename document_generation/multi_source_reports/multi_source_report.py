"""multi_source_reports/multi_source_report.py — ADVANCED: merge JSON + YAML + CSV into one report.

Reads three heterogeneous data sources and produces a single cohesive Markdown
engineering report with titled sections, a generated table of contents, and summary
statistics derived from each source.

Example command:
    python document_generation/multi_source_reports/multi_source_report.py \\
        --json  document_generation/examples/sample_project.json \\
        --yaml  document_generation/examples/sample_report.yaml \\
        --csv   document_generation/examples/sample_inventory.csv \\
        --output /tmp/engineering_report.md

    # Omit any source to skip that section:
    python document_generation/multi_source_reports/multi_source_report.py \\
        --json  document_generation/examples/sample_project.json \\
        --csv   document_generation/examples/sample_inventory.csv \\
        --output /tmp/partial_report.md \\
        --force
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

# ---------------------------------------------------------------------------
# Self-contained data loaders
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return json.load(fh)


def _load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------------------
# Self-contained markdown helpers
# ---------------------------------------------------------------------------


def _slugify(text: str) -> str:
    s = text.lower()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "-", s)
    s = re.sub(r"-{2,}", "-", s)
    return s.strip("-")


def _md_table(rows: list[dict[str, str]], columns: list[str]) -> str:
    if not rows:
        return "_No data._"
    widths = {c: max(len(c), max((len(str(r.get(c, ""))) for r in rows), default=0)) for c in columns}

    def fmt(cells: list[str]) -> str:
        return "| " + " | ".join(cells) + " |"

    return "\n".join(
        [
            fmt([c.ljust(widths[c]) for c in columns]),
            fmt(["-" * widths[c] for c in columns]),
            *[fmt([str(r.get(c, "")).ljust(widths[c]) for c in columns]) for r in rows],
        ]
    )


# ---------------------------------------------------------------------------
# Per-source section builders
# ---------------------------------------------------------------------------


def _section_from_json(data: dict) -> list[str]:
    """Build a 'Project Overview' section from the project JSON."""
    lines: list[str] = ["## Project Overview\n"]
    proj = data.get("project", {})

    # Key/value summary table
    kv_rows = [{"Field": k.replace("_", " ").title(), "Value": str(v)} for k, v in proj.items()]
    lines.append(_md_table(kv_rows, ["Field", "Value"]))
    lines.append("")

    # Team table
    team = data.get("team", [])
    if team:
        lines.append("### Team\n")
        lines.append(_md_table(team, list(team[0].keys())))
        lines.append("")

    # Components table
    components = data.get("components", [])
    if components:
        lines.append("### Components\n")
        lines.append(_md_table(components, list(components[0].keys())))
        lines.append("")

    # Metrics
    metrics = data.get("metrics", {})
    if metrics:
        lines.append("### Key Metrics\n")
        m_rows = [{"Metric": k.replace("_", " ").title(), "Value": str(v)} for k, v in metrics.items()]
        lines.append(_md_table(m_rows, ["Metric", "Value"]))
        lines.append("")

    # Notes
    notes = data.get("notes", [])
    if notes:
        lines.append("### Notes\n")
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")

    return lines


def _section_from_yaml(data: dict) -> list[str]:
    """Build a 'Engineering Report Sections' block from the YAML spec."""
    lines: list[str] = ["## Engineering Report Sections\n"]
    report_meta = data.get("report", {})

    # Report metadata header
    lines.append(f"**Report:** {report_meta.get('title', 'N/A')}  ")
    lines.append(f"**Date:** {report_meta.get('date', 'N/A')}  ")
    authors = report_meta.get("authors", [])
    if authors:
        names = ", ".join(a.get("name", "") for a in authors)
        lines.append(f"**Authors:** {names}  ")
    lines.append("")

    # Render each section as a sub-section
    for section in data.get("sections", []):
        title   = section.get("title", "Untitled")
        content = section.get("content", "").strip()
        lines.append(f"### {title}\n")
        lines.append(content)
        lines.append("")

        # Action items
        ais = section.get("action_items", [])
        if ais:
            lines.append(_md_table(ais, ["owner", "due", "task"]))
            lines.append("")

        # Metrics
        mets = section.get("metrics", [])
        if mets:
            lines.append(_md_table(mets, ["label", "value"]))
            lines.append("")

    return lines


def _section_from_csv(rows: list[dict[str, str]]) -> list[str]:
    """Build a 'System Inventory' section from the CSV."""
    lines: list[str] = ["## System Inventory\n"]

    if not rows:
        lines.append("_No inventory data._\n")
        return lines

    columns = list(rows[0].keys())

    # Summary statistics
    statuses = Counter(r.get("status", "unknown") for r in rows)
    roles    = Counter(r.get("role", "unknown") for r in rows)
    total_ram = sum(int(r.get("ram_gb", 0)) for r in rows if r.get("ram_gb", "").isdigit())

    lines.append("### Summary Statistics\n")
    stat_rows = [
        {"Metric": "Total Hosts",  "Value": str(len(rows))},
        {"Metric": "Total RAM (GB)", "Value": str(total_ram)},
        *[{"Metric": f"Status: {k}", "Value": str(v)} for k, v in sorted(statuses.items())],
        *[{"Metric": f"Role: {k}",   "Value": str(v)} for k, v in sorted(roles.items())],
    ]
    lines.append(_md_table(stat_rows, ["Metric", "Value"]))
    lines.append("")

    # Full inventory table
    lines.append("### Full Inventory\n")
    lines.append(_md_table(rows, columns))
    lines.append("")

    return lines


# ---------------------------------------------------------------------------
# TOC builder
# ---------------------------------------------------------------------------


def _build_toc(section_titles: list[str]) -> list[str]:
    toc = ["## Table of Contents\n"]
    for title in section_titles:
        anchor = _slugify(title)
        toc.append(f"- [{title}](#{anchor})")
    toc.append("")
    return toc


# ---------------------------------------------------------------------------
# Full report assembler
# ---------------------------------------------------------------------------


def build_report(
    json_data: dict | None,
    yaml_data: dict | None,
    csv_rows: list[dict[str, str]] | None,
    output_title: str = "Multi-Source Engineering Report",
) -> str:
    """Combine data from three sources into a single Markdown report."""
    doc_sections: list[tuple[str, list[str]]] = []

    if json_data is not None:
        doc_sections.append(("Project Overview", _section_from_json(json_data)))

    if yaml_data is not None:
        doc_sections.append(("Engineering Report Sections", _section_from_yaml(yaml_data)))

    if csv_rows is not None:
        doc_sections.append(("System Inventory", _section_from_csv(csv_rows)))

    # Header
    all_lines: list[str] = [
        f"# {output_title}\n",
        "_This report was assembled automatically from multiple heterogeneous data sources._\n",
    ]

    # TOC
    all_lines.extend(_build_toc([t for t, _ in doc_sections]))
    all_lines.append("---\n")

    # Sections
    for _, section_lines in doc_sections:
        all_lines.extend(section_lines)
        all_lines.append("---\n")

    all_lines.append("_Generated by multi_source_report.py_")
    return "\n".join(all_lines) + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge a JSON + YAML + CSV file into one Markdown engineering report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--json",   type=Path, metavar="FILE", help="JSON project data file.")
    parser.add_argument("--yaml",   type=Path, metavar="FILE", help="YAML report spec file.")
    parser.add_argument("--csv",    type=Path, metavar="FILE", help="CSV inventory file.")
    parser.add_argument("--output", type=Path, required=True,  help="Output .md file to write.")
    parser.add_argument("--title",  metavar="TEXT", help="Report title (default: auto).")
    parser.add_argument(
        "--force", action="store_true", help="Overwrite the output file if it already exists."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    if not any([args.json, args.yaml, args.csv]):
        print("[error] Provide at least one of --json, --yaml, --csv.")
        sys.exit(1)

    if args.output.exists() and not args.force:
        print(f"[error] Output file already exists: {args.output}")
        print("        Use --force to overwrite.")
        sys.exit(1)

    json_data: dict | None = None
    yaml_data: dict | None = None
    csv_rows:  list[dict[str, str]] | None = None

    if args.json:
        if not args.json.exists():
            print(f"[error] JSON file not found: {args.json}")
            sys.exit(1)
        json_data = _load_json(args.json)
        print(f"[load] JSON  : {args.json}")

    if args.yaml:
        if not args.yaml.exists():
            print(f"[error] YAML file not found: {args.yaml}")
            sys.exit(1)
        yaml_data = _load_yaml(args.yaml)
        print(f"[load] YAML  : {args.yaml}")

    if args.csv:
        if not args.csv.exists():
            print(f"[error] CSV file not found: {args.csv}")
            sys.exit(1)
        csv_rows = _load_csv(args.csv)
        print(f"[load] CSV   : {args.csv} ({len(csv_rows)} rows)")

    title = args.title or "Multi-Source Engineering Report"
    report = build_report(json_data, yaml_data, csv_rows, output_title=title)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report, encoding="utf-8")
    print(f"[ok] Report written → {args.output}")


if __name__ == "__main__":
    main()
