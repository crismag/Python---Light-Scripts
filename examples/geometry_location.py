"""Demo: transform a point into a rotated/mirrored cell frame.

Replaces the broken ``geometries/test_location.py`` (which never imported
the class and omitted the required ``mirrored`` argument).
"""

from python_light_scripts.geometry import PointLocationCalculator

if __name__ == "__main__":
    x, y = 5, 10
    calc = PointLocationCalculator(cell_x=20, cell_y=30, rotation=90, mirrored=True)
    x_frame, y_frame = calc.calculate_location(x, y)
    print(f"FRAME_LOC=({x_frame},{y_frame})")
