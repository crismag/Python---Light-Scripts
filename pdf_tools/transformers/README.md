# transformers/

Scripts that transform the layout of existing PDF pages using pypdf — content
is translated, not re-flowed or rasterized.

Scripts in this folder:
- `pdf_gutter_adjust.py` — ADVANCED: adjust a PDF's inside/gutter (binding) margin by shifting page content outward; supports single-file and batch modes

## pdf_gutter_adjust.py

Adjust the inside/gutter margin of an existing PDF by translating page content
outward. Right-hand (odd) pages move toward the right edge and left-hand (even)
pages move toward the left edge, so the binding margin grows. Page size, PDF
boxes and metadata are preserved; pages are never rasterized.

Install: `pip install pypdf`

```bash
# Grow a 1.00 in inside margin to 1.25 in (shift content outward by 0.25 in)
python transformers/pdf_gutter_adjust.py book.pdf book_adjusted.pdf --shift 0.25 --unit in

# Same shift expressed in points
python transformers/pdf_gutter_adjust.py book.pdf book_adjusted.pdf --inside-shift 18 --unit pt

# Treat page 1 as a left-hand (verso) page
python transformers/pdf_gutter_adjust.py book.pdf book_adjusted.pdf --first-page-side left

# Only shift selected pages (1-based: ranges and singletons)
python transformers/pdf_gutter_adjust.py book.pdf out.pdf --page-range 1-20,45,80-120

# Derive the output name from --suffix (default: _gutter_adjusted)
python transformers/pdf_gutter_adjust.py book.pdf --shift 0.25

# Batch-process a folder of PDFs
python transformers/pdf_gutter_adjust.py --batch-dir ./pdfs --output-dir ./adjusted \
    --recursive --glob "*.pdf" --shift 0.25

# Preview the changes without writing any file
python transformers/pdf_gutter_adjust.py book.pdf out.pdf --shift 0.25 --dry-run
```

Key options: `--shift/--inside-shift/--gutter-shift/--margin-delta`, `--unit`,
`--first-page-side`, `--odd-page-direction`, `--even-page-direction`,
`--page-range`, `--skip-pages`, `--only-pages`, `--shift-x-odd/even`,
`--shift-y-odd/even`, `--preserve-boxes/--no-preserve-boxes`,
`--include-annotations`, `--backup`, `--suffix`, `--output-dir`, `--batch-dir`,
`--recursive`, `--glob`, `--dry-run`, `--overwrite`, `--verbose`.

Exit codes: `0` success, `1` error, `2` bad command-line arguments.
