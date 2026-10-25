#!/usr/bin/env python3
"""Regenerate famicon/data/dungeons.json:  python tools/gen_dungeons.py [--seed N]"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from famicon.dungeon_gen import SPECS, generate, validate  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default=str(Path(__file__).resolve().parent.parent / "famicon" / "data" / "dungeons.json"))
    args = ap.parse_args()
    dungeons = [generate(n, args.seed) for n in sorted(SPECS)]
    for d in dungeons:
        bad = validate(d)
        if bad:
            sys.exit("dungeon %d: %s" % (d["id"], bad))
    out = ['{"dungeons": [']
    for i, d in enumerate(dungeons):
        head = {k: v for k, v in d.items() if k != "rooms"}
        out.append(' {"meta": %s,' % json.dumps(head))
        out.append('  "rooms": [')
        for j, r in enumerate(d["rooms"]):
            out.append('   {"x": %d, "y": %d, "role": "%s", "template": "%s", "shutter": %s, "dark": %s, "push_opens": %s,' % (
                r["x"], r["y"], r["role"], r["template"], json.dumps(r["shutter"]), json.dumps(r["dark"]), json.dumps(r["push_opens"])))
            out.append('    "doors": %s, "spawns": %s, "drops": %s,' % (json.dumps(r["doors"]), json.dumps(r["spawns"]), json.dumps(r["drops"])))
            out.append('    "tiles": [')
            out.extend('     "%s"%s' % (row, "," if k < 10 else "") for k, row in enumerate(r["tiles"]))
            out.append("    ]}%s" % ("," if j < len(d["rooms"]) - 1 else ""))
        out.append("  ]}%s" % ("," if i < len(dungeons) - 1 else ""))
    out.append("]}")
    Path(args.out).write_text("\n".join(out) + "\n", encoding="utf-8")
    for d in dungeons:
        roles = {}
        for r in d["rooms"]:
            roles[r["role"]] = roles.get(r["role"], 0) + 1
        print("D%d %-17s %2d rooms  %s" % (d["id"], d["name"], len(d["rooms"]), roles))


if __name__ == "__main__":
    main()
