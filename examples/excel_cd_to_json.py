"""CLI: convert a 'CD Coordinate' Excel sheet to JSON."""

import argparse

from python_light_scripts.excel import cd_coordinates

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert a 'CD Coordinate' sheet to JSON.")
    parser.add_argument("excel_file", help="Input .xlsx path")
    parser.add_argument("json_file", help="Output .json path")
    args = parser.parse_args()

    cd_coordinates.convert(args.excel_file, args.json_file)
