import json
from pathlib import Path

from .constants import DIRS, DOOR_CELLS, ROOM_H, ROOM_W, SIDE_DIR, TILE
from .dungeon_gen import edge_id
from .tiles import PITS, SOLID, WATER

DATA = Path(__file__).resolve().parent / "data"

INTERIOR_TILES = (
    ["#" * 16]
    + ["#" + "." * 14 + "#"] * 9
    + ["#" * 7 + ".." + "#" * 7]
)


class Room:
    """One screen: an overworld screen, a dungeon room or a cave interior."""

    def __init__(self, kind, key, tiles, theme="plains"):
        self.kind, self.key, self.theme = kind, key, theme
        self.tiles = [list(r) for r in tiles]
        self.doors, self.door_edges, self.door_side = {}, {}, {}
        self.exits = {d: False for d in DIRS}
        self.neighbor = {}
        self.spawns, self.drops = [], []
        self.caves, self.secrets = {}, {}
        self.gate = None
        self.dark = False
        self.shutter = False
        self.shut = False
        self.push_opens = False
        self.map_pos = (0, 0)
        self.interior = None
        self.cleared = False
        self.had_enemies = False

    def tile(self, tx, ty):
        if 0 <= tx < ROOM_W and 0 <= ty < ROOM_H:
            return self.tiles[ty][tx]
        return "#"

    def set_tile(self, tx, ty, ch):
        self.tiles[ty][tx] = ch

    def door_state(self, side):
        st = self.doors.get(side, "wall")
        return "shut" if self.shut and st not in ("wall", "bomb") else st

    def blocked(self, tx, ty, who):
        if not (0 <= tx < ROOM_W and 0 <= ty < ROOM_H):
            return not (who.is_player and self.can_leave(tx, ty, who))
        side = self.door_side.get((tx, ty))
        if side is not None:
            return self.door_state(side) not in ("open", "exit")
        ch = self.tiles[ty][tx]
        if ch in WATER:
            return not who.can_swim and not who.flying
        return ch in SOLID

    def can_leave(self, tx, ty, who):
        if tx < 0 and 0 <= ty < ROOM_H:
            d, ntx, nty = "left", ROOM_W - 1, ty
        elif tx >= ROOM_W and 0 <= ty < ROOM_H:
            d, ntx, nty = "right", 0, ty
        elif ty < 0 and 0 <= tx < ROOM_W:
            d, ntx, nty = "up", tx, ROOM_H - 1
        elif ty >= ROOM_H and 0 <= tx < ROOM_W:
            d, ntx, nty = "down", tx, 0
        else:
            return False
        if not self.exits[d]:
            return False
        if self.kind == "ow":
            ch = self.neighbor[d][nty][ntx]
            return ch not in SOLID and (ch not in WATER or who.can_swim)
        return True

    def collides(self, box, who):
        x, y, w, h = box
        x0, x1 = int(x // TILE), int((x + w - 0.001) // TILE)
        y0, y1 = int(y // TILE), int((y + h - 0.001) // TILE)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                if self.blocked(tx, ty, who):
                    return True
        return False

    def floor_at(self, px, py):
        tx, ty = int(px // TILE), int(py // TILE)
        return self.tile(tx, ty)

    def has_pit(self, px, py):
        return self.floor_at(px, py) in PITS


class World:
    def __init__(self, overworld, dungeons):
        self.start = overworld["start"]
        self.screens = {(s["x"], s["y"]): s for s in overworld["screens"]}
        self.dungeons = {}
        for d in dungeons["dungeons"]:
            meta = dict(d["meta"])
            meta["rooms"] = {(r["x"], r["y"]): r for r in d["rooms"]}
            self.dungeons[meta["id"]] = meta

    @classmethod
    def load(cls):
        ow = json.loads((DATA / "overworld.json").read_text(encoding="utf-8"))
        dg = json.loads((DATA / "dungeons.json").read_text(encoding="utf-8"))
        return cls(ow, dg)

    def overworld_room(self, sx, sy, flags):
        s = self.screens[(sx, sy)]
        room = Room("ow", "ow:%d,%d" % (sx, sy), s["tiles"], s["theme"])
        room.map_pos = (sx, sy)
        room.spawns = [list(sp) for sp in s["spawns"]]
        room.caves = {(tx, ty): iid for tx, ty, iid in s["caves"]}
        room.secrets = {(tx, ty): iid for tx, ty, iid in s["secrets"]}
        room.gate = tuple(s["dungeon"]) if s["dungeon"] else None
        for d, (dx, dy) in DIRS.items():
            nb = self.screens.get((sx + dx, sy + dy))
            room.exits[d] = nb is not None
            if nb:
                room.neighbor[d] = nb["tiles"]
        prefix = "gone:%s:" % room.key
        for flag in flags:
            if flag.startswith(prefix):
                tx, ty = map(int, flag[len(prefix):].split(","))
                was = room.tiles[ty][tx]
                if (tx, ty) in room.secrets:
                    room.tiles[ty][tx] = "C"
                    room.caves[(tx, ty)] = room.secrets[(tx, ty)]
                else:
                    room.tiles[ty][tx] = ":" if was == "X" else "."
        return room

    def dungeon_room(self, n, rx, ry, flags):
        d = self.dungeons[n]
        rd = d["rooms"][(rx, ry)]
        key = "dg:%d:%d,%d" % (n, rx, ry)
        room = Room("dg", key, rd["tiles"], d["theme"])
        room.map_pos = (rx, ry)
        for side, state in rd["doors"].items():
            dx, dy = DIRS[SIDE_DIR[side]]
            edge = edge_id((rx, ry), (rx + dx, ry + dy))
            room.door_edges[side] = edge
            if state in ("locked", "boss", "bomb") and "door:%d:%s" % (n, edge) in flags:
                state = "open"
            room.doors[side] = state
            if state != "wall":
                for cell in DOOR_CELLS[side]:
                    room.door_side[cell] = side
            room.exits[SIDE_DIR[side]] = state in ("open", "exit")
        cleared = "cleared:%s" % key in flags
        boss_dead = "boss:%d" % n in flags
        room.spawns = [list(s) for s in rd["spawns"] if not (cleared if s[0] != "boss" else boss_dead)]
        room.drops = [dict(dr) for dr in rd["drops"] if "taken:%s" % dr["id"] not in flags]
        room.shutter = rd["shutter"] and not cleared and bool(room.spawns)
        room.dark = rd["dark"]
        room.push_opens = rd["push_opens"] and "taken:%s" % (rd["drops"][0]["id"] if rd["drops"] else "") not in flags
        room.interior = None
        return room

    def interior_room(self, iid):
        room = Room("in", "in:%s" % iid, INTERIOR_TILES, "cave")
        room.exits["down"] = True
        return room
