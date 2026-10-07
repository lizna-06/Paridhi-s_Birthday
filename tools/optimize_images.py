"""Build the WebP images used by the GitHub Pages site from originals/."""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"

jobs = []
jobs.extend(
    (source, SITE / "assets" / "images" / f"{source.stem.lower()}.webp", False)
    for source in sorted((ROOT / "originals" / "photos").glob("*"))
)
jobs.extend(
    (source, SITE / "assets" / "images" / f"{source.stem}.webp", False)
    for source in sorted((ROOT / "originals" / "cats").glob("*.jpg"))
)
jobs.extend(
    (source, SITE / "assets" / "stickers" / f"{source.stem}.webp", True)
    for source in sorted((ROOT / "originals" / "stickers").glob("*.png"))
)

for source, output, keep_alpha in jobs:
    output.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as original:
        image = original.copy()
    if keep_alpha:
        image = image.convert("RGBA")
        image.save(output, "WEBP", quality=88, method=6)
    else:
        if max(image.size) > 1800:
            image.thumbnail((1800, 1800), Image.Resampling.LANCZOS)
        image.convert("RGB").save(output, "WEBP", quality=84, method=6)
    before, after = source.stat().st_size, output.stat().st_size
    print(f"{source.name}: {before:,} -> {after:,} bytes")
