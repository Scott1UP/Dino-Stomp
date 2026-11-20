"""Street sign generator.

A post about 3.8 m tall carrying two coloured arrow-shaped blades that point
different ways, each with a white stripe instead of words, and a ball on top.
One module. The seed varies the height, the two colours, which ways the
blades point and whether they sit at one height or stepped.

    blender --background --factory-startup --python assets-src/props/street_sign.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import BRIGHT, ball, prism  # noqa: E402

TYPE = "street_sign"
KIND = "prop"
TRIANGLE_BUDGET = 150
SPACING = (6, 7)

SIDES = 6
POST_RADIUS = 0.17
LAYOUTS = ("corner", "opposite", "stepped")


def _blade(kit, axis, direction, z0, z1, colour, length):
    """An arrow-shaped board pointing along +/-X or +/-Y, with a white stripe on both faces."""
    d = direction
    zm = (z0 + z1) / 2
    section = [(d * 0.1, z0), (d * length, z0), (d * (length + 0.38), zm), (d * length, z1), (d * 0.1, z1)]
    stripe = [(d * 0.4, zm - 0.09), (d * (length - 0.1), zm - 0.09), (d * (length - 0.1), zm + 0.09), (d * 0.4, zm + 0.09)]
    if axis == "x":
        kit.extrude_y(section, -0.08, 0.08, colour)
        for facing in (-1, 1):
            kit.poly([(a, facing * 0.1, z) for a, z in stripe], (0, facing, 0), "trimWhite")
    else:
        kit.extrude_x(section, -0.08, 0.08, colour)
        for facing in (-1, 1):
            kit.poly([(facing * 0.1, a, z) for a, z in stripe], (facing, 0, 0), "trimWhite")


def build(building_id, seed, scheme=None, collection=None):
    """Build one street sign. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    layout = LAYOUTS[seed % len(LAYOUTS)]  # cycled, so neighbouring seeds always differ
    height = rng.choice([3.6, 3.8, 4.1])
    first, second = rng.sample(BRIGHT, 2)
    post = rng.choice(["tyre", "stone", "cobalt"])
    flip = rng.choice([-1, 1])
    length = rng.choice([1.5, 1.8])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    prism(kit, (0, 0), 0, 0.5, 0.4, 0.28, SIDES, post, bottom=False)
    prism(kit, (0, 0), 0.5, height, POST_RADIUS, POST_RADIUS, SIDES, post, bottom=False, top=False)
    ball(kit, (0, 0, height + 0.12), 0.32, 6, 2, "sunny")
    top = height - 0.15
    if layout == "corner":
        _blade(kit, "x", flip, top - 0.6, top, first, length)
        _blade(kit, "y", -1, top - 1.3, top - 0.7, second, length)
    elif layout == "opposite":
        _blade(kit, "x", flip, top - 0.6, top, first, length)
        _blade(kit, "x", -flip, top - 1.3, top - 0.7, second, length)
    else:
        _blade(kit, "y", flip, top - 0.6, top, first, length)
        _blade(kit, "x", flip, top - 1.6, top - 1.0, second, length)
    building.add(kit, "detail", "tin", 0)

    return building.finish(look=f"{layout} h={height} {first}/{second} {post}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=SPACING)


if __name__ == "__main__":
    previews()
