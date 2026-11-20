"""Toy tractor generator.

A chunky toy tractor about 4.5 m long with its nose towards -Y: a long bonnet
with a grille and an upright exhaust, big rear wheels under mudguards and
small front ones. Six modules: the body, the driver's end resting on it, and
four wheels that can pop off.
The seed picks the colour (tomato, cobalt, sunny or leaf) and the driver's
end: a glazed cab, a canopy on four posts, or an open seat with a roll bar.

    blender --background --factory-startup --python assets-src/props/tractor.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import apothem, panel_x, panel_y, prism  # noqa: E402

TYPE = "tractor"
KIND = "prop"
TRIANGLE_BUDGET = 200

COLOURS = ("tomato", "leaf", "cobalt", "sunny")
STYLES = ("cab", "open", "canopy")
GLASS = "windowBlue"
NOSE, TAIL = -2.3, 2.2
REAR_R, FRONT_R = 1.0, 0.55


def build(building_id, seed, scheme=None, collection=None):
    """Build one tractor. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    style = STYLES[seed % len(STYLES)]  # cycled, so neighbouring seeds always differ
    colour = COLOURS[(seed // 2 + seed) % len(COLOURS)]
    hub = "trimWhite" if colour in ("sunny", "tomato") and rng.random() < 0.6 else ("tomato" if colour == "sunny" else "sunny")
    exhaust_x = rng.choice([-0.3, 0.3])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    # Bonnet, with a grille and headlights on the nose.
    kit.box((-0.55, NOSE, 0.75), (0.55, 0.2, 1.8), colour, skip=("+y",))
    panel_y(kit, -0.46, 0.46, 0.9, 1.65, NOSE - 0.02, -1, "tyre")
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.12, sx * 0.46))
        panel_y(kit, x0, x1, 1.28, 1.58, NOSE - 0.04, -1, "sunny")
    # Exhaust stack.
    kit.box((exhaust_x - 0.11, -1.5, 1.8), (exhaust_x + 0.11, -1.28, 2.95), "tyre", skip=("-z",))
    # Back end, and a mudguard over each rear wheel.
    kit.box((-0.75, 0.2, 0.7), (0.75, TAIL, 1.55), colour, skip=("-y",))
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.75, sx * 1.32))
        kit.box((x0, 0.15, 1.98), (x1, TAIL, 2.14), colour, skip=("+x" if sx < 0 else "-x",))
    body = building.add(kit, "detail", "tin", 0)

    # The driver's end: its own module, resting on the body.
    kit = Kit()
    if style == "cab":
        kit.extrude_x([(0.2, 1.55), (2.1, 1.55), (1.95, 3.0), (0.5, 3.0)], -0.75, 0.75, colour, {0: GLASS, 1: GLASS, 3: GLASS, 5: GLASS})
        kit.box((-0.86, 0.35, 3.0), (0.86, 2.1, 3.18), "trimWhite")
    else:
        kit.box((-0.5, 1.0, 1.55), (0.5, 1.9, 2.35), "tyre", skip=("-z",))  # seat
        post = "tyre" if style == "canopy" else "trimWhite"
        for sx in (-1, 1):
            x0, x1 = sorted((sx * 0.75, sx * 0.57))
            kit.box((x0, 1.92, 1.55), (x1, 2.1, 3.0), post, skip=("-z", "+z"))
        if style == "canopy":
            kit.box((-0.9, 0.3, 3.0), (0.9, 2.2, 3.18), "trimWhite")
        else:
            kit.box((-0.75, 1.92, 3.0), (0.75, 2.1, 3.18), "trimWhite", skip=("-z",))  # roll bar
    building.add(kit, "detail", "tin", 0, supports=(body,))

    # Wheels: flat on the ground, with a bright hub on the outside.
    for wheel_y, radius, sides, x_in, x_out in ((1.15, REAR_R, 8, 0.76, 1.3), (-1.55, FRONT_R, 6, 0.6, 0.98)):
        z = apothem(radius, sides)
        for sx in (-1, 1):
            x0, x1 = sorted((sx * x_in, sx * x_out))
            kit = Kit()
            prism(kit, (wheel_y, z), x0, x1, radius, radius, sides, "tyre", axis="x")
            h = radius * 0.45
            panel_x(kit, wheel_y - h, wheel_y + h, z - h, z + h, sx * (x_out + 0.02), sx, hub)
            building.add(kit, "detail", "rubber", 0, supports=(body,), collider="hull")

    return building.finish(look=f"{style} {colour} hubs={hub}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(7, 8))


if __name__ == "__main__":
    previews()
