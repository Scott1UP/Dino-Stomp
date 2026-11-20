"""Picnic table generator.

A chunky park picnic table: a table on two trestles, a bench either side,
and sometimes a parasol. Table and benches are separate modules. About 3 m
long, along X. The seed varies the length, the colours, the parasol and what
has been left on the table.

    blender --background --factory-startup --python assets-src/props/picnic_table.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import BRIGHT, prism  # noqa: E402

TYPE = "picnic_table"
KIND = "prop"
TRIANGLE_BUDGET = 150

TOP_Z = 1.15
SEAT_Z = 0.65


def build(building_id, seed, scheme=None, collection=None):
    """Build one picnic table. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    parasol = seed % 2 == 0  # alternates, so neighbouring seeds always differ
    half = rng.choice([1.3, 1.5, 1.7])
    top_colour = rng.choice(["wood", "wood", "tomato", "cobalt", "sunny"])
    bench_colour = rng.choice(["wood", top_colour, "leaf"])
    shade_a, shade_b = rng.sample(BRIGHT, 2)
    treat = rng.choice(["cake", "basket", "none"])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    # --- the table on two trestles ---
    kit = Kit()
    kit.box((-half, -0.65, TOP_Z - 0.18), (half, 0.65, TOP_Z), top_colour)
    for sx in (-1, 1):
        x0, x1 = sorted((sx * (half - 0.55), sx * (half - 0.3)))
        kit.extrude_x([(-0.6, 0.0), (0.6, 0.0), (0.35, TOP_Z - 0.18), (-0.35, TOP_Z - 0.18)], x0, x1, "doorBrown", {4: top_colour})
    if not parasol:
        if treat == "cake":
            prism(kit, (0.2, 0), TOP_Z, TOP_Z + 0.35, 0.4, 0.4, 6, "bubblegum", bottom=False, top_colour="trimWhite")
        elif treat == "basket":
            kit.box((-0.5, -0.3, TOP_Z), (0.2, 0.3, TOP_Z + 0.4), "tangerine", skip=("-z",), sides={"+z": "trimWhite"})
    table = building.add(kit, "detail", "wood", 0)

    # --- a bench either side ---
    for sy in (-1, 1):
        y0, y1 = sorted((sy * 0.95, sy * 1.45))
        kit = Kit()
        kit.box((-half, y0, SEAT_Z - 0.16), (half, y1, SEAT_Z), bench_colour)
        for sx in (-1, 1):
            x0, x1 = sorted((sx * (half - 0.55), sx * (half - 0.3)))
            kit.box((x0, y0 + 0.08, 0), (x1, y1 - 0.08, SEAT_Z - 0.16), "doorBrown", skip=("-z", "+z"))
        building.add(kit, "detail", "wood", 0)

    # --- the parasol ---
    if parasol:
        kit = Kit()
        kit.box((-0.1, -0.1, TOP_Z), (0.1, 0.1, 3.0), "trimWhite", skip=("-z", "+z"))
        prism(kit, (0, 0), 2.6, 3.35, 1.9, 0.0, 6, shade_a, side_colours=[shade_a, shade_b], bottom_colour="trimWhite")
        building.add(kit, "detail", "tin", 0, supports=(table,), collider="hull")

    return building.finish(look=f"half={half} {top_colour}/{bench_colour}" + ("/parasol" if parasol else f"/{treat}"))


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(7, 7))


if __name__ == "__main__":
    previews()
