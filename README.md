# Python Light Scripts

A cookbook of small, reusable Python utilities — refactored from a flat
collection of demo scripts into an importable, tested package.

## Layout

```
python_light_scripts/      Importable library (cross-platform, import-safe)
  geometry/                Point transforms, dice-face image generation
  excel/                   Excel-worksheet -> JSON readers
  xmltools/                XML reformatting helpers
  monitoring/              Date/holiday-aware command running
  acl/                     POSIX ACL management (Linux runtime)
  auth/                    TOTP and 2FA session-token helpers
  process/                 Subprocess orchestration + progress bars
  _windows/   [ISOLATED]   Windows-only code (winreg, Outlook COM)
  _network/   [ISOLATED]   Network/credential-bound code (Google Drive)
examples/                  Runnable demos / CLIs (entry points guarded)
tests/                     pytest suite
docs/                      Supporting documentation (requirements, plans)

document_generation/       Automation cookbook — Markdown/HTML/docx report generation
excel_tools/               Automation cookbook — Excel generation, parsing, dashboards
pdf_tools/                 Automation cookbook — PDF generation, merging, reports
webops/                    Automation cookbook — website & web-automation checks (HTTP)
```

## Automation cookbook sections

Alongside the `python_light_scripts` package, four top-level sections collect
**standalone, copy-and-run automation scripts**. Unlike the package, every
script here is fully self-contained — no imports between scripts, no shared
package — so you can lift a single file into your own work. Each section ships
its own `README.md` and sample datasets; the three original cookbook sections
also include `ROADMAP.md`, `requirements.txt` and `tests/`.

| Section | Focus | Key dependencies |
|---------|-------|------------------|
| `document_generation/` | Markdown / HTML / docx reports, templating, multi-source reports | `jinja2`, `pyyaml`, `markdown`, `python-docx` |
| `excel_tools/` | Workbook generation, parsing, transforms, validation, dashboards | `openpyxl`, `pandas` |
| `pdf_tools/` | PDF generation, merging/splitting, watermarking, styled reports | `reportlab`, `pypdf` |
| `webops/` | Website health, SEO, security headers, uptime, sitemap & link checks | `requests`, `beautifulsoup4`, `pyyaml` |

Scripts progress through four complexity levels — **beginner → intermediate →
advanced → showcase**. Install a section's dependencies from its
`requirements.txt`, then run any script with `--help`. See each section's
`README.md` for usage and `ROADMAP.md` for what is implemented vs planned.

## Categories

| Category | Modules | Use it for |
|----------|---------|------------|
| Geometry | `geometry.location`, `geometry.dice` | Rotate/mirror points; render images |
| Excel    | `excel.cd_coordinates`, `excel.critical_dimension` | Parse formatted `.xlsx` reports to JSON |
| XML      | `xmltools.cofc_reader` | Reformat domain-specific XML |
| Monitoring | `monitoring.holidays` | Run commands with holiday awareness |
| ACL      | `acl.manager` | Add/remove POSIX ACL entries (Linux) |
| Auth     | `auth.totp`, `auth.sessions`, `auth.rsa_token` | TOTP codes, 2FA session tokens |
| Process  | `process.parallel`, `process.progress` | Concurrent commands, progress bars |

## Install

```bash
python -m pip install -e ".[dev]"
# Optional, platform/use-case specific:
#   pip install -e ".[windows]"   pip install -e ".[network]"   pip install -e ".[ctf]"
```

## Safe usage

- **Library modules are import-safe** and have no import-time side effects.
  Runnable behaviour lives in `examples/` behind `if __name__ == "__main__"`.
- **`_windows/` and `_network/` are isolated**: not part of the public
  namespace, excluded from the default test run, and only importable where
  their platform/credentials are available.
- **No secrets are stored** in this repository. TOTP and similar helpers take
  secrets as arguments (e.g. via environment variables).
- **No network calls** are made by the `python_light_scripts` package or its
  tests. Network code is confined to the clearly-marked `_network/` package and
  the `webops/` automation section, which makes HTTP requests only to the URLs
  you explicitly supply.
- Some tools change system state — ACL modification, the Windows registry,
  Outlook COM. These carry warnings in their docstrings; see `SECURITY.md`.

## Develop

```bash
pytest          # run the test suite
ruff check .    # lint
mypy            # type-check
```

## History

This package was produced by a staged refactor of the original flat script
collection.
