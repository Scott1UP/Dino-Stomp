"""Plaza fountain generator.

A wide eight-sided stone basin full of water, about 4 m in radius, with a
centrepiece of two or three bowls stacked on a column, water spilling from
the lowest bowl, and a finial on top. The basin is eight wedges that break
away one by one; each tier of the centrepiece is a module too. The seed
varies the basin's size and wall, the number and colour of the bowls, the
finial (ball, spire or a jet of water) and the spouts.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/fountain.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import frustum, ring  # noqa: E402
from lib.shapes_props import ball  # noqa: E402

TYPE = "fountain"
HITS_TO_COLLAPSE = 1  # small
TRIANGLE_BUDGET = 400

SIDES = 8
WATER = "water"


def build(building_id, seed, scheme=None, collection=None):
    """Build one fountain. Returns (empty, stats)."""
    rng = random.Random(seed)

    # --- the fountain's character ---
    tiers = (2, 3)[seed % 2]  # cycled, so neighbouring seeds always differ
    finial = ("ball", "jet", "spire")[seed % 3]
    radius = rng.choice([3.7, 4.0, 4.3])
    wall_h = rng.choice([0.8, 0.95, 1.1])
    wall_t = rng.choice([0.5, 0.65])
    bowl_pick = rng.choice(["accent", "stone", "trim"])
    spouts = rng.choice(["four", "four", "eight"])
    rim_pick = rng.choice(["trim", "accent"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]
    accent = pal["roof"]
    bowl = {"accent": accent, "stone": "stone", "trim": "trimWhite"}[bowl_pick]
    rim = {"trim": "trimWhite", "accent": accent}[rim_pick]

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    water_z = wall_h - 0.2
    plinth_r = 1.3
    outer_lo, outer_hi = ring(0, 0, 0, radius), ring(0, 0, wall_h, radius)
    inner_lo, inner_hi = ring(0, 0, 0, radius - wall_t), ring(0, 0, wall_h, radius - wall_t)
    inner = ring(0, 0, water_z, radius - wall_t)
    core = ring(0, 0, water_z, plinth_r - 0.05)

    # --- the basin: eight wedges of wall, each with its slice of water ---
    for i in range(SIDES):
        j = (i + 1) % SIDES
        kit = Kit()
        kit.convex(
            [
                [outer_lo[i], outer_lo[j], outer_hi[j], outer_hi[i]],
                [inner_lo[i], inner_lo[j], inner_hi[j], inner_hi[i]],
                [outer_hi[i], outer_hi[j], inner_hi[j], inner_hi[i]],
                [outer_lo[i], outer_lo[j], inner_lo[j], inner_lo[i]],
                [outer_lo[i], outer_hi[i], inner_hi[i], inner_lo[i]],
                [outer_lo[j], outer_hi[j], inner_hi[j], inner_lo[j]],
            ],
            "stone",
            colours={2: rim},
        )
        kit.poly([core[i], core[j], inner[j], inner[i]], (0, 0, 1), WATER)
        add(kit, "wall", "stone", 0, collider="hull")

    # --- the centrepiece: a plinth, then a column and a bowl to each tier ---
    if tiers == 2:
        rims = [(2.6, 2.1), (4.2, 1.3)]  # (height of the rim, radius of the bowl)
    else:
        rims = [(2.4, 2.2), (3.8, 1.55), (5.0, 1.0)]
    kit = Kit()
    frustum(kit, 0, 0, 0, plinth_r, wall_h + 0.15, plinth_r, "stone", top="stone")
    below = add(kit, "pillar", "stone", 0, collider="hull")
    z = wall_h + 0.15
    for t, (rim_z, bowl_r) in enumerate(rims):
        kit = Kit()
        neck = 0.6 - 0.1 * t
        frustum(kit, 0, 0, z, neck, rim_z - 0.95, neck, "stone", sides=6)
        frustum(kit, 0, 0, rim_z - 0.95, neck, rim_z - 0.4, bowl_r, bowl)
        frustum(kit, 0, 0, rim_z - 0.4, bowl_r, rim_z, bowl_r, bowl, top=bowl)
        kit.poly(ring(0, 0, rim_z + 0.03, bowl_r - 0.32), (0, 0, 1), WATER)
        if t == 0:
            # Water spilling over the lip into the basin.
            edge = ring(0, 0, rim_z, bowl_r + 0.06)
            for i in range(0, SIDES, 2 if spouts == "four" else 1):
                a, b = edge[i], edge[(i + 1) % SIDES]
                p = (a[0] * 0.75 + b[0] * 0.25, a[1] * 0.75 + b[1] * 0.25)
                q = (a[0] * 0.25 + b[0] * 0.75, a[1] * 0.25 + b[1] * 0.75)
                mid = ((p[0] + q[0]) / 2, (p[1] + q[1]) / 2, 0)
                quad = [(p[0], p[1], rim_z + 0.03), (q[0], q[1], rim_z + 0.03), (q[0] * 1.1, q[1] * 1.1, water_z), (p[0] * 1.1, p[1] * 1.1, water_z)]
                # A paler colour than the pool, so the falling water shows against it.
                kit.poly(quad, mid, "foam")
                if spouts == "four":
                    kit.poly(quad, (-mid[0], -mid[1], 0), "foam")
        if t == len(rims) - 1:
            top = rim_z
            if finial == "ball":
                ball(kit, (0, 0, top + 0.6), 0.65, 6, 3, "sunny")
            elif finial == "spire":
                frustum(kit, 0, 0, top, 0.0, top + 0.7, 0.55, "sunny", sides=4)
                frustum(kit, 0, 0, top + 0.7, 0.55, top + 2.1, 0.0, "sunny", sides=4)
            else:
                frustum(kit, 0, 0, top, 0.34, top + 0.5, 0.34, "sunny", sides=4)
                frustum(kit, 0, 0, top + 0.5, 0.16, top + 1.7, 0.65, WATER, sides=6, top=WATER)
        below = add(kit, "detail", "stone", t + 1, supports=(below,), collider="hull")
        z = rim_z - 0.1

    return building.finish(look=f"{tiers}tiers/{finial}/r{radius:g}/wall{wall_h:g}x{wall_t:g}/bowl-{bowl_pick}/rim-{rim_pick}/spouts-{spouts}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(13, 13))


if __name__ == "__main__":
    previews()
