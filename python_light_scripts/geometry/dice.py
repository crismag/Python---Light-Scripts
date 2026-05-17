"""Render the six faces of a die as PNG images using Pillow.

Migrated from ``geometries/dice_face_generator.py``. The original ran its
loop at import time and wrote files into the current directory; the logic
is unchanged but now wrapped in a function so it is import-safe.
"""

import os

from PIL import Image, ImageDraw

# Pip positions as fractions of the face size: which positions are filled
# for each face value 1-6. (0.5, 0.5) is the centre.
_FACE_PIPS = {
    1: [(0.5, 0.5)],
    2: [(0.25, 0.25), (0.75, 0.75)],
    3: [(0.25, 0.25), (0.5, 0.5), (0.75, 0.75)],
    4: [(0.25, 0.25), (0.25, 0.75), (0.75, 0.25), (0.75, 0.75)],
    5: [(0.25, 0.25), (0.25, 0.75), (0.5, 0.5), (0.75, 0.25), (0.75, 0.75)],
    6: [(0.25, 0.25), (0.25, 0.5), (0.25, 0.75), (0.75, 0.25), (0.75, 0.5), (0.75, 0.75)],
}

# Pip radius in pixels (matches the original hard-coded +/-20).
_PIP_RADIUS = 20


def _draw_pip(draw, size, fx, fy):
    """Draw a single pip centred at fractional position ``(fx, fy)``."""
    cx, cy = fx * size, fy * size
    draw.ellipse(
        (cx - _PIP_RADIUS, cy - _PIP_RADIUS, cx + _PIP_RADIUS, cy + _PIP_RADIUS),
        fill="black",
    )


def generate_dice_faces(output_dir=".", size=200):
    """Draw dice faces 1-6 and save them as ``dice_face_<n>.png``.

    Returns a dict mapping face value -> written file path.
    """
    os.makedirs(output_dir, exist_ok=True)
    dice_faces = {}

    for value, pips in _FACE_PIPS.items():
        image = Image.new("RGB", (size, size), color="white")
        draw = ImageDraw.Draw(image)
        for fx, fy in pips:
            _draw_pip(draw, size, fx, fy)

        image_path = os.path.join(output_dir, f"dice_face_{value}.png")
        image.save(image_path)
        dice_faces[value] = image_path

    return dice_faces
