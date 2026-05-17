"""Tests for python_light_scripts.geometry.location.

Replaces the broken ad-hoc script ``geometries/test_location.py``.
"""

import math

from python_light_scripts.geometry import PointLocationCalculator


def test_identity_no_rotation_no_mirror():
    calc = PointLocationCalculator(cell_x=0, cell_y=0, rotation=0, mirrored=False)
    assert calc.calculate_location(5, 10) == (5, 10)


def test_rotation_90_degrees():
    calc = PointLocationCalculator(cell_x=0, cell_y=0, rotation=90, mirrored=False)
    x, y = calc.calculate_location(1, 0)
    assert math.isclose(x, 0, abs_tol=1e-9)
    assert math.isclose(y, 1, abs_tol=1e-9)


def test_mirror_flips_x_about_cell_origin():
    calc = PointLocationCalculator(cell_x=20, cell_y=30, rotation=0, mirrored=True)
    x, y = calc.calculate_location(25, 30)
    assert math.isclose(x, 15, abs_tol=1e-9)
    assert math.isclose(y, 30, abs_tol=1e-9)


def test_original_script_inputs_run_without_error():
    # The values from the old geometries/test_location.py
    calc = PointLocationCalculator(cell_x=20, cell_y=30, rotation=90, mirrored=True)
    x, y = calc.calculate_location(5, 10)
    assert isinstance(x, float)
    assert isinstance(y, float)
