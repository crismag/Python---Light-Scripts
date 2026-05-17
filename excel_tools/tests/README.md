# tests/

Pytest test suite for `excel_tools/`. Tests are self-contained: they generate temporary data,
run scripts or call helpers directly, then inspect produced workbooks with openpyxl.

## Files
- `test_helpers.py` — unit tests for all public functions in `helpers.py`.
- `test_single_sheet_generator.py` — integration test: run `single_sheet_generator.py` against
  temporary CSV and JSON inputs, reopen the resulting .xlsx, and assert cell contents.

Run with: `python -m pytest excel_tools/tests -q`
No network access required; all fixtures use `tmp_path`.
