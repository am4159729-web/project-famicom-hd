from .constants import MAX_HEARTS

SWORD_DAMAGE = (0, 1, 2, 4)
SWORD_NAMES = ("NO", "WOODEN", "STEEL", "MAGIC")
TOOLS = ("boomerang", "bow", "glove", "fins", "lantern")
EQUIPPABLE = ("boomerang", "bombs", "bow", "potion")

# item -> message shown when picked up (only "major" items interrupt play)
MAJOR = {
    "sword_wood": "YOU GOT THE WOODEN SWORD!",
    "sword_steel": "YOU GOT THE STEEL SWORD!",
    "sword_magic": "YOU GOT THE MAGIC SWORD!",
    "boomerang": "YOU GOT THE BOOMERANG! IT STUNS FOES AND FETCHES LOOT.",
    "bow": "YOU GOT THE BOW! ARROWS COST GEMS.",
    "glove": "YOU GOT THE POWER GLOVE! PUSH HEAVY BOULDERS.",
    "fins": "YOU GOT THE SWIM FINS! DEEP WATER IS OPEN TO YOU.",
    "lantern": "YOU GOT THE LANTERN! DARK ROOMS GLOW.",
    "heart_container": "A HEART CONTAINER! YOUR LIFE GROWS.",
    "shard": "YOU FOUND A SHARD OF THE CROWN!",
    "map": "YOU GOT THE DUNGEON MAP!",
    "compass": "YOU GOT THE COMPASS!",
    "boss_key": "YOU GOT THE BOSS KEY!",
    "bomb_bag": "YOUR BOMB BAG GROWS!",
}


class Inventory:
    def __init__(self):
        self.max_hp = 6
        self.hp = 6
        self.gems = 0
        self.bombs = 0
        self.max_bombs = 8
        self.sword = 0
        self.potions = 0
        self.tools = set()
        self.equipped = ""
        self.keys = {}
        self.maps, self.compasses, self.boss_keys, self.shards = set(), set(), set(), set()

    def equippable(self):
        out = []
        for name in EQUIPPABLE:
            if (name == "bombs" and self.max_bombs and "bombs" in self.tools) or (name == "potion" and self.potions) \
                    or name in self.tools:
                out.append(name)
        return out

    def to_dict(self):
        return {"max_hp": self.max_hp, "hp": self.hp, "gems": self.gems, "bombs": self.bombs,
                "max_bombs": self.max_bombs, "sword": self.sword, "potions": self.potions,
                "tools": sorted(self.tools), "equipped": self.equipped,
                "keys": {str(k): v for k, v in self.keys.items()}, "maps": sorted(self.maps),
                "compasses": sorted(self.compasses), "boss_keys": sorted(self.boss_keys),
                "shards": sorted(self.shards)}

    @classmethod
    def from_dict(cls, d):
        inv = cls()
        for k in ("max_hp", "hp", "gems", "bombs", "max_bombs", "sword", "potions", "equipped"):
            setattr(inv, k, d.get(k, getattr(inv, k)))
        inv.tools = set(d.get("tools", []))
        inv.keys = {int(k): v for k, v in d.get("keys", {}).items()}
        for k in ("maps", "compasses", "boss_keys", "shards"):
            setattr(inv, k, set(d.get(k, [])))
        return inv


def apply_item(inv, name, dungeon=0, amount=0):
    """Give an item to the player. Returns True if it was accepted."""
    if name == "gem1":
        inv.gems = min(999, inv.gems + 1)
    elif name == "gem5":
        inv.gems = min(999, inv.gems + 5)
    elif name == "gems":
        inv.gems = min(999, inv.gems + (amount or 50))
    elif name == "heart":
        inv.hp = min(inv.max_hp, inv.hp + 2)
    elif name == "heart_refill":
        inv.hp = inv.max_hp
    elif name == "bomb" or name == "bomb_pack":
        if "bombs" not in inv.tools:
            inv.tools.add("bombs")
        inv.bombs = min(inv.max_bombs, inv.bombs + (2 if name == "bomb" else 4))
        if not inv.equipped:
            inv.equipped = "bombs"
    elif name == "bomb_bag":
        inv.max_bombs += 4
    elif name == "potion":
        inv.potions += 1
    elif name == "small_key":
        inv.keys[dungeon] = inv.keys.get(dungeon, 0) + 1
    elif name == "boss_key":
        inv.boss_keys.add(dungeon)
    elif name == "map":
        inv.maps.add(dungeon)
    elif name == "compass":
        inv.compasses.add(dungeon)
    elif name == "heart_container":
        inv.max_hp = min(MAX_HEARTS * 2, inv.max_hp + 2)
        inv.hp = inv.max_hp
    elif name == "shard":
        inv.shards.add(dungeon)
    elif name in TOOLS:
        inv.tools.add(name)
        if name in EQUIPPABLE and not inv.equipped:
            inv.equipped = name
    elif name.startswith("sword_"):
        level = {"sword_wood": 1, "sword_steel": 2, "sword_magic": 3}[name]
        inv.sword = max(inv.sword, level)
    else:
        return False
    return True
