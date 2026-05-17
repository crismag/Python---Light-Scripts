# webops

Lightweight website and web-automation utility scripts.

This is one of the repository's automation-cookbook sections (alongside
`document_generation/`, `excel_tools/` and `pdf_tools/`). Every script is
**standalone and copy-and-run** — no imports between scripts, no shared
package — so a single file can be lifted into your own work. Each utility has
its own folder with a `main.py`, a `README.md`, a `sample_input.*` file and a
`sample_output/` directory.

Unlike the other cookbook sections, the scripts here make outbound HTTP(S)
requests — only to the URLs and hosts you explicitly supply as input.

## Start Here

Every utility at a glance — difficulty level, what it does, what it needs, and
what it writes. Each utility's folder `README.md` shows the exact command;
every `main.py` also accepts `--help`.

| Utility | Level | Purpose | Dependencies | Output |
|---------|-------|---------|--------------|--------|
| [website_health_checker/](website_health_checker/) | Beginner | Check URLs for availability, status code, redirects, and latency | `requests` | terminal table + optional JSON/Markdown |
| [ssl_expiry_checker/](ssl_expiry_checker/) | Beginner | Report TLS certificate expiry dates | stdlib only | terminal report + optional JSON |
| [redirect_chain_checker/](redirect_chain_checker/) | Beginner | Show redirect hops and final landing URL | `requests` | terminal chain + optional JSON |
| [security_headers_auditor/](security_headers_auditor/) | Beginner | Check common HTTP security headers | `requests` | terminal report + optional JSON/Markdown |
| [webpage_metadata_extractor/](webpage_metadata_extractor/) | Beginner | Extract title, description, canonical URL, and social metadata | `requests`, `beautifulsoup4` | terminal summary + optional JSON |
| [broken_link_scanner/](broken_link_scanner/) | Intermediate | Crawl a page and report broken internal/external links | `requests`, `beautifulsoup4` | terminal summary + optional JSON/Markdown |
| [sitemap_validator/](sitemap_validator/) | Intermediate | Validate sitemap XML and optionally check URL availability | `requests` | terminal summary + optional JSON |
| [robots_txt_analyzer/](robots_txt_analyzer/) | Intermediate | Fetch and inspect `robots.txt` rules | `requests` | terminal summary + optional JSON |
| [simple_seo_auditor/](simple_seo_auditor/) | Intermediate | Run simple on-page SEO checks | `requests`, `beautifulsoup4` | terminal report + optional JSON |
| [api_endpoint_checker/](api_endpoint_checker/) | Intermediate | Check JSON/API endpoints for status and expected fields | `requests` | terminal report + optional JSON |
| [uptime_monitor/](uptime_monitor/) | Intermediate | Periodically check endpoints and append uptime results | `requests` | terminal lines + optional JSON Lines |
| [web_content_change_tracker/](web_content_change_tracker/) | Advanced | Detect content changes between runs (content hash + state files) | `requests`, `beautifulsoup4` | change status + state files + optional JSON |

Utilities that accept YAML input files (`website_health_checker/`,
`uptime_monitor/`, `api_endpoint_checker/`, `web_content_change_tracker/`) also
use `pyyaml`, imported lazily — text/JSON inputs work without it.

## Dependencies

Use Python 3.11+. Install the dependencies the scripts share:

```bash
python -m pip install requests beautifulsoup4 pyyaml
```

- `requests` — used by every utility for HTTP(S) requests.
- `beautifulsoup4` — used by the HTML-parsing utilities (`broken_link_scanner/`,
  `simple_seo_auditor/`, `webpage_metadata_extractor/`, `web_content_change_tracker/`).
- `pyyaml` — optional; only needed when an input file is YAML. It is imported
  lazily, so text/JSON inputs work without it.

`sitemap_validator/` and `ssl_expiry_checker/` rely only on the standard
library beyond `requests`.

## Run The First Utility

```bash
python webops/website_health_checker/main.py \
  webops/website_health_checker/sample_input.yaml
```

Write reports:

```bash
python webops/website_health_checker/main.py \
  webops/website_health_checker/sample_input.yaml \
  --json-out webops/website_health_checker/sample_output/health_report.json \
  --markdown-out webops/website_health_checker/sample_output/health_report.md
```
