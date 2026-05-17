"""Rotate and mirror a point about the origin of a placed cell.

Productionized from ``geometries/location_calculator.py``: type hints and
docstrings added; behaviour preserved. Pure logic only — the runnable demo
lives in ``examples/geometry_location.py``.
"""

from __future__ import annotations

import math

Number = float  # ints are accepted; results are floats


class PointLocationCalculator:
    """Transform a point into a rotated/mirrored cell frame.

    The transform translates the point to the cell origin, optionally
    mirrors it on the X axis, rotates it by ``rotation`` degrees, then
    translates it back.

    Args:
        cell_x: X coordinate of the cell origin.
        cell_y: Y coordinate of the cell origin.
        rotation: rotation angle in degrees (counter-clockwise).
        mirrored: whether the cell is mirrored on the X axis.
    """

    def __init__(
        self,
        cell_x: Number,
        cell_y: Number,
        rotation: Number,
        mirrored: bool,
    ) -> None:
        self.cell_x: float = float(cell_x)
        self.cell_y: float = float(cell_y)
        self.rotation: float = float(rotation)
        self.mirrored: bool = mirrored

        self.theta: float = math.radians(rotation)
        self.cos_theta: float = math.cos(self.theta)
        self.sin_theta: float = math.sin(self.theta)

    def calculate_location(self, x: Number, y: Number) -> tuple[float, float]:
        """Return ``(x, y)`` transformed into the cell frame.

        Args:
            x: X coordinate of the point, in the parent frame.
            y: Y coordinate of the point, in the parent frame.

        Returns:
            The transformed ``(x, y)`` coordinates as floats.
        """
        # Translate the point to the origin of the cell
        x -= self.cell_x
        y -= self.cell_y

        # Apply the mirror, then the rotation
        if self.mirrored:
            x = -x
        x_rotated = x * self.cos_theta - y * self.sin_theta
        y_rotated = x * self.sin_theta + y * self.cos_theta

        # Translate the point back to the parent frame
        x_frame = self.cell_x + x_rotated
        y_frame = self.cell_y + y_rotated

        return x_frame, y_frame
