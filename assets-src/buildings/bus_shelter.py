"""Bus shelter generator.

A glass-and-tin bus shelter about 5 x 2 m: glass panels between chunky posts
along the back and the ends, a bright tin roof, a bench inside and a sign
pole at one corner (a coloured disc, never words). The seed varies the
length, the roof (flat, sloping or arched), whether an end is left open, the
bench and the side the sign pole stands on.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/bus_shelter.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import flat  # noqa: E402
from lib.shapes_props import prism  # noqa: E402

TYPE = "bus_shelter"
HITS_TO_COLLAPSE = 1  # small
TRIANGLE_BUDGET = 400

POST = 0.24
GLASS = "glassTint"


def build(building_id, seed, scheme=None, collection=None):
    """Build one bus shelter. Returns (empty, stats)."""
    rng = random.Random(seed)

    # --- the shelter's character ---
    roof_form = ("arched", "flat", "sloping")[seed % 3]  # cycled, so neighbouring seeds always differ
    width = rng.choice([4.6, 5.0, 5.4])
    depth = rng.choice([1.8, 2.0])
    height = rng.choice([2.5, 2.7])
    open_end = rng.choice([0, 0, -1, 1])  # which end has no glass (0: neither)
    sign_side = rng.choice([-1, 1])
    bench_style = rng.choice(["plank", "seats"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]
    frame = pal["wall"]
    roof = pal["roof"]
    accent = pal["door"] if pal["door"] != "doorBrown" else "sunny"

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    x0, x1 = -width / 2, width / 2
    front, back = -depth / 2, depth / 2

    def post(kit, x, y):
        kit.box((x - POST / 2, y - POST / 2, 0), (x + POST / 2, y + POST / 2, height), frame, skip=("-z", "+z"))

    # --- the back: two glass panels between three posts ---
    walls = []
    y = back - POST / 2
    for i, (a, b) in enumerate(((x0, 0.0), (0.0, x1))):
        kit = Kit()
        kit.box((a + POST / 2, y - 0.05, 0.3), (b - POST / 2, y + 0.05, height - 0.25), GLASS)
        w = b - a
        for side, yy in ((-1, y - 0.07), (1, y + 0.07)):
            kit.poly(
                [(a + w * 0.3, yy, 0.9), (a + w * 0.42, yy, 0.9), (a + w * 0.66, yy, 1.9), (a + w * 0.54, yy, 1.9)],
                (0, side, 0),
                "windowShine",
            )
        post(kit, a + POST / 2 if i == 0 else b - POST / 2, y)
        if i == 0:
            post(kit, 0.0, y)
        walls.append(add(kit, "wall", "glass", 0))

    # --- the ends: a glass panel and a front post each (one end may be open) ---
    for sign in (-1, 1):
        x = sign * (width / 2 - POST / 2)
        kit = Kit()
        post(kit, x, front + POST / 2)
        if sign != open_end:
            kit.box((x - 0.05, front + POST, 0.3), (x + 0.05, back - POST, height - 0.25), GLASS)
        walls.append(add(kit, "wall", "glass", 0))

    # --- roof ---
    out = 0.3
    kit = Kit()
    if roof_form == "flat":
        kit.box((x0 - out, front - out - 0.2, height), (x1 + out, back + out, height + 0.22), roof)
        kit.box((x0 - out, front - out - 0.2, height - 0.12), (x1 + out, front - out - 0.05, height), "trimWhite", skip=("+z",))
        collider = "box"
    elif roof_form == "sloping":
        kit.extrude_x(
            [(front - out - 0.3, height + 0.55), (back + out, height), (back + out, height + 0.2), (front - out - 0.3, height + 0.75)],
            x0 - out,
            x1 + out,
            roof,
        )
        kit.extrude_x([(front, height), (back, height), (front, height + 0.45)], x0 + 0.02, x1 - 0.02, frame)
        collider = "hull"
    else:
        ya, yb = front - out - 0.1, back + out
        ym = (ya + yb) / 2
        q = (yb - ya) / 4
        kit.extrude_x(
            [(ya, height), (yb, height), (yb, height + 0.2), (ym + q * 0.9, height + 0.75), (ym - q * 0.9, height + 0.75), (ya, height + 0.2)],
            x0 - out,
            x1 + out,
            roof,
            colours={0: "trimWhite", 1: "trimWhite"},
        )
        collider = "hull"
    add(kit, "roof", "tin", 1, supports=walls, collider=collider)

    # --- bench ---
    bx0, bx1 = x0 + 0.7, x1 - 0.7
    by0, by1 = back - POST - 0.75, back - POST - 0.15
    kit = Kit()
    if bench_style == "plank":
        kit.box((bx0, by0, 0.5), (bx1, by1, 0.66), "wood")
        for x in (bx0 + 0.35, bx1 - 0.35):
            kit.box((x - 0.12, by0 + 0.1, 0), (x + 0.12, by1 - 0.1, 0.5), frame, skip=("-z", "+z"))
    else:
        kit.box((bx0, by0 + 0.2, 0.36), (bx1, by0 + 0.4, 0.5), frame, skip=("-z",))
        seats = 3
        step = (bx1 - bx0) / seats
        for i in range(seats):
            kit.box((bx0 + i * step + 0.1, by0, 0.5), (bx0 + (i + 1) * step - 0.1, by1, 0.66), accent if i % 2 == 0 else "trimWhite", skip=("-z",))
        for x in (bx0 + 0.3, bx1 - 0.3):
            kit.box((x - 0.1, by0 + 0.2, 0), (x + 0.1, by0 + 0.4, 0.36), frame, skip=("-z", "+z"))
    add(kit, "detail", "wood", 0)

    # --- sign pole: a disc on a post, at the kerb end ---
    px = sign_side * (width / 2 + 0.75)
    py = front - 0.1
    pole_h = 3.5
    kit = Kit()
    prism(kit, (px, py), 0, 0.3, 0.32, 0.26, 6, "tyre")
    prism(kit, (px, py), 0.3, pole_h, 0.16, 0.16, 6, "tyre", bottom=False)
    centre = (px, py, pole_h - 0.55)
    prism(kit, (px, centre[2]), py - 0.17, py + 0.17, 0.66, 0.66, 8, accent, axis="y")
    for normal in ((0, -1, 0), (0, 1, 0)):
        flat(kit, centre, normal, [(-0.42, -0.13), (0.42, -0.13), (0.42, 0.13), (-0.42, 0.13)], "trimWhite", lift=0.2)
    add(kit, "detail", "tin", 0, collider="hull")

    return building.finish(look=f"{roof_form}/{width:g}x{depth:g}/h{height:g}/open{open_end:+d}/bench-{bench_style}/sign{sign_side:+d}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(9, 8))


if __name__ == "__main__":
    previews()
