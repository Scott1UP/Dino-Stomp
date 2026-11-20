"""Post box generator.

A chunky tomato pillar box: an eight-sided pillar with a rim and a domed cap, a
dark posting slot and a white plaque on the front. One module, so it tips over
whole. The seed varies its height, girth and cap.

    blender --background --factory-startup --python assets-src/props/post_box.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import apothem, panel_y, prism  # noqa: E402

TYPE = "post_box"
KIND = "prop"
TRIANGLE_BUDGET = 150

SIDES = 8


def build(building_id, seed, scheme=None, collection=None):
    """Build one post box. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    height = rng.choice([2.0, 2.2, 2.4])
    radius = rng.choice([0.55, 0.6, 0.65])
    cap = rng.choice(["dome", "dome", "flat"])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    cap_height = 0.5 if cap == "dome" else 0.3
    rim_z = height - cap_height - 0.2
    kit = Kit()
    prism(kit, (0, 0), 0, rim_z, radius, radius, SIDES, "tomato", top=False)
    prism(kit, (0, 0), rim_z, rim_z + 0.2, radius + 0.12, radius + 0.12, SIDES, "tomato", top=False)
    top_radius = radius * 0.45 if cap == "dome" else radius * 0.85
    prism(kit, (0, 0), rim_z + 0.2, height, radius + 0.12, top_radius, SIDES, "tomato", bottom=False)

    # The slot and plaque sit on the flat side that faces the front.
    face = -apothem(radius, SIDES) - 0.03
    half = radius * 0.34
    panel_y(kit, -half, half, rim_z - 0.42, rim_z - 0.2, face, -1, "windowBlue")
    panel_y(kit, -half, half, rim_z - 1.05, rim_z - 0.6, face, -1, "trimWhite")
    building.add(kit, "detail", "tin", 0, collider="hull")

    return building.finish(look=f"h={height} r={radius} {cap}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 8))


if __name__ == "__main__":
    previews()
