"""Well generator.

A stone well for the castle yard: an eight-sided stone ring about 3 m across
with water in it, and over it a little bright roof on two wooden posts, with a
windlass and a bucket on a rope. Two modules: the ring, and the timber top
that rests on it. The seed varies the size, the roof (a gable or a cone) and
its colour.

    blender --background --factory-startup --python assets-src/props/well.py
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

TYPE = "well"
KIND = "prop"
TRIANGLE_BUDGET = 150
SPACING = 8


def build(building_id, seed, scheme=None, collection=None):
    """Build one well. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    radius = rng.choice([1.35, 1.5, 1.65])
    wall_h = rng.choice([1.0, 1.2])
    roof_style = ("gable", "cone")[seed % 2]
    roof_colour = rng.choice(castle.ROOFS)
    post_h = rng.choice([2.0, 2.3])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    # --- the stone ring, with water inside ---
    inner = radius - 0.4
    kit = Kit()
    shapes.frustum(kit, radius + 0.12, radius, 0, wall_h, "stone", bottom=False, top=False)
    rim_out = shapes.ring(radius, wall_h)
    rim_in = shapes.ring(inner, wall_h)
    low = shapes.ring(inner, 0.4)
    for i in range(8):
        j = (i + 1) % 8
        kit.poly([rim_out[i], rim_out[j], rim_in[j], rim_in[i]], (0, 0, 1), "trimWhite")
        kit.poly([rim_in[i], rim_in[j], low[j], low[i]], (-rim_in[i][0] - rim_in[j][0], -rim_in[i][1] - rim_in[j][1], 0), "stone")
    kit.poly(shapes.ring(inner, 0.5), (0, 0, 1), "windowBlue")
    ring = building.add(kit, "detail", "stone", 0, collider="hull")

    # --- posts, windlass, bucket and roof ---
    top = wall_h + post_h
    px = radius - 0.2
    kit = Kit()
    for x in (-px, px):
        kit.box((x - 0.15, -0.15, wall_h), (x + 0.15, 0.15, top), "doorBrown", skip=("-z", "+z"))
    kit.box((-px, -0.1, top - 0.95), (px, 0.1, top - 0.75), "wood", skip=("-x", "+x"))
    kit.box((-0.03, -0.03, wall_h + 0.6), (0.03, 0.03, top - 0.95), "trimWhite", skip=("-z", "+z"))
    kit.box((-0.24, -0.24, wall_h + 0.2), (0.24, 0.24, wall_h + 0.62), "wood", sides={"+z": "windowBlue"})
    if roof_style == "gable":
        kit.extrude_x([(-1.15, top), (1.15, top), (0, top + 1.0)], -radius - 0.35, radius + 0.35, roof_colour, colours={0: "trimWhite", 1: "trimWhite"})
    else:
        shapes.frustum(kit, radius + 0.5, 0, top, top + 1.3, roof_colour)
    building.add(kit, "detail", "wood", 0, supports=(ring,), collider="hull")

    return building.finish(look=f"r={radius} wall={wall_h} posts={post_h} {roof_style}/{roof_colour}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
