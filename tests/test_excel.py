"""Tests for the Excel-to-JSON readers.

The Excel readers expect specifically-formatted worksheets. Rather than
committing binary ``.xlsx`` fixtures, these tests build the equivalent
in-memory DataFrames and exercise the pure parsing logic directly. Skipped
if ``pandas`` is not installed.
"""

import json

import pytest

pd = pytest.importorskip("pandas")

from python_light_scripts.excel import cd_coordinates, critical_dimension  # noqa: E402

# --- cd_coordinates ---------------------------------------------------------

def _cd_coordinate_frame():
    """Build a DataFrame shaped like a 'CD Coordinate' worksheet."""
    nan = float("nan")
    rows = [
        [nan, "Device", "DevX", nan, nan, nan, nan],
        [nan, "Layer", "L1", nan, nan, nan, nan],
        [nan, "Tool", "T1", nan, nan, nan, nan],
        [nan, "Information", nan, "PatA", nan, "PatB", nan],  # start_row
        [nan, nan, nan, "X", "Y", "X", "Y"],                  # xy labels
        [nan, nan, nan, 1, 2, 3, 4],                          # data
        [nan, nan, nan, 5, 6, 7, 8],                          # data
    ]
    return pd.DataFrame(rows)


def test_cd_coordinates_worksheet_to_dict():
    result = cd_coordinates.cd_coordinates_worksheet_to_dict(_cd_coordinate_frame())

    assert result["Device"] == "DevX"
    assert result["Layer"] == "L1"
    assert result["Tool"] == "T1"
    assert result["PatA"] == [(1, 2), (5, 6)]
    assert result["PatB"] == [(3, 4), (7, 8)]


def test_cd_coordinates_convert_writes_json(tmp_path, monkeypatch):
    # convert() reads via read_excel_file(); patch it to use our frame.
    monkeypatch.setattr(cd_coordinates, "read_excel_file", lambda _p: _cd_coordinate_frame())
    out = tmp_path / "out.json"
    data = cd_coordinates.convert("ignored.xlsx", str(out))

    on_disk = json.loads(out.read_text())
    assert on_disk["Device"] == "DevX"
    assert data["Device"] == "DevX"


# --- critical_dimension -----------------------------------------------------

def test_combine_results_rows_packs_subcategories_as_json():
    table = pd.DataFrame(
        {
            "Categories": ["Result", "Result"],
            "SubCategory": ["mean", "sigma"],
            "PatA": [1.0, 0.1],
            "PatB": [2.0, 0.2],
        }
    )
    row = critical_dimension.combine_results_rows(table)

    assert row["Categories"] == "Result"
    assert json.loads(row["PatA"]) == {"mean": 1.0, "sigma": 0.1}
    assert json.loads(row["PatB"]) == {"mean": 2.0, "sigma": 0.2}


def test_combine_specifications_rows_packs_subcategories_as_json():
    table = pd.DataFrame(
        {
            "Categories": ["Specification"],
            "SubCategory": ["limit"],
            "PatA": [9.0],
        }
    )
    row = critical_dimension.combine_specifications_rows(table)
    assert json.loads(row["PatA"]) == {"limit": 9.0}


def test_combine_details_row_collects_values_per_pattern():
    table = pd.DataFrame(
        {
            "Categories": ["Detail", "Detail"],
            "SubCategory": ["d1", "d2"],
            "PatA": [10, 11],
        }
    )
    row = critical_dimension.combine_details_row(table, ["PatA"])
    assert row["Categories"] == "Detail"
    assert row["PatA"] == [10, 11]
