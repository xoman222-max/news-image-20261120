#!/usr/bin/env python3
"""news-image-20261120: draw a one-day world news front page (1024x1024 PNG).

Reads stories.json (50 stories for Friday 20 November 2026, each verified
against its first-report date) and renders entry.png. Pure PIL, no network,
deterministic: same input -> byte-identical PNG.

Layout follows the winning front-page formula: giant date header, UTC
timeline, 4x4 featured grid with flat vector pictograms, world map with
numbered pins, ALSO ON list, DATE CHECK bar, footer with sources.
Every pictogram is drawn by code; no photographs anywhere.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024
M = 26  # outer margin
PAPER = (247, 243, 233)
INK = (26, 26, 26)
RED = (158, 28, 28)
RED_DARK = (120, 20, 20)
GREY = (110, 105, 92)
RULE = (60, 55, 45)
PANEL = (238, 232, 216)
MAP_OCEAN = (205, 224, 231)
MAP_LAND = (233, 224, 200)
MAP_LINE = (172, 160, 128)
YELLOW = (217, 164, 32)
GREEN = (46, 125, 50)
BLUE = (31, 78, 121)

FONT_DIR = "/usr/share/fonts/truetype"
SERIF_B = f"{FONT_DIR}/dejavu/DejaVuSerif-Bold.ttf"
SERIF = f"{FONT_DIR}/dejavu/DejaVuSerif.ttf"
SANS = f"{FONT_DIR}/dejavu/DejaVuSans.ttf"
SANS_B = f"{FONT_DIR}/dejavu/DejaVuSans-Bold.ttf"

_cache = {}


def font(path, size):
    key = (path, size)
    if key not in _cache:
        _cache[key] = ImageFont.truetype(path, size)
    return _cache[key]


def text_w(d, xy, s, f, fill=INK):
    d.text(xy, s, font=f[0], fill=fill) if isinstance(f, tuple) else d.text(xy, s, font=f, fill=fill)


def wrap(d, text, f, width):
    """Greedy word wrap; returns list of lines fitting width."""
    words = text.split()
    lines, cur = [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=f) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_lines(d, text, f, width, max_lines):
    """Wrap text; return (lines, overflow_bool)."""
    lines = wrap(d, text, f, width)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        # trim last line and add ellipsis
        while lines and d.textlength(lines[-1] + " ...", font=f) > width:
            lines[-1] = lines[-1][:-1]
        lines[-1] = lines[-1] + " ..."
        return lines, True
    return lines, False


def draw_wrapped(d, text, f, x, y, width, max_lines, leading, fill=INK):
    lines, overflow = fit_lines(d, text, f, width, max_lines)
    for i, ln in enumerate(lines):
        d.text((x, y + i * leading), ln, font=f, fill=fill)
    return overflow


# ---------------------------------------------------------------- icons
# Each icon draws a flat pictogram inside a box (x, y, s). INK outlines,
# RED/YELLOW/GREEN/BLUE accents. All original drawings, no images.

def _circle(d, cx, cy, r, fill=None, outline=INK, width=2):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill, outline=outline, width=width)


def icon_climate(d, x, y, s):
    cx, cy = x + s * 0.38, y + s * 0.38
    r = s * 0.22
    for a in range(0, 360, 45):
        import math
        x1 = cx + math.cos(math.radians(a)) * (r + 2)
        y1 = cy + math.sin(math.radians(a)) * (r + 2)
        x2 = cx + math.cos(math.radians(a)) * (r + s * 0.14)
        y2 = cy + math.sin(math.radians(a)) * (r + s * 0.14)
        d.line([x1, y1, x2, y2], fill=YELLOW, width=2)
    _circle(d, cx, cy, r, fill=YELLOW, outline=YELLOW)
    d.ellipse([x + s * 0.45, y + s * 0.62, x + s * 0.95, y + s * 0.85], fill=(255, 255, 255), outline=INK, width=2)
    d.ellipse([x + s * 0.55, y + s * 0.52, x + s * 0.85, y + s * 0.70], fill=(255, 255, 255), outline=INK, width=2)


def icon_parliament(d, x, y, s):
    d.polygon([(x + s * 0.08, y + s * 0.34), (x + s * 0.5, y + s * 0.08), (x + s * 0.92, y + s * 0.34)], fill=RED)
    d.rectangle([x + s * 0.12, y + s * 0.36, x + s * 0.88, y + s * 0.42], fill=INK)
    for cx in (0.22, 0.38, 0.54, 0.70, 0.84):
        d.rectangle([x + s * cx - 2, y + s * 0.44, x + s * cx + 2, y + s * 0.78], fill=INK)
    d.rectangle([x + s * 0.08, y + s * 0.80, x + s * 0.92, y + s * 0.88], fill=INK)


def icon_globe(d, x, y, s):
    cx, cy, r = x + s / 2, y + s / 2, s * 0.42
    _circle(d, cx, cy, r, fill=(255, 255, 255), outline=INK, width=2)
    d.ellipse([cx - r * 0.45, cy - r, cx + r * 0.45, cy + r], outline=INK, width=1)
    d.line([cx - r, cy, cx + r, cy], fill=INK, width=1)
    d.arc([cx - r, cy - r * 0.45, cx + r, cy + r * 0.45], 0, 360, fill=INK, width=1)


def icon_virus(d, x, y, s):
    cx, cy, r = x + s / 2, y + s / 2, s * 0.26
    import math
    for a in range(0, 360, 30):
        x1 = cx + math.cos(math.radians(a)) * r
        y1 = cy + math.sin(math.radians(a)) * r
        x2 = cx + math.cos(math.radians(a)) * (r + s * 0.16)
        y2 = cy + math.sin(math.radians(a)) * (r + s * 0.16)
        d.line([x1, y1, x2, y2], fill=INK, width=2)
        _circle(d, x2, y2, 2, fill=RED, outline=RED)
    _circle(d, cx, cy, r, fill=RED, outline=RED)
    _circle(d, cx - r * 0.35, cy - r * 0.3, 2, fill=(255, 255, 255), outline=(255, 255, 255))
    _circle(d, cx + r * 0.4, cy + r * 0.35, 2, fill=(255, 255, 255), outline=(255, 255, 255))


def icon_chip(d, x, y, s):
    d.rectangle([x + s * 0.22, y + s * 0.22, x + s * 0.78, y + s * 0.78], fill=BLUE, outline=INK, width=2)
    d.rectangle([x + s * 0.38, y + s * 0.38, x + s * 0.62, y + s * 0.62], fill=(255, 255, 255), outline=INK, width=2)
    for i in range(3):
        t = 0.32 + i * 0.18
        d.line([x + s * t, y + s * 0.10, x + s * t, y + s * 0.22], fill=INK, width=2)
        d.line([x + s * t, y + s * 0.78, x + s * t, y + s * 0.90], fill=INK, width=2)
        d.line([x + s * 0.10, y + s * t, x + s * 0.22, y + s * t], fill=INK, width=2)
        d.line([x + s * 0.78, y + s * t, x + s * 0.90, y + s * t], fill=INK, width=2)


def icon_protest(d, x, y, s):
    _circle(d, x + s * 0.30, y + s * 0.24, s * 0.10, fill=INK, outline=INK)
    d.polygon([(x + s * 0.20, y + s * 0.88), (x + s * 0.40, y + s * 0.88), (x + s * 0.36, y + s * 0.38), (x + s * 0.24, y + s * 0.38)], fill=INK)
    d.rectangle([x + s * 0.48, y + s * 0.12, x + s * 0.92, y + s * 0.42], fill=(255, 255, 255), outline=RED, width=2)
    d.line([x + s * 0.70, y + s * 0.42, x + s * 0.70, y + s * 0.88], fill=INK, width=2)
    d.line([x + s * 0.55, y + s * 0.22, x + s * 0.85, y + s * 0.22], fill=RED, width=2)
    d.line([x + s * 0.55, y + s * 0.32, x + s * 0.85, y + s * 0.32], fill=RED, width=2)


def icon_tent(d, x, y, s):
    d.polygon([(x + s * 0.5, y + s * 0.10), (x + s * 0.06, y + s * 0.85), (x + s * 0.94, y + s * 0.85)], fill=(255, 255, 255), outline=INK, width=2)
    d.polygon([(x + s * 0.5, y + s * 0.42), (x + s * 0.34, y + s * 0.85), (x + s * 0.66, y + s * 0.85)], fill=RED)
    d.line([x, y + s * 0.88, x + s, y + s * 0.88], fill=INK, width=2)


def icon_summit(d, x, y, s):
    for i, col in enumerate((RED, BLUE, GREEN)):
        px = x + s * (0.22 + i * 0.28)
        d.line([px, y + s * 0.14, px, y + s * 0.88], fill=INK, width=2)
        d.polygon([(px, y + s * 0.14), (px + s * 0.24, y + s * 0.24), (px, y + s * 0.34)], fill=col)


def icon_capitol(d, x, y, s):
    d.pieslice([x + s * 0.32, y + s * 0.06, x + s * 0.68, y + s * 0.42], 180, 360, fill=RED)
    d.rectangle([x + s * 0.48, y, x + s * 0.52, y + s * 0.10], fill=INK)
    d.rectangle([x + s * 0.14, y + s * 0.42, x + s * 0.86, y + s * 0.48], fill=INK)
    for cx in (0.24, 0.40, 0.56, 0.72):
        d.rectangle([x + s * cx - 2, y + s * 0.50, x + s * cx + 2, y + s * 0.80], fill=INK)
    d.rectangle([x + s * 0.10, y + s * 0.82, x + s * 0.90, y + s * 0.90], fill=INK)


def icon_cyclone(d, x, y, s):
    cx, cy = x + s / 2, y + s / 2
    for r, start in ((s * 0.40, 20), (s * 0.28, 200), (s * 0.16, 20)):
        d.arc([cx - r, cy - r, cx + r, cy + r], start, start + 270, fill=BLUE, width=3)
    _circle(d, cx, cy, 3, fill=RED, outline=RED)


def icon_court(d, x, y, s):
    d.line([x + s * 0.5, y + s * 0.10, x + s * 0.5, y + s * 0.86], fill=INK, width=2)
    d.line([x + s * 0.16, y + s * 0.22, x + s * 0.84, y + s * 0.22], fill=INK, width=2)
    d.line([x + s * 0.06, y + s * 0.88, x + s * 0.94, y + s * 0.88], fill=INK, width=2)
    for cx in (0.22, 0.78):
        d.line([x + s * cx, y + s * 0.22, x + s * cx, y + s * 0.38], fill=INK, width=2)
        d.polygon([(x + s * (cx - 0.14), y + s * 0.38), (x + s * (cx + 0.14), y + s * 0.38), (x + s * cx, y + s * 0.58)], fill=YELLOW, outline=INK)


def icon_chart(d, x, y, s):
    d.line([x + s * 0.08, y + s * 0.88, x + s * 0.92, y + s * 0.88], fill=INK, width=2)
    d.line([x + s * 0.08, y + s * 0.88, x + s * 0.08, y + s * 0.08], fill=INK, width=2)
    for i, h in enumerate((0.30, 0.50, 0.72)):
        bx = x + s * (0.20 + i * 0.26)
        d.rectangle([bx, y + s * (0.88 - h), bx + s * 0.16, y + s * 0.88], fill=(RED, YELLOW, GREEN)[i], outline=INK, width=1)


def icon_football(d, x, y, s):
    cx, cy, r = x + s / 2, y + s / 2, s * 0.42
    _circle(d, cx, cy, r, fill=(255, 255, 255), outline=INK, width=2)
    d.polygon([(cx, cy - r * 0.4), (cx + r * 0.38, cy - r * 0.12), (cx + r * 0.24, cy + r * 0.32), (cx - r * 0.24, cy + r * 0.32), (cx - r * 0.38, cy - r * 0.12)], fill=INK)
    import math
    for a in (90, 162, 234, 306, 18):
        x1 = cx + math.cos(math.radians(a)) * r * 0.55
        y1 = cy - math.sin(math.radians(a)) * r * 0.55
        x2 = cx + math.cos(math.radians(a)) * r * 0.95
        y2 = cy - math.sin(math.radians(a)) * r * 0.95
        d.line([x1, y1, x2, y2], fill=INK, width=1)


def icon_drought(d, x, y, s):
    _circle(d, x + s * 0.30, y + s * 0.26, s * 0.16, fill=YELLOW, outline=YELLOW)
    d.line([x + s * 0.05, y + s * 0.72, x + s * 0.95, y + s * 0.72], fill=INK, width=2)
    d.line([x + s * 0.20, y + s * 0.72, x + s * 0.30, y + s * 0.86], fill=INK, width=1)
    d.line([x + s * 0.45, y + s * 0.72, x + s * 0.40, y + s * 0.86], fill=INK, width=1)
    d.line([x + s * 0.70, y + s * 0.72, x + s * 0.78, y + s * 0.86], fill=INK, width=1)
    d.line([x + s * 0.30, y + s * 0.86, x + s * 0.40, y + s * 0.86], fill=INK, width=1)


def icon_march(d, x, y, s):
    for i, cx in enumerate((0.22, 0.50, 0.78)):
        _circle(d, x + s * cx, y + s * 0.22, s * 0.09, fill=INK, outline=INK)
        d.polygon([(x + s * (cx - 0.09), y + s * 0.88), (x + s * (cx + 0.09), y + s * 0.88), (x + s * (cx + 0.06), y + s * 0.36), (x + s * (cx - 0.06), y + s * 0.36)], fill=(RED, INK, BLUE)[i])


def icon_gavel(d, x, y, s):
    d.polygon([(x + s * 0.18, y + s * 0.22), (x + s * 0.62, y + s * 0.06), (x + s * 0.70, y + s * 0.18), (x + s * 0.26, y + s * 0.34)], fill=INK)
    d.polygon([(x + s * 0.30, y + s * 0.40), (x + s * 0.74, y + s * 0.24), (x + s * 0.82, y + s * 0.36), (x + s * 0.38, y + s * 0.52)], fill=RED)
    d.line([x + s * 0.52, y + s * 0.34, x + s * 0.86, y + s * 0.82], fill=INK, width=3)
    d.line([x + s * 0.10, y + s * 0.86, x + s * 0.90, y + s * 0.86], fill=INK, width=2)


ICONS = {
    "climate": icon_climate, "parliament": icon_parliament, "globe": icon_globe,
    "virus": icon_virus, "chip": icon_chip, "protest": icon_protest,
    "tent": icon_tent, "summit": icon_summit, "capitol": icon_capitol,
    "cyclone": icon_cyclone, "court": icon_court, "chart": icon_chart,
    "football": icon_football, "drought": icon_drought, "march": icon_march,
    "gavel": icon_gavel,
}

# ---------------------------------------------------------------- map
# Rough stylised continent outlines (lon, lat). Equirectangular projection.

NORTH_AMERICA = [(-168, 66), (-165, 60), (-158, 58), (-152, 60), (-140, 60), (-135, 57), (-130, 54), (-125, 49), (-124, 42), (-120, 34), (-114, 29), (-110, 24), (-105, 20), (-97, 16), (-94, 17), (-90, 14), (-86, 12), (-83, 9), (-80, 8), (-79, 9), (-82, 10), (-85, 11), (-87, 13), (-88, 15), (-90, 18), (-91, 19), (-96, 19), (-97, 22), (-97, 26), (-93, 30), (-89, 30), (-84, 30), (-81, 25), (-80, 32), (-76, 35), (-74, 40), (-70, 42), (-68, 45), (-65, 44), (-60, 46), (-55, 47), (-53, 50), (-55, 52), (-60, 55), (-65, 58), (-68, 55), (-72, 58), (-78, 62), (-85, 66), (-92, 66), (-95, 69), (-110, 68), (-125, 70), (-140, 70), (-155, 71), (-162, 70), (-168, 66)]
GREENLAND = [(-58, 64), (-52, 60), (-44, 60), (-40, 64), (-32, 68), (-22, 70), (-20, 74), (-25, 78), (-35, 80), (-50, 80), (-58, 76), (-60, 70), (-58, 64)]
SOUTH_AMERICA = [(-79, 9), (-77, 7), (-72, 11), (-64, 10), (-60, 8), (-55, 6), (-52, 4), (-50, 0), (-44, -3), (-38, -5), (-35, -8), (-38, -15), (-40, -20), (-48, -25), (-52, -32), (-57, -38), (-62, -41), (-65, -45), (-68, -50), (-70, -53), (-73, -50), (-73, -44), (-72, -37), (-70, -30), (-70, -23), (-75, -18), (-78, -10), (-80, -6), (-81, -3), (-80, 1), (-79, 5), (-79, 9)]
AFRICA = [(-6, 35), (-10, 31), (-15, 27), (-17, 21), (-17, 15), (-15, 11), (-12, 8), (-8, 5), (-4, 5), (0, 6), (6, 4), (9, 4), (12, -1), (13, -5), (12, -10), (13, -15), (12, -18), (14, -22), (16, -27), (18, -30), (20, -35), (26, -34), (31, -29), (33, -26), (35, -22), (36, -18), (40, -15), (40, -11), (42, -5), (46, -1), (51, 2), (51, 10), (48, 11), (44, 11), (40, 15), (38, 18), (37, 22), (35, 28), (32, 31), (30, 31), (25, 32), (20, 32), (15, 32), (10, 34), (10, 37), (5, 37), (0, 36), (-6, 35)]
EURASIA = [(-10, 36), (-9, 43), (-2, 49), (0, 51), (5, 53), (8, 57), (12, 56), (18, 56), (21, 58), (24, 60), (21, 64), (18, 68), (25, 71), (32, 70), (40, 68), (50, 69), (60, 69), (70, 72), (80, 73), (90, 75), (100, 76), (110, 74), (120, 73), (130, 72), (140, 72), (150, 70), (158, 66), (162, 60), (158, 52), (150, 59), (142, 55), (140, 50), (135, 44), (130, 42), (127, 39), (122, 38), (120, 32), (115, 28), (110, 22), (105, 18), (100, 14), (98, 10), (100, 6), (103, 1), (105, -3), (110, -5), (115, -8), (120, -10), (125, -8), (130, -4), (135, -2), (140, -3), (145, -8), (150, -12), (155, -18), (160, -22), (165, -28), (170, -33), (175, -38), (178, -40), (172, -42), (168, -40), (165, -38), (160, -35), (155, -33), (150, -30), (145, -28), (140, -25), (135, -22), (130, -20), (125, -18), (120, -15), (115, -12), (110, -10), (105, -8), (100, -6), (95, -4), (90, -2), (85, 0), (80, 5), (75, 8), (72, 12), (70, 16), (68, 20), (65, 24), (60, 25), (57, 26), (54, 26), (52, 28), (50, 29), (48, 30), (45, 32), (42, 35), (40, 38), (38, 40), (36, 36), (33, 36), (30, 36), (27, 37), (23, 36), (20, 38), (18, 40), (15, 42), (12, 44), (10, 44), (8, 44), (5, 43), (3, 42), (0, 40), (-2, 37), (-6, 36), (-10, 36)]
UK = [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51), (-3, 50), (-5, 50)]
JAPAN = [(130, 31), (132, 33), (135, 34), (137, 35), (139, 36), (140, 38), (141, 40), (142, 42), (143, 44), (144, 44), (142, 42), (140, 40), (139, 37), (137, 35), (134, 34), (131, 32), (130, 31)]
AUSTRALIA = [(113, -22), (114, -28), (115, -32), (118, -35), (124, -33), (129, -32), (132, -32), (135, -35), (137, -35), (140, -38), (145, -38), (150, -37), (153, -32), (153, -27), (150, -22), (146, -19), (142, -15), (142, -11), (140, -17), (136, -15), (135, -12), (132, -11), (130, -13), (126, -14), (122, -17), (118, -20), (113, -22)]
NEW_ZEALAND = [(167, -45), (170, -43), (173, -41), (175, -38), (177, -38), (175, -40), (173, -42), (170, -44), (167, -45)]
CONTINENTS = [NORTH_AMERICA, GREENLAND, SOUTH_AMERICA, AFRICA, EURASIA, UK, JAPAN, AUSTRALIA, NEW_ZEALAND]

REGION_COLORS = {
    "Europe": (31, 78, 121), "North America": (46, 125, 50),
    "Latin America": (217, 164, 32), "Africa": (230, 81, 0),
    "Middle East": (106, 27, 154), "Asia": (198, 40, 40),
    "Oceania": (0, 131, 143), "Global": (85, 85, 85),
}


def project(lon, lat, mx, my, mw, mh):
    """Equirectangular: lon -170..190, lat 75..-55."""
    px = mx + (lon + 170) / 360.0 * mw
    py = my + (75 - lat) / 130.0 * mh
    return px, py


# ---------------------------------------------------------------- sections

def draw_header(d, data):
    y = 20
    f_eyebrow = font(SANS_B, 13)
    d.text((M, y), "T H E   W O R L D   I N   O N E   P A G E", font=f_eyebrow, fill=GREY)
    d.text((W - M - d.textlength("FRIDAY 20 NOVEMBER 2026", font=f_eyebrow), y),
           "FRIDAY 20 NOVEMBER 2026", font=f_eyebrow, fill=GREY)
    y += 22
    f_date = font(SERIF_B, 52)
    d.text((M, y), "20 NOVEMBER 2026", font=f_date, fill=INK)
    d.text((W - M - d.textlength("FRIDAY", font=f_date), y), "FRIDAY", font=f_date, fill=RED)
    y += 66
    f_sub = font(SANS_B, 16)
    sub = f"{data['total_stories']} STORIES  ·  {data['regions_count']} REGIONS  ·  EVERY ONE FROM THIS FRIDAY"
    d.text((M, y), sub, font=f_sub, fill=RED_DARK)
    y += 28
    d.line([M, y, W - M, y], fill=RULE, width=2)
    return y + 8


def draw_timeline(d, y, data):
    f_label = font(SANS_B, 11)
    d.text((M, y), "UTC TIMELINE", font=f_label, fill=RED)
    y += 16
    n = len(data["timeline"])
    col_w = (W - 2 * M) / n
    f_time = font(SANS_B, 11)
    f_text = font(SANS, 9)
    warnings = []
    for i, item in enumerate(data["timeline"]):
        x = M + i * col_w
        d.text((x, y), item["utc"].upper(), font=f_time, fill=INK)
        lines, ov = fit_lines(d, item["label"], f_text, col_w - 10, 3)
        for j, ln in enumerate(lines):
            d.text((x, y + 14 + j * 11), ln, font=f_text, fill=INK)
        if ov:
            warnings.append(f"timeline item {i} overflow")
        if i:
            d.line([x - 5, y, x - 5, y + 40], fill=(200, 192, 172), width=1)
    return y + 48, warnings


def draw_featured(d, y, data):
    warnings = []
    grid_x, grid_w = M, W - 2 * M
    cols, rows = 4, 4
    gap = 8
    cell_w = (grid_w - (cols - 1) * gap) / cols
    cell_h = 100
    for idx, s in enumerate(data["featured"]):
        r, c = divmod(idx, cols)
        x = grid_x + c * (cell_w + gap)
        cy = y + r * (cell_h + gap)
        d.rectangle([x, cy, x + cell_w, cy + cell_h], fill=(255, 255, 255), outline=(214, 206, 188), width=1)
        ix, iy = x + 6, cy + 6
        # number badge
        d.ellipse([ix, iy, ix + 16, iy + 16], fill=RED)
        num = str(s["n"])
        f_num = font(SANS_B, 10)
        d.text((ix + 8 - d.textlength(num, font=f_num) / 2, iy + 3), num, font=f_num, fill=(255, 255, 255))
        # headline, two lines, adaptive size
        hx = ix + 21
        hw = cell_w - 27
        f_head = font(SANS_B, 12)
        lines, ov = fit_lines(d, s["headline"], f_head, hw, 2)
        if ov:
            f_head = font(SANS_B, 11)
            lines, ov = fit_lines(d, s["headline"], f_head, hw, 2)
        for j, ln in enumerate(lines):
            d.text((hx, iy + j * 14), ln, font=f_head, fill=INK)
        if ov:
            warnings.append(f"featured #{s['n']} headline overflow")
        # summary, three lines, adaptive size
        sy = iy + 30
        f_sum = font(SANS, 10)
        lines, ov = fit_lines(d, s["summary"], f_sum, cell_w - 12, 3)
        if ov:
            f_sum = font(SANS, 9)
            lines, ov = fit_lines(d, s["summary"], f_sum, cell_w - 12, 3)
        for j, ln in enumerate(lines):
            d.text((x + 6, sy + j * 12), ln, font=f_sum, fill=INK)
        if ov:
            warnings.append(f"featured #{s['n']} summary overflow")
        # icon + tag line at the bottom
        by = cy + cell_h - 26
        ICONS.get(s["icon"], icon_globe)(d, x + 6, by, 22)
        tag = f"{s['region'].upper()} · {s['topic'].upper()}"
        src = f"{s['source']} · {s['status']}"
        f_tag = font(SANS_B, 8)
        f_src = font(SANS, 8)
        d.text((x + 32, by + 2), tag, font=f_tag, fill=RED_DARK)
        d.text((x + 32, by + 13), src, font=f_src, fill=GREY)
    return y + rows * cell_h + (rows - 1) * gap, warnings


def draw_map_and_also(d, y, data):
    warnings = []
    height = 268
    # --- map panel (left)
    map_x, map_w = M, 336
    f_label = font(SANS_B, 11)
    d.text((map_x, y), "WHERE IT HAPPENED", font=f_label, fill=RED)
    my = y + 18
    mh = height - 18 - 22
    d.rectangle([map_x, my, map_x + map_w, my + mh], fill=MAP_OCEAN, outline=MAP_LINE, width=1)
    for poly in CONTINENTS:
        pts = [project(lon, lat, map_x, my, map_w, mh) for lon, lat in poly]
        d.polygon(pts, fill=MAP_LAND, outline=MAP_LINE)
    # pins, with a small offset ladder for shared spots
    placed = []
    f_pin = font(SANS_B, 8)
    for s in data["featured"]:
        if "lat" not in s or "lon" not in s:
            continue
        px, py = project(s["lon"], s["lat"], map_x, my, map_w, mh)
        dx = dy = 0
        for (ox, oy) in placed:
            if abs(px - ox) < 14 and abs(py - oy) < 14:
                dx += 11
                dy -= 9
        px, py = px + dx, py + dy
        placed.append((px, py))
        d.ellipse([px - 8, py - 8, px + 8, py + 8], fill=RED, outline=(255, 255, 255), width=1)
        num = str(s["n"])
        d.text((px - d.textlength(num, font=f_pin) / 2, py - 5), num, font=f_pin, fill=(255, 255, 255))
    # region legend
    ly = my + mh + 6
    lx = map_x
    f_leg = font(SANS, 8)
    for region in ("Europe", "N. America", "Latin Am.", "Africa", "Mid East", "Asia", "Oceania"):
        key = {"N. America": "North America", "Latin Am.": "Latin America", "Mid East": "Middle East"}.get(region, region)
        d.ellipse([lx, ly + 2, lx + 7, ly + 9], fill=REGION_COLORS[key])
        d.text((lx + 10, ly), region, font=f_leg, fill=INK)
        lx += 10 + d.textlength(region, font=f_leg) + 8
    # --- ALSO list (right, two columns)
    ax = map_x + map_w + 16
    aw = W - M - ax
    d.text((ax, y), "ALSO ON FRIDAY 20 NOVEMBER", font=f_label, fill=RED)
    items = data["also"]
    per_col = (len(items) + 1) // 2
    col_w = (aw - 12) / 2
    f_item = font(SANS, 9)
    f_dot = font(SANS_B, 9)
    for ci in range(2):
        cx = ax + ci * (col_w + 12)
        for j, item in enumerate(items[ci * per_col:(ci + 1) * per_col]):
            iy = y + 18 + j * 14
            d.text((cx, iy), "·", font=f_dot, fill=RED)
            lines, ov = fit_lines(d, item, f_item, col_w - 10, 1)
            d.text((cx + 9, iy), lines[0], font=f_item, fill=INK)
            if ov:
                warnings.append(f"also item overflow: {item[:40]}")
    return y + height, warnings


def draw_date_check(d, y, data):
    f_label = font(SANS_B, 11)
    d.text((M, y), "DATE CHECK — LEFT OUT ON PURPOSE", font=f_label, fill=RED)
    y += 16
    f_item = font(SANS, 8)
    items = data["date_check_excluded"]
    cols = 4
    col_w = (W - 2 * M) / cols
    for i, item in enumerate(items):
        c, r = divmod(i, 2)
        x = M + c * col_w
        iy = y + r * 11
        d.text((x, iy), "✕ ", font=font(SANS_B, 8), fill=RED)
        d.text((x + 10, iy), f"{item['item']} ({item['date']})", font=f_item, fill=GREY)
    y += 24
    f_ny = font(SANS_B, 8)
    notyet = "  ·  ".join(f"{i['item']} — {i['date']}" for i in data["date_check_not_yet"])
    d.text((M, y), "NOT YET:  " + notyet, font=f_ny, fill=INK)
    return y + 13


def draw_footer(d, y, data):
    f_foot = font(SANS, 8)
    sources = ", ".join(data["sources"])
    line1 = "Every story here happened or was first reported on Friday 20 November 2026."
    line2 = f"Sources: {sources}.  Original drawings — no photographs."
    d.text((M, y), line1, font=f_foot, fill=GREY)
    d.text((M, y + 11), line2, font=f_foot, fill=GREY)
    return y + 24


def render(data, out_path):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    warnings = []
    y = draw_header(d, data)
    y, w = draw_timeline(d, y, data)
    warnings += w
    d.line([M, y, W - M, y], fill=RULE, width=1)
    y += 8
    y, w = draw_featured(d, y, data)
    warnings += w
    y += 8
    d.line([M, y, W - M, y], fill=RULE, width=1)
    y += 8
    y, w = draw_map_and_also(d, y, data)
    warnings += w
    y += 6
    d.line([M, y, W - M, y], fill=RULE, width=1)
    y += 8
    y = draw_date_check(d, y, data)
    y += 4
    y = draw_footer(d, y, data)
    if y > H - 4:
        warnings.append(f"page overflow: content ends at y={y}")
    img.save(out_path, format="PNG")
    return warnings


def main(argv):
    if len(argv) != 3:
        print("usage: renderer.py stories.json entry.png", file=sys.stderr)
        return 2
    data = json.loads(Path(argv[1]).read_text())
    n = len(data["featured"]) + len(data["also"])
    if n != data["total_stories"]:
        print(f"FIT WARNING: featured+also = {n}, total_stories = {data['total_stories']}", file=sys.stderr)
    warnings = render(data, argv[2])
    for w in warnings:
        print("FIT WARNING:", w, file=sys.stderr)
    print(f"rendered {argv[2]} ({n} stories)")
    return 1 if warnings else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
