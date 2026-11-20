"""Grain silo generator.

A tall eight-sided tin drum about 5 m across and 14-18 m tall, banded with
bright hoops, under a dome or cone cap. A ladder climbs the front and a
little chute sticks out of one side. It is built as stacked ring storeys of
2-4 wall pieces each; inside is a heap of grain and one grain-covered floor,
which show once the walls start to go.

The seed varies the radius, the number of rings, how many pieces each ring
breaks into, the cap, the body, hoop and cap colours and which side the chute
is on. The scheme is not used for colours.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/silo.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_farm as farm  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_fair import beam  # noqa: E402
from lib.shapes_parkcastle import fquad  # noqa: E402
from lib.shapes_props import prism  # noqa: E402

TYPE = "silo"
HITS_TO_COLLAPSE = 3  # tall and sturdy
TRIANGLE_BUDGET = 900

WALL = 0.3
COS = math.cos(math.pi / 8)
# Facet 5 faces the front, 7 the right, 1 the back, 3 the left.
SPLITS = {2: ((4, 5, 6, 7), (8, 9, 10, 11)), 3: ((4, 5, 6), (7, 8, 9), (10, 11)), 4: ((4, 5), (6, 7), (8, 9), (10, 11))}
CAPS = ("dome", "cone")
LOOKS = (  # body, hoops, cap
    ("stone", "tomato", "tomato"),
    ("stone", "cobalt", "cobalt"),
    ("trimWhite", "tomato", "cobalt"),
    ("cobalt", "trimWhite", "sunny"),
    ("stone", "sunny", "tangerine"),
    ("trimWhite", "cobalt", "tomato"),
)


def build(building_id, seed, scheme=None, collection=None):
    """Build one silo. Returns (empty, stats)."""
    rng = random.Random(seed)

    # --- the silo's character ---
    cap = CAPS[seed % len(CAPS)]  # cycled, so neighbouring seeds always differ
    pieces = (2, 3, 4)[seed % 3]
    rings = (4, 5)[(seed // 3) % 2] if pieces < 4 else 4  # four-piece rings stay at four, for the budget
    radius = rng.choice([2.5, 2.65, 2.8])  # to the corners
    body, hoop, cap_colour = rng.choice(LOOKS)
    chute_side = rng.choice([-1, 1])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    split = SPLITS[pieces]
    ring_h = 3.0 if rings == 4 else 2.9  # height of one ring storey
    flat = radius * COS  # centre to the middle of a facet
    front_face = farm.face("front", -flat)

    def holder(ids, facet):
        """The piece of a ring that has this facet."""
        return next(ids[k] for k, facets in enumerate(split) if facet % 8 in [f % 8 for f in facets])

    # --- the drum: ring storeys, each a few pieces, each with a hoop round its foot ---
    ring_ids = []
    for s in range(rings):
        z0, z1 = s * ring_h, (s + 1) * ring_h
        ids = []
        for k, facets in enumerate(split):
            kit = Kit()
            farm.ring_piece(kit, radius, WALL, z0, z1, facets, body, "interiorCream", hoops=[(z0 + 0.1, z0 + 0.5)], hoop_colour=hoop)
            if s == 0 and 5 in facets:  # a hatch at the foot
                fquad(kit, front_face, 0.25, 1.05, 0.5, 2.1, 0.03, "trimWhite")
                fquad(kit, front_face, 0.35, 0.95, 0.5, 2.0, 0.05, hoop)
            ids.append(add(kit, "wall", "tin", s, supports=(ring_ids[-1][k],) if ring_ids else (), collider="hull"))
        ring_ids.append(ids)

    # --- grain: a heap on the ground, and a full floor part-way up ---
    kit = Kit()
    prism(kit, (0, 0), 0, 1.8, radius - WALL - 0.1, 0.0, 8, "sunny", bottom=False)
    add(kit, "detail", "leaves", 0, collider="hull")
    kit = Kit()
    prism(kit, (0, 0), 2 * ring_h - 0.25, 2 * ring_h, radius - WALL, radius - WALL, 8, "interiorCream", top_colour="sunny", phase=math.pi / 8)
    add(kit, "floor", "wood", 2, supports=ring_ids[1], collider="hull")

    # --- the cap, in two halves, and a vent on top ---
    top = rings * ring_h
    if cap == "dome":
        profile = [(top, radius + 0.2), (top + 1.0, radius * 0.86), (top + 1.9, radius * 0.5), (top + 2.3, 0.0)]
    else:
        profile = [(top, radius + 0.3), (top + 2.9, 0.0)]
    cap_ids = []
    for facets in SPLITS[2]:
        kit = Kit()
        farm.cap_piece(kit, profile, facets, cap_colour, under="interiorCream")
        cap_ids.append(add(kit, "roof", "tin", rings, supports=ring_ids[-1], collider="hull"))
    tip = profile[-1][0]
    kit = Kit()
    prism(kit, (0, 0), tip - 0.5, tip + 0.35, 0.42, 0.42, 6, "trimWhite", bottom=False)
    prism(kit, (0, 0), tip + 0.35, tip + 0.8, 0.62, 0.0, 6, hoop)
    add(kit, "detail", "tin", rings + 1, supports=cap_ids, collider="hull")

    # --- the ladder up the front, a length for each ring ---
    y_wall = -flat - 0.14
    for s in range(rings):
        z0, z1 = s * ring_h + (0.5 if s == 0 else 0.0), (s + 1) * ring_h
        kit = Kit()
        for x in (-0.95, -0.25):
            kit.box((x - 0.08, y_wall - 0.3, z0), (x + 0.08, y_wall - 0.14, z1), "tyre", skip=("-z", "+z", "+y"))
        z = z0 + 0.5
        while z < z1 - 0.1:
            kit.poly([(-0.87, y_wall - 0.24, z), (-0.33, y_wall - 0.24, z), (-0.33, y_wall - 0.24, z + 0.16), (-0.87, y_wall - 0.24, z + 0.16)], (0, -1, 0), "tyre")
            z += 0.8
        add(kit, "detail", "tin", s, supports=(holder(ring_ids[s], 5),))

    # --- the chute: a spout slanting down from a hopper on one side ---
    facet = 7 if chute_side > 0 else 3
    x_wall = chute_side * flat
    kit = Kit()
    xa, xb = sorted((x_wall, x_wall + chute_side * 0.8))
    kit.box((xa, -0.6, 3.6), (xb, 0.6, 4.8), hoop, skip=("-x" if chute_side > 0 else "+x",))
    beam(kit, (x_wall + chute_side * 0.6, 0, 3.9), (x_wall + chute_side * 2.6, 0, 1.7), 0.75, cap_colour, depth=0.5, end_colour="tyre")
    add(kit, "detail", "tin", 1, supports=(holder(ring_ids[1], facet),), collider="hull")

    height = tip + 0.8
    return building.finish(look=f"{cap} rings={rings}x{pieces} r={radius} {body}/{hoop}/{cap_colour} chute{chute_side:+d} height={height:.1f}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(12, 14))


if __name__ == "__main__":
    previews()
