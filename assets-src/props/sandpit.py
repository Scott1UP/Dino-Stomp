"""Sandpit generator.

A low square wooden frame full of sand, with a little sandcastle and a bucket
and spade left in it. About 4-5 m across. The frame's four boards, the sand,
the castle and the bucket are separate modules. The seed varies the size,
the board colour, the castle (one tower, twin towers or a keep with turrets)
and where the castle and bucket sit.

    blender --background --factory-startup --python assets-src/props/sandpit.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import BRIGHT, prism  # noqa: E402

TYPE = "sandpit"
KIND = "prop"
TRIANGLE_BUDGET = 150

BOARD = 0.35
RIM = 0.55
SAND = 0.32
CASTLES = ("tower", "twin", "keep")


def build(building_id, seed, scheme=None, collection=None):
    """Build one sandpit. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    castle = CASTLES[seed % len(CASTLES)]  # cycled, so neighbouring seeds always differ
    half = rng.choice([2.0, 2.2, 2.5])
    board_colour = rng.choice(["wood", "wood", "tomato", "cobalt", "leaf"])
    corner = rng.choice([(-1, 1), (1, 1), (-1, -1), (1, -1)])
    bucket_colour = rng.choice([c for c in BRIGHT if c not in (board_colour, "sunny")])
    sand_colour, castle_colour = "ground", "sunny"

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)
    add = building.add

    # --- the sand ---
    inner = half - BOARD
    kit = Kit()
    kit.box((-inner, -inner, 0), (inner, inner, SAND), sand_colour, skip=("-z",))
    sand = add(kit, "detail", "rubber", 0)

    # --- four boards: front and back run the full width ---
    for sy in (-1, 1):
        y0, y1 = sorted((sy * inner, sy * half))
        kit = Kit()
        kit.box((-half, y0, 0), (half, y1, RIM), board_colour, skip=("-z",), sides={"+z": "trimWhite"})
        add(kit, "detail", "wood", 0)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * inner, sx * half))
        kit = Kit()
        kit.box((x0, -inner, 0), (x1, inner, RIM), board_colour, skip=("-z", "-y", "+y"), sides={"+z": "trimWhite"})
        add(kit, "detail", "wood", 0)

    # --- the sandcastle ---
    cx, cy = corner[0] * inner * 0.38, corner[1] * inner * 0.38
    kit = Kit()
    if castle == "tower":
        prism(kit, (cx, cy), SAND, SAND + 0.7, 0.95, 0.8, 6, castle_colour, bottom=False)
        prism(kit, (cx, cy), SAND + 0.7, SAND + 1.4, 0.5, 0.42, 6, castle_colour, bottom=False, top=False)
        prism(kit, (cx, cy), SAND + 1.4, SAND + 1.95, 0.6, 0.0, 6, "tomato")
    elif castle == "twin":
        kit.box((cx - 0.9, cy - 0.3, SAND), (cx + 0.9, cy + 0.3, SAND + 0.6), castle_colour, skip=("-z",))
        for dx in (-0.8, 0.8):
            prism(kit, (cx + dx, cy), SAND, SAND + 1.1, 0.5, 0.42, 4, castle_colour, bottom=False, top=False)
            prism(kit, (cx + dx, cy), SAND + 1.1, SAND + 1.65, 0.58, 0.0, 4, "tomato")
    else:
        prism(kit, (cx, cy), SAND, SAND + 0.9, 1.15, 1.0, 4, castle_colour, bottom=False)
        for dx, dy in ((-0.6, -0.6), (0.6, -0.6), (0.6, 0.6), (-0.6, 0.6)):
            prism(kit, (cx + dx, cy + dy), SAND + 0.9, SAND + 1.3, 0.3, 0.0, 4, castle_colour, bottom=False)
        kit.box((cx - 0.06, cy - 0.06, SAND + 0.9), (cx + 0.06, cy + 0.06, SAND + 1.7), "trimWhite", skip=("-z", "+z"))
        kit.poly([(cx + 0.06, cy, SAND + 1.7), (cx + 0.06, cy, SAND + 1.3), (cx + 0.6, cy, SAND + 1.5)], (0, -1, 0), "tomato")
        kit.poly([(cx + 0.06, cy + 0.01, SAND + 1.7), (cx + 0.06, cy + 0.01, SAND + 1.3), (cx + 0.6, cy + 0.01, SAND + 1.5)], (0, 1, 0), "tomato")
    add(kit, "detail", "rubber", 0, supports=(sand,), collider="hull")

    # --- bucket and spade, in the opposite corner ---
    bx, by = -corner[0] * inner * 0.45, -corner[1] * inner * 0.4
    kit = Kit()
    prism(kit, (bx, by), SAND, SAND + 0.75, 0.36, 0.5, 6, bucket_colour, bottom=False, top_colour="trimWhite")
    sx = 1 if bx < 0 else -1
    x0, x1 = sorted((bx + sx * 0.7, bx + sx * 1.7))
    kit.box((x0, by - 0.1, SAND), (x1, by + 0.1, SAND + 0.12), "trimWhite", skip=("-z",))
    xa, xb = sorted((bx + sx * 1.4, bx + sx * 2.0))
    kit.box((xa, by - 0.28, SAND), (xb, by + 0.28, SAND + 0.14), bucket_colour, skip=("-z",))
    add(kit, "detail", "tin", 0, supports=(sand,), collider="hull")

    return building.finish(look=f"{castle} half={half} boards={board_colour} bucket={bucket_colour}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 8))


if __name__ == "__main__":
    previews()
