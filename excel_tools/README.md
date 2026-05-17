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

## Complexity Levels

### Beginner
| Script | Description |
|--------|-------------|
| `generators/single_sheet_generator.py` | CSV/JSON → styled single-sheet .xlsx |
| `imports/csv_to_excel.py`             | One or more CSVs → multi-sheet .xlsx  |

### Intermediate
| Script | Description |
|--------|-------------|
| `exports/excel_to_json.py`        | .xlsx sheet → JSON records file           |
| `generators/formatted_report.py`  | CSV → report with CF, totals, auto-sizing |
| `transformers/workbook_merge.py`  | Merge multiple .xlsx into one workbook    |
| `validators/sheet_validator.py`   | Validate columns/values, exit non-zero    |

### Advanced
| Script | Description |
|--------|-------------|
| `dashboards/dashboard_workbook.py` | Raw data sheet + aggregated Summary + chart |

### Showcase
| Script | Description |
|--------|-------------|
| `dashboards/executive_workbook.py` | Cover/KPI + Summary + Detail + CF + chart |

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
