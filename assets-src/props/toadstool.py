"""Toadstool generator.

A little cluster of two or three bright spotted mushrooms, the tallest about
1.5 m, in one module. The seed varies how many there are, their sizes, the cap
colour and how they are grouped.

    blender --background --factory-startup --python assets-src/props/toadstool.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_forest import dome  # noqa: E402

TYPE = "toadstool"
KIND = "prop"
TRIANGLE_BUDGET = 80  # one module, so the module budget is the limit
SPACING = 4

CAPS = ("tomato", "bubblegum", "tangerine", "sunny")


def build(building_id, seed, scheme=None, collection=None):
    """Build one cluster of toadstools. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    count = 2 + seed % 2  # cycled, so neighbouring seeds differ
    colour = CAPS[(seed // 2) % len(CAPS)]
    mixed = rng.random() < 0.3
    turn = rng.uniform(0, math.tau)

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    for n in range(count):
        tall = (1.5, 1.05, 0.8)[n] * rng.choice([0.92, 1.0])
        cap = tall * rng.choice([0.5, 0.56])  # the cap's radius
        if n == 0:
            x, y = 0.0, 0.0
        else:
            a = turn + n * 2.3
            x, y = math.cos(a) * 0.95, math.sin(a) * 0.95
        z = tall * 0.62
        shade = CAPS[(CAPS.index(colour) + n) % len(CAPS)] if mixed else colour
        dome(kit, x, y, [(0, tall * 0.19), (z + 0.05, tall * 0.14)], "trimWhite", sides=4, top=False)
        if n == 0 or count == 2:  # a proper domed cap
            spots = [(0, k, cap * 0.22) for k in ((0, 2, 4) if count == 2 and n == 0 else (n % 2, n % 2 + 3))]
            dome(kit, x, y, [(z, cap), (z + (tall - z) * 0.55, cap * 0.7), (tall, 0)], shade, sides=6, under="interiorCream", spots=spots, spot_sides=6 if n == 0 else 4)
        else:  # the little ones in a cluster of three get pointed caps, to stay inside the module budget
            dome(kit, x, y, [(z, cap), (tall, 0)], shade, sides=5, under="interiorCream", spots=[(0, 1, cap * 0.2), (0, 3, cap * 0.2)], spot_sides=4)
    building.add(kit, "detail", "rubber", 0, collider="hull")

    return building.finish(look=f"count={count} {colour}{' mixed' if mixed else ''}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
