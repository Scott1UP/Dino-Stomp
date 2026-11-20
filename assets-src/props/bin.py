"""Litter bin generator.

A flared eight-sided bin with a domed lid and a knob. Two modules: the body,
and the lid that pops off it. The seed varies the size and the colour pair.

    blender --background --factory-startup --python assets-src/props/bin.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import prism  # noqa: E402

TYPE = "bin"
KIND = "prop"
TRIANGLE_BUDGET = 150

SIDES = 8
COLOURS = [  # body, lid
    ("cobalt", "sunny"),
    ("tangerine", "trimWhite"),
    ("bubblegum", "cobalt"),
    ("sunny", "tomato"),
    ("tomato", "trimWhite"),
]


def build(building_id, seed, scheme=None, collection=None):
    """Build one bin. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    radius = rng.choice([0.55, 0.6, 0.65])
    height = rng.choice([1.2, 1.35, 1.5])
    body, lid = rng.choice(COLOURS)

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    # The dark top shows as the opening once the lid has gone.
    kit = Kit()
    prism(kit, (0, 0), 0, height, radius * 0.8, radius, SIDES, body, top_colour="tyre")
    body_id = building.add(kit, "detail", "tin", 0, collider="hull")

    kit = Kit()
    prism(kit, (0, 0), height, height + 0.16, radius + 0.1, radius + 0.1, SIDES, lid, top=False)
    prism(kit, (0, 0), height + 0.16, height + 0.42, radius + 0.1, radius * 0.4, SIDES, lid, bottom=False)
    prism(kit, (0, 0), height + 0.42, height + 0.62, 0.2, 0.2, 4, body, bottom=False)
    building.add(kit, "detail", "tin", 0, supports=(body_id,), collider="hull")

    return building.finish(look=f"r={radius} h={height} {body}/{lid}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 8))


if __name__ == "__main__":
    previews()
