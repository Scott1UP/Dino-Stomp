"""Great hall generator: the long feasting hall of the wizard school.

A long grey stone hall, about 12 m by 26 m and 10 m to the eaves, under a
very steep dark slate roof. A row of tall pointed windows glows warm down
both long sides, with stepped buttresses between the bays, each topped by a
little slate pinnacle above the eaves. The front gable end has a big pointed
door with a round rose window above it; the back gable has a tall window. A
slender turret with a spirelet stands at each corner.

The long walls are split into bays, one piece per bay per storey (two
storeys of about 5 m); each tall window runs from the lower piece into the
upper one. The roof is one slab per bay on each side, resting on the upper
bay below it.

The seed varies the number of bays, the width, the wall height, the roof
pitch, the slate, the corner turrets, a slender spirelet (fleche) on the
ridge, the rose window's centre and the door.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/great_hall.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib import shapes_wizard as wiz  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_parkcastle import Frame, fbox  # noqa: E402

TYPE = "great_hall"
HITS_TO_COLLAPSE = 3  # big landmark
TRIANGLE_BUDGET = 1800

WALL = 0.6
OVERHANG = 0.3
VERGE = 0.45
ROOF_THICKNESS = 0.35


def build(building_id, seed, scheme=None, collection=None):
    """Build one great hall. Returns (empty, stats)."""
    rng = random.Random(seed)

    bays, bay_len = rng.choice([(5, 4.6), (6, 4.0), (6, 4.2), (5, 5.0)])
    width = rng.choice([11.0, 12.0, 12.5])
    wall_h = rng.choice([9.5, 10.0, 10.5])
    pitch = rng.choice([56, 60, 63])  # degrees: very steep
    slate = rng.choice(wiz.SLATES)
    turrets = rng.choice(["spirelet", "spirelet", "pinnacle"])
    fleche = rng.random() < 0.6
    window_w = rng.choice([1.3, 1.5])
    rose_centre = rng.choice(["tomato", "cobalt", "sunny"])
    gold = rng.choice(wiz.GOLDS)
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    hx = width / 2
    length = bays * bay_len
    hy = length / 2
    mid_h = round(wall_h / 2, 2)
    rise = hx * math.tan(math.radians(pitch))
    ridge = wall_h + rise
    slope = rise / hx
    eave_z = wall_h - slope * OVERHANG
    sill = 1.8

    def window_pair(lower_kit, upper_kit, frame, u):
        glass, shine = wiz.pane(rng, 0.1)
        wiz.window_shaft(lower_kit, frame, u, sill, mid_h, window_w, glass=glass)
        top = wall_h - 1.0 - mid_h
        wiz.lancet(upper_kit, frame, u, mid_h, window_w, top, glass=glass, shine=shine, sill=False)

    # --- the long sides: one piece per bay per storey, a buttress and pinnacle at each bay's end ---
    uppers = {}  # (sign, bay) -> upper module
    lowers = []
    for sign in (-1, 1):
        frame = Frame((sign * hx, 0, 0), 0 if sign > 0 else 180)
        direction = 1 if sign > 0 else -1  # u = y * direction
        for b in range(bays):
            ya, yb = -hy + b * bay_len, -hy + (b + 1) * bay_len
            ua, ub = sorted((ya * direction, yb * direction))
            um = (ua + ub) / 2
            lower, upper = Kit(), Kit()
            # The end walls run between the long walls, so the long walls take the corners.
            fbox(lower, frame, (ua, -WALL, 0), (ub, 0, mid_h), "stone", skip=("-z",), sides={"-v": "interiorCream"})
            fbox(upper, frame, (ua, -WALL, mid_h), (ub, 0, wall_h), "stone", sides={"-v": "interiorCream"})
            window_pair(lower, upper, frame, um)
            buttress = b < bays - 1
            if buttress:
                ue = yb * direction
                fbox(lower, frame, (ue - 0.4, 0, 0), (ue + 0.4, 1.15, mid_h), "stone", skip=("-v", "-z"), sides={"+z": "trimWhite"})
                fbox(upper, frame, (ue - 0.32, 0, mid_h), (ue + 0.32, 0.95, wall_h - 0.2), "stone", skip=("-v", "-z"))
                px, py, _ = frame.at(ue, 0.62, 0)
                wiz.pinnacle(upper, px, py, wall_h - 0.2, 0.34, 1.5, 2.6, "stone", "stone", gold)
            low = add(lower, "wall", "stone", 0)
            lowers.append(low)
            uppers[(sign, b)] = add(upper, "wall", "stone", 1, supports=(low,))

    # --- the gable ends: three pieces a storey, and the gable above ---
    end_tops = {}
    for side, y_out in (("front", -hy), ("back", hy)):
        facing = -1 if side == "front" else 1
        frame = Frame((0, y_out, 0), -90 if side == "front" else 90)
        inner = hx - WALL
        third = inner / 3
        cuts = [(-inner, -third), (-third, third), (third, inner)]
        tops = []
        for k, (ua, ub) in enumerate(cuts):
            lower, upper = Kit(), Kit()
            fbox(lower, frame, (ua, -WALL, 0), (ub, 0, mid_h), "stone", skip=("-z",), sides={"-v": "interiorCream"})
            fbox(upper, frame, (ua, -WALL, mid_h), (ub, 0, wall_h), "stone", sides={"-v": "interiorCream"})
            um = (ua + ub) / 2
            if k == 1 and side == "front":
                wiz.pointed_door(lower, frame, 0, 2.6, min(4.4, mid_h - 0.4), "doorBrown", rim=0.3)
                wiz.rose_window(upper, frame, 0, mid_h + (wall_h - mid_h) * 0.5, 1.55, second=rose_centre)
            elif k == 1:
                window_pair(lower, upper, frame, 0)
            else:
                glass, _ = wiz.pane(rng, 0.0)
                wiz.lancet(lower, frame, um, sill, 0.9, mid_h - sill - 0.6, glass=glass, shine=None, rim=0.12)
                wiz.lancet(upper, frame, um, mid_h + 0.8, 0.9, wall_h - mid_h - 2.2, glass=glass, shine=None, rim=0.12)
            low = add(lower, "wall", "stone", 0)
            lowers.append(low)
            tops.append(add(upper, "wall", "stone", 1, supports=(low,)))
        # The gable: a stone triangle with a tall slit window, and a pinnacle at its apex.
        y0, y1 = sorted((y_out, y_out - facing * WALL))
        kit = Kit()
        kit.extrude_y([(-hx, wall_h), (hx, wall_h), (0, ridge)], y0, y1, "stone")
        wiz.lancet(kit, frame, 0, wall_h + 0.6, 0.8, rise * 0.45, glass=wiz.LIT, shine=None, rim=0.12)
        kit.box((-0.45, y0 - 0.1, ridge - 0.6), (0.45, y1 + 0.1, ridge + 0.9), "stone", skip=("-z",))
        wiz.finial(kit, 0, (y0 + y1) / 2, ridge + 0.9, size=1.1, colour=gold)
        end_tops[side] = add(kit, "wall", "stone", 2, supports=tops, collider="hull")

    # --- the steep roof: a slab per bay each side ---
    roofs = {}
    for sign in (-1, 1):
        eave_x = sign * (hx + OVERHANG)
        for b in range(bays):
            ya, yb = -hy + b * bay_len, -hy + (b + 1) * bay_len
            if b == 0:
                ya -= VERGE
            if b == bays - 1:
                yb += VERGE
            kit = Kit()
            kit.slab([(eave_x, ya, eave_z), (eave_x, yb, eave_z), (0, yb, ridge), (0, ya, ridge)], ROOF_THICKNESS, slate)
            roofs[(sign, b)] = add(kit, "roof", "tile", 2, supports=(uppers[(sign, b)],), collider="hull")

    # --- a slender spirelet on the ridge ---
    if fleche:
        b = bays // 2
        ym = -hy + (b + 0.5) * bay_len
        z = ridge - 0.9
        kit = Kit()
        wiz.drum(kit, 0.75, 0.75, z, z + 2.2, "stone", sides=6, cy=ym)
        f = shapes.facet_frame(0, 0.75, sides=6, cy=ym)
        wiz.lancet(kit, f, 0, z + 1.1, 0.4, 0.9, rim=0.0, surround=None, glass=wiz.LIT, shine=None)
        wiz.cone_part(kit, 0.95, 0.0, z + 2.2, z + 7.0, slate, 6, cy=ym)
        wiz.finial(kit, 0, ym, z + 6.8, size=0.8, colour=gold, stem=False)
        add(kit, "roof", "tile", 3, supports=(roofs[(-1, b)], roofs[(1, b)]), collider="hull")

    # --- a slender turret at each corner ---
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * (hx + 0.2), sy * (hy + 0.2)
            r = 0.95
            kit = Kit()
            wiz.drum(kit, r, r, 0, mid_h, "stone", sides=6, cx=cx, cy=cy, top="interiorCream", cap_bottom=False)
            low = add(kit, "wall", "stone", 0, collider="hull")
            top_z = wall_h + 1.6
            kit = Kit()
            wiz.drum(kit, r, r, mid_h, top_z, "stone", sides=6, cx=cx, cy=cy, bottom="interiorCream", cap_top=False)
            wiz.band_ring(kit, r + 0.18, top_z - 0.3, top_z, sides=6, cx=cx, cy=cy)
            if turrets == "spirelet":
                wiz.cone_part(kit, r + 0.12, 0.0, top_z, top_z + 4.6, slate, 6, cx=cx, cy=cy)
                wiz.finial(kit, cx, cy, top_z + 4.4, size=0.6, colour=gold, stem=False)
            else:
                wiz.pinnacle(kit, cx, cy, top_z, 0.5, 0.9, 3.0, "stone", slate, gold)
            add(kit, "wall", "stone", 1, supports=(low,), collider="hull")

    # --- steps up to the door ---
    kit = Kit()
    kit.box((-2.4, -hy - 1.4, 0), (2.4, -hy, 0.22), "stone", skip=("-z",))
    kit.box((-1.9, -hy - 0.7, 0.22), (1.9, -hy, 0.44), "trimWhite", skip=("-z",))
    add(kit, "detail", "stone", 0)

    return building.finish(
        look=f"{width}x{length:.1f} bays{bays} wall{wall_h} pitch{pitch} ridge{ridge:.1f} {slate} turrets-{turrets} fleche-{fleche}"
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(22, 36))


if __name__ == "__main__":
    previews()
