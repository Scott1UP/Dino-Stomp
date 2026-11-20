"""Giant pumpkin generator: a loose pumpkin that rolls and tumbles.

One giant tangerine pumpkin about 1.6 m across with a leaf-green stalk, in a
single hull module. It sits on a flat base. The seed varies its width, how
squat or tall it is, how many ribs it has (6 or 8), and the stalk's lean.

    blender --background --factory-startup --python assets-src/props/pumpkin.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_fair import beam  # noqa: E402
from lib.shapes_props import prism  # noqa: E402

TYPE = "pumpkin"
KIND = "block"
TRIANGLE_BUDGET = 150  # one module, so really 80

SHAPES = ("squat", "round", "tall")


def build(building_id, seed, scheme=None, collection=None):
    """Build one pumpkin. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    shape = SHAPES[seed % len(SHAPES)]  # cycled, so neighbouring seeds always differ
    ribs = (8, 6)[(seed // 3) % 2]
    radius = rng.choice([0.76, 0.8, 0.86])
    height = radius * {"squat": 1.15, "round": 1.5, "tall": 1.85}[shape]
    lean = rng.choice([-0.22, 0.0, 0.22])
    turn = rng.uniform(0, math.pi)

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    profile = [(0.0, 0.55), (0.3, 1.0), (0.68, 1.0), (1.0, 0.42)]  # (height, radius) as fractions
    for (ha, ra), (hb, rb) in zip(profile, profile[1:]):
        prism(kit, (0, 0), ha * height, hb * height, ra * radius, rb * radius, ribs, "tangerine", bottom=ha == 0.0, top=hb == 1.0, phase=turn)
    beam(kit, (0, 0, height - 0.02), (lean, lean * 0.6, height + 0.42), 0.26, "hedge", end_colour="leaf")
    building.add(kit, "detail", "leaves", 0, collider="hull")

    return building.finish(look=f"{shape} ribs={ribs} r={radius} h={height:.2f}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(5, 5))


if __name__ == "__main__":
    previews()
