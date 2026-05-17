"""Tests for the Outlook ``.msg`` attachment processor.

These tests deliberately exercise everything *except* the Outlook COM layer,
so they require neither Outlook nor Windows. The COM boundary
(``iter_msg_attachments`` / ``process_msg_file``) is covered only by a
guard-behaviour check.

The module under test lives in the isolated ``_windows`` package; it is
import-safe on every platform because the COM import is lazy.
"""

import gzip
import io
import json
import logging
import zipfile
from pathlib import Path

import pytest

from python_light_scripts._windows.outlook import (
    IS_WINDOWS,
    NotWindowsError,
    OutlookMsgProcessor,
    sanitize_filename,
)
from python_light_scripts._windows.outlook.guard import ensure_windows
from python_light_scripts._windows.outlook.logging_utils import get_structured_logger
from python_light_scripts._windows.outlook.processor import iter_msg_attachments

# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------

def make_saver(content: bytes):
    """Return a saver callable that writes ``content`` to its destination."""
    def _saver(dest: str) -> None:
        Path(dest).write_bytes(content)
    return _saver


def zip_bytes(*members: tuple[str, str]) -> bytes:
    """Build an in-memory zip from ``(arcname, text)`` pairs."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        for arcname, text in members:
            zf.writestr(arcname, text)
    return buf.getvalue()


def gzip_bytes(content: bytes) -> bytes:
    """Build in-memory gzip data."""
    buf = io.BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        gz.write(content)
    return buf.getvalue()


@pytest.fixture
def quiet_logger() -> logging.Logger:
    """A logger that discards output (keeps test runs clean)."""
    logger = logging.getLogger(f"test.outlook.{id(object())}")
    logger.handlers.clear()
    logger.addHandler(logging.NullHandler())
    logger.propagate = False
    return logger


# --------------------------------------------------------------------------
# filename sanitization
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("report.pdf", "report.pdf"),
        ("../../etc/passwd", "passwd"),
        ("..\\..\\windows\\system32\\evil.dll", "evil.dll"),
        ("/absolute/path/file.txt", "file.txt"),
        ("sub/dir/name.txt", "name.txt"),
        ("..", "unnamed_attachment"),
        ("", "unnamed_attachment"),
        ("   ", "unnamed_attachment"),
        ("...", "unnamed_attachment"),
    ],
)
def test_sanitize_filename_neutralizes_paths(raw, expected):
    assert sanitize_filename(raw) == expected


def test_sanitize_filename_strips_illegal_and_control_chars():
    out = sanitize_filename('a<b>c:"d|e?f*g\x01h.txt')
    assert "/" not in out and "\\" not in out
    for bad in '<>:"|?*':
        assert bad not in out
    assert "\x01" not in out


def test_sanitize_filename_escapes_reserved_device_names():
    assert sanitize_filename("CON") == "_CON"
    assert sanitize_filename("nul.txt") == "_nul.txt"
    assert sanitize_filename("COM1.dat") == "_COM1.dat"


def test_sanitize_filename_caps_length_and_keeps_extension():
    out = sanitize_filename("x" * 500 + ".pdf", max_length=50)
    assert len(out) <= 50
    assert out.endswith(".pdf")


def test_sanitize_filename_result_has_no_separators():
    for raw in ["a/b", "a\\b", "../x", "./y", "p/q/r.txt"]:
        assert "/" not in sanitize_filename(raw)
        assert "\\" not in sanitize_filename(raw)


# --------------------------------------------------------------------------
# attachment processing (Outlook-free seam)
# --------------------------------------------------------------------------

def test_module_imports_without_outlook():
    # Reaching this point means importing the processor needed no win32com.
    assert OutlookMsgProcessor is not None


def test_benign_attachment_is_saved_with_sanitized_name(tmp_path, quiet_logger):
    proc = OutlookMsgProcessor(tmp_path / "out", logger=quiet_logger)
    [result] = proc.process_attachments([("report.pdf", make_saver(b"PDF"))])

    assert result.saved is True
    assert result.error is None
    assert Path(result.destination).read_bytes() == b"PDF"
    assert Path(result.destination).name == "report.pdf"


def test_path_traversal_attachment_stays_inside_output_dir(tmp_path, quiet_logger):
    out = tmp_path / "out"
    proc = OutlookMsgProcessor(out, logger=quiet_logger)
    [result] = proc.process_attachments(
        [("../../escaped.txt", make_saver(b"data"))]
    )

    assert result.saved is True
    assert result.safe_name == "escaped.txt"
    # The file landed inside the output dir, not two levels up.
    assert Path(result.destination).parent == out.resolve()
    assert not (tmp_path.parent / "escaped.txt").exists()
    assert "filename_sanitized" in result.warnings


def test_dry_run_writes_nothing(tmp_path, quiet_logger):
    out = tmp_path / "out"
    proc = OutlookMsgProcessor(out, dry_run=True, logger=quiet_logger)
    [result] = proc.process_attachments([("report.pdf", make_saver(b"PDF"))])

    assert result.dry_run is True
    assert result.saved is False
    assert not out.exists()  # output dir not even created


def test_saver_failure_is_recorded_and_does_not_abort_batch(tmp_path, quiet_logger):
    def failing_saver(_dest: str) -> None:
        raise OSError("disk full")

    proc = OutlookMsgProcessor(tmp_path / "out", logger=quiet_logger)
    results = proc.process_attachments(
        [("bad.bin", failing_saver), ("good.bin", make_saver(b"ok"))]
    )

    assert results[0].saved is False
    assert "save_failed" in results[0].error
    # The second attachment is still processed.
    assert results[1].saved is True


# --------------------------------------------------------------------------
# safe archive extraction
# --------------------------------------------------------------------------

def test_benign_zip_attachment_is_extracted(tmp_path, quiet_logger):
    proc = OutlookMsgProcessor(tmp_path / "out", logger=quiet_logger)
    payload = zip_bytes(("inside/hello.txt", "hi"))
    [result] = proc.process_attachments([("bundle.zip", make_saver(payload))])

    assert result.saved is True
    assert result.error is None
    extracted = Path(result.extracted_to) / "inside" / "hello.txt"
    assert extracted.read_text() == "hi"


def test_malicious_zip_attachment_is_rejected_safely(tmp_path, quiet_logger):
    out = tmp_path / "out"
    proc = OutlookMsgProcessor(out, logger=quiet_logger)
    payload = zip_bytes(("../escaped.txt", "pwned"))
    [result] = proc.process_attachments([("evil.zip", make_saver(payload))])

    # The archive was saved, but extraction was refused...
    assert result.saved is True
    assert result.error is not None
    assert "unsafe_archive" in result.error
    assert "archive_rejected_path_traversal" in result.warnings
    # ...and proof it failed safely: nothing escaped the output directory.
    assert not (tmp_path / "escaped.txt").exists()
    assert not (out.parent / "escaped.txt").exists()


def test_gzip_attachment_is_decompressed(tmp_path, quiet_logger):
    proc = OutlookMsgProcessor(tmp_path / "out", logger=quiet_logger)
    payload = gzip_bytes(b"decompressed-content")
    [result] = proc.process_attachments([("data.txt.gz", make_saver(payload))])

    assert result.extracted_to is not None
    assert Path(result.extracted_to).read_bytes() == b"decompressed-content"


def test_archive_extraction_can_be_disabled(tmp_path, quiet_logger):
    proc = OutlookMsgProcessor(
        tmp_path / "out", extract_archives=False, logger=quiet_logger
    )
    payload = zip_bytes(("inside/hello.txt", "hi"))
    [result] = proc.process_attachments([("bundle.zip", make_saver(payload))])

    assert result.saved is True
    assert result.extracted_to is None


# --------------------------------------------------------------------------
# structured logging
# --------------------------------------------------------------------------

def test_structured_logger_emits_json_lines(tmp_path):
    log_file = tmp_path / "run.jsonl"
    logger = get_structured_logger("test.outlook.jsonl", log_file=str(log_file))
    proc = OutlookMsgProcessor(tmp_path / "out", logger=logger)
    proc.process_attachments([("report.pdf", make_saver(b"PDF"))])

    for handler in logger.handlers:
        handler.flush()
    lines = [json.loads(ln) for ln in log_file.read_text().splitlines() if ln.strip()]

    assert lines, "expected at least one structured log line"
    events = {entry["event"] for entry in lines}
    assert "attachment_saved" in events
    assert "processing_complete" in events
    # Every record carries the structured fields the formatter guarantees.
    assert all({"time", "level", "event"} <= entry.keys() for entry in lines)


# --------------------------------------------------------------------------
# Windows/Outlook guard boundary
# --------------------------------------------------------------------------

@pytest.mark.skipif(IS_WINDOWS, reason="guard only raises off Windows")
def test_iter_msg_attachments_refuses_to_run_off_windows():
    with pytest.raises(NotWindowsError):
        next(iter_msg_attachments("anything.msg"))


@pytest.mark.skipif(IS_WINDOWS, reason="guard only raises off Windows")
def test_process_msg_file_refuses_to_run_off_windows(tmp_path, quiet_logger):
    proc = OutlookMsgProcessor(tmp_path / "out", logger=quiet_logger)
    with pytest.raises(NotWindowsError):
        proc.process_msg_file("anything.msg")


def test_ensure_windows_message_mentions_the_feature():
    if IS_WINDOWS:
        ensure_windows("X")  # no-op on Windows
    else:
        with pytest.raises(NotWindowsError, match="Custom feature"):
            ensure_windows("Custom feature")
