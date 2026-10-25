import math

import pygame

from .constants import DIRS, HUD_H, MAX_HEARTS, OW_COLS, OW_ROWS, PLAY_H, PLAY_W, ROOM_H, ROOM_W, SCREEN_H, SCREEN_W, TILE
from .enemies import Enemy
from .entities import Boomerang, Effect, Pickup, Projectile
from .inventory import SWORD_NAMES
from .game import SCROLL_FRAMES, Npc

D = pygame.draw
WHITE, GOLD, GREY, RED = (252, 252, 252), (252, 216, 80), (140, 140, 156), (230, 70, 60)
SWORD_COLORS = ((0, 0, 0), (200, 140, 80), (210, 225, 245), (252, 220, 100))
ICON = {"bombs": "item_bomb", "potion": "item_potion", "boomerang": "item_boomerang", "bow": "item_bow"}


class Renderer:
    def __init__(self, assets):
        self.a = assets

    # ------------------------------------------------------------------ helpers
    def txt(self, s, msg, x, y, color=WHITE, scale=1, center=False):
        img = self.a.text(msg, color, scale)
        if center:
            x -= img.get_width() // 2
        s.blit(img, (x, y))

    def room_key(self, room):
        return "dg:" + room.theme if room.kind == "dg" else "dg:cave" if room.kind == "in" else room.theme

    # ------------------------------------------------------------------ top level
    def draw(self, g, s):
        s.fill((0, 0, 0))
        m = g.mode
        if m == "title":
            self.draw_title(g, s)
            return
        if m == "scroll":
            self.draw_scroll(g, s)
        else:
            self.draw_world(g, s)
        self.draw_hud(g, s)
        if g.banner[1] > 0:
            w = len(g.banner[0]) * 4 + 6
            s.fill((0, 0, 0), (PLAY_W // 2 - w // 2, HUD_H + 3, w, 11))
            self.txt(s, g.banner[0], PLAY_W // 2, HUD_H + 6, WHITE, 1, True)
        if m == "dialog":
            self.draw_dialog(g, s)
        elif m == "menu":
            self.draw_menu(g, s)
        elif m == "gameover":
            self.draw_gameover(g, s)
        elif m == "victory":
            self.draw_victory(g, s)
        elif m == "fade":
            f = g.fade
            a = int(255 * (1 - abs(2 * f["t"] / f["dur"] - 1)))
            veil = pygame.Surface((SCREEN_W, SCREEN_H - HUD_H), pygame.SRCALPHA)
            veil.fill((0, 0, 0, max(0, min(255, a))))
            s.blit(veil, (0, HUD_H))

    # ------------------------------------------------------------------ world
    def draw_world(self, g, s):
        self.draw_room(g.room, s, 0, 0, g.frame)
        self.draw_entities(g, s, g.entities, 0, 0)
        self.draw_player(g, s, 0, 0)
        if g.room.dark and g.mode != "scroll":
            self.draw_dark(g, s)

    def draw_scroll(self, g, s):
        t = g.trans
        k = t["t"] / SCROLL_FRAMES
        dx, dy = DIRS[t["dir"]]
        ox, oy = int(-dx * PLAY_W * k), int(-dy * PLAY_H * k)
        self.draw_room(t["old"], s, ox, oy, g.frame)
        self.draw_entities(g, s, t["old_ents"], ox, oy)
        self.draw_room(t["new"], s, ox + dx * PLAY_W, oy + dy * PLAY_H, g.frame)
        self.draw_player(g, s, 0, 0)

    def draw_room(self, room, s, ox, oy, frame):
        key = self.room_key(room)
        for ty in range(ROOM_H):
            for tx in range(ROOM_W):
                px, py = tx * TILE + ox, ty * TILE + oy
                if px <= -TILE or px >= PLAY_W or py <= -TILE or py >= PLAY_H:
                    continue
                ch = room.tiles[ty][tx]
                anim = (frame // 24) % 2 if ch in "~l" else (frame // 8) % 2 if ch == "O" else 0
                s.blit(self.a.tile(ch, key, anim), (px, py + HUD_H))
        if room.kind == "dg":
            self.draw_doors(room, s, ox, oy)

    def draw_doors(self, room, s, ox, oy):
        rects = {"N": (7 * TILE, 0, 32, 16), "S": (7 * TILE, 10 * TILE, 32, 16),
                 "W": (0, 4 * TILE, 16, 32), "E": (15 * TILE, 4 * TILE, 16, 32)}
        for side, (x, y, w, h) in rects.items():
            st = room.door_state(side)
            if st in ("wall", "bomb"):
                continue
            r = (int(x + ox), int(y + oy + HUD_H), w, h)
            if st in ("open", "exit"):
                D.rect(s, (6, 4, 10), r)
            elif st == "locked":
                D.rect(s, (130, 84, 40), r)
                D.rect(s, (70, 40, 20), r, 1)
                s.fill((252, 220, 90), (r[0] + w // 2 - 1, r[1] + h // 2 - 2, 3, 4))
            elif st == "boss":
                D.rect(s, (120, 20, 40), r)
                D.rect(s, (252, 80, 80), r, 1)
                s.fill((252, 220, 120), (r[0] + w // 2 - 2, r[1] + h // 2 - 2, 5, 5))
            else:
                D.rect(s, (70, 70, 86), r)
                for i in range(0, max(w, h), 4):
                    if w > h:
                        D.line(s, (150, 150, 170), (r[0] + i, r[1]), (r[0] + i, r[1] + h - 1))
                    else:
                        D.line(s, (150, 150, 170), (r[0], r[1] + i), (r[0] + w - 1, r[1] + i))

    def draw_entities(self, g, s, ents, ox, oy):
        for e in sorted(ents, key=lambda e: e.y):
            if getattr(e, "hidden", False):
                continue
            if isinstance(e, Enemy) and e.hurt_t and e.t % 4 < 2:
                continue
            if isinstance(e, Pickup) and e.timed and e.t > 480 and e.t % 8 < 4:
                continue
            x, y = int(e.x + ox), int(e.y - e.z + oy + HUD_H)
            if isinstance(e, Effect):
                self.draw_effect(s, e, x, y)
                continue
            if isinstance(e, Boomerang):
                img = self.a.sprite("boomerang", frame=e.t // 3)
            elif isinstance(e, Projectile):
                img = self.a.sprite(e.sprite, e.facing, e.t // 6)
            elif isinstance(e, Npc) or isinstance(e, Pickup):
                img = self.a.sprite(e.sprite)
            else:
                img = self.a.sprite(e.sprite, e.facing, e.t // 8)
            if isinstance(e, Enemy) and e.z:
                D.ellipse(s, (0, 0, 0), (x + 3, int(e.y + oy + HUD_H) + 12, 10, 3))
            s.blit(img, (x, y))
            if isinstance(e, Pickup) and e.price:
                self.txt(s, str(e.price), x + 8, y + 18, WHITE, 1, True)

    def draw_effect(self, s, e, x, y):
        k = e.t / e.life
        cx, cy = x + 8, y + 8
        if e.sprite == "boom":
            D.circle(s, (252, 140, 40), (cx, cy), int(4 + 20 * k))
            D.circle(s, (252, 230, 120), (cx, cy), max(1, int(14 * (1 - k))))
        elif e.sprite == "puff":
            D.circle(s, (240, 240, 250), (cx, cy), int(3 + 6 * k), 1)
            D.circle(s, (200, 200, 220), (cx, cy), int(1 + 4 * k))
        elif e.sprite == "spark":
            for dx, dy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                s.fill((252, 240, 140), (cx + dx * int(2 + 4 * k), cy + dy * int(2 + 4 * k), 2, 2))
        elif e.sprite == "splash":
            D.ellipse(s, (190, 230, 252), (cx - int(3 + 7 * k), cy - int(1 + 3 * k), int(6 + 14 * k), int(2 + 6 * k)), 1)
        elif e.sprite == "leaf":
            for i in range(4):
                a = i * math.pi / 2 + k * 2
                s.fill((60, 170, 70), (cx + int(math.cos(a) * (2 + 8 * k)), cy + int(math.sin(a) * (2 + 8 * k)), 2, 2))

    def draw_player(self, g, s, ox, oy):
        p = g.player
        if p.state == "dead" and p.dead_t > 60:
            return
        if p.invuln and p.t % 4 < 2 and p.state != "dead":
            return
        x, y = int(p.x + ox), int(p.y + oy + HUD_H)
        face = p.facing
        if p.state == "dead":
            face = ("down", "left", "up", "right")[(p.dead_t // 5) % 4]
        if p.holding:
            img = self.a.sprite("player_down", "down", 0)
            s.blit(img, (x, y))
            s.blit(self.a.sprite("item_" + p.holding), (x, y - 14))
            return
        frame = (p.t // 7) % 2 if p.moving else 0
        if g.room and p.in_water(g):
            D.ellipse(s, (40, 90, 220), (x + 1, y + 10, 14, 6))
        s.blit(self.a.sprite("player_" + face, face, frame), (x, y))
        if p.state == "attack" and 1 <= p.attack_t <= 12:
            self.draw_sword(g, s, x, y, face, p.attack_t)
        elif p.state != "dead":
            self.draw_shield(s, x, y, face)

    def draw_sword(self, g, s, x, y, face, t):
        col = SWORD_COLORS[g.inv.sword]
        reach = 4 if t < 3 else 12
        hilt = (150, 100, 40)
        if face == "up":
            s.fill(col, (x + 7, y - reach + 2, 2, reach))
            s.fill(hilt, (x + 5, y + 2, 6, 2))
        elif face == "down":
            s.fill(col, (x + 7, y + 13, 2, reach))
            s.fill(hilt, (x + 5, y + 12, 6, 2))
        elif face == "left":
            s.fill(col, (x - reach + 2, y + 9, reach, 2))
            s.fill(hilt, (x + 2, y + 7, 2, 6))
        else:
            s.fill(col, (x + 14, y + 9, reach, 2))
            s.fill(hilt, (x + 12, y + 7, 2, 6))

    def draw_shield(self, s, x, y, face):
        blue, rim = (60, 100, 220), (230, 230, 240)
        spots = {"down": (x + 1, y + 9), "up": (x + 10, y + 9), "left": (x - 1, y + 8), "right": (x + 12, y + 8)}
        sx, sy = spots[face]
        s.fill(rim, (sx, sy, 5, 6))
        s.fill(blue, (sx + 1, sy + 1, 3, 4))

    def draw_dark(self, g, s):
        veil = pygame.Surface((PLAY_W, PLAY_H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 238))
        radius = 58 if "lantern" in g.inv.tools else 30
        spots = [(*g.player.center(), radius)]
        for ty in range(ROOM_H):
            for tx in range(ROOM_W):
                if g.room.tiles[ty][tx] == "O":
                    spots.append((tx * TILE + 8, ty * TILE + 8, 24))
        for cx, cy, r in spots:
            D.circle(veil, (0, 0, 0, 120), (int(cx), int(cy)), r + 10)
        for cx, cy, r in spots:
            D.circle(veil, (0, 0, 0, 0), (int(cx), int(cy)), r)
        s.blit(veil, (0, HUD_H))

    # ------------------------------------------------------------------ HUD
    def draw_hud(self, g, s):
        s.fill((0, 0, 0), (0, 0, SCREEN_W, HUD_H))
        inv = g.inv
        self.draw_minimap(g, s)
        for x, label in ((88, "B"), (112, "A")):
            self.txt(s, label, x + 6, 4, WHITE)
            D.rect(s, (90, 90, 120), (x, 12, 18, 20), 1)
        if inv.equipped and inv.equipped in ICON and (inv.equipped != "potion" or inv.potions):
            s.blit(self.a.sprite(ICON[inv.equipped]), (89, 14))
        if inv.sword:
            s.blit(self.a.sprite("item_sword_" + ("wood", "steel", "magic")[inv.sword - 1]), (113, 14))
        rows = [("item_gem1", "%d" % inv.gems), ("item_small_key", "%d" % inv.keys.get(g.dungeon, 0) if g.dungeon else "-"),
                ("item_bomb", "%d" % inv.bombs if "bombs" in inv.tools else "-")]
        for i, (icon, val) in enumerate(rows):
            s.blit(self.a.sprite(icon), (132, 2 + i * 15 - 1))
            self.txt(s, "x" + val, 150, 6 + i * 15, WHITE)
        self.txt(s, "-LIFE-", 224, 4, RED, 1, True)
        hearts = inv.max_hp // 2
        for i in range(min(hearts, MAX_HEARTS)):
            hx, hy = 196 + (i % 7) * 8, 12 + (i // 7) * 9
            left = inv.hp - i * 2
            kind = "heart_full" if left >= 2 else "heart_half" if left == 1 else "heart_empty"
            s.blit(self.a.sprite(kind), (hx, hy))

    def draw_minimap(self, g, s):
        r = g.room
        if r is None:
            return
        if r.kind == "ow" or (r.kind == "in"):
            for y in range(OW_ROWS):
                for x in range(OW_COLS):
                    seen = ("visited:ow:%d,%d" % (x, y)) in g.flags
                    s.fill((70, 150, 70) if seen else (40, 40, 52), (6 + x * 4, 8 + y * 4, 3, 3))
            if r.kind == "ow":
                px, py = r.map_pos
            else:
                px, py = g.return_point()[:2]
            if g.frame // 12 % 2:
                s.fill(WHITE, (6 + px * 4, 8 + py * 4, 3, 3))
        else:
            d = g.world.dungeons[g.dungeon]
            gw, gh = d["size"]
            for (x, y) in d["rooms"]:
                seen = ("visited:dg:%d:%d,%d" % (g.dungeon, x, y)) in g.flags
                if g.dungeon not in g.inv.maps and not seen:
                    continue
                col = (110, 110, 170) if seen else (60, 60, 90)
                if g.dungeon in g.inv.compasses and [x, y] == list(d["boss"]):
                    col = RED
                s.fill(col, (6 + x * 9, 8 + y * 6, 8, 5))
            px, py = r.map_pos
            if g.frame // 12 % 2:
                s.fill(WHITE, (8 + px * 9, 9 + py * 6, 3, 3))

    # ------------------------------------------------------------------ overlays
    def draw_dialog(self, g, s):
        d = g.dialog
        D.rect(s, (0, 0, 0), (16, SCREEN_H - 72, 224, 60))
        D.rect(s, WHITE, (16, SCREEN_H - 72, 224, 60), 1)
        for i, line in enumerate(d["text"][:d["n"]].split("\n")):
            self.txt(s, line, 24, SCREEN_H - 66 + i * 12, WHITE, 2)
        if d["n"] >= len(d["text"]) and g.frame // 20 % 2:
            self.txt(s, "<", 228, SCREEN_H - 22, GOLD, 1)

    def draw_menu(self, g, s):
        veil = pygame.Surface((PLAY_W, PLAY_H), pygame.SRCALPHA)
        veil.fill((8, 8, 24, 235))
        s.blit(veil, (0, HUD_H))
        self.txt(s, "PAUSED", SCREEN_W // 2, HUD_H + 8, GOLD, 2, True)
        entries = g.menu_entries()
        for i, name in enumerate(entries):
            y = HUD_H + 34 + i * 14
            sel = i == g.menu["cursor"]
            if name in ICON:
                s.blit(self.a.sprite(ICON[name]), (28, y - 5))
                label = {"bombs": "BOMBS", "potion": "POTION X%d" % g.inv.potions}.get(name, name.upper())
                tag = "  <B>" if g.inv.equipped == name else ""
                self.txt(s, label + tag, 48, y, GOLD if sel else WHITE)
            else:
                self.txt(s, name, 48, y, GOLD if sel else WHITE)
            if sel:
                self.txt(s, ">", 18, y, GOLD)
        x0 = 150
        self.txt(s, "SWORD: " + SWORD_NAMES[g.inv.sword], x0, HUD_H + 34, WHITE)
        self.txt(s, "HEARTS: %d/%d" % ((g.inv.hp + 1) // 2, g.inv.max_hp // 2), x0, HUD_H + 46, WHITE)
        self.txt(s, "SHARDS:", x0, HUD_H + 62, WHITE)
        for i in range(1, 5):
            if i in g.inv.shards:
                s.blit(self.a.sprite("item_shard"), (x0 + 30 + (i - 1) * 17, HUD_H + 56))
            else:
                D.rect(s, (60, 60, 80), (x0 + 34 + (i - 1) * 17, HUD_H + 62, 8, 8), 1)
        for i, (name, label) in enumerate((("glove", "GLOVE"), ("fins", "FINS"), ("lantern", "LANTERN"))):
            if name in g.inv.tools:
                self.txt(s, label, x0, HUD_H + 80 + i * 10, GREY)

    def draw_gameover(self, g, s):
        veil = pygame.Surface((PLAY_W, PLAY_H), pygame.SRCALPHA)
        veil.fill((0, 0, 0, 215))
        s.blit(veil, (0, HUD_H))
        self.txt(s, "GAME OVER", SCREEN_W // 2, HUD_H + 40, RED, 3, True)
        for i, name in enumerate(("CONTINUE", "TITLE")):
            self.txt(s, ("> " if i == g.gameover_cursor else "  ") + name, SCREEN_W // 2 - 32, HUD_H + 90 + i * 16,
                     GOLD if i == g.gameover_cursor else WHITE, 2)

    def draw_victory(self, g, s):
        s.fill((8, 6, 30), (0, HUD_H, PLAY_W, PLAY_H))
        for i in range(30):
            x, y = (i * 53 + g.frame // 3) % PLAY_W, HUD_H + (i * 31) % PLAY_H
            s.fill((252, 240, 160) if i % 3 else WHITE, (x, y, 1, 1))
        s.blit(pygame.transform.scale(self.a.sprite("item_shard"), (48, 48)), (SCREEN_W // 2 - 24, HUD_H + 18))
        self.txt(s, "THE CROWN IS WHOLE", SCREEN_W // 2, HUD_H + 80, GOLD, 2, True)
        self.txt(s, "THANKS FOR PLAYING", SCREEN_W // 2, HUD_H + 106, WHITE, 1, True)
        t = g.play_frames // 3600
        self.txt(s, "TIME %d MIN   HEARTS %d" % (t, g.inv.max_hp // 2), SCREEN_W // 2, HUD_H + 122, GREY, 1, True)
        self.txt(s, "PRESS ENTER", SCREEN_W // 2, HUD_H + 150, WHITE if g.frame // 30 % 2 else GREY, 1, True)

    def draw_title(self, g, s):
        for i in range(0, SCREEN_H, 4):
            k = i / SCREEN_H
            s.fill((int(10 + 30 * k), int(8 + 14 * k), int(40 + 50 * k)), (0, i, SCREEN_W, 4))
        for i in range(40):
            x, y = (i * 67 + g.frame // 4) % SCREEN_W, (i * 29) % 120
            s.fill(WHITE if (g.frame // 10 + i) % 5 else (120, 120, 160), (x, y, 1, 1))
        D.polygon(s, (60, 50, 90), [(0, 150), (60, 100), (110, 140), (170, 90), (230, 135), (256, 120), (256, 224), (0, 224)])
        self.txt(s, "PROJECT FAMICON", SCREEN_W // 2, 34, GOLD, 3, True)
        self.txt(s, "THE CROWN SHARDS", SCREEN_W // 2, 62, WHITE, 2, True)
        s.blit(self.a.sprite("item_shard"), (SCREEN_W // 2 - 8, 84 + int(math.sin(g.frame / 15) * 3)))
        options = ["NEW GAME", "CONTINUE", "QUIT"]
        for i, name in enumerate(options):
            dim = name == "CONTINUE" and not g.save_exists
            col = (90, 90, 110) if dim else GOLD if i == g.title_cursor else WHITE
            self.txt(s, ("> " if i == g.title_cursor else "  ") + name, SCREEN_W // 2 - 36, 128 + i * 16, col, 2)
        self.txt(s, "ARROWS MOVE  Z SWORD  X ITEM  ENTER PAUSE", SCREEN_W // 2, 200, GREY, 1, True)
