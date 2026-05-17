"""Path-traversal-safe archive extraction — local to the Outlook tool.

This is a self-contained copy of the Zip-Slip-safe extraction logic, kept
local so the Outlook utility does not depend on any sibling script. (Each
script/folder in this repo is an independent mini-project.)

``zipfile``/``tarfile`` ``extractall`` are unsafe on untrusted input: a
crafted member name (``../../etc/passwd``, an absolute path, or a tar
symlink) can write outside the target directory. The helpers here validate
every member before extracting and refuse anything that would escape.

Pure and import-safe on every platform.
"""

from __future__ import annotations

import os
import tarfile
import zipfile
from pathlib import Path


class PathTraversalError(Exception):
    """Raised when an archive member would extract outside the target dir."""


def _is_within_directory(directory: Path, target: Path) -> bool:
    """Return True if ``target`` resolves to a path inside ``directory``."""
    directory = directory.resolve()
    target = target.resolve()
    try:
        target.relative_to(directory)
        return True
    except ValueError:
        return False


def _check_member(dest: Path, member_name: str) -> Path:
    """Raise :class:`PathTraversalError` if ``member_name`` escapes ``dest``."""
    if os.path.isabs(member_name) or os.path.splitdrive(member_name)[0]:
        raise PathTraversalError(f"Absolute path in archive member: {member_name!r}")
    target = dest / member_name
    if not _is_within_directory(dest, target):
        raise PathTraversalError(f"Archive member escapes target dir: {member_name!r}")
    return target


def safe_extract_zip(zip_path: str | Path, dest: str | Path) -> Path:
    """Extract a ``.zip`` to ``dest``, rejecting any path-traversal member."""
    dest = Path(dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            _check_member(dest, name)
        # Safe: every member name was validated against `dest` above.
        zf.extractall(path=dest)  # noqa: S202
    return dest


def safe_extract_tar(tar_path: str | Path, dest: str | Path) -> Path:
    """Extract a ``.tar`` to ``dest``, rejecting traversal members and links."""
    dest = Path(dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "r") as tar:
        for member in tar.getmembers():
            _check_member(dest, member.name)
            if member.issym() or member.islnk():
                _check_member(dest, member.linkname)
        # Safe: every member name and link target was validated above.
        try:
            tar.extractall(path=dest, filter="data")  # noqa: S202
        except TypeError:
            tar.extractall(path=dest)  # noqa: S202
    return dest
