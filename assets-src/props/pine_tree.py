"""Pine tree generator.

A tall toy conifer, 8-13 m: a trunk, and two or three stacked cone tiers that
rest on it as one piece. Cheap on purpose (about 50 triangles), because the
forest is full of them. The seed varies the height, the number of tiers, the
greens and which way the tree leans.

    blender --background --factory-startup --python assets-src/props/pine_tree.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_forest import cone  # noqa: E402
from lib.shapes_props import prism  # noqa: E402

TYPE = "pine_tree"
KIND = "prop"
TRIANGLE_BUDGET = 70  # the level uses a lot of these
SPACING = 9

GREENS = (("hedge", "hedge", "hedge"), ("hedge", "hedge", "leaf"), ("hedge", "leaf", "hedge"), ("leaf", "hedge", "leaf"))


def build(building_id, seed, scheme=None, collection=None):
    """Build one pine tree. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    tiers = 2 + seed % 2  # cycled, so neighbouring seeds differ
    height = rng.choice([8.0, 9.0, 10.0, 11.0, 12.0, 13.0])
    greens = GREENS[rng.randrange(len(GREENS))]
    lean = (rng.uniform(-0.7, 0.7), rng.uniform(-0.7, 0.7))  # how far the tip is off the plumb line
    girth = rng.choice([0.26, 0.29, 0.32]) * height  # radius of the bottom tier
    bark = rng.choice(["doorBrown", "doorBrown", "wood"])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    trunk_h = height * 0.2

    def middle(z):
        f = z / height
        return (lean[0] * f * f, lean[1] * f * f)

    kit = Kit()
    prism(kit, (0, 0), 0, trunk_h + 0.5, 0.55, 0.42, 5, bark, bottom=False, top=False)
    trunk = building.add(kit, "detail", "wood", 0, collider="hull")

    foliage = height - trunk_h
    tier_h = foliage / (0.55 * (tiers - 1) + 1)
    kit = Kit()
    for k in range(tiers):
        z0 = trunk_h + k * tier_h * 0.55
        z1 = z0 + tier_h
        (bx, by), (ax, ay) = middle(z0), middle(z1)
        cone(kit, (bx, by, z0), girth * (1 - 0.27 * k), (ax, ay, z1), 8, greens[k], under="hedge")
    building.add(kit, "detail", "leaves", 0, supports=(trunk,), collider="hull")

    return building.finish(look=f"h={height:g} tiers={tiers} girth={girth:.1f} {'/'.join(greens[:tiers])}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
