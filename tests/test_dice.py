"""Tests for python_light_scripts.geometry.dice. Skipped without Pillow."""

import pytest

pytest.importorskip("PIL")

from python_light_scripts.geometry.dice import generate_dice_faces  # noqa: E402


def test_generates_six_faces(tmp_path):
    paths = generate_dice_faces(str(tmp_path), size=80)
    assert sorted(paths) == [1, 2, 3, 4, 5, 6]
    for face, path in paths.items():
        assert path.endswith(f"dice_face_{face}.png")


def test_images_have_requested_size(tmp_path):
    from PIL import Image

    paths = generate_dice_faces(str(tmp_path), size=120)
    with Image.open(paths[1]) as img:
        assert img.size == (120, 120)
