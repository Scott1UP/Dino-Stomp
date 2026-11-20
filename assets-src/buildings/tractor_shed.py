"""Tractor shed generator.

An open-fronted machinery shed about 10 m wide and 7 m deep: plank back and
side walls, stout posts along the open front carrying a beam, and a
mono-pitch tin roof. Inside are a workbench with a toolbox, a few oil drums
and a stack of tyres just inside the front; the rest is left clear for a tractor.

The seed varies the number of bays, which way the roof falls (to the back,
most often, or to the front), which side the workbench is on, the drums'
colours and the wall colour. The roof takes the scheme's roof colour.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/tractor_shed.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_farm as farm  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import prism  # noqa: E402

TYPE = "tractor_shed"
HITS_TO_COLLAPSE = 1  # small and flimsy
TRIANGLE_BUDGET = 400

WIDTH = 9.6
DEPTH = 6.2  # the walls; the roof oversails them to about 10 x 7
PLANK = 0.25
POST = 0.4
DRUMS = ("tomato", "cobalt", "sunny", "tangerine", "leaf")


def build(building_id, seed, scheme=None, collection=None):
    """Build one shed. Returns (empty, stats)."""
    rng = random.Random(seed)

    bays = (2, 3)[seed % 2]  # cycled, so neighbouring seeds always differ
    fall = rng.choice(["back", "back", "front"])
    bench_side = rng.choice([-1, 1])
    wall_colour = rng.choice(["wood", "wood", "doorBrown"])
    drums = rng.sample(DRUMS, 3)
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]
    frame_colour = "doorBrown" if wall_colour == "wood" else "wood"

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    hx = WIDTH / 2
    y_front, y_back = -DEPTH / 2, DEPTH / 2
    z_front, z_back = (4.3, 3.0) if fall == "back" else (3.1, 4.2)
    slope = (z_back - z_front) / DEPTH

    def roof_z(y):
        return z_front + (y - y_front) * slope

    edges = [-hx + WIDTH * k / bays for k in range(bays + 1)]
    back_face = farm.face("back", y_back)

    # --- the back wall, in two halves, each with a window ---
    backs = {}
    back_h = roof_z(y_back)
    for side in (-1, 1):
        xa, xb = sorted((0.0, side * hx))
        kit = Kit()
        kit.box((xa, y_back - PLANK, 0), (xb, y_back, back_h), wall_colour, sides={"-y": "interiorCream"}, skip=("-z",))
        um = -(xa + xb) / 2
        farm.window(kit, back_face, um - 0.7, um + 0.7, 1.4, 2.3)
        backs[side] = add(kit, "wall", "wood", 0)

    # --- the side walls, cut to the roof, with a cross brace outside ---
    sides = {}
    for side in (-1, 1):
        xa, xb = sorted((side * hx, side * (hx - PLANK)))
        kit = Kit()
        kit.extrude_x(
            [(y_front, 0), (y_back - PLANK, 0), (y_back - PLANK, roof_z(y_back - PLANK)), (y_front, z_front)],
            xa,
            xb,
            wall_colour,
            colours={1 if side < 0 else 0: "interiorCream"},
        )
        face = farm.face("left" if side < 0 else "right", side * hx)
        farm.x_brace(kit, face, -DEPTH / 2 + 0.3, DEPTH / 2 - 0.5, 0.2, 2.7, 0.03, frame_colour, width=0.26)
        sides[side] = add(kit, "wall", "wood", 0, collider="hull")

    # --- posts along the open front, and the beam they carry ---
    posts = {}
    for index, x in enumerate(edges[1:-1], start=1):
        kit = Kit()
        kit.box((x - POST / 2, y_front, 0), (x + POST / 2, y_front + POST, z_front - 0.35), frame_colour, skip=("-z", "+z"))
        kit.box((x - POST / 2 - 0.08, y_front - 0.08, 0), (x + POST / 2 + 0.08, y_front + POST + 0.08, 0.35), "stone", skip=("-z",))
        posts[index] = add(kit, "pillar", "wood", 0)
    holders = {0: sides[-1], bays: sides[1], **posts}

    kit = Kit()
    kit.box((-hx + PLANK, y_front, z_front - 0.35), (hx - PLANK, y_front + POST, z_front), frame_colour)
    beam = add(kit, "band", "wood", 1, supports=list(holders.values()))

    # --- the tin roof, a sheet for each bay ---
    over = 0.45
    ya, yb = y_front - over, y_back + over
    for k in range(bays):
        xa = edges[k] - (over if k == 0 else 0)
        xb = edges[k + 1] + (over if k == bays - 1 else 0)
        mid = (edges[k] + edges[k + 1]) / 2
        kit = Kit()
        farm.slab(
            kit,
            [(xa, ya, roof_z(ya)), (xb, ya, roof_z(ya)), (xb, yb, roof_z(yb)), (xa, yb, roof_z(yb))],
            0.22,
            pal["roof"],
            {2: "trimWhite", 4: "trimWhite"},
        )
        add(kit, "roof", "tin", 1, supports=(beam, backs[-1 if mid < 0 else 1], holders[k], holders[k + 1]), collider="hull")

    # --- the workbench along the back wall, with a toolbox ---
    bx = bench_side * (hx - 2.4)
    yb = y_back - PLANK
    kit = Kit()
    kit.box((bx - 1.7, yb - 1.0, 0.95), (bx + 1.7, yb, 1.15), "wood")
    for x in (bx - 1.55, bx + 1.3):
        kit.box((x, yb - 0.9, 0), (x + 0.25, yb - 0.1, 0.95), frame_colour, skip=("-z", "+z"))
    kit.box((bx - 1.2, yb - 0.75, 1.15), (bx - 0.2, yb - 0.25, 1.55), "tomato", skip=("-z",))
    kit.box((bx + 0.4, yb - 0.7, 1.15), (bx + 1.1, yb - 0.3, 1.4), "cobalt", skip=("-z",))
    add(kit, "detail", "wood", 0)

    # --- oil drums, and a stack of tyres ---
    dx = -bench_side * (hx - 1.3)
    kit = Kit()
    for (ox, oy), colour in zip(((0.0, -2.2), (bench_side * 1.05, -2.45), (bench_side * 0.5, -1.4)), drums):
        prism(kit, (dx + ox, oy), 0, 1.25, 0.48, 0.48, 6, colour, bottom=False, top_colour="trimWhite")
    add(kit, "detail", "tin", 0, collider="hull")

    kit = Kit()
    tx = bench_side * (hx - 1.3)
    prism(kit, (tx, -2.4), 0, 0.45, 0.75, 0.75, 6, "tyre", bottom=False)
    prism(kit, (tx + 0.08, -2.35), 0.45, 0.9, 0.75, 0.75, 6, "tyre", bottom=False, top_colour="stone")
    add(kit, "detail", "rubber", 0, collider="hull")

    return building.finish(look=f"bays={bays} falls-{fall} bench{bench_side:+d} {wall_colour}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(15, 13))


if __name__ == "__main__":
    previews()
