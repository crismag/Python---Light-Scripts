# redirect_chain_checker

Inspect URL redirect chains.

Features:

- Follow redirects from an initial URL.
- Print each hop with status code and location.
- Detect loops and excessive chains.
- Optionally write JSON output.

## Usage

```bash
python webops/redirect_chain_checker/main.py \
  webops/redirect_chain_checker/sample_input.txt \
  --json-out webops/redirect_chain_checker/sample_output/chain.json
```
