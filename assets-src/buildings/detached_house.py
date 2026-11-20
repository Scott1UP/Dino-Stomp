"""Detached family house generator.

A two-storey house about 10 x 7 m with a garage on one side: a hipped roof,
or a gabled one with a cross gable facing the street, a chimney, a porch
over the front door and a bright garage door. The seed varies which side the
garage is on, how far back it sits and its roof (flat, lean-to or gabled),
the main roof and its pitch, the chimney (up the end wall or on the ridge),
the porch, the windows and their shutters.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/detached_house.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import round_window  # noqa: E402
from lib.shapes_town2 import (  # noqa: E402
    cross_gable,
    door,
    flatten,
    floor_slab,
    roof_gabled,
    roof_hipped,
    shell_storey,
    split,
    wall_colours,
    window,
)

TYPE = "detached_house"
HITS_TO_COLLAPSE = 2  # medium building
TRIANGLE_BUDGET = 900

WALL = 0.35
OVERHANG = 0.45


def build(building_id, seed, scheme=None, collection=None):
    """Build one house. Returns (empty, stats)."""
    rng = random.Random(seed)

    # --- the house's character ---
    roof_form = ("hipped", "cross")[seed % 2]  # cycled, so neighbouring seeds always differ
    garage_side = (-1, 1, 1, -1)[seed % 4]
    main_w = rng.choice([7.0, 7.5, 8.0])
    depth = rng.choice([6.4, 6.8])
    storey = rng.choice([2.9, 3.1])
    rise = rng.choice([2.4, 2.9, 3.3])
    garage_w = rng.choice([3.2, 3.6])
    garage_d = rng.choice([5.0, 5.6])
    garage_back = rng.choice([0.0, 0.8])
    garage_roof = rng.choice(["flat", "lean", "gable"])
    chimney_style = rng.choice(["end", "ridge"])
    porch = rng.choice(["flat", "gabled", "lean"])
    window_style = rng.choice(["square", "wide", "tall"])
    shutters = rng.random() < 0.5
    door_far = rng.random() < 0.5  # the front door in the bay away from the garage
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]
    accent = pal["door"] if pal["door"] != "doorBrown" else pal["roof"]
    colours = wall_colours(pal)

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    total_w = main_w + garage_w
    if garage_side < 0:
        gx0 = -total_w / 2
        mx0, mx1 = gx0 + garage_w, total_w / 2
    else:
        mx0, mx1 = -total_w / 2, total_w / 2 - garage_w
        gx0 = mx1
    gx1 = gx0 + garage_w
    front, back = -depth / 2, depth / 2
    bounds = (mx0, mx1, front, back)
    eaves = storey * 2
    mid_x = (mx0 + mx1) / 2
    far = "left" if garage_side > 0 else "right"  # the side wall away from the garage
    near = "right" if garage_side > 0 else "left"

    win_w, win_h, sill = {"square": (1.5, 1.4, 0.95), "wide": (1.9, 1.3, 1.0), "tall": (1.2, 1.8, 0.6)}[window_style]

    bays = {
        "front": split(mx0, mx1, main_w / 2),
        "back": split(mx0, mx1, main_w / 2),
        "left": [(front + WALL, back - WALL)],
        "right": [(front + WALL, back - WALL)],
    }
    door_bay = (0 if garage_side > 0 else 1) if door_far else (1 if garage_side > 0 else 0)
    door_x = sum(bays["front"][door_bay]) / 2

    def openings_for(s):
        z = s * storey

        def openings(side, i, a, b):
            mid = (a + b) / 2
            if side == "front":
                return [door(mid, 0)] if (s == 0 and i == door_bay) else [window(mid, z, win_w, win_h, sill)]
            if side == "back":
                return [door(mid, 0)] if (s == 0 and i != door_bay) else [window(mid, z, win_w, win_h, sill)]
            if side == near:
                return [] if s == 0 else [window(mid, z, 1.2, win_h, sill)]
            # The far side keeps its window to the front, clear of the chimney stack.
            return [window(a + (b - a) * 0.27, z, 1.2, win_h, sill)]

        return openings

    def extras_for(s):
        z = s * storey

        def extra(kit, side, i, a, b):
            if side != "front":
                return
            mid = (a + b) / 2
            if s == 0 and i == door_bay:
                kit.box((mid - 0.9, front - 1.2, 0), (mid + 0.9, front, 0.2), "stone", skip=("-z", "+y"))
            elif shutters:
                for sx in (-1, 1):
                    xa, xb = sorted((mid + sx * (win_w / 2 + 0.08), mid + sx * (win_w / 2 + 0.5)))
                    kit.box((xa, front - 0.08, z + sill - 0.05), (xb, front, z + sill + win_h + 0.05), accent, skip=("+y",))

        return extra

    walls0 = shell_storey(add, bounds, 0, storey, 0, colours, openings=openings_for(0), extra=extras_for(0), bays=bays)
    floor_slab(add, bounds, storey, 1, flatten(walls0))
    walls1 = shell_storey(add, bounds, storey, eaves, 1, colours, below=walls0, openings=openings_for(1), extra=extras_for(1), bays=bays)

    # --- main roof ---
    front_pieces = list(zip(bays["front"], walls1["front"]))
    back_pieces = list(zip(bays["back"], walls1["back"]))
    ends = {-1: walls1["left"], 1: walls1["right"]}
    ridge = eaves + rise
    slope = rise / (depth / 2)
    if roof_form == "hipped":
        roof = roof_hipped(add, bounds, eaves, rise, pal["roof"], 2, front_pieces, back_pieces, ends, overhang=OVERHANG)
        chimney_holders = roof["front"] + roof["back"]
    else:

        def gable_extra(kit, sign):
            x = mx0 if sign < 0 else mx1
            round_window(kit, (x, 0, eaves + rise * 0.36), (sign, 0, 0), min(0.65, rise * 0.22), pal["trim"])

        roof = roof_gabled(
            add, bounds, eaves, rise, pal["roof"], 2, front_pieces, back_pieces, ends, pal["wall"], overhang=OVERHANG, gable_extra=gable_extra
        )
        chimney_holders = roof["front"] + roof["back"]
        # The cross gable stands over the bay without the front door.
        g = 1 - door_bay
        ga, gb = bays["front"][g]
        g_mid = (ga + gb) / 2
        g_w = (gb - ga) * 0.9
        g_h = min(g_w / 2 * 0.95, rise * 0.88)
        face = front - OVERHANG - 0.05
        base = eaves - slope * OVERHANG - 0.05
        kit = Kit()
        cross_gable(
            kit, g_mid, g_w, base, g_h, face, min(front + g_h / slope + 0.4, 0), pal["wall"], pal["roof"], depth=OVERHANG + 0.05 + WALL
        )
        round_window(kit, (g_mid, face, base + g_h * 0.36), (0, -1, 0), min(0.6, g_h * 0.3), pal["trim"])
        add(kit, "roof", "tile", 2, supports=(walls1["front"][g],), collider="hull")

    # --- chimney ---
    far_sign = -garage_side
    kit = Kit()
    if chimney_style == "end":
        x_wall = mx0 if far_sign < 0 else mx1
        xa, xb = sorted((x_wall, x_wall + far_sign * 0.6))
        y_mid = depth * 0.2
        if roof_form == "hipped":
            top_z = eaves + 2.2
        else:
            top_z = ridge - slope * y_mid + 1.3
        shoulder = eaves * 0.7
        kit.extrude_x(
            [(y_mid - 0.9, 0), (y_mid + 0.9, 0), (y_mid + 0.9, shoulder), (y_mid + 0.5, shoulder + 0.7), (y_mid - 0.5, shoulder + 0.7)],
            xa,
            xb,
            pal["wall"],
        )
        kit.box((xa, y_mid - 0.5, shoulder + 0.7), (xb, y_mid + 0.5, top_z), pal["wall"], skip=("-z", "+z"))
        kit.box((xa - 0.1, y_mid - 0.6, top_z), (xb + 0.1, y_mid + 0.6, top_z + 0.22), pal["trim"])
        kit.box((xa + 0.12, y_mid - 0.2, top_z + 0.22), (xb - 0.12, y_mid + 0.2, top_z + 0.65), "tangerine", skip=("-z",))
        add(kit, "detail", "plaster", 0, collider="hull")
    else:
        cx = mid_x + far_sign * (0.3 if roof_form == "hipped" else main_w * 0.22)
        kit.box((cx - 0.6, -0.5, ridge - 0.7), (cx + 0.6, 0.5, ridge + 1.4), pal["wall"], skip=("-z", "+z"))
        kit.box((cx - 0.72, -0.62, ridge + 1.4), (cx + 0.72, 0.62, ridge + 1.62), pal["trim"])
        for dx in (-0.28, 0.28):
            kit.box((cx + dx - 0.17, -0.17, ridge + 1.62), (cx + dx + 0.17, 0.17, ridge + 2.05), "tangerine", skip=("-z",))
        add(kit, "detail", "plaster", 3, supports=chimney_holders)

    # --- porch: a little roof on two posts ---
    out = 1.3
    kit = Kit()
    for side in (-1, 1):
        px = door_x + side * 0.9
        kit.box((px - 0.12, front - out + 0.05, 0), (px + 0.12, front - out + 0.29, 2.5), pal["trim"], skip=("-z", "+z"))
    if porch == "flat":
        kit.box((door_x - 1.15, front - out - 0.15, 2.5), (door_x + 1.15, front, 2.74), pal["roof"], skip=("+y",))
    elif porch == "gabled":
        kit.extrude_y([(door_x - 1.25, 2.5), (door_x + 1.25, 2.5), (door_x, 3.4)], front - out - 0.2, front, pal["roof"], colours={0: pal["trim"]})
    else:
        kit.extrude_x(
            [(front - out - 0.2, 2.45), (front, 3.0), (front, 3.2), (front - out - 0.2, 2.65)],
            door_x - 1.2,
            door_x + 1.2,
            pal["roof"],
        )
    add(kit, "detail", "wood", 0, supports=(walls0["front"][door_bay],), collider="box" if porch == "flat" else "hull")

    # --- the garage, with its bright door ---
    gy0 = front + garage_back
    gy1 = gy0 + garage_d
    g_h = 2.8
    g_bounds = (gx0, gx1, gy0, gy1)
    g_mid = (gx0 + gx1) / 2
    door_w = garage_w - 0.9
    g_colours = wall_colours(pal, door=accent)

    def garage_openings(side, i, a, b):
        if side == "front":
            return [door((a + b) / 2, 0, door_w, 2.2)]
        if side == "back":
            return [window((a + b) / 2, 0, 1.3, 1.2, 1.0)]
        return [window((a + b) / 2, 0, 1.3, 1.2, 1.0)] if garage_back else []

    def garage_extra(kit, side, i, a, b):
        if side != "front":
            return
        y = gy0 + 0.1
        for z in (0.55, 1.1, 1.65):  # the panel lines across an up-and-over door
            kit.poly([(g_mid - door_w / 2, y, z), (g_mid + door_w / 2, y, z), (g_mid + door_w / 2, y, z + 0.1), (g_mid - door_w / 2, y, z + 0.1)], (0, -1, 0), pal["trim"])

    g_bays = {"front": [(gx0, gx1)], "back": [(gx0, gx1)], "left": [(gy0 + WALL, gy1 - WALL)], "right": [(gy0 + WALL, gy1 - WALL)]}
    g_walls = shell_storey(
        add, g_bounds, 0, g_h, 0, g_colours, openings=garage_openings, extra=garage_extra, bays=g_bays, skip=(far,)  # the house wall is the garage's inside wall
    )
    x_out = gx0 if garage_side < 0 else gx1
    x_in = gx1 if garage_side < 0 else gx0
    kit = Kit()
    if garage_roof == "flat":
        kit.box((min(x_out + garage_side * 0.25, x_in), gy0 - 0.25, g_h), (max(x_out + garage_side * 0.25, x_in), gy1 + 0.25, g_h + 0.3), pal["roof"])
        kit.box((min(x_out, x_in) + 0.3, gy0 + 0.2, g_h + 0.3), (max(x_out, x_in) - 0.3, gy0 + 0.5, g_h + 0.5), pal["trim"], skip=("-z",))
        collider = "box"
    elif garage_roof == "lean":
        edge = x_out + garage_side * 0.35
        kit.extrude_y([(x_in, g_h), (edge, g_h), (edge, g_h + 0.25), (x_in, g_h + 1.3)], gy0 - 0.3, gy1 + 0.25, pal["roof"], colours={0: pal["wall"]})
        collider = "hull"
    else:
        kit.extrude_y([(gx0 - 0.3, g_h), (gx1 + 0.3, g_h), (g_mid, g_h + 1.4)], gy0 - 0.3, gy1 + 0.25, pal["roof"], colours={0: pal["wall"]})
        collider = "hull"
    add(kit, "roof", "tile", 1, supports=flatten(g_walls), collider=collider)

    return building.finish(
        look=(
            f"{roof_form}/{main_w:g}x{depth:g}/rise{rise:g}/garage-{'left' if garage_side < 0 else 'right'}-{garage_roof}+{garage_back:g}"
            f"/chimney-{chimney_style}/porch-{porch}/{window_style}/{'shutters' if shutters else 'plain'}/total{total_w:g}m"
        )
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(18, 16))


if __name__ == "__main__":
    previews()
