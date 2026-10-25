import argparse

import pygame

from . import save
from .assets import Assets
from .audio import Audio
from .constants import FPS, SCREEN_H, SCREEN_W
from .controls import Controls
from .game import Game
from .render import Renderer

HELD = {
    "up": (pygame.K_UP, pygame.K_w), "down": (pygame.K_DOWN, pygame.K_s),
    "left": (pygame.K_LEFT, pygame.K_a), "right": (pygame.K_RIGHT, pygame.K_d),
    "a": (pygame.K_z, pygame.K_j, pygame.K_SPACE), "b": (pygame.K_x, pygame.K_k, pygame.K_LSHIFT),
}
START_KEYS = (pygame.K_RETURN, pygame.K_p)


def read_controls(is_down, pressed):
    """is_down(key) -> bool for held keys; pressed is the set of keys that went down this frame."""
    c = Controls()
    for name, keys in HELD.items():
        setattr(c, name, any(is_down(k) for k in keys))
        setattr(c, name + "_press", any(k in pressed for k in keys))
    c.start_press = any(k in pressed for k in START_KEYS)
    c.back_press = pygame.K_ESCAPE in pressed
    return c


def main(argv=None):
    ap = argparse.ArgumentParser(prog="project-famicon", description="Project Famicon: The Crown Shards")
    ap.add_argument("--scale", type=int, default=3, help="window scale (default 3)")
    ap.add_argument("--mute", action="store_true", help="disable sound")
    ap.add_argument("--seed", type=int, help="seed the enemy AI and drops")
    args = ap.parse_args(argv)

    pygame.mixer.pre_init(22050, -16, 1, 512)
    pygame.init()
    window = pygame.display.set_mode((SCREEN_W * args.scale, SCREEN_H * args.scale))
    pygame.display.set_caption("Project Famicon")
    canvas = pygame.Surface((SCREEN_W, SCREEN_H))
    renderer, audio = Renderer(Assets()), Audio(not args.mute)
    game = Game(seed=args.seed)
    game.loader, game.saver = save.load, save.write
    game.refresh_title()
    clock = pygame.time.Clock()

    while not game.want_quit:
        pressed = set()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.want_quit = True
            elif event.type == pygame.KEYDOWN:
                pressed.add(event.key)
                if event.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
        keys = pygame.key.get_pressed()
        game.update(read_controls(lambda k: keys[k], pressed))
        for name in game.take_sounds():
            audio.play(name)
        audio.music(game.music)
        renderer.draw(game, canvas)
        pygame.transform.scale(canvas, window.get_size(), window)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()
