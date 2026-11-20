"""Cannon generator.

A toy cannon: a dark barrel with a flared muzzle on a wooden carriage with two
wheels and a trail that rests on the ground, and a small pile of cannonballs
beside it. Three modules: the carriage with its wheels, the barrel resting on
it, and the cannonballs (on their own, so they do not fly off stuck to the
carriage). The seed varies which way it points, the barrel's length and
colour, the wheels, the wood and where the cannonballs lie.

    blender --background --factory-startup --python assets-src/props/cannon.py
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

TYPE = "cannon"
KIND = "prop"
TRIANGLE_BUDGET = 150
SPACING = 8


def build(building_id, seed, scheme=None, collection=None):
    """Build one cannon. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    flip = seed % 2 == 0  # the muzzle points along +X, or -X when flipped
    length = rng.choice([2.9, 3.2, 3.5])
    wheel_r = rng.choice([0.75, 0.85])
    barrel_colour = rng.choice(["tyre", "tyre", "cobalt"])
    ring_colour = rng.choice(["sunny", "tomato"])
    colour = rng.choice(["wood", "doorBrown"])
    trim = "doorBrown" if colour == "wood" else "wood"
    pile_y = rng.choice([-1, 1]) * 1.55
    pile_x = rng.choice([-0.4, 0.3, 0.9])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    def add(kit, *args, **kwargs):
        if flip:
            castle.mirror_x(kit)
        return building.add(kit, *args, **kwargs)

    top = wheel_r + 0.3  # top of the carriage
    kit = Kit()
    kit.extrude_y([(-2.3, 0), (0.9, top - 0.5), (0.9, top), (-1.0, top)], -0.5, 0.5, colour)
    for ya, yb in ((-0.82, -0.52), (0.52, 0.82)):
        prism(kit, (0.1, apothem(wheel_r, 6)), ya, yb, wheel_r, wheel_r, 6, "tyre", bottom_colour=trim, top_colour=trim, axis="y")
    carriage = add(kit, "detail", "wood", 0, collider="hull")

    z = top + 0.32
    x0, x1 = -1.0, -1.0 + length
    kit = Kit()
    prism(kit, (0, z), x0, x1, 0.46, 0.34, 6, barrel_colour, top=False, axis="x")
    prism(kit, (0, z), x1, x1 + 0.34, 0.47, 0.47, 6, ring_colour, top_colour="tyre", axis="x")
    add(kit, "detail", "tin", 0, supports=(carriage,), collider="hull")

    r = 0.3
    kit = Kit()
    for dx, dy, dz in ((-r, 0, 0), (r, 0, 0), (0, 0.1, r * 1.55)):
        shapes.ball(kit, pile_x + dx, pile_y + dy, r + dz, r, "tyre", sides=5)
    add(kit, "detail", "tin", 0, collider="hull")

    return building.finish(look=f"{'flipped ' if flip else ''}length={length} wheels={wheel_r} {barrel_colour}/{ring_colour}/{colour}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
