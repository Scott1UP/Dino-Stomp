"""Giant domino generator.

One giant domino: a single box 3.6 m wide (X), 0.9 m thick (Y) and 7.2 m tall
(Z), standing on its end with its origin at the centre of its base. White pips
and a dividing line are flat shapes on the front and back faces. The seed
picks the colour and the two numbers.

    blender --background --factory-startup --python assets-src/props/domino.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import BRIGHT, panel_y  # noqa: E402

TYPE = "domino"
KIND = "domino"
TRIANGLE_BUDGET = 150

WIDTH = 3.6
THICK = 0.9
HEIGHT = 7.2
PROUD = 0.02  # pips sit this far off the face, so they never flicker against it
PIP_RADIUS = 0.4
PIP_SIDES = 6
GRID = 1.02

# Pip positions on a 3 x 3 grid, as on a real domino.
PIPS = {
    1: [(0, 0)],
    2: [(-1, 1), (1, -1)],
    3: [(-1, 1), (0, 0), (1, -1)],
    4: [(-1, 1), (1, 1), (-1, -1), (1, -1)],
    5: [(-1, 1), (1, 1), (0, 0), (-1, -1), (1, -1)],
    6: [(-1, 1), (1, 1), (-1, 0), (1, 0), (-1, -1), (1, -1)],
}
# Number pairs, at most 8 pips a face to stay inside the triangle budget.
PAIRS = [(a, b) for a in range(1, 7) for b in range(1, 7) if a + b <= 8]


def _pip(kit, x, z, y, facing):
    """A flat six-sided pip in the XZ plane."""
    step = 2 * math.pi / PIP_SIDES
    points = [(x + PIP_RADIUS * math.cos(i * step), y, z + PIP_RADIUS * math.sin(i * step)) for i in range(PIP_SIDES)]
    kit.poly(points, (0, facing, 0), "trimWhite")


def build(building_id, seed, scheme=None, collection=None):
    """Build one domino. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    colour = rng.choice(BRIGHT)
    upper, lower = rng.choice(PAIRS)

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    kit.box((-WIDTH / 2, -THICK / 2, 0), (WIDTH / 2, THICK / 2, HEIGHT), colour)
    for facing in (-1, 1):
        y = facing * (THICK / 2 + PROUD)
        panel_y(kit, -WIDTH / 2 + 0.38, WIDTH / 2 - 0.38, HEIGHT / 2 - 0.1, HEIGHT / 2 + 0.1, y, facing, "trimWhite")
        for count, centre_z in ((upper, HEIGHT * 0.75), (lower, HEIGHT * 0.25)):
            for gx, gz in PIPS[count]:
                # Mirror the back face, so both sides read the same way round.
                _pip(kit, gx * GRID * -facing, centre_z + gz * GRID, y, facing)
    building.add(kit, "detail", "wood", 0)

    return building.finish(look=f"{colour} {upper}|{lower}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 8))


if __name__ == "__main__":
    previews()
