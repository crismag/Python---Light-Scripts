# Outlook `.msg` attachment processor

A safer, modular rebuild of the original `OutlookMailMessageProcessor/`
scripts. It extracts attachments from Outlook `.msg` files, sanitizes their
names, and optionally unpacks archive attachments — with a dry-run mode and
structured logging.

## Modules

| Module | Windows-only? | Purpose |
|--------|---------------|---------|
| `guard.py` | no (import-safe) | `IS_WINDOWS`, `ensure_windows()` runtime guard |
| `filenames.py` | no | `sanitize_filename()` — pure, traversal-safe |
| `logging_utils.py` | no | JSON-line structured logger |
| `safe_archive.py` | no | Zip-Slip-safe archive extraction (local copy — no sibling deps) |
| `processor.py` | **boundary only** | `OutlookMsgProcessor` (pure core) + `iter_msg_attachments()` (Outlook COM) |

This subpackage is **self-contained**: it depends only on the Python standard
library plus `win32com` (lazily, at runtime, on Windows). It does not import
any other script in this repository.

Only `iter_msg_attachments()` touches Outlook, and it imports `win32com`
lazily. Everything else imports and runs on any OS — which is why the unit
tests need neither Outlook nor Windows.

## Usage

### On Windows, against a real `.msg`

```python
from python_light_scripts._windows.outlook import OutlookMsgProcessor

processor = OutlookMsgProcessor("out/attachments", extract_archives=True)
results = processor.process_msg_file(r"C:\mail\example.msg")

for r in results:
    print(r.original_name, "->", r.safe_name, "saved" if r.saved else r.error)
```

### Dry-run (preview without writing anything)

```python
processor = OutlookMsgProcessor("out/attachments", dry_run=True)
results = processor.process_msg_file(r"C:\mail\example.msg")
# No files created; each result has dry_run=True and a logged "would_save" event.
```

### Structured logging to a file

```python
from python_light_scripts._windows.outlook.logging_utils import get_structured_logger

logger = get_structured_logger("outlook", log_file="out/run.jsonl")
processor = OutlookMsgProcessor("out/attachments", logger=logger)
```

Each line of the log is a JSON object, e.g.:

```json
{"event": "attachment_saved", "level": "INFO", "original_name": "report.pdf", ...}
```

### Off Windows / testing

`process_attachments()` is the Outlook-free seam. Supply `(name, saver)`
pairs directly — a `saver` is any callable that writes the attachment's bytes
to a given path:

```python
processor = OutlookMsgProcessor("out")
results = processor.process_attachments([
    ("../../evil.txt", lambda dest: open(dest, "w").write("data")),
])
# -> saved as out/evil.txt; the traversal attempt is neutralized.
```

## Safety properties

- **Filename sanitization** — attachment names are reduced to a single safe
  path component: no separators, no `..`, no control characters, no Windows
  reserved device names; length-capped.
- **Safe archive extraction** — `.zip`/`.tar*` attachments are unpacked via
  the local `safe_archive.py`, which rejects Zip-Slip / path-traversal
  members. A malicious archive is recorded as an error, not extracted.
- **Dry-run** — `dry_run=True` performs no writes or extraction.

## Limitations

- **Windows + Outlook required at runtime.** `process_msg_file()` /
  `iter_msg_attachments()` need a Windows host with Microsoft Outlook
  installed and configured (the COM `Outlook.Application` automation API).
- **`.msg` parsing is delegated to Outlook.** This utility does not parse the
  MAPI/`.msg` binary format itself; off Windows there is no way to open a real
  `.msg`.
- **PDF conversion/merging is out of scope.** The original
  `OutlookMailMsgToPdfConverter` / `OutlookMailMsgPdfProcessor` behaviour is
  intentionally not reimplemented here; this utility focuses on attachment
  extraction.
- **Encrypted or rights-managed messages** may not yield attachments via COM.
- Nested archives are extracted one level only.
