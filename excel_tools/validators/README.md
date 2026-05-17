# validators/

Scripts that **inspect and validate** Excel workbooks against rule sets without modifying them.

## Scripts
- `sheet_validator.py` — INTERMEDIATE: check required columns, non-negative numerics, no empty key cells;
  prints a structured report and exits non-zero when validation fails.

## Planned
- `schema_validator.py` — validate a sheet against a JSON schema definition.
- `duplicate_checker.py` — flag duplicate rows across one or more key columns.
- `date_format_checker.py` — ensure all date cells in a column use a consistent format.
