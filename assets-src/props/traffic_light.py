"""Traffic light generator.

A chunky pole about 5 m tall with a three-light head: red, yellow, green,
showing to the front and the back. One module. The seed varies the height,
the pole and head colours, and the form: a plain post, a post with a little
crossing box under the head, or a post with the head hung out on an arm.

    blender --background --factory-startup --python assets-src/props/traffic_light.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import flat, polygon  # noqa: E402
from lib.shapes_props import panel_y, prism  # noqa: E402

TYPE = "traffic_light"
KIND = "prop"
TRIANGLE_BUDGET = 150
SPACING = (7, 7)

SIDES = 6
POST_RADIUS = 0.18  # a good 0.3 m across, so it stays visible from the game camera
FORMS = ("post", "arm", "crossing")
LIGHTS = ("tomato", "sunny", "leaf")  # top to bottom


def build(building_id, seed, scheme=None, collection=None):
    """Build one traffic light. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    form = FORMS[seed % len(FORMS)]  # cycled, so neighbouring seeds always differ
    height = rng.choice([4.8, 5.1, 5.4])
    post = rng.choice(["tyre", "cobalt", "tyre"])
    head = rng.choice(["tyre", "tyre", "cobalt"])
    arm_side = rng.choice([-1, 1])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    head_h = 2.2
    head_x = arm_side * 1.5 if form == "arm" else 0.0
    head_z = height - head_h
    kit = Kit()
    prism(kit, (0, 0), 0, 0.6, 0.44, 0.3, SIDES, post, bottom=False)
    prism(kit, (0, 0), 0.6, height - 0.3 if form == "arm" else head_z, POST_RADIUS, POST_RADIUS, SIDES, post, bottom=False, top=False)
    if form == "arm":
        xa, xb = sorted((-arm_side * 0.2, head_x))
        kit.box((xa, -0.16, height - 0.6), (xb, 0.16, height - 0.28), post)
    kit.box((head_x - 0.45, -0.3, head_z), (head_x + 0.45, 0.3, height), head)
    for i, colour in enumerate(LIGHTS):
        z = height - 0.42 - i * 0.68
        for facing in (-1, 1):
            flat(kit, (head_x, facing * 0.3, z), (0, facing, 0), polygon(0.3, SIDES), colour, lift=0.04)
    if form == "crossing":
        # A little box lower down with one green light: the crossing signal.
        z = 2.2
        kit.box((-0.34, -0.26, z), (0.34, 0.26, z + 0.75), head)
        for facing in (-1, 1):
            panel_y(kit, -0.2, 0.2, z + 0.18, z + 0.58, facing * 0.28, facing, "leaf")
    building.add(kit, "detail", "tin", 0)

    return building.finish(look=f"{form} h={height} {post}/{head}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=SPACING)


if __name__ == "__main__":
    previews()
