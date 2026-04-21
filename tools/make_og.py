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
APPLE_OUT = Path("/Users/nayuta/ai/claude-code-book/assets/apple-touch-icon.png")
ICON_512_OUT = Path("/Users/nayuta/ai/claude-code-book/assets/icon-512.png")
OG_CH_DIR = Path("/Users/nayuta/ai/claude-code-book/assets")

# ------- per-chapter info (kept in sync with tools/build.py CHAPTERS) -------
CHAPTERS = [
    {"id": 1,  "en": "Feature Inventory",    "cn": "功能全景清单",             "part": 1},
    {"id": 2,  "en": "Showcase",             "cn": "典型使用场景",             "part": 1},
    {"id": 3,  "en": "Agent Loop",           "cn": "推理·工具循环主引擎",       "part": 2},
    {"id": 4,  "en": "Multi-Agent",          "cn": "Sub-Agent 协程调度",       "part": 2},
    {"id": 5,  "en": "Plan Mode",            "cn": "让 Agent 先想后做",        "part": 2},
    {"id": 6,  "en": "Worktree",             "cn": "隔离模式",                  "part": 2},
    {"id": 7,  "en": "Context",              "cn": "上下文管理与记忆",          "part": 2},
    {"id": 8,  "en": "Tools",                "cn": "Tool 接口与 ToolSearch",   "part": 2},
    {"id": 9,  "en": "Permissions",          "cn": "每次都问却不烦",            "part": 2},
    {"id": 10, "en": "Skills",               "cn": "技能系统",                  "part": 3},
    {"id": 11, "en": "Plugins",              "cn": "插件系统",                  "part": 3},
    {"id": 12, "en": "MCP",                  "cn": "集成与 upstream 代理",      "part": 3},
    {"id": 13, "en": "Cron",                 "cn": "定时任务",                  "part": 3},
    {"id": 14, "en": "Hooks",                "cn": "可编程生命周期",            "part": 3},
    {"id": 15, "en": "Proactive",            "cn": "主动提示而不打扰",          "part": 4},
    {"id": 16, "en": "Background",           "cn": "后台任务",                  "part": 4},
    {"id": 17, "en": "Remote",               "cn": "Sessions 与 Teleport",      "part": 4},
    {"id": 18, "en": "Multi-host",           "cn": "IDE / Chrome / Computer Use", "part": 4},
    {"id": 19, "en": "Buddy",                "cn": "宠物系统",                  "part": 4},
    {"id": 20, "en": "Input",                "cn": "语音 / Vim / 键位",         "part": 4},
    {"id": 21, "en": "Ink UI",               "cn": "终端 UI 背后的工程",        "part": 5},
    {"id": 22, "en": "Observability",        "cn": "成本 / 可观测 / 调试",      "part": 5},
    {"id": 23, "en": "Agent SDK",            "cn": "把 Claude Code 当库用",     "part": 5},
]
PART_NAMES = {
    1: "Overview",   2: "Core Engine",   3: "Extensions",
    4: "Interactions", 5: "Engineering",
}
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}

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

def draw_icon(size: int) -> Image.Image:
    """Draw a square app icon: cream bg + rose book-spine + italic & glyph.
    Designed to read at 40px yet still feel composed at 512px."""
    img = Image.new("RGB", (size, size), CREAM)
    d = ImageDraw.Draw(img)

    # Proportions relative to size
    spine_x0 = int(size * 0.28)
    spine_x1 = int(size * 0.72)
    spine_y0 = int(size * 0.11)
    spine_y1 = int(size * 0.89)
    r = max(2, int(size * 0.035))

    # Rose spine with light inner dividers near each edge
    d.rounded_rectangle(
        (spine_x0, spine_y0, spine_x1, spine_y1),
        radius=r,
        fill=ROSE,
    )
    divider_inset = max(2, int(size * 0.03))
    dim_cream = (250, 240, 240, 140)
    overlay = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    od.line(
        [(spine_x0 + divider_inset, spine_y0 + r),
         (spine_x0 + divider_inset, spine_y1 - r)],
        fill=dim_cream, width=max(1, int(size * 0.008)),
    )
    od.line(
        [(spine_x1 - divider_inset, spine_y0 + r),
         (spine_x1 - divider_inset, spine_y1 - r)],
        fill=dim_cream, width=max(1, int(size * 0.008)),
    )
    img.paste(overlay, (0, 0), overlay)

    # italic ampersand centered on spine
    # pick font size ~50% of icon height
    f = load(FONT_LATIN_BOLD, int(size * 0.5))
    amp = "&"
    bbox = d.textbbox((0, 0), amp, font=f)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (size - th) // 2 - bbox[1] - int(size * 0.02)
    d.text((tx, ty), amp, font=f, fill=CREAM)
    return img

def make_app_icons() -> None:
    APPLE_OUT.parent.mkdir(parents=True, exist_ok=True)
    draw_icon(180).save(APPLE_OUT, format="PNG", optimize=True)
    print(f"  wrote {APPLE_OUT}  ({APPLE_OUT.stat().st_size // 1024} KB)")
    draw_icon(512).save(ICON_512_OUT, format="PNG", optimize=True)
    print(f"  wrote {ICON_512_OUT}  ({ICON_512_OUT.stat().st_size // 1024} KB)")

def draw_chapter_og(ch: dict) -> Image.Image:
    """Per-chapter 1200x630 social card: big italic chapter number on the
    right, English title + Chinese title on the left, part eyebrow up top."""
    img = Image.new("RGB", (W, H), CREAM)

    # same warm glows as the main OG
    blush = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bd = ImageDraw.Draw(blush)
    for r, a in [(420, 28), (300, 48), (180, 70)]:
        bd.ellipse((80 - r, -60 - r, 80 + r, -60 + r), fill=(235, 190, 210, a))
    for r, a in [(440, 26), (320, 42), (180, 60)]:
        bd.ellipse((W + 40 - r, H - 40 - r, W + 40 + r, H - 40 + r),
                   fill=(238, 220, 195, a))
    img.paste(blush, (0, 0), blush)

    d = ImageDraw.Draw(img)

    # inset border
    d.rectangle((28, 28, W - 28, H - 28), outline=MIST, width=1)

    # eyebrow: "PART II · CORE ENGINE · CHAPTER 03"
    f_eye = load(FONT_CJK_SANS, 20, index=1)
    eyebrow = f"PART {ROMAN[ch['part']]}  ·  {PART_NAMES[ch['part']].upper()}  ·  CHAPTER {ch['id']:02d}"
    d.text((70, 74), eyebrow, font=f_eye, fill=ROSE)

    # English chapter name — big italic, wraps if long
    f_en = load(FONT_LATIN_IT, 122)
    max_w = 680
    # naive wrap: break on space if too wide
    words = ch["en"].split()
    lines = []
    buf = ""
    for w in words:
        test = (buf + " " + w).strip()
        if d.textlength(test, font=f_en) <= max_w:
            buf = test
        else:
            if buf: lines.append(buf)
            buf = w
    if buf: lines.append(buf)
    lh = 120
    y0 = 128
    for i, line in enumerate(lines[:2]):
        d.text((68, y0 + i * lh), line, font=f_en, fill=INK)

    # Chinese chapter topic (subtitle)
    f_cn = load(FONT_CJK_SERIF, 46, index=3)
    d.text((68, y0 + len(lines) * lh + 12), ch["cn"], font=f_cn, fill=CHARCOAL)

    # Meta row at bottom
    f_meta = load(FONT_CJK_SANS, 18, index=1)
    meta = f"ch.{ch['id']:02d} / 23      ·      nayuta403.github.io/claude-code-book"
    d.text((70, H - 76), meta, font=f_meta, fill=ASH)

    # Right — BIG italic chapter number
    f_num = load(FONT_LATIN_IT, 400)
    num_text = f"{ch['id']:02d}"
    tw = d.textlength(num_text, font=f_num)
    nx = W - 70 - tw
    ny = 150
    # First digit ink, second rose
    digits = list(num_text)
    w_a = d.textlength(digits[0], font=f_num)
    d.text((nx, ny), digits[0], font=f_num, fill=INK)
    d.text((nx + w_a, ny), digits[1], font=f_num, fill=ROSE)

    # Small vertical label next to the numeral
    f_cap = load(FONT_CJK_SANS, 15, index=1)
    cap = "CHAPTER · SOURCE READING · CLAUDE CODE"
    sub = Image.new("RGBA", (620, 32), (0, 0, 0, 0))
    ImageDraw.Draw(sub).text((0, 0), cap, font=f_cap, fill=ASH)
    sub = sub.rotate(90, expand=True, resample=Image.BICUBIC)
    img.paste(sub, (W - 92, 5), sub)

    return img

def make_chapter_ogs() -> None:
    OG_CH_DIR.mkdir(parents=True, exist_ok=True)
    for ch in CHAPTERS:
        out = OG_CH_DIR / f"og-ch{ch['id']:02d}.png"
        draw_chapter_og(ch).save(out, format="PNG", optimize=True)
        print(f"  wrote {out.name}  ({out.stat().st_size // 1024} KB)")

if __name__ == "__main__":
    main()
    make_app_icons()
    make_chapter_ogs()
