# Repository Audit — Python---Light-Scripts

**Audited:** 2026-05-17
**Scope:** All 22 Python scripts in the repository, evaluated as a personal
utility/demo-script collection.

## Summary

This is a snippet library, not an application: small standalone scripts kept for
reuse. Quality is uneven. Recurring problems:

- **Missing imports / incomplete snippets** — several scripts cannot run as-is.
- **`shell=True` + string interpolation** — shell-injection risk in 4 scripts.
- **Hardcoded placeholder secrets** — not real keys, but a poor pattern.
- **No `if __name__ == "__main__"` guards** — some scripts run work on import.
- **Platform coupling** — `winreg` / `win32com` (Windows) and `getfacl`/`source`
  (Unix) are mixed into the same flat tree with no isolation.
- **No `pyproject.toml`, no dependency manifest, no tests harness.**

## Classification table

| Path | Purpose | Current quality | Risks | Action | Test strategy |
|------|---------|-----------------|-------|--------|---------------|
| `ACLCONFIG/aclcontrol.py` | — (1-byte empty file) | Empty stub | None | **delete** | n/a |
| `ACLCONFIG/acl_manager.py` | CLI to add/remove POSIX ACLs via `getfacl`/`setfacl` | Good: argparse, docstrings, typed | `subprocess.run(shell=True)` with f-string-interpolated path & ACL entry → shell injection; Linux-only | **refactor** | Unit-test arg parsing & command-building with `getfacl`/`setfacl` mocked; integration test gated on `which setfacl` |
| `authenticators/2fa_demo.py` | Generate/validate hashed 2FA session tokens to a file | Broken | Uses `random` without `import random` → `NameError`; MD5 for tokens (weak); no `secrets` module | **refactor** | After fixing imports: unit-test generate→validate round-trip and expiry, with `tmp_path` |
| `authenticators/2fa_test.demo.py` | Demo of 2FA token generation + delivery stub | Poor | Hardcoded secret `"mysecrettoken"`; hand-built JSON string (fragile); MD5 | **refactor** | Unit-test token determinism; assert session file is valid JSON |
| `authenticators/googleauth.py` | Print a TOTP code with `pyotp` | Trivial demo | Hardcoded `secret_key='MYSECRETKEY'` is not valid base32 → runtime error | **refactor** | Test a TOTP wrapper against RFC 6238 test vectors |
| `authenticators/lastpass.py` | Manual HMAC-SHA1 TOTP implementation | Educational | Hardcoded placeholder `'YourSecretKeyHere'` is invalid base32 → crash on run | **refactor** | Test against RFC 6238 vectors; compare to `pyotp` |
| `authenticators/rsa_try.py` | CTF: sign a SHA1 hash with an RSA private key | CTF script | `ctfData` placeholder is not valid hex → `bytes.fromhex` crash; needs `private.pem`; "encrypt with private key" misuses RSA | **archive** | Smoke test only with a generated throwaway keypair |
| `command_line_tqdm_progressbar_demo.py` | tqdm progress bar over a `subprocess` call | Broken excerpt | Missing imports (`os`, `sys`, `time`, `argparse`, `subprocess`); undefined `iprint`, `fatal_error`, `safe_open`; progress bar is faked (sleep loop) | **refactor** | Extract a self-contained progress helper, then unit-test it |
| `windows/store_pass_in_registry.py` | Store/read a password in the Windows registry | Demo | **Windows-only** (`winreg`); hardcoded password; stores plaintext credential in registry (insecure pattern) | **refactor** | Windows-gated test with `winreg` mocked; skip on non-Windows |
| `monitoring/holiday.py` | Run a command, warn if today is a holiday | Poor | `os.system("source ...; cmd")` — shell injection + `source` is a bash-ism; both branches do the same thing (logic bug); `~` not expanded; Unix-only | **refactor** | Unit-test the date→holiday lookup with a fixture holiday file |
| `multi_threaded/launcher.py` | Run shell commands concurrently, then post-process | Buggy | `subprocess.Popen(shell=True)`; single shared `Event` makes the final `event.wait()` loop return after the first completion (broken join logic) | **refactor** | Unit-test with fast commands (`true`); assert all complete before post-processing |
| `multi_threaded/test.py` | Calls `run_commands` | Broken | `run_commands` never imported; hardcoded absolute paths | **delete** (replace with example) | n/a |
| `Excel_File_To_JSON/cd_coord_to_json.py` | Read a "CD Coordinate" Excel sheet → JSON | Decent | Has `main()` but no `__main__` guard / CLI; domain-specific layout assumptions | **refactor** | Test parsing with a small fixture `.xlsx` |
| `Excel_File_To_JSON/critical_dimension_reader.py` | Read a "Critical Dimension" Excel sheet → JSON | Decent (largest, 204 lines) | No `__main__` guard / CLI; brittle positional sheet assumptions | **refactor** | Test with a fixture `.xlsx`; assert JSON shape |
| `Excel_File_To_JSON/demo.read_google_drive_xls.py` | Read an `.xlsx` from Google Drive/Sheets API | Demo | **Network + OAuth credentials required**; `'.'` in filename; `IndexError` if file not found | **archive** | No automated test (network); keep as documented example only |
| `geometries/dice_face_generator.py` | Render dice-face PNGs with Pillow | Works | Runs at import (no guard); writes PNGs to CWD; unused `import random` | **refactor** | Test that 6 images of expected size are produced in `tmp_path` |
| `geometries/location_calculator.py` | Rotate/mirror a point about a cell origin | **Good** — pure, typed-ish, no side effects | None significant (mirror-before-rotate ordering is intentional) | **keep** | Unit-test known rotations (0°/90°/180°) and mirroring |
| `geometries/test_location.py` | Ad-hoc check of `PointLocationCalculator` | Broken | Class never imported; constructor called without required `mirrored` arg | **refactor** into real test | Becomes a proper `pytest` test |
| `OutlookMailMessageProcessor/OutlookMailMsgAttachmentProcessor .py` | Extract attachments from an Outlook `.msg` | Broken/incomplete | **Filename contains a space**; class name has a trailing space; file truncated mid-statement (`parser`); **Windows + Outlook only**; `tarfile`/`zipfile` `extractall` → Zip-Slip path traversal | **refactor** | Windows-gated; test archive extraction logic with `win32com` mocked |
| `OutlookMailMessageProcessor/OutlookMailMsgPdfProcessor.py` | Orchestrate attachment + PDF processing | Broken | Imports module with a space in its name (won't import); `PdfFileMerger` used but never imported; constructor signature mismatch with callee classes | **refactor** | Windows-gated integration test with mocks |
| `OutlookMailMessageProcessor/OutlookMailMsgToPdfConverter.py` | Convert `.msg` to PDF, merge PDF attachments | Broken | `PyPDF2.PdfFileMerger/PdfFileReader` removed in `pypdf` ≥3; **Windows + Outlook only**; constructor arity differs from how the orchestrator calls it | **refactor** | Windows-gated; mock `win32com`/`comtypes`, use `pypdf` API |
| `xml_parsers/metro_coin_parsers.demo.altered.py` | Reformat a "CoFC" XML file via lxml/XPath | Good — well-structured | Unused `objectify` import; `lxml.etree.parse` resolves external entities → XXE risk on untrusted XML | **refactor** | Test transform end-to-end with a fixture XML in/out pair |

## Action tally

- **keep:** 1 — `geometries/location_calculator.py`
- **refactor:** 15
- **archive:** 2 — `rsa_try.py`, `demo.read_google_drive_xls.py` (network/credential-bound)
- **delete:** 2 — `ACLCONFIG/aclcontrol.py`, `multi_threaded/test.py`

## Cross-cutting recommendations

1. Add `pyproject.toml` with pinned dependencies (`pandas`, `lxml`, `pyotp`,
   `Pillow`, `tqdm`, `pypdf`, `openpyxl`) and `ruff` / `pytest` / `mypy` config.
2. Replace every `shell=True` + interpolation with list-form `subprocess` calls.
3. Replace MD5 token hashing with `secrets` + `hmac`/`hashlib.sha256`.
4. Remove hardcoded placeholder secrets; take them via argparse or `os.environ`.
5. Separate importable library code from runnable demos; guard all entry points
   with `if __name__ == "__main__"`.
6. Isolate Windows-only code (`winreg`, `win32com`) into a clearly marked package
   so the rest of the collection imports cleanly on Linux/macOS.
7. Harden XML/archive handling against XXE and Zip-Slip.
