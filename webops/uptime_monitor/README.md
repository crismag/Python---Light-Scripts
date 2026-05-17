# uptime_monitor

Run lightweight uptime checks.

Features:

- Check endpoints on a repeat interval.
- Append results to JSON Lines or CSV.
- Print compact terminal status updates.
- Exit cleanly on Ctrl+C.

## Usage

```bash
python webops/uptime_monitor/main.py \
  webops/uptime_monitor/sample_input.yaml \
  --count 1 \
  --jsonl-out webops/uptime_monitor/sample_output/uptime.jsonl
```
