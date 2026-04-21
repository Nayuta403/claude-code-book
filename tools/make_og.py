#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_og.py — generate a 1200x630 social preview card.

Output: /Users/nayuta/ai/claude-code-book/assets/og.png

Uses system fonts:
- Georgia Italic (Latin display)
- Songti.ttc (Chinese serif)
- PingFang.ttc (Chinese sans for eyebrow)
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT = Path("/Users/nayuta/ai/claude-code-book/assets/og.png")

FONT_LATIN_IT = "/System/Library/Fonts/Supplemental/Georgia Italic.ttf"
FONT_LATIN_BOLD = "/System/Library/Fonts/Supplemental/Georgia Bold Italic.ttf"
FONT_CJK_SERIF = "/System/Library/Fonts/Supplemental/Songti.ttc"
FONT_CJK_SANS  = "/System/Library/Fonts/PingFang.ttc"

W, H = 1200, 630

# D palette converted to sRGB (approximate OKLCH)
# oklch(96% 0.005 350) -> warm cream
# oklch(10% 0 0)       -> near-black ink
# oklch(25% 0 0)       -> charcoal
# oklch(55% 0 0)       -> ash
# oklch(60% 0.25 350)  -> rose magenta
CREAM    = (245, 238, 240)
INK      = (19, 19, 20)
CHARCOAL = (61, 60, 61)
ASH      = (137, 134, 135)
MIST     = (228, 223, 224)
ROSE     = (221, 75, 142)
ROSE_MIST = (238, 208, 222)

def load(path: str, size: int, index: int | None = None) -> ImageFont.FreeTypeFont:
    try:
        if index is not None:
            return ImageFont.truetype(path, size, index=index)
        return ImageFont.truetype(path, size)
    except (OSError, IOError) as e:
        print(f"  ! fallback: could not load {path}: {e}")
        return ImageFont.load_default()

def main() -> None:
    img = Image.new("RGB", (W, H), CREAM)

    # subtle warm blush top-left and bottom-right, simulating radial gradients
    blush = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(blush)
    # top-left light pink glow
    for r, alpha in [(420, 28), (300, 48), (180, 70)]:
        bd.ellipse((80 - r, -60 - r, 80 + r, -60 + r),
                   fill=(235, 190, 210, alpha))
    # bottom-right warm amber glow
    for r, alpha in [(440, 26), (320, 42), (180, 60)]:
        bd.ellipse((W + 40 - r, H - 40 - r, W + 40 + r, H - 40 + r),
                   fill=(238, 220, 195, alpha))
    img.paste(blush, (0, 0), blush)

    d = ImageDraw.Draw(img)

    # outer border — a 1px mist line inset from edges
    inset = 28
    d.rectangle((inset, inset, W - inset, H - inset), outline=MIST, width=1)

    # eyebrow
    f_eye = load(FONT_CJK_SANS, 20, index=1)  # PingFang index 1 ~ Regular
    eyebrow = "VOL. I  —  ENGINEERING MONOGRAPH  —  2026"
    d.text((70, 74), eyebrow, font=f_eye, fill=ROSE)

    # Big italic title — "Claude & Code"
    f_title = load(FONT_LATIN_IT, 134)
    line1 = "Claude "
    ampersand = "&"
    line1b = " Code"
    x0, y0 = 68, 126
    # Measure for ampersand rose colour
    w1 = d.textlength(line1, font=f_title)
    w_amp = d.textlength(ampersand, font=f_title)
    d.text((x0, y0), line1, font=f_title, fill=INK)
    d.text((x0 + w1, y0), ampersand, font=f_title, fill=ROSE)
    d.text((x0 + w1 + w_amp, y0), line1b, font=f_title, fill=INK)

    # Subtitle "源码解读" in Chinese serif
    f_sub = load(FONT_CJK_SERIF, 64, index=3)  # Songti.ttc index 3 ~ Regular
    d.text((x0, y0 + 148), "源码解读", font=f_sub, fill=CHARCOAL)

    # Lead line (kept short so it doesn't collide with the "23" numeral)
    f_lead = load(FONT_CJK_SANS, 22, index=3)  # PingFang Regular
    lead = "二十三章深读一个十万行的终端 agent。"
    d.text((x0, y0 + 240), lead, font=f_lead, fill=CHARCOAL)

    # Meta row at bottom
    f_meta = load(FONT_CJK_SANS, 18, index=1)
    meta = "23 章   ·   约 15,000 行   ·   简体中文   ·   nayuta403.github.io/claude-code-book"
    d.text((70, H - 76), meta, font=f_meta, fill=ASH)

    # Right side — big italic "23" numeral, partially fading
    f_num = load(FONT_LATIN_IT, 340)
    num_text = "23"
    tw = d.textlength(num_text, font=f_num)
    nx = W - 80 - tw
    ny = 130
    # Split: "2" in ink, "3" in rose (echoes the site hero)
    w_2 = d.textlength("2", font=f_num)
    d.text((nx, ny), "2", font=f_num, fill=INK)
    d.text((nx + w_2, ny), "3", font=f_num, fill=ROSE)

    # A small vertical caption beside the numeral
    f_cap = load(FONT_CJK_SANS, 16, index=1)
    cap = "CHAPTERS · FIVE PARTS · ONE BOOK"
    # draw at angle: use a rotated text-only sub-image
    sub = Image.new("RGBA", (620, 36), (0, 0, 0, 0))
    ImageDraw.Draw(sub).text((0, 0), cap, font=f_cap, fill=ASH)
    sub = sub.rotate(90, expand=True, resample=Image.BICUBIC)
    img.paste(sub, (W - 92, 5), sub)

    # Save
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img.save(OUT, format="PNG", optimize=True)
    print(f"  wrote {OUT}  ({OUT.stat().st_size // 1024} KB)")

if __name__ == "__main__":
    main()
