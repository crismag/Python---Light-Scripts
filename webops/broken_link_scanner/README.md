# broken_link_scanner

Scan webpages and report broken links.

Features:

- Fetch a starting page.
- Extract anchor links with `beautifulsoup4`.
- Check HTTP status for internal and external links.
- Print a terminal summary and optionally write JSON or Markdown output.

## Usage

```bash
python webops/broken_link_scanner/main.py \
  webops/broken_link_scanner/sample_input.txt \
  --limit 25 \
  --json-out webops/broken_link_scanner/sample_output/links.json
```
