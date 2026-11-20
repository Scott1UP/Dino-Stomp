"""Cafe table generator.

A small round table with a striped parasol. Two modules: the table (foot, leg
and top), and the parasol (pole and canopy) that stands on it. The seed varies
the stripe colour, the table top and the canopy shape.

    blender --background --factory-startup --python assets-src/props/cafe_table.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import BRIGHT, prism  # noqa: E402

TYPE = "cafe_table"
KIND = "prop"
TRIANGLE_BUDGET = 150

POLE = 0.19  # a four-sided pole about 0.27 m across
TABLE_Z = 1.1


def build(building_id, seed, scheme=None, collection=None):
    """Build one cafe table. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    stripe = rng.choice(BRIGHT)
    top_colour = rng.choice(["trimWhite", "wood", "wood"])
    canopy = rng.choice(["cone", "cone", "flat"])
    reach = rng.choice([1.5, 1.65, 1.8])
    height = rng.choice([3.1, 3.3])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    prism(kit, (0, 0), 0, 0.14, 0.55, 0.45, 6, "doorBrown")
    prism(kit, (0, 0), 0.14, TABLE_Z - 0.16, POLE, POLE, 4, "doorBrown", bottom=False, top=False)
    prism(kit, (0, 0), TABLE_Z - 0.16, TABLE_Z, 0.9, 0.9, 8, top_colour)
    table = building.add(kit, "detail", "wood", 0, collider="hull")

    eaves = height - 0.85
    kit = Kit()
    prism(kit, (0, 0), TABLE_Z, eaves, POLE, POLE, 4, "doorBrown", top=False)
    stripes = [stripe, "trimWhite"]
    if canopy == "cone":
        prism(kit, (0, 0), eaves, height, reach, 0.0, 8, stripe, bottom_colour="trimWhite", side_colours=stripes)
    else:
        prism(kit, (0, 0), eaves, height - 0.25, reach, reach * 0.35, 8, stripe, bottom_colour="trimWhite",
              side_colours=stripes)  # fmt: skip
    building.add(kit, "detail", "wood", 0, supports=(table,), collider="hull")

    return building.finish(look=f"{stripe} {canopy} reach={reach}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 8))


if __name__ == "__main__":
    previews()
