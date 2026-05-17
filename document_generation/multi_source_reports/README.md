# multi_source_reports/

Advanced scripts that merge heterogeneous data sources into a single cohesive report.

## Scripts

- **`multi_source_report.py`** — Combine a JSON project file, a YAML report spec, and a CSV
  inventory file into one Markdown engineering report.  Each source produces a titled section.
  A generated table of contents links all sections.  Any source can be omitted via its flag.
