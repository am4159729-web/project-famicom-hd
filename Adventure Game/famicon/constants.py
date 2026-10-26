TILE = 16
ROOM_W, ROOM_H = 16, 11
PLAY_W, PLAY_H = ROOM_W * TILE, ROOM_H * TILE
HUD_H = 48
SCREEN_W, SCREEN_H = PLAY_W, PLAY_H + HUD_H
FPS = 60
OW_COLS, OW_ROWS = 16, 8

DIRS = {"up": (0, -1), "down": (0, 1), "left": (-1, 0), "right": (1, 0)}
OPPOSITE = {"up": "down", "down": "up", "left": "right", "right": "left"}
SIDE = {"up": "N", "down": "S", "left": "W", "right": "E"}
SIDE_DIR = {v: k for k, v in SIDE.items()}
SIDE_OPP = {"N": "S", "S": "N", "E": "W", "W": "E"}

# doorway cells on each side of a dungeon room (tile coordinates)
DOOR_CELLS = {
    "N": [(7, 0), (8, 0)],
    "S": [(7, 10), (8, 10)],
    "W": [(0, 4), (0, 5)],
    "E": [(15, 4), (15, 5)],
}

MAX_HEARTS = 14
