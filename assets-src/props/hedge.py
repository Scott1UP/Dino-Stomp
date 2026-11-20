"""Hedge generator.

One 3 m section of clipped hedge, about 1 m deep and 1.2 m tall: three chunky
faceted lumps in one module, so the hedge goes down a section at a time.
Sections tile end to end along X. The seed varies each lump's height and girth.

    blender --background --factory-startup --python assets-src/props/hedge.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "hedge"
KIND = "prop"
TRIANGLE_BUDGET = 150

LENGTH = 3.0
LUMPS = 3


def build(building_id, seed, scheme=None, collection=None):
    """Build one hedge section. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    step = LENGTH / LUMPS
    for index in range(LUMPS):
        x0 = -LENGTH / 2 + index * step
        height = rng.choice([1.05, 1.2, 1.35])
        half = rng.choice([0.45, 0.5, 0.55])
        shoulder = height * rng.choice([0.55, 0.65])
        top = half * rng.choice([0.45, 0.6])
        # Section order: bottom, back, back slope, top, front slope, front.
        kit.extrude_x(
            [(-half, 0), (half, 0), (half, shoulder), (top, height), (-top, height), (-half, shoulder)],
            x0,
            x0 + step,
            "hedge",
            colours={5: "leaf"},  # a lighter top, so the lumps read from above
        )
    building.add(kit, "detail", "leaves", 0)

    return building.finish()


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 8))


if __name__ == "__main__":
    previews()
