"""Generate and validate hashed 2FA session tokens stored on disk.

Migrated from ``authenticators/2fa_demo.py``.

HARDENING (Phase 3):
  - The original imported nothing for ``random`` (a bug) and used the
    non-cryptographic ``random`` module to mint tokens. Tokens are now
    generated with :mod:`secrets`.
  - Token hashing used MD5; it now uses SHA-256.
  - Token comparison now uses :func:`hmac.compare_digest` (constant time).

No secrets are stored in this module — session files hold only a salted
hash of the one-time token.
"""

import hashlib
import hmac
import json
import secrets
import time

_TOKEN_TTL_SECONDS = 10 * 60


def _hash_token(token, salt):
    """Return the hex SHA-256 digest of ``salt + token``."""
    return hashlib.sha256((salt + token).encode("utf-8")).hexdigest()


def generate_2fa_secret(username, session_id, method):
    """Generate a 6-digit token; store its salted hash in a ``.session`` file.

    Returns the plaintext token (to be delivered to the user out of band).
    The token itself is never written to disk.
    """
    token = str(secrets.randbelow(900000) + 100000)
    salt = secrets.token_hex(16)

    generated_timestamp = time.time()
    data = {
        "user": username,
        "salt": salt,
        "token_hash": _hash_token(token, salt),
        "generated": generated_timestamp,
        "expires": generated_timestamp + _TOKEN_TTL_SECONDS,
        "method": method,
    }

    filename = f"{username}.{session_id}.session"
    with open(filename, "w") as f:
        json.dump(data, f)
    return token


def validate_2fa_token(username, session_id, token):
    """Validate ``token`` against the stored session file; check expiry."""
    filename = f"{username}.{session_id}.session"
    with open(filename) as f:
        data = json.load(f)

    expected = data["token_hash"]
    actual = _hash_token(token, data["salt"])
    if not hmac.compare_digest(expected, actual):
        print("Invalid token.")
        return False
    if time.time() >= data["expires"]:
        print("Token has expired.")
        return False
    return True
