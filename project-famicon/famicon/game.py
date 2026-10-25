"""Game core. No pygame in here: the app feeds it Controls each frame and reads state back out,
so the whole game can be simulated headless (see tests/)."""
import math
import random

from .constants import DIRS, DOOR_CELLS, OPPOSITE, PLAY_H, PLAY_W, ROOM_H, ROOM_W, SIDE, SIDE_DIR, TILE
from .data.interiors import INTERIORS
from .enemies import Enemy, build_enemy
from .entities import Boomerang, Effect, Entity, Pickup, Player, Projectile
from .inventory import MAJOR, SWORD_DAMAGE, Inventory, apply_item
from .tiles import CUTTABLE, HAZARD, PITS, SOLID
from .util import clamp, dist, overlap, wrap_text
from .world import World

SCROLL_FRAMES = 32
SAVE_VERSION = 1


class Npc(Entity):
    def __init__(self, x, y, sprite):
        super().__init__(x, y)
        self.sprite = sprite


class Probe:
    """Stands in for an entity when asking the room about free space."""
    is_player = False
    can_swim = False
    flying = False


class Game:
    def __init__(self, seed=None, world=None):
        self.world = world or World.load()
        self.rng = random.Random(seed)
        self.mode = "title"
        self.music = "title"
        self.sounds = []
        self.frame = 0
        self.title_cursor = 0
        self.want_quit = False
        self.loader = self.saver = None
        self.save_exists = False
        self.reset()

    # ------------------------------------------------------------------ setup / persistence
    def reset(self):
        self.inv = Inventory()
        self.flags = set()
        self.player = Player(0, 0)
        self.room = None
        self.entities = []
        self.dungeon = 0
        self.ret = None
        self.trans = self.fade = self.dialog = None
        self.menu = {"cursor": 0}
        self.banner = ["", 0]
        self.play_frames = 0
        self.hold_t = 0
        self.victory_t = 0
        self.gameover_cursor = 0

    def new_game(self):
        self.reset()
        sx, sy, tx, ty = self.world.start
        self.set_room(self.world.overworld_room(sx, sy, self.flags), tx * TILE, ty * TILE, "up")
        self.mode = "play"

    def to_save(self):
        return {"version": SAVE_VERSION, "inv": self.inv.to_dict(), "flags": sorted(self.flags),
                "frames": self.play_frames, "room": self.room.key, "pos": [self.player.x, self.player.y],
                "dungeon": self.dungeon, "ret": list(self.ret) if self.ret else None}

    def load_save(self, data):
        if data.get("version") != SAVE_VERSION:
            return False
        self.reset()
        self.inv = Inventory.from_dict(data["inv"])
        self.flags = set(data["flags"])
        self.play_frames = data.get("frames", 0)
        self.dungeon = data.get("dungeon", 0)
        self.ret = tuple(data["ret"]) if data.get("ret") else None
        kind, *rest = data["room"].split(":")
        px, py = data["pos"]
        if kind == "ow":
            sx, sy = map(int, rest[0].split(","))
            self.set_room(self.world.overworld_room(sx, sy, self.flags), px, py)
        elif kind == "dg":
            n, pos = int(rest[0]), rest[1]
            rx, ry = map(int, pos.split(","))
            self.set_room(self.world.dungeon_room(n, rx, ry, self.flags), px, py)
        else:  # saved inside a cave: stand outside it
            sx, sy, tx, ty = self.ret
            self.dungeon = 0
            self.set_room(self.world.overworld_room(sx, sy, self.flags), tx * TILE, (ty + 1) * TILE, "down")
        self.mode = "play"
        return True

    # ------------------------------------------------------------------ small helpers used by entities
    def sfx(self, name):
        self.sounds.append(name)

    def take_sounds(self):
        out, self.sounds = self.sounds, []
        return out

    def add(self, e):
        self.entities.append(e)
        return e

    def find(self, cls):
        return [e for e in self.entities if isinstance(e, cls) and not e.dead]

    def find_arrow(self):
        return [e for e in self.entities if isinstance(e, Projectile) and e.sprite == "arrow" and not e.dead]

    def effect(self, x, y, kind, life=16):
        self.entities.append(Effect(x, y, kind, life))

    def say_banner(self, text, frames=120):
        self.banner = [text, frames]

    def line_clear(self, a, b):
        steps = int(max(abs(a[0] - b[0]), abs(a[1] - b[1])) // 8) + 1
        for i in range(1, steps):
            x = a[0] + (b[0] - a[0]) * i / steps
            y = a[1] + (b[1] - a[1]) * i / steps
            if self.room.tile(int(x // TILE), int(y // TILE)) in SOLID:
                return False
        return True

    def random_floor(self, near=None, max_dist=None, min_dist=0, avoid=None, size=16):
        probe = Probe()
        for _ in range(40):
            if near is not None:
                a, r = self.rng.uniform(0, math.tau), self.rng.uniform(min_dist, max_dist or 64)
                x, y = near[0] + math.cos(a) * r - size / 2, near[1] + math.sin(a) * r - size / 2
            else:
                x, y = self.rng.randint(2, ROOM_W - 3) * TILE, self.rng.randint(2, ROOM_H - 3) * TILE
            x, y = clamp(x, 16, PLAY_W - 16 - size), clamp(y, 16, PLAY_H - 16 - size)
            box = (x + 2, y + 2, size - 4, size - 4)
            if self.room.collides(box, probe) or self.room.has_pit(x + size / 2, y + size / 2):
                continue
            if self.room.floor_at(x + size / 2, y + size / 2) in HAZARD or self.room.floor_at(x + size / 2, y + size / 2) == "~":
                continue
            if avoid is not None and dist((x + size / 2, y + size / 2), avoid) < min_dist:
                continue
            return (x, y)
        return None

    # ------------------------------------------------------------------ rooms
    def set_room(self, room, px, py, facing=None):
        self.room = room
        p = self.player
        p.x, p.y = float(px), float(py)
        p.safe = (p.x, p.y)
        if facing:
            p.facing = facing
        self.entities = []
        self.flags.add("visited:" + room.key)
        self.spawn_room()

    def spawn_room(self):
        r = self.room
        px, py = self.player.center()
        for spec in r.spawns:
            e = build_enemy(spec)
            if r.kind == "ow" and dist(e.center(), (px, py)) < 40:
                continue
            self.entities.append(e)
        r.had_enemies = bool(r.spawns)
        r.cleared = not r.had_enemies
        r.shut = r.shutter and r.had_enemies
        for dr in r.drops:
            if dr["when"] == "always" or (dr["when"] == "clear" and r.cleared):
                self.drop_room_item(dr)
        boss = any(e.boss for e in self.entities if isinstance(e, Enemy))
        self.music = {"ow": "overworld", "dg": "boss" if boss else "dungeon", "in": "cave"}[r.kind]

    def drop_room_item(self, dr):
        self.entities.append(Pickup(PLAY_W / 2 - 8, PLAY_H / 2 - 8, dr["item"], dr["id"]))
        self.sfx("secret")

    def begin_scroll(self, d):
        r, dx, dy = self.room, *DIRS[d]
        sx, sy = r.map_pos
        if r.kind == "ow":
            new = self.world.overworld_room(sx + dx, sy + dy, self.flags)
        else:
            new = self.world.dungeon_room(self.dungeon, sx + dx, sy + dy, self.flags)
        p = self.player
        nx = {"right": 0, "left": PLAY_W - 16}.get(d, p.x)
        ny = {"down": 0, "up": PLAY_H - 16}.get(d, p.y)
        self.trans = dict(dir=d, t=0, old=r, old_ents=list(self.entities), new=new, src=(p.x, p.y), dst=(nx, ny))
        self.mode = "scroll"

    def update_scroll(self):
        t = self.trans
        t["t"] += 1
        k = t["t"] / SCROLL_FRAMES
        dx, dy = DIRS[t["dir"]]
        sx, sy = t["src"]
        tx, ty = t["dst"]
        self.player.x = sx + (tx + dx * PLAY_W - sx) * k if dx else sx + (tx - sx) * k
        self.player.y = sy + (ty + dy * PLAY_H - sy) * k if dy else sy + (ty - sy) * k
        if t["t"] >= SCROLL_FRAMES:
            self.player.x, self.player.y = float(tx), float(ty)
            self.trans = None
            self.set_room(t["new"], tx, ty)
            self.mode = "play"

    def start_fade(self, callback, then=None, dur=36):
        self.fade = dict(t=0, dur=dur, cb=callback, then=then, switched=False)
        self.mode = "fade"

    def update_fade(self):
        f = self.fade
        f["t"] += 1
        if f["t"] >= f["dur"] // 2 and not f["switched"]:
            f["switched"] = True
            f["cb"]()
        if f["t"] >= f["dur"]:
            self.fade = None
            self.mode = "play"
            if f["then"]:
                f["then"]()

    def enter_interior(self, tx, ty, iid):
        spec = INTERIORS[iid]
        ret = (*self.room.map_pos, tx, ty)

        def go():
            self.ret = ret
            self.set_room(self.world.interior_room(iid), 120, 144, "up")
            self.entities.append(Npc(120, 40, spec["npc"]))
            locked = self.inv.max_hp < spec.get("need_hearts", 0) * 2
            if not locked:
                for it in spec["items"]:
                    if it.get("id") and "taken:" + it["id"] in self.flags:
                        continue
                    self.entities.append(Pickup(it["x"] * TILE - 8, 96, it["item"], it.get("id"),
                                                it.get("price", 0), it.get("amount", 0)))
            self._cave_text = spec["text"] if not locked else "YOU NEED %d HEARTS FIRST." % spec["need_hearts"]

        self.sfx("stairs")
        self.start_fade(go, then=lambda: self.say(self._cave_text))

    def return_point(self):
        sx, sy, tx, ty = self.world.start
        return self.ret or (sx, sy, tx, ty - 1)

    def leave_interior(self):
        sx, sy, tx, ty = self.return_point()

        def go():
            self.set_room(self.world.overworld_room(sx, sy, self.flags), tx * TILE, (ty + 1) * TILE, "down")

        self.start_fade(go)

    def enter_dungeon(self, n):
        self.ret = (*self.room.map_pos, self.room.gate[0], self.room.gate[1])
        d = self.world.dungeons[n]

        def go():
            self.dungeon = n
            self.set_room(self.world.dungeon_room(n, *d["start"], self.flags), 120, 144, "up")

        self.sfx("stairs")
        self.start_fade(go)

    def leave_dungeon(self, then=None):
        sx, sy, tx, ty = self.return_point()

        def go():
            self.dungeon = 0
            self.set_room(self.world.overworld_room(sx, sy, self.flags), tx * TILE, (ty + 1) * TILE, "down")

        self.start_fade(go, then=then)

    # ------------------------------------------------------------------ dialog / menu
    def say(self, text, then=None):
        self.dialog = dict(text="\n".join(wrap_text(text, 24)), n=0, then=then)
        self.mode = "dialog"

    def update_dialog(self, c):
        d = self.dialog
        total = len(d["text"])
        if d["n"] < total:
            d["n"] += 1
            if d["n"] % 3 == 0 and d["text"][d["n"] - 1] != " ":
                self.sfx("text")
        if c.a_press or c.b_press or c.start_press:
            if d["n"] < total:
                d["n"] = total
            else:
                self.dialog = None
                self.mode = "play"
                if d["then"]:
                    d["then"]()

    def open_menu(self):
        self.menu = {"cursor": 0}
        self.mode = "menu"
        self.sfx("select")

    def menu_entries(self):
        return self.inv.equippable() + ["SAVE", "RESUME", "QUIT"]

    def update_menu(self, c):
        entries = self.menu_entries()
        m = self.menu
        m["cursor"] = clamp(m["cursor"], 0, len(entries) - 1)
        if c.up_press or c.left_press:
            m["cursor"] = (m["cursor"] - 1) % len(entries)
            self.sfx("select")
        if c.down_press or c.right_press:
            m["cursor"] = (m["cursor"] + 1) % len(entries)
            self.sfx("select")
        if c.start_press or c.back_press:
            self.mode = "play"
        elif c.a_press or c.b_press:
            choice = entries[m["cursor"]]
            if choice == "RESUME":
                self.mode = "play"
            elif choice == "SAVE":
                if self.saver:
                    self.saver(self.to_save())
                self.say_banner("GAME SAVED.")
                self.sfx("secret")
                self.mode = "play"
            elif choice == "QUIT":
                self.mode = "title"
                self.music = "title"
                self.refresh_title()
            else:
                self.inv.equipped = choice
                self.sfx("select")

    # ------------------------------------------------------------------ title
    def refresh_title(self):
        self.save_exists = bool(self.loader and self.loader())

    def update_title(self, c):
        options = ["NEW GAME", "CONTINUE", "QUIT"]
        if c.up_press:
            self.title_cursor = (self.title_cursor - 1) % 3
            self.sfx("select")
        if c.down_press:
            self.title_cursor = (self.title_cursor + 1) % 3
            self.sfx("select")
        if c.a_press or c.start_press:
            choice = options[self.title_cursor]
            if choice == "NEW GAME":
                self.new_game()
            elif choice == "CONTINUE" and self.loader:
                data = self.loader()
                if data and self.load_save(data):
                    self.sfx("secret")
                else:
                    self.sfx("error")
            elif choice == "QUIT":
                self.want_quit = True

    # ------------------------------------------------------------------ main update
    def update(self, c):
        self.frame += 1
        if self.banner[1] > 0:
            self.banner[1] -= 1
        m = self.mode
        if m == "title":
            self.update_title(c)
        elif m == "play":
            self.update_play(c)
        elif m == "scroll":
            self.update_scroll()
        elif m == "fade":
            self.update_fade()
        elif m == "dialog":
            self.update_dialog(c)
        elif m == "menu":
            self.update_menu(c)
        elif m == "hold":
            self.update_hold()
        elif m == "dying":
            self.update_dying()
        elif m == "gameover":
            self.update_gameover(c)
        elif m == "victory":
            if c.a_press or c.start_press:
                self.mode, self.music = "title", "title"
                self.refresh_title()

    def update_play(self, c):
        if c.start_press or c.back_press:
            self.open_menu()
            return
        self.play_frames += 1
        self.player.update(self, c)
        for e in list(self.entities):
            e.update(self)
        self.resolve()
        self.entities = [e for e in self.entities if not e.dead]
        if self.mode != "play":
            return
        self.check_clear()
        self.check_hazards()
        self.check_doors()
        self.check_triggers()
        self.boss_support()
        if self.victory_t:
            self.victory_t -= 1
            if not self.victory_t:
                self.mode, self.music = "victory", "victory"
        if self.mode == "play":
            self.check_edges()

    # ------------------------------------------------------------------ combat and interaction
    def resolve(self):
        p, inv = self.player, self.inv
        enemies = [e for e in self.entities if isinstance(e, Enemy) and not e.dead and not e.hidden]
        sb = p.sword_box()
        if sb:
            dx, dy = DIRS[p.facing]
            for e in enemies:
                if e.swing_seen != p.swing and overlap(sb, e.box()):
                    e.swing_seen = p.swing
                    e.hurt(self, SWORD_DAMAGE[inv.sword], dx, dy, "sword")
            self.cut_bushes(sb)
        for pr in [e for e in self.entities if isinstance(e, Projectile) and not e.dead]:
            if pr.friendly:
                for e in enemies:
                    if e.dead or not overlap(pr.box(), e.box()):
                        continue
                    if pr.stun and not e.boss:
                        e.stun = pr.stun
                    if isinstance(pr, Boomerang):
                        pr.out = False
                    if pr.damage:
                        e.hurt(self, pr.damage, pr.vx, pr.vy, pr.sprite)
                    if not pr.pierce:
                        pr.dead = True
                        self.effect(pr.x - 4, pr.y - 4, "spark", 8)
                        break
            elif overlap(pr.box(), p.box()) and p.state != "dead":
                if pr.blockable and p.state != "attack" and p.facing == OPPOSITE[pr.facing]:
                    pr.dead = True
                    self.sfx("clink")
                elif p.hurt(self, pr.damage, pr.x + 4, pr.y + 4):
                    pr.dead = True
        for e in enemies:
            if e.touch and overlap(e.box(), p.box()) and p.state != "dead":
                p.hurt(self, e.damage, *e.center())
        for pk in [e for e in self.entities if isinstance(e, Pickup) and not e.dead]:
            for b in self.find(Boomerang):
                if overlap(pk.box(), b.box()) and pk.carrier is None and not pk.price:
                    pk.carrier = b
            if overlap(pk.box(), p.box()) and p.state != "dead":
                self.collect(pk)

    def cut_bushes(self, box):
        x, y, w, h = box
        for ty in range(int(y // TILE), int((y + h) // TILE) + 1):
            for tx in range(int(x // TILE), int((x + w) // TILE) + 1):
                if self.room.tile(tx, ty) in CUTTABLE:
                    self.remove_tile(tx, ty)
                    self.sfx("cut")
                    self.effect(tx * TILE, ty * TILE, "leaf", 14)
                    if self.rng.random() < 0.12:
                        self.entities.append(Pickup(tx * TILE, ty * TILE, self.rng.choice(("gem1", "heart", "gem1")), timed=True))

    def remove_tile(self, tx, ty):
        """Take an obstacle off the map for good (bush, cracked rock, boulder); secrets open a cave."""
        r = self.room
        was = r.tile(tx, ty)
        if (tx, ty) in r.secrets:
            r.set_tile(tx, ty, "C")
            r.caves[(tx, ty)] = r.secrets[(tx, ty)]
            self.flags.add("gone:%s:%d,%d" % (r.key, tx, ty))
            self.sfx("secret")
        else:
            r.set_tile(tx, ty, ":" if was == "X" else ".")
            if was in "XH":
                self.flags.add("gone:%s:%d,%d" % (r.key, tx, ty))

    def push_tile(self, tx, ty, dx, dy):
        r = self.room
        ch = r.tile(tx, ty)
        if ch == "H" and "glove" in self.inv.tools:
            self.remove_tile(tx, ty)
            self.effect(tx * TILE, ty * TILE, "puff", 14)
            self.sfx("rumble")
        elif ch == "B":
            nx, ny = tx + dx, ty + dy
            if 0 < nx < ROOM_W - 1 and 0 < ny < ROOM_H - 1 and r.tile(nx, ny) in "._":
                r.set_tile(tx, ty, ".")
                r.set_tile(nx, ny, "B")
                self.sfx("rumble")
                if r.push_opens:
                    r.push_opens = False
                    for dr in r.drops:
                        if dr["when"] == "push":
                            self.drop_room_item(dr)

    def explode(self, cx, cy):
        r = self.room
        self.effect(cx - 8, cy - 8, "boom", 20)
        self.sfx("explosion")
        for e in self.entities:
            if isinstance(e, Enemy) and not e.dead and dist(e.center(), (cx, cy)) < 28:
                ex, ey = e.center()
                e.hurt(self, 4, ex - cx, ey - cy, "bomb")
        if dist(self.player.center(), (cx, cy)) < 20:
            self.player.hurt(self, 2, cx, cy)
        for ty in range(ROOM_H):
            for tx in range(ROOM_W):
                if r.tile(tx, ty) == "X" and dist((tx * TILE + 8, ty * TILE + 8), (cx, cy)) < 30:
                    self.remove_tile(tx, ty)
        for side, state in list(r.doors.items()):
            if state == "bomb" and any(dist((a * TILE + 8, b * TILE + 8), (cx, cy)) < 34 for a, b in DOOR_CELLS[side]):
                self.open_door(side)

    def open_door(self, side):
        self.room.doors[side] = "open"
        self.flags.add("door:%d:%s" % (self.dungeon, self.room.door_edges[side]))
        self.room.exits[SIDE_DIR[side]] = True
        self.sfx("door")

    def collect(self, pk):
        inv = self.inv
        if pk.price:
            if inv.gems < pk.price:
                if self.frame % 60 == 0:
                    self.say_banner("NOT ENOUGH GEMS.", 90)
                    self.sfx("error")
                return
            inv.gems -= pk.price
        apply_item(inv, pk.item, self.dungeon, pk.amount)
        if pk.ident:
            self.flags.add("taken:" + pk.ident)
        pk.dead = True
        if pk.item in MAJOR:
            self.player.holding = pk.item
            self.player.state = "walk"
            self.hold_t = 70
            self.mode = "hold"
            self.music_before_hold = self.music
            self.sfx("item")
        else:
            self.sfx({"heart": "heart", "key": "key", "small_key": "key", "potion": "pickup"}.get(pk.item, "pickup"))

    def update_hold(self):
        self.hold_t -= 1
        if self.hold_t <= 0:
            item = self.player.holding
            self.player.holding = None
            self.mode = "play"
            then = None
            if item == "shard":
                then = lambda: self.leave_dungeon()
            self.say(MAJOR[item], then=then)

    def on_enemy_death(self, e):
        cx, cy = e.center()
        self.effect(cx - 8, cy - 8, "puff", 14)
        self.sfx("kill")
        if e.boss:
            self.on_boss_death(e)
            return
        roll = self.rng.random()
        for limit, item in ((0.30, "gem1"), (0.42, "heart"), (0.47, "gem5"), (0.52, "bomb")):
            if roll < limit:
                if item != "bomb" or "bombs" in self.inv.tools:
                    self.entities.append(Pickup(cx - 8, cy - 8, item, timed=True))
                break

    def on_boss_death(self, e):
        n = self.dungeon
        self.flags.add("boss:%d" % n)
        self.sfx("boss_die")
        cx, cy = e.center()
        for i in range(6):
            self.effect(cx - 8 + self.rng.randint(-14, 14), cy - 8 + self.rng.randint(-14, 14), "boom", 20)
        if n == 5:
            self.victory_t = 160
            return
        self.entities.append(Pickup(cx - 28, cy - 8, "heart_container", "heart_d%d" % n))
        self.entities.append(Pickup(cx + 12, cy - 8, "shard", "shard_%d" % n))
        self.music = "dungeon"

    def on_player_death(self):
        self.mode = "dying"
        self.music = None
        self.sfx("die")

    def update_dying(self):
        self.player.dead_t += 1
        if self.player.dead_t > 80:
            self.mode = "gameover"
            self.gameover_cursor = 0

    def update_gameover(self, c):
        if c.up_press or c.down_press:
            self.gameover_cursor ^= 1
            self.sfx("select")
        if c.a_press or c.start_press:
            if self.gameover_cursor == 0:
                self.respawn()
            else:
                self.mode, self.music = "title", "title"
                self.refresh_title()

    def respawn(self):
        self.inv.hp = min(self.inv.max_hp, 6)
        p = self.player
        p.state, p.invuln, p.dead_t, p.knock_t = "walk", 90, 0, 0

        def go():
            if self.dungeon:
                d = self.world.dungeons[self.dungeon]
                self.set_room(self.world.dungeon_room(self.dungeon, *d["start"], self.flags), 120, 144, "up")
            else:
                sx, sy, tx, ty = self.world.start
                self.set_room(self.world.overworld_room(sx, sy, self.flags), tx * TILE, ty * TILE, "up")

        self.start_fade(go)

    # ------------------------------------------------------------------ per-frame room checks
    def check_clear(self):
        r = self.room
        if r.cleared or not r.had_enemies:
            return
        if any(isinstance(e, Enemy) and not e.dead for e in self.entities):
            return
        r.cleared, was_shut, r.shut = True, r.shut, False
        if r.kind == "dg":
            self.flags.add("cleared:" + r.key)
            for dr in r.drops:
                if dr["when"] == "clear":
                    self.drop_room_item(dr)
        if was_shut:
            self.sfx("door")

    def check_hazards(self):
        p, r = self.player, self.room
        if p.state == "dead":
            return
        cx, cy = p.center()
        ch = r.floor_at(cx, cy)
        if ch in PITS and p.knock_t == 0:
            self.sfx("fall")
            p.hurt(self, 1, cx, cy)
            p.x, p.y = p.safe
            p.knock_t = 0
        elif ch in HAZARD:
            p.hurt(self, HAZARD[ch], cx, cy + 4)

    def check_doors(self):
        p, r = self.player, self.room
        if r.kind != "dg":
            return
        dx, dy = DIRS[p.facing]
        probe = (p.box()[0] + dx * 3, p.box()[1] + dy * 3, p.box()[2], p.box()[3])
        for side, state in list(r.doors.items()):
            if state not in ("locked", "boss"):
                continue
            if any(overlap(probe, (a * TILE, b * TILE, TILE, TILE)) for a, b in DOOR_CELLS[side]):
                if state == "locked" and self.inv.keys.get(self.dungeon, 0) > 0:
                    self.inv.keys[self.dungeon] -= 1
                    self.open_door(side)
                elif state == "boss" and self.dungeon in self.inv.boss_keys:
                    self.open_door(side)
                elif self.frame % 90 == 0:
                    self.say_banner("THE DOOR IS LOCKED." if state == "locked" else "A BOSS KEY IS NEEDED.", 80)
                    self.sfx("error")

    def check_triggers(self):
        p, r = self.player, self.room
        if r.kind != "ow":
            return
        cx, cy = p.center()
        tx, ty = int(cx // TILE), int(cy // TILE)
        ch = r.tile(tx, ty)
        if ch == "C" and (tx, ty) in r.caves and p.facing == "up":
            self.enter_interior(tx, ty, r.caves[(tx, ty)])
        elif ch == "D" and r.gate:
            n = r.gate[2]
            if n == 5 and len(self.inv.shards) < 4:
                p.y += 12
                self.say("THE GATE IS SEALED. FOUR SHARDS ARE NEEDED.")
            else:
                self.enter_dungeon(n)

    def check_edges(self):
        cx, cy = self.player.center()
        d = "left" if cx < 0 else "right" if cx >= PLAY_W else "up" if cy < 0 else "down" if cy >= PLAY_H else None
        if d is None:
            return
        r = self.room
        if r.kind == "in":
            self.leave_interior()
        elif r.kind == "dg" and r.doors.get(SIDE[d]) == "exit":
            self.leave_dungeon()
        else:
            self.begin_scroll(d)

    def boss_support(self):
        """The bomb boss is only hurt by bombs, so keep the player stocked while it lives."""
        from .enemies import Magmamaw
        if self.frame % 420 or not self.find(Magmamaw) or self.inv.bombs >= 2:
            return
        if not any(isinstance(e, Pickup) and e.item == "bomb" for e in self.entities):
            spot = self.random_floor(avoid=self.player.center(), min_dist=40)
            if spot:
                self.entities.append(Pickup(spot[0], spot[1], "bomb", timed=True))
