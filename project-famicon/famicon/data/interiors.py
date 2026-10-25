"""Caves and shops. Item x positions are in tiles; `id` makes a pickup one-time."""


def _hint(text):
    return dict(npc="oldman", text=text, items=[])


INTERIORS = {
    "sword_cave": dict(npc="oldman", text="IT'S DANGEROUS TO GO ALONE! TAKE THIS.",
                       items=[dict(item="sword_wood", x=8, id="sword_wood")]),
    "steel_sword": dict(npc="oldman", text="BRAVE HEARTS EARN STEEL. COME BACK WITH 5 HEARTS.", need_hearts=5,
                        items=[dict(item="sword_steel", x=8, id="sword_steel")]),
    "magic_sword": dict(npc="oldman", text="ONLY A HERO WITH 10 HEARTS MAY WIELD THIS.", need_hearts=10,
                        items=[dict(item="sword_magic", x=8, id="sword_magic")]),
    "shop_west": dict(npc="merchant", text="BUY SOMETHIN' WILL YA!",
                      items=[dict(item="bomb_pack", x=4.5, price=15), dict(item="potion", x=8, price=40),
                             dict(item="lantern", x=11.5, price=90, id="shop_lantern")]),
    "shop_potion": dict(npc="merchant", text="WELCOME! HEALTHY HEARTS FOR SALE.",
                        items=[dict(item="heart_refill", x=4.5, price=25), dict(item="potion", x=8, price=40),
                               dict(item="bomb_bag", x=11.5, price=100, id="shop_bombbag")]),
    "shop_east": dict(npc="merchant", text="LONG WAY FROM HOME. SHOP A WHILE.",
                      items=[dict(item="bomb_pack", x=4.5, price=15), dict(item="potion", x=8, price=40),
                             dict(item="heart_refill", x=11.5, price=25)]),
    "hint_1": _hint("THE EAST IS CUT OFF BY STONE. FIND BOMBS."),
    "hint_2": _hint("FOUR SHARDS UNLOCK THE CROWN CITADEL."),
    "hint_3": _hint("THE HOLLOW GUARDS A BOOMERANG."),
    "hint_4": _hint("CRACKED ROCKS SOMETIMES HIDE CAVES."),
    "hint_5": _hint("THE GRAVEYARD SLEEPS UNEASILY."),
    "hint_6": _hint("THE CITADEL GATE OPENS ONLY FOR THE WORTHY."),
    "hint_7": _hint("HEAVY STONES MOVE FOR STRONG HANDS."),
}
for _i, _amt in enumerate((30, 20, 50, 30, 100, 50, 80), start=1):
    INTERIORS["gems_%d" % _i] = dict(npc="oldman", text="TAKE THIS, TRAVELER.",
                                     items=[dict(item="gems", amount=_amt, x=8, id="gems_%d" % _i)])
for _i in range(1, 7):
    INTERIORS["heart_%d" % _i] = dict(npc="oldman", text="A GIFT FOR THE CURIOUS.",
                                      items=[dict(item="heart_container", x=8, id="heart_%d" % _i)])
