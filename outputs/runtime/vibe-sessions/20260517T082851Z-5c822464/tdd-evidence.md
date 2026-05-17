# Host TDD Evidence

## Red Phase

Command run before implementation:

```bash
python webops/security_headers_auditor/main.py \
  webops/security_headers_auditor/sample_input.txt \
  --json-out /tmp/security_headers.json
```

Observed result:

- Exit code: `2`
- Error: `main.py: error: unrecognized arguments: --json-out /tmp/security_headers.json`

This established that scaffolded utility scripts did not yet support the report-output behavior required for the generated standalone CLIs.

## Green Phase

Targeted verification after implementation:

```bash
python -B webops/security_headers_auditor/main.py \
  webops/security_headers_auditor/sample_input.txt \
  --json-out /tmp/security_headers.json
```

Observed result:

- Exit code: `0`
- Terminal audit ran against `https://example.com`
- JSON report output was accepted and written.

Additional verification:

```bash
ruff check webops
python -m compileall -q webops
for f in webops/*/main.py; do python "$f" --help >/tmp/webops-help.txt || exit 1; done
```

Observed result:

- Ruff passed for `webops`.
- Compileall passed for `webops`.
- Every standalone CLI exposed a working `--help`.

