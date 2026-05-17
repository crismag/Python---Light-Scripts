"""CLI: convert a 'Critical Dimension' Excel sheet to JSON."""

import argparse

from python_light_scripts.excel import critical_dimension

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a 'Critical Dimension' sheet to JSON.")
    parser.add_argument("excel_file", help="Input .xlsx path")
    parser.add_argument("json_file", help="Output .json path")
    args = parser.parse_args()

    critical_dimension.convert(args.excel_file, args.json_file)
