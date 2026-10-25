import pytest

pygame = pytest.importorskip("pygame")

from conftest import finish, kit, press, run  # noqa: E402
from famicon.assets import Assets  # noqa: E402
from famicon.constants import SCREEN_H, SCREEN_W  # noqa: E402
from famicon.game import Game  # noqa: E402
from famicon.render import Renderer  # noqa: E402


def draw(r, g):
    surf = pygame.Surface((SCREEN_W, SCREEN_H))
    r.draw(g, surf)
    return surf


def test_every_mode_renders(game):
    r = Renderer(Assets())
    kit(game)
    t = Game(seed=1)
    t.refresh_title()
    draw(r, t)
    draw(r, game)
    press(game, "start")
    draw(r, game)
    press(game, "start")
    game.say("HELLO TRAVELER THIS IS A LONG LINE OF TEXT THAT WRAPS")
    run(game, 30)
    draw(r, game)
    finish(game)
    game.player.x = 250.0
    run(game, 30, right=True)
    draw(r, game)
    finish(game)
    game.enter_interior(4, 6, "shop_west")
    run(game, 20)
    draw(r, game)
    finish(game)
    draw(r, game)
    game.inv.hp = 0
    game.on_player_death()
    for _ in range(100):
        game.update(__import__("famicon.controls", fromlist=["Controls"]).Controls())
        if game.mode == "gameover":
            break
    draw(r, game)
    game.mode = "victory"
    draw(r, game)


def test_every_dungeon_room_renders_with_enemies(game):
    r = Renderer(Assets())
    kit(game)
    for n, meta in game.world.dungeons.items():
        for pos in meta["rooms"]:
            game.dungeon = n
            game.set_room(game.world.dungeon_room(n, *pos, game.flags), 120, 100)
            game.mode = "play"
            run(game, 20)
            game.room.dark = pos[0] % 2 == 0
            draw(r, game)
            game.inv.hp = game.inv.max_hp


def test_every_overworld_screen_renders(game):
    r = Renderer(Assets())
    for (sx, sy) in game.world.screens:
        game.set_room(game.world.overworld_room(sx, sy, game.flags), 120, 80)
        game.mode = "play"
        run(game, 3)
        draw(r, game)
        game.inv.hp = game.inv.max_hp
