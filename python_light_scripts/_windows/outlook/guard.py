"""Windows-only runtime guard.

Importing this module is safe on every platform. Call :func:`ensure_windows`
at the boundary where Windows-specific APIs are about to be used (i.e. just
before touching the Outlook COM API), so that pure logic remains testable
off Windows.
"""

from __future__ import annotations

import sys

#: True only when running on Microsoft Windows.
IS_WINDOWS: bool = sys.platform == "win32"


class NotWindowsError(RuntimeError):
    """Raised when a Windows-only operation is attempted on another OS."""


def ensure_windows(feature: str = "This feature") -> None:
    """Raise :class:`NotWindowsError` unless running on Windows.

    Args:
        feature: short description used in the error message.
    """
    if not IS_WINDOWS:
        raise NotWindowsError(
            f"{feature} requires Microsoft Windows with Outlook installed "
            f"(current platform: {sys.platform!r})."
        )
