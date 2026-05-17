# Security

This repository is a collection of small utility scripts. It was put through
a security-hardening pass; this document records what was found, what was
fixed, and how to use the remaining sensitive tools safely.

## Reporting

This is a personal script collection, not a deployed service. If you spot a
problem, open an issue or contact the author.

## Hardening performed

### Secrets

No secrets are stored in this repository.

- The original `authenticators/googleauth.py`, `lastpass.py` and
  `2fa_test.demo.py` contained hardcoded placeholder keys, and
  `windows/store_pass_in_registry.py` contained a hardcoded password. All have
  been removed.
- `auth.totp` takes the TOTP secret as a function argument; the demo
  (`examples/totp_demo.py`) reads it from the `TOTP_SECRET` environment
  variable.
- `auth.sessions` never writes a token to disk — only a **salted SHA-256
  hash** of the one-time token. Token comparison is constant-time
  (`hmac.compare_digest`). The original used MD5 and the non-cryptographic
  `random` module.
- `_windows/registry_secret.py` takes the value to store as an argument and
  carries a warning that the Windows registry is **not** a secure secret
  store.

**Never commit** credential files (`private.pem`, Google OAuth
`credentials.json`, `*.session`). `.gitignore` excludes `*.session`.

### Command injection (`shell=True` / `os.system`)

All shell-string command execution has been replaced with argument-list
`subprocess` calls (no shell):

| Module | Before | After |
|--------|--------|-------|
| `acl.manager` | `subprocess.run(f"setfacl {entry} {path}", shell=True)` | argument-list `subprocess.run([...])`; ACL entries validated against a regex |
| `process.parallel` | `subprocess.Popen(cmd, shell=True)` | argument-list `Popen`; string commands are rejected with `TypeError` |
| `monitoring.holidays` | `os.system("source {profile}; {cmd}")` with `cmd` from `argv` | `bash -c` with the profile path and command passed as **separate argv entries**, so neither can inject shell syntax |

### Path traversal / Zip-Slip

`python_light_scripts/archives/safe_extract.py` provides
`safe_extract_zip` / `safe_extract_tar`, which validate every archive
member's resolved destination before extraction and raise
`PathTraversalError` on:

- relative escapes (`../../etc/passwd`),
- absolute paths,
- (for tar) symlink/hardlink members whose targets escape the destination.

The `_windows/outlook/` subpackage applies the same protection through its
own local `safe_archive.py` (each script/folder in this repo is an
independent mini-project, so the logic is duplicated rather than shared). It
also sanitizes every attachment file name (rejecting path traversal, absolute
paths, control characters and Windows reserved device names) before writing.

### XML external entities (XXE)

`xmltools.cofc_reader.read_xml_file` parses with an lxml parser configured
with `resolve_entities=False` and `no_network=True`, so a malicious
`<!ENTITY>` cannot read local files or make network requests.

## Sensitive tools — use with care

These tools change system state. They carry warnings in their docstrings.

| Tool | Effect | Precautions |
|------|--------|-------------|
| `acl.manager` | Changes POSIX filesystem ACLs | Linux only; run only on directories you own; review `.acllog`/`.aclinfo` it writes |
| `_windows/registry_secret.py` | Writes to `HKEY_CURRENT_USER` | Registry is readable by same-user processes — do not treat as a vault |
| `_windows/outlook/` | Drives Outlook via COM, writes files | Run `process_msg_file()` only on Windows; file names are sanitized and archive extraction is Zip-Slip-safe; use `dry_run=True` to preview |
| `process.parallel` / `process.progress` | Spawn subprocesses | Pass argument lists, never user-controlled shell strings |
| `_network/google_drive_xls.py` | Outbound network + OAuth | Keep credentials out of the repo |

## Isolation

Platform- and credential-bound code lives in `python_light_scripts/_windows`
and `python_light_scripts/_network`. These packages are excluded from the
public namespace and from the default `pytest`/`ruff`/`mypy` runs, so the
rest of the cookbook stays offline, cross-platform, and testable.

## Tests

`tests/test_safe_extract.py` proves the unsafe cases fail safely: malicious
zip/tar archives are rejected with `PathTraversalError` and **no file is
written outside the target directory**. `tests/test_acl_manager.py`,
`tests/test_parallel.py` and `tests/test_sessions.py` cover input validation
and the secret-handling changes.
