"""Bench generator.

A park bench in three plank modules: a front seat plank and a rear seat plank,
each with its own pair of stubby legs, and a backrest plank on two uprights.
The seed varies the length and the plank colour.

    blender --background --factory-startup --python assets-src/props/bench.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "bench"
KIND = "prop"
TRIANGLE_BUDGET = 150

SEAT = 0.7  # top of the seat
PLANK = 0.2
LEG = 0.28


def build(building_id, seed, scheme=None, collection=None):
    """Build one bench. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    half = rng.choice([1.2, 1.4, 1.6])
    planks = rng.choice(["wood", "wood", "sunny", "tomato", "cobalt", "tangerine"])
    legs = "doorBrown"
    back_top = rng.choice([1.5, 1.65])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)
    leg_x = half - 0.45

    def seat_plank(y0, y1):
        kit = Kit()
        kit.box((-half, y0, SEAT - PLANK), (half, y1, SEAT), planks)
        mid = (y0 + y1) / 2
        for sx in (-1, 1):
            kit.box(
                (sx * leg_x - LEG / 2, mid - LEG / 2, 0),
                (sx * leg_x + LEG / 2, mid + LEG / 2, SEAT - PLANK),
                legs,
                skip=("+z",),
            )
        return building.add(kit, "detail", "wood", 0)

    seat_plank(-0.55, -0.06)
    rear = seat_plank(0.06, 0.55)

    # The backrest stands on the rear seat plank.
    kit = Kit()
    kit.box((-half, 0.4, back_top - 0.5), (half, 0.62, back_top), planks)
    for sx in (-1, 1):
        kit.box(
            (sx * leg_x - LEG / 2, 0.36, SEAT),
            (sx * leg_x + LEG / 2, 0.6, back_top - 0.5),
            legs,
            skip=("+z", "-z"),
        )
    building.add(kit, "detail", "wood", 0, supports=(rear,))

    return building.finish(look=f"len={half * 2} {planks}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 8))


if __name__ == "__main__":
    previews()
