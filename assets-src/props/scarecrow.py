"""Scarecrow generator.

A friendly scarecrow about 4 m tall. Two modules: a stout post (0.34 m
thick), and the scarecrow himself resting on it: a bright
patched shirt with straw cuffs, a sack head with a smile and a carrot nose,
and a hat. The seed varies the shirt and hat colours, the hat (pointed,
brimmed top hat or floppy) and which way the arms tilt.

    blender --background --factory-startup --python assets-src/props/scarecrow.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_fair import beam  # noqa: E402
from lib.shapes_props import panel_y, prism  # noqa: E402

TYPE = "scarecrow"
KIND = "prop"
TRIANGLE_BUDGET = 150

HATS = ("pointed", "top", "floppy")
SHIRTS = ("tomato", "cobalt", "bubblegum", "leaf", "tangerine")
POST = 0.17  # half the post's thickness


def build(building_id, seed, scheme=None, collection=None):
    """Build one scarecrow. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    hat = HATS[seed % len(HATS)]  # cycled, so neighbouring seeds always differ
    shirt = SHIRTS[seed % len(SHIRTS)]
    hat_colour = rng.choice([c for c in ("doorBrown", "cobalt", "tomato", "tyre") if c != shirt])
    patch = rng.choice([c for c in ("sunny", "trimWhite", "tangerine") if c != shirt])
    tilt = rng.choice([-0.25, 0.0, 0.25])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    # The post.
    kit = Kit()
    kit.box((-POST, -POST, 0), (POST, POST, 3.0), "doorBrown", skip=("-z",))
    post = building.add(kit, "detail", "wood", 0)

    # The scarecrow.
    kit = Kit()
    # One pole through both sleeves, so the arms tilt together; its ends are the straw hands.
    beam(kit, (-1.8, 0, 2.45 - tilt), (1.8, 0, 2.45 + tilt), 0.42, shirt, end_colour="sunny")
    kit.extrude_y([(-0.7, 1.3), (0.7, 1.3), (0.55, 2.75), (-0.55, 2.75)], -0.3, 0.3, shirt)
    panel_y(kit, -0.4, -0.05, 1.6, 1.95, -0.32, -1, patch)
    kit.box((-0.75, -0.33, 1.1), (0.75, 0.33, 1.3), "sunny", skip=("+z", "-z"))  # straw skirt
    # Sack head with a face.
    kit.box((-0.42, -0.4, 2.75), (0.42, 0.4, 3.5), "wood", skip=("-z", "+z"))
    for x in (-0.2, 0.2):
        panel_y(kit, x - 0.08, x + 0.08, 3.18, 3.34, -0.42, -1, "tyre")
    kit.poly([(-0.24, -0.42, 2.98), (0.24, -0.42, 2.98), (0.12, -0.42, 2.86), (-0.12, -0.42, 2.86)], (0, -1, 0), "tyre")
    kit.poly([(-0.08, -0.4, 3.04), (0.08, -0.4, 3.04), (0, -0.75, 3.1)], (0, -0.2, 1), "tangerine")
    kit.poly([(-0.08, -0.4, 3.04), (0.08, -0.4, 3.04), (0, -0.75, 3.1)], (0, -0.2, -1), "tangerine")
    # Hat.
    if hat == "pointed":
        prism(kit, (0, 0), 3.5, 3.6, 0.85, 0.85, 6, hat_colour, bottom=False)
        prism(kit, (0, 0), 3.6, 4.4, 0.5, 0.0, 6, hat_colour)
    elif hat == "top":
        prism(kit, (0, 0), 3.5, 3.6, 0.85, 0.85, 5, hat_colour, bottom=False, top_colour=patch)
        prism(kit, (0, 0), 3.6, 4.25, 0.5, 0.52, 5, hat_colour, bottom=False)
    else:
        prism(kit, (0, 0), 3.42, 3.62, 0.95, 0.6, 6, hat_colour, bottom=False, top=False)
        prism(kit, (0, 0), 3.62, 4.0, 0.5, 0.3, 6, hat_colour, bottom=False)
    building.add(kit, "detail", "leaves", 0, supports=(post,), collider="hull")

    return building.finish(look=f"{hat} hat={hat_colour} shirt={shirt} tilt={tilt}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(6, 6))


if __name__ == "__main__":
    previews()
