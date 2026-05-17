# tests/

Pytest test suite for the document_generation section.

## Files

- **`test_helpers.py`** — Unit tests for all functions in `helpers.py`:
  `render_template`, `slugify`, `build_md_table`, `build_md_toc`, `load_data_file`.

- **`test_table_generator.py`** — Tests for `markdown/table_generator.py`:
  internal helpers, `load_records`, `generate_table` integration, and CLI via `main()`.

Run with: `python -m pytest document_generation/tests -q`
