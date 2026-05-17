# webops

Lightweight website and web-automation utility scripts.

This folder follows the same spirit as the rest of Python Light Scripts:
small tools, readable code, practical defaults, and examples that are easy to
run from a terminal.

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

Use Python 3.11+.

The scripts use:

```bash
python -m pip install requests beautifulsoup4 pyyaml
```

Future utilities may also use `beautifulsoup4`.

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
