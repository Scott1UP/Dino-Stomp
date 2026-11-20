"""Training dummy generator.

A straw dummy for sword practice, about 3 m tall: a post on crossed feet, and
on it a fat straw body with a target painted on its chest, a sack head (with
or without a pointed helmet), a cross-arm and a little round shield. Two
modules: the post, and the dummy resting on it. The seed varies the size, the
shield (side and colours), the helmet and the target.

    blender --background --factory-startup --python assets-src/props/training_dummy.py
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

TYPE = "training_dummy"
KIND = "prop"
TRIANGLE_BUDGET = 150
SPACING = 6


def build(building_id, seed, scheme=None, collection=None):
    """Build one training dummy. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    size = rng.choice([0.92, 1.0, 1.08])
    shield_colour = castle.BRIGHTS[seed % 3]  # cycled, so neighbouring seeds differ
    boss = rng.choice(["trimWhite", "sunny"]) if shield_colour != "sunny" else "trimWhite"
    shield_side = rng.choice([-1, 1])
    helmet = rng.choice([None, "tomato", "cobalt", "stone"])
    target = rng.choice(["tomato", "cobalt"])
    arm = 1.15 * size

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    kit.box((-0.95, -0.15, 0), (0.95, 0.15, 0.22), "doorBrown", skip=("-z",))
    kit.box((-0.15, -0.95, 0), (0.15, 0.95, 0.22), "doorBrown", skip=("-z",))
    kit.box((-0.14, -0.14, 0.22), (0.14, 0.14, 1.3 * size), "doorBrown", skip=("-z", "+z"))
    post = building.add(kit, "detail", "wood", 0)

    z0, z1 = 1.1 * size, 2.25 * size  # the straw body
    kit = Kit()
    prism(kit, (0, 0), z0, z1, 0.46 * size, 0.58 * size, 6, "sunny")
    kit.box((-arm, -0.11, z1 - 0.42), (arm, 0.11, z1 - 0.2), "doorBrown")
    prism(kit, (0, 0), z1, z1 + 0.62 * size, 0.36 * size, 0.36 * size, 6, "interiorCream", bottom=False)
    if helmet:
        prism(kit, (0, 0), z1 + 0.42 * size, z1 + 1.05 * size, 0.44 * size, 0.0, 6, helmet, bottom=False)
    # The target on its chest.
    zc = (z0 + z1) / 2 - 0.1
    for facing in (-1,):
        y = facing * 0.52 * size
        kit.poly([(-0.3, y, zc - 0.3), (0.3, y, zc - 0.3), (0.3, y, zc + 0.3), (-0.3, y, zc + 0.3)], (0, facing, 0), "trimWhite")
        y += facing * 0.03
        kit.poly([(-0.14, y, zc - 0.14), (0.14, y, zc - 0.14), (0.14, y, zc + 0.14), (-0.14, y, zc + 0.14)], (0, facing, 0), target)
    # A round shield on the end of one arm.
    sx = shield_side * (arm - 0.1)
    sz = z1 - 0.45
    prism(kit, (sx, sz), -0.3, -0.16, 0.55 * size, 0.55 * size, 6, "trimWhite", bottom_colour=shield_colour, top_colour=shield_colour, axis="y")
    kit.poly([(sx - 0.17, -0.33, sz - 0.17), (sx + 0.17, -0.33, sz - 0.17), (sx + 0.17, -0.33, sz + 0.17), (sx - 0.17, -0.33, sz + 0.17)], (0, -1, 0), boss)
    building.add(kit, "detail", "leaves", 0, supports=(post,), collider="hull")

    return building.finish(look=f"size={size} shield={shield_colour}/{'left' if shield_side < 0 else 'right'} helmet={helmet} target={target}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
