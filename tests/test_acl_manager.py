"""Tests for ACL-entry validation and injection rejection.

These do not require ``setfacl`` — they cover the input validation added
during the security-hardening pass.
"""

import pytest

from python_light_scripts.acl.manager import AclError, apply_acl_change, validate_acl_entry


@pytest.mark.parametrize("entry", ["u:alice:rw", "g:devs:rwx", "u:bob", "m::rx", "o::r"])
def test_valid_acl_entries_accepted(entry):
    assert validate_acl_entry(entry) == entry


@pytest.mark.parametrize(
    "entry",
    [
        "u:alice:rw; rm -rf /",      # command-injection attempt
        "u:alice:rw && reboot",
        "$(touch /tmp/pwned)",
        "u:alice:rw\nmalicious",
        "notanentry",
        "",
    ],
)
def test_malicious_or_malformed_acl_entries_rejected(entry):
    with pytest.raises(AclError):
        validate_acl_entry(entry)


def test_apply_acl_change_rejects_unknown_action(tmp_path):
    with pytest.raises(AclError):
        apply_acl_change(tmp_path, "u:alice:rw", action="destroy")


def test_apply_acl_change_validates_entry_before_running(tmp_path):
    # A malformed entry must fail during validation, before any setfacl call.
    with pytest.raises(AclError):
        apply_acl_change(tmp_path, "u:alice:rw; rm -rf /", action="add")
