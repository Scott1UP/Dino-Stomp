"""Double-decker bus generator.

A tomato double-decker about 9 m long, 2.6 m wide and 4.4 m tall. It runs
along Y with its nose towards -Y. One module, wheels included, so it tumbles
and rolls whole. Windows are flat quads. The seed varies the trim.

    blender --background --factory-startup --python assets-src/props/bus.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import apothem, panel_x, panel_y, prism  # noqa: E402

TYPE = "bus"
KIND = "prop"
TRIANGLE_BUDGET = 150

HALF_LENGTH = 4.5
HALF_WIDTH = 1.3
FLOOR = 0.5
HEIGHT = 4.4
LOWER = (1.25, 2.2)  # window heights, lower deck
UPPER = (2.85, 3.75)  # and upper deck
BAYS = 4
WHEEL_RADIUS = 0.62
WHEEL_SIDES = 6
GLASS = "windowBlue"


def build(building_id, seed, scheme=None, collection=None):
    """Build one bus. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    band = rng.choice(["trimWhite", "trimWhite", "sunny"])
    board = "sunny" if band == "trimWhite" else "trimWhite"
    roof = rng.choice(["tomato", "tomato", "trimWhite"])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    kit.box((-HALF_WIDTH, -HALF_LENGTH, FLOOR), (HALF_WIDTH, HALF_LENGTH, HEIGHT), "tomato", sides={"+z": roof})

    bay = (HALF_LENGTH * 2 - 0.6) / BAYS
    for facing in (-1, 1):
        x = facing * (HALF_WIDTH + 0.02)
        for index in range(BAYS):
            y0 = -HALF_LENGTH + 0.3 + index * bay + 0.2
            y1 = y0 + bay - 0.4
            panel_x(kit, y0, y1, UPPER[0], UPPER[1], x, facing, GLASS)
            if facing == 1 and index == 0:
                # The door, on the kerb side by the driver.
                panel_x(kit, y0, y0 + 1.1, FLOOR + 0.1, LOWER[1], x, facing, GLASS)
            else:
                panel_x(kit, y0, y1, LOWER[0], LOWER[1], x, facing, GLASS)
        # A band between the decks.
        panel_x(kit, -HALF_LENGTH, HALF_LENGTH, 2.38, 2.66, x, facing, band)

    front = -HALF_LENGTH - 0.02
    back = HALF_LENGTH + 0.02
    side = HALF_WIDTH - 0.2
    panel_y(kit, -side, side, LOWER[0], LOWER[1] + 0.05, front, -1, GLASS)
    panel_y(kit, -side, side, UPPER[0], UPPER[1], front, -1, GLASS)
    panel_y(kit, -0.8, 0.8, 2.36, 2.7, front, -1, board)
    panel_y(kit, -side, side, UPPER[0], UPPER[1], back, 1, GLASS)
    panel_y(kit, -side, side, LOWER[0], LOWER[1], back, 1, GLASS)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * 0.6, sx * 1.05))
        panel_y(kit, x0, x1, 0.7, 1.0, front, -1, "sunny")

    wheel_z = apothem(WHEEL_RADIUS, WHEEL_SIDES)
    for wheel_y in (-2.9, 2.7):
        for sx in (-1, 1):
            x0, x1 = sorted((sx * 0.8, sx * (HALF_WIDTH + 0.04)))
            prism(kit, (wheel_y, wheel_z), x0, x1, WHEEL_RADIUS, WHEEL_RADIUS, WHEEL_SIDES, "tyre", axis="x")

    building.add(kit, "detail", "tin", 0)

    return building.finish(look=f"band={band} roof={roof}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(9, 14))


if __name__ == "__main__":
    previews()
