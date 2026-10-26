## Project Famicon: The Crown Shards
 
A top-down action adventure like the old 8-bit games, written in Python with pygame. You walk around a big overworld, find caves and secrets, beat five dungeons, and put the Crown back together.
 
Everything in it is made in code. The art, music, names, and text are all original, so there's nothing to download or license.
 
![Title screen](docs/screens/title.png)
 
![Overworld](docs/screens/overworld.png) ![Dungeon](docs/screens/dungeon.png)
![Boss fight](docs/screens/boss.png) ![Pause menu](docs/screens/menu.png)
 
*These screenshots come from the game's own renderer.*
 
## How to Run
 
You need Python 3.10+ and pygame 2.5+.
 
```bash
pip install -r requirements.txt
python main.py            # or: python -m famicon
python main.py --scale 4  # bigger window; --mute turns off sound
```
 
Saves go to `~/.project_famicon/slot1.json`. If you want them somewhere else, set the `FAMICON_SAVE_DIR` environment variable.
 
## Controls
 
| Action | Keys |
|---|---|
| Move | Arrow keys / WASD |
| Sword | Z / J / Space |
| Use item | X / K / Left Shift |
| Pause, items, save | Enter / P / Esc |
| Fullscreen | F11 |
 
## How to Play
 
You start with nothing. Go into the cave on the first screen and talk to the old man.
 
Hearts are your health. Each hit takes half a heart. When you're at full health, your sword shoots a beam.
 
Your shield blocks rocks and arrows if you're facing them. It doesn't block fire or magic.
 
Cut bushes, bomb cracked rocks, and push boulders. A lot of them hide caves with hearts, gems, and hints. Enemies drop gems, hearts, and bombs. You can spend gems at shops on bombs, potions, heart refills, and the lantern.
 
Each dungeon has a map, a compass, small keys, a boss key, and one big item. Beat the boss and you get a heart container and a shard of the Crown. Get four shards to open the gate to the Crown Citadel.
 
You can't go everywhere right away. Bombs open the eastern pass, the power glove moves boulders, and swim fins let you cross deep water.
 
| Dungeon | Where | Reward | Boss |
|---|---|---|---|
| 1 Mossroot Hollow | Forest, northwest | Boomerang | Thornwyrm |
| 2 Gravewatch Crypt | Graveyard, northeast | Power glove | Tidecrab |
| 3 Sunscar Pyramid | Desert, north | Swim fins | Magmamaw (bombs only) |
| 4 Drowned Spire | Island, southeast | Bow | Frostwyrm |
| 5 Crown Citadel | Volcano, northeast | None | The Warlock |
 
## The World
 
![Overworld map](docs/overworld.png)
 
Yellow rings are caves, red rings are dungeons, cyan rings are secrets, and the white square is where you start.
 
I made the overworld and the dungeons with scripts and saved the output as data files. That way you can rebuild them and check what changed.
 
```bash
python tools/worldgen.py --preview docs/overworld.png   # famicon/data/overworld.json
python tools/gen_dungeons.py                            # famicon/data/dungeons.json
```
 
`worldgen` builds the whole map as one big tile grid, so the land flows from screen to screen. It places gates, landmarks, and secrets, then checks that you can only reach each landmark once you have the right ability.
 
The dungeon generator puts locks on the path to the boss and puts keys somewhere you can reach before each lock. Then it checks that you can't get stuck.
 
## Project Layout
 
```
main.py                 entry point
famicon/
  game.py               game core: modes, rooms, scrolling, combat, items, save/load (no pygame)
  entities.py           player, projectiles, boomerang, bombs, pickups
  enemies.py            14 enemies and 5 bosses
  world.py              rooms, doors, overworld/dungeon/cave loading
  dungeon_gen.py        dungeon generator + solvability checker
  inventory.py          items and what they do
  assets.py             all art, drawn in code (tiles, sprites, bitmap font)
  render.py             drawing: world, HUD, menus, transitions
  audio.py              chiptune synth: sound effects and music
  app.py                pygame loop, input mapping, window scaling
  data/                 overworld.json, dungeons.json, interiors, room templates
tools/                  map and dungeon generators
tests/                  pytest suite (headless)
docs/                   architecture notes and screenshots
```
 
Check out [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) to see how everything fits together and how to add enemies, items, and caves.
 
## Tests
 
```bash
pip install pytest
pytest
```
 
The game core doesn't use pygame, so the tests can play the game without a window. They cover scrolling, caves, dungeons, keys, bosses, secrets, and saves. There are also long runs with random input that should never crash.
 
## Roadmap
 
I want to add more dungeons and bosses, multiple save slots, a warp whistle, bigger overworld set pieces, and gamepad support. Pull requests are welcome.
 
## Why I Made This
 
I wanted to see if I could build a whole 8-bit style adventure game with nothing but code. No art files, no sound files, no game engine. Just Python and pygame.
 
I also liked the idea of a world that scripts build for me but that I can still trust. Every landmark can be reached and every dungeon can be finished, and the generators check that so I don't have to find out by playing.
 
Mostly, it's a game I wanted to play, and making it was fun.
