#!/usr/bin/env python3
"""pygame/bg.png: the right-half system art for the Pygame / RomM-o-Cera system, drawn
from scratch (no third-party artwork): a violet field in RomM-o-Cera's palette, a soft
glow and the app's own R icon (romm-o-cera/icon.png, same author).

    mkbg-pygame.py /path/to/romm-o-cera/icon.png
"""
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1980, 1080                      # same canvas as the theme's other bg.png files
X0 = int(W * 0.5455)                   # art occupies the right of the page like every other system
VIOLET, INK, HI = (139, 92, 246), (28, 25, 54), (183, 160, 255)


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def main(icon_path):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    px = img.load()
    for y in range(H):
        for x in range(X0, W):
            t = ((x - X0) / (W - X0)) * 0.55 + (y / H) * 0.45
            px[x, y] = lerp(VIOLET, INK, t) + (255,)
    # soft glow behind the icon
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    cx, cy = X0 + (W - X0) // 2, H // 2 - 40
    g.ellipse((cx - 330, cy - 330, cx + 330, cy + 330), fill=HI + (120,))
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    glow.paste((0, 0, 0, 0), (0, 0, X0, H))   # keep the glow inside the panel (left half stays transparent)
    img.alpha_composite(glow)
    # faint tile grid: the app's game tiles, as texture
    tiles = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(tiles)
    tw, th, gap = 150, 200, 22
    for row in range(-1, 7):
        for col in range(-1, 8):
            x = X0 + 60 + col * (tw + gap) + (row % 2) * (tw // 2)
            y = -80 + row * (th + gap)
            d.rounded_rectangle((x, y, x + tw, y + th), radius=14, outline=(255, 255, 255, 26), width=3)
    img.alpha_composite(tiles)
    icon = Image.open(icon_path).convert("RGBA")
    icon = icon.resize((440, 440), Image.LANCZOS)
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 110), (cx - 220 + 12, cy - 220 + 18, cx + 220 + 12, cy + 220 + 18), icon)
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(18)))
    img.alpha_composite(icon, (cx - 220, cy - 220))
    font = ImageFont.truetype(os.path.join(HERE, "..", "_inc", "fonts", "FiraSans-Bold.ttf"), 44)
    d = ImageDraw.Draw(img)
    label = "RomM-o-Cera"
    lw = font.getlength(label)
    d.text((cx - lw / 2, cy + 275), label, font=font, fill=(242, 239, 255, 255))
    sub = "your RomM library, on this box"
    font2 = ImageFont.truetype(os.path.join(HERE, "..", "_inc", "fonts", "FiraSans-Regular.ttf"), 30)
    lw = font2.getlength(sub)
    d.text((cx - lw / 2, cy + 335), sub, font=font2, fill=(183, 160, 255, 255))
    # the page's bottom black help bar overlaps the last ~5%: leave that opaque too (ES draws over it)
    img.save(os.path.join(HERE, "..", "pygame", "bg.png"))


if __name__ == "__main__":
    main(sys.argv[1])
