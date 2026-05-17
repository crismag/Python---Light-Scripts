"""Demo: generate a TOTP code.

The secret is read from the ``TOTP_SECRET`` environment variable so that no
secret is ever hardcoded. Example::

    TOTP_SECRET=JBSWY3DPEHPK3PXP python examples/totp_demo.py
"""

import os
import sys

from python_light_scripts.auth.totp import generate_totp

if __name__ == "__main__":
    secret = os.environ.get("TOTP_SECRET")
    if not secret:
        print("Set TOTP_SECRET (base32) in the environment first.", file=sys.stderr)
        sys.exit(1)
    print(generate_totp(secret))
