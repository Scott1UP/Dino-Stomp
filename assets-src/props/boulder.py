"""Boulder generator.

A chunky faceted rock, 2.5-4 m across, in one module. The seed varies its
size and shape (squat, tall or long), how craggy it is, a mossy top, and a
smaller rock leaning against it.

    blender --background --factory-startup --python assets-src/props/boulder.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_forest import rock  # noqa: E402

TYPE = "boulder"
KIND = "prop"
TRIANGLE_BUDGET = 150
SPACING = 7

SHAPES = {"squat": (1.7, 1.5, 1.5), "tall": (1.35, 1.3, 2.4), "long": (2.0, 1.3, 1.6)}  # half widths and height


def build(building_id, seed, scheme=None, collection=None):
    """Build one boulder. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    shape = ("squat", "tall", "long")[seed % 3]  # cycled, so neighbouring seeds differ
    size = rng.choice([0.85, 1.0, 1.1])
    segments = rng.choice([6, 7])
    moss = rng.choice([None, None, "hedge", "leaf"])
    pebble = rng.choice([True, False])
    turn = rng.uniform(0, math.tau)

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    sx, sy, sz = (v * size for v in SHAPES[shape])
    kit = Kit()
    rock(kit, (0, 0), (sx, sy, sz), rng, "stone", segments=segments, cap=moss)
    if pebble:
        reach = 0.95
        rock(kit, (math.cos(turn) * sx * reach, math.sin(turn) * sy * reach), (sx * 0.45, sy * 0.45, sz * 0.4), rng, "stone", segments=5)
    building.add(kit, "detail", "stone", 0, collider="hull")

    return building.finish(look=f"{shape} x{size} seg={segments} moss={moss} pebble={int(pebble)}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
