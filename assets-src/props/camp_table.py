"""Camp table generator.

A log table with a lantern on it and one or two log benches: two or three
modules (the table and lantern, and each bench). The seed varies the table's
length, the number of benches and how they sit, the wood and the lantern.

    blender --background --factory-startup --python assets-src/props/camp_table.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_castle2 import pyramid  # noqa: E402
from lib.shapes_forest import log  # noqa: E402

TYPE = "camp_table"
KIND = "prop"
TRIANGLE_BUDGET = 150
SPACING = 6


def build(building_id, seed, scheme=None, collection=None):
    """Build one camp table. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    benches = 2 - seed % 2  # cycled, so neighbouring seeds differ
    length = rng.choice([2.4, 2.8, 3.2])
    dark = rng.choice([True, False])
    lantern = rng.choice(["tomato", "cobalt", "tyre"])
    glow = rng.choice(["sunny", "sunny", "windowShine"])
    lantern_x = rng.choice([-0.5, 0.0, 0.5]) * length / 2
    skew = rng.choice([-0.25, 0.0, 0.25])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)
    bark, pale = ("doorBrown", "wood") if dark else ("wood", "doorBrown")
    half = length / 2

    kit = Kit()
    for x in (-half + 0.55, half - 0.55):
        log(kit, "z", 0, 0.85, (x, 0), 0.3, bark, sides=6, caps=(False, False))
    kit.box((-half, -0.6, 0.85), (half, 0.6, 1.05), pale, sides={"+z": "interiorCream"})
    z = 1.05
    kit.box((lantern_x - 0.2, -0.2, z), (lantern_x + 0.2, 0.2, z + 0.08), lantern, skip=("-z",))
    kit.box((lantern_x - 0.15, -0.15, z + 0.08), (lantern_x + 0.15, 0.15, z + 0.48), glow, skip=("-z", "+z"))
    pyramid(kit, lantern_x, 0, 0.23, 0.23, z + 0.48, 0.24, lantern)
    building.add(kit, "detail", "wood", 0)

    for n in range(benches):
        sign = -1 if n == 0 else 1
        y = sign * 1.25
        x = skew * sign
        kit = Kit()
        log(kit, "x", x - half * 0.92, x + half * 0.92, (y, 0.47), 0.2, bark, end="interiorCream", sides=6)
        for fx in (-half * 0.6, half * 0.6):
            kit.box((x + fx - 0.14, y - 0.22, 0), (x + fx + 0.14, y + 0.22, 0.3), pale, skip=("-z", "+z"))
        building.add(kit, "detail", "wood", 0, collider="box")

    return building.finish(look=f"len={length} benches={benches} {bark} lantern={lantern}/{glow}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
