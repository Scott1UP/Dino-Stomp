"""Lollipop tree generator.

A rounded toy tree in two modules: a stout trunk, and a faceted top that rests
on it. About 5-6 m tall. The seed varies the height and the top: a ball, a
pair of stacked cones, or a double ball.

    blender --background --factory-startup --python assets-src/props/tree.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import ball, prism  # noqa: E402

TYPE = "tree"
KIND = "prop"
TRIANGLE_BUDGET = 150

TOPS = ("ball", "cone", "double", "ball")


def _leaves(segment, ring):
    """Darker underneath, so the top reads as round even in flat light."""
    return "hedge" if ring == 0 else "leaf"


def build(building_id, seed, scheme=None, collection=None):
    """Build one tree. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    top = TOPS[seed % len(TOPS)]  # cycled, so neighbouring seeds always differ
    trunk_height = rng.choice([2.2, 2.5, 2.8])
    trunk_colour = rng.choice(["doorBrown", "doorBrown", "wood"])
    size = rng.choice([0.9, 1.0, 1.1])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    prism(kit, (0, 0), 0, trunk_height, 0.42, 0.3, 6, trunk_colour)
    trunk = building.add(kit, "detail", "wood", 0, collider="hull")

    kit = Kit()
    z = trunk_height - 0.3  # the top sits down over the trunk
    if top == "ball":
        radius = 1.65 * size
        ball(kit, (0, 0, z + radius), radius, 8, 4, "leaf", _leaves)
    elif top == "cone":
        radius = 1.75 * size
        prism(kit, (0, 0), z, z + 2.2, radius, 0.0, 8, "leaf", bottom_colour="hedge")
        prism(kit, (0, 0), z + 1.3, z + 3.4, radius * 0.72, 0.0, 8, "leaf", bottom_colour="hedge")
    else:
        radius = 1.4 * size
        ball(kit, (0, 0, z + radius), radius, 6, 4, "leaf", _leaves)
        ball(kit, (0, 0, z + radius * 2.15), radius * 0.72, 6, 4, "leaf", _leaves)
    building.add(kit, "detail", "leaves", 0, supports=(trunk,), collider="hull")

    return building.finish(look=f"{top} trunk={trunk_height} size={size}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 8))


if __name__ == "__main__":
    previews()
