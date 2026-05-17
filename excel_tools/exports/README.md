# exports/

Scripts that **extract data from Excel** and write it to another format (JSON, CSV, Parquet, Markdown, etc.).

## Scripts
- `excel_to_json.py` — INTERMEDIATE: read a chosen sheet from an .xlsx file and export it as a
  JSON array (records orientation), with optional pretty-printing and field filtering.

## Planned
- `excel_to_csv.py` — export every sheet of a workbook to individual CSV files.
- `excel_to_markdown.py` — render a sheet as a Markdown table for documentation use.
- `excel_to_parquet.py` — export a sheet to a Parquet file via pandas.
