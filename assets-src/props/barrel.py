"""Barrel generator.

A chunky wooden barrel, about 1.4 m across and 1.7 m tall, with two iron
hoops. One module. The seed varies the height and girth, the wood, the hoops
and the top: a lid, or open and full of apples or water.

    blender --background --factory-startup --python assets-src/props/barrel.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import shapes_castle2 as castle  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import prism  # noqa: E402

TYPE = "barrel"
KIND = "prop"
TRIANGLE_BUDGET = 150
SPACING = 5


def build(building_id, seed, scheme=None, collection=None):
    """Build one barrel. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    r = rng.choice([0.62, 0.7, 0.78])
    h = rng.choice([1.5, 1.7, 1.9])
    colour = rng.choice(["wood", "wood", "doorBrown"])
    hoop = rng.choice(["tyre", "tyre", "stone"])
    top = ("lid", "apples", "lid", "water")[seed % 4]  # cycled, so neighbouring seeds differ
    top_colour = {"lid": "doorBrown" if colour == "wood" else "wood", "apples": "tomato", "water": "windowBlue"}[top]

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    # Staves that bulge in the middle, with the two hoops as bands in the same skin.
    bands = ((0.0, 0.24, r * 0.8, r, colour), (0.24, 0.36, r, r, hoop), (0.36, 0.64, r, r, colour), (0.64, 0.76, r, r, hoop), (0.76, 1.0, r, r * 0.8, colour))
    for index, (fa, fb, ra, rb, c) in enumerate(bands):
        prism(kit, (0, 0), h * fa, h * fb, ra, rb, 6, c, bottom=index == 0, top=index == len(bands) - 1, top_colour=top_colour)
    building.add(kit, "detail", "wood", 0, collider="hull")

    return building.finish(look=f"r={r} h={h} {colour}/{hoop}/{top}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
