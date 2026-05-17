# pdf_tools — Implementation Roadmap

Scripts are grouped by complexity. `[implemented]` means a working script exists;
`[planned]` means it is scoped but not yet written.

---

## Beginner

- [implemented] **Simple PDF generation** (`generators/simple_pdf.py`) — title + body text from
  CLI args or a plain-text file; basic paragraphs, auto page breaks.

---

## Intermediate

- [implemented] **Table report** (`generators/table_report.py`) — paginated PDF table from a CSV
  or JSON list of records; auto-width columns, header row, page numbers.
- [implemented] **PDF merging** (`mergers/pdf_merge.py`) — combine an ordered list of PDFs into
  one output file using pypdf.
- [implemented] **PDF splitting** (`mergers/pdf_split.py`) — split by individual pages or
  named page ranges into an output directory.
- [implemented] **Text/metadata extraction** (`extractors/pdf_text_extract.py`) — extract full
  text and document metadata to .txt or structured JSON.
- [implemented] **Watermarking** (`generators/watermark.py`) — diagonal text watermark stamped
  on every page (reportlab stamp + pypdf overlay).
- [planned] **Form filling** (`fillers/fill_form.py`) — populate AcroForm fields from a JSON
  mapping using pypdf.
- [planned] **CSV-to-PDF** (`converters/csv_to_pdf.py`) — thin wrapper around table_report for
  CSV-specific defaults and styling.
- [planned] **JSON-to-PDF** (`converters/json_to_pdf.py`) — render arbitrary JSON structures as
  formatted PDF documents.

---

## Advanced

- [implemented] **Invoice generator** (`report_builders/invoice_generator.py`) — styled invoice
  from a JSON spec: seller/buyer blocks, itemized table, tax computation, totals, header/footer.
- [planned] **Markdown-to-PDF** (`converters/markdown_to_pdf.py`) — parse Markdown with
  mistune/commonmark and render via reportlab platypus.
- [planned] **HTML-to-PDF** (`converters/html_to_pdf.py`) — convert an HTML file to PDF
  (weasyprint or xhtml2pdf); noted as planned to avoid a heavy native dependency at this stage.
- [planned] **Chart embedding** (`generators/chart_embed.py`) — embed matplotlib/reportlab
  charts (bar, line, pie) as vector graphics inside a PDF page.
- [planned] **Multi-source report assembly** (`report_builders/multi_source_report.py`) — merge
  a cover page, a chart page, a data table, and external PDFs into one cohesive report.

---

## Showcase

- [implemented] **Engineering / audit report** (`report_builders/engineering_report.py`) —
  polished multi-section report: cover page, auto-generated table of contents, section headers,
  data table, simple bar chart drawn in reportlab graphics, page-numbered footers.
- [implemented] **Certificate generator** (`generators/certificate_generator.py`) — single or
  batch certificate PDFs; decorative border, recipient name, award title, date; driven by CLI
  args or a JSON recipient list.
- [planned] **Audit report** (`report_builders/audit_report.py`) — structured audit findings
  report with severity tables, executive summary, and appendix.
- [planned] **Batch certificate pipeline** (`report_builders/batch_certificates.py`) — CSV-driven
  batch certificate generation with per-row customisation.
