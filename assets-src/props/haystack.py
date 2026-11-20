"""Haystack generator.

A sunny yellow haystack, in one module. The seed picks the kind: a rounded
mound with a pole through it, a stack of strapped bales, or a tall stook tied
round the middle, and varies its size.

    blender --background --factory-startup --python assets-src/props/haystack.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import shapes_castle2 as castle  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import prism  # noqa: E402

TYPE = "haystack"
KIND = "prop"
TRIANGLE_BUDGET = 150
SPACING = 7

STYLES = ("mound", "bales", "stook")


def build(building_id, seed, scheme=None, collection=None):
    """Build one haystack. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    style = STYLES[seed % len(STYLES)]  # cycled, so neighbouring seeds differ
    size = rng.choice([0.9, 1.0, 1.12])
    strap = rng.choice(["tangerine", "doorBrown"])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    if style == "mound":
        r, h = 1.7 * size, 2.6 * size
        shapes.frustum(kit, r, r * 0.92, 0, h * 0.4, "sunny", bottom=False, top=False)
        shapes.frustum(kit, r * 0.92, r * 0.5, h * 0.4, h * 0.8, "sunny", bottom=False, top=False)
        shapes.frustum(kit, r * 0.5, 0, h * 0.8, h, "sunny", bottom=False)
        kit.box((-0.09, -0.09, h * 0.9), (0.09, 0.09, h + 0.7), "doorBrown", skip=("-z",))
    elif style == "bales":
        w, d, t = 1.9 * size, 1.1 * size, 0.9 * size
        spots = [(-w / 2 - 0.03, 0.0, 0.0), (w / 2 + 0.03, 0.05, 0.0), (0.1, 0.0, t)]
        if rng.random() < 0.5:
            spots.append((-w * 0.6, -d - 0.2, 0.0))
        for cx, cy, z in spots:
            kit.box((cx - w / 2, cy - d / 2, z), (cx + w / 2, cy + d / 2, z + t), "sunny", skip=("-z",))
            for x in (cx - w * 0.25, cx + w * 0.25):
                kit.poly([(x - 0.07, cy - d / 2 - 0.02, z), (x + 0.07, cy - d / 2 - 0.02, z), (x + 0.07, cy - d / 2 - 0.02, z + t), (x - 0.07, cy - d / 2 - 0.02, z + t)], (0, -1, 0), strap)
                kit.poly([(x - 0.07, cy - d / 2, z + t + 0.02), (x + 0.07, cy - d / 2, z + t + 0.02), (x + 0.07, cy + d / 2, z + t + 0.02), (x - 0.07, cy + d / 2, z + t + 0.02)], (0, 0, 1), strap)
    else:
        r, h = 1.25 * size, 3.4 * size
        shapes.frustum(kit, r, r * 0.42, 0, h * 0.72, "sunny", bottom=False, top=False)
        shapes.frustum(kit, r * 0.47, r * 0.47, h * 0.66, h * 0.74, strap, bottom=False, top=False)
        shapes.frustum(kit, r * 0.42, r * 0.75, h * 0.72, h, "sunny", bottom=False)
    building.add(kit, "detail", "leaves", 0, collider="hull")

    return building.finish(look=f"{style} size={size} strap={strap}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
