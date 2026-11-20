"""Cottage generator.

A small one- or two-storey cottage under a steep pitched roof, with one big
chimney, an octagonal window in the gable and a little porch over the door.
The seed varies the plan (a plain rectangle or an L with a front wing), which
way the ridge runs, the number of storeys, the roof pitch, the chimney (a
stack up the outside of an end wall, or a fat one on the ridge), the porch,
the window style and where the door goes.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/cottage.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import round_window, wall_y  # noqa: E402

TYPE = "cottage"
HITS_TO_COLLAPSE = 1  # small building
TRIANGLE_BUDGET = 400

WALL = 0.35
OVERHANG = 0.5
VERGE = 0.35  # how far the roof sails past the gable ends
ROOF_THICKNESS = 0.3


def build(building_id, seed, scheme=None, collection=None):
    """Build one cottage. Returns (empty, stats)."""
    rng = random.Random(seed)

    # --- the cottage's character ---
    plan = rng.choice(["rect", "rect", "L"])
    ridge_along = rng.choice(["x", "x", "y"])  # along the frontage, or front to back (gable to the street)
    storeys = rng.choice([1, 1, 2])
    width = rng.choice([6.5, 7.0, 7.5])
    depth = rng.choice([5.5, 6.0, 6.5])
    storey = rng.choice([2.8, 3.0])
    pitch = rng.choice([1.0, 1.2, 1.4])  # rise per metre: steep
    chimney_style = rng.choice(["end", "end", "ridge"])
    chimney_side = rng.choice([-1, 1])
    porch = rng.choice(["flat", "gabled", "lean"])
    window_style = rng.choice(["square", "wide", "tall"])
    door_pos = rng.choice(["left", "right", "centre"])
    wing_side = rng.choice([-1, 1])
    wing_width = rng.choice([3.2, 3.6])
    wing_out = rng.choice([2.0, 2.6])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    if plan == "L":  # the wing needs the main ridge along the frontage, and the budget keeps it to one storey
        ridge_along = "x"
        storeys = 1
    if storeys == 2 and door_pos == "centre":
        door_pos = "left"
    two = storeys == 2

    colours = {
        "wall": pal["wall"],
        "interior": "interiorCream",
        "trim": pal["trim"],
        "glass": "windowBlue",
        "shine": "windowShine",
        "door": pal["door"],
    }

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    x0, x1 = -width / 2, width / 2
    front, back = -depth / 2, depth / 2
    eaves = storeys * storey
    span = depth if ridge_along == "x" else width
    rise = min(pitch * span / 2, 4.2)
    slope = rise / (span / 2)
    ridge = eaves + rise
    eave_z = eaves - slope * OVERHANG

    def window(centre, z, style=None):
        style = style or window_style
        if style == "wide":
            return {"x0": centre - 0.95, "x1": centre + 0.95, "z0": z + 1.0, "z1": z + 2.3, "kind": "window"}
        if style == "tall":
            return {"x0": centre - 0.55, "x1": centre + 0.55, "z0": z + 0.7, "z1": z + 2.4, "kind": "window"}
        return {"x0": centre - 0.7, "x1": centre + 0.7, "z0": z + 0.95, "z1": z + 2.35, "kind": "window"}

    # --- where the front wing, door and ground-floor windows go ---
    if plan == "L":
        if wing_side < 0:
            wing_x0, wing_x1 = x0, x0 + wing_width
            main_x0, main_x1 = wing_x1, x1
            door_x = main_x0 + 1.2
        else:
            wing_x0, wing_x1 = x1 - wing_width, x1
            main_x0, main_x1 = x0, wing_x0
            door_x = main_x1 - 1.2
        ground_windows = []
        if main_x1 - main_x0 >= 3.9:
            centre = (door_x + 0.65 + main_x1) / 2 if wing_side < 0 else (main_x0 + door_x - 0.65) / 2
            ground_windows = [window(centre, 0, "tall")]
    else:
        main_x0, main_x1 = x0, x1
        if door_pos == "centre":
            door_x = 0.0
            ground_windows = [window(-width / 4 - 0.35, 0), window(width / 4 + 0.35, 0)]
        else:
            side = -1 if door_pos == "left" else 1
            door_x = side * (width / 2 - 1.45)
            ground_windows = [window(-side * width / 5, 0)]
    door = {"x0": door_x - 0.65, "x1": door_x + 0.65, "z0": 0.0, "z1": 2.4, "kind": "door"}

    # --- walls, storey by storey ---
    fronts, backs, lefts, rights = [], [], [], []
    for s in range(storeys):
        z0, z1 = s * storey, (s + 1) * storey

        kit = Kit()
        if s == 0:
            kit.wall(main_x0, main_x1, z0, z1, front, WALL, 1, [door] + ground_windows, colours)
        else:
            kit.wall(x0, x1, z0, z1, front, WALL, 1, [window(-width / 4, z0), window(width / 4, z0)], colours)
        fronts.append(add(kit, "wall", "plaster", s, supports=fronts[-1:]))

        kit = Kit()
        if two or plan == "L":
            back_windows = [window(0, z0, "wide")]
        else:
            back_windows = [window(-width / 4, z0), window(width / 4, z0)]
        kit.wall(x0, x1, z0, z1, back, WALL, -1, back_windows, colours)
        backs.append(add(kit, "wall", "plaster", s, supports=backs[-1:]))

        for sign, bucket in ((-1, lefts), (1, rights)):
            x_out = sign * width / 2
            y_a = front + WALL
            if plan == "L" and sign == wing_side:
                y_a = front  # the wing's own side wall carries on from here
            has_chimney = chimney_style == "end" and sign == chimney_side
            kit = Kit()
            if s == 0 and not has_chimney and not (plan == "L" and sign == wing_side):
                wall_y(kit, y_a, back - WALL, z0, z1, x_out, WALL, -sign, [window(0, z0)], colours)
            else:
                lo, hi = sorted((x_out, x_out - sign * WALL))
                inner = "+x" if sign < 0 else "-x"
                kit.box((lo, y_a, z0), (hi, back - WALL, z1), pal["wall"], sides={inner: "interiorCream"})
            bucket.append(add(kit, "wall", "plaster", s, supports=bucket[-1:]))

        if s > 0:
            kit = Kit()
            kit.box((x0 + WALL, front + WALL, z0 - 0.2), (x1 - WALL, back - WALL, z0), "interiorCream")
            add(kit, "floor", "wood", s, supports=(fronts[s - 1], backs[s - 1], lefts[s - 1], rights[s - 1]))

    top = storeys - 1
    roof_storey = storeys

    # --- gables and roof halves ---
    if ridge_along == "x":
        gables = {}
        for sign, wall_id in ((-1, lefts[top]), (1, rights[top])):
            xa, xb = sorted((sign * width / 2, sign * (width / 2 - WALL)))
            kit = Kit()
            kit.extrude_x([(front, eaves), (back, eaves), (0, ridge)], xa, xb, pal["wall"])
            plain = (chimney_style == "end" and sign == chimney_side) or (plan == "L" and sign != -1)
            if not plain and not (two and sign == 1):
                round_window(kit, (sign * width / 2, 0, eaves + rise * 0.36), (sign, 0, 0), min(0.62, rise * 0.2), pal["trim"])
            gables[sign] = add(kit, "wall", "plaster", roof_storey, supports=(wall_id,), collider="hull")
        halves = []
        for sign, wall_id in ((-1, fronts[top]), (1, backs[top])):
            eave_y = sign * (depth / 2 + OVERHANG)
            kit = Kit()
            kit.slab(
                [(x0 - VERGE, eave_y, eave_z), (x1 + VERGE, eave_y, eave_z), (x1 + VERGE, 0, ridge), (x0 - VERGE, 0, ridge)],
                ROOF_THICKNESS,
                pal["roof"],
            )
            halves.append(add(kit, "roof", "tile", roof_storey, supports=(wall_id,), collider="hull"))
    else:
        gables = {}
        for sign, wall_id in ((-1, fronts[top]), (1, backs[top])):
            ya, yb = sorted((sign * depth / 2, sign * (depth / 2 - WALL)))
            kit = Kit()
            kit.extrude_y([(x0, eaves), (x1, eaves), (0, ridge)], ya, yb, pal["wall"])
            if sign < 0:
                round_window(kit, (0, front, eaves + rise * 0.36), (0, -1, 0), min(0.7, rise * 0.2), pal["trim"])
            gables[sign] = add(kit, "wall", "plaster", roof_storey, supports=(wall_id,), collider="hull")
        halves = []
        for sign, wall_id in ((-1, lefts[top]), (1, rights[top])):
            eave_x = sign * (width / 2 + OVERHANG)
            kit = Kit()
            kit.slab(
                [(eave_x, front - VERGE, eave_z), (eave_x, back + VERGE, eave_z), (0, back + VERGE, ridge), (0, front - VERGE, ridge)],
                ROOF_THICKNESS,
                pal["roof"],
            )
            halves.append(add(kit, "roof", "tile", roof_storey, supports=(wall_id,), collider="hull"))

    # --- the front wing of an L-shaped cottage: its own gable to the street ---
    if plan == "L":
        wing_front = front - wing_out
        wing_mid = (wing_x0 + wing_x1) / 2
        half = wing_width / 2
        wing_rise = min(pitch * half, rise - 0.5)
        wing_slope = wing_rise / half
        wing_ridge = eaves + wing_rise

        kit = Kit()
        kit.wall(wing_x0, wing_x1, 0, storey, wing_front, WALL, 1, [window(wing_mid, 0)], colours)
        wing_wall = add(kit, "wall", "plaster", 0)

        for xa, xb, inner in ((wing_x0, wing_x0 + WALL, "+x"), (wing_x1 - WALL, wing_x1, "-x")):
            kit = Kit()
            kit.box((xa, wing_front + WALL, 0), (xb, front, storey), pal["wall"], sides={inner: "interiorCream"})
            add(kit, "wall", "plaster", 0)

        kit = Kit()
        kit.extrude_y(
            [(wing_x0, eaves), (wing_x1, eaves), (wing_mid, wing_ridge)],
            wing_front,
            wing_front + WALL,
            pal["wall"],
        )
        round_window(kit, (wing_mid, wing_front, eaves + wing_rise * 0.38), (0, -1, 0), min(0.55, wing_rise * 0.24), pal["trim"])
        wing_gable = add(kit, "wall", "plaster", 1, supports=(wing_wall,), collider="hull")

        # The wing's roof runs back into the main roof: each half is cut on the slant where they meet.
        y_ridge_end = front + wing_rise / slope + 0.3
        for sign in (-1, 1):
            eave_x = wing_mid + sign * (half + OVERHANG)
            z_low = eaves - wing_slope * OVERHANG
            kit = Kit()
            kit.slab(
                [
                    (eave_x, wing_front - VERGE, z_low),
                    (eave_x, front, z_low),
                    (wing_mid, y_ridge_end, wing_ridge),
                    (wing_mid, wing_front - VERGE, wing_ridge),
                ],
                ROOF_THICKNESS,
                pal["roof"],
            )
            add(kit, "roof", "tile", 1, supports=(wing_gable,), collider="hull")

    # --- porch: a little roof on two posts, and a doorstep ---
    out = 1.3
    kit = Kit()
    if not two:  # the budget only stretches to a doorstep on the single-storey cottages
        kit.box((door_x - 0.95, front - out, 0), (door_x + 0.95, front, 0.2), "stone", skip=("-z", "+y"))
    for side in (-1, 1):
        px = door_x + side * 0.85
        kit.box((px - 0.1, front - out + 0.05, 0), (px + 0.1, front - out + 0.25, 2.5), pal["trim"], skip=("-z", "+z"))
    if porch == "flat":
        kit.box((door_x - 1.1, front - out - 0.15, 2.5), (door_x + 1.1, front, 2.72), pal["roof"], skip=("+y",))
    elif porch == "gabled":
        kit.extrude_y(
            [(door_x - 1.2, 2.5), (door_x + 1.2, 2.5), (door_x, 3.35)],
            front - out - 0.2,
            front,
            pal["roof"],
            colours={0: pal["trim"]},
        )
    else:
        kit.extrude_x(
            [(front - out - 0.2, 2.45), (front, 3.0), (front, 3.2), (front - out - 0.2, 2.65)],
            door_x - 1.15,
            door_x + 1.15,
            pal["roof"],
        )
    add(kit, "detail", "wood", 0, supports=(fronts[0],), collider="hull" if porch != "flat" else "box")

    # --- one big chimney ---
    kit = Kit()
    if chimney_style == "end":
        # A stack up the outside of an end wall, with sloped shoulders.
        sign = chimney_side
        xa, xb = sorted((sign * (width / 2), sign * (width / 2 + 0.6)))
        y_mid = 0.0 if ridge_along == "x" else depth * 0.12
        shoulder = eaves * 0.72
        top_z = ridge + 1.3 if ridge_along == "x" else eaves + rise * 0.55 + 1.2
        kit.extrude_x(
            [(y_mid - 0.95, 0), (y_mid + 0.95, 0), (y_mid + 0.95, shoulder), (y_mid + 0.5, shoulder + 0.7), (y_mid - 0.5, shoulder + 0.7)],
            xa,
            xb,
            pal["wall"],
        )
        kit.box((xa, y_mid - 0.5, shoulder + 0.7), (xb, y_mid + 0.5, top_z), pal["wall"], skip=("-z", "+z"))
        kit.box((xa - 0.1, y_mid - 0.6, top_z), (xb + 0.1, y_mid + 0.6, top_z + 0.22), pal["trim"])
        add(kit, "detail", "plaster", 0, collider="hull")
    else:
        if ridge_along == "x":
            cx, cy = chimney_side * width * 0.22, 0.0
        else:
            cx, cy = 0.0, depth * 0.2
        kit.box((cx - 0.65, cy - 0.5, ridge - 0.7), (cx + 0.65, cy + 0.5, ridge + 1.5), pal["wall"], skip=("-z", "+z"))
        kit.box((cx - 0.77, cy - 0.62, ridge + 1.5), (cx + 0.77, cy + 0.62, ridge + 1.72), pal["trim"])
        if not two:
            kit.box((cx - 0.2, cy - 0.2, ridge + 1.72), (cx + 0.2, cy + 0.2, ridge + 2.2), "tangerine", skip=("-z",))
        add(kit, "detail", "plaster", roof_storey, supports=tuple(halves))

    empty, stats = building.finish(
        look=f"{plan}/ridge-{ridge_along}/{storeys}st/pitch{pitch}/{chimney_style}/{porch}/{window_style}/door-{door_pos}"
    )
    return empty, stats


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(14, 15))


if __name__ == "__main__":
    previews()
