# web_content_change_tracker

Detect webpage content changes between runs.

Features:

- Fetch a URL and normalize selected content.
- Store a hash snapshot locally.
- Compare current content against the previous run.
- Print changed/unchanged status and optionally save snapshots.

## Usage

```bash
python webops/web_content_change_tracker/main.py \
  webops/web_content_change_tracker/sample_input.yaml \
  --state-dir webops/web_content_change_tracker/sample_output/state \
  --json-out webops/web_content_change_tracker/sample_output/changes.json
```
