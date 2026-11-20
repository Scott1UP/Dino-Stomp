"""Farm trailer generator.

A two-wheeled farm trailer about 4.8 m long with its drawbar towards -Y,
loaded up. Three modules: the bed (with its drawbar and end boards), the pair
of wheels on their axle, and the load. The seed picks the load (square hay
bales, crates of vegetables or two round bales) and the trailer's colour.

    blender --background --factory-startup --python assets-src/props/trailer.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_fair import beam  # noqa: E402
from lib.shapes_props import apothem, panel_x, panel_z, prism  # noqa: E402

TYPE = "trailer"
KIND = "prop"
TRIANGLE_BUDGET = 150

LOADS = ("hay", "crates", "round")
COLOURS = ("tomato", "cobalt", "leaf", "tangerine")
HX = 1.15
Y0, Y1 = -1.5, 2.1
BED = 1.0  # top of the bed
WHEEL_R = 0.6


def build(building_id, seed, scheme=None, collection=None):
    """Build one trailer. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    load = LOADS[seed % len(LOADS)]  # cycled, so neighbouring seeds always differ
    colour = rng.choice(COLOURS)
    strap = rng.choice(["tangerine", "doorBrown"])
    produce = rng.sample(["tangerine", "leaf", "tomato", "sunny"], 3)

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    # The bed, its end boards and the drawbar.
    kit = Kit()
    kit.box((-HX, Y0, BED - 0.25), (HX, Y1, BED), colour, sides={"+z": "wood"})
    for ya, yb in ((Y0, Y0 + 0.14), (Y1 - 0.14, Y1)):
        kit.box((-HX, ya, BED), (HX, yb, BED + 0.55), colour, skip=("-z",))
    beam(kit, (0, Y0, BED - 0.15), (0, Y0 - 1.2, 0.62), 0.24, "tyre", depth=0.2)
    kit.box((-0.09, Y0 - 1.25, 0), (0.09, Y0 - 1.07, 0.6), "tyre", skip=("-z", "+z"))
    bed = building.add(kit, "detail", "wood", 0, collider="hull")

    # Both wheels and their axle.
    z = apothem(WHEEL_R, 6)
    kit = Kit()
    kit.box((-HX, 0.55, z - 0.1), (HX, 0.75, BED - 0.25), "tyre", skip=("-x", "+x", "+z"))
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (HX + 0.02), sx * (HX + 0.42)))
        prism(kit, (0.65, z), x0, x1, WHEEL_R, WHEEL_R, 6, "tyre", axis="x", bottom=sx < 0, top=sx > 0)
        panel_x(kit, 0.4, 0.9, z - 0.25, z + 0.25, sx * (HX + 0.44), sx, "trimWhite")
    building.add(kit, "detail", "rubber", 0, collider="hull")

    # The load.
    kit = Kit()
    ya, yb = Y0 + 0.2, Y1 - 0.2
    if load == "hay":
        mid = (ya + yb) / 2
        for y_lo, y_hi, z0 in ((ya, mid - 0.03, BED), (mid + 0.03, yb, BED), (ya + 0.8, yb - 0.8, BED + 0.8)):
            kit.box((-HX + 0.1, y_lo, z0), (HX - 0.1, y_hi, z0 + 0.8), "sunny", skip=("-z",))
            for sx in (-1, 1):
                x0, x1 = sorted((sx * 0.35, sx * 0.5))
                panel_z(kit, x0, x1, y_lo, y_hi, z0 + 0.82, 1, strap)
    elif load == "crates":
        spots = [(-0.55, ya + 0.55), (0.55, ya + 0.6), (-0.5, yb - 0.6), (0.55, yb - 0.55)]
        for (cx, cy), fill in zip(spots[: 3 if rng.random() < 0.5 else 4], produce + produce[:1]):
            kit.box((cx - 0.5, cy - 0.5, BED), (cx + 0.5, cy + 0.5, BED + 0.7), "wood", skip=("-z",), sides={"+z": fill})
        kit.box((-0.5, -0.2, BED), (0.5, 0.8, BED + 1.0), produce[2], skip=("-z",))  # a heap in the middle
    else:
        r = 0.9
        zc = BED + apothem(r, 8)
        for cy in (ya + 0.85, yb - 0.85):
            prism(kit, (cy, zc), -HX + 0.1, HX - 0.1, r, r, 8, "sunny", axis="x", bottom_colour="wood", top_colour="wood")
    building.add(kit, "detail", "leaves", 0, supports=(bed,), collider="hull" if load == "round" else "box")

    return building.finish(look=f"{load} {colour}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(7, 8))


if __name__ == "__main__":
    previews()
