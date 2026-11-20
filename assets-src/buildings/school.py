"""School generator.

A long two-storey schoolhouse about 14 x 9 m with rows of big windows, a
central entrance wing with its own gable (and a clock or a round window in
it), wide steps up to a double door, a little bell cupola on the ridge and a
flagpole out front. The seed varies the length and depth, the roof (gabled or
hipped) and its pitch, the entrance wing, the cupola's roof, the windows and
which side the flag stands on.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/school.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import clock_face, frustum, round_window  # noqa: E402
from lib.shapes_town2 import (  # noqa: E402
    cross_gable,
    door,
    flag,
    flatten,
    floor_slab,
    roof_gabled,
    roof_hipped,
    shell_storey,
    split,
    wall_colours,
    window,
)

TYPE = "school"
HITS_TO_COLLAPSE = 2  # medium building
TRIANGLE_BUDGET = 1300

WALL = 0.35


def build(building_id, seed, scheme=None, collection=None):
    """Build one school. Returns (empty, stats)."""
    rng = random.Random(seed)

    # --- the school's character ---
    roof_form = ("gabled", "hipped")[seed % 2]  # cycled, so neighbouring seeds always differ
    width = rng.choice([13.0, 14.0, 15.0])
    depth = rng.choice([8.0, 8.5, 9.0])
    storey = rng.choice([3.0, 3.2])
    rise = rng.choice([2.6, 3.0, 3.4])
    wing_w = rng.choice([4.0, 4.4, 4.8])
    wing_out = rng.choice([1.2, 1.6, 2.0])
    gable_face = rng.choice(["clock", "clock", "round"])
    cupola = rng.choice(["pyramid", "dome", "spire"])
    window_style = rng.choice(["big", "tall"])
    flag_side = (-1, 1, 1, -1)[seed % 4]
    hour = rng.randrange(12)
    minute = rng.choice([0, 15, 30, 45])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]
    accent = pal["door"] if pal["door"] != "doorBrown" else pal["roof"]
    colours = wall_colours(pal)

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    total_d = depth + wing_out
    wing_front = -total_d / 2
    front, back = wing_front + wing_out, total_d / 2
    x0, x1 = -width / 2, width / 2
    bounds = (x0, x1, front, back)
    mid_y = (front + back) / 2
    half_wing = wing_w / 2
    eaves = storey * 2

    win_w, win_h, sill = (1.6, 1.5, 0.9) if window_style == "big" else (1.3, 1.9, 0.6)

    side_span = (x0, -half_wing), (half_wing, x1)
    front_bays = split(*side_span[0], 2.6) + split(*side_span[1], 2.6)
    back_bays = split(x0, x1, 4.7)
    side_bays = [(front + WALL, back - WALL)]
    bays = {"front": front_bays, "back": back_bays, "left": side_bays, "right": side_bays}

    def openings_for(z):
        def openings(side, i, a, b):
            mid = (a + b) / 2
            if side == "front":
                return [window(mid, z, win_w, win_h, sill)]
            if side == "back":
                if z == 0 and i == len(back_bays) // 2:
                    return [door(mid - 0.9, 0), window(mid + 1.0, z, 1.3, win_h, sill)]
                return [window(mid, z, 2.6, win_h, sill)]
            quarter = (b - a) / 4
            return [window(mid - quarter, z, win_w, win_h, sill), window(mid + quarter, z, win_w, win_h, sill)]

        return openings

    walls0 = shell_storey(add, bounds, 0, storey, 0, colours, openings=openings_for(0), bays=bays)
    floor_slab(add, bounds, storey, 1, flatten(walls0), pieces=2)
    walls1 = shell_storey(add, bounds, storey, eaves, 1, colours, below=walls0, openings=openings_for(storey), bays=bays)

    # --- the entrance wing: steps and a double door below, a big window above ---
    wing = []
    for s in range(2):
        z0, z1 = s * storey, (s + 1) * storey
        ids = []
        kit = Kit()
        if s == 0:
            kit.wall(-half_wing, half_wing, z0, z1, wing_front, WALL, 1, [door(0, 0, 1.9, 2.5)], colours)
            kit.box((-half_wing + 0.3, wing_front - 1.2, 0), (half_wing - 0.3, wing_front, 0.16), "stone", skip=("-z", "+y"))
            kit.box((-half_wing + 0.7, wing_front - 0.6, 0.16), (half_wing - 0.7, wing_front, 0.32), "stone", skip=("-z", "+y"))
            # The split down the middle of the double door.
            y = wing_front + 0.1
            kit.poly([(-0.06, y, 0), (0.06, y, 0), (0.06, y, 2.5), (-0.06, y, 2.5)], (0, -1, 0), pal["trim"])
        else:
            kit.wall(-half_wing, half_wing, z0, z1, wing_front, WALL, 1, [window(0, z0, wing_w - 1.8, win_h, sill)], colours)
            kit.box((-half_wing + WALL, wing_front + WALL, z0 - 0.2), (half_wing - WALL, front + WALL, z0), "interiorCream")
        ids.append(add(kit, "wall", "plaster", s, supports=(wing[0][0],) if s else ()))
        for sign in (-1, 1):
            xa, xb = sorted((sign * half_wing, sign * (half_wing - WALL)))
            kit = Kit()
            kit.box((xa, wing_front + WALL, z0), (xb, front + WALL, z1), pal["wall"], sides={"+x" if sign < 0 else "-x": "interiorCream"})
            ids.append(add(kit, "wall", "plaster", s, supports=(wing[0][len(ids)],) if s else ()))
        wing.append(ids)

    # --- main roof ---
    n_left = len(split(*side_span[0], 2.6))
    front_pieces = [(bay, walls1["front"][i]) for i, bay in enumerate(front_bays)]
    front_pieces.insert(n_left, ((-half_wing, half_wing), wing[1][0]))
    back_pieces = [(bay, walls1["back"][i]) for i, bay in enumerate(back_bays)]
    ends = {-1: walls1["left"], 1: walls1["right"]}
    if roof_form == "gabled":

        def gable_extra(kit, sign):
            round_window(kit, (sign * width / 2, mid_y, eaves + rise * 0.36), (sign, 0, 0), min(0.75, rise * 0.24), pal["trim"])

        main_roof = roof_gabled(add, bounds, eaves, rise, pal["roof"], 2, front_pieces, back_pieces, ends, pal["wall"], gable_extra=gable_extra)
    else:
        main_roof = roof_hipped(add, bounds, eaves, rise, pal["roof"], 2, front_pieces, back_pieces, ends)
    ridge = eaves + rise

    # --- the entrance gable, with the school clock ---
    gable_h = min(wing_w / 2 * 0.95, rise * 0.9)
    slope = rise / (depth / 2)
    kit = Kit()
    cross_gable(kit, 0, wing_w, eaves, gable_h, wing_front, min(front + gable_h / slope + 0.4, mid_y), pal["wall"], pal["roof"])
    centre = (0, wing_front, eaves + gable_h * 0.36)
    radius = min(0.95, gable_h * 0.3)
    if gable_face == "clock":
        clock_face(kit, centre, (0, -1, 0), radius, accent, hour, minute)
    else:
        round_window(kit, centre, (0, -1, 0), radius, pal["trim"])
    add(kit, "roof", "tile", 2, supports=(wing[1][0],), collider="hull")

    # --- bell cupola on the ridge ---
    holders = (main_roof["front"][n_left], main_roof["back"][len(back_bays) // 2])
    c = 0.85
    base_top = ridge + 0.55
    bell_top = base_top + 1.5
    kit = Kit()
    kit.box((-c, mid_y - c, ridge - 0.75), (c, mid_y + c, base_top), pal["trim"], skip=("-z",))
    for sx in (-1, 1):
        for sy in (-1, 1):
            xa, xb = sorted((sx * c, sx * (c - 0.28)))
            ya, yb = sorted((mid_y + sy * c, mid_y + sy * (c - 0.28)))
            kit.box((xa, ya, base_top), (xb, yb, bell_top), pal["trim"], skip=("-z", "+z"))
    frustum(kit, 0, mid_y, base_top + 0.2, 0.55, base_top + 1.2, 0.22, "sunny", sides=6, bottom="tyre", top="sunny")
    cupola_base = add(kit, "detail", "wood", 3, supports=holders)

    kit = Kit()
    kit.box((-c - 0.2, mid_y - c - 0.2, bell_top), (c + 0.2, mid_y + c + 0.2, bell_top + 0.2), pal["roof"])
    r = (c + 0.2) * math.sqrt(2)
    if cupola == "pyramid":
        tip = bell_top + 1.5
        frustum(kit, 0, mid_y, bell_top + 0.2, r, tip, 0.0, pal["roof"], sides=4)
    elif cupola == "spire":
        tip = bell_top + 2.6
        frustum(kit, 0, mid_y, bell_top + 0.2, r * 0.8, tip, 0.0, accent, sides=4)
    else:
        r8 = (c + 0.1) / math.cos(math.pi / 8)
        tip = bell_top + 1.3
        frustum(kit, 0, mid_y, bell_top + 0.2, r8, bell_top + 0.8, r8 * 0.75, pal["roof"])
        frustum(kit, 0, mid_y, bell_top + 0.8, r8 * 0.75, tip, 0.0, pal["roof"])
    frustum(kit, 0, mid_y, tip - 0.05, 0.0, tip + 0.3, 0.26, "sunny", sides=4)
    frustum(kit, 0, mid_y, tip + 0.3, 0.26, tip + 0.75, 0.0, "sunny", sides=4)
    add(kit, "roof", "tile", 4, supports=(cupola_base,), collider="hull")

    # --- flagpole ---
    fx = flag_side * (half_wing + (width / 2 - half_wing) * 0.55)
    fy = wing_front + 0.4
    kit = Kit()
    kit.box((fx - 0.5, fy - 0.5, 0), (fx + 0.5, fy + 0.5, 0.35), "stone", skip=("-z",))
    flag(kit, fx, fy, 0.35, 8.2, "trimWhite", accent, size=(2.0, 1.3), facing=flag_side)
    add(kit, "detail", "tin", 0)

    return building.finish(
        look=(
            f"{roof_form}/{width:g}x{depth:g}/storey{storey:g}/rise{rise:g}/wing{wing_w:g}+{wing_out:g}/{gable_face}"
            f"/cupola-{cupola}/{window_style}/flag{flag_side:+d}/height{tip + 0.75:.1f}"
        )
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(24, 22))


if __name__ == "__main__":
    previews()
