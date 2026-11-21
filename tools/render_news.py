"""Draw the front page of THE WORLD TODAY for 21 November 2026.

Everything here is plain standard-library Python: a small pixel canvas,
a hand-made 5-by-7 blocky letter set, a few line-and-shape pictograms,
and a tiny PNG encoder. Running this file produces
``news-21-nov-2026.png`` next to the entry folder, 1024 by 1024 pixels,
and running it twice gives byte-identical output.
"""

import math
import os
import struct
import sys
import zlib

PAGE_W = 1024
PAGE_H = 1024
OUT_NAME = "news-21-nov-2026.png"

PAPER = (250, 243, 229)
INK = (18, 18, 18)
CRIMSON = (176, 32, 32)
NAVY = (36, 80, 148)
GOLD = (198, 150, 30)
PALE_BLUE = (214, 228, 244)
WHITE = (255, 255, 255)
GREY = (90, 86, 76)

# ---------------------------------------------------------------------------
# Letterforms. Each glyph is seven rows of five cells, '#' meaning ink.
# These shapes were drawn for this page; capitals, digits and the
# punctuation the headlines actually use.
# ---------------------------------------------------------------------------

GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#..##", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
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
    "0": (".###.", "#..##", "#.#.#", "##..#", "#...#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".....", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", "..#..", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"),
    "(": ("...##", "..#..", ".#...", ".#...", ".#...", "..#..", "...##"),
    ")": ("##...", "..#..", "...#.", "...#.", "...#.", "..#..", "##..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
}

CELL_W = 5
CELL_H = 7
CELL_GAP = 1  # one blank column between letters, in glyph units


def glyph_width(text, scale):
    """Width in pixels of *text* drawn at *scale*."""
    if not text:
        return 0
    per_char = (CELL_W + CELL_GAP) * scale
    return len(text) * per_char - CELL_GAP * scale


def wrap_words(text, scale, max_width):
    """Greedy word wrap; returns a list of lines that fit *max_width*."""
    lines = []
    current = ""
    for word in text.split(" "):
        trial = word if not current else current + " " + word
        if glyph_width(trial, scale) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# Pixel canvas
# ---------------------------------------------------------------------------

class Page:
    def __init__(self, width, height, background):
        self.width = width
        self.height = height
        self.buf = bytearray(bytes(background)) * (width * height)

    def dot(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            at = (y * self.width + x) * 3
            self.buf[at] = colour[0]
            self.buf[at + 1] = colour[1]
            self.buf[at + 2] = colour[2]

    def block(self, x, y, w, h, colour):
        x0 = max(x, 0)
        y0 = max(y, 0)
        x1 = min(x + w, self.width)
        y1 = min(y + h, self.height)
        for yy in range(y0, y1):
            base = (yy * self.width + x0) * 3
            for xx in range(x0, x1):
                at = base + (xx - x0) * 3
                self.buf[at] = colour[0]
                self.buf[at + 1] = colour[1]
                self.buf[at + 2] = colour[2]

    def frame(self, x, y, w, h, colour, thick=1):
        self.block(x, y, w, thick, colour)
        self.block(x, y + h - thick, w, thick, colour)
        self.block(x, y, thick, h, colour)
        self.block(x + w - thick, y, thick, h, colour)

    def rule(self, x, y, w, colour, thick=1):
        self.block(x, y, w, thick, colour)

    def stroke(self, x0, y0, x1, y1, colour):
        """Bresenham line, inclusive of both ends."""
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        x, y = x0, y0
        while True:
            self.dot(x, y, colour)
            if x == x1 and y == y1:
                return
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy

    def thick_stroke(self, x0, y0, x1, y1, radius, colour):
        steps = max(abs(x1 - x0), abs(y1 - y0), 1) + 1
        for i in range(steps):
            t = i / (steps - 1) if steps > 1 else 0.0
            cx = int(round(x0 + (x1 - x0) * t))
            cy = int(round(y0 + (y1 - y0) * t))
            self.disc(cx, cy, radius, colour)

    def disc(self, cx, cy, r, colour):
        for yy in range(cy - r, cy + r + 1):
            half = int(math.sqrt(max(r * r - (yy - cy) ** 2, 0)))
            self.block(cx - half, yy, 2 * half + 1, 1, colour)

    def ring(self, cx, cy, r, colour, thick=2):
        for rr in range(r - thick + 1, r + 1):
            for angle in range(360):
                rad = math.radians(angle)
                self.dot(cx + int(round(rr * math.cos(rad))),
                         cy + int(round(rr * math.sin(rad))), colour)

    def fill_poly(self, points, colour):
        """Scanline fill for a simple polygon given as (x, y) vertices."""
        if len(points) < 3:
            return
        ys = [p[1] for p in points]
        for yy in range(min(ys), max(ys) + 1):
            cuts = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    t = (yy - y0) / (y1 - y0)
                    cuts.append(int(round(x0 + t * (x1 - x0))))
            cuts.sort()
            for j in range(0, len(cuts) - 1, 2):
                self.block(cuts[j], yy, cuts[j + 1] - cuts[j] + 1, 1, colour)

    def poly_outline(self, points, colour):
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            self.stroke(x0, y0, x1, y1, colour)

    def spark(self, cx, cy, outer, inner, tips, colour, tilt=-90.0):
        """A star with *tips* points, filled."""
        pts = []
        for i in range(tips * 2):
            radius = outer if i % 2 == 0 else inner
            ang = math.radians(tilt + i * 180.0 / tips)
            pts.append((cx + int(round(radius * math.cos(ang))),
                        cy + int(round(radius * math.sin(ang)))))
        self.fill_poly(pts, colour)


# ---------------------------------------------------------------------------
# Text drawing
# ---------------------------------------------------------------------------

def draw_text(page, x, y, text, scale, colour):
    cursor = x
    for ch in text.upper():
        glyph = GLYPHS.get(ch, GLYPHS[" "])
        for row in range(CELL_H):
            for col in range(CELL_W):
                if glyph[row][col] == "#":
                    page.block(cursor + col * scale, y + row * scale,
                               scale, scale, colour)
        cursor += (CELL_W + CELL_GAP) * scale
    return cursor


def draw_centred(page, cx, y, text, scale, colour):
    draw_text(page, cx - glyph_width(text, scale) // 2, y, text, scale, colour)


def draw_lines(page, x, y, lines, scale, colour, pitch):
    for i, line in enumerate(lines):
        draw_text(page, x, y + i * pitch, line, scale, colour)


# ---------------------------------------------------------------------------
# Pictograms. Each one draws inside a small box (bx, by, bw, bh).
# ---------------------------------------------------------------------------

def pic_shield(page, bx, by, bw, bh):
    top = by + 6
    mid = by + int(bh * 0.55)
    bot = by + bh - 4
    pts = [(bx + 8, top), (bx + bw - 8, top), (bx + bw - 2, mid),
           (bx + bw // 2, bot), (bx + 2, mid)]
    page.fill_poly(pts, PALE_BLUE)
    page.poly_outline(pts, NAVY)
    page.spark(bx + bw // 2, by + int(bh * 0.38), 26, 9, 4, GOLD)
    page.disc(bx + bw // 2, by + int(bh * 0.38), 4, NAVY)


def pic_chart(page, bx, by, bw, bh):
    page.stroke(bx + 4, by + bh - 10, bx + bw - 4, by + bh - 10, INK)
    page.stroke(bx + 8, by + 6, bx + 8, by + bh - 10, INK)
    trail = [(bx + 12, by + 16), (bx + 30, by + 26), (bx + 44, by + 22),
             (bx + 62, by + 38), (bx + 76, by + 34), (bx + 92, by + 52)]
    for a, b in zip(trail, trail[1:]):
        page.thick_stroke(a[0], a[1], b[0], b[1], 2, CRIMSON)
    page.stroke(92 + bx - 0, by + 52, bx + 92, by + 52, CRIMSON)
    page.stroke(bx + 92, by + 52, bx + 82, by + 46, CRIMSON)
    page.stroke(bx + 92, by + 52, bx + 82, by + 58, CRIMSON)
    page.disc(bx + 30, by + 26, 3, GOLD)
    page.disc(bx + 62, by + 38, 3, GOLD)


def pic_badge(page, bx, by, bw, bh):
    page.spark(bx + 34, by + 34, 30, 13, 5, GOLD)
    page.spark(bx + 34, by + 34, 22, 10, 5, PALE_BLUE)
    page.disc(bx + 34, by + 34, 5, CRIMSON)
    page.ring(bx + 74, by + 56, 11, INK, 2)
    page.ring(bx + 92, by + 66, 11, INK, 2)
    page.stroke(bx + 74, by + 56, bx + 92, by + 66, INK)


def pic_seismo(page, bx, by, bw, bh):
    page.stroke(bx + 4, by + 30, bx + bw - 4, by + 30, INK)
    spikes = [(bx + 6, by + 30), (bx + 22, by + 30), (bx + 30, by + 12),
              (bx + 38, by + 48), (bx + 46, by + 20), (bx + 54, by + 30),
              (bx + 70, by + 30), (bx + 76, by + 18), (bx + 82, by + 42),
              (bx + 88, by + 30), (bx + bw - 4, by + 30)]
    for a, b in zip(spikes, spikes[1:]):
        page.thick_stroke(a[0], a[1], b[0], b[1], 1, CRIMSON)
    page.stroke(bx + 30, by + 58, bx + 44, by + 66, INK)
    page.stroke(bx + 44, by + 66, bx + 58, by + 58, INK)
    page.stroke(bx + 58, by + 58, bx + 72, by + 66, INK)


def pic_robot(page, bx, by, bw, bh):
    page.stroke(bx + 44, by + 4, bx + 44, by + 16, INK)
    page.disc(bx + 44, by + 4, 4, CRIMSON)
    page.frame(bx + 14, by + 16, 60, 44, INK, 2)
    page.block(bx + 26, by + 30, 10, 10, NAVY)
    page.block(bx + 52, by + 30, 10, 10, NAVY)
    page.stroke(bx + 30, by + 50, bx + 58, by + 50, INK)
    page.stroke(bx + 84, by + 18, bx + 98, by + 32, CRIMSON)
    page.stroke(bx + 98, by + 18, bx + 84, by + 32, CRIMSON)


def pic_planet(page, bx, by, bw, bh):
    page.disc(bx + 40, by + 38, 24, GOLD)
    page.disc(bx + 32, by + 30, 5, INK)
    page.disc(bx + 48, by + 44, 4, INK)
    page.disc(bx + 52, by + 28, 3, INK)
    page.stroke(bx + 8, by + 50, bx + 72, by + 26, NAVY)
    page.stroke(bx + 8, by + 54, bx + 72, by + 30, NAVY)
    # A small moon riding just above the ring, upper right.
    page.disc(bx + 80, by + 12, 5, NAVY)
    page.spark(bx + 84, by + 18, 12, 5, 4, NAVY)


def pic_capsule(page, bx, by, bw, bh):
    page.thick_stroke(bx + 16, by + 52, bx + 58, by + 22, 11, CRIMSON)
    page.thick_stroke(bx + 58, by + 22, bx + 66, by + 16, 11, WHITE)
    page.ring(bx + 16, by + 52, 12, INK, 2)
    page.ring(bx + 66, by + 16, 12, INK, 2)
    page.stroke(bx + 30, by + 44, bx + 52, by + 28, WHITE)
    page.block(bx + 82, by + 22, 8, 26, GOLD)
    page.block(bx + 73, by + 31, 26, 8, GOLD)


PICTOGRAMS = {
    "shield": pic_shield,
    "chart": pic_chart,
    "badge": pic_badge,
    "seismo": pic_seismo,
    "robot": pic_robot,
    "planet": pic_planet,
    "capsule": pic_capsule,
}


# ---------------------------------------------------------------------------
# Stories
# ---------------------------------------------------------------------------

LEAD = {
    "kicker": "EUROPE - NATO",
    "headline": "POLAND SEEKS MORE NATO AIR DEFENCES",
    "deck": ("WARSAW ASKS FOR MORE SUPPORT AFTER TWO RUSSIAN MISSILES AND A "
             "DRONE CAME DOWN: NATO CALLS IT A GRAVE VIOLATION."),
    "pic": "shield",
}

GRID = [
    {"kicker": "MARKETS",
     "headline": "NASDAQ PLUNGES 5.3% AS NVIDIA TUMBLES ON SEC PROBE REPORT",
     "deck": ("S AND P 500 FALLS 3.7% IN SEVENTH STRAIGHT LOSS: NVIDIA DOWN "
              "ABOUT 14% AFTER REUTERS REPORT."),
     "pic": "chart"},
    {"kicker": "LATIN AMERICA - CRIME",
     "headline": "MEXICO CAPTURES 'EL CHAPO ISIDRO' CARTEL BOSS",
     "deck": ("FAUSTO ISIDRO MEZA FLORES, ONE OF THE FBI'S 10 MOST WANTED, "
              "SEIZED IN GUASAVE, SINALOA."),
     "pic": "badge"},
    {"kicker": "ASIA-PACIFIC - QUAKE",
     "headline": "MAGNITUDE 6.8 QUAKE STRIKES OFF TIMOR-LESTE",
     "deck": ("TREMOR 103 KM NORTHEAST OF LOSPALOS AT 09:42 UTC: NO TSUNAMI "
              "THREAT, LOW RISK OF DAMAGE."),
     "pic": "seismo"},
    {"kicker": "DIPLOMACY - GENEVA",
     "headline": "UN TALKS AGREE TO DRAFT 'KILLER ROBOT' RULES",
     "deck": ("128 COUNTRIES IN GENEVA AGREE TO WORK TOWARD RULES FOR "
              "LETHAL AUTONOMOUS WEAPONS BY 2028."),
     "pic": "robot"},
    {"kicker": "SPACE",
     "headline": "BEPICOLOMBO REACHES MERCURY ORBIT AFTER EIGHT YEARS",
     "deck": ("EUROPE-JAPAN TWIN ORBITERS ENTER ORBIT 18:24 UTC: ONLY THE "
              "SECOND MISSION TO ORBIT MERCURY."),
     "pic": "planet"},
    {"kicker": "HEALTH",
     "headline": "PILL HAILED AS BREAKTHROUGH FOR PANCREATIC CANCER",
     "deck": ("DARAXONRASIB MADE TUMOURS UNDETECTABLE IN ONE IN 12 PATIENTS: "
              "NEARLY ALL TUMOURS STOPPED GROWING."),
     "pic": "capsule"},
]


# ---------------------------------------------------------------------------
# Page assembly
# ---------------------------------------------------------------------------

def build_front():
    page = Page(PAGE_W, PAGE_H, PAPER)
    page.frame(10, 10, PAGE_W - 20, PAGE_H - 20, INK, 2)
    page.frame(18, 18, PAGE_W - 36, PAGE_H - 36, INK, 1)

    # Masthead.
    draw_centred(page, PAGE_W // 2, 34, "THE WORLD TODAY", 9, INK)
    page.rule(30, 106, PAGE_W - 60, INK, 2)
    page.rule(30, 111, PAGE_W - 60, INK, 1)

    # Black date band.
    page.block(30, 120, PAGE_W - 60, 46, INK)
    draw_centred(page, PAGE_W // 2, 129, "SATURDAY, 21 NOVEMBER 2026",
                 4, WHITE)

    # Tagline and rule.
    draw_centred(page, PAGE_W // 2, 178,
                 "SEVEN STORIES - ONE DAY - REPORTED AROUND THE WORLD",
                 2, GREY)
    page.rule(30, 200, PAGE_W - 60, INK, 1)

    # Lead story, full width, pictogram on the right.
    lx, lw = 34, PAGE_W - 68
    draw_text(page, lx, 212, LEAD["kicker"], 2, CRIMSON)
    head_lines = wrap_words(LEAD["headline"], 4, lw - 150)
    draw_lines(page, lx, 234, head_lines, 4, INK, 34)
    # The deck also stops short of the shield on the right, so no line
    # of small type ever runs underneath the pictogram.
    deck_lines = wrap_words(LEAD["deck"], 2, lw - 150)
    draw_lines(page, lx, 308, deck_lines, 2, INK, 18)
    PICTOGRAMS[LEAD["pic"]](page, 852, 212, 110, 130)
    page.rule(30, 356, PAGE_W - 60, INK, 1)

    # Six more stories in a two-by-three grid.
    col_w = 466
    row_h = 172
    grid_top = 370
    for idx, story in enumerate(GRID):
        row, col = divmod(idx, 2)
        cx = 34 + col * 490
        cy = grid_top + row * row_h
        draw_text(page, cx, cy + 2, story["kicker"], 2, CRIMSON)
        lines = wrap_words(story["headline"], 3, col_w - 108)
        draw_lines(page, cx, cy + 24, lines, 3, INK, 27)
        deck = wrap_words(story["deck"], 2, col_w)
        draw_lines(page, cx, cy + 108, deck, 2, INK, 18)
        PICTOGRAMS[story["pic"]](page, cx + col_w - 104, cy + 22, 104, 80)

    # Grid dividers.
    page.block(512, grid_top, 1, row_h * 3 - 14, INK)
    for divider_y in (grid_top + row_h - 8, grid_top + 2 * row_h - 8):
        page.rule(34, divider_y, PAGE_W - 68, INK, 1)

    # Footer.
    page.rule(30, 928, PAGE_W - 60, INK, 1)
    draw_centred(page, PAGE_W // 2, 944,
                 "ALL STORIES FIRST REPORTED SATURDAY 21 NOVEMBER 2026.",
                 2, GREY)
    return page


# ---------------------------------------------------------------------------
# PNG encoding (filter 0, fixed compression: fully deterministic)
# ---------------------------------------------------------------------------

def _chunk(kind, payload):
    size = struct.pack(">I", len(payload))
    crc = struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
    return size + kind + payload + crc


def encode_png(page):
    raw = bytearray()
    for y in range(page.height):
        raw.append(0)
        start = y * page.width * 3
        raw += page.buf[start:start + page.width * 3]
    ihdr = struct.pack(">IIBBBBB", page.width, page.height, 8, 2, 0, 0, 0)
    blob = b"\x89PNG\r\n\x1a\n"
    blob += _chunk(b"IHDR", ihdr)
    blob += _chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    blob += _chunk(b"IEND", b"")
    return blob


def main(argv):
    out_path = argv[1] if len(argv) > 1 else os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        OUT_NAME)
    blob = encode_png(build_front())
    with open(out_path, "wb") as handle:
        handle.write(blob)
    print("wrote {} ({} bytes)".format(out_path, len(blob)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
