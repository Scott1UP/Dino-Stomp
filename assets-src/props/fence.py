"""Fence generator.

One 3 m section of chunky picket fence: pointed pickets on two rails, all one
module, so the fence goes down a section at a time. Sections tile end to end
along X. The seed varies the colour, the height and the number of pickets.

    blender --background --factory-startup --python assets-src/props/fence.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "fence"
KIND = "prop"
TRIANGLE_BUDGET = 150

LENGTH = 3.0
THICK = 0.26  # pickets and rails, front to back
RAIL = 0.25


def build(building_id, seed, scheme=None, collection=None):
    """Build one fence section. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    colour = rng.choice(["trimWhite", "trimWhite", "sunny", "tomato", "cobalt", "wood"])
    height = rng.choice([1.3, 1.45, 1.6])
    pickets = rng.choice([4, 5, 5])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    pitch = LENGTH / pickets
    width = pitch * 0.62
    for index in range(pickets):
        x = -LENGTH / 2 + pitch * (index + 0.5)
        kit.extrude_y(
            [
                (x - width / 2, 0),
                (x + width / 2, 0),
                (x + width / 2, height - width * 0.6),
                (x, height),
                (x - width / 2, height - width * 0.6),
            ],
            -THICK / 2,
            THICK / 2,
            colour,
        )
    # Two rails behind the pickets, running the full length so sections join up.
    for z in (0.3, height - width * 0.6 - 0.45):
        kit.box((-LENGTH / 2, THICK / 2, z), (LENGTH / 2, THICK / 2 + RAIL, z + RAIL), colour, skip=("-y",))
    building.add(kit, "detail", "wood", 0)

    return building.finish(look=f"{colour} h={height} pickets={pickets}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 8))


if __name__ == "__main__":
    previews()
