# simple_seo_auditor

Run simple on-page SEO checks.

Features:

- Check page title and meta description presence.
- Inspect heading structure.
- Count images missing alt text.
- Report canonical URL and robots directives.

## Usage

```bash
python webops/simple_seo_auditor/main.py \
  webops/simple_seo_auditor/sample_input.txt \
  --json-out webops/simple_seo_auditor/sample_output/seo.json
```
