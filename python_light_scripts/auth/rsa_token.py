"""Sign a SHA-1 digest with an RSA private key (CTF helper).

Migrated from ``authenticators/rsa_try.py``. The original ran at module
scope with an invalid placeholder; the logic is wrapped in a function here.

NOTE: This was a CTF exercise. "Signing by encrypting with the private key"
is cryptographically unidiomatic; kept only for reference / reproducibility.
Supply your own key file — none is bundled.
"""

import base64
import hashlib


def make_token(ctf_data_hex, private_key_path):
    """Hash ``ctf_data_hex``, sign it with the RSA key, return a base32 token."""
    import rsa

    ctf_data_bytes = bytes.fromhex(ctf_data_hex)

    # SHA-1 is fixed by the original CTF challenge spec; not a security choice.
    hash_bytes = hashlib.sha1(ctf_data_bytes).digest()  # noqa: S324
    padded_hash_bytes = b"\x00" * (20 - len(hash_bytes)) + hash_bytes

    with open(private_key_path, mode="rb") as privatefile:
        keydata = privatefile.read()
    privkey = rsa.PrivateKey.load_pkcs1(keydata)

    token_bytes = rsa.pkcs1.encrypt(padded_hash_bytes, privkey)
    return base64.b32encode(token_bytes).decode("ascii")
