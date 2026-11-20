"""Banner pole generator.

A tall pole, about 7 m high and 0.32 m thick, on a stone block, with a long
bright banner hanging from an arm near the top and a gold point on the tip.
One module. The seed varies the height, the colours, whether the banner hangs
to one side of the pole or in front of it, and its tail (a point or a
swallowtail) and badge.

    blender --background --factory-startup --python assets-src/props/banner_pole.py
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

TYPE = "banner_pole"
KIND = "prop"
TRIANGLE_BUDGET = 150
SPACING = 7

THICK = 0.32


def build(building_id, seed, scheme=None, collection=None):
    """Build one banner pole. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    height = rng.choice([6.7, 7.0, 7.3])
    colour = castle.BRIGHTS[seed % 3]  # cycled, so neighbouring seeds differ
    second = rng.choice([c for c in castle.BRIGHTS + ["bubblegum", "tangerine"] if c != colour])
    style = rng.choice(["side", "side", "front"])
    tail = rng.choice(["point", "swallow"])
    badge = rng.choice(["square", "diamond", "stripe"])
    length = rng.choice([3.8, 4.3, 4.8])
    pole = rng.choice(["trimWhite", "doorBrown"])
    direction = rng.choice([-1, 1])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    h = THICK / 2
    kit = Kit()
    kit.box((-0.55, -0.55, 0), (0.55, 0.55, 0.45), "stone", skip=("-z",))
    kit.box((-h, -h, 0.45), (h, h, height), pole, skip=("-z", "+z"))
    castle.pyramid(kit, 0, 0, 0.3, 0.3, height, 0.65, "sunny")

    # The banner hangs in the XZ plane from an arm.
    z_top = height - 0.7
    width = 1.7
    if style == "side":
        xa, y = h + 0.12, 0.0
        kit.box((h, -0.09, z_top), (h + width + 0.3, 0.09, z_top + 0.2), pole, skip=("-x",))
    else:
        xa, y = -width / 2, -h - 0.12
        kit.box((-width / 2 - 0.2, y - 0.09, z_top), (width / 2 + 0.2, y + 0.09, z_top + 0.2), pole)
        kit.box((-0.08, y, z_top + 0.02), (0.08, -h, z_top + 0.18), pole, skip=("-y", "+y"))
    xb = xa + width
    xm = (xa + xb) / 2
    z_end = z_top - length

    def cloth(points, c, proud=0.0):
        """A flat shape in the banner's plane, seen from both sides. Points are (x, z)."""
        for facing in (-1, 1):
            kit.poly([(x, y + facing * (0.03 + proud), z) for x, z in points], (0, facing, 0), c)

    if tail == "point":
        cloth([(xa, z_top), (xb, z_top), (xb, z_end + 0.8), (xm, z_end), (xa, z_end + 0.8)], colour)
    else:
        cloth([(xa, z_top), (xm, z_top), (xm, z_end + 0.75), (xa, z_end)], colour)
        cloth([(xm, z_top), (xb, z_top), (xb, z_end), (xm, z_end + 0.75)], colour)
    cloth([(xa, z_top - 0.7), (xb, z_top - 0.7), (xb, z_top - 0.3), (xa, z_top - 0.3)], second, 0.03)
    zc = z_top - length * 0.45
    if badge == "square":
        cloth([(xm - 0.4, zc - 0.4), (xm + 0.4, zc - 0.4), (xm + 0.4, zc + 0.4), (xm - 0.4, zc + 0.4)], "trimWhite", 0.03)
    elif badge == "diamond":
        cloth([(xm, zc - 0.6), (xm + 0.5, zc), (xm, zc + 0.6), (xm - 0.5, zc)], "trimWhite", 0.03)
    else:
        cloth([(xm - 0.22, z_end + 1.0), (xm + 0.22, z_end + 1.0), (xm + 0.22, z_top - 0.7), (xm - 0.22, z_top - 0.7)], "trimWhite", 0.03)
    if style == "side" and direction < 0:
        castle.mirror_x(kit)
    building.add(kit, "detail", "wood", 0)

    return building.finish(look=f"h={height} {colour}/{second} {style}/{tail}/{badge} length={length}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
