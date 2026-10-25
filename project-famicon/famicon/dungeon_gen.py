"""Procedural dungeons.

A dungeon is a tree of rooms on a grid. Locks sit on the main path to the boss and every key
is placed in the part of the dungeon reachable before its lock, so a generated dungeon cannot
soft-lock. `validate` re-checks all of that (plus door lanes and pickup counts).
"""
import random
from collections import deque

from .constants import SIDE_OPP
from .data.room_templates import COMBAT_TEMPLATES, TEMPLATES

SIDES = {"N": (0, -1), "S": (0, 1), "W": (-1, 0), "E": (1, 0)}
INWARD = {"N": [(7, 1), (8, 1)], "S": [(7, 9), (8, 9)], "W": [(1, 4), (1, 5)], "E": [(14, 4), (14, 5)]}

SPECS = {
    1: dict(name="Mossroot Hollow", theme="forest", size=(5, 4), rooms=9, locks=1, boss="thornwyrm",
            item="boomerang", pool=["bat", "slime", "snake"], dark=0.0),
    2: dict(name="Gravewatch Crypt", theme="crypt", size=(6, 4), rooms=11, locks=2, boss="tidecrab",
            item="glove", pool=["skeleton", "bat", "slime", "goblin"], dark=0.1),
    3: dict(name="Sunscar Pyramid", theme="desert", size=(6, 5), rooms=13, locks=2, boss="magmamaw",
            item="fins", pool=["snake", "goblin", "bat", "knight"], dark=0.2),
    4: dict(name="Drowned Spire", theme="water", size=(6, 5), rooms=14, locks=3, boss="frostwyrm",
            item="bow", pool=["slime", "mage", "goblin", "knight", "bat"], dark=0.25),
    5: dict(name="Crown Citadel", theme="citadel", size=(7, 5), rooms=17, locks=3, boss="warlock",
            item=None, pool=["knight", "mage", "goblin", "skeleton", "snake"], dark=0.25),
}


def edge_id(a, b):
    a, b = sorted((tuple(a), tuple(b)))
    return "%d,%d-%d,%d" % (a + b)


def side_between(a, b):
    for side, (dx, dy) in SIDES.items():
        if (a[0] + dx, a[1] + dy) == tuple(b):
            return side
    return None


def floor_cells(tiles, lanes=True):
    out = []
    for y in range(2, 9):
        for x in range(2, 14):
            if tiles[y][x] in "._" and not (lanes and 6 <= x <= 9 and 3 <= y <= 6):
                out.append((x, y))
    return out


def generate(num, seed=7):
    for attempt in range(400):
        d = _attempt(num, SPECS[num], random.Random(seed * 7919 + attempt))
        if d and not validate(d):
            return d
    raise RuntimeError("could not build dungeon %d" % num)


def _attempt(num, spec, rng):
    gw, gh = spec["size"]
    start = (gw // 2, gh - 1)
    cells, parent, depth = [start], {start: None}, {start: 0}
    while len(cells) < spec["rooms"]:
        base = rng.choice(cells)
        dx, dy = SIDES[rng.choice("NSEW")]
        c = (base[0] + dx, base[1] + dy)
        if 0 <= c[0] < gw and 0 <= c[1] < gh and c not in parent:
            parent[c], depth[c] = base, depth[base] + 1
            cells.append(c)
    kids = {c: [] for c in cells}
    for c, p in parent.items():
        if p:
            kids[p].append(c)
    leaves = [c for c in cells if not kids[c] and c != start]
    boss = max(leaves, key=lambda c: (depth[c], rng.random()))
    path = []
    c = boss
    while c:
        path.append(c)
        c = parent[c]
    path.reverse()
    candidates = list(range(1, len(path) - 2))
    if len(candidates) < spec["locks"]:
        return None
    lock_idx = sorted(rng.sample(candidates, spec["locks"]))
    lock_edges = [edge_id(path[i], path[i + 1]) for i in lock_idx]

    states = {edge_id(c, p): "open" for c, p in parent.items() if p}
    for e in lock_edges:
        states[e] = "locked"
    states[edge_id(path[-2], boss)] = "boss"

    index = {start: 0}
    queue = deque([start])
    while queue:
        c = queue.popleft()
        for n in kids[c]:
            index[n] = index[c] + (1 if states[edge_id(c, n)] == "locked" else 0)
            queue.append(n)

    # extra loops and one hidden (bomb) connection, never across a lock
    pairs = [(a, b) for a in cells for b in cells if a < b and side_between(a, b) and edge_id(a, b) not in states
             and index[a] == index[b] and boss not in (a, b)]
    rng.shuffle(pairs)
    for n, (a, b) in enumerate(pairs[:3]):
        states[edge_id(a, b)] = "bomb" if n == 0 else "open"

    used = {start, boss}
    roles = {start: "start", boss: "boss"}

    def take(role, pool):
        free = [c for c in pool if c not in used]
        if not free:
            return None
        free.sort(key=lambda c: (c in kids and bool(kids[c]), -depth[c], rng.random()))
        pick = free[0]
        used.add(pick)
        roles[pick] = role
        return pick

    everyone = [c for c in cells]
    item_room = take("item", [c for c in leaves if c != boss] or everyone)
    key_rooms = [take("key", [c for c in everyone if index[c] <= i]) for i in range(spec["locks"])]
    boss_key_room = take("bosskey", [c for c in everyone if index[c] <= spec["locks"]])
    map_room = take("map", [c for c in everyone if depth[c] <= 2 and index[c] == 0])
    compass_room = take("compass", everyone)
    if None in key_rooms or None in (item_room, boss_key_room, map_room, compass_room):
        return None

    rooms = []
    for c in cells:
        role = roles.get(c, "combat")
        tpl = {"start": "plain", "boss": "arena", "map": "torches", "compass": "puzzle"}.get(role)
        if tpl is None:
            tpl = rng.choice(COMBAT_TEMPLATES + (["torches"] if role != "combat" else []))
            if spec["theme"] == "citadel" and rng.random() < 0.25:
                tpl = "lava"
        tiles = list(TEMPLATES[tpl])
        enemies = 0 if role in ("start", "boss", "map", "compass") else min(5, 2 + depth[c] // 3 + (role != "combat"))
        cells_free = floor_cells(tiles)
        rng.shuffle(cells_free)
        spawns = [[rng.choice(spec["pool"]), x, y] for x, y in cells_free[:enemies]]
        if spec["theme"] == "citadel" and role == "combat" and tiles[2][2] == "." and rng.random() < 0.35:
            spawns.append(["bladetrap", 2, 2])
        drops = []
        pid = "d%d_%d%d" % (num, c[0], c[1])
        when = "clear" if spawns else "always"
        if role == "item":
            drops.append({"item": spec["item"] or "gems", "id": pid + "_item", "when": "clear"})
        elif role == "key":
            drops.append({"item": "small_key", "id": pid + "_key", "when": "clear"})
        elif role == "bosskey":
            drops.append({"item": "boss_key", "id": pid + "_bosskey", "when": "clear"})
        elif role == "map":
            drops.append({"item": "map", "id": pid + "_map", "when": "always"})
        elif role == "compass":
            drops.append({"item": "compass", "id": pid + "_compass", "when": "push"})
        if role == "boss":
            spawns = [["boss", spec["boss"], 7, 3]]
        doors = {}
        for side, (dx, dy) in SIDES.items():
            n = (c[0] + dx, c[1] + dy)
            doors[side] = states.get(edge_id(c, n), "wall") if n in parent else "wall"
        if c == start:
            doors["S"] = "exit"
        shutter = role in ("item", "key", "bosskey") or (role == "combat" and len(spawns) >= 3 and rng.random() < 0.4)
        rooms.append({
            "x": c[0], "y": c[1], "role": role, "template": tpl, "tiles": tiles, "doors": doors,
            "spawns": spawns, "drops": drops, "shutter": shutter and bool(spawns),
            "dark": role not in ("start", "boss") and rng.random() < spec["dark"],
            "push_opens": role == "compass",
        })
    return {"id": num, "name": spec["name"], "theme": spec["theme"], "start": list(start), "boss": list(boss),
            "boss_kind": spec["boss"], "item": spec["item"], "size": list(spec["size"]), "rooms": rooms}


def lane_ok(room):
    """Every non-wall door's inward cell must reach every other one inside the room."""
    tiles = room["tiles"]
    cells = [INWARD[s][0] for s, st in room["doors"].items() if st != "wall"]
    if len(cells) < 2:
        return True
    seen, queue = {cells[0]}, deque([cells[0]])
    while queue:
        x, y = queue.popleft()
        for n in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if n not in seen and 0 < n[0] < 15 and 0 < n[1] < 10 and tiles[n[1]][n[0]] in "._":
                seen.add(n)
                queue.append(n)
    return all(c in seen for c in cells)


def solvable(d):
    rooms = {(r["x"], r["y"]): r for r in d["rooms"]}
    start, boss = tuple(d["start"]), tuple(d["boss"])

    def has(reach, item):
        return sum(1 for p in reach for dr in rooms[p]["drops"] if dr["item"] == item)

    def explore(opened):
        boss_key = False
        while True:
            reach, queue = {start}, deque([start])
            while queue:
                p = queue.popleft()
                for side, st in rooms[p]["doors"].items():
                    dx, dy = SIDES[side]
                    q = (p[0] + dx, p[1] + dy)
                    if q not in rooms or q in reach:
                        continue
                    if st in ("open", "bomb") or (st == "locked" and edge_id(p, q) in opened) or (st == "boss" and boss_key):
                        reach.add(q)
                        queue.append(q)
            if (has(reach, "boss_key") > 0) == boss_key:
                return reach
            boss_key = not boss_key

    seen, stack = set(), [frozenset()]
    while stack:
        opened = stack.pop()
        if opened in seen:
            continue
        seen.add(opened)
        reach = explore(opened)
        if boss in reach:
            continue
        keys = has(reach, "small_key") - len(opened)
        moves = []
        for p in reach:
            for side, st in rooms[p]["doors"].items():
                dx, dy = SIDES[side]
                q = (p[0] + dx, p[1] + dy)
                if st == "locked" and q in rooms and q not in reach and keys > 0:
                    moves.append(opened | {edge_id(p, q)})
        if not moves:
            return False
        stack.extend(moves)
    return True


def validate(d):
    problems = []
    rooms = {(r["x"], r["y"]): r for r in d["rooms"]}
    if len(rooms) != len(d["rooms"]):
        problems.append("duplicate room coordinates")
    ids = []
    for pos, r in rooms.items():
        if len(r["tiles"]) != 11 or any(len(row) != 16 for row in r["tiles"]):
            problems.append("bad tile size at %s" % (pos,))
        for side, st in r["doors"].items():
            dx, dy = SIDES[side]
            n = (pos[0] + dx, pos[1] + dy)
            if n in rooms:
                if rooms[n]["doors"][SIDE_OPP[side]] != st:
                    problems.append("door mismatch %s %s" % (pos, side))
            elif st not in ("wall", "exit"):
                problems.append("door to nowhere %s %s" % (pos, side))
        if not lane_ok(r):
            problems.append("blocked door lane in room %s" % (pos,))
        for kind, x, y in [(s[0], s[-2], s[-1]) for s in r["spawns"]]:
            if kind != "boss" and r["tiles"][y][x] not in "._":
                problems.append("enemy on solid tile in %s" % (pos,))
        ids += [dr["id"] for dr in r["drops"]]
    if len(ids) != len(set(ids)):
        problems.append("duplicate pickup ids")
    drops = [dr["item"] for r in d["rooms"] for dr in r["drops"]]
    locks = sum(1 for r in d["rooms"] for st in r["doors"].values() if st == "locked") // 2
    if drops.count("small_key") != locks:
        problems.append("keys (%d) != locks (%d)" % (drops.count("small_key"), locks))
    for item in ("map", "compass", "boss_key"):
        if drops.count(item) != 1:
            problems.append("need exactly one %s" % item)
    if d["item"] and drops.count(d["item"]) != 1:
        problems.append("dungeon item missing")
    if not solvable(d):
        problems.append("not solvable")
    return problems
