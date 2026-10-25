"""All graphics are generated in code: no image or font files to ship."""
import random
import zlib

import pygame

D = pygame.draw

THEME = {
    "plains": dict(ground=(96, 176, 64), wall=(150, 120, 88), tree=(40, 120, 48), water=(48, 96, 224)),
    "forest": dict(ground=(60, 140, 60), wall=(120, 100, 80), tree=(24, 88, 40), water=(40, 88, 200)),
    "desert": dict(ground=(228, 204, 136), wall=(196, 140, 88), tree=(60, 150, 70), water=(56, 120, 220)),
    "volcano": dict(ground=(92, 68, 68), wall=(72, 48, 48), tree=(60, 40, 40), water=(60, 70, 160)),
    "graveyard": dict(ground=(104, 130, 106), wall=(110, 110, 128), tree=(60, 72, 60), water=(50, 80, 150)),
    "beach": dict(ground=(236, 214, 150), wall=(160, 130, 100), tree=(40, 140, 60), water=(48, 110, 230)),
}
DUNGEON = {
    "forest": ((64, 96, 64), (36, 80, 52)), "crypt": ((76, 76, 90), (44, 44, 64)),
    "desert": ((196, 164, 104), (140, 100, 60)), "water": ((64, 96, 150), (34, 54, 108)),
    "citadel": ((88, 62, 104), (52, 32, 74)), "cave": ((28, 24, 32), (66, 56, 70)),
}
GLYPHS = {
    "A": "### #.# ### #.# #.#", "B": "##. #.# ##. #.# ##.", "C": "### #.. #.. #.. ###",
    "D": "##. #.# #.# #.# ##.", "E": "### #.. ##. #.. ###", "F": "### #.. ##. #.. #..",
    "G": "### #.. #.# #.# ###", "H": "#.# #.# ### #.# #.#", "I": "### .#. .#. .#. ###",
    "J": "..# ..# ..# #.# ###", "K": "#.# #.# ##. #.# #.#", "L": "#.. #.. #.. #.. ###",
    "M": "#.# ### ### #.# #.#", "N": "### #.# #.# #.# #.#", "O": "### #.# #.# #.# ###",
    "P": "### #.# ### #.. #..", "Q": "### #.# #.# ### ..#", "R": "##. #.# ##. #.# #.#",
    "S": "### #.. ### ..# ###", "T": "### .#. .#. .#. .#.", "U": "#.# #.# #.# #.# ###",
    "V": "#.# #.# #.# #.# .#.", "W": "#.# #.# ### ### #.#", "X": "#.# #.# .#. #.# #.#",
    "Y": "#.# #.# .#. .#. .#.", "Z": "### ..# .#. #.. ###",
    "0": "### #.# #.# #.# ###", "1": ".#. ##. .#. .#. ###", "2": "### ..# ### #.. ###",
    "3": "### ..# ### ..# ###", "4": "#.# #.# ### ..# ..#", "5": "### #.. ### ..# ###",
    "6": "### #.. ### #.# ###", "7": "### ..# ..# ..# ..#", "8": "### #.# ### #.# ###",
    "9": "### #.# ### ..# ###", ".": "... ... ... ... .#.", ",": "... ... ... .#. #..",
    "!": ".#. .#. .#. ... .#.", "?": "### ..# .## ... .#.", "'": ".#. .#. ... ... ...",
    "-": "... ... ### ... ...", ":": "... .#. ... .#. ...", "/": "..# ..# .#. #.. #..",
    "(": ".## .#. .#. .#. .##", ")": "##. .#. .#. .#. ##.", "%": "#.# ..# .#. #.. #.#",
    "+": "... .#. ### .#. ...", "x": "... #.# .#. #.# ...", " ": "... ... ... ... ...",
    ">": "#.. ##. ### ##. #..", "<": "..# .## ### .## ..#", "=": "... ### ... ### ...",
    "$": ".## ##. .#. .## ##.", "*": "#.# .#. ### .#. #.#",
}

HERO = {
    "down": ["................", ".....KKKKKK.....", "....KGGGGGGK....", "...KGGGGGGGGK...", "...KGGGGGGGGK...",
             "...KHSSSSSSHK...", "...KSKSSSSKSK...", "...KSSSSSSSSK...", "....KSSSSSSK....",
             "...KGGGGGGGGK...", "..KSKGGBBGGKSK..", "..KSKGGGGGGKSK..", "...KKGGGGGGKK...",
             "....KGGKKGGK....", "....KBBK.KBBK...", "....KKK...KKK..."],
    "up": ["................", ".....KKKKKK.....", "....KGGGGGGK....", "...KGGGGGGGGK...", "...KGGGGGGGGK...",
           "...KHHHHHHHHK...", "...KHHHHHHHHK...", "...KHHHHHHHHK...", "....KHHHHHHK....",
           "...KGGGGGGGGK...", "..KSKGGBBGGKSK..", "..KSKGGGGGGKSK..", "...KKGGGGGGKK...",
           "....KGGKKGGK....", "....KBBK.KBBK...", "....KKK...KKK..."],
    "right": ["................", ".....KKKKKK.....", "....KGGGGGGK....", "...KGGGGGGGGGK..", "...KGGGGGGGGK...",
              "...KHHSSSSSK....", "...KHHSSSKSK....", "...KHHSSSSSSK...", "....KHSSSSSK....",
              "....KGGGGGGK....", "...KGGGBBGGSK...", "...KGGGGGGSSK...", "....KGGGGGGK....",
              "....KGGKKGGK....", "....KBBK.KBBK...", "....KKK...KKK..."],
}
HERO_PAL = {"K": (24, 16, 28), "G": (56, 176, 80), "S": (252, 208, 160), "H": (170, 96, 36), "B": (124, 68, 28)}
OLDMAN = ["................", "......KKKK......", ".....KWWWWK.....", "....KWWWWWWK....", "....KWSSSSWK....",
          "....KWKSSKWK....", "....KWSSSSWK....", "....KWWWWWWK....", ".....KWWWWK.....",
          "....KRRRRRRK....", "...KRRRRRRRRK...", "...KRRRRRRRRK...", "...KRRRRRRRRK...",
          "...KRRRRRRRRK...", "...KKKKKKKKKK...", "................"]


def surf(w=16, h=16):
    return pygame.Surface((w, h), pygame.SRCALPHA)


def art(rows, pal, flip=False):
    s = surf(len(rows[0]), len(rows))
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in pal:
                s.fill(pal[ch], (15 - x if flip else x, y, 1, 1))
    return s


def shade(c, k):
    return tuple(max(0, min(255, int(v * k))) for v in c)


def facings(fn):
    """Build a {facing: surface} dict from fn(surface, facing)."""
    out = {}
    for f in ("up", "down", "left", "right"):
        s = surf(8, 8)
        fn(s, f)
        out[f] = s
    return out


class Assets:
    def __init__(self):
        self.tiles, self.texts = {}, {}
        self.sprites = {}
        self._build_sprites()

    # ------------------------------------------------------------------ text
    def text(self, msg, color=(252, 252, 252), scale=1):
        key = (msg, color, scale)
        s = self.texts.get(key)
        if s is None:
            s = surf(max(1, len(msg) * 4 * scale), 5 * scale)
            for i, ch in enumerate(msg.upper()):
                rows = GLYPHS.get(ch, GLYPHS["?"]).split()
                for y, row in enumerate(rows):
                    for x, bit in enumerate(row):
                        if bit == "#":
                            s.fill(color, ((i * 4 + x) * scale, y * scale, scale, scale))
            if len(self.texts) > 800:
                self.texts.clear()
            self.texts[key] = s
        return s

    # ------------------------------------------------------------------ tiles
    def tile(self, ch, key, frame=0):
        k = (ch, key, frame)
        s = self.tiles.get(k)
        if s is None:
            s = self.tiles[k] = self._draw_tile(ch, key, frame)
        return s

    def _draw_tile(self, ch, key, frame):
        s = surf()
        rng = random.Random(zlib.crc32((ch + key).encode()))
        dg = key.startswith("dg:")
        if dg:
            floor, wall = DUNGEON[key[3:]]
            ground, wallc, tree, water = floor, wall, shade(floor, 0.5), (40, 80, 200)
        else:
            t = THEME[key] if key in THEME else THEME["plains"]
            ground, wallc, tree, water = t["ground"], t["wall"], t["tree"], t["water"]
        speck = shade(ground, 0.88)

        def floor_fill(color=ground, specks=5):
            s.fill(color)
            for _ in range(specks):
                s.fill(shade(color, 0.88), (rng.randint(0, 14), rng.randint(0, 14), 2, 1))

        if ch in ".,:sw_":
            base = {".": ground, ",": ground, ":": shade(ground, 0.8) if dg else (190, 154, 100),
                    "s": (232, 208, 144), "_": (150, 40, 52), "w": (110, 160, 240)}[ch]
            floor_fill(base, 0 if ch == "_" else 5)
            if dg and ch == ".":
                D.rect(s, shade(ground, 0.9), (0, 0, 16, 16), 1)
            if ch == "_":
                D.rect(s, (110, 24, 36), (1, 1, 14, 14), 1)
                D.rect(s, (214, 170, 60), (7, 7, 2, 2))
            if ch == ",":
                for fx, fy in ((3, 4), (10, 9), (6, 12)):
                    s.fill((252, 252, 252), (fx, fy, 2, 2))
                    s.fill((252, 200, 60), (fx, fy, 1, 1))
        elif ch == "#":
            if dg:
                s.fill(wallc)
                for row in range(4):
                    D.line(s, shade(wallc, 0.65), (0, row * 4 + 3), (15, row * 4 + 3))
                    off = 4 if row % 2 else 0
                    for x in range(off, 16, 8):
                        D.line(s, shade(wallc, 0.65), (x, row * 4), (x, row * 4 + 3))
                s.fill(shade(wallc, 1.3), (0, 0, 16, 1))
            else:
                s.fill(wallc)
                D.polygon(s, shade(wallc, 0.7), [(0, 16), (16, 16), (16, 8), (11, 11), (6, 6), (0, 12)])
                D.polygon(s, shade(wallc, 1.25), [(0, 0), (16, 0), (16, 4), (9, 2), (4, 5), (0, 3)])
                D.line(s, shade(wallc, 0.55), (0, 15), (15, 15))
        elif ch == "X":
            s.fill(wallc)
            D.polygon(s, shade(wallc, 0.7), [(0, 16), (16, 16), (16, 9), (0, 11)])
            D.line(s, (30, 20, 20), (4, 1), (7, 6))
            D.line(s, (30, 20, 20), (7, 6), (5, 10))
            D.line(s, (30, 20, 20), (5, 10), (9, 15))
        elif ch == "T":
            floor_fill()
            D.circle(s, shade(tree, 0.7), (8, 8), 8)
            D.circle(s, tree, (7, 7), 6)
            D.circle(s, shade(tree, 1.35), (5, 5), 2)
        elif ch == "b":
            floor_fill()
            D.circle(s, shade(tree, 1.15), (8, 9), 6)
            D.circle(s, shade(tree, 1.5), (6, 7), 2)
            D.circle(s, shade(tree, 0.7), (11, 11), 2)
        elif ch == "H":
            floor_fill()
            D.circle(s, (88, 88, 98), (8, 9), 7)
            D.circle(s, (150, 150, 162), (6, 7), 4)
            D.circle(s, (200, 200, 210), (5, 5), 1)
        elif ch == "G":
            floor_fill()
            D.rect(s, (60, 60, 72), (4, 3, 8, 11))
            D.rect(s, (170, 170, 186), (4, 3, 7, 10))
            s.fill((90, 90, 104), (7, 4, 2, 6))
            s.fill((90, 90, 104), (5, 6, 6, 2))
        elif ch == "c":
            floor_fill((232, 208, 144))
            D.rect(s, (30, 110, 50), (6, 2, 4, 13))
            D.rect(s, (30, 110, 50), (2, 6, 4, 3))
            D.rect(s, (30, 110, 50), (10, 4, 4, 3))
            s.fill((90, 190, 100), (7, 3, 1, 10))
        elif ch == "~":
            s.fill(water)
            off = (frame * 3) % 8
            for i in range(2):
                x = (i * 8 + off) % 16
                D.line(s, shade(water, 1.5), (x, 4 + i * 7), (x + 3, 4 + i * 7))
        elif ch == "=":
            s.fill(water)
            D.rect(s, (150, 100, 52), (0, 2, 16, 12))
            for y in (5, 9):
                D.line(s, (96, 60, 28), (0, y), (15, y))
        elif ch == "l":
            s.fill((220, 80, 20) if frame == 0 else (240, 110, 30))
            for x, y in ((3, 4), (10, 9), (6, 12)):
                s.fill((252, 220, 80), (x + frame * 2, y, 3, 2))
        elif ch == "C":
            s.fill(wallc)
            D.rect(s, (8, 6, 12), (2, 3, 12, 13))
            D.rect(s, (8, 6, 12), (4, 1, 8, 4))
            D.rect(s, shade(wallc, 0.6), (2, 3, 12, 13), 1)
        elif ch == "D":
            s.fill(wallc)
            D.rect(s, (24, 4, 16), (1, 1, 14, 15))
            D.rect(s, (200, 40, 100), (1, 1, 14, 15), 2)
            D.rect(s, (8, 0, 8), (4, 4, 8, 12))
        elif ch == "K":
            s.fill(shade(wallc, 1.1))
            D.rect(s, shade(wallc, 0.6), (0, 0, 16, 16), 1)
            s.fill(shade(wallc, 1.5), (1, 1, 14, 2))
        elif ch == "B":
            s.fill(shade(wallc, 1.3))
            D.rect(s, shade(wallc, 0.55), (0, 0, 16, 16), 2)
            D.rect(s, shade(wallc, 0.75), (4, 4, 8, 8), 1)
        elif ch == "S":
            floor_fill()
            D.rect(s, (110, 110, 124), (4, 2, 8, 13))
            D.circle(s, (170, 170, 184), (8, 5), 4)
            s.fill((24, 20, 28), (6, 5, 1, 2))
            s.fill((24, 20, 28), (9, 5, 1, 2))
        elif ch == "O":
            floor_fill()
            D.rect(s, (90, 60, 30), (6, 8, 4, 7))
            D.circle(s, (252, 140, 30) if frame == 0 else (252, 190, 50), (8, 6), 4)
            D.circle(s, (252, 240, 140), (8, 7), 2)
        elif ch == "v":
            s.fill((4, 2, 6))
            D.rect(s, shade(ground, 0.6), (0, 0, 16, 16), 1)
        elif ch == "x":
            floor_fill()
            for x in (3, 8, 12):
                D.polygon(s, (190, 190, 200), [(x - 2, 14), (x + 2, 14), (x, 5)])
        else:
            s.fill((252, 0, 252))
        return s

    # ------------------------------------------------------------------ sprites
    def sprite(self, name, facing="down", frame=0):
        s = self.sprites.get(name) or self.sprites["missing"]
        if isinstance(s, dict):
            s = s.get(facing) or s["down"]
        if isinstance(s, list):
            s = s[frame % len(s)]
        return s

    def _build_sprites(self):
        sp = self.sprites
        sp["missing"] = art(["#" * 16] * 16, {"#": (252, 0, 252)})
        for f, rows in HERO.items():
            sp["player_" + f] = [art(rows, HERO_PAL), art(self._step(rows), HERO_PAL)]
        sp["player_left"] = [art(HERO["right"], HERO_PAL, True), art(self._step(HERO["right"]), HERO_PAL, True)]
        sp["oldman"] = art(OLDMAN, {"K": (24, 16, 28), "W": (240, 240, 240), "S": (252, 208, 160), "R": (150, 60, 40)})
        sp["merchant"] = art(OLDMAN, {"K": (24, 16, 28), "W": (230, 150, 50), "S": (252, 208, 160), "R": (60, 90, 160)})
        for name, fn in ENEMY_ART.items():
            sp[name] = [self._frame(fn, f, 16) for f in (0, 1)]
        for name, (fn, args) in BOSS_ART.items():
            sp[name] = [self._frame(lambda s, f, fn=fn, args=args: fn(s, f, *args), f, 32) for f in (0, 1)]
        for name, fn in ITEM_ART.items():
            sp["item_" + name] = self._frame(lambda s, f, fn=fn: fn(s), 0, 16)
        sp["rock"] = self._frame(lambda s, f: (D.circle(s, (130, 130, 140), (4, 4), 3), D.circle(s, (200, 200, 210), (3, 3), 1)), 0, 8)
        sp["fire"] = self._frame(lambda s, f: (D.circle(s, (240, 90, 20), (4, 4), 4), D.circle(s, (252, 220, 80), (4, 4), 2)), 0, 8)
        sp["magic"] = self._frame(lambda s, f: (D.circle(s, (130, 60, 200), (4, 4), 4), D.circle(s, (230, 190, 252), (4, 4), 2)), 0, 8)
        sp["bubble"] = self._frame(lambda s, f: (D.circle(s, (120, 220, 252), (4, 4), 4, 1), s.fill((255, 255, 255), (2, 2, 1, 1))), 0, 8)
        sp["energy"] = self._frame(lambda s, f: D.polygon(s, (252, 140, 40), [(4, 0), (8, 4), (4, 8), (0, 4)]), 0, 8)
        sp["bomb"] = [self._frame(lambda s, f, k=k: self._bomb(s, k), 0, 16) for k in (0, 1)]
        sp["boomerang"] = [self._frame(lambda s, f, k=k: self._boomerang(s, k), 0, 8) for k in range(4)]
        sp["spear"] = facings(lambda s, f: self._shaft(s, f, (200, 150, 90), (230, 230, 240)))
        sp["axe"] = facings(lambda s, f: self._shaft(s, f, (120, 80, 40), (200, 60, 60)))
        sp["arrow"] = facings(lambda s, f: self._shaft(s, f, (160, 110, 60), (240, 240, 250)))
        sp["beam"] = facings(lambda s, f: self._shaft(s, f, (120, 200, 252), (252, 252, 252)))
        sp["heart_full"], sp["heart_half"], sp["heart_empty"] = (self._small_heart(a) for a in ("full", "half", "empty"))

    @staticmethod
    def _step(rows):
        out = list(rows)
        out[13], out[14], out[15] = "....KGGKKGGK....", "...KBBK..KBBK...", "...KKK....KKK..."
        return out

    @staticmethod
    def _frame(fn, f, size):
        s = surf(size, size)
        fn(s, f)
        return s

    @staticmethod
    def _bomb(s, k):
        D.circle(s, (30, 30, 40), (8, 10), 5)
        D.circle(s, (90, 90, 110), (6, 8), 1)
        D.line(s, (180, 140, 80), (8, 5), (10, 2))
        s.fill((252, 200, 60) if k else (252, 90, 30), (10, 1, 2, 2))

    @staticmethod
    def _boomerang(s, k):
        pts = [[(1, 1), (7, 1), (7, 3), (3, 3), (3, 7), (1, 7)], [(7, 1), (7, 7), (5, 7), (5, 3), (1, 3), (1, 1)],
               [(7, 7), (1, 7), (1, 5), (5, 5), (5, 1), (7, 1)], [(1, 7), (1, 1), (3, 1), (3, 5), (7, 5), (7, 7)]][k]
        D.polygon(s, (230, 170, 60), pts)

    @staticmethod
    def _shaft(s, f, wood, tip):
        if f in ("left", "right"):
            D.line(s, wood, (0, 4), (7, 4))
            D.rect(s, tip, (5, 2, 3, 5) if f == "right" else (0, 2, 3, 5))
        else:
            D.line(s, wood, (4, 0), (4, 7))
            D.rect(s, tip, (2, 5, 5, 3) if f == "down" else (2, 0, 5, 3))

    @staticmethod
    def _small_heart(kind):
        s = surf(8, 8)
        rows = [".##.##..", "########", "########", "########", ".######.", "..####..", "...##...", "........"]
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                if ch == "#":
                    full = kind == "full" or (kind == "half" and x < 4)
                    s.fill((216, 40, 32) if full else (70, 20, 30), (x, y, 1, 1))
        if kind != "empty":
            s.fill((252, 180, 170), (1, 1, 1, 1))
        return s


# ---------------------------------------------------------------------- enemy and boss drawings
def _eyes(s, y=6, a=5, b=9):
    s.fill((252, 252, 252), (a, y, 2, 2))
    s.fill((252, 252, 252), (b, y, 2, 2))
    s.fill((20, 12, 20), (a + 1, y + 1, 1, 1))
    s.fill((20, 12, 20), (b + 1, y + 1, 1, 1))


def _legs(s, color, y, xs, f):
    for x in xs:
        s.fill(color, (x + (1 if f else 0), y, 2, 3))


def _rocktopus(s, f):
    D.ellipse(s, (216, 72, 40), (2, 2, 12, 11))
    D.rect(s, (160, 40, 20), (6, 9, 4, 3))
    _eyes(s)
    _legs(s, (160, 40, 20), 12, (2, 5, 9, 12), f)


def _boarman(s, f):
    D.rect(s, (120, 70, 30), (4, 1, 8, 5))
    D.rect(s, (230, 160, 90), (5, 3, 6, 4))
    s.fill((20, 12, 20), (6, 4, 1, 1))
    s.fill((20, 12, 20), (9, 4, 1, 1))
    D.rect(s, (200, 90, 40), (3, 7, 10, 6))
    D.line(s, (230, 230, 240), (13, 2), (13, 13))
    _legs(s, (90, 50, 20), 12, (4, 9), f)


def _goblin(s, f):
    D.circle(s, (80, 170, 70), (8, 5), 4)
    _eyes(s, 4, 5, 9)
    D.rect(s, (60, 110, 120), (4, 8, 8, 5))
    D.line(s, (120, 80, 40), (13, 3), (13, 13))
    D.rect(s, (200, 60, 60), (11, 2, 4, 3))
    _legs(s, (60, 50, 30), 12, (4, 9), f)


def _centaur(s, f):
    D.ellipse(s, (170, 90, 40), (1, 5, 14, 9))
    D.circle(s, (230, 190, 130), (8, 4), 3)
    D.rect(s, (90, 40, 20), (5, 1, 6, 2))
    _eyes(s, 3, 6, 9)
    _legs(s, (110, 60, 30), 12, (2, 5, 9, 12), f)


def _hopper(s, f):
    D.circle(s, (60, 100, 220), (8, 8), 5)
    _eyes(s, 6)
    for x in (1, 13):
        D.line(s, (30, 50, 150), (x, 4), (x + (2 if f else 0), 12))
    D.line(s, (30, 50, 150), (3, 12), (3, 14 + f))
    D.line(s, (30, 50, 150), (12, 12), (12, 14 + f))


def _slime(s, f):
    D.ellipse(s, (70, 200, 110), (2, 6 + f, 12, 9 - f))
    s.fill((200, 252, 210), (5, 8 + f, 2, 1))
    _eyes(s, 9 + f, 5, 9)


def _burrower(s, f):
    D.ellipse(s, (230, 200, 130), (1, 8, 14, 7))
    D.circle(s, (170, 120, 70), (8, 7), 4)
    _eyes(s, 5)


def _lurker(s, f):
    D.circle(s, (60, 120, 230), (8, 8), 5)
    _eyes(s, 6)
    D.ellipse(s, (160, 210, 252), (1, 11, 14, 4), 1)


def _bat(s, f):
    D.circle(s, (60, 30, 90), (8, 8), 3)
    D.polygon(s, (90, 50, 130), [(8, 7), (0, 3 + f * 4), (3, 9)])
    D.polygon(s, (90, 50, 130), [(8, 7), (16, 3 + f * 4), (13, 9)])
    s.fill((252, 80, 80), (6, 7, 1, 1))
    s.fill((252, 80, 80), (9, 7, 1, 1))


def _skeleton(s, f):
    D.circle(s, (240, 240, 230), (8, 4), 3)
    s.fill((20, 12, 20), (6, 3, 1, 2))
    s.fill((20, 12, 20), (9, 3, 1, 2))
    D.rect(s, (230, 230, 220), (6, 7, 4, 5))
    for y in (8, 10):
        D.line(s, (60, 60, 70), (6, y), (9, y))
    _legs(s, (230, 230, 220), 12, (5, 9), f)
    D.line(s, (230, 230, 220), (3, 8), (3, 12))
    D.line(s, (230, 230, 220), (12, 8), (12, 12))


def _snake(s, f):
    pts = [(2, 12), (5, 9 + f), (8, 12), (11, 9 + f), (13, 6)]
    D.line(s, (200, 60, 50), pts[0], pts[1], 3)
    D.line(s, (200, 60, 50), pts[1], pts[2], 3)
    D.line(s, (200, 60, 50), pts[2], pts[3], 3)
    D.line(s, (200, 60, 50), pts[3], pts[4], 3)
    D.circle(s, (230, 90, 70), (13, 5), 2)
    s.fill((252, 252, 80), (13, 4, 1, 1))


def _mage(s, f):
    D.polygon(s, (110, 50, 170), [(8, 4), (1, 15), (15, 15)])
    D.circle(s, (240, 200, 160), (8, 6), 3)
    D.polygon(s, (60, 20, 110), [(8, 0), (4, 5), (12, 5)])
    s.fill((252, 252, 80), (7, 6, 1, 1))
    s.fill((252, 252, 80), (9, 6, 1, 1))
    s.fill((200, 120, 252), (13, 6 + f, 2, 2))


def _knight(s, f):
    D.rect(s, (150, 160, 180), (4, 1, 8, 6))
    D.rect(s, (30, 30, 40), (6, 3, 4, 2))
    D.rect(s, (110, 120, 150), (3, 7, 10, 6))
    D.rect(s, (200, 60, 60), (2, 6, 5, 7))
    D.rect(s, (252, 220, 80), (2, 6, 5, 7), 1)
    _legs(s, (90, 100, 120), 12, (4, 9), f)


def _bladetrap(s, f):
    D.rect(s, (150, 150, 165), (2, 2, 12, 12))
    D.rect(s, (80, 80, 96), (2, 2, 12, 12), 1)
    D.polygon(s, (220, 220, 230), [(8, 0), (6, 3), (10, 3)])
    D.polygon(s, (220, 220, 230), [(8, 16), (6, 13), (10, 13)])
    D.polygon(s, (220, 220, 230), [(0, 8), (3, 6), (3, 10)])
    D.polygon(s, (220, 220, 230), [(16, 8), (13, 6), (13, 10)])
    D.circle(s, (200, 40, 40), (8, 8), 2)


def _wyrm(s, f, body, belly, glow):
    D.ellipse(s, body, (2, 10, 22, 18))
    D.ellipse(s, belly, (6, 16, 14, 11))
    D.polygon(s, body, [(0, 27), (8, 22), (6, 31)])
    D.circle(s, body, (22, 8), 7)
    D.rect(s, body, (22, 8, 10, 7))
    D.rect(s, (30, 10, 20), (23, 13 + f * 2, 9, 3 - f))
    s.fill(glow, (20, 5, 3, 3))
    for x in (6, 11, 16):
        D.polygon(s, shade(body, 0.7), [(x, 10), (x + 3, 3), (x + 6, 10)])


def _crab(s, f, open_):
    D.ellipse(s, (210, 70, 50), (4, 8, 24, 20))
    D.ellipse(s, (240, 120, 80), (8, 11, 16, 9))
    for cx in (3, 29):
        D.circle(s, (230, 90, 60), (cx, 12 if open_ else 20), 5)
        if open_:
            D.polygon(s, (30, 10, 10), [(cx, 12), (cx - 3, 4), (cx + 3, 4)])
    for x in (11, 20):
        s.fill((252, 252, 252), (x, 13 if open_ else 18, 3, 3))
        s.fill((20, 10, 20), (x + 1, 14 if open_ else 19, 1, 2))
    if not open_:
        D.ellipse(s, (150, 40, 30), (4, 14, 24, 14))


def _magmamaw(s, f):
    D.rect(s, (110, 60, 50), (2, 3, 28, 27))
    D.rect(s, (60, 30, 30), (2, 3, 28, 27), 2)
    for x, y in ((6, 6), (22, 8), (10, 24), (24, 22)):
        D.line(s, (252, 140, 40), (x, y), (x + 3, y + 5))
    D.rect(s, (20, 6, 8), (7, 15, 18, 11 + f * 2))
    for x in range(8, 24, 4):
        D.polygon(s, (240, 240, 230), [(x, 15), (x + 3, 15), (x + 1, 20)])
    s.fill((252, 220, 60), (9, 8, 4, 3))
    s.fill((252, 220, 60), (19, 8, 4, 3))


def _warlock(s, f):
    D.polygon(s, (90, 40, 140), [(16, 6), (1, 31), (31, 31)])
    D.polygon(s, (60, 20, 100), [(16, 12), (8, 31), (24, 31)])
    D.circle(s, (230, 200, 170), (16, 9), 5)
    D.polygon(s, (252, 210, 60), [(10, 5), (11, 0), (14, 4), (16, 0), (18, 4), (21, 0), (22, 5)])
    s.fill((252, 60, 60), (13, 8, 2, 2))
    s.fill((252, 60, 60), (18, 8, 2, 2))
    D.line(s, (150, 100, 50), (28, 6), (28, 30), 2)
    D.circle(s, (230, 120, 252), (28, 5 + f), 3)


ENEMY_ART = {"rocktopus": _rocktopus, "boarman": _boarman, "goblin": _goblin, "centaur": _centaur,
             "hopper": _hopper, "slime": _slime, "burrower": _burrower, "lurker": _lurker, "bat": _bat,
             "skeleton": _skeleton, "snake": _snake, "mage": _mage, "knight": _knight, "bladetrap": _bladetrap}
BOSS_ART = {
    "thornwyrm": (_wyrm, ((60, 150, 70), (200, 220, 120), (252, 220, 60))),
    "frostwyrm": (_wyrm, ((90, 150, 230), (210, 235, 252), (252, 80, 80))),
    "tidecrab_open": (_crab, (True,)),
    "tidecrab_shut": (_crab, (False,)),
    "magmamaw": (lambda s, f: _magmamaw(s, f), ()),
    "warlock": (lambda s, f: _warlock(s, f), ()),
}


# ---------------------------------------------------------------------- item icons
def _gem(color):
    def draw(s):
        D.polygon(s, color, [(8, 2), (13, 7), (8, 14), (3, 7)])
        D.polygon(s, shade(color, 1.5), [(8, 2), (3, 7), (8, 7)])
        D.polygon(s, shade(color, 0.6), [(8, 14), (13, 7), (8, 7)])
    return draw


def _heart_big(s, scale_color=(216, 40, 32)):
    D.circle(s, scale_color, (5, 6), 4)
    D.circle(s, scale_color, (11, 6), 4)
    D.polygon(s, scale_color, [(1, 8), (15, 8), (8, 15)])
    s.fill((252, 190, 180), (3, 4, 2, 2))


def _key(color):
    def draw(s):
        D.circle(s, color, (8, 4), 3, 2)
        D.rect(s, color, (7, 6, 2, 8))
        D.rect(s, color, (9, 11, 3, 2))
        D.rect(s, color, (9, 8, 2, 2))
    return draw


def _sword(blade):
    def draw(s):
        D.polygon(s, blade, [(8, 0), (11, 3), (10, 11), (6, 11), (5, 3)])
        s.fill(shade(blade, 1.4), (7, 1, 1, 9))
        D.rect(s, (180, 130, 40), (3, 11, 10, 2))
        D.rect(s, (110, 60, 30), (7, 13, 2, 3))
    return draw


def _potion(color):
    def draw(s):
        D.circle(s, color, (8, 10), 5)
        D.rect(s, (230, 230, 240), (6, 2, 4, 5))
        D.rect(s, (160, 110, 60), (6, 1, 4, 2))
        s.fill((252, 252, 252), (5, 8, 1, 2))
    return draw


def _bomb_icon(s):
    Assets._bomb(s, 0)


def _bomb_pack(s):
    Assets._bomb(s, 0)
    D.circle(s, (30, 30, 40), (4, 12), 3)
    s.fill((252, 252, 252), (13, 11, 1, 3))
    s.fill((252, 252, 252), (12, 12, 3, 1))


def _map(s):
    D.rect(s, (230, 200, 130), (2, 2, 12, 12))
    D.rect(s, (130, 90, 40), (2, 2, 12, 12), 1)
    D.line(s, (200, 40, 40), (4, 10), (7, 6))
    D.line(s, (200, 40, 40), (7, 6), (11, 9))
    s.fill((200, 40, 40), (10, 4, 2, 2))


def _compass(s):
    D.circle(s, (210, 170, 60), (8, 8), 7)
    D.circle(s, (250, 250, 240), (8, 8), 5)
    D.polygon(s, (216, 40, 32), [(8, 3), (6, 8), (10, 8)])
    D.polygon(s, (60, 60, 80), [(8, 13), (6, 8), (10, 8)])


def _shard(s):
    D.polygon(s, (252, 220, 80), [(8, 0), (15, 14), (1, 14)])
    D.polygon(s, (252, 252, 200), [(8, 3), (11, 12), (5, 12)])
    D.polygon(s, (200, 140, 30), [(8, 14), (15, 14), (8, 0)], 1)


def _boomerang_icon(s):
    D.polygon(s, (230, 170, 60), [(2, 2), (13, 2), (13, 6), (6, 6), (6, 13), (2, 13)])
    D.polygon(s, (150, 100, 30), [(2, 2), (13, 2), (13, 6), (6, 6), (6, 13), (2, 13)], 1)


def _bow(s):
    D.line(s, (150, 100, 50), (4, 1), (12, 8), 2)
    D.line(s, (150, 100, 50), (12, 8), (4, 15), 2)
    D.line(s, (240, 240, 240), (4, 1), (4, 15))
    D.line(s, (200, 200, 210), (4, 8), (14, 8))


def _glove(s):
    D.rect(s, (180, 110, 50), (3, 6, 10, 8))
    for x in (3, 6, 9, 12):
        D.rect(s, (200, 130, 60), (x, 2, 2, 6))
    D.rect(s, (110, 60, 30), (3, 12, 10, 3))


def _fins(s):
    D.polygon(s, (60, 170, 220), [(2, 3), (14, 3), (14, 8), (9, 14), (3, 14)])
    D.polygon(s, (30, 100, 150), [(2, 3), (14, 3), (14, 8), (9, 14), (3, 14)], 1)
    for x in (5, 8, 11):
        D.line(s, (30, 100, 150), (x, 4), (x, 10))


def _lantern(s):
    D.rect(s, (100, 70, 40), (4, 3, 8, 11))
    D.rect(s, (252, 200, 80), (5, 5, 6, 7))
    D.circle(s, (252, 240, 160), (8, 8), 2)
    D.line(s, (100, 70, 40), (5, 2), (11, 2), 2)


ITEM_ART = {
    "gem1": _gem((60, 220, 110)), "gem5": _gem((70, 130, 250)), "gems": _gem((250, 80, 120)),
    "heart": _heart_big, "heart_container": lambda s: _heart_big(s, (240, 70, 60)),
    "heart_refill": _potion((220, 50, 60)), "potion": _potion((70, 190, 110)),
    "bomb": _bomb_icon, "bomb_pack": _bomb_pack, "bomb_bag": _bomb_pack,
    "small_key": _key((240, 220, 100)), "boss_key": _key((230, 70, 70)),
    "map": _map, "compass": _compass, "shard": _shard,
    "boomerang": _boomerang_icon, "bow": _bow, "glove": _glove, "fins": _fins, "lantern": _lantern,
    "sword_wood": _sword((190, 130, 70)), "sword_steel": _sword((200, 215, 235)), "sword_magic": _sword((250, 210, 90)),
}
