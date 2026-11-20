"""Boathouse generator: the wizard school's boathouse by the lake.

A small boathouse about 7 m wide and 10 m deep: a grey stone base with
timber walls above, under a steep dark slate roof with a little spire on the
ridge. The front gable end (facing -Y, out over the water) has a big arched
water door, with lake water inside and a rowing boat nosing out. Small warm
windows down the sides and a door at the back; a plank jetty runs along one
side on some seeds.

The front is two pieces (a jamb and half the arch each), each side two
pieces and the back one, all on the ground. The timber gables rest on the
walls under them, the roof is a slab per side on that side's walls, and the
spire rests on both roof slabs.

The seed varies the size, the arch (round or pointed), the timber colour,
the slate, the spire (square or six-sided), the jetty and the boat.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/boathouse.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_castle2 as castle  # noqa: E402
from lib import shapes_wizard as wiz  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import round_window  # noqa: E402
from lib.shapes_parkcastle import Frame, fquad  # noqa: E402

TYPE = "boathouse"
HITS_TO_COLLAPSE = 1  # small building
TRIANGLE_BUDGET = 400

WALL = 0.4
STONE_H = 2.2
OVERHANG = 0.4
VERGE = 0.4


def build(building_id, seed, scheme=None, collection=None):
    """Build one boathouse. Returns (empty, stats)."""
    rng = random.Random(seed)

    width = rng.choice([6.6, 7.0, 7.4])
    depth = rng.choice([9.4, 10.0])
    wall_h = rng.choice([4.4, 4.8])
    pitch = rng.choice([54, 58])
    head = ("round", "pointed")[seed % 2]  # alternated, so neighbouring seeds differ
    timber = rng.choice(["wood", "wood", "doorBrown"])
    slate = rng.choice(wiz.SLATES)
    spire_sides = rng.choice([4, 6])
    jetty = rng.choice([None, "left", "right", "right"])
    boat = rng.choice(["tomato", "cobalt", "sunny", None])
    gold = rng.choice(wiz.GOLDS)
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    hx, hy = width / 2, depth / 2
    rise = hx * math.tan(math.radians(pitch))
    ridge = wall_h + rise
    slope = rise / hx
    eave_z = wall_h - slope * OVERHANG
    trim = "trimWhite" if timber == "doorBrown" else "doorBrown"

    def two_tone(kit, lo, hi):
        """A wall block: stone up to STONE_H, timber above, cream inside."""
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        kit.box((x0, y0, z0), (x1, y1, STONE_H), "stone", skip=("-z", "+z"))
        kit.box((x0, y0, STONE_H), (x1, y1, z1), timber, skip=("-z",))

    # --- the front: a jamb and half the water arch on each side ---
    x_open = min(2.1, hx - 1.0)
    spring = 2.2
    crown = wall_h - 0.4
    front = []
    for side in (-1, 1):
        kit = Kit()
        xa, xb = sorted((side * x_open, side * hx))
        kit.box((xa, -hy, 0), (xb, -hy + WALL, spring), "stone", skip=("-z",))
        castle.arch_half(kit, side, x_open, hx, -hy, -hy + WALL, spring, crown, wall_h, timber, trim="stone", steps=3, pointed=head == "pointed", ring=0.45)
        front.append(add(kit, "wall", "stone", 0, collider="hull"))

    # --- the sides: two pieces each, with small warm windows ---
    sides = {-1: [], 1: []}
    for sx in (-1, 1):
        frame = Frame((sx * hx, 0, 0), 0 if sx > 0 else 180)
        for k in range(2):
            ya, yb = -hy + WALL + k * (depth - 2 * WALL) / 2, -hy + WALL + (k + 1) * (depth - 2 * WALL) / 2
            xa, xb = sorted((sx * hx, sx * (hx - WALL)))
            kit = Kit()
            two_tone(kit, (xa, ya, 0), (xb, yb, wall_h))
            u = ((ya + yb) / 2) * (1 if sx > 0 else -1)
            wiz.lancet(kit, frame, u, STONE_H + 0.5, 0.6, 1.3, glass=wiz.LIT, shine=None, rim=0.1, surround=trim)
            sides[sx].append(add(kit, "wall", "wood", 0))

    # --- the back, with a door, and the lake water inside ---
    kit = Kit()
    two_tone(kit, (-hx, hy - WALL, 0), (hx, hy, wall_h))
    back = Frame((0, hy, 0), 90)
    fquad(kit, back, -0.6, 0.6, 0, 2.1, 0.04, "doorBrown")
    fquad(kit, back, -0.75, 0.75, 2.1, 2.3, 0.04, trim)
    kit.poly([(-hx + WALL, -hy, 0.03), (hx - WALL, -hy, 0.03), (hx - WALL, hy - WALL, 0.03), (-hx + WALL, hy - WALL, 0.03)], (0, 0, 1), "water")
    back_id = add(kit, "wall", "wood", 0)

    # --- the gables ---
    for y_out, holders, facing in ((-hy, front, -1), (hy, [back_id], 1)):
        y0, y1 = sorted((y_out, y_out - facing * WALL))
        kit = Kit()
        kit.extrude_y([(-hx, wall_h), (hx, wall_h), (0, ridge)], y0, y1, timber)
        round_window(kit, (0, y_out, wall_h + rise * 0.38), (0, facing, 0), min(0.7, rise * 0.18), trim, glass=wiz.LIT)
        add(kit, "wall", "wood", 1, supports=holders, collider="hull")

    # --- the steep roof, a slab a side ---
    roofs = []
    for sx in (-1, 1):
        eave_x = sx * (hx + OVERHANG)
        kit = Kit()
        kit.slab([(eave_x, -hy - VERGE, eave_z), (eave_x, hy + VERGE, eave_z), (0, hy + VERGE, ridge), (0, -hy - VERGE, ridge)], 0.3, slate)
        roofs.append(add(kit, "roof", "tile", 1, supports=sides[sx], collider="hull"))

    # --- a little spire on the ridge ---
    y = -hy * 0.35
    z = ridge - 0.5
    kit = Kit()
    if spire_sides == 4:
        kit.box((-0.5, y - 0.5, z), (0.5, y + 0.5, z + 1.4), timber, skip=("-z", "+z"))
    else:
        wiz.drum(kit, 0.6, 0.6, z, z + 1.4, timber, sides=6, cy=y, cap_top=False, cap_bottom=False)
    r = 0.78 if spire_sides == 4 else 0.75
    wiz.cone_part(kit, r, 0.0, z + 1.4, z + 4.6, slate, spire_sides, cy=y)
    wiz.finial(kit, 0, y, z + 4.4, size=0.6, colour=gold, stem=False)
    add(kit, "roof", "tile", 2, supports=roofs, collider="hull")

    # --- a plank jetty along one side, on posts ---
    if jetty:
        sx = -1 if jetty == "left" else 1
        x0, x1 = sorted((sx * (hx + 0.1), sx * (hx + 1.4)))
        kit = Kit()
        kit.box((x0, -hy - 2.2, 0.55), (x1, hy - 1.0, 0.75), "wood", sides={"-z": "doorBrown"})
        for py in (-hy - 1.9, -hy + 1.4):
            px = (x0 + x1) / 2
            kit.box((px - 0.14, py - 0.14, 0), (px + 0.14, py + 0.14, 0.55), "doorBrown", skip=("-z", "+z"))
        add(kit, "detail", "wood", 0)

    # --- a rowing boat nosing out of the water door ---
    if boat:
        kit = Kit()
        y0, y1 = -hy - 1.3, -hy + 2.4
        section = [(-0.55, 0.05), (0.55, 0.05), (0.85, 0.6), (-0.85, 0.6)]
        kit.extrude_y(section, y0 + 0.6, y1, boat, colours={1: boat})
        kit.convex([[(-0.85, y0 + 0.6, 0.6), (0.85, y0 + 0.6, 0.6), (0.55, y0 + 0.6, 0.05), (-0.55, y0 + 0.6, 0.05)], [(0, y0, 0.65), (0.85, y0 + 0.6, 0.6), (0.55, y0 + 0.6, 0.05)], [(0, y0, 0.65), (-0.55, y0 + 0.6, 0.05), (-0.85, y0 + 0.6, 0.6)], [(0, y0, 0.65), (-0.85, y0 + 0.6, 0.6), (0.85, y0 + 0.6, 0.6)], [(0, y0, 0.65), (0.55, y0 + 0.6, 0.05), (-0.55, y0 + 0.6, 0.05)]], boat)
        kit.box((-0.6, (y0 + y1) / 2 - 0.2, 0.45), (0.6, (y0 + y1) / 2 + 0.2, 0.62), "wood", skip=("-z",))
        add(kit, "detail", "wood", 0, collider="hull")

    return building.finish(look=f"{width}x{depth} wall{wall_h} pitch{pitch} {head}/{timber}/{slate} spire{spire_sides} jetty-{jetty} boat-{boat}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(14, 18))


if __name__ == "__main__":
    previews()
