"""Generate brand assets (PNG) for the NEC MultiSync integration.

Produces square icons and a wide logo matching the SVG logo style, sized to the
Home Assistant brands repository spec:
  - icon.png       256 x 256
  - icon@2x.png    512 x 512
  - logo.png       <=512 wide (we use a 2:1-ish wordmark)
  - logo@2x.png    2x of logo

Run:  python tools/make_brand_assets.py
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

SCREEN_TOP = (0x18, 0xBC, 0xF2)
SCREEN_BOT = (0x0A, 0x6F, 0xB5)
BEZEL = (0x21, 0x25, 0x2B)
TEXT = (0x12, 0x14, 0x18)
WHITE = (255, 255, 255)


def _v_gradient(size, top, bottom):
    w, h = size
    base = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        base.putpixel(
            (0, y),
            tuple(round(top[i] + (bottom[i] - top[i]) * t) for i in range(3)),
        )
    return base.resize((w, h))


def _rounded_mask(size, radius):
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    d.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=255)
    return m


def make_icon(px: int) -> Image.Image:
    """Square app icon: a stylized display screen with a signal arc."""
    img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = px / 256.0

    # Rounded bezel filling most of the square.
    bez = [int(20 * s), int(36 * s), int(236 * s), int(196 * s)]
    d.rounded_rectangle(bez, radius=int(28 * s), fill=BEZEL)

    # Screen with vertical gradient.
    sx0, sy0, sx1, sy1 = (
        int(38 * s),
        int(54 * s),
        int(218 * s),
        int(166 * s),
    )
    grad = _v_gradient((sx1 - sx0, sy1 - sy0), SCREEN_TOP, SCREEN_BOT)
    mask = _rounded_mask((sx1 - sx0, sy1 - sy0), int(14 * s))
    img.paste(grad, (sx0, sy0), mask)

    # Diagonal sheen, clipped to the screen's rounded rect.
    sheen = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    ImageDraw.Draw(sheen).polygon(
        [
            (sx0, sy0),
            (sx1, sy0),
            (sx1, sy0 + int(30 * s)),
            (sx0, sy0 + int(70 * s)),
        ],
        fill=(255, 255, 255, 30),
    )
    img.alpha_composite(
        Image.composite(
            sheen,
            Image.new("RGBA", (px, px), (0, 0, 0, 0)),
            _shifted_mask(px, mask, sx0, sy0),
        )
    )

    # Signal arcs + node (LAN control motif), centered on screen.
    cx, cy = int(128 * s), int(150 * s)
    for r, width, alpha in (
        (int(40 * s), int(10 * s), 150),
        (int(24 * s), int(10 * s), 210),
    ):
        d.arc(
            [cx - r, cy - r, cx + r, cy + r],
            start=210,
            end=330,
            fill=(255, 255, 255, alpha),
            width=max(2, width),
        )
    nr = int(8 * s)
    d.ellipse([cx - nr, cy - nr, cx + nr, cy + nr], fill=WHITE)

    # Stand.
    d.rounded_rectangle(
        [int(110 * s), int(196 * s), int(146 * s), int(210 * s)],
        radius=int(4 * s),
        fill=BEZEL,
    )
    d.rounded_rectangle(
        [int(86 * s), int(210 * s), int(170 * s), int(224 * s)],
        radius=int(6 * s),
        fill=(0x2B, 0x2F, 0x36),
    )
    return img


def _shifted_mask(px, mask, ox, oy):
    full = Image.new("L", (px, px), 0)
    full.paste(mask, (ox, oy))
    return full


def _load_font(size: int):
    for name in ("seguisb.ttf", "segoeui.ttf", "arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


LOGO_TEXT = (0x20, 0x28, 0x33)  # dark slate, reads on light backgrounds


def make_logo(scale: int = 1) -> Image.Image:
    """Wide wordmark logo with the icon on the left (transparent background).

    Sized so the wordmark always fits, and drawn in dark slate (HA renders the
    integration logo on a light card). Width stays within the brands limit.
    """
    w, h = 760 * scale, 200 * scale
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    icon = make_icon(int(184 * scale))
    img.alpha_composite(icon, (int(6 * scale), int(8 * scale)))

    d = ImageDraw.Draw(img)
    big = _load_font(int(58 * scale))
    small = _load_font(int(28 * scale))
    tx = int(208 * scale)

    d.text((tx, int(50 * scale)), "NEC MultiSync", font=big, fill=LOGO_TEXT)
    d.text(
        (tx + int(2 * scale), int(120 * scale)),
        "for Home Assistant",
        font=small,
        fill=SCREEN_BOT,
    )
    return img


def main() -> None:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out = os.path.join(root, "custom_components", "nec_multisync", "brand")
    os.makedirs(out, exist_ok=True)
    make_icon(256).save(os.path.join(out, "icon.png"))
    make_icon(512).save(os.path.join(out, "icon@2x.png"))
    make_logo(1).save(os.path.join(out, "logo.png"))
    make_logo(2).save(os.path.join(out, "logo@2x.png"))
    print("wrote brand assets to", out)


if __name__ == "__main__":
    main()
