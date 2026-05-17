# document_generation — Implementation Roadmap

Progressive implementation plan, grouped by complexity.

---

## Beginner

| Status | Script | Description |
|--------|--------|-------------|
| [implemented] | `markdown/table_generator.py` | Read a JSON array or CSV of records; emit a Markdown table file. |
| [implemented] | `markdown/json_to_markdown.py` | Turn a JSON object into a structured Markdown document (headings, lists, nested keys). |

---

## Intermediate

| Status | Script | Description |
|--------|--------|-------------|
| [implemented] | `report_builders/changelog_generator.py` | Build a CHANGELOG.md / release-notes file from a JSON list of change entries. |
| [implemented] | `templating/yaml_report_generator.py` | Render a multi-section Markdown report from a YAML spec using Jinja2. |
| [implemented] | `docx/docx_report.py` | Generate a formatted .docx report from a JSON dataset using python-docx. |
| [planned]     | `report_builders/audit_report_generator.py` | Generate a structured audit report from a JSON list of findings grouped by severity. |
| [planned]     | `report_builders/release_notes_generator.py` | Produce polished release notes from a CHANGELOG-style JSON file (highlights, upgrade guide). |

---

## Advanced

| Status | Script | Description |
|--------|--------|-------------|
| [implemented] | `multi_source_reports/multi_source_report.py` | Merge a JSON + YAML + CSV file into one Markdown engineering report with TOC. |
| [planned]     | `multi_source_reports/system_inventory_report.py` | Combine multiple CSV/JSON inventory sources into a site-wide system report with group stats. |
| [planned]     | `report_builders/executive_summary_generator.py` | Generate a concise executive summary from a richer JSON dataset (KPI cards, bullets). |

---

## Showcase

| Status | Script | Description |
|--------|--------|-------------|
| [implemented] | `html/html_report.py` | Dashboard-style HTML report — embedded CSS, TOC, stat cards, data tables, inline-SVG bar chart. |
| [planned]     | `markdown/markdown_knowledgebook_generator.py` | Produce a multi-file Markdown knowledge book (one .md per topic) from a YAML definition. |
| [planned]     | `report_builders/yaml_driven_report_generator.py` | Fully YAML-driven report builder: layouts, sections, charts, tables all defined in YAML. |

---

## Notes

- **[implemented]** — script exists, runs, and produces output.
- **[planned]** — design scoped; implementation not yet started.
- All planned scripts follow the same design rules: self-contained, `argparse` CLI, safe defaults,
  real output, ruff-clean, Python 3.9+.
