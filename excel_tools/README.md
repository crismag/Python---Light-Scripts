# excel_tools/

A self-contained cookbook of Excel automation scripts built on **openpyxl** and **pandas**.
Every script is fully independent — copy a single file and run it.

---

## Folder Map

| Folder          | Purpose                                                         |
|-----------------|-----------------------------------------------------------------|
| `generators/`   | Create workbooks from scratch or from CSV/JSON data             |
| `parsers/`      | Read and extract data from existing workbooks                   |
| `transformers/` | Merge, split, or reshape workbooks                              |
| `validators/`   | Validate sheets against rule sets without modifying them        |
| `updaters/`     | Selectively update cells/rows in existing workbooks             |
| `dashboards/`   | Multi-sheet, chart-equipped workbooks for reporting             |
| `imports/`      | Convert external formats (CSV, JSON, SQL) into Excel            |
| `exports/`      | Extract data from Excel into other formats (JSON, CSV, …)       |
| `examples/`     | Sample datasets (`sample_sales.csv`, `sample_employees.json`)   |
| `tests/`        | Pytest suite — run with `python -m pytest excel_tools/tests -q` |

---

## Start Here

Every script at a glance — difficulty level, what it does, what it needs, and
what it writes. Exact run commands are in
[CLI Usage Examples](#cli-usage-examples) below; every script also accepts `--help`.

| Script | Level | Purpose | Dependencies | Output |
|--------|-------|---------|--------------|--------|
| [generators/single_sheet_generator.py](generators/single_sheet_generator.py) | Beginner | CSV/JSON → styled single-sheet workbook | `openpyxl` | `.xlsx` |
| [imports/csv_to_excel.py](imports/csv_to_excel.py) | Beginner | One or more CSVs → multi-sheet workbook | `openpyxl` | `.xlsx` |
| [exports/excel_to_json.py](exports/excel_to_json.py) | Intermediate | Worksheet → JSON records (file or stdout) | `openpyxl` | `.json` / stdout |
| [generators/formatted_report.py](generators/formatted_report.py) | Intermediate | CSV → report with conditional formatting, totals, auto-sizing | `openpyxl` | `.xlsx` |
| [transformers/workbook_merge.py](transformers/workbook_merge.py) | Intermediate | Merge multiple workbooks into one | `openpyxl` | `.xlsx` |
| [validators/sheet_validator.py](validators/sheet_validator.py) | Intermediate | Validate columns/values; non-zero exit on failure | `openpyxl` | terminal report + exit code |
| [dashboards/dashboard_workbook.py](dashboards/dashboard_workbook.py) | Advanced | Raw data sheet + aggregated Summary + chart | `openpyxl` | `.xlsx` |
| [dashboards/executive_workbook.py](dashboards/executive_workbook.py) | Showcase | Cover/KPI + Summary + Detail + conditional formatting + chart | `openpyxl` | `.xlsx` |
| [helpers.py](helpers.py) | Reference | Copy-ready helper functions with a standalone demo | `openpyxl` | demo `.xlsx` |

---

## CLI Usage Examples

```bash
# Generate a styled .xlsx from CSV
python excel_tools/generators/single_sheet_generator.py \
    --input excel_tools/examples/sample_sales.csv \
    --output output/sales.xlsx

# Generate a styled .xlsx from JSON
python excel_tools/generators/single_sheet_generator.py \
    --input excel_tools/examples/sample_employees.json \
    --output output/employees.xlsx --sheet-name Employees

# Convert one or more CSVs to a multi-sheet workbook
python excel_tools/imports/csv_to_excel.py \
    --inputs excel_tools/examples/sample_sales.csv \
    --output output/workbook.xlsx

# Export a sheet to JSON
python excel_tools/exports/excel_to_json.py \
    --input output/sales.xlsx --output output/sales.json --pretty

# Export with field filtering
python excel_tools/exports/excel_to_json.py \
    --input output/sales.xlsx --fields date region revenue --stdout

# Formatted report with conditional formatting
python excel_tools/generators/formatted_report.py \
    --input excel_tools/examples/sample_sales.csv \
    --output output/report.xlsx --title "Q1-Q3 Sales Report"

# Merge multiple workbooks
python excel_tools/transformers/workbook_merge.py \
    --inputs output/sales.xlsx output/employees.xlsx \
    --output output/merged.xlsx

# Validate a sheet (auto-inferred rules)
python excel_tools/validators/sheet_validator.py --input output/sales.xlsx

# Validate with explicit rules
python excel_tools/validators/sheet_validator.py \
    --input output/sales.xlsx \
    --required-cols date region revenue \
    --nonneg-cols units unit_price revenue \
    --nonempty-cols date region

# Multi-sheet dashboard with chart
python excel_tools/dashboards/dashboard_workbook.py \
    --input excel_tools/examples/sample_sales.csv \
    --output output/dashboard.xlsx

# Executive workbook (showcase)
python excel_tools/dashboards/executive_workbook.py \
    --input excel_tools/examples/sample_sales.csv \
    --output output/executive.xlsx \
    --company "Acme Corp" \
    --report-title "Q1-Q3 2024 Sales Performance"

# helpers.py standalone demo
python excel_tools/helpers.py --out output/helpers_demo.xlsx
```

---

## Dependencies

Install with:
```bash
pip install -r excel_tools/requirements.txt
```

| Package   | Min version | Used for                                    |
|-----------|------------|---------------------------------------------|
| openpyxl  | 3.1.0      | All workbook read/write, charts, formatting |
| pandas    | 2.0.0      | Available for future scripts; not required by current scripts |

Python 3.9+ required.

---

## Safety & Portability Notes

- **No overwrite without `--force`** — every script refuses to overwrite an existing output file
  unless you explicitly pass `--force`. This prevents accidental data loss.
- **Parent directory auto-creation** — output parent directories are created automatically
  (`parents=True, exist_ok=True`), so you don't need to `mkdir` first.
- **Self-contained scripts** — each script in `generators/`, `imports/`, etc. imports only from
  the standard library and pip packages. No sibling imports. Copy one file; it runs.
- **`helpers.py` is a reference module** — it is NOT imported by the example scripts. Use it
  as a copy-paste reference or for learning. It has its own `if __name__ == "__main__"` demo.
- **`data_only=True`** — export/validation scripts open workbooks with `data_only=True` so they
  read computed cell values rather than formula strings.
- **Sheet names** — Excel limits sheet names to 31 characters; all scripts enforce this.
- **Encoding** — all file I/O uses UTF-8 explicitly.
