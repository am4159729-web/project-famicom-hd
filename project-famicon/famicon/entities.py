import math

from .constants import DIRS, PLAY_H, PLAY_W, TILE
from .inventory import SWORD_DAMAGE
from .tiles import PUSHABLE, WATER
from .util import clamp, dist


class Entity:
    sprite = "none"
    hb = (2, 2, 12, 12)
    flying = False
    is_player = False
    can_swim = False

    def __init__(self, x, y):
        self.x, self.y = float(x), float(y)
        self.dead = False
        self.t = 0
        self.z = 0
        self.facing = "down"

    def box(self):
        return (self.x + self.hb[0], self.y + self.hb[1], self.hb[2], self.hb[3])

    def box_at(self, x, y):
        return (x + self.hb[0], y + self.hb[1], self.hb[2], self.hb[3])

    def center(self):
        b = self.box()
        return (b[0] + b[2] / 2, b[1] + b[3] / 2)

    def move(self, room, dx, dy):
        hit = [False, False]
        for axis, amount in ((0, dx), (1, dy)):
            while abs(amount) > 1e-6:
                step = max(-1.0, min(1.0, amount))
                amount -= step
                if axis == 0:
                    self.x += step
                else:
                    self.y += step
                if room.collides(self.box(), self):
                    if axis == 0:
                        self.x -= step
                    else:
                        self.y -= step
                    hit[axis] = True
                    break
        return hit

    def update(self, g):
        self.t += 1


class Effect(Entity):
    """Short-lived visual: puff, boom, spark, splash."""

    def __init__(self, x, y, kind, life=16):
        super().__init__(x, y)
        self.sprite, self.life = kind, life

    def update(self, g):
        self.t += 1
        self.dead = self.t >= self.life


class Pickup(Entity):
    def __init__(self, x, y, item, ident=None, price=0, amount=0, timed=False):
        super().__init__(x, y)
        self.item, self.ident, self.price, self.amount, self.timed = item, ident, price, amount, timed
        self.sprite = "item_" + item
        self.carrier = None

    def update(self, g):
        self.t += 1
        if self.carrier is not None:
            if self.carrier.dead:
                self.carrier = None
            else:
                self.x, self.y = self.carrier.x - 4, self.carrier.y - 4
        if self.timed and self.t > 600:
            self.dead = True


class Projectile(Entity):
    hb = (0, 0, 8, 8)
    flying = True

    def __init__(self, x, y, vx, vy, kind, damage=1, friendly=False, blockable=True, pierce=False, life=300):
        super().__init__(x, y)
        self.vx, self.vy, self.sprite = vx, vy, kind
        self.damage, self.friendly, self.blockable, self.pierce, self.life = damage, friendly, blockable, pierce, life
        self.stun = 0
        self.facing = ("right" if vx > 0 else "left") if abs(vx) >= abs(vy) else ("down" if vy > 0 else "up")

    def update(self, g):
        self.t += 1
        self.x += self.vx
        self.y += self.vy
        cx, cy = self.center()
        tx, ty = int(cx // TILE), int(cy // TILE)
        if self.t > self.life or g.room.blocked(tx, ty, self):
            self.dead = True
            if self.friendly or self.sprite in ("rock", "fire"):
                g.effect(cx - 8, cy - 8, "spark", 8)


class Boomerang(Projectile):
    def __init__(self, owner):
        dx, dy = DIRS[owner.facing]
        cx, cy = owner.center()
        super().__init__(cx - 4, cy - 4, dx * 3.0, dy * 3.0, "boomerang", damage=0, friendly=True, pierce=True)
        self.owner, self.out, self.stun = owner, True, 150

    def update(self, g):
        self.t += 1
        ox, oy = self.owner.center()
        if self.out:
            self.x += self.vx
            self.y += self.vy
            cx, cy = self.center()
            if dist((cx, cy), (ox, oy)) > 72 or g.room.blocked(int(cx // TILE), int(cy // TILE), self):
                self.out = False
        else:
            cx, cy = self.center()
            d = max(1.0, dist((cx, cy), (ox, oy)))
            self.x += (ox - cx) / d * 3.5
            self.y += (oy - cy) / d * 3.5
            if d < 7:
                self.dead = True
        if self.t > 400:
            self.dead = True


class Bomb(Entity):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.sprite, self.fuse = "bomb", 90

    def update(self, g):
        self.t += 1
        self.fuse -= 1
        if self.fuse <= 0:
            self.dead = True
            cx, cy = self.center()
            g.explode(cx, cy)


class Player(Entity):
    sprite = "player"
    hb = (3, 7, 10, 8)
    is_player = True
    speed = 1.35

    def __init__(self, x, y):
        super().__init__(x, y)
        self.state = "walk"
        self.attack_t = 0
        self.swing = 0
        self.invuln = 0
        self.knock_t = 0
        self.kx = self.ky = 0.0
        self.moving = False
        self.push_t = 0
        self.dead_t = 0
        self.holding = None
        self.safe = (x, y)
        self.can_swim = False

    def sword_box(self):
        if self.state != "attack" or not 3 <= self.attack_t <= 10:
            return None
        x, y = self.x, self.y
        return {"up": (x + 5, y - 8, 6, 12), "down": (x + 5, y + 12, 6, 12),
                "left": (x - 8, y + 6, 12, 6), "right": (x + 12, y + 6, 12, 6)}[self.facing]

    def in_water(self, g):
        cx, cy = self.center()
        return g.room.floor_at(cx, cy + 3) in WATER

    def update(self, g, c=None):
        self.t += 1
        self.invuln = max(0, self.invuln - 1)
        self.can_swim = "fins" in g.inv.tools
        if self.state == "dead":
            self.dead_t += 1
            return
        if self.knock_t > 0:
            self.knock_t -= 1
            self.move(g.room, self.kx, self.ky)
            return
        if self.state == "attack":
            self.attack_t += 1
            if self.attack_t == 3 and g.inv.hp == g.inv.max_hp and g.inv.sword:
                dx, dy = DIRS[self.facing]
                cx, cy = self.center()
                g.add(Projectile(cx - 4 + dx * 10, cy - 4 + dy * 10, dx * 3.2, dy * 3.2, "beam",
                                 damage=SWORD_DAMAGE[g.inv.sword], friendly=True, blockable=False, life=90))
                g.sfx("beam")
            if self.attack_t >= 14:
                self.state = "walk"
            return
        if c is None:
            return
        if c.a_press and g.inv.sword and not self.in_water(g):
            self.state, self.attack_t = "attack", 0
            self.swing += 1
            g.sfx("sword")
            return
        if c.b_press and not self.in_water(g):
            self.use_item(g)
        self.walk(g, c)
        cx, cy = self.center()
        if g.room.floor_at(cx, cy) not in "v~" and not g.room.collides(self.box(), self):
            self.safe = (self.x, self.y)

    def walk(self, g, c):
        held = [d for d in DIRS if getattr(c, d)]
        self.moving = bool(held)
        if not held:
            self.push_t = 0
            return
        d = self.facing if self.facing in held else held[0]
        for k in held:
            if getattr(c, k + "_press"):
                d = k
        self.facing = d
        dx, dy = DIRS[d]
        speed = self.speed * (0.6 if self.in_water(g) else 1.0)
        # glide toward the 8px grid on the other axis, like the originals
        if dx:
            off = round(self.y / 8) * 8 - self.y
            if 0 < abs(off) <= 3:
                self.move(g.room, 0, clamp(off, -1, 1))
        else:
            off = round(self.x / 8) * 8 - self.x
            if 0 < abs(off) <= 3:
                self.move(g.room, clamp(off, -1, 1), 0)
        hx, hy = self.move(g.room, dx * speed, dy * speed)
        if hx or hy:
            self.assist(g.room, dx, dy)
            self.try_push(g, dx, dy)
        else:
            self.push_t = 0

    def assist(self, room, dx, dy):
        """Slide around tile corners instead of sticking to them."""
        for n in range(1, 7):
            for off in (-n, n):
                ox, oy = (0, off) if dx else (off, 0)
                probe = self.box_at(self.x + ox + dx * 2, self.y + oy + dy * 2)
                if not room.collides(probe, self):
                    step = 1 if off > 0 else -1
                    self.move(room, 0 if dx else step, step if dx else 0)
                    return

    def try_push(self, g, dx, dy):
        cx, cy = self.center()
        tx, ty = int((cx + dx * 9) // TILE), int((cy + dy * 9) // TILE)
        if g.room.tile(tx, ty) in PUSHABLE:
            self.push_t += 1
            if self.push_t >= 22:
                self.push_t = 0
                g.push_tile(tx, ty, dx, dy)
        else:
            self.push_t = 0

    def use_item(self, g):
        inv = g.inv
        cx, cy = self.center()
        dx, dy = DIRS[self.facing]
        item = inv.equipped
        if item == "boomerang" and "boomerang" in inv.tools and not g.find(Boomerang):
            g.add(Boomerang(self))
            g.sfx("boomerang")
        elif item == "bombs" and inv.bombs > 0 and len(g.find(Bomb)) < 2:
            inv.bombs -= 1
            bx = clamp(cx + dx * 14, 10, PLAY_W - 10)
            by = clamp(cy + dy * 14, 10, PLAY_H - 10)
            g.add(Bomb(bx - 8, by - 8))
            g.sfx("bomb_set")
        elif item == "bow" and "bow" in inv.tools and inv.gems > 0 and not g.find_arrow():
            inv.gems -= 1
            g.add(Projectile(cx - 4 + dx * 8, cy - 4 + dy * 8, dx * 4.0, dy * 4.0, "arrow", damage=2,
                             friendly=True, life=120))
            g.sfx("arrow")
        elif item == "potion" and inv.potions > 0 and inv.hp < inv.max_hp:
            inv.potions -= 1
            inv.hp = inv.max_hp
            g.sfx("heal")

    def hurt(self, g, dmg, sx, sy):
        if self.invuln or self.state == "dead" or g.mode != "play":
            return False
        g.inv.hp -= dmg
        self.invuln = 60
        cx, cy = self.center()
        d = max(1.0, math.hypot(cx - sx, cy - sy))
        self.kx, self.ky, self.knock_t = (cx - sx) / d * 2.4, (cy - sy) / d * 2.4, 8
        self.state = "walk"
        g.sfx("hurt")
        if g.inv.hp <= 0:
            g.inv.hp = 0
            self.state, self.dead_t = "dead", 0
            g.on_player_death()
        return True
