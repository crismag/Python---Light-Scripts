# ssl_expiry_checker

Check TLS certificate expiry dates.

Features:

- Connect to a hostname over TLS.
- Read certificate expiry date with the standard library.
- Warn when expiry is within a configurable number of days.
- Support text or YAML input files.

## Usage

```bash
python webops/ssl_expiry_checker/main.py \
  webops/ssl_expiry_checker/sample_input.txt \
  --json-out webops/ssl_expiry_checker/sample_output/ssl.json
```
