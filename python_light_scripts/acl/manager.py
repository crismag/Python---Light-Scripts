"""Manage POSIX ACL permissions on a directory via getfacl/setfacl.

Migrated from ``ACLCONFIG/acl_manager.py``. The CLI entry point lives in
``examples/acl_manager.py``.

WARNING: This tool changes filesystem permissions. It shells out to
``getfacl``/``setfacl`` (Linux). See ``SECURITY.md``.

HARDENING (Phase 3): the original built shell strings and ran them with
``subprocess.run(..., shell=True)``, allowing command injection through the
folder path or ACL entry. This version uses argument-list ``subprocess``
calls (no shell) and validates the ACL-entry syntax.
"""

import re
import subprocess
from datetime import datetime
from pathlib import Path

# An ACL entry is e.g. "u:alice:rw", "g:devs:rwx", or "u:bob" (for removal).
_ACL_ENTRY_RE = re.compile(r"^[ugmo]:[A-Za-z0-9._-]*(?::[rwxX-]+)?$")


class AclError(Exception):
    """Raised when an ACL command fails or an entry is malformed."""


def validate_acl_entry(acl_entry):
    """Validate an ACL entry string; raise :class:`AclError` if malformed."""
    if not _ACL_ENTRY_RE.match(acl_entry):
        raise AclError(f"Malformed ACL entry: {acl_entry!r}")
    return acl_entry


def _run(args):
    """Run a command given as an argument list (no shell); return stdout."""
    result = subprocess.run(args, capture_output=True, text=True)  # noqa: S603
    if result.returncode != 0:
        raise AclError(f"Command failed: {' '.join(args)}\n{result.stderr}")
    return result.stdout.strip()


def get_acl_info(path):
    """Retrieve the current ACL information for ``path``."""
    return _run(["getfacl", "-p", str(path)])


def save_current_acl_snapshot(path):
    """Save the current ACL to a ``.aclinfo`` file in the target directory."""
    (Path(path) / ".aclinfo").write_text(get_acl_info(path))


def log_acl_change(path, action, acl_entry):
    """Append a timestamped change record to ``.acllog`` in the directory."""
    acllog_path = Path(path) / ".acllog"
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] ACTION: {action.upper()} | ENTRY: {acl_entry}\n"
    with acllog_path.open("a") as f:
        f.write(log_entry)


def apply_acl_change(path, acl_entry, action, use_default=False, recursive=False):
    """Apply an ACL add/remove to ``path`` and record the change.

    ``action`` must be ``"add"`` or ``"remove"``. The ACL entry is validated
    before any command runs.
    """
    if action not in ("add", "remove"):
        raise AclError(f"Unknown action: {action!r}")
    validate_acl_entry(acl_entry)

    args = ["setfacl"]
    if recursive:
        args.append("-R")
    if use_default:
        args.append("-d")
    args.append("-m" if action == "add" else "-x")
    args += [acl_entry, str(path)]

    _run(args)
    log_acl_change(path, action, acl_entry)
    save_current_acl_snapshot(path)
