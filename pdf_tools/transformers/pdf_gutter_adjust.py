"""
transformers/pdf_gutter_adjust.py — ADVANCED: adjust a PDF's inside/gutter margin.

Shifts page *content* outward so an existing document gains a larger binding
(inside / gutter) margin, without re-imposing or re-flowing the pages. On a
double-sided book the gutter is the inner edge of each page:

    - Odd / right-hand (recto) pages  -> content moves RIGHT (toward outer edge)
    - Even / left-hand  (verso) pages -> content moves LEFT  (toward outer edge)

This is a pure page-content translation, NOT booklet imposition: page size and
PDF boxes are preserved, page order is unchanged, pages are never rasterized,
and the input file is never modified. Content already sitting closer to the
outer edge than the shift distance can be clipped — books normally keep enough
outer margin for the small (~0.25 in) shifts this tool is meant for.

Requirements:
    pip install pypdf

Examples:
    python pdf_gutter_adjust.py book.pdf book_adjusted.pdf --shift 0.25 --unit in
    python pdf_gutter_adjust.py book.pdf book_adjusted.pdf --inside-shift 18 --unit pt
    python pdf_gutter_adjust.py book.pdf book_adjusted.pdf --first-page-side left
    python pdf_gutter_adjust.py book.pdf book_adjusted.pdf --page-range 1-20,45,80-120
    python pdf_gutter_adjust.py --batch-dir ./pdfs --output-dir ./adjusted --recursive --glob "*.pdf"

A README-style usage section is included at the end of this file and in the
folder README.md.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pypdf
from pypdf import Transformation

# ---------------------------------------------------------------------------
# Default constants
# ---------------------------------------------------------------------------

DEFAULT_UNIT = "in"
DEFAULT_SHIFT_AMOUNT = 0.25
POINTS_PER_INCH = 72
POINTS_PER_MM = 72 / 25.4
DEFAULT_FIRST_PAGE_SIDE = "right"
DEFAULT_ODD_PAGE_DIRECTION = "right"
DEFAULT_EVEN_PAGE_DIRECTION = "left"
DEFAULT_OUTPUT_SUFFIX = "_gutter_adjusted"
DEFAULT_GLOB = "*.pdf"

SUPPORTED_UNITS = {"pt", "in", "mm"}
SUPPORTED_DIRECTIONS = {"left", "right", "none"}
SUPPORTED_PAGE_SIDES = {"left", "right"}

#: Signed multiplier applied to a shift magnitude for each named direction.
DIRECTION_SIGN: dict[str, float] = {"right": 1.0, "left": -1.0, "none": 0.0}

# Process exit codes.
EXIT_OK = 0
EXIT_ERROR = 1


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class PdfGutterAdjustError(Exception):
    """Raised for any user-facing failure (bad input, validation, write error)."""


# ---------------------------------------------------------------------------
# Options
# ---------------------------------------------------------------------------


@dataclass
class PdfGutterAdjustOptions:
    """
    Structured configuration for a gutter-adjustment run.

    A run is either *single* mode (``input_pdf`` set) or *batch* mode
    (``batch_dir`` set). The two are mutually exclusive.

    Attributes:
        input_pdf:            Source PDF for single mode (None in batch mode).
        output_pdf:           Explicit destination for single mode. If None it
                              is derived from the input name + ``suffix``.
        shift_amount:         Outward shift magnitude, expressed in ``unit``.
        unit:                 Measurement unit: ``pt``, ``in`` or ``mm``.
        first_page_side:      Binding side of page 1: ``right`` (recto) or
                              ``left`` (verso). Seeds the default directions.
        odd_page_direction:   Outward direction for odd pages.
        even_page_direction:  Outward direction for even pages.
        page_range:           Page selection string (e.g. ``"1-10,15,20-30"``)
                              limiting which pages are shifted; None = all.
        preserve_boxes:       Keep MediaBox/CropBox unchanged (no page growth).
        include_annotations:  Also translate annotation rectangles.
        dry_run:              Report intended changes without writing output.
        verbose:              Emit per-page diagnostics.
        overwrite:            Allow overwriting an existing output file.
        shift_x_odd/even:     Explicit horizontal shift overrides (in ``unit``).
        shift_y_odd/even:     Explicit vertical shift overrides (in ``unit``).
        skip_pages:           Page selection string of pages to skip.
        only_pages:           Page selection string restricting processing.
        backup:               Copy an existing output to ``*.bak`` before write.
        suffix:               Suffix used when deriving output file names.
        output_dir:           Directory for derived/batch output files.
        batch_dir:            Source directory for batch mode.
        recursive:            Recurse into sub-directories in batch mode.
        glob:                 Filename glob used to find PDFs in batch mode.
    """

    input_pdf: Path | None = None
    output_pdf: Path | None = None
    shift_amount: float = DEFAULT_SHIFT_AMOUNT
    unit: str = DEFAULT_UNIT
    first_page_side: str = DEFAULT_FIRST_PAGE_SIDE
    odd_page_direction: str = DEFAULT_ODD_PAGE_DIRECTION
    even_page_direction: str = DEFAULT_EVEN_PAGE_DIRECTION
    page_range: str | None = None
    preserve_boxes: bool = True
    include_annotations: bool = False
    dry_run: bool = False
    verbose: bool = False
    overwrite: bool = False

    # Advanced per-axis / per-parity overrides (values are in ``unit``).
    shift_x_odd: float | None = None
    shift_x_even: float | None = None
    shift_y_odd: float | None = None
    shift_y_even: float | None = None

    # Page filtering.
    skip_pages: str | None = None
    only_pages: str | None = None

    # Output handling.
    backup: bool = False
    suffix: str = DEFAULT_OUTPUT_SUFFIX
    output_dir: Path | None = None

    # Batch mode.
    batch_dir: Path | None = None
    recursive: bool = False
    glob: str = DEFAULT_GLOB


@dataclass
class PageShiftReport:
    """One page's outcome, collected for the dry-run / verbose report."""

    page_number: int
    processed: bool
    shift_x_pt: float = 0.0
    shift_y_pt: float = 0.0


@dataclass
class FileAdjustReport:
    """Per-file summary returned by :meth:`PdfGutterAdjuster._process_single_pdf`."""

    input_path: Path
    output_path: Path
    total_pages: int
    pages: list[PageShiftReport] = field(default_factory=list)
    written: bool = False

    @property
    def pages_shifted(self) -> int:
        return sum(1 for p in self.pages if p.processed)


# ---------------------------------------------------------------------------
# Adjuster
# ---------------------------------------------------------------------------


class PdfGutterAdjuster:
    """
    Apply gutter-margin adjustments to one PDF or a folder of PDFs.

    Business logic only — argument parsing lives in :func:`build_arg_parser`
    and :func:`options_from_args`. Construct with validated-or-not options;
    :meth:`run` validates before doing any work.
    """

    def __init__(self, options: PdfGutterAdjustOptions) -> None:
        self.options = options
        # Parsed page-selection sets, populated by _validate_options().
        self._page_range: set[int] | None = None
        self._skip_pages: set[int] | None = None
        self._only_pages: set[int] | None = None

    # -- public entry point ------------------------------------------------

    def run(self) -> list[FileAdjustReport]:
        """
        Validate options and process every target PDF.

        Returns:
            A list of per-file reports.

        Raises:
            PdfGutterAdjustError: On any validation or processing failure.
        """
        self._validate_options()
        if self.options.batch_dir is not None:
            return self._process_batch()
        return [self._process_single_pdf(*self._resolve_single_paths())]

    # -- validation --------------------------------------------------------

    def _validate_options(self) -> None:
        """Check every option up front so failures are reported before any I/O."""
        opts = self.options

        if opts.unit not in SUPPORTED_UNITS:
            raise PdfGutterAdjustError(
                f"Invalid unit {opts.unit!r}. Choose from: {sorted(SUPPORTED_UNITS)}."
            )
        if opts.first_page_side not in SUPPORTED_PAGE_SIDES:
            raise PdfGutterAdjustError(
                f"Invalid first page side {opts.first_page_side!r}. "
                f"Choose from: {sorted(SUPPORTED_PAGE_SIDES)}."
            )
        for label, direction in (
            ("odd-page-direction", opts.odd_page_direction),
            ("even-page-direction", opts.even_page_direction),
        ):
            if direction not in SUPPORTED_DIRECTIONS:
                raise PdfGutterAdjustError(
                    f"Invalid --{label} {direction!r}. "
                    f"Choose from: {sorted(SUPPORTED_DIRECTIONS)}."
                )
        if opts.shift_amount < 0:
            raise PdfGutterAdjustError(
                f"--shift must be zero or positive, got {opts.shift_amount}."
            )

        # Mode selection: exactly one of single / batch.
        if opts.batch_dir is not None and opts.input_pdf is not None:
            raise PdfGutterAdjustError(
                "Choose either single-file mode (INPUT) or batch mode (--batch-dir), not both."
            )
        if opts.batch_dir is None and opts.input_pdf is None:
            raise PdfGutterAdjustError(
                "Nothing to do: provide an INPUT pdf or use --batch-dir."
            )
        if opts.batch_dir is not None and opts.output_dir is None:
            raise PdfGutterAdjustError("Batch mode requires --output-dir.")

        # Parse page-selection strings once and cache the resulting sets.
        self._page_range = self._parse_page_selection(opts.page_range)
        self._skip_pages = self._parse_page_selection(opts.skip_pages)
        self._only_pages = self._parse_page_selection(opts.only_pages)

    # -- path resolution ---------------------------------------------------

    def _resolve_single_paths(self) -> tuple[Path, Path]:
        """Return the (input, output) paths for single-file mode."""
        opts = self.options
        assert opts.input_pdf is not None  # guaranteed by _validate_options
        input_path = opts.input_pdf
        if opts.output_pdf is not None:
            return input_path, opts.output_pdf
        return input_path, self._derive_output_path(input_path, opts.output_dir)

    def _derive_output_path(self, input_path: Path, out_dir: Path | None) -> Path:
        """Build an output path from an input name, the suffix and an output dir."""
        suffix = self.options.suffix or DEFAULT_OUTPUT_SUFFIX
        filename = f"{input_path.stem}{suffix}.pdf"
        target_dir = out_dir if out_dir is not None else input_path.parent
        return target_dir / filename

    # -- batch mode --------------------------------------------------------

    def _process_batch(self) -> list[FileAdjustReport]:
        """Find and process every PDF under ``batch_dir``."""
        opts = self.options
        assert opts.batch_dir is not None and opts.output_dir is not None

        if not opts.batch_dir.is_dir():
            raise PdfGutterAdjustError(f"Batch folder not found: {opts.batch_dir}")

        finder = opts.batch_dir.rglob if opts.recursive else opts.batch_dir.glob
        pdf_files = sorted(p for p in finder(opts.glob) if p.is_file())
        if not pdf_files:
            raise PdfGutterAdjustError(
                f"No files matching {opts.glob!r} found in {opts.batch_dir}."
            )

        reports: list[FileAdjustReport] = []
        for pdf_path in pdf_files:
            relative = pdf_path.relative_to(opts.batch_dir)
            out_path = self._derive_output_path(
                pdf_path, opts.output_dir / relative.parent
            )
            reports.append(self._process_single_pdf(pdf_path, out_path))
        return reports

    # -- single file -------------------------------------------------------

    def _process_single_pdf(
        self, input_path: Path, output_path: Path
    ) -> FileAdjustReport:
        """Load, shift and write one PDF; honours dry-run and overwrite rules."""
        self._check_input_readable(input_path)
        if input_path.resolve() == output_path.resolve():
            raise PdfGutterAdjustError(
                f"Output must differ from input: {input_path}"
            )
        if output_path.exists() and not self.options.overwrite:
            raise PdfGutterAdjustError(
                f"Output already exists: {output_path}. Pass --overwrite to replace it."
            )

        try:
            reader = pypdf.PdfReader(str(input_path))
        except Exception as exc:  # pypdf raises a variety of types on bad input
            raise PdfGutterAdjustError(
                f"Could not read PDF (corrupt or unsupported?): {input_path} — {exc}"
            ) from exc

        total_pages = len(reader.pages)
        report = FileAdjustReport(
            input_path=input_path, output_path=output_path, total_pages=total_pages
        )

        writer = pypdf.PdfWriter()
        writer.append(reader)
        if reader.metadata:  # preserve document metadata where present
            writer.add_metadata(reader.metadata)

        for index, page in enumerate(writer.pages):
            page_number = index + 1  # 1-based
            if not self._should_process_page(page_number):
                report.pages.append(PageShiftReport(page_number, processed=False))
                continue
            shift_x, shift_y = self._get_page_shift(page_number)
            self._shift_page_content(page, shift_x, shift_y)
            report.pages.append(
                PageShiftReport(page_number, True, shift_x, shift_y)
            )
            if self.options.verbose:
                print(
                    f"  page {page_number}: shift ({shift_x:+.2f}, {shift_y:+.2f}) pt"
                )

        if self.options.dry_run:
            self._print_dry_run(report)
            return report

        self._write_output(writer, output_path)
        report.written = True
        print(
            f"Adjusted {input_path.name} → {output_path}  "
            f"({report.pages_shifted}/{total_pages} pages shifted)"
        )
        return report

    @staticmethod
    def _check_input_readable(input_path: Path) -> None:
        """Raise a friendly error if the input is missing or clearly not a PDF."""
        if not input_path.exists():
            raise PdfGutterAdjustError(f"Input file does not exist: {input_path}")
        if not input_path.is_file():
            raise PdfGutterAdjustError(f"Input path is not a file: {input_path}")
        if input_path.suffix.lower() != ".pdf":
            raise PdfGutterAdjustError(
                f"Input does not look like a PDF (expected .pdf): {input_path}"
            )

    def _write_output(self, writer: pypdf.PdfWriter, output_path: Path) -> None:
        """Write the writer to disk, taking a backup first if requested."""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            if self.options.backup and output_path.exists():
                backup_path = output_path.with_suffix(output_path.suffix + ".bak")
                shutil.copy2(output_path, backup_path)
                if self.options.verbose:
                    print(f"  backup written: {backup_path}")
            with open(output_path, "wb") as handle:
                writer.write(handle)
        except PermissionError as exc:
            raise PdfGutterAdjustError(
                f"No permission to write output: {output_path} — {exc}"
            ) from exc
        except OSError as exc:
            raise PdfGutterAdjustError(
                f"Failed to write output: {output_path} — {exc}"
            ) from exc

    # -- per-page geometry -------------------------------------------------

    def _get_page_shift(self, page_number: int) -> tuple[float, float]:
        """
        Return the ``(shift_x, shift_y)`` translation in points for a 1-based page.

        Explicit per-axis overrides (``shift_x_odd`` etc.) win over the direction
        derived from ``first_page_side`` / ``odd|even_page_direction``.
        """
        opts = self.options
        is_odd = page_number % 2 == 1
        base_pt = self._convert_to_points(opts.shift_amount, opts.unit)

        if is_odd:
            direction = opts.odd_page_direction
            override_x, override_y = opts.shift_x_odd, opts.shift_y_odd
        else:
            direction = opts.even_page_direction
            override_x, override_y = opts.shift_x_even, opts.shift_y_even

        if override_x is not None:
            shift_x = self._convert_to_points(override_x, opts.unit)
        else:
            shift_x = DIRECTION_SIGN[direction] * base_pt

        shift_y = (
            self._convert_to_points(override_y, opts.unit)
            if override_y is not None
            else 0.0
        )
        return shift_x, shift_y

    @staticmethod
    def _convert_to_points(value: float, unit: str) -> float:
        """Convert a measurement in ``unit`` to PDF points."""
        if unit == "pt":
            return value
        if unit == "in":
            return value * POINTS_PER_INCH
        if unit == "mm":
            return value * POINTS_PER_MM
        raise PdfGutterAdjustError(f"Invalid unit {unit!r}.")

    def _shift_page_content(
        self, page: pypdf.PageObject, shift_x: float, shift_y: float
    ) -> None:
        """Translate one page's content (and optionally its annotations)."""
        if shift_x == 0.0 and shift_y == 0.0:
            return
        transformation = Transformation().translate(shift_x, shift_y)
        # expand=False keeps MediaBox/CropBox fixed (preserve_boxes behaviour).
        page.add_transformation(
            transformation, expand=not self.options.preserve_boxes
        )
        if self.options.include_annotations:
            self._shift_annotations(page, shift_x, shift_y)

    @staticmethod
    def _shift_annotations(
        page: pypdf.PageObject, shift_x: float, shift_y: float
    ) -> None:
        """Best-effort translation of annotation rectangles by the same offset."""
        annots = page.get("/Annots")
        if not annots:
            return
        for annotation in annots:  # type: ignore[union-attr]
            try:
                obj = annotation.get_object()
                rect = obj.get("/Rect")
                if rect and len(rect) == 4:
                    x1, y1, x2, y2 = (float(v) for v in rect)
                    obj[pypdf.generic.NameObject("/Rect")] = pypdf.generic.ArrayObject(
                        pypdf.generic.FloatObject(v)
                        for v in (x1 + shift_x, y1 + shift_y, x2 + shift_x, y2 + shift_y)
                    )
            except Exception:  # noqa: BLE001 — annotations are best-effort only
                continue

    # -- page selection ----------------------------------------------------

    def _should_process_page(self, page_number: int) -> bool:
        """Return True if a 1-based page passes the range / skip / only filters."""
        if self._only_pages is not None and page_number not in self._only_pages:
            return False
        if self._skip_pages is not None and page_number in self._skip_pages:
            return False
        if self._page_range is not None and page_number not in self._page_range:
            return False
        return True

    @staticmethod
    def _parse_page_selection(value: str | None) -> set[int] | None:
        """
        Parse a page-selection string like ``"1-10,15,20-30"`` into a set of ints.

        Args:
            value: Comma-separated page numbers and ``start-end`` ranges, or None.

        Returns:
            A set of 1-based page numbers, or None if ``value`` is None/empty.

        Raises:
            PdfGutterAdjustError: If the string is malformed.
        """
        if value is None:
            return None
        value = value.strip()
        if not value:
            return None

        pages: set[int] = set()
        for token in value.split(","):
            token = token.strip()
            if not token:
                continue
            if "-" in token:
                start_str, _, end_str = token.partition("-")
                try:
                    start, end = int(start_str), int(end_str)
                except ValueError:
                    raise PdfGutterAdjustError(
                        f"Invalid page range token {token!r} in {value!r}."
                    ) from None
                if start < 1 or end < start:
                    raise PdfGutterAdjustError(
                        f"Invalid page range {token!r}: need 1<=start<=end."
                    )
                pages.update(range(start, end + 1))
            else:
                try:
                    page = int(token)
                except ValueError:
                    raise PdfGutterAdjustError(
                        f"Invalid page token {token!r} in {value!r}."
                    ) from None
                if page < 1:
                    raise PdfGutterAdjustError(
                        f"Page numbers are 1-based; got {page} in {value!r}."
                    )
                pages.add(page)
        return pages or None

    # -- reporting ---------------------------------------------------------

    @staticmethod
    def _print_dry_run(report: FileAdjustReport) -> None:
        """Print a dry-run preview for one file without writing anything."""
        print(f"[dry-run] {report.input_path} → {report.output_path}")
        print(f"[dry-run]   {report.total_pages} page(s) total")
        for page in report.pages:
            if page.processed:
                print(
                    f"[dry-run]   page {page.page_number}: "
                    f"shift ({page.shift_x_pt:+.2f}, {page.shift_y_pt:+.2f}) pt"
                )
            else:
                print(f"[dry-run]   page {page.page_number}: skipped")
        print(
            f"[dry-run]   would shift {report.pages_shifted}/{report.total_pages} "
            f"page(s); no file written"
        )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_arg_parser() -> argparse.ArgumentParser:
    """Construct the argparse parser for the command-line interface."""
    parser = argparse.ArgumentParser(
        prog="pdf_gutter_adjust.py",
        description="Adjust a PDF's inside/gutter margin by shifting page content outward.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument("input", nargs="?", metavar="INPUT", help="Source PDF file")
    parser.add_argument(
        "output", nargs="?", metavar="OUTPUT", help="Destination PDF file"
    )

    parser.add_argument(
        "--shift",
        "--inside-shift",
        "--gutter-shift",
        "--margin-delta",
        dest="shift",
        type=float,
        default=None,
        metavar="AMOUNT",
        help=f"Outward shift magnitude in --unit (default: {DEFAULT_SHIFT_AMOUNT})",
    )
    parser.add_argument(
        "--unit",
        choices=sorted(SUPPORTED_UNITS),
        default=DEFAULT_UNIT,
        help=f"Unit for shift values (default: {DEFAULT_UNIT})",
    )
    parser.add_argument(
        "--first-page-side",
        choices=sorted(SUPPORTED_PAGE_SIDES),
        default=DEFAULT_FIRST_PAGE_SIDE,
        help=f"Binding side of page 1 (default: {DEFAULT_FIRST_PAGE_SIDE})",
    )
    parser.add_argument(
        "--odd-page-direction",
        choices=sorted(SUPPORTED_DIRECTIONS),
        default=None,
        help="Outward direction for odd pages (default: derived from --first-page-side)",
    )
    parser.add_argument(
        "--even-page-direction",
        choices=sorted(SUPPORTED_DIRECTIONS),
        default=None,
        help="Outward direction for even pages (default: derived from --first-page-side)",
    )

    parser.add_argument(
        "--page-range", metavar="SPEC", help="Pages to shift, e.g. 1-10,15,20-30"
    )
    parser.add_argument(
        "--skip-pages", metavar="SPEC", help="Pages to leave unshifted, e.g. 1-4,9"
    )
    parser.add_argument(
        "--only-pages", metavar="SPEC", help="Restrict processing to these pages"
    )

    parser.add_argument(
        "--preserve-boxes",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Keep page size / PDF boxes unchanged (default: enabled)",
    )
    parser.add_argument(
        "--include-annotations",
        action="store_true",
        help="Also translate annotation rectangles",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without writing output"
    )
    parser.add_argument(
        "--overwrite", action="store_true", help="Allow overwriting existing output"
    )
    parser.add_argument(
        "--backup",
        action="store_true",
        help="Copy an existing output to *.bak before overwriting",
    )
    parser.add_argument("--verbose", action="store_true", help="Print per-page detail")

    # Advanced explicit per-axis / per-parity overrides.
    parser.add_argument("--shift-x-odd", type=float, help="Explicit X shift for odd pages")
    parser.add_argument("--shift-x-even", type=float, help="Explicit X shift for even pages")
    parser.add_argument("--shift-y-odd", type=float, help="Explicit Y shift for odd pages")
    parser.add_argument("--shift-y-even", type=float, help="Explicit Y shift for even pages")

    # Output handling / batch mode.
    parser.add_argument(
        "--suffix",
        default=DEFAULT_OUTPUT_SUFFIX,
        help=f"Suffix for derived output names (default: {DEFAULT_OUTPUT_SUFFIX})",
    )
    parser.add_argument("--output-dir", metavar="DIR", help="Directory for output files")
    parser.add_argument("--batch-dir", metavar="DIR", help="Process every PDF in this folder")
    parser.add_argument(
        "--recursive", action="store_true", help="Recurse into sub-folders in batch mode"
    )
    parser.add_argument(
        "--glob",
        default=DEFAULT_GLOB,
        help=f"Filename glob for batch mode (default: {DEFAULT_GLOB})",
    )
    return parser


def options_from_args(args: argparse.Namespace) -> PdfGutterAdjustOptions:
    """
    Translate parsed CLI arguments into a :class:`PdfGutterAdjustOptions`.

    Resolves odd/even directions from ``--first-page-side`` when the user did
    not pass them explicitly.
    """
    if args.first_page_side == "right":
        default_odd, default_even = "right", "left"
    else:
        default_odd, default_even = "left", "right"

    return PdfGutterAdjustOptions(
        input_pdf=Path(args.input) if args.input else None,
        output_pdf=Path(args.output) if args.output else None,
        shift_amount=args.shift if args.shift is not None else DEFAULT_SHIFT_AMOUNT,
        unit=args.unit,
        first_page_side=args.first_page_side,
        odd_page_direction=args.odd_page_direction or default_odd,
        even_page_direction=args.even_page_direction or default_even,
        page_range=args.page_range,
        preserve_boxes=args.preserve_boxes,
        include_annotations=args.include_annotations,
        dry_run=args.dry_run,
        verbose=args.verbose,
        overwrite=args.overwrite,
        shift_x_odd=args.shift_x_odd,
        shift_x_even=args.shift_x_even,
        shift_y_odd=args.shift_y_odd,
        shift_y_even=args.shift_y_even,
        skip_pages=args.skip_pages,
        only_pages=args.only_pages,
        backup=args.backup,
        suffix=args.suffix,
        output_dir=Path(args.output_dir) if args.output_dir else None,
        batch_dir=Path(args.batch_dir) if args.batch_dir else None,
        recursive=args.recursive,
        glob=args.glob,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point. Returns a process exit code."""
    args = build_arg_parser().parse_args(argv)
    try:
        options = options_from_args(args)
        reports = PdfGutterAdjuster(options).run()
    except PdfGutterAdjustError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return EXIT_ERROR
    except KeyboardInterrupt:  # pragma: no cover
        print("Interrupted.", file=sys.stderr)
        return EXIT_ERROR

    written = sum(1 for r in reports if r.written)
    if options.dry_run:
        print(f"Dry-run complete: previewed {len(reports)} file(s).")
    else:
        print(f"Done: wrote {written} file(s).")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())


# ===========================================================================
# README — usage
# ===========================================================================
#
# pdf_gutter_adjust.py
# --------------------
# Adjust the inside/gutter margin of an existing PDF by translating page
# content outward. Right-hand (odd) pages move toward the right edge and
# left-hand (even) pages move toward the left edge, so the binding margin
# grows. Page size, PDF boxes and metadata are preserved; pages are never
# rasterized.
#
# Install:
#     pip install pypdf
#
# Single file:
#     python pdf_gutter_adjust.py book.pdf book_adjusted.pdf --shift 0.25 --unit in
#     python pdf_gutter_adjust.py book.pdf book_adjusted.pdf --inside-shift 18 --unit pt
#     python pdf_gutter_adjust.py book.pdf book_adjusted.pdf --first-page-side left
#     python pdf_gutter_adjust.py book.pdf out.pdf --page-range 1-20,45,80-120
#
# Derived output name (uses --suffix, default "_gutter_adjusted"):
#     python pdf_gutter_adjust.py book.pdf --shift 0.25
#
# Batch folder:
#     python pdf_gutter_adjust.py --batch-dir ./pdfs --output-dir ./adjusted \
#         --recursive --glob "*.pdf" --shift 0.25
#
# Preview only (no file written):
#     python pdf_gutter_adjust.py book.pdf out.pdf --shift 0.25 --dry-run
#
# Exit codes: 0 = success, 1 = error, 2 = bad command-line arguments.
