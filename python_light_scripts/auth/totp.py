"""Time-based one-time password (TOTP) helpers.

Migrated from ``authenticators/lastpass.py`` (manual HMAC implementation)
and ``authenticators/googleauth.py`` (pyotp wrapper).

No secret keys are stored in this module — every function takes the secret
as an argument. Callers should load secrets from the environment or a
secrets manager, never hardcode them. See ``SECURITY.md``.
"""

import base64
import hashlib
import hmac
import time


def generate_totp(secret_key, interval=30, digits=6, at_time=None):
    """Generate a TOTP code from a base32 ``secret_key``.

    Pure HMAC-SHA1 implementation (RFC 6238). ``at_time`` may be supplied as
    a Unix timestamp to make the result deterministic for testing.
    """
    key_bytes = base64.b32decode(secret_key)

    now = time.time() if at_time is None else at_time
    counter = int(now / interval)
    counter_bytes = counter.to_bytes(8, byteorder="big")

    # SHA-1 is mandated by the TOTP standard (RFC 6238); used inside HMAC.
    hmac_hash = hmac.new(key_bytes, counter_bytes, hashlib.sha1).digest()  # noqa: S324
    offset = hmac_hash[-1] & 0x0F
    code_bytes = hmac_hash[offset : offset + 4]
    code_int = int.from_bytes(code_bytes, byteorder="big") & 0x7FFFFFFF
    code = code_int % (10**digits)
    return str(code).zfill(digits)


def generate_totp_pyotp(secret_key):
    """Generate a TOTP code using the ``pyotp`` library, if installed."""
    import pyotp

    return pyotp.TOTP(secret_key).now()
