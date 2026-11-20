"""Tree stump generator.

A fat stump about 2 m across with a pale cut top showing its growth rings and
two or three roots, in one module. The seed varies the height and girth, the
bark, the roots and a little leafy sprout.

    blender --background --factory-startup --python assets-src/props/stump.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import flat, polygon  # noqa: E402
from lib.shapes_forest import cone  # noqa: E402
from lib.shapes_props import prism  # noqa: E402

TYPE = "stump"
KIND = "prop"
TRIANGLE_BUDGET = 150
SPACING = 5


def build(building_id, seed, scheme=None, collection=None):
    """Build one stump. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    roots = 2 + seed % 2  # cycled, so neighbouring seeds differ
    height = rng.choice([0.8, 1.0, 1.3])
    girth = rng.choice([0.85, 0.95, 1.05])
    bark = rng.choice(["doorBrown", "doorBrown", "wood"])
    sprout = rng.choice([True, False])
    turn = rng.uniform(0, math.tau)

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)
    ring = "wood" if bark == "doorBrown" else "doorBrown"

    kit = Kit()
    prism(kit, (0, 0), 0, height, girth * 1.12, girth, 8, bark, bottom=False, top_colour="interiorCream")
    flat(kit, (0, 0, height), (0, 0, 1), polygon(girth * 0.62, 8), ring, lift=0.015)
    flat(kit, (0, 0, height), (0, 0, 1), polygon(girth * 0.4, 8), "interiorCream", lift=0.03)
    for n in range(roots):
        a = turn + n * math.tau / roots + rng.uniform(-0.3, 0.3)
        d = (math.cos(a), math.sin(a))
        t = (-d[1], d[0])
        inner, outer, w = girth * 0.6, girth * 1.12 + rng.choice([0.5, 0.65, 0.8]), 0.48
        foot = [(d[0] * inner + t[0] * w, d[1] * inner + t[1] * w, 0), (d[0] * inner - t[0] * w, d[1] * inner - t[1] * w, 0), (d[0] * outer, d[1] * outer, 0)]
        crown = (d[0] * inner, d[1] * inner, height * 0.8)
        kit.convex([foot] + [[foot[k], foot[(k + 1) % 3], crown] for k in range(3)], bark)
    if sprout:
        a = turn + 1.0
        x, y = math.cos(a) * girth * 0.45, math.sin(a) * girth * 0.45
        cone(kit, (x, y, height), 0.3, (x + 0.1, y, height + 0.75), 4, "leaf", under="hedge")
    building.add(kit, "detail", "wood", 0, collider="hull")

    return building.finish(look=f"h={height} girth={girth} roots={roots} {bark} sprout={int(sprout)}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
