"""Wheelbarrow generator.

A wheelbarrow about 3 m long with its wheel towards -Y, heaped with
vegetables, in one module: a bright tapered tray, one wheel, two handles and
a stand. The seed varies the tray colour and what is in it: pumpkins,
cabbages, a mixed load or hay.

    blender --background --factory-startup --python assets-src/props/wheelbarrow.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import shapes_farm as farm  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_fair import beam, hexa  # noqa: E402
from lib.shapes_props import apothem, prism  # noqa: E402

TYPE = "wheelbarrow"
KIND = "prop"
TRIANGLE_BUDGET = 150  # one module, so really 80

LOADS = ("pumpkins", "cabbages", "mixed", "hay")
TRAYS = ("tomato", "cobalt", "leaf", "sunny", "bubblegum")
WHEEL_R = 0.5


def build(building_id, seed, scheme=None, collection=None):
    """Build one wheelbarrow. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    load = LOADS[seed % len(LOADS)]  # cycled, so neighbouring seeds always differ
    tray = TRAYS[seed % len(TRAYS)]
    if (load == "hay" and tray == "sunny") or (load == "cabbages" and tray == "leaf"):
        tray = "cobalt"
    turn = rng.uniform(0, 1)

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    # The tray: narrow at the bottom, wide at the top, filled to the brim.
    z0, z1 = 0.75, 1.4
    bottom = [(-0.45, -0.75, z0), (0.45, -0.75, z0), (0.45, 0.55, z0), (-0.45, 0.55, z0)]
    top = [(-0.75, -1.15, z1), (0.75, -1.15, z1), (0.75, 0.85, z1), (-0.75, 0.85, z1)]
    fill = {"pumpkins": "doorBrown", "cabbages": "doorBrown", "mixed": "doorBrown", "hay": "sunny"}[load]
    hexa(kit, bottom, top, tray, colours={1: fill})
    # The wheel, the handles (running forward to the axle) and the legs.
    wz = apothem(WHEEL_R, 6)
    prism(kit, (-1.35, wz), -0.14, 0.14, WHEEL_R, WHEEL_R, 6, "tyre", axis="x", bottom_colour="trimWhite", top_colour="trimWhite")
    for sx in (-1, 1):
        beam(kit, (sx * 0.22, -1.35, wz), (sx * 0.62, 1.75, 1.15), 0.13, "wood", caps=False)
    kit.box((-0.55, 0.3, 0), (0.55, 0.46, z0), "tyre", skip=("-z", "+z"))  # the stand
    # The load.
    if load == "hay":
        kit.box((-0.6, -0.9, z1), (0.6, 0.6, z1 + 0.45), "sunny", skip=("-z",))
    else:
        colours = {"pumpkins": ("tangerine", "tangerine"), "cabbages": ("leaf", "hedge"), "mixed": ("tangerine", "leaf")}[load]
        for (x, y, r), colour in zip(((-0.12, -0.55, 0.56), (0.1, 0.32, 0.5)), colours):
            farm.blob(kit, (x, y, z1 - 0.02), r, r * 1.2, 4, colour, turn=turn)
    building.add(kit, "detail", "tin", 0, collider="hull")

    return building.finish(look=f"{load} tray={tray}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(5, 6))


if __name__ == "__main__":
    previews()
