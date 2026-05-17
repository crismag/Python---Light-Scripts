# pdf_tools

Lightweight, self-contained PDF utility scripts built on **reportlab** (generation) and **pypdf**
(manipulation). Every script is copy-and-run — no shared helpers import, no framework.

---

## Folder map

| Folder | Contents |
|---|---|
| `generators/` | Create PDFs from scratch (text, tables, watermarks, certificates) |
| `mergers/` | Merge and split existing PDFs |
| `transformers/` | Transform page layout of existing PDFs (gutter/margin adjustment) |
| `extractors/` | Extract text and metadata from PDFs |
| `report_builders/` | Advanced multi-section reports and invoices |
| `fillers/` | PDF form filling (planned) |
| `parsers/` | Low-level PDF structure parsing (planned) |
| `converters/` | Convert other formats to/from PDF (planned) |
| `templates/` | Reusable reportlab page templates (planned) |
| `forms/` | AcroForm creation utilities (planned) |
| `examples/` | Sample data files used by scripts |
| `tests/` | pytest test suite |

---

## Start Here

Every script at a glance — difficulty level, what it does, what it needs, and
what it writes. Exact run commands are in
[CLI usage examples](#cli-usage-examples) below; every script also accepts `--help`.

| Script | Level | Purpose | Dependencies | Output |
|--------|-------|---------|--------------|--------|
| [generators/simple_pdf.py](generators/simple_pdf.py) | Beginner | Generate a basic PDF from a title + body text | `reportlab` | `.pdf` |
| [generators/table_report.py](generators/table_report.py) | Intermediate | Paginated table report from CSV or JSON | `reportlab` | `.pdf` |
| [generators/watermark.py](generators/watermark.py) | Intermediate | Stamp a diagonal text watermark across every page | `reportlab`, `pypdf` | `.pdf` |
| [mergers/pdf_merge.py](mergers/pdf_merge.py) | Intermediate | Merge multiple PDFs into one output file | `pypdf` | `.pdf` |
| [mergers/pdf_split.py](mergers/pdf_split.py) | Intermediate | Split a PDF into per-page or page-range files | `pypdf` | `.pdf` files |
| [extractors/pdf_text_extract.py](extractors/pdf_text_extract.py) | Intermediate | Extract text and metadata to .txt or JSON | `pypdf` | `.txt` / `.json` |
| [report_builders/invoice_generator.py](report_builders/invoice_generator.py) | Advanced | Styled invoice PDF from a JSON spec | `reportlab` | `.pdf` |
| [transformers/pdf_gutter_adjust.py](transformers/pdf_gutter_adjust.py) | Advanced | Adjust a PDF's inside/gutter margin by shifting page content outward (single-file or batch) | `pypdf` | `.pdf` |
| [report_builders/engineering_report.py](report_builders/engineering_report.py) | Showcase | Multi-section report with TOC, charts, tables | `reportlab` | `.pdf` |
| [generators/certificate_generator.py](generators/certificate_generator.py) | Showcase | Presentation-quality certificate PDF(s) | `reportlab` | `.pdf` file(s) |
| [helpers.py](helpers.py) | Reference | Copy-ready helper functions with a standalone demo | `reportlab`, `pypdf` | demo `.pdf` |

---

## CLI usage examples

```bash
# Beginner
python generators/simple_pdf.py --title "Hello World" --text "My first PDF." --output out/hello.pdf

# Table report from CSV
python generators/table_report.py --input examples/sample_metrics.csv --output out/metrics_report.pdf

# Table report from JSON
python generators/table_report.py --input examples/sample_invoice.json --output out/json_report.pdf

# Merge PDFs
python mergers/pdf_merge.py a.pdf b.pdf c.pdf --output out/merged.pdf

# Split PDF (per-page)
python mergers/pdf_split.py input.pdf --output-dir out/pages/

# Adjust inside/gutter margin (shift content outward by 0.25 in)
python transformers/pdf_gutter_adjust.py book.pdf book_adjusted.pdf --shift 0.25 --unit in

# Split PDF (page ranges)
python mergers/pdf_split.py input.pdf --output-dir out/parts/ --ranges 1-3 4-6

# Extract text
python extractors/pdf_text_extract.py input.pdf --output out/text.txt
python extractors/pdf_text_extract.py input.pdf --output out/meta.json --format json

# Watermark
python generators/watermark.py input.pdf --text "CONFIDENTIAL" --output out/watermarked.pdf

# Invoice
python report_builders/invoice_generator.py examples/sample_invoice.json --output out/invoice.pdf

# Engineering report
python report_builders/engineering_report.py --output out/engineering_report.pdf

# Certificate
python generators/certificate_generator.py --recipient "Jane Smith" --title "Certificate of Excellence" --output out/cert.pdf
python generators/certificate_generator.py --input examples/recipients.json --output-dir out/certs/
```

---

## Dependencies

```
reportlab>=4.0   # PDF generation
pypdf>=4.0       # PDF reading / manipulation
```

Install: `pip install -r pdf_tools/requirements.txt`

HTML-to-PDF (weasyprint / xhtml2pdf) is noted as **planned** in ROADMAP.md to avoid a heavy
native dependency.

---

## Safety & portability notes

- Scripts never overwrite an existing output file unless `--force` is passed.
- PDF splitting/merging never overwrites input files (output paths are validated).
- All output parent directories are created automatically.
- Path-traversal is guarded when extracting page ranges to a directory.
- Compatible with Python 3.9+ on Linux, macOS, and Windows.
- `helpers.py` is a standalone reference module; example scripts do **not** import it.
