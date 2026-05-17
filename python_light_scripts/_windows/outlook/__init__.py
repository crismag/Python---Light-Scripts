"""ISOLATED / Windows-only: Outlook ``.msg`` attachment processing.

Rebuilt from the original ``OutlookMailMessageProcessor/`` scripts into a
small, modular utility.

Design — what is and is not Windows-bound:

- :mod:`~python_light_scripts._windows.outlook.filenames` and
  :mod:`~python_light_scripts._windows.outlook.logging_utils` are **pure** and
  import-safe on any platform.
- :class:`~python_light_scripts._windows.outlook.processor.OutlookMsgProcessor`
  is also import-safe and fully unit-testable: its attachment-handling logic
  is decoupled from Outlook via the ``process_attachments`` seam.
- Only :func:`~python_light_scripts._windows.outlook.processor.iter_msg_attachments`
  touches the Outlook COM API, imports ``win32com`` lazily, and is guarded so
  it raises on non-Windows hosts.

This means **unit tests never require Outlook or Windows**.

See ``python_light_scripts/_windows/outlook/README.md``.
"""

from python_light_scripts._windows.outlook.filenames import sanitize_filename
from python_light_scripts._windows.outlook.guard import IS_WINDOWS, NotWindowsError, ensure_windows
from python_light_scripts._windows.outlook.processor import (
    AttachmentResult,
    OutlookMsgProcessor,
)

__all__ = [
    "sanitize_filename",
    "IS_WINDOWS",
    "NotWindowsError",
    "ensure_windows",
    "AttachmentResult",
    "OutlookMsgProcessor",
]
