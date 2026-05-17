# api_endpoint_checker

Check API endpoints for expected status codes and optional JSON fields.

Features:

- Send GET, POST, or other configured methods.
- Validate expected status codes.
- Optionally assert expected JSON fields.
- Print concise terminal results and optionally write JSON.

## Usage

```bash
python webops/api_endpoint_checker/main.py \
  webops/api_endpoint_checker/sample_input.yaml \
  --json-out webops/api_endpoint_checker/sample_output/api.json
```
