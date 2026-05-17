# webpage_metadata_extractor

Extract webpage metadata.

Features:

- Fetch a webpage.
- Extract title, meta description, canonical URL, Open Graph tags, and Twitter card tags.
- Print terminal output and optionally write JSON.

## Usage

```bash
python webops/webpage_metadata_extractor/main.py \
  webops/webpage_metadata_extractor/sample_input.txt \
  --json-out webops/webpage_metadata_extractor/sample_output/metadata.json
```
