"""Demo/CLI: render the six dice-face PNG images."""

import argparse

from python_light_scripts.geometry.dice import generate_dice_faces

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate dice-face PNG images.")
    parser.add_argument("output_dir", nargs="?", default=".", help="Directory for PNGs")
    parser.add_argument("--size", type=int, default=200, help="Image size in pixels")
    args = parser.parse_args()

    paths = generate_dice_faces(args.output_dir, size=args.size)
    for face, path in paths.items():
        print(f"face {face}: {path}")
