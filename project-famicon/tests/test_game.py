import random

import pytest

from conftest import finish, kit, press, run
from famicon import save
from famicon.constants import PLAY_H, PLAY_W, TILE
from famicon.controls import Controls
from famicon.enemies import Enemy, Knight, Rocktopus, build_enemy
from famicon.entities import Pickup, Projectile
from famicon.game import Game


def goto_dungeon(g, n, room=None):
    g.dungeon = n
    d = g.world.dungeons[n]
    g.set_room(g.world.dungeon_room(n, *(room or d["start"]), g.flags), 120, 100)
    g.mode = "play"


def test_new_game_starts_on_the_start_screen(game):
    assert game.mode == "play" and game.room.key == "ow:2,6"
    assert game.inv.hp == 6 and game.inv.sword == 0


def test_walking_off_a_screen_scrolls_to_the_next(game):
    game.player.x, game.player.y = 150.0, 70.0
    # find a clear row to the east edge on the start screen
    row = next(ty for ty in range(1, 10) if game.room.tiles[ty][15] == "." and game.world.screens[(3, 6)]["tiles"][ty][0] == ".")
    game.player.y = row * TILE - 4
    game.player.x = 14 * TILE
    run(game, 60, right=True)
    assert game.mode in ("scroll", "play")
    finish(game)
    assert game.room.key == "ow:3,6"


def test_cave_gives_the_sword_and_leads_back(game):
    game.player.x, game.player.y, game.player.facing = 4 * TILE, 7 * TILE, "up"
    run(game, 40, up=True)
    finish(game)
    assert game.room.kind == "in" and game.inv.sword == 0
    game.player.x, game.player.y = 120.0, 96.0
    run(game, 2)
    assert game.mode == "hold"
    finish(game)
    assert game.inv.sword == 1 and "taken:sword_wood" in game.flags
    game.player.y = PLAY_H - 8
    run(game, 3, down=True)
    finish(game)
    assert game.room.key == "ow:2,6" and game.player.y > 6 * TILE


def test_dungeon_entrance_and_exit(game):
    sx, sy = next(k for k, s in game.world.screens.items() if s["dungeon"] and s["dungeon"][2] == 1)
    tx, ty, _ = game.world.screens[(sx, sy)]["dungeon"]
    game.set_room(game.world.overworld_room(sx, sy, game.flags), tx * TILE, (ty + 1) * TILE, "up")
    run(game, 30, up=True)
    finish(game)
    assert game.room.kind == "dg" and game.dungeon == 1
    game.player.y = PLAY_H - 6
    run(game, 3, down=True)
    finish(game)
    assert game.room.kind == "ow" and game.dungeon == 0


def test_final_gate_stays_shut_without_four_shards(game):
    sx, sy = next(k for k, s in game.world.screens.items() if s["dungeon"] and s["dungeon"][2] == 5)
    tx, ty, _ = game.world.screens[(sx, sy)]["dungeon"]
    game.set_room(game.world.overworld_room(sx, sy, game.flags), tx * TILE, (ty + 1) * TILE, "up")
    run(game, 30, up=True)
    assert game.mode == "dialog" and game.room.kind == "ow"
    finish(game)
    game.inv.shards = {1, 2, 3, 4}
    game.player.y = (ty + 1) * TILE
    run(game, 30, up=True)
    finish(game)
    assert game.dungeon == 5


def test_locked_door_opens_with_a_key_and_stays_open(game):
    n = next(n for n, d in game.world.dungeons.items() if any("locked" in r["doors"].values() for r in d["rooms"].values()))
    (rx, ry), rd = next(((k, r) for k, r in game.world.dungeons[n]["rooms"].items() if "locked" in r["doors"].values()))
    side = next(s for s, st in rd["doors"].items() if st == "locked")
    goto_dungeon(game, n, (rx, ry))
    game.room.shut = False
    cell = {"N": (7.5, 1), "S": (7.5, 9), "W": (1, 4.5), "E": (14, 4.5)}[side]
    game.player.x, game.player.y = cell[0] * TILE - 8, cell[1] * TILE - 8
    game.inv.keys[n] = 1
    run(game, 20, **{{"N": "up", "S": "down", "W": "left", "E": "right"}[side]: True})
    assert game.room.doors[side] == "open" and game.inv.keys[n] == 0
    fresh = game.world.dungeon_room(n, rx, ry, game.flags)
    assert fresh.doors[side] == "open"


def test_boss_drops_heart_and_shard_then_leaves_the_dungeon(game):
    kit(game)
    d = game.world.dungeons[1]
    game.ret = (2, 1, 5, 3)
    goto_dungeon(game, 1, tuple(d["boss"]))
    boss = next(e for e in game.entities if e.boss)
    for _ in range(80):
        boss.hurt_t = 0
        boss.hurt(game, 4, 1, 0)
        if boss.dead:
            break
    run(game, 2)
    items = {e.item for e in game.entities if isinstance(e, Pickup)}
    assert items == {"heart_container", "shard"} and "boss:1" in game.flags
    for pk in [e for e in game.entities if isinstance(e, Pickup)]:
        game.player.x, game.player.y = pk.x, pk.y
        run(game, 2)
        finish(game)
    assert game.inv.max_hp == 8 and 1 in game.inv.shards
    assert game.room.kind == "ow"


def test_final_boss_leads_to_victory(game):
    kit(game)
    goto_dungeon(game, 5, tuple(game.world.dungeons[5]["boss"]))
    boss = next(e for e in game.entities if e.boss)
    for _ in range(80):
        boss.hurt_t = 0
        boss.hidden = False
        boss.hurt(game, 5, 1, 0)
    run(game, 200)
    assert game.mode == "victory"


def test_sword_cuts_bushes_and_secrets_open_caves(game):
    kit(game)
    key = next(k for k, s in game.world.screens.items() if any(game.world.screens[k]["tiles"][ty][tx] == "b" for tx, ty, _ in s["secrets"]))
    tx, ty, iid = next((tx, ty, i) for tx, ty, i in game.world.screens[key]["secrets"] if game.world.screens[key]["tiles"][ty][tx] == "b")
    game.set_room(game.world.overworld_room(*key, game.flags), 0, 0)
    game.cut_bushes((tx * TILE + 2, ty * TILE + 2, 4, 4))
    assert game.room.tile(tx, ty) == "C" and game.room.caves[(tx, ty)] == iid
    again = game.world.overworld_room(*key, game.flags)
    assert again.tile(tx, ty) == "C" and again.caves[(tx, ty)] == iid


def test_bombs_break_cracked_rock_for_good(game):
    key = next(k for k, s in game.world.screens.items() if any(c == "X" for row in s["tiles"] for c in row))
    ty = next(y for y, row in enumerate(game.world.screens[key]["tiles"]) if "X" in row)
    tx = game.world.screens[key]["tiles"][ty].index("X")
    game.set_room(game.world.overworld_room(*key, game.flags), 0, 0)
    game.explode(tx * TILE + 8, ty * TILE + 8)
    assert game.room.tile(tx, ty) in ":C"
    assert game.world.overworld_room(*key, game.flags).tile(tx, ty) in ":C"


def test_boulders_need_the_glove(game):
    key = next(k for k, s in game.world.screens.items() if any(c == "H" for row in s["tiles"] for c in row))
    ty = next(y for y, row in enumerate(game.world.screens[key]["tiles"]) if "H" in row)
    tx = game.world.screens[key]["tiles"][ty].index("H")
    game.set_room(game.world.overworld_room(*key, game.flags), 0, 0)
    game.push_tile(tx, ty, 1, 0)
    assert game.room.tile(tx, ty) == "H"
    game.inv.tools.add("glove")
    game.push_tile(tx, ty, 1, 0)
    assert game.room.tile(tx, ty) != "H"


def test_push_block_puzzle_releases_the_compass(game):
    n, pos = next((n, k) for n, d in game.world.dungeons.items() for k, r in d["rooms"].items() if r["role"] == "compass")
    goto_dungeon(game, n, pos)
    ty = next(y for y, row in enumerate(game.room.tiles) if "B" in row)
    tx = game.room.tiles[ty].index("B")
    game.push_tile(tx, ty, 1, 0)
    assert any(isinstance(e, Pickup) and e.item == "compass" for e in game.entities)


def test_shield_blocks_frontal_projectiles_only(game):
    p = game.player
    p.x, p.y, p.facing = 120.0, 80.0, "right"
    game.add(Projectile(p.x + 30, p.y + 8, -2, 0, "rock"))
    run(game, 20)
    assert game.inv.hp == 6
    p.facing = "left"
    game.add(Projectile(p.x + 30, p.y + 8, -2, 0, "rock"))
    run(game, 20)
    assert game.inv.hp < 6


def test_knight_blocks_sword_from_the_front_but_not_bombs(game):
    kit(game)
    k = Knight(100, 80)
    k.facing = "right"
    game.add(k)
    assert not k.hurt(game, 2, -1, 0, "sword") and k.hp == 4
    assert k.hurt(game, 2, 1, 0, "sword") and k.hp == 2
    k.hurt_t = 0
    assert k.hurt(game, 4, -1, 0, "bomb")


def test_shop_sells_bombs_for_gems(game):
    game.inv.gems = 20
    game.enter_interior(4, 6, "shop_west")
    finish(game)
    pk = next(e for e in game.entities if isinstance(e, Pickup) and e.item == "bomb_pack")
    game.player.x, game.player.y = pk.x, pk.y
    run(game, 2)
    assert game.inv.gems == 5 and game.inv.bombs == 4


def test_shop_refuses_when_poor(game):
    game.inv.gems = 3
    game.enter_interior(4, 6, "shop_west")
    finish(game)
    pk = next(e for e in game.entities if isinstance(e, Pickup) and e.item == "bomb_pack")
    game.player.x, game.player.y = pk.x, pk.y
    run(game, 2)
    assert game.inv.gems == 3 and game.inv.bombs == 0 and not pk.dead


def test_steel_sword_cave_checks_hearts(game):
    game.enter_interior(9, 5, "steel_sword")
    finish(game)
    assert not any(isinstance(e, Pickup) for e in game.entities)
    game.inv.max_hp = 10
    game.ret = None
    game.enter_interior(9, 5, "steel_sword")
    finish(game)
    assert any(isinstance(e, Pickup) and e.item == "sword_steel" for e in game.entities)


def test_death_and_respawn(game):
    game.inv.hp = 1
    game.player.hurt(game, 2, 0, 0)
    assert game.mode == "dying"
    for _ in range(100):
        game.update(Controls())
    assert game.mode == "gameover"
    press(game, "a")
    finish(game)
    assert game.inv.hp == 6 and game.player.state == "walk" and game.room.key == "ow:2,6"


def test_boomerang_stuns_and_comes_back(game):
    from famicon.entities import Boomerang
    kit(game)
    game.inv.equipped = "boomerang"
    e = Rocktopus(150, 80)
    game.add(e)
    game.player.x, game.player.y, game.player.facing = 100.0, 76.0, "right"
    press(game, "b")
    assert game.find(Boomerang)
    stunned = False
    for _ in range(60):
        run(game, 1)
        stunned = stunned or e.stun > 0
    assert stunned and e.hp == e.__class__.hp
    run(game, 200)
    assert not game.find(Boomerang)


def test_boomerang_fetches_pickups(game):
    from famicon.entities import Boomerang
    kit(game)
    game.inv.equipped, game.inv.gems = "boomerang", 0
    game.player.x, game.player.y, game.player.facing = 20.0, 30.0, "right"
    assert not game.room.collides(game.player.box(), game.player)
    game.add(Pickup(70, 30, "gem5"))
    press(game, "b")
    run(game, 120)
    assert game.inv.gems == 5 and not game.find(Boomerang)


def test_save_round_trip(game, tmp_path):
    kit(game)
    game.inv.max_hp = 12
    game.flags.add("taken:heart_1")
    game.set_room(game.world.overworld_room(5, 4, game.flags), 100, 60)
    assert save.write(game.to_save())
    other = Game(seed=2)
    assert other.load_save(save.load())
    assert other.room.key == "ow:5,4" and other.inv.max_hp == 12 and other.inv.sword == 3
    assert other.flags == game.flags and (other.player.x, other.player.y) == (100, 60)
    assert "glove" in other.inv.tools


def test_save_inside_a_cave_resumes_outside(game):
    game.enter_interior(4, 6, "hint_1")
    finish(game)
    data = game.to_save()
    other = Game(seed=2)
    assert other.load_save(data) and other.room.kind == "ow"


def test_title_menu_new_game_and_continue(game, tmp_path):
    t = Game(seed=1)
    t.loader, t.saver = save.load, save.write
    t.refresh_title()
    assert not t.save_exists
    press(t, "a")
    assert t.mode == "play"
    t.saver(t.to_save())
    t.mode = "title"
    t.refresh_title()
    assert t.save_exists
    t.title_cursor = 1
    press(t, "a")
    assert t.mode == "play"


def test_pause_menu_equips_items(game):
    kit(game)
    game.inv.equipped = "boomerang"
    assert game.inv.equippable() == ["boomerang", "bombs", "bow"]
    press(game, "start")
    assert game.mode == "menu"
    press(game, "down")
    press(game, "down")
    press(game, "a")
    assert game.inv.equipped == "bow"
    press(game, "start")
    assert game.mode == "play"


def test_menu_save_and_quit(game, tmp_path):
    game.saver = save.write
    press(game, "start")
    for _ in range(len(game.menu_entries()) - 3 + 0):
        press(game, "down")
    assert game.menu_entries()[game.menu["cursor"]] == "SAVE"
    press(game, "a")
    assert save.load()["room"] == "ow:2,6" and game.mode == "play"
    press(game, "start")
    game.menu["cursor"] = len(game.menu_entries()) - 1
    press(game, "a")
    assert game.mode == "title"


def test_heart_containers_and_potions(game):
    from famicon.inventory import apply_item
    apply_item(game.inv, "heart_container")
    assert game.inv.max_hp == 8 and game.inv.hp == 8
    for _ in range(30):
        apply_item(game.inv, "heart_container")
    assert game.inv.max_hp == 28
    kit(game)
    game.inv.potions, game.inv.hp, game.inv.equipped = 1, 2, "potion"
    press(game, "b")
    assert game.inv.hp == game.inv.max_hp and game.inv.potions == 0


@pytest.mark.parametrize("seed", [1, 2, 3])
def test_random_play_never_crashes(seed):
    g = Game(seed=seed)
    g.new_game()
    kit(g)
    rng = random.Random(seed)
    direction, left = "up", 0
    for i in range(12000):
        c = Controls()
        if g.mode in ("dialog", "hold", "gameover", "victory", "menu"):
            c.a_press = True
        else:
            if left <= 0:
                direction, left = rng.choice(["up", "down", "left", "right"]), rng.randint(30, 120)
            left -= 1
            setattr(c, direction, True)
            c.a_press, c.b_press = rng.random() < 0.06, rng.random() < 0.03
        g.update(c)
        if i % 4 == 0 and g.mode == "play":
            g.inv.hp = g.inv.max_hp


def test_every_dungeon_room_runs(game):
    for n, d in game.world.dungeons.items():
        for pos in d["rooms"]:
            g = Game(seed=n)
            g.new_game()
            kit(g)
            goto_dungeon(g, n, pos)
            for i in range(240):
                g.update(Controls(a_press=g.mode in ("dialog", "hold"), left=i % 90 < 45, up=i % 60 < 30))
                g.inv.hp = g.inv.max_hp


def test_enemies_can_all_be_built_and_updated(game):
    from famicon.enemies import BOSSES, ENEMIES
    kit(game)
    for name in ENEMIES:
        game.entities = []
        e = build_enemy([name, 7, 5])
        game.add(e)
        for _ in range(240):
            for ent in list(game.entities):
                ent.update(game)
            game.resolve()
    for name in BOSSES:
        game.entities = []
        game.add(build_enemy(["boss", name, 7, 3]))
        for _ in range(400):
            for ent in list(game.entities):
                ent.update(game)
            game.entities = [x for x in game.entities if not x.dead]
