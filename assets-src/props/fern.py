"""Fern generator.

A low clump of arching fronds about 2.5 m across, in one module and under 60
triangles. The seed varies the number of fronds, the clump's size and height,
and which green is on top.

    blender --background --factory-startup --python assets-src/props/fern.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
TYPE = "fern"
KIND = "prop"
TRIANGLE_BUDGET = 60
SPACING = 4


def _frond(kit, angle, reach, rise, droop, width, top, under):
    """A blade arching up and out from the middle, then drooping to a point: two triangles a side."""
    d = (math.cos(angle), math.sin(angle))
    t = (-d[1], d[0])
    base = (d[0] * 0.08, d[1] * 0.08, 0.05)
    bend = reach * 0.62
    left = (d[0] * bend + t[0] * width, d[1] * bend + t[1] * width, rise * 0.92)
    right = (d[0] * bend - t[0] * width, d[1] * bend - t[1] * width, rise * 0.92)
    ridge = (d[0] * bend, d[1] * bend, rise * 1.08)  # a crease down the middle keeps the blade from being flat
    tip = (d[0] * reach, d[1] * reach, droop)
    up = (d[0] * 0.3, d[1] * 0.3, 1)
    down = (-d[0] * 0.3, -d[1] * 0.3, -1)
    kit.poly([base, left, ridge], up, top)
    kit.poly([base, ridge, right], up, top)
    kit.poly([left, tip, ridge], up, top)
    kit.poly([ridge, tip, right], up, top)
    kit.poly([base, left, right], down, under)
    kit.poly([left, tip, right], down, under)


def build(building_id, seed, scheme=None, collection=None):
    """Build one fern. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    outer = 5 + seed % 2  # cycled, so neighbouring seeds differ
    inner = 3
    size = rng.choice([0.9, 1.0, 1.1])
    swap = rng.choice([True, False])
    turn = rng.uniform(0, math.tau)

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)
    top, under = ("hedge", "leaf") if swap else ("leaf", "hedge")

    kit = Kit()
    for n in range(outer):
        a = turn + n * math.tau / outer + rng.uniform(-0.15, 0.15)
        _frond(kit, a, 1.3 * size * rng.choice([0.9, 1.0, 1.05]), 0.8 * size, 0.18, 0.4 * size, top, under)
    for n in range(inner):
        a = turn + 0.5 + n * math.tau / inner
        _frond(kit, a, 0.65 * size, 1.25 * size, 0.95 * size, 0.3 * size, under, top)
    building.add(kit, "detail", "leaves", 0, collider="hull")

    return building.finish(look=f"fronds={outer}+{inner} x{size} top={top}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
