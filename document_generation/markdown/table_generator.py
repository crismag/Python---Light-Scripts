"""markdown/table_generator.py — BEGINNER: convert a JSON array or CSV to a Markdown table.

Reads a JSON file (containing a list of objects) or a CSV file and writes a
GitHub-Flavored Markdown table to the output file.

Example commands:
    python document_generation/markdown/table_generator.py \\
        document_generation/examples/sample_inventory.csv \\
        /tmp/inventory_table.md

    python document_generation/markdown/table_generator.py \\
        document_generation/examples/sample_project.json \\
        /tmp/team_table.md \\
        --key team

    python document_generation/markdown/table_generator.py \\
        document_generation/examples/sample_inventory.csv \\
        /tmp/inventory_table.md \\
        --columns hostname,role,status \\
        --title "Server Inventory"
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Self-contained helpers (not imported from helpers.py)
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, list):
        raise TypeError(f"Top-level JSON value must be an array, got {type(data).__name__}.")
    return data  # type: ignore[return-value]


def _load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _build_md_table(rows: list[dict], columns: list[str]) -> str:
    """Render a list of dicts as a GitHub-Flavored Markdown table."""
    if not rows:
        return "_No data._"

    # Compute column widths
    widths = {c: len(c) for c in columns}
    for row in rows:
        for c in columns:
            widths[c] = max(widths[c], len(str(row.get(c, ""))))

    def fmt_row(cells: list[str]) -> str:
        return "| " + " | ".join(cells) + " |"

    header = fmt_row([c.ljust(widths[c]) for c in columns])
    sep    = fmt_row(["-" * widths[c]    for c in columns])
    lines  = [header, sep]
    for row in rows:
        lines.append(fmt_row([str(row.get(c, "")).ljust(widths[c]) for c in columns]))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------


def load_records(input_path: Path, key: str | None) -> list[dict]:
    """Load records from a JSON or CSV file.

    For JSON, if *key* is given the value at that key (must be a list) is used;
    otherwise the top-level value must already be an array.
    """
    ext = input_path.suffix.lower()
    if ext == ".json":
        with input_path.open(encoding="utf-8") as fh:
            data = json.load(fh)
        if key:
            # Drill into a dict to find the named list
            if not isinstance(data, dict):
                raise TypeError("Cannot use --key on a JSON array; remove --key or use a JSON object.")
            value = data.get(key)
            if value is None:
                raise KeyError(f"Key '{key}' not found in JSON object. Available keys: {list(data.keys())}")
            if not isinstance(value, list):
                raise TypeError(f"Value at key '{key}' must be a list, got {type(value).__name__}.")
            return value  # type: ignore[return-value]
        # No key: expect top-level array
        if not isinstance(data, list):
            raise TypeError(
                f"Top-level JSON value must be an array, got {type(data).__name__}. "
                f"Use --key to select a list inside a JSON object."
            )
        return data  # type: ignore[return-value]
    elif ext == ".csv":
        return _load_csv(input_path)
    else:
        raise ValueError(f"Unsupported file type '{ext}'. Use .json or .csv.")


def generate_table(
    input_path: Path,
    output_path: Path,
    key: str | None = None,
    columns: list[str] | None = None,
    title: str | None = None,
    force: bool = False,
) -> None:
    """Read records and write a markdown table to *output_path*."""
    # Safety: don't overwrite unless --force
    if output_path.exists() and not force:
        print(f"[error] Output file already exists: {output_path}")
        print("        Use --force to overwrite.")
        sys.exit(1)

    records = load_records(input_path, key)
    if not records:
        print("[warn] No records found in input — writing empty table placeholder.")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text("_No records found._\n", encoding="utf-8")
        return

    # Determine columns
    cols = columns if columns else list(records[0].keys())

    # Build markdown
    parts: list[str] = []
    if title:
        parts.append(f"# {title}\n")
    parts.append(_build_md_table(records, cols))
    parts.append("")  # trailing newline

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(parts), encoding="utf-8")

    print(f"[ok] Wrote {len(records)} rows × {len(cols)} columns → {output_path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a JSON array or CSV file to a GitHub-Flavored Markdown table.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("input",  type=Path, help="Input file (.json or .csv).")
    parser.add_argument("output", type=Path, help="Output .md file to write.")
    parser.add_argument(
        "--key",
        metavar="KEY",
        help="For JSON objects: top-level key whose value is the list of records (e.g. 'team').",
    )
    parser.add_argument(
        "--columns",
        metavar="COL1,COL2,...",
        help="Comma-separated list of columns to include (default: all).",
    )
    parser.add_argument("--title", metavar="TEXT", help="Optional H1 heading above the table.")
    parser.add_argument(
        "--force", action="store_true", help="Overwrite the output file if it already exists."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    cols = [c.strip() for c in args.columns.split(",")] if args.columns else None
    generate_table(
        input_path=args.input,
        output_path=args.output,
        key=args.key,
        columns=cols,
        title=args.title,
        force=args.force,
    )


if __name__ == "__main__":
    main()
