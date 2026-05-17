"""Read a "CD Coordinate" Excel worksheet and convert it to a JSON-ready dict.

Productionized from ``Excel_File_To_JSON/cd_coord_to_json.py``: type hints
and docstrings added; behaviour preserved. The CLI entry point lives in
``examples/excel_cd_to_json.py``.

The "CD Coordinate" sheet is expected to contain ``Device``/``Layer``/``Tool``
rows in column B (value in column C) and an ``Information`` row that marks the
start of the per-pattern X/Y coordinate block.
"""

from __future__ import annotations

import json
import os
from typing import Any

import pandas as pd

pd.set_option("display.max_columns", None)
pd.set_option("display.max_rows", None)
pd.set_option("display.width", None)
pd.set_option("display.max_colwidth", None)


def read_excel_file(excel_file_path: str) -> pd.DataFrame:
    """Read the 'CD Coordinate' sheet of an Excel file into a DataFrame."""
    return pd.read_excel(excel_file_path, sheet_name="CD Coordinate", header=None, usecols=None)


def cd_coordinates_worksheet_to_dict(df: pd.DataFrame) -> dict[str, Any]:
    """Convert a 'CD Coordinate' DataFrame into a dict of pattern -> XY pairs."""
    # Get the patterns as column names
    main_row = {}
    for keys in ["Device", "Layer", "Tool"]:
        row = df[df[1] == keys].index[0]
        main_row.update({keys: str(df.loc[row, 2])})
    start_row = df[df[1] == "Information"].index[0]
    start_col = df.columns.get_loc(1)
    patterns = list(df.iloc[start_row, start_col + 2 :])
    patterns = [x for x in patterns if str(x) != "nan"]
    if patterns[0] == "No.":
        patterns.pop(0)

    item_count: dict[Any, int] = {}
    # Count the occurrences of each pattern item in the list
    for item in patterns:
        if item in item_count:
            item_count[item] += 1
        else:
            item_count[item] = 1

    new_pattern = []
    for pat in patterns:
        new_pattern.append(pat + "##X")
        new_pattern.append(pat + "##Y")

    # Define column names
    column_names = new_pattern

    # Slice the table from the start row and column
    table = df.iloc[start_row:, start_col + 2 :]

    # Drop the first row of the table : pattern names
    table = table.iloc[1:].reset_index(drop=True)
    # Drop the first row of the table : x y names
    table = table.iloc[1:].reset_index(drop=True)

    # Rename columns
    table.columns = column_names

    # Reset the index to ensure all values are unique
    table = table.reset_index(drop=True)

    new_row: dict[str, Any] = {}
    for pat in patterns:
        x_col = pat + "##X"
        y_col = pat + "##Y"
        x = table[x_col].dropna()
        y = table[y_col].dropna()
        xy_list = list(zip(x, y))
        new_row[pat] = xy_list

    new_row.update(main_row)

    return new_row


def convert(excel_file_path: str, json_file_path: str) -> dict[str, Any]:
    """Read ``excel_file_path`` and write the JSON result to ``json_file_path``.

    Returns the JSON-ready dict that was written.
    """
    excel_file = os.path.normpath(excel_file_path)

    df = read_excel_file(excel_file)
    json_data = cd_coordinates_worksheet_to_dict(df)
    with open(json_file_path, "w") as f:
        json.dump(json_data, f, indent=4)

    print(f"JSON_OUTPUT={json_file_path}")
    return json_data
