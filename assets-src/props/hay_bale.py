"""Hay bale generator: loose bales that roll and tumble.

Usually ONE big round bale: an eight-sided cylinder lying on its side (its
axle along X), about 2 m across and 1.6 m wide, a single hull module. Every
third seed (3, 6, 9...) is instead a little stack of three rectangular bales,
two side by side and one across the top, each its own box module. They sit on
each other exactly: no overlaps and no gaps, and the top bale's centre is over
the join it rests on (the same rule as toy_blocks.py). In the game every
module of a "block" is a loose physics body from the start.

The seed varies the round bale's size, its wrap (bare, a twine band or white
net) and its end faces; and the square bales' size and twine.

    blender --background --factory-startup --python assets-src/props/hay_bale.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import apothem, panel_y, prism  # noqa: E402

TYPE = "hay_bale"
KIND = "block"
TRIANGLE_BUDGET = 150

WRAPS = ("twine", "bare", "net")
PROUD = 0.02  # twine decals sit this far off a face; never on a face that touches another bale


def build(building_id, seed, scheme=None, collection=None):
    """Build one round bale, or a stack of three square ones. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    stack = seed % 3 == 0
    wrap = WRAPS[(seed - seed // 3) % len(WRAPS)]  # cycled through the round bales
    radius = rng.choice([1.0, 1.05, 1.1])  # to the corners: about 2 m across
    width = rng.choice([1.5, 1.6, 1.7])
    twine = rng.choice(["tangerine", "doorBrown"])
    swirl = rng.choice(["tangerine", "sunny"])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    if not stack:
        z = apothem(radius, 8)  # a flat on the ground
        hw = width / 2
        kit = Kit()
        if wrap == "twine":
            # One broad band of twine round the middle (three lengths of drum: all the module can afford).
            prism(kit, (0, z), -hw, -0.2, radius, radius, 8, "sunny", axis="x", bottom_colour="wood", top=False)
            prism(kit, (0, z), -0.2, 0.2, radius, radius, 8, twine, axis="x", bottom=False, top=False)
            prism(kit, (0, z), 0.2, hw, radius, radius, 8, "sunny", axis="x", bottom=False, top_colour="wood")
        else:
            side = "trimWhite" if wrap == "net" else "sunny"
            if wrap == "net":
                swirl = "wood"
            prism(kit, (0, z), -hw, hw, radius, radius, 8, side, axis="x", bottom_colour="sunny" if wrap == "net" else "wood", top_colour="sunny" if wrap == "net" else "wood")
            # The rolled-up heart of the bale, painted on each end.
            for facing in (-1, 1):
                x = facing * (hw + PROUD)
                ring = [(x, radius * 0.5 * math.cos(k * math.pi / 4), z + radius * 0.5 * math.sin(k * math.pi / 4)) for k in range(8)]
                kit.poly(ring, (facing, 0, 0), swirl)
        building.add(kit, "detail", "leaves", 0, collider="hull")
        return building.finish(look=f"round {wrap} r={radius} w={width}")

    # Three square bales: two on the ground, one resting across the join.
    w, d, t = rng.choice([(1.6, 1.0, 0.8), (1.8, 1.0, 0.9), (1.6, 1.1, 0.9)])
    under = []
    for index, (cx, z0) in enumerate(((-w / 2, 0.0), (w / 2, 0.0), (0.0, t))):
        kit = Kit()
        kit.box((cx - w / 2, -d / 2, z0), (cx + w / 2, d / 2, z0 + t), "sunny")
        for facing in (-1, 1):
            for x in (cx - w * 0.25, cx + w * 0.25):
                panel_y(kit, x - 0.07, x + 0.07, z0, z0 + t, facing * (d / 2 + PROUD), facing, twine)
        module = building.add(kit, "detail", "leaves", 0 if index < 2 else 1, supports=under if index == 2 else (), collider="box")
        if index < 2:
            under.append(module)
    return building.finish(look=f"stack of 3 {w}x{d}x{t}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(6, 6))


if __name__ == "__main__":
    previews()
