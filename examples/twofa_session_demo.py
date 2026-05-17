"""Demo: generate and validate a 2FA session token."""

from python_light_scripts.auth import sessions

if __name__ == "__main__":
    token = sessions.generate_2fa_secret("alice", "sess1", "email")
    print(f"Generated token: {token}")
    print("Valid:", sessions.validate_2fa_token("alice", "sess1", token))
    print("Wrong token valid:", sessions.validate_2fa_token("alice", "sess1", "000000"))
