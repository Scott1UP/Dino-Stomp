"""Flower planter generator.

A low wooden box planter with a mound of green leaves and a row of chunky
bright flower blobs. One module. The seed varies the length, the number of
flowers and their colours.

    blender --background --factory-startup --python assets-src/props/flower_planter.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import BRIGHT, prism  # noqa: E402

TYPE = "flower_planter"
KIND = "prop"
TRIANGLE_BUDGET = 150

HALF_DEPTH = 0.5
BOX = 0.7  # height of the box
MOUND = 1.0  # top of the leaves


def build(building_id, seed, scheme=None, collection=None):
    """Build one planter. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    half = rng.choice([1.0, 1.2, 1.4])
    flowers = rng.choice([4, 5, 5])
    colours = rng.sample(BRIGHT, rng.choice([1, 2, 3]))
    box_colour = rng.choice(["wood", "wood", "doorBrown"])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    kit.box((-half, -HALF_DEPTH, 0), (half, HALF_DEPTH, BOX), box_colour, sides={"+z": "doorBrown"})
    kit.extrude_x(
        [(-0.4, BOX), (0.4, BOX), (0.26, MOUND), (-0.26, MOUND)],
        -half + 0.1,
        half - 0.1,
        "leaf",
    )
    pitch = (half * 2 - 0.3) / flowers
    for index in range(flowers):
        x = -half + 0.15 + pitch * (index + 0.5)
        y = 0.1 if index % 2 else -0.1
        petals = colours[index % len(colours)]
        centre = "trimWhite" if petals == "sunny" else "sunny"
        prism(kit, (x, y), MOUND - 0.05, MOUND + 0.3, 0.32, 0.19, 4, petals, bottom=False, top_colour=centre)
    building.add(kit, "detail", "wood", 0)

    return building.finish(look=f"len={half * 2} flowers={flowers} {'/'.join(colours)}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 8))


if __name__ == "__main__":
    previews()
