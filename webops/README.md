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

## Utilities

| Folder | Purpose | Status |
|--------|---------|--------|
| `website_health_checker/` | Check one or more URLs for availability, status code, redirects, and latency | Working |
| `broken_link_scanner/` | Crawl a page and report broken internal/external links | Working |
| `sitemap_validator/` | Validate sitemap XML and optionally check URL availability | Working |
| `security_headers_auditor/` | Check common HTTP security headers | Working |
| `ssl_expiry_checker/` | Report TLS certificate expiry dates | Working |
| `uptime_monitor/` | Periodically check endpoints and append uptime results | Working |
| `redirect_chain_checker/` | Show redirect hops and final landing URL | Working |
| `webpage_metadata_extractor/` | Extract page title, description, canonical URL, and social metadata | Working |
| `simple_seo_auditor/` | Run simple on-page SEO checks | Working |
| `api_endpoint_checker/` | Check JSON/API endpoints for status and expected fields | Working |
| `robots_txt_analyzer/` | Fetch and inspect `robots.txt` rules | Working |
| `web_content_change_tracker/` | Detect content changes between runs | Working |

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
