# updaters/

Scripts that **read and selectively update** cells, rows, or sheets in existing workbooks.

## Planned
- `field_updater.py` — update a specific column's values using a lookup dict or CSV mapping.
- `template_filler.py` — fill named placeholder cells in an .xlsx template from a JSON/dict payload.
- `bulk_cell_writer.py` — write a list of (sheet, cell, value) triples into a workbook in one pass.

Scripts here must never silently overwrite the input file; they should always write to a new path or
require an explicit --in-place flag.
