# examples/

Runnable demos and CLI wrappers around `python_light_scripts`. Each file
guards its entry point with `if __name__ == "__main__"` and imports the
library rather than redefining logic.

Run from the repository root, e.g.:

```bash
python -m examples.geometry_location
python examples/excel_cd_to_json.py input.xlsx output.json
```

Demos for the isolated `_windows` / `_network` packages are intentionally
omitted — see those packages' own READMEs.
