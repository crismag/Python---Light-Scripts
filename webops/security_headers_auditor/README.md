# security_headers_auditor

Audit common HTTP security headers.

Features:

- Check headers such as `Content-Security-Policy`, `Strict-Transport-Security`,
  `X-Content-Type-Options`, and `Referrer-Policy`.
- Print missing or weak headers.
- Optionally write a Markdown report for quick sharing.

## Usage

```bash
python webops/security_headers_auditor/main.py \
  webops/security_headers_auditor/sample_input.txt \
  --json-out webops/security_headers_auditor/sample_output/audit.json
```
