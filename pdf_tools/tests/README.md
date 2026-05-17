# tests/

pytest test suite for pdf_tools scripts and helpers.

Test files:
- `test_helpers.py` — unit tests for helpers.py (merge page counts, watermark page count preservation)
- `test_simple_pdf.py` — integration test: run simple_pdf.py, reopen with pypdf, assert validity
- `test_pdf_merge.py` — integration test: run pdf_merge.py on generated inputs, verify merged page count
