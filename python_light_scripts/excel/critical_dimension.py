"""Read a "Critical Dimension" Excel worksheet and convert it to JSON.

Productionized from ``Excel_File_To_JSON/critical_dimension_reader.py``: type
hints and docstrings added; behaviour preserved. The CLI entry point lives
in ``examples/excel_critical_dimension.py``.
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
    """Read the 'Critical Dimension' sheet of an Excel file into a DataFrame."""
    return pd.read_excel(
        excel_file_path, sheet_name="Critical Dimension", header=None, usecols=None
    )


def combine_details_row(table: pd.DataFrame, patterns: list[Any]) -> dict[str, Any]:
    """Collapse all 'Detail' rows into a single record keyed by pattern."""
    new_row = {"Categories": "Detail", "SubCategory": "DetailsList"}

    try:
        detail_rows = table[table["Categories"] == "Detail"]
        for pat in patterns:
            foo_values = detail_rows[pat].dropna().values.tolist()
            new_row.update({pat: foo_values})
    except Exception as e:
        print(f"Error occurred while combining detail rows: {e}")
        new_row = {}

    return new_row


def combine_results_rows(table: pd.DataFrame) -> dict[str, Any]:
    """Collapse all 'Result' rows into a single JSON-per-column record."""
    pattern = "Result"
    df = table[table["Categories"] == pattern]
    new_row = {"Categories": "Result", "SubCategory": "ResultsJson"}
    for col in df.columns[2:]:
        subcats = df["SubCategory"].unique()
        new_json = {}
        for subcat in subcats:
            val = df.loc[df["SubCategory"] == subcat, col].iloc[0]
            new_json.update({subcat: val})
        new_row.update({col: json.dumps(new_json)})
    return new_row


def combine_specifications_rows(table: pd.DataFrame) -> dict[str, Any]:
    """Collapse all 'Specification' rows into a single JSON-per-column record."""
    pattern = "Specification"
    df = table[table["Categories"] == pattern]
    new_row = {"Categories": "Specification", "SubCategory": "SpecificationJson"}
    for col in df.columns[2:]:
        subcats = df["SubCategory"].unique()
        new_json = {}
        for subcat in subcats:
            val = df.loc[df["SubCategory"] == subcat, col].iloc[0]
            new_json.update({subcat: val})
        new_row.update({col: json.dumps(new_json)})
    return new_row


def create_category_tables(df: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    """Parse the raw worksheet into ``(main_row, category_table)``."""
    main_row = {}
    for keys in ["Device", "Layer", "Tool"]:
        row = df[df[1] == keys].index[0]
        main_row.update({keys: str(df.loc[row][2])})

    start_row = df[df[1] == "Information"].index[0]
    start_col = df.columns.get_loc(1)
    patterns = list(df.iloc[start_row - 1, start_col + 1 :])
    patterns = [x for x in patterns if str(x) != "nan"]
    if patterns[0] == "No.":
        patterns.pop(0)

    item_count: dict[Any, int] = {}
    for item in patterns:
        if item in item_count:
            item_count[item] += 1
        else:
            item_count[item] = 1

    # Append suffix to duplicates
    for i in range(len(patterns)):
        item = patterns[i]
        if item_count[item] > 1:
            suffix = "_#DUP_" + str(item_count[item] - 1)
            patterns[i] = str(item) + suffix
            item_count[item] += 1

    column_names = ["Categories", "SubCategory"] + patterns

    table = df.iloc[start_row - 1 :, start_col:]
    table = table.iloc[1:].reset_index(drop=True)
    table.columns = column_names
    table["Categories"] = table["Categories"].fillna(method="ffill")
    table = table.reset_index(drop=True)

    new_table = table
    for cat in ["Detail", "Result", "Specification"]:
        new_table = new_table[new_table["Categories"] != cat].copy()

    try:
        new_detail_row = combine_details_row(table, patterns)
        new_table = pd.concat([new_table, pd.DataFrame([new_detail_row])], ignore_index=True)
    except Exception as e:
        print(f"Detail Row Error: {str(e)}")

    try:
        new_result_row = combine_results_rows(table)
        new_table = pd.concat([new_table, pd.DataFrame([new_result_row])], ignore_index=True)
    except Exception as e:
        print(f"Result Row Error: {str(e)}")

    try:
        new_spec_row = combine_specifications_rows(table)
        new_table = pd.concat([new_table, pd.DataFrame([new_spec_row])], ignore_index=True)
    except Exception as e:
        print(f"Specifications Row Error: {str(e)}")

    return main_row, new_table


def generate_json_data(main_row: dict[str, Any], df: pd.DataFrame) -> dict[str, Any]:
    """Transpose the category table and emit a pattern-keyed JSON dict."""
    dft = df.transpose()
    column_names = list(dft.iloc[1])
    dft.columns = column_names
    dft = dft.iloc[2:]
    dft = dft.reset_index(drop=True)
    d = dft.to_dict(orient="records")

    for row in d:
        for key, value in row.items():
            if isinstance(value, str):
                try:
                    row[key] = json.loads(value)
                except ValueError:
                    row[key] = value

    json_data = {row["Pattern"]: row for row in d}
    json_data.update(main_row)
    return json_data


def convert(excel_file_path: str, json_file_path: str) -> dict[str, Any]:
    """Read ``excel_file_path`` and write the JSON result to ``json_file_path``.

    Returns the JSON-ready dict that was written.
    """
    excel_file = os.path.normpath(excel_file_path)

    df = read_excel_file(excel_file)
    main_row, table = create_category_tables(df)
    json_data = generate_json_data(main_row, table)

    with open(json_file_path, "w") as f:
        json.dump(json_data, f, indent=4)

    print(f"JSON_OUTPUT={json_file_path}")
    return json_data
