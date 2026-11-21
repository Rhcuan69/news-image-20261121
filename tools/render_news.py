#!/usr/bin/env python3
"""Draw the Saturday 21 November 2026 front page of THE WORLD TODAY.

Build-time tool for the make.fun bounty news-image-20261121. It paints
a 1024x1024 newspaper front page -- masthead, black date band, one lead
story and six more in a two-by-three grid, each with a small hand-drawn
pictogram -- and writes it to news-21-nov-2026.png next to this tool.

Everything here is pure Python standard library: the pixel buffer, the
5x7 bitmap letterforms, the pictograms and the PNG writer are all
implemented in this file, so the script runs on a vanilla interpreter
with no third-party packages. Output is deterministic: the same input
always produces the same bytes.

The seven stories are the day's verified headlines, worded as reported.
"""

import math
import struct
import zlib
from pathlib import Path

# ---------------------------------------------------------------- page
# Page size and the small palette used across the whole front page.

PAGE_W = 1024
PAGE_H = 1024

PAPER = (250, 244, 230)     # newsprint cream
INK = (18, 18, 18)         # near-black
CRIMSON = (176, 32, 32)    # kicker red
SLATE = (88, 84, 74)       # muted grey for the strapline
SKY = (52, 96, 158)        # blue accents (water, waves, planet)
GOLD = (198, 148, 38)      # gold accents (star, badge, key)

MARGIN = 24            # inner text margin
COL_GAP = 24           # gap between the two grid columns
ROW_TOPS = (374, 559, 744)
GRID_BOTTOM = 929


# -------------------------------------------------------------- canvas
class Sheet:
    """An RGB pixel buffer with tiny vector/text drawing helpers."""

    def __init__(self, width, height, background):
        self.width = width
        self.height = height
        self.buf = bytearray(background * (width * height))

    def dot(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.buf[i:i + 3] = bytes(colour)

    def fill(self, x0, y0, x1, y1, colour):
        """Fill the rectangle [x0, x1) x [y0, y1), clipped to the page."""
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.width, x1)
        y1 = min(self.height, y1)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(colour) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.width + x0) * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x0, x1, y, colour, thick=1):
        self.fill(x0, y, x1, y + thick, colour)

    def vline(self, x, y0, y1, colour, thick=1):
        self.fill(x, y0, x + thick, y1, colour)

    def frame(self, x0, y0, x1, y1, colour, thick=1):
        self.hline(x0, x1, y0, colour, thick)
        self.hline(x0, x1, y1 - thick, colour, thick)
        self.vline(x0, y0, y1, colour, thick)
        self.vline(x1 - thick, y0, y1, colour, thick)

    def segment(self, x0, y0, x1, y1, colour, thick=1):
        """Bresenham line; thickness is a square brush at each step."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        half = thick // 2
        while True:
            self.fill(x0 - half, y0 - half, x0 - half + thick,
                      y0 - half + thick, colour)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def polyline(self, points, colour, thick=1):
        for a, b in zip(points, points[1:]):
            self.segment(a[0], a[1], b[0], b[1], colour, thick)

    def ring(self, cx, cy, radius, colour, thick=1):
        steps = max(24, int(2 * math.pi * radius))
        for n in range(steps):
            a = 2 * math.pi * n / steps
            self.fill(int(cx + radius * math.cos(a)) - thick // 2,
                      int(cy + radius * math.sin(a)) - thick // 2,
                      int(cx + radius * math.cos(a)) - thick // 2 + thick,
                      int(cy + radius * math.sin(a)) - thick // 2 + thick,
                      colour)

    def disc(self, cx, cy, radius, colour):
        for dy in range(-radius, radius + 1):
            dx = int(math.sqrt(radius * radius - dy * dy))
            self.hline(cx - dx, cx + dx + 1, cy + dy, colour)

    # -- text ------------------------------------------------------
    def write(self, x, y, text, scale, colour):
        """Draw one line of text; returns the x just past the last glyph."""
        cx = x
        for ch in text:
            glyph = GLYPHS.get(ch, GLYPHS[" "])
            for row, bits in enumerate(glyph):
                for col, bit in enumerate(bits):
                    if bit == "#":
                        self.fill(cx + col * scale, y + row * scale,
                                  cx + (col + 1) * scale,
                                  y + (row + 1) * scale, colour)
            cx += CELL_ADV * scale
        return cx

    def centred(self, y, text, scale, colour):
        self.write((self.width - text_width(text, scale)) // 2,
                   y, text, scale, colour)

    def wrapped(self, x, y, text, scale, colour, max_w, leading):
        """Greedy word wrap; returns the y just below the last line."""
        words = text.split(" ")
        lines = []
        current = ""
        for word in words:
            trial = word if not current else current + " " + word
            if text_width(trial, scale) <= max_w or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        for line in lines:
            self.write(x, y, line, scale, colour)
            y += CELL_H * scale + leading
        return y - leading


# ---------------------------------------------------------------- font
# Each letterform is seven rows of five cells; '#' is ink, '.' is blank.
# Only capitals, digits and the punctuation used on the page are needed.
# The table is grouped: capitals first, then digits, then punctuation.

GLYPHS = {
    # capitals A-M
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    # capitals N-Z
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
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    # digits
    "0": (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    # space and punctuation
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".....", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "%": ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
}

CELL_W = 5          # glyph columns
CELL_H = 7          # glyph rows
CELL_ADV = 6        # advance per character at scale 1 (5 + 1 gap)


def text_width(text, scale):
    """Pixel width of text at the given scale, without trailing gap."""
    if not text:
        return 0
    return len(text) * CELL_ADV * scale - scale


# ------------------------------------------------------------- stories
# Each entry drives one block on the page: kicker line, headline, deck
# and the name of the pictogram drawn beside it. The lead entry spans
# the full width; the other six fill a two-by-three grid in order.
# All seven were first reported on Saturday 21 November 2026.

STORIES = [
    {
        "kicker": "EUROPE - NATO",
        "headline": "POLAND SEEKS MORE NATO AIR DEFENCES",
        "deck": "WARSAW ASKS FOR MORE SUPPORT AFTER TWO RUSSIAN "
                "MISSILES AND A DRONE CAME DOWN; NATO CALLS IT A "
                "GRAVE VIOLATION.",
        "art": "shield",
        "lead": True,
    },
    {
        "kicker": "MARKETS",
        "headline": "NASDAQ PLUNGES 5.3% AS NVIDIA TUMBLES ON SEC PROBE REPORT",
        "deck": "S AND P 500 FALLS 3.7% IN SEVENTH STRAIGHT LOSS; "
                "NVIDIA DOWN ABOUT 14% AFTER REUTERS REPORT.",
        "art": "chart",
    },
    {
        "kicker": "LATIN AMERICA - CRIME",
        "headline": "MEXICO CAPTURES 'EL CHAPO ISIDRO' CARTEL BOSS",
        "deck": "FAUSTO ISIDRO MEZA FLORES, ONE OF THE FBI'S 10 MOST "
                "WANTED, SEIZED IN GUASAVE, SINALOA.",
        "art": "badge",
    },
    {
        "kicker": "ASIA-PACIFIC - QUAKE",
        "headline": "MAGNITUDE 6.8 QUAKE STRIKES OFF TIMOR-LESTE",
        "deck": "TREMOR 103 KM NORTHEAST OF LOSPALOS AT 09:42 UTC; "
                "NO TSUNAMI THREAT, LOW RISK OF DAMAGE.",
        "art": "quake",
    },
    {
        "kicker": "DIPLOMACY - GENEVA",
        "headline": "UN TALKS AGREE TO DRAFT 'KILLER ROBOT' RULES",
        "deck": "128 COUNTRIES IN GENEVA AGREE TO WORK TOWARD RULES "
                "FOR LETHAL AUTONOMOUS WEAPONS BY 2028.",
        "art": "robot",
    },
    {
        "kicker": "SPACE",
        "headline": "BEPICOLOMBO REACHES MERCURY ORBIT AFTER EIGHT YEARS",
        "deck": "EUROPE-JAPAN TWIN ORBITERS ENTER ORBIT 18:24 UTC; "
                "ONLY THE SECOND MISSION TO ORBIT MERCURY.",
        "art": "planet",
    },
    {
        "kicker": "HEALTH",
        "headline": "PILL HAILED AS BREAKTHROUGH FOR PANCREATIC CANCER",
        "deck": "DARAXONRASIB MADE TUMOURS UNDETECTABLE IN ONE IN 12 "
                "PATIENTS; NEARLY ALL TUMOURS STOPPED GROWING.",
        "art": "pill",
    },
]


# ----------------------------------------------------------- pictograms
# Each draws inside a small box whose top-left corner is (ox, oy).
# The pictures are deliberately simple line art: a NATO shield, a
# falling market chart, a police badge, a seismic trace, a robot
# head, a ringed planet with its orbiter, and a medicine capsule.

def art_shield(s, ox, oy):
    """NATO shield with a four-point star and two jets overhead."""
    # Shield outline: flat top, curved sides meeting at a point.
    s.segment(ox + 14, oy + 6, ox + 62, oy + 6, SKY, 3)
    s.segment(ox + 14, oy + 6, ox + 14, oy + 30, SKY, 3)
    s.segment(ox + 62, oy + 6, ox + 62, oy + 30, SKY, 3)
    s.segment(ox + 14, oy + 30, ox + 38, oy + 52, SKY, 3)
    s.segment(ox + 62, oy + 30, ox + 38, oy + 52, SKY, 3)
    # Four-point star in the middle of the shield.
    cx, cy = ox + 38, oy + 26
    s.segment(cx, cy - 12, cx, cy + 12, GOLD, 3)
    s.segment(cx - 12, cy, cx + 12, cy, GOLD, 3)
    s.segment(cx - 8, cy - 8, cx + 8, cy + 8, GOLD, 2)
    s.segment(cx - 8, cy + 8, cx + 8, cy - 8, GOLD, 2)
    # Small jets overhead, guarding the shield.
    s.segment(ox + 78, oy + 8, ox + 96, oy + 8, INK, 2)
    s.segment(ox + 96, oy + 8, ox + 104, oy + 5, INK, 2)
    s.segment(ox + 96, oy + 8, ox + 104, oy + 11, INK, 2)


def art_chart(s, ox, oy):
    # Axes first, then the jagged line falling to the lower right.
    s.vline(ox + 6, oy + 6, oy + 50, INK, 2)
    s.hline(ox + 6, ox + 112, oy + 50, INK, 2)
    points = [(ox + 12, oy + 14), (ox + 30, oy + 20), (ox + 46, oy + 18),
              (ox + 62, oy + 30), (ox + 78, oy + 28), (ox + 94, oy + 40),
              (ox + 110, oy + 46)]
    s.polyline(points, CRIMSON, 2)
    s.segment(ox + 110, oy + 46, ox + 102, oy + 42, CRIMSON, 2)
    s.segment(ox + 110, oy + 46, ox + 104, oy + 38, CRIMSON, 2)
    s.disc(ox + 98, oy + 10, 3, GOLD)


def art_badge(s, ox, oy):
    # Five-point star badge with a crimson centre.
    cx, cy = ox + 30, oy + 28
    pts = []
    for n in range(10):
        r = 22 if n % 2 == 0 else 9
        a = -math.pi / 2 + n * math.pi / 5
        pts.append((cx + int(r * math.cos(a)), cy + int(r * math.sin(a))))
    s.polyline(pts + [pts[0]], GOLD, 3)
    s.disc(cx, cy, 4, CRIMSON)
    # Handcuffs: two linked rings at the lower right.
    s.ring(ox + 72, oy + 36, 9, INK, 2)
    s.ring(ox + 92, oy + 36, 9, INK, 2)
    s.segment(ox + 81, oy + 36, ox + 83, oy + 36, INK, 2)


def art_quake(s, ox, oy):
    # Ground line cracked by the tremor.
    s.hline(ox + 6, ox + 58, oy + 44, INK, 2)
    s.segment(ox + 58, oy + 44, ox + 64, oy + 50, INK, 2)
    s.hline(ox + 64, ox + 112, oy + 50, INK, 2)
    # Zigzag seismic trace above the ground.
    points = [(ox + 8, oy + 28), (ox + 22, oy + 28), (ox + 30, oy + 10),
              (ox + 38, oy + 40), (ox + 46, oy + 16), (ox + 54, oy + 34),
              (ox + 66, oy + 28), (ox + 80, oy + 28), (ox + 88, oy + 12),
              (ox + 96, oy + 36), (ox + 108, oy + 28)]
    s.polyline(points, CRIMSON, 2)
    # Small island rooftops shaken by the quake.
    for hx in (ox + 78, ox + 92):
        s.segment(hx, oy + 44, hx + 5, oy + 38, INK, 2)
        s.segment(hx + 10, oy + 44, hx + 5, oy + 38, INK, 2)


def art_robot(s, ox, oy):
    # Antenna with a blinking tip, then the head frame and glowing eyes.
    s.vline(ox + 38, oy + 4, oy + 14, INK, 2)
    s.disc(ox + 38, oy + 6, 3, CRIMSON)
    s.frame(ox + 16, oy + 14, ox + 60, oy + 44, INK, 2)
    s.fill(ox + 24, oy + 24, ox + 32, oy + 30, CRIMSON)
    s.fill(ox + 44, oy + 24, ox + 52, oy + 30, CRIMSON)
    # Grille mouth.
    for gx in (ox + 26, ox + 34, ox + 42):
        s.vline(gx, oy + 34, oy + 40, INK, 2)
    # Ears and a small "no" cross over the head.
    s.hline(ox + 10, ox + 16, oy + 26, INK, 2)
    s.hline(ox + 60, ox + 66, oy + 26, INK, 2)
    s.segment(ox + 76, oy + 10, ox + 92, oy + 26, CRIMSON, 2)
    s.segment(ox + 92, oy + 10, ox + 76, oy + 26, CRIMSON, 2)


def art_planet(s, ox, oy):
    # Ringed planet (Mercury) with its craters.
    cx, cy = ox + 34, oy + 30
    s.disc(cx, cy, 18, GOLD)
    s.disc(cx - 6, cy - 5, 3, INK)
    s.disc(cx + 5, cy + 6, 2, INK)
    s.disc(cx + 8, cy - 8, 2, INK)
    s.segment(ox + 6, oy + 40, ox + 62, oy + 18, SKY, 2)
    # Tiny orbiter with solar panels trailing behind.
    s.disc(ox + 88, oy + 14, 3, INK)
    s.hline(ox + 76, ox + 84, oy + 14, INK, 2)
    s.hline(ox + 92, ox + 100, oy + 14, INK, 2)
    s.segment(ox + 88, oy + 14, ox + 80, oy + 26, SKY, 2)
    s.segment(ox + 88, oy + 14, ox + 96, oy + 26, SKY, 2)


def art_pill(s, ox, oy):
    """Medicine capsule lying diagonally, with a gold health cross."""
    # Capsule lying diagonally, half red half white, ink outline.
    cx, cy = ox + 44, oy + 26
    s.segment(cx - 26, cy + 12, cx + 26, cy - 12, INK, 12)
    s.segment(cx - 26, cy + 12, cx + 26, cy - 12, CRIMSON, 10)
    s.segment(cx, cy, cx + 26, cy - 12, PAPER, 10)
    # Small cross of health beside the capsule.
    s.fill(ox + 92, oy + 14, ox + 100, oy + 34, GOLD)
    s.fill(ox + 86, oy + 20, ox + 106, oy + 28, GOLD)


ART = {
    "shield": art_shield,
    "chart": art_chart,
    "badge": art_badge,
    "quake": art_quake,
    "robot": art_robot,
    "planet": art_planet,
    "pill": art_pill,
}


# -------------------------------------------------------------- layout
def draw_lead(sheet, story):
    """Full-width lead story: kicker, big headline, deck, shield art."""
    sheet.write(MARGIN, 220, story["kicker"], 2, CRIMSON)
    ART[story["art"]](sheet, 848, 222)
    y = sheet.wrapped(MARGIN, 240, story["headline"], 4, INK, 806, 8)
    sheet.wrapped(MARGIN, y + 10, story["deck"], 2, INK,
                  PAGE_W - 2 * MARGIN, 5)


def draw_cell(sheet, story, x0, y0, width):
    """One grid cell: kicker, headline, deck, pictogram top right."""
    sheet.write(x0, y0, story["kicker"], 2, CRIMSON)
    ART[story["art"]](sheet, x0 + width - 118, y0 - 2)
    y = sheet.wrapped(x0, y0 + 22, story["headline"], 3, INK,
                      width - 132, 7)
    sheet.wrapped(x0, y + 8, story["deck"], 2, INK, width, 5)


def build_page():
    """Assemble the whole front page and return the finished sheet."""
    sheet = Sheet(PAGE_W, PAGE_H, PAPER)
    # Double frame around the page.
    sheet.frame(14, 14, PAGE_W - 14, PAGE_H - 14, INK, 3)
    sheet.frame(22, 22, PAGE_W - 22, PAGE_H - 22, INK, 1)
    # Masthead and rules.
    sheet.centred(44, "THE WORLD TODAY", 8, INK)
    sheet.hline(MARGIN, PAGE_W - MARGIN, 114, INK, 2)
    sheet.hline(MARGIN, PAGE_W - MARGIN, 120, INK, 1)
    # Black date band and strapline.
    sheet.fill(MARGIN, 132, PAGE_W - MARGIN, 182, INK)
    sheet.centred(143, "SATURDAY, 21 NOVEMBER 2026", 4, PAPER)
    sheet.centred(194, "SEVEN STORIES - ONE DAY - REPORTED AROUND THE WORLD",
                  2, SLATE)
    # Lead story, then a rule.
    draw_lead(sheet, STORIES[0])
    sheet.hline(MARGIN, PAGE_W - MARGIN, 358, INK, 1)
    # Two-by-three grid of the remaining stories.
    col_w = (PAGE_W - 2 * MARGIN - COL_GAP) // 2
    for row, top in enumerate(ROW_TOPS):
        for col in range(2):
            story = STORIES[1 + row * 2 + col]
            x0 = MARGIN + col * (col_w + COL_GAP)
            draw_cell(sheet, story, x0, top, col_w)
        if row < 2:
            sheet.hline(MARGIN, PAGE_W - MARGIN, top + 176, INK, 1)
    sheet.vline(MARGIN + col_w + COL_GAP // 2, ROW_TOPS[0], GRID_BOTTOM,
                INK, 1)
    # Footer.
    sheet.hline(MARGIN, PAGE_W - MARGIN, 946, INK, 1)
    sheet.centred(962, "ALL STORIES FIRST REPORTED SATURDAY 21 NOVEMBER 2026.",
                  2, SLATE)
    return sheet


# ------------------------------------------------------------ PNG out
def encode_png(sheet):
    """Encode the sheet as a PNG: filter 0 rows, zlib level 9."""
    raw = bytearray()
    stride = sheet.width * 3
    for y in range(sheet.height):
        raw.append(0)
        raw += sheet.buf[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        out += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return out

    ihdr = struct.pack(">IIBBBBB", sheet.width, sheet.height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    out_path = Path(__file__).resolve().parent.parent / "news-21-nov-2026.png"
    out_path.write_bytes(encode_png(build_page()))
    print(f"wrote {out_path} ({out_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
