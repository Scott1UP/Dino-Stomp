"""Trail signpost generator.

A stout wooden post, 0.4 m thick and 3.5-4 m tall, with two or three bright
arrow boards pointing different ways (a pale stripe on each; no words), in one
module. The seed varies the height, the number of boards, where they point and
their colours.

    blender --background --factory-startup --python assets-src/props/signpost.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_forest import COS8, arrow_board, cone, log  # noqa: E402
from lib.shapes_props import BRIGHT  # noqa: E402

TYPE = "signpost"
KIND = "prop"
TRIANGLE_BUDGET = 80  # one module, so the module budget is the limit
SPACING = 5

POST = 0.2  # apothem: the post is 0.4 m thick


def build(building_id, seed, scheme=None, collection=None):
    """Build one signpost. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    boards = 2 + seed % 2  # cycled, so neighbouring seeds differ
    height = rng.choice([3.5, 3.8, 4.0])
    bark = rng.choice(["doorBrown", "doorBrown", "wood"])
    colours = list(BRIGHT)
    rng.shuffle(colours)
    first = rng.choice([0.0, math.pi])
    cap = rng.choice(["point", "cut"])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    log(kit, "z", 0, height, (0, 0), POST, bark, end="interiorCream", sides=6, caps=(False, cap == "cut"))
    if cap == "point":
        cone(kit, (0, 0, height), POST / COS8 + 0.06, (0, 0, height + 0.45), 6, bark)
    for n in range(boards):
        angle = first + n * math.pi + rng.choice([-0.5, -0.2, 0.2, 0.5])  # alternate sides, a little askew
        z = height - 0.5 - n * 0.72
        arrow_board(kit, (0, 0, z), angle, rng.choice([1.9, 2.1, 2.3]), 0.55, 0.14, colours[n], stripe="trimWhite")
    building.add(kit, "detail", "wood", 0, collider="box")

    return building.finish(look=f"h={height} boards={boards} {bark} {cap} {'/'.join(colours[:boards])}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
