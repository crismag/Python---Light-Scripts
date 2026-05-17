# `_network` — network/credential-bound, isolated

These modules make outbound network calls and require credentials. They are
isolated so the rest of the cookbook stays fully offline and testable. They
are excluded from the default `pytest` run.

| Module | Origin | Requires | Notes |
|--------|--------|----------|-------|
| `google_drive_xls.py` | `Excel_File_To_JSON/demo.read_google_drive_xls.py` | `google-api-python-client`, `google-auth`, OAuth credentials | Reads an `.xlsx` from Google Drive/Sheets. Supply a credentials file path; none is bundled. |

Never commit credential files. See `SECURITY.md`.
