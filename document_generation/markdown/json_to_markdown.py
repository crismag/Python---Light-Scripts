"""markdown/json_to_markdown.py — BEGINNER: convert a JSON object to structured Markdown.

Turns any JSON object (or array) into a readable Markdown document with headings,
bullet lists, and nested keys rendered at appropriate heading levels.

Example commands:
    python document_generation/markdown/json_to_markdown.py \\
        document_generation/examples/sample_project.json \\
        /tmp/project_doc.md

    python document_generation/markdown/json_to_markdown.py \\
        document_generation/examples/sample_project.json \\
        /tmp/project_doc.md \\
        --title "Orion Pipeline — Project Summary" \\
        --force
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Markdown rendering helpers (self-contained — no imports from helpers.py)
# ---------------------------------------------------------------------------


def _scalar_to_str(value: Any) -> str:
    """Format a scalar value as a readable string."""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    return str(value)


def _render_list_of_dicts(items: list[dict], indent: int = 0) -> list[str]:
    """Render a list of dicts as a Markdown definition/bullet block."""
    lines: list[str] = []
    pad = "  " * indent
    for item in items:
        # First key becomes the bullet label if possible
        keys = list(item.keys())
        if keys:
            first_val = _scalar_to_str(item[keys[0]])
            lines.append(f"{pad}- **{first_val}**")
            for k in keys[1:]:
                v = item[k]
                if isinstance(v, (dict, list)):
                    lines.append(f"{pad}  - *{k}*:")
                    lines.extend(_render_value(v, indent + 2))
                else:
                    lines.append(f"{pad}  - *{k}*: {_scalar_to_str(v)}")
    return lines


def _render_value(value: Any, indent: int = 0) -> list[str]:
    """Recursively render a JSON value as markdown lines."""
    pad = "  " * indent
    lines: list[str] = []

    if isinstance(value, dict):
        for k, v in value.items():
            if isinstance(v, dict):
                lines.append(f"{pad}- **{k}**:")
                lines.extend(_render_value(v, indent + 1))
            elif isinstance(v, list):
                lines.append(f"{pad}- **{k}**:")
                lines.extend(_render_value(v, indent + 1))
            else:
                lines.append(f"{pad}- **{k}**: {_scalar_to_str(v)}")

    elif isinstance(value, list):
        if not value:
            lines.append(f"{pad}_empty_")
        elif all(isinstance(item, dict) for item in value):
            lines.extend(_render_list_of_dicts(value, indent))
        else:
            for item in value:
                if isinstance(item, (dict, list)):
                    lines.extend(_render_value(item, indent + 1))
                else:
                    lines.append(f"{pad}- {_scalar_to_str(item)}")
    else:
        lines.append(f"{pad}{_scalar_to_str(value)}")

    return lines


def json_to_markdown(data: Any, title: str | None = None, source_path: str | None = None) -> str:
    """Convert a parsed JSON object/array to a Markdown document string.

    Args:
        data:        Parsed JSON (dict or list).
        title:       Optional H1 heading for the document.
        source_path: Optional source file name shown in a footer.

    Returns:
        A multiline Markdown string.
    """
    sections: list[str] = []

    if title:
        sections.append(f"# {title}\n")
    elif source_path:
        sections.append(f"# {Path(source_path).stem}\n")

    if isinstance(data, dict):
        for key, value in data.items():
            # Top-level keys become ## headings
            sections.append(f"## {key.replace('_', ' ').title()}\n")
            if isinstance(value, dict):
                sections.extend(_render_value(value))
            elif isinstance(value, list):
                if all(isinstance(item, dict) for item in value):
                    sections.extend(_render_list_of_dicts(value))
                else:
                    for item in value:
                        sections.append(f"- {_scalar_to_str(item)}")
            else:
                sections.append(_scalar_to_str(value))
            sections.append("")  # blank line between sections

    elif isinstance(data, list):
        # Top-level array — render as a list
        sections.append("## Contents\n")
        if all(isinstance(item, dict) for item in data):
            sections.extend(_render_list_of_dicts(data))
        else:
            for item in data:
                sections.append(f"- {_scalar_to_str(item)}")
        sections.append("")
    else:
        sections.append(_scalar_to_str(data))

    if source_path:
        sections.append(f"\n---\n_Source: `{source_path}`_\n")

    return "\n".join(sections)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a JSON file to a structured Markdown document.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input",  type=Path, help="Input .json file.")
    parser.add_argument("output", type=Path, help="Output .md file to write.")
    parser.add_argument("--title", metavar="TEXT", help="Document title (H1 heading).")
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

    md = json_to_markdown(data, title=args.title, source_path=str(args.input))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(md, encoding="utf-8")

    line_count = md.count("\n") + 1
    print(f"[ok] Wrote {line_count} lines → {args.output}")


if __name__ == "__main__":
    main()
