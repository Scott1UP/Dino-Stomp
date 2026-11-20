"""Bird house generator.

A tall pole, 4-5 m, with a bright little bird house on top: a pitched roof, a
round dark doorway and a perch (no birds), in one module. The seed varies the
pole's height and colour, the house (a cube, a tall one, or a wide one with
two doors), its colours, and which way it faces.

    blender --background --factory-startup --python assets-src/props/bird_house.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import flat, polygon  # noqa: E402
from lib.shapes_forest import log  # noqa: E402
from lib.shapes_props import BRIGHT  # noqa: E402

TYPE = "bird_house"
KIND = "prop"
TRIANGLE_BUDGET = 150
SPACING = 5

HOUSES = {"cube": (1.0, 0.95, (0.0,)), "tall": (0.85, 1.35, (0.0,)), "wide": (1.5, 0.9, (-0.36, 0.36))}  # width, height, doors


def build(building_id, seed, scheme=None, collection=None):
    """Build one bird house. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    house = ("cube", "tall", "wide")[seed % 3]  # cycled, so neighbouring seeds differ
    pole_h = rng.choice([3.4, 3.8, 4.2])
    pole = rng.choice(["wood", "doorBrown", "trimWhite"])
    wall = rng.choice(BRIGHT)
    roof = rng.choice([c for c in BRIGHT if c != wall])
    pitch = rng.choice([0.7, 0.95])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)
    width, height, doors = HOUSES[house]
    depth = 0.9
    w, d = width / 2, depth / 2

    kit = Kit()
    log(kit, "z", 0, pole_h, (0, 0), 0.13, pole, sides=6, caps=(False, False))
    kit.box((-w - 0.15, -d - 0.3, pole_h), (w + 0.15, d + 0.1, pole_h + 0.1), "wood")
    z0 = pole_h + 0.1
    z1 = z0 + height
    kit.box((-w, -d, z0), (w, d, z1), wall, skip=("-z", "+z"))
    rise = (w + 0.2) * pitch
    kit.extrude_y([(-w - 0.2, z1), (w + 0.2, z1), (0, z1 + rise)], -d - 0.2, d + 0.2, roof, colours={0: wall, 1: wall})
    for x in doors:
        hole = min(0.24, width * 0.2)
        flat(kit, (x, -d, z0 + height * 0.56), (0, -1, 0), polygon(hole, 8), "tyre", lift=0.02)
        kit.box((x - 0.05, -d - 0.26, z0 + height * 0.56 - hole - 0.14), (x + 0.05, -d, z0 + height * 0.56 - hole - 0.05), "trimWhite", skip=("+y",))
    building.add(kit, "detail", "wood", 0, collider="box")

    return building.finish(look=f"{house} pole={pole_h}/{pole} {wall}+{roof} pitch={pitch}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
