# markdown/

Beginner-level scripts that produce GitHub-Flavored Markdown files from structured data.

## Scripts

- **`table_generator.py`** — Read a JSON array or CSV file and emit a padded Markdown table.
  Supports `--columns` to select a subset, `--title` for an H1 heading, and `--key` to
  extract a nested list from a JSON object.
- **`json_to_markdown.py`** — Convert any JSON object or array into a structured Markdown
  document: top-level keys become `##` headings, nested objects and lists render as bullets.
