"""Tests proving unsafe archive members are rejected safely.

These exercise the Zip-Slip / path-traversal protections in
``python_light_scripts.archives.safe_extract``. The key assertion in each
unsafe case is twofold: an exception is raised AND no file is created
outside the intended destination directory.
"""

import tarfile
import zipfile

import pytest

from python_light_scripts.archives import (
    PathTraversalError,
    is_within_directory,
    safe_extract_tar,
    safe_extract_zip,
)

# --- is_within_directory ----------------------------------------------------

def test_is_within_directory_accepts_child(tmp_path):
    assert is_within_directory(tmp_path, tmp_path / "sub" / "file.txt")


def test_is_within_directory_rejects_escape(tmp_path):
    assert not is_within_directory(tmp_path, tmp_path / ".." / "file.txt")


# --- safe zip extraction ----------------------------------------------------

def test_safe_zip_extracts_benign_archive(tmp_path):
    archive = tmp_path / "good.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("inside/hello.txt", "hi")

    dest = tmp_path / "out"
    safe_extract_zip(archive, dest)
    assert (dest / "inside" / "hello.txt").read_text() == "hi"


def test_safe_zip_rejects_parent_traversal(tmp_path):
    archive = tmp_path / "evil.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../escaped.txt", "pwned")

    dest = tmp_path / "out"
    with pytest.raises(PathTraversalError):
        safe_extract_zip(archive, dest)

    # Proof it failed *safely*: nothing landed outside the destination.
    assert not (tmp_path / "escaped.txt").exists()


def test_safe_zip_rejects_absolute_path(tmp_path):
    archive = tmp_path / "abs.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("/tmp/pl_scripts_abs_probe.txt", "pwned")  # noqa: S108

    with pytest.raises(PathTraversalError):
        safe_extract_zip(archive, tmp_path / "out")


# --- safe tar extraction ----------------------------------------------------

def test_safe_tar_extracts_benign_archive(tmp_path):
    payload = tmp_path / "hello.txt"
    payload.write_text("hi")
    archive = tmp_path / "good.tar"
    with tarfile.open(archive, "w") as tar:
        tar.add(payload, arcname="inside/hello.txt")

    dest = tmp_path / "out"
    safe_extract_tar(archive, dest)
    assert (dest / "inside" / "hello.txt").read_text() == "hi"


def test_safe_tar_rejects_parent_traversal(tmp_path):
    payload = tmp_path / "hello.txt"
    payload.write_text("pwned")
    archive = tmp_path / "evil.tar"
    with tarfile.open(archive, "w") as tar:
        tar.add(payload, arcname="../escaped.txt")

    with pytest.raises(PathTraversalError):
        safe_extract_tar(archive, tmp_path / "out")
    assert not (tmp_path / "escaped.txt").exists()


def test_safe_tar_rejects_escaping_symlink(tmp_path):
    archive = tmp_path / "link.tar"
    info = tarfile.TarInfo(name="link")
    info.type = tarfile.SYMTYPE
    info.linkname = "../../etc/passwd"
    with tarfile.open(archive, "w") as tar:
        tar.addfile(info)

    with pytest.raises(PathTraversalError):
        safe_extract_tar(archive, tmp_path / "out")
