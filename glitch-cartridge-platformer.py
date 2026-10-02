import pygame
import math
import random
import sys
from array import array

pygame.init()

WIDTH, HEIGHT = 960, 540
FPS = 60
TILE_SIZE = 32

BG_COLOR = (10, 8, 18)
GRID_COLOR = (22, 18, 36)
WHITE = (245, 245, 250)
CYAN = (0, 240, 220)
YELLOW = (255, 225, 50)
PINK = (255, 50, 130)
PURPLE = (170, 70, 240)
ORANGE = (255, 130, 40)
RED = (255, 60, 70)
GREEN = (80, 240, 120)
DARK_BLUE = (15, 20, 35)

LEVEL_1_DATA = [
    "11111111111111111111111111111111111111111111111111",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10001111000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000011111000000000000000111110000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000011110000000000000000000000001",
    "11100000000000000000000000000000000000000011111111",
    "10000001110000000000000000001110000000000000000001",
    "10000000000000011100000000000000000000000000000001",
    "10000000000000000000000000000000001110000000000001",
    "10000000000000000000000000000000000000000000000001",
    "11111111111111333311111111111333331111111111111111"
]

LEVEL_2_DATA = [
    "11111111111111111111111111111111111111111111111111",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10001111000000000000000000000000000000000111100001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000011100000000000001110000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "11100000000000000011111100000000000000111000000111",
    "10000000000000000000000000000000000000000000000001",
    "10000001111000000000000000000001111000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000111100000000111100000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "11111111111333311111111133331111111133331111111111"
]

LEVEL_3_DATA = [
    "11111111111111111111111111111111111111111111111111",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "11111000000000000000000000000000000000000000111111",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000001111111110000000000000001111111110000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "10000000000000000000000000000000000000000000000001",
    "11111111111111111111111111111111111111111111111111"
]

def clamp(v, l, h):
    return max(l, min(h, v))

def lerp(a, b, t):
    return a + (b - a) * t

def draw_text(surface, font, text, x, y, color=WHITE, center=False):
    img = font.render(text, True, color)
    rect = img.get_rect()
    if center:
        rect.center = (int(x), int(y))
    else:
        rect.topleft = (int(x), int(y))
    surface.blit(img, rect)

def make_glow(radius, color, alpha=100, layers=4):
    size = radius * 2 + layers * 12
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    for i in range(layers, 0, -1):
        r = radius + i * 6
        a = max(2, int(alpha / (i + 1)))
        pygame.draw.circle(surf, (*color, a), (cx, cy), r)
    pygame.draw.circle(surf, (*color, min(255, alpha + 40)), (cx, cy), radius)
    return surf

class AudioEngine:
    def __init__(self):
        self.enabled = False
        self.sounds = {}
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=256)
            self.enabled = True
            self.sounds["jump"] = self._tone(0.08, 180, 520, 0.18, "square")
            self.sounds["dash"] = self._tone(0.12, 600, 150, 0.22, "noise")
            self.sounds["shoot"] = self._tone(0.06, 850, 300, 0.15, "square")
            self.sounds["hit"] = self._tone(0.09, 220, 80, 0.25, "noise")
            self.sounds["coin"] = self._chime([750, 1050], [0.05, 0.08], 0.18)
            self.sounds["boss_hit"] = self._tone(0.15, 140, 50, 0.35, "noise")
            self.sounds["victory"] = self._fanfare()
        except pygame.error:
            self.enabled = False

    def _tone(self, duration, start_hz, end_hz, volume, wave="square"):
        rate = 44100
        count = max(1, int(duration * rate))
        data = array("h")
        for i in range(count):
            t = i / max(1, count - 1)
            freq = lerp(start_hz, end_hz, t)
            phase = 2.0 * math.pi * freq * (i / rate)
            if wave == "noise":
                sample = random.uniform(-1.0, 1.0)
            else:
                sample = 1.0 if math.sin(phase) >= 0 else -1.0
            envelope = (1.0 - t) ** 1.8
            data.append(int(32767 * volume * sample * envelope))
        return pygame.mixer.Sound(buffer=data.tobytes())

    def _chime(self, freqs, durations, volume):
        rate = 44100
        data = array("h")
        for freq, duration in zip(freqs, durations):
            count = max(1, int(duration * rate))
            for i in range(count):
                t = i / max(1, count - 1)
                phase = 2.0 * math.pi * freq * (i / rate)
                sample = math.sin(phase) * (1.0 - t) ** 1.4
                data.append(int(32767 * volume * sample))
        return pygame.mixer.Sound(buffer=data.tobytes())

    def _fanfare(self):
        rate = 44100
        seq = [(523, 0.08), (659, 0.08), (784, 0.10), (1047, 0.20)]
        data = array("h")
        for freq, duration in seq:
            count = int(duration * rate)
            for i in range(count):
                t = i / max(1, count - 1)
                phase = 2.0 * math.pi * freq * (i / rate)
                sample = math.sin(phase) * (1.0 - t * 0.6) ** 1.3
                data.append(int(32767 * 0.22 * sample))
        return pygame.mixer.Sound(buffer=data.tobytes())

    def play(self, name):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

class ScreenShake:
    def __init__(self):
        self.time = 0.0
        self.magnitude = 0.0

    def add(self, magnitude, duration):
        self.magnitude = max(self.magnitude, magnitude)
        self.time = max(self.time, duration)

    def update(self, dt):
        self.time = max(0.0, self.time - dt)
        if self.time <= 0:
            self.magnitude = 0.0

    def offset(self):
        if self.time <= 0 or self.magnitude <= 0:
            return 0, 0
        s = self.magnitude * min(1.0, self.time / 0.10)
        return random.uniform(-s, s), random.uniform(-s, s)

class Particle:
    def __init__(self, x, y, vx, vy, color, size, life, gravity=0.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.life = life
        self.max_life = life
        self.gravity = gravity

    def update(self, dt):
        self.life -= dt
        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

    @property
    def alive(self):
        return self.life > 0

    def draw(self, surface, camera_x, camera_y):
        alpha = clamp(int(255 * (self.life / self.max_life)), 0, 255)
        if alpha <= 0:
            return
        r = max(1, int(self.size * (self.life / self.max_life)))
        px = int(self.x - camera_x)
        py = int(self.y - camera_y)
        pygame.draw.circle(surface, (*self.color, alpha), (px, py), r)

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def burst(self, x, y, color, count=12, speed=140, size=(2, 4), life=(0.15, 0.4), gravity=0):
        for _ in range(count):
            a = random.uniform(0, math.tau)
            s = random.uniform(speed * 0.3, speed)
            self.particles.append(
                Particle(
                    x, y,
                    math.cos(a) * s, math.sin(a) * s,
                    color,
                    random.uniform(*size),
                    random.uniform(*life),
                    gravity=gravity
                )
            )

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.alive]

    def draw(self, surface, camera_x, camera_y):
        for p in self.particles:
            p.draw(surface, camera_x, camera_y)

class TileMap:
    def __init__(self, data):
        self.tiles = []
        self.hazards = []
        self.width = len(data[0]) * TILE_SIZE
        self.height = len(data) * TILE_SIZE
        self.data = data

        for y, row in enumerate(data):
            for x, char in enumerate(row):
                r = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if char == '1':
                    self.tiles.append(r)
                elif char == '3':
                    self.hazards.append(r)

    def draw(self, surface, camera_x, camera_y):
        for rect in self.tiles:
            dr = rect.move(-camera_x, -camera_y)
            if dr.colliderect(-TILE_SIZE, -TILE_SIZE, WIDTH + TILE_SIZE * 2, HEIGHT + TILE_SIZE * 2):
                pygame.draw.rect(surface, (25, 30, 50), dr)
                pygame.draw.rect(surface, CYAN, dr, 1)
                pygame.draw.line(surface, WHITE, (dr.left + 2, dr.top + 2), (dr.right - 2, dr.top + 2), 1)

        for rect in self.hazards:
            dr = rect.move(-camera_x, -camera_y)
            if dr.colliderect(-TILE_SIZE, -TILE_SIZE, WIDTH + TILE_SIZE * 2, HEIGHT + TILE_SIZE * 2):
                pts = [(dr.left, dr.bottom), (dr.centerx, dr.top), (dr.right, dr.bottom)]
                pygame.draw.polygon(surface, RED, pts)
                pygame.draw.polygon(surface, WHITE, pts, 1)

class Coin:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 16, 16)
        self.alive = True
        self.wobble = random.uniform(0, math.tau)
        self.glow = make_glow(10, YELLOW, 80, layers=3)

    def update(self, dt):
        self.wobble += dt * 6.0

    def draw(self, surface, camera_x, camera_y):
        cx = int(self.rect.centerx - camera_x)
        cy = int(self.rect.centery - camera_y + math.sin(self.wobble) * 3)
        surface.blit(self.glow, self.glow.get_rect(center=(cx, cy)))
        pygame.draw.circle(surface, YELLOW, (cx, cy), 6)
        pygame.draw.circle(surface, WHITE, (cx, cy), 3)

class Bullet:
    def __init__(self, x, y, vx, vy, is_player=True):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.radius = 4 if is_player else 6
        self.is_player = is_player
        self.alive = True
        self.glow = make_glow(self.radius, YELLOW if is_player else RED, 100, layers=2)

    def update(self, dt, tilemap):
        self.x += self.vx * dt
        self.y += self.vy * dt
        r = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
        
        for t in tilemap.tiles:
            if r.colliderect(t):
                self.alive = False
                return

        if self.x < -50 or self.x > tilemap.width + 50 or self.y < -50 or self.y > tilemap.height + 50:
            self.alive = False

    def draw(self, surface, camera_x, camera_y):
        cx = int(self.x - camera_x)
        cy = int(self.y - camera_y)
        surface.blit(self.glow, self.glow.get_rect(center=(cx, cy)))
        color = YELLOW if self.is_player else RED
        pygame.draw.circle(surface, color, (cx, cy), self.radius)
        pygame.draw.circle(surface, WHITE, (cx, cy), max(1, self.radius - 2))

class Enemy:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 24, 24)
        self.vx = 80.0
        self.hp = 3
        self.alive = True
        self.flash = 0.0

    def update(self, dt, tilemap):
        self.flash = max(0.0, self.flash - dt)
        self.rect.x += int(self.vx * dt)
        
        for t in tilemap.tiles:
            if self.rect.colliderect(t):
                if self.vx > 0:
                    self.rect.right = t.left
                    self.vx = -self.vx
                elif self.vx < 0:
                    self.rect.left = t.right
                    self.vx = -self.vx

        ground_check = pygame.Rect(self.rect.left if self.vx < 0 else self.rect.right - 2, self.rect.bottom + 2, 2, 2)
        has_ground = any(ground_check.colliderect(t) for t in tilemap.tiles)
        if not has_ground:
            self.vx = -self.vx

    def take_hit(self, damage):
        self.hp -= damage
        self.flash = 0.1
        if self.hp <= 0:
            self.alive = False

    def draw(self, surface, camera_x, camera_y):
        dr = self.rect.move(-camera_x, -camera_y)
        color = WHITE if self.flash > 0 else PINK
        pygame.draw.rect(surface, color, dr)
        pygame.draw.rect(surface, BG_COLOR, dr.inflate(-8, -8))

class Boss:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 64, 64)
        self.max_hp = 40
        self.hp = self.max_hp
        self.alive = True
        self.flash = 0.0
        self.state_timer = 0.0
        self.phase = "hover"
        self.target_y = y
        self.shoot_timer = 0.0
        self.glow = make_glow(32, PURPLE, 110, layers=5)

    def update(self, dt, player, bullets):
        self.flash = max(0.0, self.flash - dt)
        self.state_timer += dt
        self.shoot_timer += dt

        if self.phase == "hover":
            self.rect.x += int(math.sin(self.state_timer * 2.5) * 120.0 * dt)
            self.rect.y = int(self.target_y + math.sin(self.state_timer * 4.0) * 20)
            if self.shoot_timer >= 0.85:
                self.shoot_timer = 0.0
                angle = math.atan2(player.rect.centery - self.rect.centery, player.rect.centerx - self.rect.centerx)
                bullets.append(Bullet(self.rect.centerx, self.rect.centery, math.cos(angle) * 320, math.sin(angle) * 320, False))

            if self.state_timer > 6.0:
                self.phase = "charge"
                self.state_timer = 0.0

        elif self.phase == "charge":
            dx = player.rect.centerx - self.rect.centerx
            self.rect.x += int(clamp(dx, -250, 250) * dt)
            if self.state_timer > 2.5:
                self.phase = "hover"
                self.state_timer = 0.0

    def take_hit(self, damage):
        self.hp -= damage
        self.flash = 0.10
        if self.hp <= 0:
            self.alive = False

    def draw(self, surface, camera_x, camera_y):
        dr = self.rect.move(-camera_x, -camera_y)
        surface.blit(self.glow, self.glow.get_rect(center=dr.center))
        color = WHITE if self.flash > 0 else PURPLE
        pygame.draw.rect(surface, color, dr, border_radius=8)
        pygame.draw.rect(surface, RED, dr.inflate(-12, -12), border_radius=6)
        
        eyex = dr.centerx + (4 if self.phase == "charge" else 0)
        pygame.draw.circle(surface, YELLOW, (eyex - 10, dr.centery - 6), 6)
        pygame.draw.circle(surface, YELLOW, (eyex + 10, dr.centery - 6), 6)

class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 20, 28)
        self.vx = 0.0
        self.vy = 0.0
        
        self.ACCEL = 1800.0
        self.FRICTION = 1100.0
        self.MAX_SPEED = 240.0
        self.GRAVITY = 1300.0
        self.JUMP_FORCE = -520.0
        
        self.on_ground = False
        self.coyote_timer = 0.0
        self.jump_buffer = 0.0
        
        self.max_hp = 5
        self.hp = self.max_hp
        self.invincible_timer = 0.0
        self.flash_timer = 0.0
        
        self.facing_right = True
        self.dash_cooldown = 0.0
        self.dash_timer = 0.0
        self.shoot_cooldown = 0.0

        self.glow = make_glow(14, CYAN, 90, layers=3)

    def handle_input(self, keys, dt, audio, particles, bullets):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vx -= self.ACCEL * dt
            self.facing_right = False
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vx += self.ACCEL * dt
            self.facing_right = True
        else:
            if self.vx > 0:
                self.vx = max(0.0, self.vx - self.FRICTION * dt)
            elif self.vx < 0:
                self.vx = min(0.0, self.vx + self.FRICTION * dt)

        self.vx = clamp(self.vx, -self.MAX_SPEED, self.MAX_SPEED)

        if keys[pygame.K_SPACE] or keys[pygame.K_w] or keys[pygame.K_UP]:
            self.jump_buffer = 0.12

        if (keys[pygame.K_LSHIFT] or keys[pygame.K_k]) and self.dash_cooldown <= 0:
            self.dash_timer = 0.15
            self.dash_cooldown = 0.70
            self.invincible_timer = 0.20
            self.vx = (380.0 if self.facing_right else -380.0)
            self.vy = 0.0
            audio.play("dash")
            particles.burst(self.rect.centerx, self.rect.centery, CYAN, count=10, speed=160)

        if (keys[pygame.K_j] or keys[pygame.K_x]) and self.shoot_cooldown <= 0:
            self.shoot_cooldown = 0.18
            bx = self.rect.right if self.facing_right else self.rect.left
            bvx = 550.0 if self.facing_right else -550.0
            bullets.append(Bullet(bx, self.rect.centery - 2, bvx, 0, True))
            audio.play("shoot")

    def update(self, dt, tilemap, audio, particles):
        self.invincible_timer = max(0.0, self.invincible_timer - dt)
        self.flash_timer = max(0.0, self.flash_timer - dt)
        self.dash_cooldown = max(0.0, self.dash_cooldown - dt)
        self.shoot_cooldown = max(0.0, self.shoot_cooldown - dt)
        self.jump_buffer = max(0.0, self.jump_buffer - dt)
        self.coyote_timer = max(0.0, self.coyote_timer - dt)

        if self.dash_timer > 0:
            self.dash_timer -= dt
            self.rect.x += int(self.vx * dt)
            self.resolve_collisions(tilemap, 'x')
            return

        if self.on_ground:
            self.coyote_timer = 0.10

        if self.jump_buffer > 0 and self.coyote_timer > 0:
            self.vy = self.JUMP_FORCE
            self.jump_buffer = 0.0
            self.coyote_timer = 0.0
            self.on_ground = False
            audio.play("jump")
            particles.burst(self.rect.centerx, self.rect.bottom, WHITE, count=8, speed=80)

        self.rect.x += int(self.vx * dt)
        self.resolve_collisions(tilemap, 'x')

        self.vy += self.GRAVITY * dt
        self.rect.y += int(self.vy * dt)
        self.on_ground = False
        self.resolve_collisions(tilemap, 'y')

    def resolve_collisions(self, tilemap, axis):
        for tile in tilemap.tiles:
            if self.rect.colliderect(tile):
                if axis == 'x':
                    if self.vx > 0:
                        self.rect.right = tile.left
                    elif self.vx < 0:
                        self.rect.left = tile.right
                    self.vx = 0
                elif axis == 'y':
                    if self.vy > 0:
                        self.rect.bottom = tile.top
                        self.on_ground = True
                    elif self.vy < 0:
                        self.rect.top = tile.bottom
                    self.vy = 0

    def take_damage(self, amount, audio, shake, particles):
        if self.invincible_timer > 0:
            return False
        self.hp -= amount
        self.invincible_timer = 0.80
        self.flash_timer = 0.15
        shake.add(10, 0.25)
        audio.play("hit")
        particles.burst(self.rect.centerx, self.rect.centery, RED, count=16, speed=180)
        return True

    def draw(self, surface, camera_x, camera_y):
        dr = self.rect.move(-camera_x, -camera_y)
        if self.invincible_timer > 0 and int(pygame.time.get_ticks() / 50) % 2 == 0:
            return

        surface.blit(self.glow, self.glow.get_rect(center=dr.center))
        color = WHITE if self.flash_timer > 0 else CYAN
        pygame.draw.rect(surface, color, dr, border_radius=3)
        pygame.draw.rect(surface, BG_COLOR, dr.inflate(-6, -6), border_radius=2)
        
        eyex = dr.right - 6 if self.facing_right else dr.left + 2
        pygame.draw.rect(surface, YELLOW, (eyex, dr.top + 6, 4, 6))

class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def update(self, target_x, target_y, map_w, map_h, dt):
        tx = target_x - WIDTH // 2
        ty = target_y - HEIGHT // 2
        self.x += (tx - self.x) * 6.0 * dt
        self.y += (ty - self.y) * 6.0 * dt
        self.x = clamp(self.x, 0, map_w - WIDTH)
        self.y = clamp(self.y, 0, map_h - HEIGHT)

class Game:
    START = "START"
    PLAYING = "PLAYING"
    GAME_OVER = "GAME_OVER"
    VICTORY = "VICTORY"

    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("GLITCH CARTRIDGE 2026")
        self.clock = pygame.time.Clock()

        self.font_s = pygame.font.SysFont("consolas", 16)
        self.font_m = pygame.font.SysFont("consolas", 24)
        self.font_l = pygame.font.SysFont("consolas", 48, bold=True)

        self.audio = AudioEngine()
        self.shake = ScreenShake()
        self.particles = ParticleSystem()
        self.camera = Camera()

        self.state = self.START
        self.current_level = 1
        self.coins_collected = 0
        self.score = 0
        
        self.load_level(1)

    def load_level(self, lvl):
        self.current_level = lvl
        if lvl == 1:
            data = LEVEL_1_DATA
        elif lvl == 2:
            data = LEVEL_2_DATA
        else:
            data = LEVEL_3_DATA

        self.tilemap = TileMap(data)
        self.player = Player(64, 100)
        self.bullets = []
        self.enemies = []
        self.coins = []
        self.boss = None

        if lvl == 3:
            self.boss = Boss(self.tilemap.width - 200, 150)

        for y, row in enumerate(data):
            for x, char in enumerate(row):
                px, py = x * TILE_SIZE, y * TILE_SIZE
                if char == '0' and random.random() < 0.08 and lvl != 3:
                    self.coins.append(Coin(px + 8, py + 8))
                elif char == '0' and random.random() < 0.04 and lvl != 3 and px > 200:
                    self.enemies.append(Enemy(px, py + 8))

        self.portal_rect = pygame.Rect(self.tilemap.width - 80, self.tilemap.height - 96, 32, 48)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if self.state == self.START and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self.state = self.PLAYING
                    self.load_level(1)
                elif self.state in (self.GAME_OVER, self.VICTORY) and event.key == pygame.K_r:
                    self.state = self.PLAYING
                    self.coins_collected = 0
                    self.score = 0
                    self.load_level(1)
        return True

    def update(self, dt):
        if self.state != self.PLAYING:
            return

        keys = pygame.key.get_pressed()
        self.player.handle_input(keys, dt, self.audio, self.particles, self.bullets)
        self.player.update(dt, self.tilemap, self.audio, self.particles)

        self.camera.update(self.player.rect.centerx, self.player.rect.centery, self.tilemap.width, self.tilemap.height, dt)

        for hz in self.tilemap.hazards:
            if self.player.rect.colliderect(hz):
                if self.player.take_damage(1, self.audio, self.shake, self.particles):
                    self.player.vy = -350.0

        if self.player.rect.top > self.tilemap.height:
            self.player.take_damage(99, self.audio, self.shake, self.particles)

        if self.player.hp <= 0:
            self.state = self.GAME_OVER
            self.audio.play("hit")

        for c in self.coins:
            if c.alive and self.player.rect.colliderect(c.rect):
                c.alive = False
                self.coins_collected += 1
                self.score += 50
                self.audio.play("coin")
                self.particles.burst(c.rect.centerx, c.rect.centery, YELLOW, count=8, speed=100)
        self.coins = [c for c in self.coins if c.alive]

        for e in self.enemies:
            if e.alive:
                e.update(dt, self.tilemap)
                if self.player.rect.colliderect(e.rect):
                    self.player.take_damage(1, self.audio, self.shake, self.particles)
        self.enemies = [e for e in self.enemies if e.alive]

        if self.boss and self.boss.alive:
            self.boss.update(dt, self.player, self.bullets)
            if self.player.rect.colliderect(self.boss.rect):
                self.player.take_damage(2, self.audio, self.shake, self.particles)

        for b in self.bullets:
            if not b.alive:
                continue
            b.update(dt, self.tilemap)
            brect = pygame.Rect(b.x - b.radius, b.y - b.radius, b.radius * 2, b.radius * 2)

            if b.is_player:
                for e in self.enemies:
                    if e.alive and brect.colliderect(e.rect):
                        b.alive = False
                        e.take_hit(1)
                        self.audio.play("hit")
                        self.particles.burst(b.x, b.y, PINK, count=6, speed=100)
                        if not e.alive:
                            self.score += 100

                if self.boss and self.boss.alive and brect.colliderect(self.boss.rect):
                    b.alive = False
                    self.boss.take_hit(1)
                    self.audio.play("boss_hit")
                    self.shake.add(4, 0.10)
                    self.particles.burst(b.x, b.y, PURPLE, count=10, speed=140)
                    if not self.boss.alive:
                        self.score += 2000
                        self.state = self.VICTORY
                        self.audio.play("victory")
            else:
                if brect.colliderect(self.player.rect):
                    b.alive = False
                    self.player.take_damage(1, self.audio, self.shake, self.particles)

        self.bullets = [b for b in self.bullets if b.alive]

        if self.current_level < 3 and self.player.rect.colliderect(self.portal_rect):
            self.load_level(self.current_level + 1)
            self.audio.play("victory")

        self.particles.update(dt)
        self.shake.update(dt)

    def draw_hud(self):
        for i in range(self.player.max_hp):
            color = RED if i < self.player.hp else (60, 20, 30)
            pygame.draw.rect(self.screen, color, (20 + i * 22, 20, 18, 14), border_radius=2)

        draw_text(self.screen, self.font_s, f"COINS: {self.coins_collected}", 20, 42, YELLOW)
        draw_text(self.screen, self.font_s, f"SCORE: {self.score}", 20, 62, CYAN)
        draw_text(self.screen, self.font_s, f"LEVEL 0{self.current_level}", WIDTH - 100, 20, PURPLE)

        if self.boss and self.boss.alive:
            bw = 300
            bx = (WIDTH - bw) // 2
            pygame.draw.rect(self.screen, (30, 10, 20), (bx, 20, bw, 16), border_radius=4)
            ratio = max(0, self.boss.hp / self.boss.max_hp)
            pygame.draw.rect(self.screen, PURPLE, (bx + 2, 22, int((bw - 4) * ratio), 12), border_radius=3)
            draw_text(self.screen, self.font_s, "BOSS CORRUPTION", WIDTH // 2, 21, WHITE, center=True)

    def draw(self):
        so = self.shake.offset()
        cx = int(self.camera.x + so[0])
        cy = int(self.camera.y + so[1])

        self.screen.fill(BG_COLOR)

        if self.state == self.START:
            draw_text(self.screen, self.font_l, "GLITCH CARTRIDGE", WIDTH // 2, 160, CYAN, center=True)
            draw_text(self.screen, self.font_m, "2026 RETRO EDITION", WIDTH // 2, 220, PINK, center=True)
            draw_text(self.screen, self.font_s, "WASD / ARROWS : Move & Jump", WIDTH // 2, 310, WHITE, center=True)
            draw_text(self.screen, self.font_s, "J / X : Shoot  |  LSHIFT / K : Dash", WIDTH // 2, 340, WHITE, center=True)
            draw_text(self.screen, self.font_m, "PRESS ENTER TO PLAY", WIDTH // 2, 430, YELLOW, center=True)

        elif self.state in (self.PLAYING, self.GAME_OVER, self.VICTORY):
            self.tilemap.draw(self.screen, cx, cy)

            if self.current_level < 3:
                dr = self.portal_rect.move(-cx, -cy)
                pygame.draw.rect(self.screen, PURPLE, dr, border_radius=6)
                pygame.draw.rect(self.screen, CYAN, dr.inflate(-6, -6), border_radius=4)

            for c in self.coins:
                c.draw(self.screen, cx, cy)

            for e in self.enemies:
                e.draw(self.screen, cx, cy)

            if self.boss and self.boss.alive:
                self.boss.draw(self.screen, cx, cy)

            for b in self.bullets:
                b.draw(self.screen, cx, cy)

            self.player.draw(self.screen, cx, cy)
            self.particles.draw(self.screen, cx, cy)

            self.draw_hud()

            if self.state == self.GAME_OVER:
                ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                ov.fill((10, 0, 5, 200))
                self.screen.blit(ov, (0, 0))
                draw_text(self.screen, self.font_l, "SYSTEM CRASH", WIDTH // 2, 200, RED, center=True)
                draw_text(self.screen, self.font_m, f"FINAL SCORE: {self.score}", WIDTH // 2, 270, WHITE, center=True)
                draw_text(self.screen, self.font_m, "PRESS R TO REBOOT", WIDTH // 2, 360, YELLOW, center=True)

            elif self.state == self.VICTORY:
                ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                ov.fill((0, 10, 5, 200))
                self.screen.blit(ov, (0, 0))
                draw_text(self.screen, self.font_l, "CARTRIDGE CLEARED!", WIDTH // 2, 200, GREEN, center=True)
                draw_text(self.screen, self.font_m, f"FINAL SCORE: {self.score}", WIDTH // 2, 270, WHITE, center=True)
                draw_text(self.screen, self.font_m, "PRESS R TO REPLAY", WIDTH // 2, 360, YELLOW, center=True)

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            running = self.handle_events()
            if not running:
                break
            self.update(dt)
            self.draw()
        pygame.quit()

if __name__ == "__main__":
    Game().run()
