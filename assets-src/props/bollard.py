"""Bollard generator.

A short chunky post about 1.1 m tall and 0.6 m across. One module. The seed
picks the form (a round striped post with a domed cap, a square post with a
pointed cap, or a post with a big ball on top) and the colours.

    blender --background --factory-startup --python assets-src/props/bollard.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import ball, prism  # noqa: E402

TYPE = "bollard"
KIND = "prop"
TRIANGLE_BUDGET = 150
SPACING = (4, 4)

FORMS = ("striped", "square", "ball")


def build(building_id, seed, scheme=None, collection=None):
    """Build one bollard. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    form = FORMS[seed % len(FORMS)]  # cycled, so neighbouring seeds always differ
    colour = rng.choice(["tomato", "cobalt", "tangerine", "sunny"])
    stripe = "trimWhite" if colour != "sunny" else "tyre"
    height = rng.choice([1.0, 1.1, 1.25])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    if form == "striped":
        bands = 3
        step = (height - 0.2) / bands
        prism(kit, (0, 0), 0, 0.2, 0.42, 0.38, 6, "tyre", bottom=False)
        for b in range(bands):
            prism(kit, (0, 0), 0.2 + b * step, 0.2 + (b + 1) * step, 0.34, 0.34, 6, colour if b % 2 == 0 else stripe, bottom=False, top=False)
        prism(kit, (0, 0), height, height + 0.24, 0.34, 0.0, 6, stripe)
    elif form == "square":
        kit.box((-0.32, -0.32, 0), (0.32, 0.32, 0.25), "tyre", skip=("-z",))
        kit.box((-0.26, -0.26, 0.25), (0.26, 0.26, height - 0.35), colour, skip=("-z", "+z"))
        kit.box((-0.29, -0.29, height - 0.35), (0.29, 0.29, height - 0.1), stripe)
        prism(kit, (0, 0), height - 0.1, height + 0.3, 0.37, 0.0, 4, colour, bottom=False)
    else:
        prism(kit, (0, 0), 0, 0.22, 0.4, 0.34, 6, "tyre", bottom=False)
        prism(kit, (0, 0), 0.22, height - 0.3, 0.26, 0.22, 6, "stone", bottom=False, top=False)
        prism(kit, (0, 0), height - 0.42, height - 0.3, 0.3, 0.3, 6, stripe)
        ball(kit, (0, 0, height), 0.36, 6, 3, colour)
    building.add(kit, "detail", "stone", 0, collider="hull")

    return building.finish(look=f"{form} {colour} h={height}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=SPACING)


if __name__ == "__main__":
    previews()
