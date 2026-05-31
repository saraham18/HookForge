"""Generate a simple branded announcement card.

Instagram's API cannot publish text-only posts, so when you publish there you
need an image. This makes a clean 1080x1080 card from a headline + subtitle so
you don't need a designer for a launch post. Pillow is imported lazily.
"""
from __future__ import annotations

import textwrap
from pathlib import Path


def _load_font(size: int):
    from PIL import ImageFont

    # Try a few fonts commonly available on macOS/Linux; fall back to default.
    for name in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ):
        if Path(name).exists():
            try:
                return ImageFont.truetype(name, size)
            except OSError:
                continue
    return ImageFont.load_default()


def make_card(
    headline: str,
    subtitle: str = "",
    out_path: str = "card.png",
    *,
    size: int = 1080,
    bg: tuple = (15, 18, 28),
    fg: tuple = (240, 240, 245),
    accent: tuple = (120, 170, 255),
) -> str:
    """Render a square announcement card and return its path."""
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (size, size), bg)
    draw = ImageDraw.Draw(img)

    # Accent bar at the top.
    draw.rectangle([0, 0, size, 16], fill=accent)

    headline_font = _load_font(76)
    subtitle_font = _load_font(38)

    margin = 110
    wrap_width = 18
    lines = textwrap.wrap(headline, width=wrap_width) or [""]

    # Vertically center the headline block.
    line_height = 92
    block_height = line_height * len(lines)
    y = (size - block_height) // 2 - 40
    for line in lines:
        draw.text((margin, y), line, font=headline_font, fill=fg)
        y += line_height

    if subtitle:
        sub_lines = textwrap.wrap(subtitle, width=40)
        sy = y + 40
        for line in sub_lines:
            draw.text((margin, sy), line, font=subtitle_font, fill=accent)
            sy += 52

    out = Path(out_path)
    if out.parent and not out.parent.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
    # Instagram's content-publishing API only accepts JPEG, so save JPEG with a
    # sensible quality when the caller asks for .jpg/.jpeg (RGB mode is already
    # JPEG-compatible). Other extensions save in their native format.
    if out.suffix.lower() in (".jpg", ".jpeg"):
        img.save(out, "JPEG", quality=90, optimize=True)
    else:
        img.save(out)
    return str(out)
