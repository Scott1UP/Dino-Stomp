"""Mushroom house generator.

A storybook giant toadstool to live in: a fat white stalk with a front door
and round windows, under a big bright spotted cap with a crooked little
chimney. About 6 m across and 6-7 m tall.

The seed varies the cap (a dome, a pointed hat or a flat parasol; tomato,
bubblegum or tangerine; how big and how spotty), the stalk's height and girth,
which side the front window and the chimney are on, the door's colour and
whether a baby toadstool grows beside it.

The stalk is four quarter shells, role "wall" at storey 0; the cap is two
halves resting on them.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/mushroom_house.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import flat, round_window, shell  # noqa: E402
from lib.shapes_forest import COS8, dome, facet_normal, facet_point  # noqa: E402

TYPE = "mushroom_house"
HITS_TO_COLLAPSE = 1
TRIANGLE_BUDGET = 400

CAPS = ("dome", "hat", "parasol")
CAP_COLOURS = ("tomato", "bubblegum", "tangerine")
SHELL = 0.3


def _cap_profile(shape, z, radius, height):
    if shape == "hat":
        return [(z, radius * 0.93), (z + height * 0.14, radius), (z + height * 0.5, radius * 0.58), (z + height * 0.82, radius * 0.22), (z + height, 0)]
    if shape == "parasol":
        return [(z, radius * 0.92), (z + height * 0.25, radius), (z + height * 0.7, radius * 0.66), (z + height * 0.95, radius * 0.25), (z + height, 0)]
    return [(z, radius * 0.9), (z + height * 0.24, radius), (z + height * 0.62, radius * 0.76), (z + height * 0.9, radius * 0.36), (z + height, 0)]


def build(building_id, seed, scheme=None, collection=None):
    """Build one mushroom house. Returns (empty, stats)."""
    rng = random.Random(seed)

    shape = CAPS[seed % len(CAPS)]  # cycled, so neighbouring seeds differ
    cap_colour = CAP_COLOURS[(seed // 2) % len(CAP_COLOURS)]
    radius = rng.choice([2.9, 3.1, 3.3])
    stalk_h = rng.choice([3.2, 3.5, 3.8])
    girth = rng.choice([1.85, 2.0, 2.15])  # the stalk's corner radius at the ground
    window_side = rng.choice([-1, 1])
    chimney_side = rng.choice([-1, 1])
    spotty = rng.choice([4, 5])
    baby = rng.choice([True, False])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    door_colour = pal["door"] if pal["door"] != cap_colour else "cobalt"
    cap_h = {"dome": 2.9, "hat": 3.5, "parasol": 2.3}[shape]
    top_r = girth * 0.82
    lean = (girth - top_r) * COS8 / stalk_h

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    def on_stalk(i, z):
        return facet_point(i, girth + (top_r - girth) * z / stalk_h, z)

    # --- the stalk: four quarter shells ---
    quarters = []
    for q in range(4):
        kit = Kit()
        shell(kit, 0, 0, [(0, girth), (stalk_h, top_r)], SHELL, (q * 2, q * 2 + 1), "trimWhite", "interiorCream")
        if q == 2:  # the front: facet 5 faces -Y
            normal = facet_normal(5, lean)
            flat(kit, on_stalk(5, 0), normal, [(-0.62, 0), (0.62, 0), (0.62, 1.55), (0.32, 2.05), (-0.32, 2.05), (-0.62, 1.55)], "wood", lift=0.04)
            flat(kit, on_stalk(5, 0), normal, [(-0.48, 0), (0.48, 0), (0.48, 1.5), (0.24, 1.9), (-0.24, 1.9), (-0.48, 1.5)], door_colour, lift=0.08)
            flat(kit, on_stalk(5, 0.95), normal, [(0.22, -0.08), (0.36, -0.08), (0.36, 0.08), (0.22, 0.08)], "sunny", lift=0.11)
            if window_side < 0:
                round_window(kit, on_stalk(4, 1.7), facet_normal(4, lean), 0.5, "wood")
        if q == 3 and window_side > 0:
            round_window(kit, on_stalk(6, 1.7), facet_normal(6, lean), 0.5, "wood")
        if q == 0:  # a window at the back
            round_window(kit, on_stalk(1, 1.7), facet_normal(1, lean), 0.55, "wood")
        quarters.append(add(kit, "wall", "plaster", 0, collider="hull"))

    kit = Kit()  # the doorstep
    x, y, _ = on_stalk(5, 0)
    kit.box((x - 0.9, y - 0.75, 0), (x + 0.9, y + 0.15, 0.18), "stone", skip=("-z",))
    add(kit, "detail", "stone", 0)

    # --- the cap, in a left and a right half ---
    rim = stalk_h - 0.35
    profile = _cap_profile(shape, rim, radius, cap_h)
    halves = {}
    for side, facets, holders in ((-1, (2, 3, 4, 5), (quarters[1], quarters[2])), (1, (6, 7, 8, 9), (quarters[3], quarters[0]))):
        picks = [(1, facets[0]), (2, facets[1]), (1, facets[2]), (2, facets[3]), (1, facets[3])][:spotty]
        spots = [(band, i, radius * (0.2 if band == 1 else 0.15)) for band, i in picks]
        if side > 0:
            spots = [(3 - band, i, size) for band, i, size in spots]  # the other half is spotted the other way up
        kit = Kit()
        dome(kit, 0, 0, profile, cap_colour, facets=facets, under="interiorCream", cut=cap_colour, spots=spots)
        halves[side] = add(kit, "roof", "rubber", 1, supports=holders, collider="hull")

    # --- a crooked little chimney, poking out of the cap ---
    cx, cy = chimney_side * radius * 0.42, radius * 0.15
    z0 = rim + cap_h * 0.5
    z1 = rim + cap_h + 0.5
    kit = Kit()
    low = [(cx - 0.36, cy - 0.36, z0), (cx + 0.36, cy - 0.36, z0), (cx + 0.36, cy + 0.36, z0), (cx - 0.36, cy + 0.36, z0)]
    tilt = chimney_side * 0.3
    high = [(x + tilt, y, z1) for x, y, _ in low]
    kit.convex([low, high] + [[low[k], low[(k + 1) % 4], high[(k + 1) % 4], high[k]] for k in range(4)], "stone")
    kit.box((cx + tilt - 0.48, cy - 0.48, z1), (cx + tilt + 0.48, cy + 0.48, z1 + 0.22), "trimWhite")
    add(kit, "detail", "stone", 2, supports=(halves[chimney_side],), collider="hull")

    # --- a baby toadstool beside the door ---
    if baby:
        bx, by = -window_side * (girth + 1.0), -girth * 0.75
        kit = Kit()
        dome(kit, bx, by, [(0, 0.42), (1.1, 0.34)], "trimWhite", sides=6, top=False)
        dome(kit, bx, by, [(0.95, 0.95), (1.25, 1.05), (1.65, 0.6), (1.85, 0)], cap_colour, sides=6, under="interiorCream", spots=[(1, 0, 0.2), (1, 2, 0.2), (1, 4, 0.2)])
        add(kit, "detail", "rubber", 0, collider="hull")

    return building.finish(look=f"{shape}/{cap_colour}/r{radius}/stalk{stalk_h}x{girth}/window{window_side:+d}/chimney{chimney_side:+d}/spots{spotty}/baby-{int(baby)}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(10, 11))


if __name__ == "__main__":
    previews()
