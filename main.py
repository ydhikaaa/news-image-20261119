#!/usr/bin/env python3
"""The World on 19 November -- a newspaper front page drawn in pure Python.

Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png): a 1024x1024
front page summing up the world news of Thursday 19 November 2026.
Standard library only, no network, no clock, no randomness: two runs
produce byte-identical files.
"""

import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (246, 241, 227)
INK = (22, 22, 22)
NAVY = (19, 38, 78)
NAVY_DARK = (12, 26, 54)
RED = (179, 38, 30)
GOLD = (217, 164, 65)
TEAL = (18, 92, 96)
SKY = (143, 178, 205)
DUSK1 = (247, 166, 84)
DUSK2 = (214, 96, 84)
DUSK3 = (94, 64, 120)
NIGHT = (16, 24, 52)
WHITE = (255, 255, 255)
GREY = (110, 108, 96)
LIGHT = (232, 226, 208)

# ---------------------------------------------------------------- font -----
# A 5x7 pixel font. Each glyph is 7 rows of 5 cells; '#' is on, '.' is off.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    'a': ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    'b': ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    'c': ("00000", "00000", "01110", "10001", "10000", "10001", "01110"),
    'd': ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    'e': ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    'f': ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    'g': ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    'h': ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    'i': ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    'j': ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    'k': ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    'l': ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    'm': ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    'n': ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    'o': ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    'p': ("00000", "11110", "10001", "10001", "11110", "10000", "10000"),
    'q': ("00000", "01111", "10001", "10001", "01111", "00001", "00001"),
    'r': ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    's': ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    't': ("00100", "00100", "11110", "00100", "00100", "00100", "00110"),
    'u': ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    'v': ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    'w': ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    'x': ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    'y': ("00000", "10001", "10001", "10001", "01111", "00001", "01110"),
    'z': ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '*': ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
}


def text_width(text, scale):
    return len(text) * 6 * scale - scale


def wrap_text(text, max_width, scale):
    """Greedy word wrap; returns a list of lines that fit max_width."""
    lines = []
    for para in text.split("\n"):
        words = para.split(" ")
        line = ""
        for word in words:
            trial = word if not line else line + " " + word
            if text_width(trial, scale) <= max_width or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


# -------------------------------------------------------------- canvas -----
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i], self.px[i + 1], self.px[i + 2] = color

    def rect(self, x, y, w, h, color):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, color)

    def hline(self, x0, x1, y, color):
        for xx in range(min(x0, x1), max(x0, x1) + 1):
            self.set(xx, y, color)

    def vline(self, x, y0, y1, color):
        for yy in range(min(y0, y1), max(y0, y1) + 1):
            self.set(x, yy, color)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set(xx, yy, color)

    def ring(self, cx, cy, r, color):
        steps = max(24, r * 6)
        for i in range(steps):
            a = 2 * 3.141592653589793 * i / steps
            x = int(cx + r * _cos(a))
            y = int(cy + r * _sin(a))
            self.set(x, y, color)
            self.set(x + 1, y, color)
            self.set(x, y + 1, color)

    def text(self, x, y, s, scale, color):
        cx = x
        for ch in s:
            glyph = FONT.get(ch, FONT['?'])
            for row in range(7):
                bits = glyph[row]
                for col in range(5):
                    if bits[col] == '1':
                        self.rect(cx + col * scale, y + row * scale,
                                  scale, scale, color)
            cx += 6 * scale
        return cx

    def text_centred(self, cx, y, s, scale, color):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, color)


def _sin(a):
    # Small fixed Taylor-free sine via lookup-free series; deterministic.
    a = a % 6.283185307179586
    sign = 1
    if a > 3.141592653589793:
        a -= 3.141592653589793
        sign = -1
    x = a
    x2 = a * a
    return sign * (x - x * x2 / 6.0 + x * x2 * x2 / 120.0
                   - x * x2 * x2 * x2 / 5040.0)


def _cos(a):
    return _sin(a + 1.5707963267948966)


# --------------------------------------------------------- illustrations ---
def draw_gta(cv, x, y, w, h):
    """Vice City at dusk: banded sunset sky, sun, skyline, palm, road."""
    cv.rect(x, y, w, h, DUSK3)
    cv.rect(x, y, w, h // 3, DUSK1)
    cv.rect(x, y + h // 3, w, h // 3, DUSK2)
    cv.disc(x + 64, y + 42, 26, (255, 214, 120))
    cv.text(x + w - 112, y + 10, "VI", 5, NAVY_DARK)
    # Skyline silhouettes with lit windows.
    towers = [(0, 78, 52, 102), (56, 58, 40, 122), (100, 88, 46, 92),
              (150, 48, 38, 132), (192, 70, 44, 110), (240, 86, 48, 94),
              (292, 60, 42, 120), (338, 84, 44, 96), (386, 66, 34, 114)]
    for tx, ty, tw, th in towers:
        cv.rect(x + tx, y + ty, tw, th, (24, 18, 44))
        for wy in range(y + ty + 10, y + ty + th - 8, 16):
            for wx in range(x + tx + 7, x + tx + tw - 6, 13):
                if (wx * 7 + wy * 3) % 5 < 2:
                    cv.rect(wx, wy, 5, 6, (255, 205, 90))
    # Palm tree.
    cv.line(x + 30, y + h - 6, x + 44, y + h - 78, (20, 40, 22))
    cv.line(x + 31, y + h - 6, x + 45, y + h - 78, (20, 40, 22))
    for dx, dy in [(-26, -14), (-14, -24), (4, -28), (20, -22), (28, -10)]:
        cv.line(x + 44, y + h - 78, x + 44 + dx, y + h - 78 + dy, (26, 84, 44))
    # Road with centre dashes.
    cv.rect(x, y + h - 26, w, 26, (30, 30, 34))
    for rx in range(x + 8, x + w - 8, 34):
        cv.rect(rx, y + h - 14, 18, 4, (250, 200, 60))


def draw_summit(cv, x, y, w, h):
    """Shenzhen towers and a table with three small flags."""
    cv.rect(x, y, w, h, (214, 228, 238))
    cv.rect(x, y + h - 34, w, 34, (120, 140, 160))
    # Towers.
    for tx, tw, th in [(8, 26, 62), (40, 20, 84), (66, 30, 56),
                       (104, 18, 92), (128, 26, 64)]:
        cv.rect(x + tx, y + h - 34 - th, tw, th, NAVY)
        for wy in range(y + h - 34 - th + 8, y + h - 40, 12):
            for wx in range(x + tx + 4, x + tx + tw - 4, 9):
                if (wx + wy) % 3 == 0:
                    cv.rect(wx, wy, 3, 4, (180, 210, 235))
    # Table.
    cv.rect(x + 8, y + h - 52, w - 16, 8, (122, 72, 34))
    cv.rect(x + 16, y + h - 44, 6, 10, (122, 72, 34))
    cv.rect(x + w - 22, y + h - 44, 6, 10, (122, 72, 34))
    # Three flags: red, stars-and-stripes, white-blue-red.
    flags = [((200, 40, 40), None), (None, "us"), (None, "tri")]
    fx = x + 22
    for color, kind in flags:
        cv.vline(fx + 2, y + 12, y + 44, INK)
        if kind == "us":
            cv.rect(fx + 3, y + 12, 26, 16, (190, 40, 40))
            cv.rect(fx + 3, y + 12, 26, 3, WHITE)
            cv.rect(fx + 3, y + 18, 26, 3, WHITE)
            cv.rect(fx + 3, y + 24, 26, 3, WHITE)
            cv.rect(fx + 3, y + 12, 11, 9, NAVY)
        elif kind == "tri":
            cv.rect(fx + 3, y + 12, 26, 6, WHITE)
            cv.rect(fx + 3, y + 18, 26, 5, (30, 60, 160))
            cv.rect(fx + 3, y + 23, 26, 5, (200, 40, 40))
        else:
            cv.rect(fx + 3, y + 12, 26, 16, color)
            cv.disc(fx + 11, y + 20, 3, GOLD)
        fx += 46


def draw_court(cv, x, y, w, h):
    """Courthouse with columns and the scales of justice."""
    cv.rect(x, y, w, h, (226, 220, 200))
    # Pediment.
    for i in range(26):
        cv.hline(x + w // 2 - i, x + w // 2 + i, y + 12 + i // 2, NAVY)
    cv.rect(x + 8, y + 40, w - 16, 6, NAVY)
    # Columns.
    for cx in [x + 18, x + 52, x + 86, x + 120]:
        cv.rect(cx, y + 46, 10, 44, WHITE)
        cv.rect(cx - 2, y + 44, 14, 4, NAVY)
        cv.rect(cx - 2, y + 90, 14, 4, NAVY)
    cv.rect(x, y + h - 14, w, 14, (150, 142, 122))
    # Scales: beam, two pans.
    sx, sy = x + w - 8, y + 8
    cv.vline(sx - 74, sy + 4, sy + 26, INK)
    cv.line(sx - 88, sy + 6, sx - 60, sy + 6, INK)
    cv.line(sx - 88, sy + 6, sx - 84, sy + 16, INK)
    cv.line(sx - 88, sy + 6, sx - 92, sy + 16, INK)
    cv.line(sx - 60, sy + 6, sx - 56, sy + 16, INK)
    cv.line(sx - 60, sy + 6, sx - 64, sy + 16, INK)
    cv.rect(sx - 96, sy + 16, 16, 3, GOLD)
    cv.rect(sx - 68, sy + 16, 16, 3, GOLD)


def draw_cyclone(cv, x, y, w, h):
    """Spiral storm over the sea, rain, and a strip of coast."""
    cv.rect(x, y, w, h, (168, 196, 214))
    cx, cy = x + w // 2, y + 52
    for r in [44, 36, 28, 20, 12]:
        cv.ring(cx, cy, r, WHITE if r % 16 == 4 else (70, 110, 150))
    cv.disc(cx, cy, 8, (40, 70, 110))
    # Rain streaks.
    for rx, ry in [(16, 14), (34, 26), (118, 18), (132, 32), (60, 8),
                   (96, 30), (8, 40), (140, 44)]:
        cv.line(x + rx, y + ry, x + rx - 3, y + ry + 10, (60, 100, 150))
    # Sea and coast.
    cv.rect(x, y + h - 26, w, 26, (28, 90, 130))
    cv.rect(x, y + h - 30, w, 5, (240, 220, 160))
    for wx in range(x + 6, x + w - 6, 22):
        cv.rect(wx, y + h - 18, 12, 3, WHITE)


def draw_voyager(cv, x, y, w, h):
    """Starfield, the Sun, and a small probe with a dish antenna."""
    cv.rect(x, y, w, h, NIGHT)
    for sx, sy, sr in [(12, 12, 1), (30, 30, 1), (52, 10, 2), (78, 26, 1),
                       (104, 12, 1), (124, 34, 2), (20, 52, 1), (140, 8, 1),
                       (96, 48, 1), (60, 44, 1), (138, 52, 1), (44, 58, 1)]:
        cv.disc(x + sx, y + sy, sr, WHITE)
    cv.disc(x + 16, y + h - 16, 14, (255, 200, 90))
    # Probe body, dish and long antenna.
    bx, by = x + w - 62, y + 40
    cv.rect(bx, by, 30, 16, (200, 200, 205))
    cv.rect(bx + 30, by + 4, 10, 8, (150, 150, 155))
    cv.line(bx + 15, by, bx + 24, by - 18, (220, 220, 225))
    cv.disc(bx + 24, by - 20, 3, GOLD)
    cv.line(bx, by + 8, bx - 22, by + 2, (220, 220, 225))
    # Signal arcs back toward the Sun.
    for r in [26, 34, 42]:
        cv.ring(bx - 26, by + 8, r, (120, 200, 220))
    cv.rect(bx + 4, by + 16, 4, 10, (120, 120, 125))
    cv.rect(bx + 20, by + 16, 4, 10, (120, 120, 125))


# -------------------------------------------------------------- stories ----
STORIES = [
    {
        "tag": "CULTURE",
        "headline": "THREE LEADERS, ONE TABLE",
        "body": ("Trump, Xi and Putin meet in Shenzhen on the sidelines "
                 "of the APEC summit, the first three-way talks of the "
                 "three powers. Ukraine, Iran, trade and nuclear arms "
                 "are on the agenda."),
        "draw": draw_summit,
    },
    {
        "tag": "LAW",
        "headline": "WORLD COURT RULES TODAY",
        "body": ("The International Court of Justice delivers its "
                 "judgment in The Gambia's case against Myanmar over "
                 "the Rohingya, after seven years. A genocide finding "
                 "would be a first for a state."),
        "draw": draw_court,
    },
    {
        "tag": "WEATHER",
        "headline": "INDIA BRACES FOR CYCLONE AKVAN",
        "body": ("Red alerts and school closures on India's east coast "
                 "as Cyclone Akvan nears land with extremely heavy "
                 "rain. Landfall is expected Friday."),
        "draw": draw_cyclone,
    },
    {
        "tag": "SPACE",
        "headline": "VOYAGER 1, A LIGHT-DAY AWAY",
        "body": ("NASA marks a milestone today: Voyager 1, launched in "
                 "1977, is now one light-day from Earth, about 16 "
                 "billion miles out. A signal takes a day to reach it."),
        "draw": draw_voyager,
    },
]

LEAD_BODY = ("After 13 years, Rockstar's Grand Theft Auto VI began its "
             "global rollout at midnight in New Zealand, sweeping across "
             "time zones with a 99 Metacritic score. Players return to "
             "Vice City, in the state of Leonida, on PS5 and Xbox.")


# -------------------------------------------------------------- layout -----
def draw_page(cv):
    # Masthead.
    cv.rect(0, 0, W, 150, NAVY)
    cv.rect(0, 146, W, 4, GOLD)
    cv.text_centred(W // 2, 18, "THE WORLD TODAY", 7, WHITE)
    cv.text_centred(W // 2, 82, "THURSDAY 19 NOVEMBER 2026", 4, GOLD)
    cv.text_centred(W // 2, 122, "ONE DAY IN THE NEWS", 2, (200, 210, 230))

    # Kicker line.
    cv.text_centred(W // 2, 164, "FIVE STORIES FROM FIVE CORNERS OF THE WORLD",
                    2, RED)

    # Lead story: GTA VI.
    cv.text(24, 196, "VICE CITY OPENS ITS DOORS", 5, INK)
    cv.text(24, 240, "Grand Theft Auto VI rolls out worldwide after 13 years",
            2, GREY)
    draw_gta(cv, 24, 268, 420, 180)
    lines = wrap_text(LEAD_BODY, 976 - 468, 2)
    yy = 272
    for ln in lines:
        cv.text(468, yy, ln, 2, INK)
        yy += 22
    cv.text(468, 414, "REUTERS - SYDNEY, 19 NOV", 2, RED)

    # Divider.
    cv.rect(24, 462, 976, 3, INK)

    # Grid of four stories.
    cell_w, cell_h = 488, 240
    gap = 16
    origins = [(24, 478), (24 + cell_w + gap, 478),
               (24, 478 + cell_h + gap), (24 + cell_w + gap, 478 + cell_h + gap)]
    for story, (ox, oy) in zip(STORIES, origins):
        cv.rect(ox, oy, cell_w, 2, RED)
        cv.text(ox, oy + 10, story["tag"], 2, RED)
        story["draw"](cv, ox, oy + 34, 150, 112)
        head_lines = wrap_text(story["headline"], cell_w - 166, 3)
        hy = oy + 38
        for ln in head_lines:
            cv.text(ox + 166, hy, ln, 3, INK)
            hy += 28
        body_lines = wrap_text(story["body"], cell_w - 8, 2)
        by = oy + 158
        for ln in body_lines:
            cv.text(ox, by, ln, 2, INK)
            by += 20

    # Footer.
    cv.rect(24, 976, 976, 2, INK)
    cv.text_centred(W // 2, 986, "Sources: Reuters - AP - NASA - IMD - ICJ",
                    2, GREY)
    cv.text_centred(W // 2, 1006,
                    "All stories happened or were first reported on 19 November 2026",
                    2, GREY)


# -------------------------------------------------------------- png out -----
def chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def write_png(cv, path):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    data = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(data)
    return len(data)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    cv = Canvas(W, H, PAPER)
    draw_page(cv)
    size = write_png(cv, os.path.join(out_dir, "entry.png"))
    print("wrote entry.png", size, "bytes")


if __name__ == "__main__":
    main()
