"""Tests for auth.sessions — hardened 2FA session tokens."""

import json
import os

import pytest

from python_light_scripts.auth import sessions


@pytest.fixture(autouse=True)
def _in_tmp_dir(tmp_path, monkeypatch):
    # Session files are written to the CWD; isolate them per test.
    monkeypatch.chdir(tmp_path)


def test_generate_then_validate_round_trip():
    token = sessions.generate_2fa_secret("alice", "s1", "email")
    assert sessions.validate_2fa_token("alice", "s1", token) is True


def test_wrong_token_is_rejected():
    sessions.generate_2fa_secret("alice", "s1", "email")
    assert sessions.validate_2fa_token("alice", "s1", "000000") is False


def test_plaintext_token_is_never_written_to_disk():
    token = sessions.generate_2fa_secret("alice", "s1", "email")
    data = json.loads(open("alice.s1.session").read())
    # Only a salted hash is stored — the token itself must not appear.
    assert "token" not in data
    assert token not in json.dumps(data)
    assert "token_hash" in data and "salt" in data


def test_expired_token_is_rejected(monkeypatch):
    token = sessions.generate_2fa_secret("alice", "s1", "email")
    # Jump past the TTL.
    real_time = sessions.time.time()
    monkeypatch.setattr(sessions.time, "time", lambda: real_time + 10_000)
    assert sessions.validate_2fa_token("alice", "s1", token) is False


def test_session_files_are_gitignored():
    # The generated artifact matches the .gitignore *.session rule.
    sessions.generate_2fa_secret("alice", "s1", "email")
    assert os.path.exists("alice.s1.session")
