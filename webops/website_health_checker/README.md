# website_health_checker

Check whether one or more websites are reachable and responding as expected.

The script reports:

- HTTP status code
- final URL after redirects
- redirect count
- response time in milliseconds
- basic pass/fail result
- error details for timeouts, DNS failures, TLS failures, and connection errors

## Usage

```bash
python webops/website_health_checker/main.py \
  webops/website_health_checker/sample_input.yaml
```

Create optional report files:

```bash
python webops/website_health_checker/main.py \
  webops/website_health_checker/sample_input.yaml \
  --json-out webops/website_health_checker/sample_output/health_report.json \
  --markdown-out webops/website_health_checker/sample_output/health_report.md
```

Fail the command when any target is unhealthy:

```bash
python webops/website_health_checker/main.py urls.txt --fail-on-error
```

## Input Formats

YAML:

```yaml
urls:
  - url: https://example.com
    expected_status: 200
  - https://www.python.org
```

Plain text:

```text
https://example.com
https://www.python.org
```

Blank lines and `#` comments are ignored.

