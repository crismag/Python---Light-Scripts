# templating/

Intermediate scripts that use Jinja2 to render documents from structured data specs.

## Scripts

- **`yaml_report_generator.py`** — Render a multi-section Markdown report from a YAML spec.
  Uses a built-in Jinja2 template by default; pass `--template` to supply a custom `.j2` file.
  The YAML spec drives section titles, body text, and optional tables (metrics, action items).
