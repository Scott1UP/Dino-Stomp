"""Covered bridge generator.

A wooden covered bridge about 14 m long and 6 m wide, running along X so a
path can pass straight through it: a raised plank deck with a short ramp at
each end, low boarded side walls with open timber trusses above them, and a
bright pitched roof with a gable over each end. The inside is open from end to
end.

The seed varies the length, the roof pitch, the height of the side walls, the
trusses (crosses, V's or a single diagonal), the timber colour and what the
ramps are made of.

How it comes down: each side is three wall bays, role "wall" at storey 0. Each
roof sheet rests on the bay under it and each gable on the end bays.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/covered_bridge.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import beam, flat, polygon  # noqa: E402
from lib.shapes_forest import roof_halves  # noqa: E402

TYPE = "covered_bridge"
HITS_TO_COLLAPSE = 2
TRIANGLE_BUDGET = 900

HALF = 3.0  # half the width, to the outside of the walls
WALL = 0.3
DECK = 0.6  # height of the roadway
EAVE = 4.4
POST = 0.42
RAMP = 2.0
BAYS = 3


def build(building_id, seed, scheme=None, collection=None):
    """Build one covered bridge. Returns (empty, stats)."""
    rng = random.Random(seed)

    length = rng.choice([9.6, 10.0, 10.4])  # the covered part; the ramps add 2 m at each end
    pitch = rng.choice([0.6, 0.75, 0.9])
    parapet = rng.choice([1.2, 1.4, 1.6])
    truss = ("cross", "vee", "slash")[seed % 3]  # cycled, so neighbouring seeds differ
    dark = rng.choice([True, False])
    ramp_colour = rng.choice(["stone", "stone", "wood"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    frame = "doorBrown" if dark else "wood"
    planks = "wood" if dark else "doorBrown"

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    x0, x1 = -length / 2, length / 2
    bay = length / BAYS
    rail = DECK + parapet
    rise = pitch * HALF
    ridge = EAVE + rise

    # --- the roadway: three lengths of deck and a ramp at each end ---
    for n in range(BAYS):
        kit = Kit()
        kit.box((x0 + n * bay, -HALF + WALL, 0), (x0 + (n + 1) * bay, HALF - WALL, DECK), "stone", sides={"+z": planks})
        add(kit, "floor", "wood", 0)
    for sign in (-1, 1):
        xa = sign * length / 2
        xb = xa + sign * RAMP
        kit = Kit()
        kit.extrude_y([(xa, 0), (xb, 0), (xa, DECK)], -HALF + WALL, HALF - WALL, ramp_colour, colours={4: planks} if ramp_colour == "stone" else None)
        add(kit, "detail", "stone" if ramp_colour == "stone" else "wood", 0, collider="hull")

    # --- the side walls: boarded below, open trusses above ---
    walls = {-1: [], 1: []}
    for sy in (-1, 1):
        y_out = sy * HALF
        ya, yb = sorted((y_out, y_out - sy * WALL))
        yp = y_out - sy * WALL / 2  # the trusses' centre line
        inner = "+y" if sy < 0 else "-y"
        for n in range(BAYS):
            a, b = x0 + n * bay, x0 + (n + 1) * bay
            kit = Kit()
            kit.box((a, ya, 0), (b, yb, rail), pal["wall"], sides={inner: "interiorCream", "+z": pal["trim"]})
            posts = [a + POST / 2] + ([b - POST / 2] if n == BAYS - 1 else [])
            for x in posts:
                kit.box((x - POST / 2, yp - POST / 2, rail), (x + POST / 2, yp + POST / 2, EAVE), frame, skip=("-z", "+z"))
            kit.box((a, yp - POST / 2, EAVE - 0.4), (b, yp + POST / 2, EAVE), frame, skip=("-x", "+x") if 0 < n < BAYS - 1 else ())
            lo, hi = rail + 0.05, EAVE - 0.4
            left, right = a + POST, b - (POST if n == BAYS - 1 else 0)
            mid = (left + right) / 2
            if truss == "cross":
                beam(kit, (left, yp, lo), (right, yp, hi), 0.22, frame, caps=False)
                beam(kit, (left, yp, hi), (right, yp, lo), 0.22, frame, caps=False)
            elif truss == "vee":
                beam(kit, (left, yp, hi), (mid, yp, lo), 0.24, frame, caps=False)
                beam(kit, (mid, yp, lo), (right, yp, hi), 0.24, frame, caps=False)
            else:
                way = (n % 2 == 0) == (sy < 0)
                beam(kit, (left, yp, lo if way else hi), (right, yp, hi if way else lo), 0.26, frame, caps=False)
            walls[sy].append(add(kit, "wall", "wood", 0))

    # --- a gable over each end, leaving the way through clear ---
    gables = []
    for sign in (-1, 1):
        x_out = sign * length / 2
        xa, xb = sorted((x_out, x_out - sign * WALL))
        end = 0 if sign < 0 else BAYS - 1
        kit = Kit()
        kit.extrude_x([(-HALF, EAVE), (HALF, EAVE), (0, ridge)], xa, xb, pal["wall"])
        kit.box((xa - 0.06, -HALF, EAVE - 0.45), (xb + 0.06, HALF, EAVE), pal["trim"])
        flat(kit, (x_out, 0, EAVE + rise * 0.38), (sign, 0, 0), polygon(min(0.6, rise * 0.24)), pal["trim"], lift=0.04)
        gables.append(add(kit, "wall", "wood", 1, supports=(walls[-1][end], walls[1][end]), collider="hull"))

    # --- the roof: three sheets a side, and a ridge board ---
    over = 0.7
    sheets = []
    for n in range(BAYS):
        a = x0 + n * bay - (0.6 if n == 0 else 0)
        b = x0 + (n + 1) * bay + (0.6 if n == BAYS - 1 else 0)
        for kit, sy in zip(roof_halves("x", a, b, HALF + over, EAVE - pitch * over, ridge, 0.3, pal["roof"]), (-1, 1)):
            sheets.append(add(kit, "roof", "tile", 1, supports=(walls[sy][n],), collider="hull"))
    kit = Kit()
    kit.box((x0 - 0.75, -0.24, ridge + 0.12), (x1 + 0.75, 0.24, ridge + 0.5), pal["trim"])
    add(kit, "detail", "wood", 2, supports=sheets)

    return building.finish(look=f"len{length:g}/pitch{pitch}/parapet{parapet}/{truss}/{frame}/ramp-{ramp_colour}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(20, 14))


if __name__ == "__main__":
    previews()
