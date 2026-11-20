"""Hay cart generator.

A wooden farm cart piled with hay: a plank bed with board sides on two big
wheels, and a draw pole sloping down to the ground. Three modules: the wheels,
the cart body resting on them, and the hay resting in the cart. The seed
varies which way the pole points, the size of the wheels, the height of the
sides, the wood and the shape of the hay.

    blender --background --factory-startup --python assets-src/props/hay_cart.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import shapes_castle2 as castle  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import apothem, prism  # noqa: E402

TYPE = "hay_cart"
KIND = "prop"
TRIANGLE_BUDGET = 150
SPACING = 9


def build(building_id, seed, scheme=None, collection=None):
    """Build one hay cart. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    flip = seed % 2 == 0  # the pole points along +X, or -X when flipped
    wheel_r = rng.choice([0.8, 0.9, 1.0])
    side_h = rng.choice([0.55, 0.7, 0.85])
    colour = rng.choice(["wood", "wood", "doorBrown"])
    trim = "doorBrown" if colour == "wood" else "wood"
    hay = rng.choice(["heap", "tall", "double"])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)
    lx, ly = 1.7, 1.0
    bed = wheel_r + 0.1  # underside of the bed
    floor = bed + 0.18

    def add(kit, *args, **kwargs):
        if flip:
            castle.mirror_x(kit)
        return building.add(kit, *args, **kwargs)

    kit = Kit()
    for ya, yb in ((-ly - 0.32, -ly - 0.02), (ly + 0.02, ly + 0.32)):
        prism(kit, (0, apothem(wheel_r, 8)), ya, yb, wheel_r, wheel_r, 8, "tyre", bottom_colour=trim, top_colour=trim, axis="y")
    wheels = add(kit, "detail", "wood", 0, collider="hull")

    kit = Kit()
    kit.box((-lx, -ly, bed), (lx, ly, floor), colour)
    top = floor + side_h
    for ya, yb in ((-ly, -ly + 0.12), (ly - 0.12, ly)):
        kit.box((-lx, ya, floor), (lx, yb, top), colour, skip=("-z",), sides={"+z": trim})
    for xa, xb in ((-lx, -lx + 0.12), (lx - 0.12, lx)):
        kit.box((xa, -ly + 0.12, floor), (xb, ly - 0.12, top), colour, skip=("-z",), sides={"+z": trim})
    castle.beam(kit, (lx, 0, bed), (lx + 2.0, 0, 0.05), 0.24, 0.2, trim)
    body = add(kit, "detail", "wood", 0, supports=(wheels,))

    kit = Kit()

    def heap(x0, x1, z1, pinch):
        low = [(x0, -ly + 0.14, floor), (x1, -ly + 0.14, floor), (x1, ly - 0.14, floor), (x0, ly - 0.14, floor)]
        mx, w = (x0 + x1) / 2, (x1 - x0) / 2 * pinch
        high = [(mx - w, -ly * pinch, z1), (mx + w, -ly * pinch, z1), (mx + w, ly * pinch, z1), (mx - w, ly * pinch, z1)]
        kit.convex([high] + [[low[i], low[(i + 1) % 4], high[(i + 1) % 4], high[i]] for i in range(4)], "sunny")

    if hay == "double":
        heap(-lx + 0.14, 0.1, top + 0.9, 0.55)
        heap(-0.1, lx - 0.14, top + 0.5, 0.6)
    else:
        heap(-lx + 0.14, lx - 0.14, top + (1.3 if hay == "tall" else 0.7), 0.45 if hay == "tall" else 0.65)
    add(kit, "detail", "leaves", 0, supports=(body,), collider="hull")

    return building.finish(look=f"{'flipped ' if flip else ''}wheels={wheel_r} sides={side_h} {colour}/{hay}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
