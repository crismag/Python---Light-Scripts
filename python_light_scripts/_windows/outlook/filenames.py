"""Safe filename sanitization for untrusted attachment names.

Attachment file names inside a ``.msg`` are attacker-controlled. Writing them
to disk verbatim allows path traversal (``../../evil``), absolute-path
escapes, NUL/control-character tricks, and collisions with Windows reserved
device names (``CON``, ``NUL``, ``COM1`` ...).

:func:`sanitize_filename` reduces any input to a single, safe path component.
This module is pure and import-safe on every platform.
"""

from __future__ import annotations

import re

# Windows reserved device names (case-insensitive), with or without extension.
_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

# Characters illegal in a Windows path component, plus all control chars.
_ILLEGAL_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')

DEFAULT_NAME = "unnamed_attachment"
MAX_LENGTH = 200


def sanitize_filename(
    name: str,
    *,
    default: str = DEFAULT_NAME,
    max_length: int = MAX_LENGTH,
) -> str:
    """Reduce ``name`` to a single safe path component.

    Guarantees about the result:

    - contains no directory separators and no ``..`` traversal,
    - contains no control characters or characters illegal on Windows,
    - is not a Windows reserved device name,
    - is non-empty and no longer than ``max_length`` characters.

    Args:
        name: the raw, untrusted attachment file name.
        default: value returned when ``name`` reduces to nothing usable.
        max_length: maximum length of the returned name.

    Returns:
        A safe file name (a bare component, never a path).
    """
    if not isinstance(name, str):
        return default

    # Keep only the final path component, regardless of separator style.
    candidate = name.replace("\\", "/").split("/")[-1]

    # Drop illegal/control characters, then trim surrounding dots/spaces
    # (Windows silently strips trailing dots and spaces).
    candidate = _ILLEGAL_CHARS.sub("_", candidate).strip().strip(". ")

    if not candidate or set(candidate) <= {"."}:
        return default

    # Guard against reserved device names (compare the part before the dot).
    stem, dot, ext = candidate.partition(".")
    if stem.upper() in _RESERVED_NAMES:
        candidate = f"_{candidate}"

    # Enforce the length limit while preserving the extension where possible.
    if len(candidate) > max_length:
        root, dot, ext = candidate.rpartition(".")
        if dot and 0 < len(ext) < max_length - 1:
            candidate = root[: max_length - len(ext) - 1] + "." + ext
        else:
            candidate = candidate[:max_length]
        candidate = candidate.strip(". ") or default

    return candidate
