# robots_txt_analyzer

Fetch and inspect `robots.txt`.

Features:

- Fetch `robots.txt` for a site.
- List user-agent blocks, disallow rules, allow rules, and sitemap entries.
- Check whether a path is allowed for a given user agent.

## Usage

```bash
python webops/robots_txt_analyzer/main.py \
  webops/robots_txt_analyzer/sample_input.txt \
  --path / \
  --json-out webops/robots_txt_analyzer/sample_output/robots.json
```
