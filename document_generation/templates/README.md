# templates/

Jinja2 template files (.j2) used by the scripted document generators.

## Files

- **`report.md.j2`** — Markdown report template driven by the YAML report spec.
  Used by `templating/yaml_report_generator.py` when passed via `--template`.
  Renders title, metadata table, table of contents, section body text, and optional
  metrics / incidents / action-item tables.

- **`report.html.j2`** — HTML report template with a linked `report.css` stylesheet.
  Renders a styled header, TOC, and one `<section>` per report spec section.
