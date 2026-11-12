"""Render the plugin's storefront icon to PNG.

The market only accepts raster images (png/jpg/webp), so the source SVG is
redrawn here from the same coordinates at 8x and downsampled. Run:

    python scripts/make-icon.py

Writes assets/icon-512.png and assets/icon-180.png.
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

# Source geometry, in the SVG's 64x64 user units.
VIEW = 64.0
CORNER = 14.0
CIRCLE_CENTER = (28.0, 28.0)
CIRCLE_RADIUS = 13.0
CIRCLE_STROKE = 4.5
HANDLE_FROM = (38.0, 38.0)
HANDLE_TO = (50.0, 50.0)
HANDLE_STROKE = 5.5
ARROW_SHAFT = ((28.0, 33.5), (28.0, 22.5))
ARROW_HEAD = ((23.5, 27.0), (28.0, 22.5), (32.5, 27.0))
ARROW_STROKE = 3.5

GRADIENT_FROM = np.array([0x4D, 0x8D, 0xFF], dtype=float)
GRADIENT_TO = np.array([0x1A, 0x5F, 0xD0], dtype=float)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
SUPERSAMPLE = 8


def render(size: int) -> Image.Image:
    scale = size / VIEW
    steps = size * SUPERSAMPLE

    # Diagonal gradient, matching the SVG's objectBoundingBox 0,0 -> 1,1.
    ys, xs = np.mgrid[0:steps, 0:steps]
    t = ((xs + ys) / (2.0 * (steps - 1)))[..., None]
    rgb = (GRADIENT_FROM * (1.0 - t) + GRADIENT_TO * t).astype(np.uint8)

    # Rounded-rect alpha mask.
    mask = Image.new("L", (steps, steps), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, steps - 1, steps - 1),
        radius=CORNER * scale * SUPERSAMPLE,
        fill=255,
    )

    canvas = Image.new("RGBA", (steps, steps), (0, 0, 0, 0))
    canvas.paste(Image.fromarray(rgb, "RGB"), (0, 0), mask)

    def px(value: float) -> float:
        return value * scale * SUPERSAMPLE

    draw = ImageDraw.Draw(canvas)
    white = (255, 255, 255, 255)

    # Magnifier ring.
    cx, cy = px(CIRCLE_CENTER[0]), px(CIRCLE_CENTER[1])
    r = px(CIRCLE_RADIUS)
    w = px(CIRCLE_STROKE)
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=white, width=int(round(w)))

    # Handle.
    draw.line(
        (px(HANDLE_FROM[0]), px(HANDLE_FROM[1]), px(HANDLE_TO[0]), px(HANDLE_TO[1])),
        fill=white,
        width=int(round(px(HANDLE_STROKE))),
    )

    # Arrow shaft + head.
    draw.line(
        (px(ARROW_SHAFT[0][0]), px(ARROW_SHAFT[0][1]), px(ARROW_SHAFT[1][0]), px(ARROW_SHAFT[1][1])),
        fill=white,
        width=int(round(px(ARROW_STROKE))),
    )
    draw.line(
        [(px(x), px(y)) for x, y in ARROW_HEAD],
        fill=white,
        width=int(round(px(ARROW_STROKE))),
        joint="curve",
    )

    # Round the caps: the SVG uses stroke-linecap round throughout.
    for point in (ARROW_SHAFT[0], ARROW_SHAFT[1], HANDLE_FROM, HANDLE_TO):
        x, y = px(point[0]), px(point[1])
        stroke = px(HANDLE_STROKE) if point in (HANDLE_FROM, HANDLE_TO) else px(ARROW_STROKE)
        draw.ellipse((x - stroke / 2, y - stroke / 2, x + stroke / 2, y + stroke / 2), fill=white)

    return canvas.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for size in (512, 180):
        target = OUT / f"icon-{size}.png"
        render(size).save(target, "PNG", optimize=True)
        print(f"{target.relative_to(ROOT)}  {size}x{size}  {target.stat().st_size} bytes")


if __name__ == "__main__":
    main()
