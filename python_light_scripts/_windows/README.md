# `_windows` — Windows-only, isolated

Code in this package targets Windows APIs and is kept out of the package's
public namespace and the default `pytest` collection.

| Item | Origin | Requires (runtime) | Import-safe off Windows? | Notes |
|------|--------|--------------------|--------------------------|-------|
| `registry_secret.py` | `windows/store_pass_in_registry.py` | `winreg` | No (imports `winreg`) | Stores a value in `HKCU\Software\...`. The registry is **not** a secure secret store — see `SECURITY.md`. |
| `outlook/` (subpackage) | `OutlookMailMessageProcessor/*` | `win32com` + Outlook | **Yes** | Extracts attachments from `.msg` files. The Outlook COM import is lazy, so the package imports and unit-tests on any OS. See `outlook/README.md`. |

`registry_secret.py` must only be run on Windows.

The `outlook/` subpackage is a safer, modular rebuild of the original
`OutlookMailMessageProcessor/` scripts: only `iter_msg_attachments()` /
`process_msg_file()` touch Outlook (guarded + lazy import); filename
sanitization, dry-run, structured logging and safe archive extraction are
pure and fully tested without Outlook (see `tests/test_outlook_processor.py`).

Run anything that opens a real `.msg` only on Windows, in an environment you
control.
