# excel_tools/ — Implementation Roadmap

Scripts are grouped by complexity. `[implemented]` items are present and tested;
`[planned]` items are documented stubs for future contributors.

---

## Beginner

| Feature | Script | Status |
|---------|--------|--------|
| Excel creation from CSV | `generators/single_sheet_generator.py` | **[implemented]** |
| Excel creation from JSON | `generators/single_sheet_generator.py` | **[implemented]** |
| CSV-to-Excel (multi-sheet) | `imports/csv_to_excel.py` | **[implemented]** |
| JSON-to-Excel | `imports/json_to_excel.py` | [planned] |
| SQL-to-Excel | `imports/sql_to_excel.py` | [planned] |

---

## Intermediate

| Feature | Script | Status |
|---------|--------|--------|
| Formatted report (CF + totals + auto-size) | `generators/formatted_report.py` | **[implemented]** |
| Excel-to-JSON export | `exports/excel_to_json.py` | **[implemented]** |
| Excel-to-CSV export | `exports/excel_to_csv.py` | [planned] |
| Excel-to-Markdown export | `exports/excel_to_markdown.py` | [planned] |
| Workbook merging | `transformers/workbook_merge.py` | **[implemented]** |
| Sheet validation (required cols, non-negative, no empty) | `validators/sheet_validator.py` | **[implemented]** |
| Schema-based validation | `validators/schema_validator.py` | [planned] |
| Duplicate row detection | `validators/duplicate_checker.py` | [planned] |
| Date format validation | `validators/date_format_checker.py` | [planned] |
| Field/column updater | `updaters/field_updater.py` | [planned] |
| Template filler | `updaters/template_filler.py` | [planned] |
| Bulk cell writer | `updaters/bulk_cell_writer.py` | [planned] |

---

## Advanced

| Feature | Script | Status |
|---------|--------|--------|
| Multi-sheet dashboard + chart | `dashboards/dashboard_workbook.py` | **[implemented]** |
| Row filtering to new workbook | `transformers/row_filter.py` | [planned] |
| Sheet splitter (by key column) | `transformers/sheet_splitter.py` | [planned] |
| Column renamer in-place | `transformers/column_renamer.py` | [planned] |
| Formula insertion | `generators/formula_inserter.py` | [planned] |
| Named range parser | `parsers/named_range_parser.py` | [planned] |
| Formula extractor | `parsers/formula_extractor.py` | [planned] |
| Summary sheet generator | `dashboards/summary_sheet_generator.py` | [planned] |
| Excel diff (two workbooks) | `validators/excel_diff.py` | [planned] |
| Large-workbook transformation (chunked) | `transformers/large_workbook_transformer.py` | [planned] |

---

## Showcase

| Feature | Script | Status |
|---------|--------|--------|
| Executive workbook (cover + KPIs + CF + chart) | `dashboards/executive_workbook.py` | **[implemented]** |
| Engineering risk/effort matrix | `dashboards/engineering_matrix.py` | [planned] |
| Chart generation standalone | `generators/chart_generator.py` | [planned] |
| Conditional formatting toolkit | `generators/conditional_format_demo.py` | [planned] |

---

## Helpers reference

| Feature | Location | Status |
|---------|----------|--------|
| `autosize_columns` | `helpers.py` | **[implemented]** |
| `write_header_row` | `helpers.py` | **[implemented]** |
| `apply_color_scale` | `helpers.py` | **[implemented]** |
| `write_records_to_sheet` | `helpers.py` | **[implemented]** |
| `add_bar_chart` | `helpers.py` | **[implemented]** |
| `add_line_chart` | `helpers.py` | [planned] |
| `add_pie_chart` | `helpers.py` | [planned] |
| `write_formula_row` | `helpers.py` | [planned] |
| `protect_sheet` | `helpers.py` | [planned] |
