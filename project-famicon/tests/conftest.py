import os
import sys
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

import pytest  # noqa: E402

from famicon.controls import Controls  # noqa: E402
from famicon.game import Game  # noqa: E402


@pytest.fixture
def game(tmp_path, monkeypatch):
    monkeypatch.setenv("FAMICON_SAVE_DIR", str(tmp_path))
    g = Game(seed=1)
    g.new_game()
    return g


def run(g, frames=1, **held):
    """Advance the game, holding the given controls (e.g. run(g, 30, up=True))."""
    for _ in range(frames):
        g.update(Controls(**held))


def press(g, name):
    g.update(Controls(**{name + "_press": True}))


def finish(g, limit=600):
    """Advance until the game is back in normal play (fades, holds, dialogs)."""
    for _ in range(limit):
        if g.mode == "play":
            return
        g.update(Controls(a_press=g.mode in ("dialog", "hold")))
    raise AssertionError("stuck in mode %s" % g.mode)


def kit(g):
    g.inv.sword = 3
    g.inv.tools |= {"boomerang", "bombs", "bow", "glove", "fins", "lantern"}
    g.inv.bombs, g.inv.gems, g.inv.equipped = 8, 200, "bombs"
