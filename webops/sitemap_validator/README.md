# sitemap_validator

Validate sitemap XML files.

Features:

- Fetch or read a sitemap.
- Parse `<urlset>` and `<sitemapindex>` files.
- Validate URL shape and required XML structure.
- Optionally check URL availability.

## Usage

```bash
python webops/sitemap_validator/main.py https://example.com/sitemap.xml \
  --json-out webops/sitemap_validator/sample_output/sitemap.json
```
