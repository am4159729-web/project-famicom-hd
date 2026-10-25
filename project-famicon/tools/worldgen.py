#!/usr/bin/env python3
"""Build famicon/data/overworld.json from the region plan below.

    python tools/worldgen.py [--seed N] [--preview docs/overworld.png]

The whole map is generated as one 256x88 tile grid and sliced into 16x11 screens,
so terrain is seamless across screen edges.
"""
import argparse
import random
import sys
from collections import deque
from pathlib import Path

TW, TH = 16, 11
COLS, ROWS = 16, 8
W, H = COLS * TW, ROWS * TH

REGIONS = [
    "FFFFFDDDDVVVGGGG",
    "FFFFFDDDDVVVGGGG",
    "FFFFFDDDDVVVGGGG",
    "WWWWWWWEEEEEEEEE",
    "WWWWWWWEEEEEEEEE",
    "WWWWWWWEEEEEEEEE",
    "WWWWWWWEEEEEEIIE",
    "WWWWWWWEEEEEEEEE",
]
THEMES = {"W": "plains", "E": "plains", "F": "forest", "D": "desert",
          "V": "volcano", "G": "graveyard", "I": "beach"}
BASE = {"W": ".", "E": ".", "F": ".", "D": "s", "V": ":", "G": ".", "I": "s"}
STAGE_NEEDED = {"W": 0, "F": 0, "E": 1, "G": 1, "V": 1, "D": 2, "I": 3}
STAGES = [{"sword"}, {"sword", "bomb"}, {"sword", "bomb", "glove"}, {"sword", "bomb", "glove", "fins"}]

START = (2, 6, 8, 7)  # screen x, screen y, tile x, tile y

# (screen x, screen y, side, kind): the border to the east ("E") or south ("S") of that screen
GATES = [
    (2, 2, "S", "open"),
    (6, 4, "E", "bomb"),
    (6, 2, "S", "glove"),
    (10, 2, "S", "open"),
    (13, 2, "S", "open"),
]

# (screen x, screen y, kind, id)
LANDMARKS = [
    (2, 6, "cave", "sword_cave"), (3, 5, "cave", "shop_west"), (5, 7, "cave", "hint_1"),
    (0, 4, "cave", "gems_1"), (6, 6, "cave", "hint_2"),
    (1, 7, "bush", "heart_1"), (4, 3, "bomb", "gems_2"),
    (2, 1, "dungeon", 1), (4, 0, "cave", "hint_3"), (1, 2, "cave", "shop_potion"),
    (0, 0, "bush", "heart_2"), (3, 2, "boulder", "gems_3"),
    (8, 4, "cave", "hint_4"), (9, 5, "cave", "steel_sword"), (10, 6, "cave", "shop_east"),
    (12, 4, "cave", "hint_5"), (11, 3, "bomb", "heart_3"), (15, 5, "bush", "gems_4"),
    (8, 7, "boulder", "heart_4"),
    (13, 1, "dungeon", 2), (12, 0, "cave", "magic_sword"), (15, 0, "bomb", "heart_5"),
    (14, 2, "bush", "gems_5"),
    (10, 1, "dungeon", 5), (9, 2, "cave", "hint_6"), (11, 0, "bomb", "heart_6"),
    (6, 1, "dungeon", 3), (8, 1, "cave", "hint_7"), (5, 0, "boulder", "gems_6"),
    (14, 6, "dungeon", 4), (13, 6, "bush", "gems_7"),
]

POOLS = {
    "W": ["rocktopus", "rocktopus", "hopper"],
    "F": ["boarman", "hopper", "rocktopus"],
    "E": ["boarman", "rocktopus", "burrower", "hopper"],
    "D": ["burrower", "burrower", "hopper"],
    "V": ["centaur", "hopper", "boarman"],
    "G": ["skeleton", "bat", "skeleton"],
    "I": ["rocktopus", "hopper"],
}
FLOORISH = set(".,:s")
COLORS = {
    ".": (88, 160, 72), ",": (110, 180, 90), ":": (176, 140, 90), "s": (222, 200, 140),
    "T": (24, 90, 40), "b": (50, 130, 60), "#": (112, 100, 96), "X": (150, 120, 110),
    "H": (130, 130, 140), "~": (40, 80, 200), "w": (90, 150, 230), "=": (150, 100, 50),
    "G": (170, 170, 180), "c": (60, 150, 80), "l": (230, 90, 30), "C": (0, 0, 0), "D": (200, 0, 120),
}


def region_at(x, y):
    if 0 <= x < W and 0 <= y < H:
        return REGIONS[y // TH][x // TW]
    return "?"


def walkable(ch, abilities):
    if ch in ".,:s=wCD":
        return True
    return {"b": "sword", "X": "bomb", "H": "glove", "~": "fins"}.get(ch) in abilities


def flood(grid, start, abilities):
    seen = {start}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < W and 0 <= ny < H and (nx, ny) not in seen and walkable(grid[ny][nx], abilities):
                seen.add((nx, ny))
                queue.append((nx, ny))
    return seen


class Builder:
    def __init__(self, seed):
        self.rng = random.Random(seed)
        self.grid = [[BASE[region_at(x, y)] for x in range(W)] for y in range(H)]
        self.protected = set()
        self.screens = {(sx, sy): {"caves": [], "secrets": [], "dungeon": None, "spawns": []}
                        for sx in range(COLS) for sy in range(ROWS)}
        self.landmark_cells = []  # (kind, id, region, x, y) in absolute tiles

    def put(self, x, y, ch, lock=False):
        if 0 <= x < W and 0 <= y < H:
            self.grid[y][x] = ch
            if lock:
                self.protected.add((x, y))

    def free(self, x, y):
        return 0 <= x < W and 0 <= y < H and (x, y) not in self.protected

    def scatter(self, region, ch, prob, only=FLOORISH):
        for y in range(H):
            for x in range(W):
                if region_at(x, y) == region and self.grid[y][x] in only and self.rng.random() < prob:
                    self.grid[y][x] = ch

    def blob(self, cx, cy, rx, ry, ch, ring=None):
        for y in range(cy - ry - 1, cy + ry + 2):
            for x in range(cx - rx - 1, cx + rx + 2):
                if not self.free(x, y):
                    continue
                d = ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2
                if d <= 1.0:
                    self.grid[y][x] = ch
                elif ring and d <= 1.7 and self.grid[y][x] in FLOORISH:
                    self.grid[y][x] = ring

    def smooth_trees(self, region, density, passes=2):
        cells = [(x, y) for y in range(H) for x in range(W) if region_at(x, y) == region]
        trees = {c for c in cells if self.rng.random() < density}
        for _ in range(passes):
            nxt = set()
            for x, y in cells:
                n = sum((x + dx, y + dy) in trees for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy)
                if n >= 5 or ((x, y) in trees and n >= 4):
                    nxt.add((x, y))
            trees = nxt
        for x, y in trees:
            self.grid[y][x] = "T"

    def decorate(self):
        r = self.rng
        self.smooth_trees("F", 0.46)
        self.scatter("F", "b", 0.03)
        for reg in "WE":
            self.smooth_trees(reg, 0.20, passes=1)
            self.scatter(reg, "b", 0.03)
            self.scatter(reg, ",", 0.07)
            for _ in range(14):
                x, y = r.randrange(W), r.randrange(H)
                if region_at(x, y) == reg and self.grid[y][x] in FLOORISH:
                    for dx in (0, 1):
                        for dy in (0, 1):
                            self.put(x + dx, y + dy, "#")
        self.scatter("D", "c", 0.035)
        self.scatter("V", "#", 0.10)
        self.scatter("I", "T", 0.04)
        self.scatter("G", "T", 0.03)
        for y in range(H):
            for x in range(W):
                if region_at(x, y) == "G" and x % 3 == 1 and y % 3 == 1 and self.grid[y][x] in FLOORISH and r.random() < 0.65:
                    self.grid[y][x] = "G"
        for reg, count, ch, ring in (("W", 3, "~", "w"), ("E", 3, "~", "w"), ("F", 1, "~", "w"),
                                     ("D", 1, "~", "w"), ("V", 5, "l", None)):
            for _ in range(count):
                for _try in range(40):
                    x, y = r.randrange(W), r.randrange(H)
                    if region_at(x, y) == reg and region_at(x - 5, y) == reg and region_at(x + 5, y) == reg \
                            and region_at(x, y - 4) == reg and region_at(x, y + 4) == reg:
                        self.blob(x, y, r.randint(2, 3), r.randint(1, 2), ch, ring)
                        break

    def borders(self):
        r = self.rng
        for sy in range(ROWS):
            for sx in range(COLS):
                reg = REGIONS[sy][sx]
                if sx + 1 < COLS and REGIONS[sy][sx + 1] != reg:
                    water = "I" in (reg, REGIONS[sy][sx + 1])
                    x0 = (sx + 1) * TW
                    for y in range(sy * TH, (sy + 1) * TH):
                        j = r.choice((-1, 0, 0, 1))
                        lo, hi = (x0 - 3, x0 + 3) if water else (x0 - 2, x0 + 2)
                        for x in range(lo + j, hi + j):
                            self.put(x, y, "~" if water else "#", lock=True)
                if sy + 1 < ROWS and REGIONS[sy + 1][sx] != reg:
                    water = "I" in (reg, REGIONS[sy + 1][sx])
                    y0 = (sy + 1) * TH
                    for x in range(sx * TW, (sx + 1) * TW):
                        j = r.choice((-1, 0, 0, 1))
                        lo, hi = (y0 - 2, y0 + 2) if water else (y0 - 1, y0 + 1)
                        for y in range(lo + j, hi + j):
                            self.put(x, y, "~" if water else "#", lock=True)
        for x in range(W):
            self.put(x, 0, "#", True)
            self.put(x, H - 1, "#", True)
        for y in range(H):
            self.put(0, y, "#", True)
            self.put(W - 1, y, "#", True)

    def gates(self):
        barrier = {"bomb": "X", "glove": "H"}
        for sx, sy, side, kind in GATES:
            if side == "E":
                x0, y0 = (sx + 1) * TW, sy * TH + 4
                for y in range(y0 - 1, y0 + 3):
                    for x in list(range(x0 - 7, x0 - 3)) + list(range(x0 + 3, x0 + 7)):
                        self.put(x, y, ".")
                for y in (y0, y0 + 1):
                    for x in range(x0 - 4, x0 + 4):
                        self.put(x, y, ".")
                    if kind != "open":
                        self.put(x0, y, barrier[kind], lock=True)
            else:
                x0, y0 = sx * TW + 7, (sy + 1) * TH
                for x in range(x0 - 1, x0 + 3):
                    for y in list(range(y0 - 6, y0 - 3)) + list(range(y0 + 3, y0 + 6)):
                        self.put(x, y, ".")
                for x in (x0, x0 + 1):
                    for y in range(y0 - 3, y0 + 3):
                        self.put(x, y, ".")
                    if kind != "open":
                        self.put(x, y0, barrier[kind], lock=True)

    def clear_start(self):
        sx, sy, tx, ty = START
        cx, cy = sx * TW + tx, sy * TH + ty
        for y in range(cy - 3, cy + 3):
            for x in range(cx - 5, cx + 6):
                if self.free(x, y):
                    self.grid[y][x] = "."

    def outcrop(self, sx, sy, w, h, entrance):
        r = self.rng
        for strict in (True, False):
            cands = []
            for ty in range(h + 1, 9):
                for tx in range(2 + w // 2, 14 - w // 2):
                    x0 = sx * TW + tx - w // 2
                    y0 = sy * TH + ty - h + 1
                    cells = [(x, y) for y in range(y0 - 1, y0 + h + 1) for x in range(x0 - 1, x0 + w + 1)]
                    if any(not self.free(x, y) for x, y in cells):
                        continue
                    if any(self.grid[y][x] in "~lCD=" for x, y in cells):
                        continue
                    if strict and any(self.grid[y][x] not in FLOORISH for x, y in cells):
                        continue
                    cands.append((tx, ty, x0, y0))
            if cands:
                tx, ty, x0, y0 = r.choice(cands)
                for y in range(y0, y0 + h):
                    for x in range(x0, x0 + w):
                        self.put(x, y, "#", lock=True)
                ax, ay = sx * TW + tx, sy * TH + ty
                self.put(ax, ay, entrance, lock=True)
                for x in range(x0 - 1, x0 + w + 1):
                    self.put(x, ay + 1, ".")
                return tx, ty
        raise RuntimeError(f"no room for landmark on screen {sx},{sy}")

    def landmarks(self):
        r = self.rng
        for sx, sy, kind, ident in LANDMARKS:
            scr = self.screens[(sx, sy)]
            region = REGIONS[sy][sx]
            if kind in ("cave", "dungeon"):
                tx, ty = self.outcrop(sx, sy, 5 if kind == "dungeon" else 3, 3 if kind == "dungeon" else 2,
                                      "D" if kind == "dungeon" else "C")
                if kind == "dungeon":
                    scr["dungeon"] = [tx, ty, ident]
                else:
                    scr["caves"].append([tx, ty, ident])
                self.landmark_cells.append((kind, ident, region, sx * TW + tx, sy * TH + ty))
            else:
                spots = [(tx, ty) for ty in range(2, 9) for tx in range(2, 14)
                         if self.free(sx * TW + tx, sy * TH + ty) and self.grid[sy * TH + ty][sx * TW + tx] in FLOORISH]
                tx, ty = r.choice(spots)
                self.put(sx * TW + tx, sy * TH + ty, {"bush": "b", "bomb": "X", "boulder": "H"}[kind], lock=True)
                scr["secrets"].append([tx, ty, ident])
                self.landmark_cells.append(("secret", ident, region, sx * TW + tx, sy * TH + ty))

    def repair(self):
        """Make every floor tile in a region reachable from that region's biggest open area."""
        for reg in set("".join(REGIONS)):
            cells = {(x, y) for y in range(H) for x in range(W)
                     if region_at(x, y) == reg and self.grid[y][x] in FLOORISH | {"=", "w"}}
            comps = []
            while cells:
                seed = cells.pop()
                comp, queue = {seed}, deque([seed])
                while queue:
                    x, y = queue.popleft()
                    for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                        if n in cells:
                            cells.discard(n)
                            comp.add(n)
                            queue.append(n)
                comps.append(comp)
            comps.sort(key=len, reverse=True)
            main = set(comps[0])
            for comp in comps[1:]:
                self.connect(comp, main, reg)
                main |= comp

    def connect(self, comp, main, reg):
        prev = {c: None for c in comp}
        queue = deque(comp)
        hit = None
        while queue and hit is None:
            x, y = queue.popleft()
            for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                nx, ny = n
                if n in prev or not self.free(nx, ny) or region_at(nx, ny) != reg or self.grid[ny][nx] in "~lCD":
                    continue
                prev[n] = (x, y)
                if n in main:
                    hit = n
                    break
                queue.append(n)
        if hit is None:
            for x, y in comp:
                self.grid[y][x] = "T"
            return
        cur = hit
        while cur is not None:
            x, y = cur
            if self.grid[y][x] not in FLOORISH | {"=", "w"}:
                self.grid[y][x] = "."
            cur = prev.get(cur)

    def spawns(self):
        r = self.rng
        start_abs = (START[0] * TW + START[2], START[1] * TH + START[3])
        near_marks = [(x, y) for _, _, _, x, y in self.landmark_cells]
        for (sx, sy), scr in self.screens.items():
            if (sx, sy) == (START[0], START[1]):
                continue
            reg = REGIONS[sy][sx]
            spots = []
            for ty in range(2, 9):
                for tx in range(2, 14):
                    x, y = sx * TW + tx, sy * TH + ty
                    if self.grid[y][x] in FLOORISH and all(abs(x - mx) + abs(y - my) > 3 for mx, my in near_marks):
                        spots.append((tx, ty))
            r.shuffle(spots)
            lo, hi = (1, 3) if reg in "WI" else (2, 4)
            for tx, ty in spots[:r.randint(lo, hi)]:
                scr["spawns"].append([r.choice(POOLS[reg]), tx, ty])
            water = [(tx, ty) for ty in range(2, 9) for tx in range(2, 14)
                     if all(self.grid[sy * TH + ty + dy][sx * TW + tx + dx] == "~" for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
            if len(water) >= 4:
                tx, ty = r.choice(water)
                scr["spawns"].append(["lurker", tx, ty])

    def build(self):
        self.decorate()
        self.borders()
        self.gates()
        self.clear_start()
        self.landmarks()
        self.repair()
        self.clear_start()
        self.spawns()
        return self


def check(b):
    start = (START[0] * TW + START[2], START[1] * TH + START[3])
    reach = [flood(b.grid, start, ab) for ab in STAGES]
    problems = []
    for kind, ident, region, x, y in b.landmark_cells:
        need = STAGE_NEEDED[region]
        probe = (x, y) if kind != "secret" else (x, y)
        if kind == "secret":
            if probe not in reach[3]:
                problems.append(f"secret {ident} unreachable even with every ability")
            continue
        if probe not in reach[need]:
            problems.append(f"{kind} {ident} in {region} not reachable at stage {need}")
        if need > 0 and probe in reach[need - 1]:
            problems.append(f"{kind} {ident} in {region} reachable too early (stage {need - 1})")
    return problems


def render_png(b, path, px=4):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (W * px, H * px))
    d = ImageDraw.Draw(img)
    for y in range(H):
        for x in range(W):
            d.rectangle([x * px, y * px, x * px + px - 1, y * px + px - 1], fill=COLORS.get(b.grid[y][x], (255, 0, 255)))
    for sx in range(1, COLS):
        d.line([(sx * TW * px, 0), (sx * TW * px, H * px)], fill=(0, 0, 0), width=1)
    for sy in range(1, ROWS):
        d.line([(0, sy * TH * px), (W * px, sy * TH * px)], fill=(0, 0, 0), width=1)
    for kind, ident, _, x, y in b.landmark_cells:
        color = {"dungeon": (255, 40, 40), "cave": (255, 230, 60), "secret": (60, 240, 240)}[kind]
        d.ellipse([x * px - 3, y * px - 3, x * px + 6, y * px + 6], outline=color, width=2)
    sx, sy, tx, ty = START
    x, y = (sx * TW + tx) * px, (sy * TH + ty) * px
    d.rectangle([x - 3, y - 3, x + 6, y + 6], outline=(255, 255, 255), width=2)
    img.save(path)


def dump(b, path):
    lines = ['{"cols": %d, "rows": %d, "start": %s,' % (COLS, ROWS, list(START)), ' "screens": [']
    items = []
    for sy in range(ROWS):
        for sx in range(COLS):
            scr = b.screens[(sx, sy)]
            rows = ["".join(b.grid[sy * TH + r][sx * TW:(sx + 1) * TW]) for r in range(TH)]
            body = ['  {"x": %d, "y": %d, "theme": "%s",' % (sx, sy, THEMES[REGIONS[sy][sx]]), '   "tiles": [']
            body += ['    "%s"%s' % (row, "," if i < TH - 1 else "") for i, row in enumerate(rows)]
            body.append("   ],")
            fields = []
            for key in ("spawns", "caves", "secrets", "dungeon"):
                fields.append('"%s": %s' % (key, repr(scr[key]).replace("'", '"').replace("None", "null")))
            body.append("   " + ", ".join(fields) + "}")
            items.append("\n".join(body))
    lines.append(",\n".join(items))
    lines.append(" ]}")
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=1986)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "famicon" / "data" / "overworld.json"))
    ap.add_argument("--preview")
    args = ap.parse_args()
    b = Builder(args.seed).build()
    problems = check(b)
    if problems:
        print("\n".join(problems), file=sys.stderr)
        sys.exit(1)
    dump(b, args.out)
    if args.preview:
        render_png(b, args.preview)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
