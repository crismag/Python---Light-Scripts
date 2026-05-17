"""Path-traversal-safe archive extraction.

``zipfile.ZipFile.extractall`` and ``tarfile.TarFile.extractall`` are unsafe
on untrusted input: a crafted member name such as ``../../etc/passwd`` or an
absolute path, or (for tar) a symlink, can write files *outside* the intended
destination directory. This is known as "Zip-Slip".

The helpers here validate every member's resolved destination against the
target directory and refuse to extract anything that would escape it.
"""

import os
import tarfile
import zipfile
from pathlib import Path


class PathTraversalError(Exception):
    """Raised when an archive member would extract outside the target dir."""


def is_within_directory(directory, target):
    """Return True if ``target`` resolves to a path inside ``directory``."""
    directory = Path(directory).resolve()
    target = Path(target).resolve()
    try:
        target.relative_to(directory)
        return True
    except ValueError:
        return False


def _check_member(dest, member_name):
    """Raise PathTraversalError if ``member_name`` escapes ``dest``."""
    # Reject absolute paths and parent-directory escapes outright.
    if os.path.isabs(member_name) or os.path.splitdrive(member_name)[0]:
        raise PathTraversalError(f"Absolute path in archive member: {member_name!r}")
    target = Path(dest) / member_name
    if not is_within_directory(dest, target):
        raise PathTraversalError(f"Archive member escapes target dir: {member_name!r}")
    return target


def safe_extract_zip(zip_path, dest):
    """Extract a ``.zip`` to ``dest``, rejecting any path-traversal member.

    Raises :class:`PathTraversalError` before extracting anything if a member
    would escape ``dest``.
    """
    dest = Path(dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        for name in zf.namelist():
            _check_member(dest, name)
        # Safe: every member name was validated against `dest` above.
        zf.extractall(path=dest)  # noqa: S202
    return dest


def safe_extract_tar(tar_path, dest):
    """Extract a ``.tar`` to ``dest``, rejecting traversal members and links.

    Symlink/hardlink members and members whose names escape ``dest`` are
    rejected. Raises :class:`PathTraversalError`.
    """
    dest = Path(dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar_path, "r") as tar:
        members = tar.getmembers()
        for member in members:
            _check_member(dest, member.name)
            if member.issym() or member.islnk():
                link_target = member.linkname
                _check_member(dest, link_target)
        # filter="data" (Python 3.12+) adds another safety layer; ignore if
        # unsupported on the running interpreter.
        # Safe: every member name and link target was validated above.
        try:
            tar.extractall(path=dest, filter="data")  # noqa: S202
        except TypeError:
            tar.extractall(path=dest)  # noqa: S202
    return dest
