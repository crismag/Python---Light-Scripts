"""document_generation/helpers.py — Standalone reference module of reusable helpers.

This file is a STUDY / COPY REFERENCE — it is NOT imported by any other script in
this section.  Each example script is self-contained and copies whatever logic it needs.

Running this file directly demos every function with sample inputs:

    python document_generation/helpers.py
"""

from __future__ import annotations

import csv
import json
import re
import textwrap
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# 1. load_data_file — load .json / .yaml / .yml / .csv → Python objects
# ---------------------------------------------------------------------------


def load_data_file(path: str | Path) -> Any:
    """Load a data file by extension and return a Python object.

    Supported extensions: .json, .yaml, .yml, .csv

    Args:
        path: Path to the data file (str or Path).

    Returns:
        - JSON  → dict or list
        - YAML  → dict or list
        - CSV   → list[dict] (using csv.DictReader, all values are strings)

    Raises:
        ValueError: If the file extension is not supported.
        FileNotFoundError: If the file does not exist.
    """
    import yaml  # pyyaml — imported lazily so the module stays importable without it

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")

    ext = p.suffix.lower()
    if ext == ".json":
        with p.open(encoding="utf-8") as fh:
            return json.load(fh)
    elif ext in {".yaml", ".yml"}:
        with p.open(encoding="utf-8") as fh:
            return yaml.safe_load(fh)
    elif ext == ".csv":
        with p.open(newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))
    else:
        raise ValueError(f"Unsupported extension '{ext}'. Use .json, .yaml, .yml, or .csv.")


# ---------------------------------------------------------------------------
# 2. render_template — render a Jinja2 template string with a context dict
# ---------------------------------------------------------------------------


def render_template(template_str: str, context: dict[str, Any]) -> str:
    """Render a Jinja2 template string with the given context dictionary.

    Args:
        template_str: A Jinja2 template as a plain string.
        context: Dictionary of variables available inside the template.

    Returns:
        The rendered string with all {{ }} and {% %} expressions evaluated.

    Example:
        >>> render_template("Hello, {{ name }}!", {"name": "World"})
        'Hello, World!'
    """
    from jinja2 import Environment, StrictUndefined

    env = Environment(undefined=StrictUndefined, autoescape=False)  # noqa: S701 — rendering Markdown, not HTML
    return env.from_string(template_str).render(**context)


# ---------------------------------------------------------------------------
# 3. slugify — convert a heading string to a GitHub-Flavored Markdown anchor
# ---------------------------------------------------------------------------


def slugify(heading: str) -> str:
    """Convert a heading string to a GitHub-Flavored Markdown anchor slug.

    Rules applied:
      - Lowercase everything
      - Remove characters that are not alphanumeric, spaces, or hyphens
      - Replace spaces (and consecutive spaces) with a single hyphen

    Args:
        heading: Raw heading text, e.g. "Table of Contents".

    Returns:
        URL-safe slug, e.g. "table-of-contents".

    Example:
        >>> slugify("System & Network Overview")
        'system--network-overview'
    """
    s = heading.lower()
    s = re.sub(r"[^\w\s-]", "", s)   # strip punctuation except hyphens and underscores
    s = re.sub(r"[\s_]+", "-", s)    # spaces/underscores → hyphen
    s = re.sub(r"-{2,}", "-", s)     # collapse runs of hyphens
    return s.strip("-")


# ---------------------------------------------------------------------------
# 4. build_md_table — GitHub-Flavored Markdown table from list[dict]
# ---------------------------------------------------------------------------


def build_md_table(rows: list[dict[str, Any]], columns: list[str] | None = None) -> str:
    """Build a GitHub-Flavored Markdown table from a list of dicts.

    Args:
        rows:    List of dicts; all share the same keys (extra keys are ignored).
        columns: Ordered list of column keys to include.  If *None*, uses the
                 keys of the first row in their natural insertion order.

    Returns:
        A GFM-formatted markdown table as a string (no trailing newline).

    Raises:
        ValueError: If *rows* is empty.

    Example:
        >>> build_md_table([{"a": 1, "b": 2}, {"a": 3, "b": 4}])
        '| a | b |\\n|---|---|\\n| 1 | 2 |\\n| 3 | 4 |'
    """
    if not rows:
        raise ValueError("rows must not be empty")

    cols = columns if columns is not None else list(rows[0].keys())

    # Compute column widths (at least as wide as the header)
    widths = {c: len(str(c)) for c in cols}
    for row in rows:
        for c in cols:
            widths[c] = max(widths[c], len(str(row.get(c, ""))))

    def fmt_row(cells: list[str]) -> str:
        return "| " + " | ".join(cells) + " |"

    header = fmt_row([str(c).ljust(widths[c]) for c in cols])
    sep = fmt_row(["-" * widths[c] for c in cols])
    data_rows = [fmt_row([str(row.get(c, "")).ljust(widths[c]) for c in cols]) for row in rows]

    return "\n".join([header, sep, *data_rows])


# ---------------------------------------------------------------------------
# 5. build_md_toc — generate a Table of Contents from markdown headings
# ---------------------------------------------------------------------------


def build_md_toc(markdown_text: str) -> str:
    """Generate a GitHub-Flavored Markdown Table of Contents from heading lines.

    Scans for lines starting with '#' or '##' (level-1 and level-2) and builds
    an indented bullet list of anchor links.

    Args:
        markdown_text: Raw markdown text containing heading lines.

    Returns:
        A multiline string with the TOC, or an empty string if no headings found.

    Example:
        >>> build_md_toc("# Intro\\n## Background\\n## Goals")
        '- [Intro](#intro)\\n  - [Background](#background)\\n  - [Goals](#goals)'
    """
    toc_lines: list[str] = []
    for line in markdown_text.splitlines():
        # Match level-1 or level-2 headings only
        m = re.match(r"^(#{1,2})\s+(.+)", line)
        if not m:
            continue
        level = len(m.group(1))
        title = m.group(2).strip()
        anchor = slugify(title)
        indent = "  " * (level - 1)
        toc_lines.append(f"{indent}- [{title}](#{anchor})")

    return "\n".join(toc_lines)


# ---------------------------------------------------------------------------
# __main__ demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("=" * 60)
    print("helpers.py — function demos")
    print("=" * 60)

    # --- render_template ---
    print("\n[1] render_template")
    result = render_template("Project: {{ name }} (v{{ version }})", {"name": "Orion", "version": "2.4.1"})
    print(f"    {result}")

    # --- slugify ---
    print("\n[2] slugify")
    headings = ["Table of Contents", "System & Network Overview", "Q2 2026 Report"]
    for h in headings:
        print(f"    {h!r:40s} → {slugify(h)!r}")

    # --- build_md_table ---
    print("\n[3] build_md_table")
    sample_rows = [
        {"hostname": "prod-web-01", "role": "Web Server", "status": "online"},
        {"hostname": "prod-db-01",  "role": "Database",   "status": "online"},
        {"hostname": "prod-app-03", "role": "App Server", "status": "maintenance"},
    ]
    table = build_md_table(sample_rows)
    print(textwrap.indent(table, "    "))

    # --- build_md_toc ---
    print("\n[4] build_md_toc")
    sample_md = "# Introduction\n## Background\n## Goals\n# Architecture\n## Components"
    toc = build_md_toc(sample_md)
    print(textwrap.indent(toc, "    "))

    # --- load_data_file (uses the bundled sample files if present) ---
    print("\n[5] load_data_file")
    _here = Path(__file__).parent
    for candidate in [
        _here / "examples" / "sample_inventory.csv",
        _here / "examples" / "sample_project.json",
        _here / "examples" / "sample_report.yaml",
    ]:
        if candidate.exists():
            data = load_data_file(candidate)
            n = len(data) if isinstance(data, list) else len(data.keys())  # type: ignore[union-attr]
            print(f"    {candidate.name}: loaded {n} top-level items/rows")

    print("\nAll demos complete.")
