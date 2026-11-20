"""Parked toy car generator.

A chunky toy car about 4 m long, 1.9 m wide and 1.5 m tall. It runs along Y
with its nose towards -Y. Five modules: the body (windows and lights
included), and four wheels that can pop off it. The seed picks a bright colour
and a body style: hatchback, van or pickup.

    blender --background --factory-startup --python assets-src/props/car.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import BRIGHT, apothem, panel_x, panel_y, prism  # noqa: E402

TYPE = "car"
KIND = "prop"
TRIANGLE_BUDGET = 150

HALF_LENGTH = 2.0
HALF_WIDTH = 0.85  # the body; the wheels stand a little proud of it
FLOOR = 0.3
WAIST = 1.0
WHEEL_RADIUS = 0.46
WHEEL_SIDES = 6
GLASS = "windowBlue"
STYLES = ("hatchback", "van", "pickup")


def build(building_id, seed, scheme=None, collection=None):
    """Build one car. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    style = STYLES[seed % len(STYLES)]  # cycled, so neighbouring seeds always differ
    colour = rng.choice(BRIGHT)
    headlight = "trimWhite" if colour == "sunny" else "sunny"
    taillight = "trimWhite" if colour == "tomato" else "tomato"

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    # Cabin sections are (y, z), in the order: floor, rear, roof, windscreen.
    all_glass = {0: GLASS, 1: GLASS, 3: GLASS, 5: GLASS}
    if style == "hatchback":
        kit.box((-HALF_WIDTH, -HALF_LENGTH, FLOOR), (HALF_WIDTH, HALF_LENGTH, WAIST), colour)
        kit.extrude_x(
            [(-0.7, WAIST), (1.9, WAIST), (1.5, 1.55), (-0.1, 1.55)], -HALF_WIDTH, HALF_WIDTH, colour, all_glass
        )
        kit.box((-HALF_WIDTH - 0.03, -0.25, 1.55), (HALF_WIDTH + 0.03, 1.65, 1.68), colour)
    elif style == "van":
        # One tall body with a sloping windscreen: floor, rear, roof, windscreen, nose.
        kit.extrude_x(
            [(-HALF_LENGTH, FLOOR), (HALF_LENGTH, FLOOR), (HALF_LENGTH, 1.9), (-1.2, 1.9), (-HALF_LENGTH, 1.1)],
            -HALF_WIDTH,
            HALF_WIDTH,
            colour,
            {5: GLASS},
        )
        for facing in (-1, 1):
            x = facing * (HALF_WIDTH + 0.02)
            panel_x(kit, -1.15, -0.25, 1.15, 1.7, x, facing, GLASS)
            panel_x(kit, 0.05, 1.8, 0.75, 1.05, x, facing, "trimWhite")
        panel_y(kit, -0.6, 0.6, 1.15, 1.7, HALF_LENGTH + 0.02, 1, GLASS)
    else:
        kit.box((-HALF_WIDTH, -HALF_LENGTH, FLOOR), (HALF_WIDTH, HALF_LENGTH, WAIST), colour)
        kit.extrude_x(
            [(-0.9, WAIST), (0.45, WAIST), (0.35, 1.6), (-0.4, 1.6)], -HALF_WIDTH, HALF_WIDTH, colour, all_glass
        )
        # The open load bed: two side rails and a tailgate.
        for sx in (-1, 1):
            x0, x1 = sorted((sx * HALF_WIDTH, sx * (HALF_WIDTH - 0.22)))
            kit.box((x0, 0.45, WAIST), (x1, HALF_LENGTH, WAIST + 0.32), colour, skip=("-z",))
        kit.box(
            (-HALF_WIDTH + 0.22, HALF_LENGTH - 0.22, WAIST),
            (HALF_WIDTH - 0.22, HALF_LENGTH, WAIST + 0.32),
            colour,
            skip=("-z", "-x", "+x"),
        )
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.3, sx * 0.72))
        panel_y(kit, x0, x1, 0.6, 0.86, -HALF_LENGTH - 0.02, -1, headlight)
        panel_y(kit, x0, x1, 0.6, 0.86, HALF_LENGTH + 0.02, 1, taillight)
    body = building.add(kit, "detail", "tin", 0)

    # Wheels: flat on the ground, with a white hub on the outside.
    wheel_z = apothem(WHEEL_RADIUS, WHEEL_SIDES)
    for wheel_y in (-1.25, 1.25):
        for sx in (-1, 1):
            x0, x1 = sorted((sx * 0.6, sx * 0.97))
            kit = Kit()
            prism(kit, (wheel_y, wheel_z), x0, x1, WHEEL_RADIUS, WHEEL_RADIUS, WHEEL_SIDES, "tyre", axis="x")
            panel_x(kit, wheel_y - 0.16, wheel_y + 0.16, wheel_z - 0.16, wheel_z + 0.16, sx * 0.99, sx, "trimWhite")
            building.add(kit, "detail", "tin", 0, supports=(body,), collider="hull")

    return building.finish(look=f"{style} {colour}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 8))


if __name__ == "__main__":
    previews()
