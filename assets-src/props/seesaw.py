"""Seesaw generator.

A playground seesaw in two modules: a chunky pivot, and a long plank resting
on it with a handle and a seat pad at each end, tipped one way or the other.
About 5-6 m long, along X. The seed varies the length, which end is down,
the pivot (a wedge or a drum) and the colours.

    blender --background --factory-startup --python assets-src/props/seesaw.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_fair import beam  # noqa: E402
from lib.shapes_props import BRIGHT, prism  # noqa: E402

TYPE = "seesaw"
KIND = "prop"
TRIANGLE_BUDGET = 150

PIVOT_Z = 1.0


def build(building_id, seed, scheme=None, collection=None):
    """Build one seesaw. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    tip = 1 if seed % 2 else -1  # which end is up; alternates, so neighbouring seeds differ
    half = rng.choice([2.6, 2.9, 3.2])
    pivot = rng.choice(["wedge", "drum"])
    plank_colour, pivot_colour, pad_a, pad_b = rng.sample(BRIGHT, 4)

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    if pivot == "wedge":
        kit.extrude_y([(-0.8, 0.0), (0.8, 0.0), (0.25, PIVOT_Z - 0.1), (-0.25, PIVOT_Z - 0.1)], -0.55, 0.55, pivot_colour)
    else:
        prism(kit, (0, PIVOT_Z * 0.45), -0.55, 0.55, 0.52, 0.52, 6, pivot_colour, axis="y")
        kit.box((-0.6, -0.65, 0), (0.6, 0.65, 0.2), "trimWhite", skip=("-z",))
    base = building.add(kit, "detail", "wood", 0, collider="hull")

    # The plank: its low end rests just above the ground.
    lean = math.asin((PIVOT_Z - 0.3) / half) * tip
    along = (math.cos(lean), 0.0, math.sin(lean))
    up = (-math.sin(lean), 0.0, math.cos(lean))

    def at(s, lift=0.0):
        return (along[0] * s + up[0] * lift, 0.0, PIVOT_Z + 0.05 + along[2] * s + up[2] * lift)

    kit = Kit()
    beam(kit, at(-half), at(half), 0.8, plank_colour, depth=0.22, up=up)
    for sx, pad in ((-1, pad_a), (1, pad_b)):
        beam(kit, at(sx * (half - 1.3), 0.11), at(sx * (half - 1.3), 0.75), 0.9, "trimWhite", depth=0.22, up=along)
        beam(kit, at(sx * (half - 0.95), 0.11), at(sx * (half - 0.1), 0.11), 0.82, pad, depth=0.2, up=up, flat=False)
    building.add(kit, "detail", "wood", 0, supports=(base,), collider="hull")

    return building.finish(look=f"{pivot} half={half} tip{tip:+d} {plank_colour}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(9, 7))


if __name__ == "__main__":
    previews()
