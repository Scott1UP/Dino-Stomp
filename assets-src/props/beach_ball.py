"""Beach ball generator.

One faceted ball of radius 1.2 m in coloured wedges, resting on the ground
(its centre is at z = 1.2). One module with a hull collider. The seed picks
the wedge colours and tilts the ball, so no two sit the same way.

    blender --background --factory-startup --python assets-src/props/beach_ball.py
"""

import math
import os
import random
import sys

from mathutils import Euler

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import ball  # noqa: E402

TYPE = "beach_ball"
KIND = "ball"
TRIANGLE_BUDGET = 150

RADIUS = 1.2
SEGMENTS = 8
RINGS = 5
WEDGES = [
    ["tomato", "trimWhite", "sunny", "trimWhite", "cobalt", "trimWhite", "tangerine", "trimWhite"],
    ["tomato", "sunny", "cobalt", "trimWhite", "tomato", "sunny", "cobalt", "trimWhite"],
    ["bubblegum", "trimWhite", "cobalt", "trimWhite", "sunny", "trimWhite", "tomato", "trimWhite"],
    ["tomato", "trimWhite", "cobalt", "sunny", "tomato", "trimWhite", "cobalt", "sunny"],
]


def build(building_id, seed, scheme=None, collection=None):
    """Build one beach ball. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    wedges = rng.choice(WEDGES)
    tilt = Euler(
        (math.radians(rng.uniform(-50, 50)), math.radians(rng.uniform(-50, 50)), rng.uniform(0, math.tau))
    ).to_matrix()

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    ball(kit, (0, 0, RADIUS), RADIUS, SEGMENTS, RINGS, "trimWhite", lambda segment, ring: wedges[segment], matrix=tilt)
    building.add(kit, "detail", "rubber", 0, collider="hull")

    return building.finish(look="/".join(dict.fromkeys(wedges)))


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 8))


if __name__ == "__main__":
    previews()
