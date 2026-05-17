"""
generators/certificate_generator.py — SHOWCASE: presentation-quality certificate PDFs.

Generates a single certificate from CLI args, or a batch of certificates from a JSON
file containing a list of recipient objects. Each certificate features a decorative
double-line border, the organisation name, certificate title, recipient name in large
script-style font, award description, and the date.

Example commands (single certificate):
    python generators/certificate_generator.py \\
        --recipient "Jane Smith" \\
        --title "Certificate of Excellence" \\
        --description "In recognition of outstanding contributions to the Q1 2024 project." \\
        --output out/cert_jane.pdf

Example commands (batch from JSON):
    python generators/certificate_generator.py \\
        --input examples/recipients.json \\
        --output-dir out/certs/

JSON format for --input:
    [
      {"recipient": "Jane Smith", "title": "Certificate of Excellence",
       "description": "...", "date": "2024-03-15"},
      ...
    ]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas as rl_canvas

# ---------------------------------------------------------------------------
# Page geometry (landscape for certificates)
# ---------------------------------------------------------------------------
PAGE_H, PAGE_W = letter  # swap: landscape
MARGIN = 0.85 * inch

# ---------------------------------------------------------------------------
# Colours & style
# ---------------------------------------------------------------------------
GOLD = colors.HexColor("#c8922a")
NAVY = colors.HexColor("#1a3a6b")
DARK_GREY = colors.HexColor("#333333")
LIGHT_GREY = colors.HexColor("#aaaaaa")


# ---------------------------------------------------------------------------
# Core certificate rendering
# ---------------------------------------------------------------------------


def _draw_certificate(
    c: rl_canvas.Canvas,
    recipient: str,
    title: str,
    description: str,
    org_name: str,
    signatory: str,
    signatory_title: str,
    cert_date: str,
) -> None:
    """
    Draw a single certificate on the current canvas page (landscape Letter).

    Args:
        c:               Active reportlab Canvas, page not yet saved.
        recipient:       Name of the certificate recipient.
        title:           Certificate title (e.g. "Certificate of Completion").
        description:     Award description sentence.
        org_name:        Issuing organisation name.
        signatory:       Name of the signing authority.
        signatory_title: Title of the signing authority.
        cert_date:       Date string printed on the certificate.
    """
    w, h = PAGE_W, PAGE_H

    # Background: off-white cream
    c.setFillColor(colors.HexColor("#fdfaf4"))
    c.rect(0, 0, w, h, stroke=0, fill=1)

    # Outer double border
    border_margin = 22
    bm = border_margin
    c.setStrokeColor(GOLD)
    c.setLineWidth(3)
    c.rect(bm, bm, w - 2 * bm, h - 2 * bm, stroke=1, fill=0)

    c.setStrokeColor(NAVY)
    c.setLineWidth(1)
    inner = bm + 6
    c.rect(inner, inner, w - 2 * inner, h - 2 * inner, stroke=1, fill=0)

    # Corner ornaments — simple filled squares at corners of outer border
    sq = 8
    for cx, cy in [
        (bm, bm),
        (w - bm - sq, bm),
        (bm, h - bm - sq),
        (w - bm - sq, h - bm - sq),
    ]:
        c.setFillColor(GOLD)
        c.rect(cx, cy, sq, sq, stroke=0, fill=1)

    # Top decorative bar
    bar_h = 52
    c.setFillColor(NAVY)
    c.rect(inner + 1, h - inner - bar_h - 1, w - 2 * (inner + 1), bar_h, stroke=0, fill=1)

    # Organisation name in bar
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(w / 2, h - inner - bar_h + 18, org_name.upper())

    # Certificate title
    title_y = h - inner - bar_h - 52
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 26)
    c.drawCentredString(w / 2, title_y, title.upper())

    # Thin gold rule under title
    rule_y = title_y - 12
    c.setStrokeColor(GOLD)
    c.setLineWidth(1.5)
    c.line(w / 4, rule_y, 3 * w / 4, rule_y)

    # "Presented to"
    presented_y = rule_y - 28
    c.setFillColor(DARK_GREY)
    c.setFont("Helvetica-Oblique", 11)
    c.drawCentredString(w / 2, presented_y, "This certificate is proudly presented to")

    # Recipient name — large, in a contrasting colour
    name_y = presented_y - 52
    c.setFillColor(GOLD)
    c.setFont("Helvetica-Bold", 38)
    c.drawCentredString(w / 2, name_y, recipient)

    # Gold underline beneath recipient name
    name_w = c.stringWidth(recipient, "Helvetica-Bold", 38)
    c.setStrokeColor(GOLD)
    c.setLineWidth(1)
    c.line(w / 2 - name_w / 2, name_y - 4, w / 2 + name_w / 2, name_y - 4)

    # Description text — wrapped manually at ~85 chars
    desc_y = name_y - 40
    c.setFillColor(DARK_GREY)
    c.setFont("Helvetica", 10.5)
    _draw_wrapped_centred(
        c, description, w / 2, desc_y, max_width=w - 4 * MARGIN, font="Helvetica", size=10.5
    )

    # Bottom section: date left, signature right
    bottom_y = inner + 48

    # Date
    c.setFillColor(DARK_GREY)
    c.setFont("Helvetica", 9)
    c.drawString(inner + MARGIN, bottom_y + 16, "Date")
    c.setFont("Helvetica-Bold", 10)
    c.drawString(inner + MARGIN, bottom_y, cert_date)
    # Date underline
    c.setStrokeColor(LIGHT_GREY)
    c.setLineWidth(0.5)
    c.line(inner + MARGIN - 4, bottom_y - 4, inner + MARGIN + 140, bottom_y - 4)

    # Signature block (right side)
    sig_x = w - inner - MARGIN - 160
    c.setFillColor(DARK_GREY)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(sig_x, bottom_y, signatory)
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(sig_x, bottom_y - 14, signatory_title)
    c.setStrokeColor(LIGHT_GREY)
    c.setLineWidth(0.5)
    c.line(sig_x - 4, bottom_y - 4, sig_x + 200, bottom_y - 4)

    c.showPage()


def _draw_wrapped_centred(
    c: rl_canvas.Canvas,
    text: str,
    cx: float,
    y: float,
    max_width: float,
    font: str = "Helvetica",
    size: float = 10.5,
    leading: float = 15,
) -> None:
    """Draw text centred at cx, word-wrapping to fit max_width."""
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip() if current else word
        if c.stringWidth(candidate, font, size) <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    for line in lines:
        c.drawCentredString(cx, y, line)
        y -= leading


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_certificate(
    output_path: Path,
    recipient: str,
    title: str = "Certificate of Achievement",
    description: str = "",
    org_name: str = "Acme Organisation",
    signatory: str = "Director",
    signatory_title: str = "Executive Director",
    cert_date: str | None = None,
) -> None:
    """
    Generate a single certificate PDF and write it to output_path.

    Args:
        output_path:     Destination .pdf path.
        recipient:       Recipient's full name.
        title:           Certificate title line.
        description:     Award description sentence.
        org_name:        Issuing organisation.
        signatory:       Name on the signature line.
        signatory_title: Title on the signature line.
        cert_date:       Date string; defaults to today in ISO format.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if cert_date is None:
        cert_date = date.today().isoformat()

    c = rl_canvas.Canvas(str(output_path), pagesize=(PAGE_W, PAGE_H))
    _draw_certificate(
        c,
        recipient=recipient,
        title=title,
        description=description,
        org_name=org_name,
        signatory=signatory,
        signatory_title=signatory_title,
        cert_date=cert_date,
    )
    c.save()


def generate_batch_certificates(
    recipients: list[dict[str, Any]],
    output_dir: Path,
    defaults: dict[str, Any] | None = None,
    force: bool = False,
) -> list[Path]:
    """
    Generate one certificate PDF per recipient dict in a list.

    Each dict may contain: recipient, title, description, org_name, signatory,
    signatory_title, date. Missing keys fall back to `defaults` or built-in defaults.

    Args:
        recipients:  List of recipient dicts.
        output_dir:  Directory where certificate PDFs are written.
        defaults:    Shared default values for all recipients.
        force:       Overwrite existing output files if True.

    Returns:
        List of written output paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    defs: dict[str, Any] = defaults or {}
    written: list[Path] = []

    for i, rec in enumerate(recipients, start=1):
        name = rec.get("recipient", defs.get("recipient", f"Recipient {i}"))
        # Sanitise name for filename
        safe = "".join(ch if ch.isalnum() or ch in " -_" else "_" for ch in name).strip()
        safe = safe.replace(" ", "_")[:60]
        out = output_dir / f"cert_{i:03d}_{safe}.pdf"

        if out.exists() and not force:
            print(f"  SKIP (exists): {out}", file=sys.stderr)
            continue

        generate_certificate(
            output_path=out,
            recipient=name,
            title=rec.get("title", defs.get("title", "Certificate of Achievement")),
            description=rec.get("description", defs.get("description", "")),
            org_name=rec.get("org_name", defs.get("org_name", "Acme Organisation")),
            signatory=rec.get("signatory", defs.get("signatory", "Director")),
            signatory_title=rec.get(
                "signatory_title", defs.get("signatory_title", "Executive Director")
            ),
            cert_date=rec.get("date", defs.get("date")),
        )
        written.append(out)

    return written


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="certificate_generator.py",
        description="Generate presentation-quality certificate PDFs.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Single-cert args
    single = p.add_argument_group("Single certificate")
    single.add_argument("--recipient", metavar="NAME", help="Recipient full name")
    single.add_argument(
        "--title", default="Certificate of Achievement", help="Certificate title"
    )
    single.add_argument(
        "--description",
        default="In recognition of exceptional dedication and outstanding achievement.",
        help="Award description sentence",
    )
    single.add_argument(
        "--org-name", default="Acme Organisation", help="Issuing organisation name"
    )
    single.add_argument("--signatory", default="Director", help="Name on signature line")
    single.add_argument(
        "--signatory-title", default="Executive Director", help="Title on signature line"
    )
    single.add_argument(
        "--date",
        default="",
        metavar="YYYY-MM-DD",
        help="Certificate date (default: today)",
    )
    single.add_argument("--output", metavar="PDF", help="Output PDF path (single mode)")

    # Batch args
    batch = p.add_argument_group("Batch mode")
    batch.add_argument(
        "--input",
        metavar="JSON",
        help="JSON file with a list of recipient objects (batch mode)",
    )
    batch.add_argument(
        "--output-dir",
        metavar="DIR",
        help="Output directory for batch PDFs",
    )

    p.add_argument("--force", action="store_true", help="Overwrite existing output files")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    # Batch mode
    if args.input:
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
            return 1
        if not args.output_dir:
            print("ERROR: --output-dir is required in batch mode.", file=sys.stderr)
            return 1

        try:
            data: Any = json.loads(input_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            print(f"ERROR: invalid JSON — {exc}", file=sys.stderr)
            return 1

        if not isinstance(data, list):
            print("ERROR: JSON must be a list of recipient objects.", file=sys.stderr)
            return 1

        output_dir = Path(args.output_dir)
        written = generate_batch_certificates(data, output_dir, force=args.force)
        print(f"Generated {len(written)} certificate(s) in: {output_dir}")
        return 0

    # Single mode
    if not args.recipient:
        print("ERROR: --recipient is required (or use --input for batch mode).", file=sys.stderr)
        return 1
    if not args.output:
        print("ERROR: --output is required in single mode.", file=sys.stderr)
        return 1

    output_path = Path(args.output)
    if output_path.exists() and not args.force:
        print(
            f"ERROR: output already exists: {output_path}\n       Pass --force to overwrite.",
            file=sys.stderr,
        )
        return 1

    generate_certificate(
        output_path=output_path,
        recipient=args.recipient,
        title=args.title,
        description=args.description,
        org_name=args.org_name,
        signatory=args.signatory,
        signatory_title=args.signatory_title,
        cert_date=args.date or None,
    )

    print(f"Certificate written: {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
