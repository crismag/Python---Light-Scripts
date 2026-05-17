# report_builders/

Intermediate report-building scripts.  Each script reads structured data and produces
a complete, publication-ready Markdown document.

## Scripts

- **`changelog_generator.py`** — Build a CHANGELOG.md from a JSON list of versioned release
  entries.  Change types (feat, fix, improve, docs, chore, etc.) are grouped under sub-headings
  within each version section, following Keep-a-Changelog conventions.
