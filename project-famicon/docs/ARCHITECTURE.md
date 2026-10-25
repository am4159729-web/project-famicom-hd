# Architecture

## The core is pygame-free

`famicon/game.py` owns all state and rules. Each frame the app builds a `Controls` object and calls
`game.update(controls)`; the renderer reads the game back out. Sound is a list of names
(`game.take_sounds()`), music is a name (`game.music`). Because nothing in the core touches pygame,
the test suite can play thousands of frames headless.

Modes: `title`, `play`, `scroll` (screen slide), `fade` (caves, dungeon doors), `dialog`, `menu`,
`hold` (item-get pose), `dying`, `gameover`, `victory`.

## Coordinates

Rooms are 16x11 tiles of 16px (256x176). Entities use pixel positions inside the room. The HUD is the
top 48px of the 256x224 canvas, which the app scales up with nearest-neighbour.

## Data formats

- `overworld.json`: 128 screens, each with `tiles` (11 strings of 16), `theme`, `spawns`
  (`[kind, tx, ty]`), `caves` and `secrets` (`[tx, ty, interior_id]`) and an optional `dungeon` gate.
- `dungeons.json`: per dungeon a `meta` block and `rooms` with `tiles`, `doors` (N/S/E/W:
  `wall`, `open`, `locked`, `boss`, `bomb`, `exit`), `spawns`, `drops`, `shutter`, `dark`, `push_opens`.
- Persistent world changes are string flags (`gone:...`, `door:...`, `taken:...`, `cleared:...`,
  `boss:N`, `visited:...`) stored in the save file; rooms are rebuilt from static data plus flags.

## Recipes

**Add an enemy**: subclass `Enemy` in `enemies.py` (set `sprite`, `hp`, `speed`, implement `ai(self, g)`),
register it in `ENEMIES`, draw it in `assets.ENEMY_ART`, then reference its name in `worldgen.POOLS` or a
dungeon spec's `pool`. `tests/test_content.py` fails if a sprite or enemy name is missing.

**Add an item**: add a draw function to `assets.ITEM_ART`, handle it in `inventory.apply_item`, and put
it in an interior (`data/interiors.py`) or a dungeon drop. If it should interrupt play, add a line to
`inventory.MAJOR`.

**Add a cave or shop**: add an entry to `data/interiors.py`, then a `(screen_x, screen_y, "cave", id)`
line in `worldgen.LANDMARKS` and rerun `tools/worldgen.py`.

**Add a dungeon room layout**: add a 16x11 template to `data/room_templates.py`. Keep rows 4-5 and
columns 7-8 open so every door connects (the generator validates this). Rerun `tools/gen_dungeons.py`.

**Add a dungeon**: add a spec to `dungeon_gen.SPECS`, a `dungeon` landmark in `worldgen.LANDMARKS`, and
regenerate both data files.

## Generators

Both generators are deterministic for a given seed and committed as data. `tests/test_worldgen.py` and
`tests/test_dungeons.py` regenerate and compare, so hand-edits that drift from the generator are caught.
