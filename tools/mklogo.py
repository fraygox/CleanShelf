#!/usr/bin/env python3
"""Text wordmarks for systems that have no logo art, in the theme's own house style
(the PORTS / FAVORITES / "Sheezie2Clean" logos): a small label over one heavy
Fira Sans Black word with a vertical gradient in the system's colour.

    mklogo.py OUTDIR "Big Name" "Small label" RRGGBB [RRGGBB-end]

Writes the four variants the theme expects per system folder:
    logo.png   colour gradient, black label        (light mode carousel)
    logo2.png  all black                           (light mode gamelist header)
    logo3.png  all white                           (dark mode gamelist header)
    logo4.png  colour gradient, white label        (dark mode carousel)
Nothing here is traced from any trademark: it is type set in Fira Sans (OFL).
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "..", "_inc", "fonts")
W, H = 1200, 400          # same aspect family as the theme's own wordmarks (3:1)
PAD = 20


def hexrgb(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def rgbhex(c):
    return "%02X%02X%02X" % c


def lighten(c, f):
    return tuple(min(255, int(v + (255 - v) * f)) for v in c)


def darken(c, f):
    return tuple(int(v * (1 - f)) for v in c)


def fit_lines(text, font_path, max_w, max_h):
    """Biggest font size at which the uppercase name fits on one line, or two
    lines when one would have to go under 150 px."""
    words = text.upper().split()
    for lines in ([" ".join(words)], two_lines(words)):
        if lines is None:
            continue
        lo, hi = 40, 330
        while lo < hi:
            mid = (lo + hi + 1) // 2
            f = ImageFont.truetype(font_path, mid)
            widths = [f.getlength(l) for l in lines]
            asc, desc = f.getmetrics()
            if max(widths) <= max_w and len(lines) * asc * 0.98 <= max_h:
                lo = mid
            else:
                hi = mid - 1
        if lo >= 150 or len(lines) == 2:
            return lines, lo
    return lines, lo


def two_lines(words):
    if len(words) < 2:
        return None
    best, bestdiff = None, 1e9
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        d = abs(len(a) - len(b))
        if d < bestdiff:
            best, bestdiff = [a, b], d
    return best


def gradient(size, top, bottom):
    g = Image.new("RGBA", size)
    px = g.load()
    w, h = size
    for y in range(h):
        t = y / max(1, h - 1)
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3)) + (255,)
        for x in range(w):
            px[x, y] = c
    return g


def render(out, name, label, word_fill, label_fill):
    """word_fill: RGB or (top, bottom) gradient pair; label_fill: RGB."""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    black = os.path.join(FONTS, "FiraSans-Black.ttf")
    bold = os.path.join(FONTS, "FiraSans-Bold.ttf")
    label_font = ImageFont.truetype(bold, 64) if label else None
    label_h = 78 if label else 0
    lines, size = fit_lines(name, black, W - 2 * PAD, H - 2 * PAD - label_h)
    font = ImageFont.truetype(black, size)
    asc, desc = font.getmetrics()
    line_h = int(asc * 0.98)
    block_h = label_h + line_h * len(lines)
    y = (H - block_h) // 2
    if label:
        lw = label_font.getlength(label)
        draw.text(((W - lw) / 2, y), label, font=label_font, fill=label_fill + (255,))
        y += label_h
    mask = Image.new("L", (W, H), 0)
    mdraw = ImageDraw.Draw(mask)
    for l in lines:
        lw = font.getlength(l)
        mdraw.text(((W - lw) / 2, y - asc * 0.18), l, font=font, fill=255)
        y += line_h
    if isinstance(word_fill[0], tuple):
        fill = gradient((W, H), *word_fill)
    else:
        fill = Image.new("RGBA", (W, H), word_fill + (255,))
    img.paste(fill, (0, 0), mask)
    img.save(out)


def make_set(outdir, name, label, color, color_end=None):
    os.makedirs(outdir, exist_ok=True)
    c = hexrgb(color)
    top = lighten(c, 0.18)
    bottom = hexrgb(color_end) if color_end else darken(c, 0.35)
    render(os.path.join(outdir, "logo.png"), name, label, (top, bottom), (0, 0, 0))
    render(os.path.join(outdir, "logo2.png"), name, label, (0, 0, 0), (0, 0, 0))
    render(os.path.join(outdir, "logo3.png"), name, label, (255, 255, 255), (255, 255, 255))
    render(os.path.join(outdir, "logo4.png"), name, label, (lighten(c, 0.3), bottom), (255, 255, 255))


if __name__ == "__main__":
    if len(sys.argv) < 5:
        sys.exit(__doc__)
    make_set(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] if len(sys.argv) > 5 else None)
