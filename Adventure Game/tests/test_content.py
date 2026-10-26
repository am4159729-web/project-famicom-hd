"""Catch typos: every sound or sprite name used in code must exist, and the art tables must be well formed."""
import re
from pathlib import Path

import pytest

pygame = pytest.importorskip("pygame")

from famicon.assets import GLYPHS, HERO, ITEM_ART, OLDMAN, Assets  # noqa: E402
from famicon.audio import MUSIC, SFX, hz, render_music, render_sfx  # noqa: E402
from famicon.enemies import BOSSES, ENEMIES  # noqa: E402

PKG = Path(__file__).resolve().parent.parent / "famicon"


def test_every_sound_effect_used_in_code_exists():
    used = set()
    for path in PKG.glob("*.py"):
        used |= set(re.findall(r'sfx\("([a-z_]+)"\)', path.read_text()))
    assert used and used <= set(SFX), sorted(used - set(SFX))


def test_every_music_track_used_by_the_game_exists():
    used = set(re.findall(r'(?:music = |"ow": |"in": )"([a-z]+)"', (PKG / "game.py").read_text()))
    used |= {"title", "victory", "dungeon", "boss", "cave", "overworld"}
    assert used <= set(MUSIC)


def test_audio_synthesis_is_in_range_and_in_tune():
    assert abs(hz("A4") - 440) < 1e-6 and abs(hz("C4") - 261.6256) < 1e-3
    for name in SFX:
        assert 0 < max(abs(v) for v in render_sfx(name, 22050)) <= 1.0
    for name in MUSIC:
        mix = render_music(name, 22050)
        assert len(mix) > 22050 * 4 and max(abs(v) for v in mix) <= 1.0


def test_art_tables_are_well_formed():
    for rows in list(HERO.values()) + [OLDMAN]:
        assert len(rows) == 16 and all(len(r) == 16 for r in rows)
    for ch, glyph in GLYPHS.items():
        rows = glyph.split()
        assert len(rows) == 5 and all(len(r) == 3 for r in rows), ch


def test_every_sprite_name_resolves():
    a = Assets()
    names = {cls.sprite for cls in ENEMIES.values()} | {"tidecrab_open", "tidecrab_shut"}
    names |= {cls.sprite for cls in BOSSES.values()} | {"player_down", "player_up", "player_left", "player_right"}
    names |= {"item_" + n for n in ITEM_ART} | {"oldman", "merchant", "bomb", "boomerang", "rock", "fire", "magic"}
    names |= {"bubble", "energy", "spear", "axe", "arrow", "beam", "heart_full", "heart_half", "heart_empty"}
    for name in names:
        assert a.sprite(name) is not a.sprites["missing"], name


def test_every_tile_character_is_drawn(game):
    a = Assets()
    seen = set()
    for screen in game.world.screens.values():
        for row in screen["tiles"]:
            seen |= set(row)
    for meta in game.world.dungeons.values():
        for room in meta["rooms"].values():
            for row in room["tiles"]:
                seen |= set(row)
    for ch in seen:
        for key in ("plains", "forest", "desert", "volcano", "graveyard", "beach", "dg:crypt"):
            assert a.tile(ch, key, 0) is not None and a.tile(ch, key, 1) is not None


def test_item_names_in_data_are_known(game):
    from famicon.data.interiors import INTERIORS
    from famicon.inventory import apply_item, Inventory
    names = {it["item"] for spec in INTERIORS.values() for it in spec["items"]}
    names |= {dr["item"] for meta in game.world.dungeons.values() for r in meta["rooms"].values() for dr in r["drops"]}
    names |= {"heart_container", "shard", "gem1", "gem5", "heart", "bomb"}
    for name in names:
        assert apply_item(Inventory(), name, 1, 5), name
        assert ("item_" + name) in Assets().sprites, name
