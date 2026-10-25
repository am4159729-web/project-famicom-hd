# Overworld: . grass  , flowers  : path  s sand  T tree  b bush  # mountain  X cracked rock
#            H boulder  ~ deep water  w shallows  = bridge  G gravestone  c cactus  l lava
#            C cave mouth  D dungeon gate
# Dungeon:   . floor  _ carpet  # wall  K block  B push block  v pit  O torch  S statue
#            x spikes  ~ water  l lava
SOLID = set("T#bXHGSOBcK")
WATER = set("~")
HAZARD = {"l": 2, "x": 1}
CUTTABLE = set("b")
BOMBABLE = set("X")
PUSHABLE = set("BH")
TRIGGERS = set("CD")
PITS = set("v")
