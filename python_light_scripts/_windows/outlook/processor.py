"""Extract attachments from Outlook ``.msg`` files — safely and modularly.

The Outlook COM dependency is confined to :func:`iter_msg_attachments`, which
imports ``win32com`` lazily and is guarded against non-Windows hosts. Every
other part of this module — filename sanitization, destination resolution,
dry-run handling, archive extraction — is pure and unit-testable without
Outlook or Windows, via the :meth:`OutlookMsgProcessor.process_attachments`
seam.
"""

from __future__ import annotations

import gzip
import logging
import shutil
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path

from python_light_scripts._windows.outlook.filenames import sanitize_filename
from python_light_scripts._windows.outlook.guard import ensure_windows
from python_light_scripts._windows.outlook.logging_utils import get_structured_logger, log_event
from python_light_scripts._windows.outlook.safe_archive import (
    PathTraversalError,
    safe_extract_tar,
    safe_extract_zip,
)

# A "saver" writes one attachment's bytes to the absolute path it is given.
Saver = Callable[[str], None]


@dataclass
class AttachmentResult:
    """Outcome of processing a single attachment."""

    original_name: str
    safe_name: str
    destination: str | None = None
    saved: bool = False
    dry_run: bool = False
    extracted_to: str | None = None
    error: str | None = None
    warnings: list[str] = field(default_factory=list)


def _archive_kind(name: str) -> str | None:
    """Classify ``name`` as ``"zip"``, ``"tar"``, ``"gz"`` or ``None``."""
    low = name.lower()
    if low.endswith(".zip"):
        return "zip"
    if low.endswith((".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tbz2")):
        return "tar"
    if low.endswith(".gz"):
        return "gz"
    return None


class OutlookMsgProcessor:
    """Extract (and optionally unpack) attachments from Outlook ``.msg`` files.

    Args:
        output_dir: directory attachments are written into. Created if absent
            (unless ``dry_run`` is set).
        dry_run: when True, nothing is written or extracted; every action is
            logged and reported as it *would* have happened.
        extract_archives: when True, ``.zip``/``.tar*``/``.gz`` attachments are
            unpacked with path-traversal-safe helpers after being saved.
        logger: a structured logger; one is created if omitted.
    """

    def __init__(
        self,
        output_dir: str | Path,
        *,
        dry_run: bool = False,
        extract_archives: bool = True,
        logger: logging.Logger | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.dry_run = dry_run
        self.extract_archives = extract_archives
        self.logger = logger or get_structured_logger()

    # -- public, Outlook-free API (the unit-test seam) -----------------------

    def process_attachments(
        self, attachments: Iterable[tuple[str, Saver]]
    ) -> list[AttachmentResult]:
        """Process an iterable of ``(name, saver)`` pairs.

        This is the testable core: callers (including
        :meth:`process_msg_file`) supply the attachments, so tests can pass
        fakes and never need Outlook.

        Args:
            attachments: pairs of raw attachment name and a ``saver`` callable
                that writes the attachment's bytes to a given absolute path.

        Returns:
            One :class:`AttachmentResult` per attachment, in input order.
        """
        if not self.dry_run:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        results: list[AttachmentResult] = []
        for raw_name, saver in attachments:
            results.append(self._handle_one(raw_name, saver))

        log_event(
            self.logger,
            logging.INFO,
            "processing_complete",
            output_dir=str(self.output_dir),
            dry_run=self.dry_run,
            total=len(results),
            saved=sum(r.saved for r in results),
            errors=sum(r.error is not None for r in results),
        )
        return results

    # -- Windows/Outlook boundary -------------------------------------------

    def process_msg_file(self, msg_path: str | Path) -> list[AttachmentResult]:
        """Open ``msg_path`` via Outlook and process its attachments.

        Windows-only: raises :class:`~...guard.NotWindowsError` off Windows.
        """
        ensure_windows("Reading Outlook .msg files")
        log_event(self.logger, logging.INFO, "open_msg", msg_path=str(msg_path))
        return self.process_attachments(iter_msg_attachments(msg_path))

    # -- internals -----------------------------------------------------------

    def _handle_one(self, raw_name: str, saver: Saver) -> AttachmentResult:
        """Sanitize, save (unless dry-run) and optionally extract one attachment."""
        safe_name = sanitize_filename(raw_name)
        result = AttachmentResult(original_name=raw_name, safe_name=safe_name)

        if safe_name != raw_name:
            result.warnings.append("filename_sanitized")

        destination = (self.output_dir / safe_name).resolve()
        # Defence in depth: the sanitized name cannot contain separators, so
        # this should always hold — but verify before writing anything.
        if self.output_dir.resolve() not in destination.parents:
            result.error = "destination_escapes_output_dir"
            log_event(
                self.logger, logging.ERROR, "rejected_attachment",
                original_name=raw_name, reason=result.error,
            )
            return result

        result.destination = str(destination)

        if self.dry_run:
            result.dry_run = True
            log_event(
                self.logger, logging.INFO, "would_save_attachment",
                original_name=raw_name, safe_name=safe_name, destination=str(destination),
            )
            if self.extract_archives and _archive_kind(safe_name):
                log_event(
                    self.logger, logging.INFO, "would_extract_archive",
                    safe_name=safe_name,
                )
            return result

        try:
            saver(str(destination))
            result.saved = True
            log_event(
                self.logger, logging.INFO, "attachment_saved",
                original_name=raw_name, destination=str(destination),
            )
        except Exception as exc:  # noqa: BLE001 - record & continue
            result.error = f"save_failed: {exc}"
            log_event(
                self.logger, logging.ERROR, "attachment_save_failed",
                original_name=raw_name, error=str(exc),
            )
            return result

        if self.extract_archives and _archive_kind(safe_name):
            self._extract(destination, safe_name, result)

        return result

    def _extract(self, archive_path: Path, safe_name: str, result: AttachmentResult) -> None:
        """Unpack a saved archive attachment with path-traversal-safe helpers."""
        kind = _archive_kind(safe_name)
        try:
            if kind == "zip":
                dest = self.output_dir / f"{safe_name}__contents"
                safe_extract_zip(archive_path, dest)
            elif kind == "tar":
                dest = self.output_dir / f"{safe_name}__contents"
                safe_extract_tar(archive_path, dest)
            else:  # gz: single-member gzip
                out_name = sanitize_filename(safe_name[:-3] or "decompressed")
                dest = self.output_dir / out_name
                with gzip.open(archive_path, "rb") as f_in, open(dest, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
            result.extracted_to = str(dest)
            log_event(
                self.logger, logging.INFO, "archive_extracted",
                safe_name=safe_name, extracted_to=str(dest),
            )
        except PathTraversalError as exc:
            result.error = f"unsafe_archive: {exc}"
            result.warnings.append("archive_rejected_path_traversal")
            log_event(
                self.logger, logging.ERROR, "unsafe_archive_rejected",
                safe_name=safe_name, error=str(exc),
            )
        except Exception as exc:  # noqa: BLE001 - record & continue
            result.error = f"extract_failed: {exc}"
            log_event(
                self.logger, logging.ERROR, "archive_extract_failed",
                safe_name=safe_name, error=str(exc),
            )


def iter_msg_attachments(msg_path: str | Path) -> Iterator[tuple[str, Saver]]:
    """Yield ``(name, saver)`` pairs for each attachment in an Outlook ``.msg``.

    Windows-only. ``win32com`` is imported lazily so that the rest of this
    module stays import-safe (and unit-testable) on every platform.

    Raises:
        NotWindowsError: when called on a non-Windows host.
    """
    ensure_windows("Reading Outlook .msg files")
    import win32com.client  # noqa: PLC0415 - lazy, Windows-only import

    outlook = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
    message = outlook.OpenSharedItem(str(msg_path))
    try:
        for attachment in message.Attachments:
            name = attachment.FileName

            def _saver(dest: str, _attachment=attachment) -> None:
                _attachment.SaveAsFile(dest)

            yield name, _saver
    finally:
        message.Close(0)
