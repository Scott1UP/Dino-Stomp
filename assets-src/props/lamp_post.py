"""Lamp post generator.

A chunky cobalt post on a wide foot, with a sunny lantern and a pointed cap.
One module, about 5 m tall. The seed varies the height and the lantern (a
flared box lantern or a faceted globe).

    blender --background --factory-startup --python assets-src/props/lamp_post.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import ball, prism  # noqa: E402

TYPE = "lamp_post"
KIND = "prop"
TRIANGLE_BUDGET = 150

SIDES = 6
POST_RADIUS = 0.17  # about 0.3 m across, so it stays visible from the game camera
LANTERNS = ("box", "globe", "box")


def build(building_id, seed, scheme=None, collection=None):
    """Build one lamp post. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    height = rng.choice([4.8, 5.1, 5.4])
    lantern = LANTERNS[seed % len(LANTERNS)]  # cycled, so neighbouring seeds always differ
    post = rng.choice(["cobalt", "cobalt", "tomato"])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    lamp_z = height - 1.3
    kit = Kit()
    prism(kit, (0, 0), 0, 0.6, 0.42, 0.3, SIDES, post)
    prism(kit, (0, 0), 0.6, lamp_z, POST_RADIUS, POST_RADIUS, SIDES, post, bottom=False, top=False)
    if lantern == "box":
        prism(kit, (0, 0), lamp_z, lamp_z + 0.85, 0.36, 0.55, SIDES, "sunny", top=False)
        prism(kit, (0, 0), lamp_z + 0.85, height, 0.7, 0.0, SIDES, post)
    else:
        prism(kit, (0, 0), lamp_z, lamp_z + 0.2, 0.42, 0.42, SIDES, post, top=False)
        ball(kit, (0, 0, lamp_z + 0.7), 0.64, SIDES, 3, "sunny", squash=0.9)
        prism(kit, (0, 0), lamp_z + 1.15, height, 0.3, 0.0, SIDES, post, bottom=False)
    building.add(kit, "detail", "tin", 0)

    return building.finish(look=f"h={height} {lantern} {post}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 8))


if __name__ == "__main__":
    previews()
