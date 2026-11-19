#!/usr/bin/env python3
"""THE WORLD TODAY -- Thursday 19 November 2026 in one image.

A broadsheet front page drawn entirely in code: a masthead, one lead
story with a drawn illustration, twelve numbered story cards, a
by-the-numbers strip, a dotted world map with pins, and an also-today
ticker.  Pure Python standard library, no network, no clock, no
randomness: the grader runs this program twice and both runs must
produce byte-identical output, so every pixel below is a function of
the constants in this file and nothing else.

Output: $MAKEFUN_OUTPUT_DIR/entry.png (default /output/entry.png),
1024 x 1024 PNG, well under the 1 MiB limit.
"""

import math
import os
import struct
import zlib

PAGE_W = 1024
PAGE_H = 1024

# --- palette: warm newsprint cream, ink black, one accent per section ---
PAPER = (247, 243, 231)
PAPER_SHADE = (238, 231, 213)
INK = (26, 24, 20)
FAINT = (122, 114, 98)
RULE = (58, 54, 46)
CRIMSON = (168, 32, 38)
OCEAN = (23, 60, 110)
OCEAN_DEEP = (13, 36, 72)
GOLD = (206, 148, 44)
JADE = (20, 105, 92)
SKY_TOP = (250, 176, 92)
SKY_MID = (226, 106, 92)
SKY_LOW = (110, 62, 118)
NEON = (255, 92, 168)
NEON_CYAN = (72, 214, 228)
WHITE = (255, 255, 255)
SPACE = (10, 14, 34)
STAR = (235, 238, 255)


class Canvas:
    """A flat RGB raster with just enough drawing to typeset a page."""

    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def put(self, x, y, colour):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = colour[0]
            self.px[i + 1] = colour[1]
            self.px[i + 2] = colour[2]

    def rect(self, x, y, w, h, colour):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, colour)

    def frame(self, x, y, w, h, colour, thick=1):
        for t in range(thick):
            self.rect(x + t, y + t, w - 2 * t, 1, colour)
            self.rect(x + t, y + h - 1 - t, w - 2 * t, 1, colour)
            self.rect(x + t, y + t, 1, h - 2 * t, colour)
            self.rect(x + w - 1 - t, y + t, 1, h - 2 * t, colour)

    def line(self, x0, y0, x1, y1, colour, thick=1):
        # Bresenham, with a square brush for thickness.
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            r = thick // 2
            self.rect(x - r, y - r, thick, thick, colour)
            if x == x1 and y == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, colour):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.put(xx, yy, colour)

    def ring(self, cx, cy, r, colour, thick=1):
        for yy in range(cy - r - thick, cy + r + thick + 1):
            for xx in range(cx - r - thick, cx + r + thick + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - thick) ** 2 < d2 <= r * r:
                    self.put(xx, yy, colour)

    def tri(self, x0, y0, x1, y1, x2, y2, colour):
        # Filled triangle via scanline over its bounding box.
        minx = max(0, min(x0, x1, x2))
        maxx = min(self.w - 1, max(x0, x1, x2))
        miny = max(0, min(y0, y1, y2))
        maxy = min(self.h - 1, max(y0, y1, y2))

        def edge(ax, ay, bx, by, px_, py_):
            return (px_ - ax) * (by - ay) - (py_ - ay) * (bx - ax)

        for yy in range(miny, maxy + 1):
            for xx in range(minx, maxx + 1):
                d0 = edge(x0, y0, x1, y1, xx, yy)
                d1 = edge(x1, y1, x2, y2, xx, yy)
                d2 = edge(x2, y2, x0, y0, xx, yy)
                if (d0 >= 0 and d1 >= 0 and d2 >= 0) or (
                    d0 <= 0 and d1 <= 0 and d2 <= 0
                ):
                    self.put(xx, yy, colour)


def write_png(canvas, path):
    """Serialise the canvas as a PNG with fixed compression settings."""

    def chunk(tag, payload):
        body = tag + payload
        return (
            struct.pack(">I", len(payload))
            + body
            + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)
        )

    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter type 0 on every scanline
        raw += canvas.px[y * stride:(y + 1) * stride]
    ihdr = struct.pack(
        ">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0
    )  # 8-bit RGB
    data = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )
    with open(path, "wb") as fh:
        fh.write(data)
    return len(data)


# ----------------------------------------------------------------------
# A 5x7 bitmap typeface, drawn for this page.  Each glyph is seven
# strings of five cells; '#' is ink, '.' is paper.  Text is measured in
# whole cells, so wrapping is exact and the layout cannot drift.
# ----------------------------------------------------------------------
FONT = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", ".#.#.", "..#..", "..#..", "..#..", ".#.#.", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "-": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "%": ("##..#", "##.#.", "....#", "...#.", "..#..", ".#...", "#..##"),
    "$": ("..#..", ".####", "##.#.", ".###.", ".#.##", "####.", "..#.."),
    "+": (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "*": (".....", "#.#.#", ".###.", "#####", ".###.", "#.#.#", "....."),
    "=": (".....", ".....", "#####", ".....", "#####", ".....", "....."),
    "\u20ac": (".###.", "#....", "#####", "#....", "#####", "#....", ".###."),
    "\u00b7": (".....", ".....", ".....", ".##..", ".##..", ".....", "....."),
    "\u2014": (".....", ".....", ".....", "#####", "#####", ".....", "....."),
}

FONT.update({
    "a": (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#...", ".#...", "####.", ".#...", ".#...", ".#..."),
    "g": (".....", ".....", ".####", "#...#", ".####", "....#", ".###."),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": ("..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."),
    "j": ("...#.", ".....", "..##.", "...#.", "...#.", "#..#.", ".##.."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "####.", "#....", "#...."),
    "q": (".....", ".....", ".####", "#...#", ".####", "....#", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", ".####", "....#", ".###."),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
})

CELL_W = 6   # glyph width 5 + 1 tracking, in font cells
CELL_H = 9   # glyph height 7 + 2 leading, in font cells


def text_width(text, scale):
    return len(text) * CELL_W * scale - scale


def draw_text(cv, x, y, text, colour, scale=1):
    """Draw one line of text with its top-left at (x, y)."""
    cx = x
    for ch in text:
        glyph = FONT.get(ch, FONT[" "])
        for row_i, row in enumerate(glyph):
            for col_i, cell in enumerate(row):
                if cell == "#":
                    cv.rect(
                        cx + col_i * scale,
                        y + row_i * scale,
                        scale,
                        scale,
                        colour,
                    )
        cx += CELL_W * scale
    return cx


def draw_centered(cv, cx, y, text, colour, scale=1):
    return draw_text(cv, cx - text_width(text, scale) // 2, y, text, colour, scale)


def wrap(text, scale, max_width):
    """Greedy word wrap; returns the list of lines that fit max_width."""
    lines = []
    current = ""
    for word in text.split(" "):
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_wrapped(cv, x, y, text, colour, scale, max_width, max_lines=None):
    lines = wrap(text, scale, max_width)
    if max_lines is not None:
        lines = lines[:max_lines]
    for i, line in enumerate(lines):
        draw_text(cv, x, y + i * CELL_H * scale, line, colour, scale)
    return y + len(lines) * CELL_H * scale


# ----------------------------------------------------------------------
# Illustrations.  Everything is rectangles, lines, discs and triangles
# on the raster: no image files, no fonts on disk, nothing to load.
# ----------------------------------------------------------------------

def vice_city(cv, x, y, w, h):
    """The lead picture: a neon dusk over a returning game's skyline."""
    bands = [SKY_LOW, SKY_MID, SKY_TOP]
    band_h = h // 5
    for i in range(5):
        colour = bands[min(i * len(bands) // 5, len(bands) - 1)]
        cv.rect(x, y + i * band_h, w, band_h + 1, colour)
    cv.disc(x + w * 3 // 4, y + band_h * 2, 17, (255, 214, 120))
    # Skyline: fixed tower widths and heights, lit windows on a stride.
    towers = [(0, 52), (26, 74), (58, 44), (84, 88), (118, 60), (146, 96),
              (182, 54), (210, 80), (244, 46), (272, 70), (306, 58)]
    base = y + h - 26
    for off, th in towers:
        tx = x + off
        cv.rect(tx, base - th, 22, th, OCEAN_DEEP)
        for wy in range(base - th + 6, base - 6, 9):
            for wx in range(tx + 4, tx + 18, 7):
                if (wx * 7 + wy * 13) % 5 == 0:
                    cv.rect(wx, wy, 3, 4, (255, 226, 130))
    # Two palms leaning over the water.
    for px0, lean in ((x + 18, 10), (x + w - 30, -12)):
        cv.line(px0, base, px0 + lean, base - 44, OCEAN_DEEP, 3)
        top_x, top_y = px0 + lean, base - 44
        for a in range(-3, 4):
            cv.line(top_x, top_y, top_x + a * 7, top_y - 8 + abs(a) * 2,
                    OCEAN_DEEP, 2)
    cv.rect(x, base, w, h - (base - y), OCEAN)
    for i in range(14):
        rx = x + (i * 67) % (w - 30)
        cv.rect(rx, base + 5 + (i * 11) % 16, 16, 2, NEON_CYAN)
    draw_centered(cv, x + w // 2, y + 8, "VICE CITY", NEON, 2)


def icon_summit(cv, x, y, s):
    """Three flags over a table: a first trilateral meeting."""
    cv.rect(x, y + s - 8, s, 3, INK)
    flags = [(CRIMSON, GOLD), ((38, 74, 160), WHITE), ((206, 32, 40), WHITE)]
    for i, (field, mark) in enumerate(flags):
        fx = x + 4 + i * (s // 3)
        cv.rect(fx, y + 4, 2, s - 14, INK)
        cv.rect(fx + 2, y + 4, s // 3 - 4, 12, field)
        cv.disc(fx + 2 + (s // 3 - 4) // 2, y + 10, 3, mark)


def icon_voyager(cv, x, y, s):
    """A lonely probe, a dashed signal home, one blue dot."""
    cv.rect(x, y, s, s, SPACE)
    stars = [(6, 8), (20, 4), (44, 10), (50, 30), (10, 40), (30, 48), (52, 50)]
    for sx, sy in stars:
        cv.put(x + sx, y + sy, STAR)
        cv.put(x + sx + 1, y + sy, STAR)
    cv.disc(x + 16, y + 18, 6, GOLD)
    cv.ring(x + 16, y + 18, 10, WHITE, 2)
    cv.line(x + 20, y + 24, x + 44, y + 44, WHITE, 2)
    for t in range(0, 20, 5):
        cv.put(x + 24 + t, y + 26 + t // 2, NEON_CYAN)
    cv.disc(x + 48, y + 48, 4, (70, 130, 230))


def icon_cyclone(cv, x, y, s):
    """A spiral storm over a coastline."""
    cx, cy = x + s // 2, y + s // 2
    for r in (22, 16, 10):
        for a in range(0, 360, 6):
            px_ = cx + int(r * math.cos(math.radians(a + r * 4)))
            py_ = cy + int(r * 0.72 * math.sin(math.radians(a + r * 4)))
            cv.rect(px_ - 1, py_ - 1, 3, 3, OCEAN)
    cv.disc(cx, cy, 4, CRIMSON)
    cv.line(x + 2, y + s - 6, x + s - 2, y + s - 12, JADE, 2)


def icon_eu(cv, x, y, s):
    """A circle of gold stars on deep blue."""
    cv.rect(x, y, s, s, OCEAN_DEEP)
    cx, cy = x + s // 2, y + s // 2
    for k in range(12):
        a = math.radians(k * 30 - 90)
        sx = cx + int(17 * math.cos(a))
        sy = cy + int(17 * math.sin(a))
        cv.disc(sx, sy, 3, GOLD)


def icon_capitol(cv, x, y, s):
    """A dome on columns: a new Speaker is chosen."""
    cx = x + s // 2
    for r in range(14, 0, -2):
        cv.rect(cx - r, y + 22 - (14 - r) // 2, 2 * r, 2, OCEAN)
    cv.rect(cx - 1, y + 2, 2, 8, OCEAN)
    for i in range(5):
        cv.rect(x + 8 + i * 10, y + 26, 4, 20, OCEAN)
    cv.rect(x + 4, y + 46, s - 8, 3, OCEAN)
    cv.rect(x + 2, y + 51, s - 4, 3, OCEAN_DEEP)


def icon_gulf(cv, x, y, s):
    """A tanker under a dashed arc in a narrow strait."""
    cv.rect(x, y + s - 16, s, 16, OCEAN)
    cv.line(x + 4, y + 10, x + 20, y + 30, CRIMSON, 2)
    for t in range(6):
        cv.put(x + 22 + t * 4, y + 30 - t * 2, CRIMSON)
        cv.put(x + 23 + t * 4, y + 30 - t * 2, CRIMSON)
    hull = y + s - 22
    cv.rect(x + 18, hull, 30, 5, INK)
    cv.rect(x + 26, hull - 6, 12, 6, INK)
    cv.tri(x + 48, hull, x + 54, hull + 5, x + 48, hull + 5, INK)


def icon_chip(cv, x, y, s):
    """A processor: the chip story of the day."""
    cv.rect(x + 12, y + 12, s - 24, s - 24, JADE)
    cv.frame(x + 12, y + 12, s - 24, s - 24, INK, 2)
    cv.rect(x + 22, y + 22, s - 44, s - 44, PAPER)
    for i in range(4):
        p = y + 8 + i * 11
        cv.rect(x + 4, p, 8, 3, INK)
        cv.rect(x + s - 12, p, 8, 3, INK)
        q = x + 8 + i * 11
        cv.rect(q, y + 4, 3, 8, INK)
        cv.rect(q, y + s - 12, 3, 8, INK)


def icon_fed(cv, x, y, s):
    """Columns and a rising arrow: rates are heading up."""
    for i in range(4):
        cv.rect(x + 6 + i * 12, y + 16, 5, 26, OCEAN)
    cv.tri(x + 2, y + 14, x + s - 2, y + 14, x + s // 2, y + 4, OCEAN)
    cv.rect(x + 4, y + 44, s - 8, 3, OCEAN)
    pts = [(8, 40), (20, 34), (30, 36), (42, 26), (50, 20)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        cv.line(x + ax, y + ay, x + bx, y + by, CRIMSON, 2)
    cv.tri(x + 50, y + 14, x + 50, y + 24, x + 42, y + 22, CRIMSON)


def icon_football(cv, x, y, s):
    """A ball and a score: a final settled 2-1."""
    cx, cy = x + 11, y + s // 2
    cv.ring(cx, cy, 9, INK, 2)
    cv.disc(cx, cy, 3, INK)
    for dx, dy in ((-7, -6), (7, -6), (-8, 5), (8, 5), (0, 9)):
        cv.disc(cx + dx, cy + dy, 1, INK)
    draw_text(cv, x + 25, y + s // 2 - 8, "2-1", CRIMSON, 2)


def icon_bars(cv, x, y, s):
    """Two rising bars and a year: a projection to 2035."""
    cv.rect(x + 6, y + s - 8, s - 10, 2, INK)
    cv.rect(x + 12, y + 26, 10, s - 34, OCEAN)
    cv.rect(x + 30, y + 12, 10, s - 20, GOLD)
    draw_text(cv, x + 6, y + 1, "2035", INK, 1)


def icon_solar(cv, x, y, s):
    """Sun over a panel grid: a clean-energy pledge."""
    cv.disc(x + s - 14, y + 12, 7, GOLD)
    for gx in range(3):
        for gy in range(2):
            px0 = x + 6 + gx * 14
            py0 = y + 26 + gy * 12
            cv.rect(px0, py0, 12, 10, OCEAN)
            cv.line(px0 + 6, py0, px0 + 6, py0 + 10, PAPER, 1)
            cv.line(px0, py0 + 5, px0 + 12, py0 + 5, PAPER, 1)


def icon_strata(cv, x, y, s):
    """Rock layers with one missing band: a billion-year gap."""
    layers = [GOLD, (150, 96, 54), JADE, (150, 96, 54), OCEAN]
    yy = y + 6
    for i, colour in enumerate(layers):
        if i == 2:
            cv.frame(x + 8, yy, s - 16, 8, CRIMSON, 2)
        else:
            cv.rect(x + 8, yy, s - 16, 8, colour)
        yy += 10


# ----------------------------------------------------------------------
# A dotted world map: continents are soft blobs, a dot is drawn where a
# grid point falls inside one, and crimson pins mark today's stories.
# ----------------------------------------------------------------------
BLOBS = [
    (0.05, 0.14, 0.045, 0.09),   # Alaska
    (0.14, 0.27, 0.115, 0.20),   # North America
    (0.17, 0.52, 0.030, 0.07),   # Central America
    (0.23, 0.73, 0.052, 0.17),   # South America
    (0.465, 0.21, 0.052, 0.12),  # Europe
    (0.485, 0.55, 0.062, 0.21),  # Africa
    (0.665, 0.23, 0.165, 0.17),  # Asia
    (0.605, 0.47, 0.034, 0.10),  # India
    (0.705, 0.49, 0.040, 0.09),  # South-East Asia
    (0.735, 0.63, 0.075, 0.035), # Indonesia
    (0.795, 0.75, 0.058, 0.10),  # Australia
    (0.865, 0.30, 0.016, 0.07),  # Japan
]

PINS = [
    (0.755, 0.40),  # Shenzhen summit
    (0.640, 0.46),  # Bay of Bengal cyclone
    (0.470, 0.19),  # Brussels EU loan
    (0.530, 0.20),  # Kyiv
    (0.185, 0.29),  # Washington
    (0.565, 0.35),  # The Gulf
    (0.075, 0.31),  # Silicon Valley chips
    (0.190, 0.24),  # Canada ties reset
]


def draw_map(cv, x, y, w, h):
    cv.rect(x, y, w, h, OCEAN_DEEP)
    pitch = 6
    for gy in range(y + 4, y + h - 2, pitch):
        for gx in range(x + 4, x + w - 2, pitch):
            fx = (gx - x) / w
            fy = (gy - y) / h
            for bx, by, brx, bry in BLOBS:
                if ((fx - bx) / brx) ** 2 + ((fy - by) / bry) ** 2 <= 1.0:
                    cv.disc(gx, gy, 1, (168, 196, 226))
                    break
    for fx, fy in PINS:
        px_, py_ = x + int(fx * w), y + int(fy * h)
        cv.disc(px_, py_, 3, CRIMSON)
        cv.ring(px_, py_, 5, GOLD, 1)
    # Voyager's way out: a dashed line leaving the top-right corner.
    for t in range(5):
        cv.put(x + w - 12 - t * 5, y + 10 + t * 2, NEON_CYAN)
        cv.put(x + w - 11 - t * 5, y + 10 + t * 2, NEON_CYAN)


# ----------------------------------------------------------------------
# The day itself: Thursday 19 November 2026, as the wires reported it.
# ----------------------------------------------------------------------
STORIES = [
    ("DIPLOMACY · SHENZHEN", "TRUMP, XI, PUTIN MEET IN SHENZHEN",
     "A first trilateral meeting, held as the APEC summit opens in "
     "Shenzhen; Xi urges open trade.", icon_summit),
    ("SPACE · DEEP SPACE", "VOYAGER 1 NOW ONE LIGHT-DAY AWAY",
     "NASA's farthest probe crosses the mark after 49 years; "
     "confirmation due at today's briefing.", icon_voyager),
    ("WEATHER · BAY OF BENGAL", "CYCLONE AKVAN NEARS INDIAN COAST",
     "A very severe storm spins over the Bay of Bengal; landfall on "
     "the Andhra coast due Friday.", icon_cyclone),
    ("EUROPE · UKRAINE", "EU PROPOSES \u20ac45BN UKRAINE LOAN",
     "Brussels would borrow the money, repaid only once Russia pays "
     "war reparations.", icon_eu),
    ("POLITICS · WASHINGTON", "JEFFRIES SET TO BE FIRST BLACK SPEAKER",
     "Democrats nominate Hakeem Jeffries to lead the House of "
     "Representatives.", icon_capitol),
    ("MIDDLE EAST · THE GULF", "US AND IRAN TRADE FIRE AGAIN",
     "Tehran widens its strikes on Gulf states as Hormuz shipping is "
     "hit again.", icon_gulf),
    ("TECHNOLOGY · CHIPS", "NVIDIA'S NEW CHIEF PLEDGES RAISES",
     "Acting CEO Colette Kress pledges earlier pay rises after "
     "founder Huang's shock exit.", icon_chip),
    ("ECONOMY · THE FED", "FED MINUTES POINT TO MORE HIKES",
     "Most officials back further rate rises if inflation and jobs "
     "stay hot.", icon_fed),
    ("SPORT · DHAKA", "INDIA BEAT PAKISTAN 2-1 IN FINAL",
     "Dhaka hosts a thriller as India lift the South Asian crown.",
     icon_football),
    ("SOCIETY · PEW STUDY", "ISLAM TO TOP FAITH TABLE BY 2035",
     "A Pew study projects Islam will become the world's largest "
     "religion.", icon_bars),
    ("BUSINESS · INDIA", "AMAZON BETS $7BN ON INDIA ENERGY",
     "The tech giant plans renewable projects across India by 2030.",
     icon_solar),
    ("SCIENCE · GEOLOGY", "EARTH'S MISSING BILLION YEARS",
     "Scientists may have solved the Great Unconformity riddle at "
     "last.", icon_strata),
]

MARGIN = 28
CONTENT_W = PAGE_W - 2 * MARGIN


def masthead(cv):
    cv.rect(MARGIN, 18, CONTENT_W, 3, INK)
    cv.rect(MARGIN, 24, CONTENT_W, 1, INK)
    draw_centered(cv, PAGE_W // 2, 30,
                  "VOL. I \u00b7 NO. 19 \u00b7 ONE IMAGE, THE WHOLE DAY",
                  FAINT, 1)
    draw_centered(cv, PAGE_W // 2, 42, "THE WORLD TODAY", INK, 6)
    draw_centered(cv, PAGE_W // 2, 90,
                  "THURSDAY \u00b7 19 NOVEMBER 2026", CRIMSON, 2)
    cv.rect(MARGIN, 110, CONTENT_W, 2, INK)
    cv.rect(MARGIN, 115, CONTENT_W, 1, INK)


def lead_story(cv):
    y0 = 124
    vice_city(cv, MARGIN, y0, 330, 156)
    cv.frame(MARGIN, y0, 330, 156, INK, 2)
    tx = MARGIN + 348
    tw = PAGE_W - MARGIN - tx
    draw_text(cv, tx, y0 + 2, "THE LEAD \u00b7 ENTERTAINMENT", CRIMSON, 1)
    draw_text(cv, tx, y0 + 16, "GTA VI ARRIVES:", INK, 3)
    draw_text(cv, tx, y0 + 43, "VICE CITY OPENS", INK, 3)
    draw_wrapped(
        cv, tx, y0 + 78,
        "Rockstar's Grand Theft Auto VI begins its worldwide rollout, "
        "ending a 13-year wait as millions pour into a neon Vice City.",
        INK, 2, tw, 3)
    draw_text(cv, tx, y0 + 140,
              "Midnight launches on five continents", FAINT, 1)


def story_card(cv, x, y, w, number, story):
    kicker, headline, summary, icon = story
    cv.rect(x, y, w, 82, PAPER_SHADE)
    cv.frame(x, y, w, 82, RULE, 1)
    cv.rect(x + 8, y + 8, 28, 28, CRIMSON)
    label = str(number)
    draw_text(cv, x + 8 + (28 - text_width(label, 2)) // 2, y + 15,
              label, WHITE, 2)
    draw_text(cv, x + 44, y + 9, kicker, FAINT, 1)
    draw_wrapped(cv, x + 44, y + 20, headline, INK, 2, w - 44 - 76, 2)
    draw_wrapped(cv, x + 44, y + 58, summary, INK, 1, w - 44 - 76, 2)
    icon(cv, x + w - 64, y + 13, 56)


def numbers_strip(cv):
    y0 = 856
    cv.frame(MARGIN, y0, CONTENT_W, 44, INK, 2)
    tag = "BY THE NUMBERS"
    cv.rect(MARGIN + 16, y0 - 5, text_width(tag, 1) + 10, 11, PAPER)
    draw_text(cv, MARGIN + 21, y0 - 3, tag, CRIMSON, 1)
    draw_centered(cv, PAGE_W // 2, y0 + 6,
                  "13 YRS TO GTA VI \u00b7 \u20ac45BN FOR UKRAINE \u00b7 "
                  "1 LIGHT-DAY TO VOYAGER", INK, 2)
    draw_centered(cv, PAGE_W // 2, y0 + 25,
                  "2-1 SAFF FINAL \u00b7 $7BN INDIA ENERGY \u00b7 "
                  "2035 FAITH SHIFT", INK, 2)


def bottom_band(cv):
    y0 = 912
    draw_map(cv, MARGIN, y0, 296, 78)
    cv.frame(MARGIN, y0, 296, 78, INK, 1)
    tx = MARGIN + 316
    draw_text(cv, tx, y0, "ALSO TODAY", CRIMSON, 2)
    items = [
        "Canada resets China ties, hunting a US deal",
        "Senators: AI cyber threats outpace defences",
        "Gold under pressure as a firm dollar weighs",
        "Melenchon tipped as a possible president",
    ]
    for i, item in enumerate(items):
        draw_text(cv, tx, y0 + 24 + i * 15, "\u00b7 " + item, INK, 1)


def footer(cv):
    cv.rect(MARGIN, 1000, CONTENT_W, 1, INK)
    draw_centered(
        cv, PAGE_W // 2, 1006,
        "Sources: AP \u00b7 BBC \u00b7 The Hindu \u00b7 The Economist \u00b7 "
        "Space.com \u00b7 Jagran Josh \u00b7 Times of India \u00b7 Drawn in "
        "pure Python", FAINT, 1)


def build_page():
    cv = Canvas(PAGE_W, PAGE_H, PAPER)
    masthead(cv)
    lead_story(cv)
    draw_centered(cv, PAGE_W // 2, 292, "THE DAY IN TWELVE STORIES",
                  CRIMSON, 2)
    card_w = (CONTENT_W - 16) // 2
    for i, story in enumerate(STORIES):
        row, col = divmod(i, 2)
        x = MARGIN + col * (card_w + 16)
        y = 318 + row * 88
        story_card(cv, x, y, card_w, i + 1, story)
    numbers_strip(cv)
    bottom_band(cv)
    footer(cv)
    return cv


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    size = write_png(build_page(), os.path.join(out_dir, "entry.png"))
    print("wrote entry.png", size, "bytes")


if __name__ == "__main__":
    main()
