"""Ice cream van generator.

A chunky van about 4.6 m long with a serving hatch and a striped awning on
one side, and a giant ice cream cone on the roof. It runs along Y with its
nose towards -Y. The van body is one module, the cone on the roof breaks off
on its own, and the four wheels pop off as they do on the car. The seed picks the van's colour, the stripe, the
flavour of the scoop and its topping (a cherry or a flake), and which side
the hatch is on.

    blender --background --factory-startup --python assets-src/props/ice_cream_van.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import apothem, ball, panel_x, panel_y, prism  # noqa: E402

TYPE = "ice_cream_van"
KIND = "prop"
TRIANGLE_BUDGET = 200  # the cone on the roof earns it a few more than other props

HALF_LENGTH = 2.3
HALF_WIDTH = 1.0
FLOOR = 0.35
ROOF = 2.35
WHEEL_RADIUS = 0.48
WHEEL_SIDES = 6
GLASS = "windowBlue"
SPACING = (8, 8)


def build(building_id, seed, scheme=None, collection=None):
    """Build one ice cream van. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    body = ("bubblegum", "trimWhite", "glassTint", "sunny")[seed % 4]  # cycled, so neighbouring seeds always differ
    band = rng.choice([c for c in ("tomato", "cobalt", "bubblegum", "tangerine") if c != body])
    scoop = rng.choice([c for c in ("bubblegum", "trimWhite", "leaf", "sunny") if c != body])
    topping = rng.choice(["cherry", "flake"])
    hatch_side = rng.choice([-1, 1])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    # --- the van: floor, rear, roof, windscreen, nose ---
    kit = Kit()
    kit.extrude_x(
        [(-HALF_LENGTH, FLOOR), (HALF_LENGTH, FLOOR), (HALF_LENGTH, ROOF), (-1.45, ROOF), (-HALF_LENGTH, 1.25)],
        -HALF_WIDTH,
        HALF_WIDTH,
        body,
        {5: GLASS},
    )
    for facing in (-1, 1):
        x = facing * (HALF_WIDTH + 0.02)
        panel_x(kit, -HALF_LENGTH + 0.05, HALF_LENGTH - 0.05, 0.6, 0.95, x, facing, band)
        panel_x(kit, -1.45, -0.55, 1.3, 2.0, x, facing, GLASS)  # the cab window
        if facing == hatch_side:
            panel_x(kit, 0.0, 1.9, 1.2, 2.05, x, facing, GLASS)
            xa, xb = sorted((facing * HALF_WIDTH, facing * (HALF_WIDTH + 0.4)))
            kit.box((xa, -0.1, 1.05), (xb, 2.0, 1.2), "trimWhite", skip=("-x",) if facing > 0 else ("+x",))
            # The awning: four stripes sloping out over the counter.
            edge = facing * (HALF_WIDTH + 0.75)
            for i in range(4):
                ya, yb = -0.1 + i * 0.525, -0.1 + (i + 1) * 0.525
                quad = [(facing * HALF_WIDTH, ya, 2.25), (facing * HALF_WIDTH, yb, 2.25), (edge, yb, 1.95), (edge, ya, 1.95)]
                kit.poly(quad, (facing * 0.4, 0, 1), band if i % 2 == 0 else "trimWhite")
                kit.poly(quad, (-facing * 0.4, 0, -1), band if i % 2 == 0 else "trimWhite")
    panel_y(kit, -0.6, 0.6, 1.35, 1.95, HALF_LENGTH + 0.02, 1, GLASS)
    for sx in (-1, 1):
        xa, xb = sorted((sx * 0.4, sx * 0.82))
        panel_y(kit, xa, xb, 0.62, 0.9, -HALF_LENGTH - 0.02, -1, "sunny" if body != "sunny" else "trimWhite")
        panel_y(kit, xa, xb, 0.62, 0.9, HALF_LENGTH + 0.02, 1, "tomato")
    van = building.add(kit, "detail", "tin", 0)

    # Wheels: their own modules, as on the car, so they can pop off.
    wheel_z = apothem(WHEEL_RADIUS, WHEEL_SIDES)
    for wheel_y in (-1.4, 1.35):
        for sx in (-1, 1):
            xa, xb = sorted((sx * 0.75, sx * 1.1))
            kit = Kit()
            prism(kit, (wheel_y, wheel_z), xa, xb, WHEEL_RADIUS, WHEEL_RADIUS, WHEEL_SIDES, "tyre", axis="x")
            panel_x(kit, wheel_y - 0.17, wheel_y + 0.17, wheel_z - 0.17, wheel_z + 0.17, sx * 1.12, sx, "trimWhite")
            building.add(kit, "detail", "tin", 0, supports=(van,), collider="hull")

    # --- the giant cone on the roof ---
    cy = 0.75
    kit = Kit()
    prism(kit, (0, cy), ROOF - 0.05, ROOF + 1.45, 0.12, 0.72, 6, "wood", bottom=False, top=False)
    ball(kit, (0, cy, ROOF + 1.75), 0.85, 6, 3, scoop, squash=0.85)
    if topping == "cherry":
        ball(kit, (0, cy, ROOF + 2.6), 0.26, 4, 2, "tomato")
    else:
        kit.box((0.15, cy - 0.12, ROOF + 2.0), (0.4, cy + 0.12, ROOF + 2.95), "doorBrown", skip=("-z",))
    building.add(kit, "detail", "wood", 1, supports=(van,), collider="hull")

    return building.finish(look=f"{body} band={band} scoop={scoop} {topping} hatch{hatch_side:+d}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=SPACING)


if __name__ == "__main__":
    previews()
