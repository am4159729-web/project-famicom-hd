import math

from .constants import DIRS, TILE
from .entities import Entity, Projectile
from .util import sign


def face(dx, dy):
    return ("right" if dx > 0 else "left") if abs(dx) >= abs(dy) else ("down" if dy > 0 else "up")


class Enemy(Entity):
    hp = 1
    damage = 1
    speed = 0.5
    touch = True
    boss = False

    def __init__(self, x, y):
        super().__init__(x, y)
        self.hp = type(self).hp
        self.hidden = False
        self.stun = self.hurt_t = self.knock_t = 0
        self.kx = self.ky = 0.0
        self.timer = self.turn = self.pause = 0
        self.cool = 60
        self.dirv = (0, 0)
        self.phase = ""
        self.swing_seen = -1

    def update(self, g):
        self.t += 1
        self.hurt_t = max(0, self.hurt_t - 1)
        if self.knock_t:
            self.knock_t -= 1
            self.move(g.room, self.kx, self.ky)
        elif self.stun:
            self.stun -= 1
        else:
            self.ai(g)

    def ai(self, g):
        pass

    def guarded(self, dx, dy, source):
        return False

    def hurt(self, g, dmg, dx, dy, source="sword"):
        if self.hidden or dmg <= 0 or self.hurt_t > 8:
            return False
        if self.guarded(dx, dy, source):
            g.sfx("clink")
            return False
        self.hp -= dmg
        self.hurt_t = 14
        if not self.boss:
            d = max(1.0, math.hypot(dx, dy))
            self.kx, self.ky, self.knock_t = dx / d * 3.0, dy / d * 3.0, 6
        g.sfx("boss_hit" if self.boss else "hit")
        if self.hp <= 0:
            self.dead = True
            g.on_enemy_death(self)
        return True

    # helpers -----------------------------------------------------------
    def to_player(self, g):
        px, py = g.player.center()
        cx, cy = self.center()
        return px - cx, py - cy

    def wander(self, g, speed, lo=30, hi=90):
        self.timer -= 1
        if self.timer <= 0 or self.dirv == (0, 0):
            self.facing = g.rng.choice(list(DIRS))
            self.dirv = DIRS[self.facing]
            self.timer = g.rng.randint(lo, hi)
        hx, hy = self.move(g.room, self.dirv[0] * speed, self.dirv[1] * speed)
        if hx or hy:
            self.timer = 0

    def chase(self, g, speed, retarget=30):
        self.turn -= 1
        if self.turn <= 0:
            dx, dy = self.to_player(g)
            horizontal = abs(dx) > abs(dy)
            if g.rng.random() < 0.25:
                horizontal = not horizontal
            self.facing = ("right" if dx > 0 else "left") if horizontal else ("down" if dy > 0 else "up")
            self.dirv = DIRS[self.facing]
            self.turn = retarget
        hx, hy = self.move(g.room, self.dirv[0] * speed, self.dirv[1] * speed)
        if hx or hy:
            self.turn = 0

    def aligned(self, g, rng=100, tol=8):
        dx, dy = self.to_player(g)
        if abs(dy) < tol and abs(dx) < rng:
            return "right" if dx > 0 else "left"
        if abs(dx) < tol and abs(dy) < rng:
            return "down" if dy > 0 else "up"
        return None

    def shoot(self, g, kind, vx, vy, blockable=True, damage=None):
        cx, cy = self.center()
        g.add(Projectile(cx - 4, cy - 4, vx, vy, kind, damage or self.damage, blockable=blockable))


class Rocktopus(Enemy):
    sprite, speed = "rocktopus", 0.55

    def ai(self, g):
        if self.pause:
            self.pause -= 1
            if self.pause == 10:
                dx, dy = DIRS[self.facing]
                self.shoot(g, "rock", dx * 1.8, dy * 1.8)
            return
        self.cool -= 1
        if self.cool <= 0:
            self.cool = g.rng.randint(80, 200)
            if g.rng.random() < 0.6:
                self.pause = 28
                return
        self.wander(g, self.speed)


class Thrower(Enemy):
    ammo, ammo_speed, hunts = "spear", 2.2, False

    def ai(self, g):
        if self.pause:
            self.pause -= 1
            if self.pause == 12:
                dx, dy = DIRS[self.facing]
                self.shoot(g, self.ammo, dx * self.ammo_speed, dy * self.ammo_speed)
            return
        self.cool -= 1
        d = self.aligned(g)
        if d and self.cool <= 0:
            self.facing, self.pause, self.cool = d, 24, 110
            return
        if self.hunts:
            self.chase(g, self.speed)
        else:
            self.wander(g, self.speed)


class Boarman(Thrower):
    sprite, hp, speed = "boarman", 2, 0.6


class Goblin(Thrower):
    sprite, hp, speed, ammo, hunts = "goblin", 3, 0.65, "axe", True


class Centaur(Thrower):
    sprite, hp, damage, speed, ammo, ammo_speed, hunts = "centaur", 6, 2, 0.85, "energy", 2.6, True


class Hopper(Enemy):
    sprite, hp, speed = "hopper", 2, 1.2

    def ai(self, g):
        if self.timer > 0:
            self.timer -= 1
            hx, hy = self.move(g.room, self.dirv[0] * self.speed, self.dirv[1] * self.speed)
            if hx or hy:
                self.dirv = (-self.dirv[0], -self.dirv[1])
            self.z = math.sin(math.pi * (28 - self.timer) / 28) * 10
            if self.timer == 0:
                self.z, self.pause = 0, g.rng.randint(25, 70)
        elif self.pause > 0:
            self.pause -= 1
        else:
            if g.rng.random() < 0.4:
                dx, dy = self.to_player(g)
                a = math.atan2(dy, dx)
            else:
                a = g.rng.uniform(0, math.tau)
            self.dirv = (math.cos(a), math.sin(a))
            self.timer = 28


class Slime(Enemy):
    sprite, hp, speed = "slime", 1, 1.0

    def ai(self, g):
        if self.timer > 0:
            self.timer -= 1
            hx, hy = self.move(g.room, self.dirv[0] * self.speed, self.dirv[1] * self.speed)
            self.z = math.sin(math.pi * (16 - self.timer) / 16) * 4
            if hx or hy:
                self.timer = 0
            if self.timer == 0:
                self.z = 0
        elif self.pause > 0:
            self.pause -= 1
        else:
            self.dirv = DIRS[g.rng.choice(list(DIRS))]
            self.timer, self.pause = 16, g.rng.randint(40, 90)


class Burrower(Enemy):
    sprite, hp, speed = "burrower", 2, 0.8

    def __init__(self, x, y):
        super().__init__(x, y)
        self.hidden = True
        self.cool = 60

    def ai(self, g):
        self.cool -= 1
        if self.hidden:
            if self.cool <= 0:
                spot = g.random_floor(near=g.player.center(), max_dist=64, min_dist=24)
                if spot is None:
                    self.cool = 30
                    return
                self.x, self.y = spot
                self.hidden, self.cool = False, 170
                g.effect(self.x, self.y, "puff", 10)
            return
        self.chase(g, self.speed)
        if self.cool <= 0:
            self.hidden, self.cool = True, g.rng.randint(90, 160)
            g.effect(self.x, self.y, "puff", 10)


class Lurker(Enemy):
    sprite, hp = "lurker", 2
    can_swim = True

    def __init__(self, x, y):
        super().__init__(x, y)
        self.hidden = True
        self.cool = 90

    def ai(self, g):
        self.cool -= 1
        if self.hidden:
            if self.cool <= 0:
                self.hidden, self.cool = False, 120
                g.effect(self.x, self.y, "splash", 12)
            return
        if self.cool == 70:
            dx, dy = self.to_player(g)
            self.facing = face(dx, dy)
            vx, vy = DIRS[self.facing]
            self.shoot(g, "rock", vx * 1.7, vy * 1.7)
        if self.cool <= 0:
            self.hidden, self.cool = True, g.rng.randint(80, 170)
            g.effect(self.x, self.y, "splash", 12)


class Bat(Enemy):
    sprite, speed, flying = "bat", 1.25, True

    def ai(self, g):
        self.timer -= 1
        if self.timer <= 0:
            a = g.rng.uniform(0, math.tau)
            self.dirv = (math.cos(a), math.sin(a))
            self.timer = g.rng.randint(25, 60)
        hx, hy = self.move(g.room, self.dirv[0] * self.speed, self.dirv[1] * self.speed)
        if hx:
            self.dirv = (-self.dirv[0], self.dirv[1])
        if hy:
            self.dirv = (self.dirv[0], -self.dirv[1])


class Skeleton(Enemy):
    sprite, hp, speed = "skeleton", 3, 0.55

    def ai(self, g):
        self.chase(g, self.speed, 36)


class Snake(Enemy):
    sprite, speed = "snake", 0.4

    def ai(self, g):
        if self.phase == "charge":
            hx, hy = self.move(g.room, self.dirv[0] * 2.2, self.dirv[1] * 2.2)
            if hx or hy:
                self.phase, self.pause = "", 30
            return
        if self.pause:
            self.pause -= 1
            return
        d = self.aligned(g, rng=110, tol=6)
        if d:
            self.facing, self.dirv, self.phase = d, DIRS[d], "charge"
            return
        self.wander(g, self.speed)


class Mage(Enemy):
    sprite, hp = "mage", 3

    def ai(self, g):
        if self.pause:
            self.pause -= 1
            if not self.pause:
                self.hidden, self.cool = False, 120
            return
        self.cool -= 1
        if self.cool == 60:
            dx, dy = self.to_player(g)
            a = math.atan2(dy, dx)
            self.facing = face(dx, dy)
            self.shoot(g, "magic", math.cos(a) * 1.7, math.sin(a) * 1.7, blockable=False)
        if self.cool <= 0:
            spot = g.random_floor(avoid=g.player.center(), min_dist=48)
            if spot:
                self.hidden, self.pause = True, 24
                self.x, self.y = spot


class Knight(Enemy):
    sprite, hp, damage, speed = "knight", 4, 2, 0.45

    def guarded(self, dx, dy, source):
        if source == "bomb":
            return False
        fx, fy = DIRS[self.facing]
        return dx * fx + dy * fy < 0

    def ai(self, g):
        self.chase(g, self.speed, 40)


class BladeTrap(Enemy):
    sprite, hp = "bladetrap", 999

    def __init__(self, x, y):
        super().__init__(x, y)
        self.home = (x, y)

    def hurt(self, g, dmg, dx, dy, source="sword"):
        g.sfx("clink")
        return False

    def ai(self, g):
        if self.phase == "dash":
            hx, hy = self.move(g.room, self.dirv[0] * 3.0, self.dirv[1] * 3.0)
            if hx or hy:
                self.phase = "back"
        elif self.phase == "back":
            dx, dy = self.home[0] - self.x, self.home[1] - self.y
            if abs(dx) < 1 and abs(dy) < 1:
                self.x, self.y = self.home
                self.phase = ""
            else:
                self.x += sign(dx) * min(1.0, abs(dx))
                self.y += sign(dy) * min(1.0, abs(dy))
        else:
            d = self.aligned(g, rng=300, tol=10)
            if d and g.line_clear(self.center(), g.player.center()):
                self.dirv, self.phase = DIRS[d], "dash"


class Boss(Enemy):
    boss = True
    hb = (2, 2, 28, 28)
    damage = 2


class Thornwyrm(Boss):
    sprite, hp, speed, fan, shot_speed = "thornwyrm", 12, 0.45, 3, 1.9

    def ai(self, g):
        if self.dirv == (0, 0):
            self.dirv = (-1, 0)
        hx, _ = self.move(g.room, self.dirv[0] * self.speed, 0)
        if hx:
            self.dirv = (-self.dirv[0], 0)
        self.cool -= 1
        if self.cool <= 0:
            self.cool = 110
            dx, dy = self.to_player(g)
            base = math.atan2(dy, dx)
            for i in range(self.fan):
                a = base + (i - (self.fan - 1) / 2) * 0.32
                self.shoot(g, "fire", math.cos(a) * self.shot_speed, math.sin(a) * self.shot_speed, blockable=False)


class Frostwyrm(Thornwyrm):
    sprite, hp, speed, fan, shot_speed = "frostwyrm", 20, 0.7, 5, 2.1


class Tidecrab(Boss):
    sprite, hp = "tidecrab_open", 14

    def __init__(self, x, y):
        super().__init__(x, y)
        self.open, self.cool = True, 150

    def hurt(self, g, dmg, dx, dy, source="sword"):
        if not self.open:
            g.sfx("clink")
            return False
        return super().hurt(g, dmg, dx, dy, source)

    def ai(self, g):
        self.cool -= 1
        if self.open:
            self.chase(g, 0.35, 50)
            if self.cool == 120:
                for vx, vy in ((1, 1), (-1, 1), (1, -1), (-1, -1)):
                    self.shoot(g, "bubble", vx * 1.2, vy * 1.2)
            if self.cool <= 0:
                self.open, self.cool, self.sprite = False, 100, "tidecrab_shut"
        else:
            dx, _ = self.to_player(g)
            self.move(g.room, sign(dx) * 1.6, 0)
            if self.cool <= 0:
                self.open, self.cool, self.sprite = True, 150, "tidecrab_open"


class Magmamaw(Boss):
    sprite, hp, speed = "magmamaw", 12, 0.5

    def hurt(self, g, dmg, dx, dy, source="sword"):
        if source != "bomb":
            g.sfx("clink")
            return False
        return super().hurt(g, dmg, dx, dy, source)

    def ai(self, g):
        self.chase(g, self.speed, 45)
        self.cool -= 1
        if self.cool <= 0:
            self.cool = 140
            dx, dy = self.to_player(g)
            a = math.atan2(dy, dx)
            self.shoot(g, "fire", math.cos(a) * 1.8, math.sin(a) * 1.8, blockable=False)


class Warlock(Boss):
    sprite, hp = "warlock", 30

    def __init__(self, x, y):
        super().__init__(x, y)
        self.cool = 90

    def ai(self, g):
        if self.pause:
            self.pause -= 1
            if not self.pause:
                self.hidden = False
            return
        rage = self.hp <= 10
        self.cool -= 1
        if self.cool == 40:
            dx, dy = self.to_player(g)
            base = math.atan2(dy, dx)
            for i in (-1, 0, 1):
                self.shoot(g, "magic", math.cos(base + i * 0.3) * 1.8, math.sin(base + i * 0.3) * 1.8, blockable=False)
            if rage:
                for i in range(8):
                    a = i * math.tau / 8
                    self.shoot(g, "magic", math.cos(a) * 1.3, math.sin(a) * 1.3, blockable=False)
        if self.cool <= 0:
            self.cool = 70 if rage else 100
            spot = g.random_floor(avoid=g.player.center(), min_dist=56, size=32)
            if spot:
                self.hidden, self.pause = True, 18
                self.x, self.y = spot


ENEMIES = {c.sprite: c for c in (Rocktopus, Boarman, Goblin, Centaur, Hopper, Slime, Burrower, Lurker, Bat,
                                 Skeleton, Snake, Mage, Knight, BladeTrap)}
BOSSES = {"thornwyrm": Thornwyrm, "frostwyrm": Frostwyrm, "tidecrab": Tidecrab, "magmamaw": Magmamaw,
          "warlock": Warlock}


def build_enemy(spec):
    """spec is [kind, tx, ty] or ["boss", kind, tx, ty]."""
    if spec[0] == "boss":
        return BOSSES[spec[1]](spec[2] * TILE, spec[3] * TILE)
    return ENEMIES[spec[0]](spec[1] * TILE, spec[2] * TILE)
