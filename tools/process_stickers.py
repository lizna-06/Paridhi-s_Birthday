from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

root = Path(__file__).resolve().parents[1]
source_dir = root / "originals" / "stickers"
output_dir = Path(__file__).resolve().parent / "generated-stickers"
output_dir.mkdir(parents=True, exist_ok=True)
for source in sorted(source_dir.glob("gift-sticker-*.jpg")):
    image = Image.open(source).convert("RGBA")
    if source.name == "gift-sticker-hamster.jpg":
        # The white hamster runs into the white page at the bottom, so use a
        # hand-traced silhouette to keep its white body while removing paper.
        alpha = Image.new("L", image.size, 0)
        ImageDraw.Draw(alpha).polygon([
            (379, 0), (418, 0), (434, 12), (435, 25), (420, 38),
            (491, 207), (496, 216), (513, 230), (530, 258), (548, 302),
            (572, 351), (597, 409), (623, 469), (652, 545), (676, 618),
            (698, 702), (699, 722), (40, 722), (45, 708), (65, 649),
            (91, 577), (113, 520), (140, 463), (165, 409), (189, 364),
            (214, 326), (235, 289), (253, 264), (272, 245), (277, 228),
            (287, 215), (318, 210), (320, 198), (354, 69), (375, 28),
            (370, 17), (379, 0)
        ], fill=255)
        alpha = alpha.filter(ImageFilter.GaussianBlur(0.55))
    else:
        rgb = np.asarray(image.convert("RGB"), dtype=np.int16)
        low, high = rgb.min(axis=2), rgb.max(axis=2)
        # Remove only near-white/neutral regions connected to the outer edge,
        # preserving white details enclosed within the actual sticker subject.
        candidates = (low >= 225) & ((high - low) <= 24)
        mask = Image.fromarray(np.where(candidates, 255, 0).astype("uint8"), mode="L")
        draw = ImageDraw.Draw(mask)
        w, h = mask.size
        edge_points = ([(x, 0) for x in range(w)] + [(x, h - 1) for x in range(w)]
                       + [(0, y) for y in range(1, h - 1)] + [(w - 1, y) for y in range(1, h - 1)])
        for point in edge_points:
            if mask.getpixel(point) == 255:
                ImageDraw.floodfill(mask, point, 127, thresh=0)
        exterior = mask.point(lambda value: 255 if value == 127 else 0).filter(ImageFilter.MaxFilter(7))
        alpha = ImageOps.invert(exterior).filter(ImageFilter.GaussianBlur(0.45))
    image.putalpha(alpha)
    bbox = alpha.getbbox()
    if not bbox:
        continue
    image = image.crop(bbox)
    alpha = image.getchannel("A")
    outline = alpha.filter(ImageFilter.MaxFilter(19))
    sticker = Image.new("RGBA", image.size, (255, 253, 248, 0))
    sticker.putalpha(outline)
    sticker.alpha_composite(image)
    shadow = Image.new("RGBA", sticker.size, (75, 62, 55, 0))
    shadow.putalpha(outline.filter(ImageFilter.GaussianBlur(5)).point(lambda value: int(value * 0.22)))
    result = Image.new("RGBA", sticker.size, (0, 0, 0, 0))
    result.alpha_composite(shadow, (0, 4))
    result.alpha_composite(sticker)
    output = output_dir / source.with_suffix(".png").name
    result.save(output, optimize=True)
    print(f"{source.name} -> {output.name} ({result.width}x{result.height})")
