# document_generation

Practical, self-contained Python scripts for generating documents in multiple formats
(Markdown, HTML, DOCX) from structured data sources (JSON, YAML, CSV).

---

## Folder Map

| Folder | Contents |
|--------|----------|
| `markdown/` | Beginner Markdown generators (tables, JSON-to-doc) |
| `html/` | Showcase HTML dashboard report |
| `docx/` | Word document (.docx) report generator |
| `templating/` | Jinja2-driven YAML-to-Markdown renderer |
| `report_builders/` | Intermediate report builders (changelog, etc.) |
| `multi_source_reports/` | Advanced multi-source data merge report |
| `assets/` | Shared CSS stylesheet for HTML reports |
| `examples/` | Sample data files (JSON, YAML, CSV) |
| `templates/` | Jinja2 template files (.j2) |
| `tests/` | Pytest test suite |

---

## Start Here

Every script at a glance — difficulty level, what it does, what it needs, and
what it writes. Exact run commands are in
[CLI Usage Examples](#cli-usage-examples) below; every script also accepts `--help`.

| Script | Level | Purpose | Dependencies | Output |
|--------|-------|---------|--------------|--------|
| [markdown/table_generator.py](markdown/table_generator.py) | Beginner | JSON array or CSV → GitHub-Flavored Markdown table | stdlib only | `.md` table file |
| [markdown/json_to_markdown.py](markdown/json_to_markdown.py) | Beginner | JSON object → structured Markdown document | stdlib only | `.md` document |
| [report_builders/changelog_generator.py](report_builders/changelog_generator.py) | Intermediate | JSON change-log entries → CHANGELOG | stdlib only | `CHANGELOG.md` |
| [templating/yaml_report_generator.py](templating/yaml_report_generator.py) | Intermediate | YAML spec + Jinja2 template → Markdown report | `jinja2`, `pyyaml` | `.md` report |
| [docx/docx_report.py](docx/docx_report.py) | Intermediate | JSON project data → formatted Word document | `python-docx` | `.docx` file |
| [multi_source_reports/multi_source_report.py](multi_source_reports/multi_source_report.py) | Advanced | Merge JSON + YAML + CSV into one Markdown report | `pyyaml` | `.md` report |
| [html/html_report.py](html/html_report.py) | Showcase | JSON/YAML/CSV → polished HTML dashboard with SVG chart | `pyyaml` | `.html` page |
| [helpers.py](helpers.py) | Reference | Copy-ready helper functions with a standalone demo | stdlib only | demo `.md` files |

---

## CLI Usage Examples

```bash
# Markdown table from CSV
python document_generation/markdown/table_generator.py \
    document_generation/examples/sample_inventory.csv /tmp/inventory.md

# Markdown table from JSON array key (--key selects a sub-list)
python document_generation/markdown/table_generator.py \
    document_generation/examples/sample_project.json /tmp/team.md --key team

# JSON object → structured Markdown
python document_generation/markdown/json_to_markdown.py \
    document_generation/examples/sample_project.json /tmp/project.md \
    --title "Orion Pipeline"

# CHANGELOG from JSON entries
python document_generation/report_builders/changelog_generator.py \
    document_generation/examples/sample_changelog.json /tmp/CHANGELOG.md \
    --project "Orion Data Pipeline"

# YAML spec → Markdown report (built-in template)
python document_generation/templating/yaml_report_generator.py \
    document_generation/examples/sample_report.yaml /tmp/report.md

# YAML spec → Markdown report (custom .j2 template)
python document_generation/templating/yaml_report_generator.py \
    document_generation/examples/sample_report.yaml /tmp/report.md \
    --template document_generation/templates/report.md.j2

# Multi-source Markdown report (JSON + YAML + CSV)
python document_generation/multi_source_reports/multi_source_report.py \
    --json  document_generation/examples/sample_project.json \
    --yaml  document_generation/examples/sample_report.yaml \
    --csv   document_generation/examples/sample_inventory.csv \
    --output /tmp/engineering_report.md

# HTML dashboard report from JSON
python document_generation/html/html_report.py \
    document_generation/examples/sample_project.json /tmp/project.html

# HTML dashboard report from YAML
python document_generation/html/html_report.py \
    document_generation/examples/sample_report.yaml /tmp/report.html

# DOCX Word document from JSON
python document_generation/docx/docx_report.py \
    document_generation/examples/sample_project.json /tmp/project.docx

# helpers.py demo (standalone — not imported by any script)
python document_generation/helpers.py

# Run tests
python -m pytest document_generation/tests -q
```

---

## Dependencies

```
jinja2>=3.1
pyyaml>=6.0
markdown>=3.5
python-docx>=1.1
```

Install with:

```bash
pip install -r document_generation/requirements.txt
```

---

## Safety & Portability Notes

- **No overwrite by default.** Every script refuses to clobber an existing output file unless
  `--force` is given.  Parent directories are created automatically as needed.
- **Self-contained scripts.** Each script runs standalone — copy a single file and it works.
  No script imports `helpers.py` or any sibling module.
- **`helpers.py` is a reference only.** It is an independently runnable study module containing
  copy-ready helper functions; it is not a shared library.
- **Python 3.9+.** All scripts use `from __future__ import annotations` for forward-compatible type hints.
- **No internet access required.** All output is generated locally from local data files.
- **DOCX generation** requires `python-docx`; no Office installation needed.
