"""Beehive generator.

A white wooden beehive about 2.3 m tall on stubby legs, in one module:
stacked boxes that step in a little as they go up, a landing board and a dark
entrance slot at the front, and a bright lid. The seed varies the number of
boxes, the lid (gabled, flat or a pointed cap), the lid's colour and whether
one box is painted.

    blender --background --factory-startup --python assets-src/props/beehive.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_castle2 import pyramid  # noqa: E402
from lib.shapes_props import panel_y  # noqa: E402

TYPE = "beehive"
KIND = "prop"
TRIANGLE_BUDGET = 150  # one module, so really 80

LIDS = ("gabled", "flat", "pointed")
LID_COLOURS = ("sunny", "cobalt", "tomato", "tangerine", "leaf")


def build(building_id, seed, scheme=None, collection=None):
    """Build one beehive. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    lid = LIDS[seed % len(LIDS)]  # cycled, so neighbouring seeds always differ
    lid_colour = LID_COLOURS[seed % len(LID_COLOURS)]
    boxes = rng.choice([2, 3, 3])
    painted = rng.choice([None, 0, 1])  # which box, if any, takes the lid's colour
    box_h = 0.55

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    half = 0.8
    legs = 0.55
    for x in (-half + 0.05, half - 0.3):
        kit.box((x, -half + 0.1, 0), (x + 0.25, half - 0.1, legs), "doorBrown", skip=("-z", "+z"))
    kit.box((-half - 0.05, -half - 0.45, legs), (half + 0.05, half + 0.05, legs + 0.12), "wood")  # floor and landing board
    z = legs + 0.12
    for k in range(boxes):
        h = half - 0.06 * k
        colour = lid_colour if painted == k else "trimWhite"
        kit.box((-h, -h, z), (h, h, z + box_h), colour, skip=("-z",) if k else ("-z", "+z"))
        if k == 0:
            panel_y(kit, -0.4, 0.4, z + 0.03, z + 0.2, -h - 0.02, -1, "tyre")  # the entrance
        else:
            panel_y(kit, -0.22, 0.22, z + 0.22, z + 0.34, -h - 0.02, -1, "wood")  # a hand hold
        z += box_h
    top = half - 0.06 * (boxes - 1) + 0.14
    if lid == "gabled":
        kit.extrude_y([(-top, z), (top, z), (0, z + 0.55)], -top, top, lid_colour)
    elif lid == "flat":
        kit.box((-top, -top, z), (top, top, z + 0.22), lid_colour, skip=("-z",))
        pyramid(kit, 0, 0, 0.3, 0.3, z + 0.22, 0.25, "stone")
    else:
        pyramid(kit, 0, 0, top, top, z, 0.7, lid_colour)
    building.add(kit, "detail", "wood", 0, collider="hull" if lid != "flat" else "box")

    return building.finish(look=f"{boxes} boxes lid-{lid} {lid_colour} painted={painted}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(4, 4))


if __name__ == "__main__":
    previews()
