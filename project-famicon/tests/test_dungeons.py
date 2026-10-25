import json

import pytest

from famicon.dungeon_gen import SPECS, generate, validate
from famicon.enemies import BOSSES, ENEMIES
from famicon.world import DATA


@pytest.mark.parametrize("num", sorted(SPECS))
def test_generated_dungeon_is_valid_and_solvable(num):
    assert validate(generate(num, 7)) == []


def test_committed_dungeons_match_generator(game):
    for num, meta in game.world.dungeons.items():
        fresh = generate(num, 7)
        assert [list(k) for k in sorted(meta["rooms"])] == sorted([r["x"], r["y"]] for r in fresh["rooms"])
        assert meta["boss_kind"] == fresh["boss_kind"]


def test_spawns_use_known_enemies(game):
    for meta in game.world.dungeons.values():
        for room in meta["rooms"].values():
            for spec in room["spawns"]:
                assert (spec[1] in BOSSES) if spec[0] == "boss" else (spec[0] in ENEMIES)


def test_each_dungeon_has_its_item_and_a_boss_room(game):
    for num, meta in game.world.dungeons.items():
        drops = [dr["item"] for r in meta["rooms"].values() for dr in r["drops"]]
        if meta["item"]:
            assert meta["item"] in drops
        boss_room = meta["rooms"][tuple(meta["boss"])]
        assert boss_room["doors"] and any(s[0] == "boss" for s in boss_room["spawns"])


def test_data_file_is_valid_json():
    assert len(json.loads((DATA / "dungeons.json").read_text())["dungeons"]) == 5
