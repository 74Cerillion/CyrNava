#!/usr/bin/env python3
"""Copy the owner-supplied logo unchanged and downsample complete artwork."""

import argparse
import shutil
from pathlib import Path

from PIL import Image, ImageOps

DESTINATION = Path(__file__).resolve().parents[1] / "frontend/public/assets/branding"
SIZES = (16, 32, 48, 64, 128, 256, 512)


def generate(source: Path, destination: Path = DESTINATION):
    destination.mkdir(parents=True, exist_ok=True)
    original = destination / "DesktopLogo.png"
    if source.resolve() != original.resolve():
        shutil.copy2(source, original)
    with Image.open(original) as image:
        image.load()
        for size in SIZES:
            # No cropping, recoloring or background removal. Pad only if a future
            # approved source is not square; preserve its aspect ratio.
            resized = ImageOps.contain(image, (size, size), Image.Resampling.LANCZOS)
            icon = Image.new(image.mode, (size, size))
            icon.paste(
                resized, ((size - resized.width) // 2, (size - resized.height) // 2)
            )
            icon.save(destination / f"cyrnava-{size}.png", optimize=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    generate(parser.parse_args().source)
