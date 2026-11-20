"""Milk churns generator.

A little cluster of three tin milk churns in one module, each about 1.6 m
tall: a drum, a sloping shoulder and a wide bright lid. The seed varies how they are
grouped, their heights, the lid colour and whether one churn is painted.

    blender --background --factory-startup --python assets-src/props/milk_churns.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import prism  # noqa: E402

TYPE = "milk_churns"
KIND = "prop"
TRIANGLE_BUDGET = 150  # one module, so really 80

GROUPS = ("triangle", "row", "pair-and-one")
LIDS = ("cobalt", "tomato", "trimWhite", "sunny")
SIDES = 5


def build(building_id, seed, scheme=None, collection=None):
    """Build three churns. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    group = GROUPS[seed % len(GROUPS)]  # cycled, so neighbouring seeds always differ
    lid = LIDS[seed % len(LIDS)]
    painted = rng.choice([None, None, "cobalt", "tomato"])
    radius = 0.5

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    d = radius * 1.05
    if group == "triangle":
        spots = [(-d, -0.45), (d, -0.45), (0.0, 0.55 + d * 0.3)]
    elif group == "row":
        spots = [(-2.1 * d, 0.1), (0.0, -0.1), (2.1 * d, 0.1)]
    else:
        spots = [(-1.6 * d, 0.2), (0.45 * d, 0.2), (2.0 * d, -0.9)]

    kit = Kit()
    for index, (x, y) in enumerate(spots):
        h = 1.55 * rng.choice([0.9, 1.0, 1.1])
        body = painted if painted and index == 2 and painted != lid else "stone"
        turn = rng.uniform(0, 2 * math.pi / SIDES)
        prism(kit, (x, y), 0, h * 0.6, radius, radius, SIDES, body, bottom=False, top=False, phase=turn)
        prism(kit, (x, y), h * 0.6, h, radius, radius * 0.5, SIDES, body, bottom=False, top=False, phase=turn)
        # The lid: a wide flat disc on the neck (both faces; all one module can afford).
        step = 2 * math.pi / SIDES
        disc = [(x + radius * 0.82 * math.cos(turn + k * step), y + radius * 0.82 * math.sin(turn + k * step), h) for k in range(SIDES)]
        kit.poly(disc, (0, 0, 1), lid)
        kit.poly(disc, (0, 0, -1), lid)
    building.add(kit, "detail", "tin", 0, collider="hull")

    return building.finish(look=f"{group} lid={lid} painted={painted}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(5, 5))


if __name__ == "__main__":
    previews()
