import worldgen
from famicon.data.interiors import INTERIORS
from famicon.enemies import ENEMIES
from famicon.world import DATA


def test_world_is_gated_correctly():
    assert worldgen.check(worldgen.Builder(1986).build()) == []


def test_committed_overworld_matches_generator(tmp_path):
    out = tmp_path / "overworld.json"
    worldgen.dump(worldgen.Builder(1986).build(), out)
    assert out.read_text() == (DATA / "overworld.json").read_text()


def test_every_referenced_interior_and_enemy_exists(game):
    for screen in game.world.screens.values():
        assert len(screen["tiles"]) == 11 and all(len(r) == 16 for r in screen["tiles"])
        for _, _, iid in screen["caves"] + screen["secrets"]:
            assert iid in INTERIORS
        for kind, tx, ty in screen["spawns"]:
            assert kind in ENEMIES
            assert screen["tiles"][ty][tx] in ".,:s~"


def test_every_dungeon_has_one_gate(game):
    gates = sorted(s["dungeon"][2] for s in game.world.screens.values() if s["dungeon"])
    assert gates == [1, 2, 3, 4, 5]
