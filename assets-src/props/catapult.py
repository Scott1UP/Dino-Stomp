"""Catapult generator.

A wooden siege catapult on four small wheels: a timber base frame, two
uprights with a cross-beam, and a long throwing arm with a cup at one end and
a stone counterweight at the other. Three modules: the wheels, the base on
them, and the arm assembly on the base. The seed varies which way it faces,
whether the arm is wound down with a bright ball in the cup or has just been
let fly, the height of the uprights and the colours.

    blender --background --factory-startup --python assets-src/props/catapult.py
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
import math  # noqa: E402

TYPE = "catapult"
KIND = "prop"
TRIANGLE_BUDGET = 200
SPACING = 10


def build(building_id, seed, scheme=None, collection=None):
    """Build one catapult. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    flip = seed % 2 == 0
    loaded = rng.choice([True, True, False])
    post_h = rng.choice([2.0, 2.3, 2.6])
    colour = rng.choice(["wood", "wood", "doorBrown"])
    trim = "doorBrown" if colour == "wood" else "wood"
    ball_colour = rng.choice(["tomato", "cobalt", "tyre"])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    def add(kit, *args, **kwargs):
        if flip:
            castle.mirror_x(kit)
        return building.add(kit, *args, **kwargs)

    lx, ly = 2.4, 1.1
    r = 0.6
    z0, z1 = 0.55, 0.9

    kit = Kit()
    for x in (-1.6, 1.6):
        for ya, yb in ((-ly - 0.5, -ly - 0.2), (ly + 0.2, ly + 0.5)):
            prism(kit, (x, apothem(r, 6)), ya, yb, r, r, 6, "tyre", bottom_colour=trim, top_colour=trim, axis="y")
    wheels = add(kit, "detail", "wood", 0, collider="hull")

    kit = Kit()
    for ya, yb in ((-ly - 0.17, -ly + 0.17), (ly - 0.17, ly + 0.17)):
        kit.box((-lx, ya, z0), (lx, yb, z1), colour)
    for x in (-2.0, 2.0):
        kit.box((x - 0.17, -ly + 0.17, z0), (x + 0.17, ly - 0.17, z1), colour, skip=("-y", "+y"))
    base = add(kit, "detail", "wood", 0, supports=(wheels,))

    # --- uprights, cross-beam and the arm ---
    px = 0.5
    pivot = z1 + post_h
    kit = Kit()
    for y in (-ly, ly):
        kit.box((px - 0.17, y - 0.17, z1), (px + 0.17, y + 0.17, pivot + 0.15), trim, skip=("-z",))
    kit.box((px - 0.13, -ly + 0.17, pivot - 0.28), (px + 0.13, ly - 0.17, pivot - 0.02), trim, skip=("-y", "+y"))
    angle = math.radians(-22 if loaded else 58)  # how far the long end is above the pivot
    long, short = 3.3, 1.1
    tip = (px - long * math.cos(angle), 0, pivot + long * math.sin(angle))
    tail = (px + short * math.cos(angle), 0, pivot - short * math.sin(angle))
    castle.beam(kit, tip, tail, 0.3, 0.26, colour)
    kit.box((tip[0] - 0.45, -0.45, tip[2] + 0.2), (tip[0] + 0.45, 0.45, tip[2] + 0.55), trim, sides={"+z": "tyre"})
    if loaded:
        shapes.ball(kit, tip[0], 0, tip[2] + 0.9, 0.42, ball_colour, sides=4)
    kit.box((tail[0] - 0.4, -0.4, tail[2] - 0.75), (tail[0] + 0.4, 0.4, tail[2] + 0.02), "stone")
    add(kit, "detail", "wood", 0, supports=(base,), collider="hull")

    return building.finish(look=f"{'flipped ' if flip else ''}{'loaded' if loaded else 'fired'} posts={post_h} {colour}/{ball_colour}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
