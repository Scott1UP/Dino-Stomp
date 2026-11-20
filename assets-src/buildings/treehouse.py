"""Treehouse generator: a forest landmark.

A huge eight-sided tree trunk about 3 m across carries a square wooden deck
with railings some 6 m up, a bright little cabin built round the trunk, and a
canopy of big leafy blobs on top: 16-18 m tall overall. A rope ladder hangs
from the front of the deck, or chunky steps wind up round the trunk.

The seed varies the trunk's height and colour, the deck's height and size, the
cabin's roof (ridge along the front, ridge front to back, or a pyramid), the
way up, the number and placing of the canopy blobs, and a tyre swing.

How it comes down: the trunk's ground tier is four quarter wedges, role
"pillar" at storey 0. The trunk tiers above rest on them, the deck on the
trunk, the cabin and railings on the deck, and the canopy on the top of the
trunk, so smashing the trunk brings everything down.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/treehouse.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import beam, wall_y  # noqa: E402
from lib.shapes_castle2 import pyramid  # noqa: E402
from lib.shapes_forest import dome, ladder, leaf_blob, railing, roof_halves  # noqa: E402
from lib.shapes_parkcastle import Frame, fbox  # noqa: E402
from lib.shapes_props import prism  # noqa: E402

TYPE = "treehouse"
HITS_TO_COLLAPSE = 3  # landmark
TRIANGLE_BUDGET = 1800

R_BASE = 1.75  # corner radius of the trunk at the ground
R_TOP = 1.3
DECK = 0.3
WALL = 0.3
CABIN = 2.5  # half the cabin's width
CABIN_H = 2.6


def build(building_id, seed, scheme=None, collection=None):
    """Build one treehouse. Returns (empty, stats)."""
    rng = random.Random(seed)

    trunk_h = rng.choice([10.0, 10.5, 11.0])
    deck_z = rng.choice([5.4, 5.8, 6.2])
    half = rng.choice([3.8, 4.1, 4.4])  # half the deck's width
    roof_style = ("ridge-x", "pyramid", "ridge-y")[seed % 3]  # cycled, so neighbouring seeds differ
    access = ("ladder", "steps")[seed % 2]
    side_blobs = rng.choice([2, 3, 4])
    blob_turn = rng.uniform(-0.25, 0.25)
    swing = rng.choice([True, False])
    swing_side = rng.choice([-1, 1])
    bark = rng.choice(["doorBrown", "doorBrown", "wood"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    timber = "wood" if bark == "doorBrown" else "doorBrown"
    door_colour = pal["door"] if pal["door"] != "doorBrown" else pal["roof"]
    colours = {"wall": pal["wall"], "interior": "interiorCream", "trim": pal["trim"], "glass": "windowBlue", "shine": "windowShine", "door": door_colour}

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    def radius(z):
        return R_BASE + (R_TOP - R_BASE) * z / trunk_h

    # --- the trunk: four quarter wedges with roots, then two whole tiers ---
    z1 = deck_z / 2
    quarters = []
    for q in range(4):
        kit = Kit()
        dome(kit, 0, 0, [(0, R_BASE + 0.25), (z1, radius(z1))], bark, facets=(q * 2, q * 2 + 1), under=bark, cut=bark)
        a = math.radians(q * 90 + 67.5)  # a root out from the middle of each quarter
        d = (math.cos(a), math.sin(a))
        t = (-d[1], d[0])
        inner, outer, w = 1.2, 3.1, 0.55
        foot = [(d[0] * inner + t[0] * w, d[1] * inner + t[1] * w, 0), (d[0] * inner - t[0] * w, d[1] * inner - t[1] * w, 0), (d[0] * outer, d[1] * outer, 0)]
        crown = (d[0] * inner, d[1] * inner, 1.7)
        kit.convex([foot] + [[foot[k], foot[(k + 1) % 3], crown] for k in range(3)], bark)
        quarters.append(add(kit, "pillar", "wood", 0, collider="hull"))

    kit = Kit()
    dome(kit, 0, 0, [(z1, radius(z1)), (deck_z, radius(deck_z))], bark, under=bark)
    mid_trunk = add(kit, "pillar", "wood", 1, supports=quarters, collider="hull")
    kit = Kit()
    dome(kit, 0, 0, [(deck_z, radius(deck_z)), (trunk_h, R_TOP)], bark, under=bark)
    top_trunk = add(kit, "pillar", "wood", 2, supports=(mid_trunk,), collider="hull")

    # --- the deck, in four quadrants, each on a diagonal brace ---
    floor_z = deck_z + DECK
    decks = {}
    for sx in (-1, 1):
        for sy in (-1, 1):
            xa, xb = sorted((0.0, sx * half))
            ya, yb = sorted((0.0, sy * half))
            kit = Kit()
            kit.box((xa, ya, deck_z), (xb, yb, floor_z), timber, sides={"+z": "interiorCream"})
            beam(kit, (sx * 0.9, sy * 0.9, deck_z - 2.6), (sx * (half - 0.5), sy * (half - 0.5), deck_z), 0.4, timber, caps=False)
            decks[sx, sy] = add(kit, "floor", "wood", 2, supports=(mid_trunk,), collider="hull")

    # --- railings: the front one leaves a gap for the way up ---
    edge = half - 0.15
    for sy in (-1, 1):
        for sx in (-1, 1):
            kit = Kit()
            inner = 0.8 if sy < 0 else 0.0
            railing(kit, (sx * inner, sy * edge, floor_z), (sx * edge, sy * edge, floor_z), 1.1, pal["trim"], posts=3)
            add(kit, "detail", "wood", 2, supports=(decks[sx, sy],))
    for sx in (-1, 1):
        kit = Kit()
        railing(kit, (sx * edge, -edge + 0.2, floor_z), (sx * edge, edge - 0.2, floor_z), 1.1, pal["trim"], posts=3)
        add(kit, "detail", "wood", 2, supports=(decks[sx, -1], decks[sx, 1]))

    # --- the cabin, built round the trunk ---
    c = CABIN
    top = floor_z + CABIN_H
    walls = {}

    kit = Kit()
    kit.wall(
        -c,
        c,
        floor_z,
        top,
        -c,
        WALL,
        1,
        [
            {"x0": -1.9, "x1": -0.7, "z0": floor_z, "z1": floor_z + 2.1, "kind": "door"},
            {"x0": 0.3, "x1": 1.8, "z0": floor_z + 0.9, "z1": floor_z + 2.1, "kind": "window"},
        ],
        colours,
    )
    walls["front"] = add(kit, "wall", "wood", 2, supports=(decks[-1, -1], decks[1, -1]))
    kit = Kit()
    kit.wall(-c, c, floor_z, top, c, WALL, -1, [{"x0": -1.1, "x1": 1.1, "z0": floor_z + 0.9, "z1": floor_z + 2.1, "kind": "window"}], colours)
    walls["back"] = add(kit, "wall", "wood", 2, supports=(decks[-1, 1], decks[1, 1]))
    for sx, name in ((-1, "left"), (1, "right")):
        kit = Kit()
        wall_y(kit, -c + WALL, c - WALL, floor_z, top, sx * c, WALL, -sx, [{"x0": -0.9, "x1": 0.9, "z0": floor_z + 0.9, "z1": floor_z + 2.1, "kind": "window"}], colours)
        walls[name] = add(kit, "wall", "wood", 2, supports=(decks[sx, -1], decks[sx, 1]))

    over = 0.5
    rise = 1.7
    if roof_style == "pyramid":
        kit = Kit()
        pyramid(kit, 0, 0, c + over, c + over, top, rise + 0.4, pal["roof"], under="interiorCream")
        add(kit, "roof", "tile", 3, supports=list(walls.values()), collider="hull")
    else:
        axis = "x" if roof_style == "ridge-x" else "y"
        slope = rise / c
        ends = ("left", "right") if axis == "x" else ("front", "back")
        holders = ("front", "back") if axis == "x" else ("left", "right")
        for sign, name in zip((-1, 1), ends):
            lo, hi = sorted((sign * c, sign * (c - WALL)))
            kit = Kit()
            section = [(-c, top), (c, top), (0, top + rise)]
            if axis == "x":
                kit.extrude_x(section, lo, hi, pal["wall"])
            else:
                kit.extrude_y(section, lo, hi, pal["wall"])
            walls[name + "-gable"] = add(kit, "wall", "wood", 3, supports=(walls[name],), collider="hull")
        for kit, name in zip(roof_halves(axis, -c - 0.4, c + 0.4, c + over, top - slope * over, top + rise, 0.28, pal["roof"]), holders):
            add(kit, "roof", "tile", 3, supports=(walls[name],), collider="hull")

    # --- the way up ---
    if access == "ladder":
        y = -half - 0.12
        pieces = []
        for za, zb in ((deck_z / 2, deck_z + 0.1), (0.3, deck_z / 2)):
            kit = Kit()
            ladder(kit, (0, y, za), (0, y, zb), (1, 0, 0), timber, width=1.1, rung=0.7, rail=0.16, rung_colour="doorBrown" if timber == "wood" else "wood")
            pieces = [add(kit, "detail", "wood", 1 if za > 1 else 0, supports=pieces or (decks[-1, -1], decks[1, -1]), collider="box")]
    else:
        count = 9
        for group in range(3):
            kit = Kit()
            for n in range(group * 3, group * 3 + 3):
                deg = 30 + n * 30  # winding round the back, to arrive at the front
                z = (n + 1) * (deck_z - 0.5) / count
                fbox(kit, Frame((0, 0, 0), deg), (-0.55, 1.15, z - 0.28), (0.55, 3.0, z), pal["roof"] if n % 2 else pal["trim"])
            add(kit, "detail", "wood", 0 if group == 0 else 1, supports=(quarters[0],) if group == 0 else (mid_trunk,), collider="hull")

    # --- a tyre swing under the deck ---
    if swing:
        x = swing_side * (half - 1.0)
        kit = Kit()
        beam(kit, (x, 0.9, 1.9), (x, 0.9, deck_z), 0.1, "trimWhite", caps=False)
        prism(kit, (x, 1.35), 0.6, 1.2, 0.72, 0.72, 8, "tyre", axis="y")
        add(kit, "detail", "rubber", 1, supports=(decks[swing_side, 1],), collider="box")

    # --- the canopy: one big blob on the trunk and smaller ones round it, each on a branch ---
    kit = Kit()
    crown_r = 4.0
    crown_z = trunk_h + 2.6
    leaf_blob(kit, (0, 0, crown_z), crown_r, 8, 4, dark_rings=2)
    add(kit, "roof", "leaves", 4, supports=(top_trunk,), collider="hull")
    for n in range(side_blobs):
        a = blob_turn + math.pi * (n + 0.5) / side_blobs  # round the back and sides, so the cabin's front stays in view
        r = rng.choice([2.4, 2.7, 3.0])
        reach = 3.6
        centre = (math.cos(a) * reach, math.sin(a) * reach, trunk_h + rng.choice([-0.4, 0.3, 1.0]))
        kit = Kit()
        leaf_blob(kit, centre, r, 6, 4, top="hedge" if n % 2 else "leaf")
        beam(kit, (math.cos(a) * 0.8, math.sin(a) * 0.8, trunk_h - 2.2), (centre[0] * 0.75, centre[1] * 0.75, centre[2] - 0.6), 0.5, bark, caps=False)
        add(kit, "roof", "leaves", 3, supports=(top_trunk,), collider="hull")

    return building.finish(look=f"trunk{trunk_h:g}/deck{deck_z:g}x{half * 2:g}/{roof_style}/{access}/blobs{side_blobs}/swing-{int(swing)}/{bark}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(20, 26))


if __name__ == "__main__":
    previews()
