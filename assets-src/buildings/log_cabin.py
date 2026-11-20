"""Log cabin generator.

A chunky single-storey cabin about 9 m by 7 m. The walls are courses of fat
faceted logs, with the log ends crossing and sticking out at the corners, a
bright pitched roof, a stone chimney, a little porch on log posts over the
door, and windows front, back and sides.

The seed varies the size, the wood (pale logs with dark ends or the other way
round), which bay the door is in, the roof pitch, the porch (lean-to or
gabled), the chimney (a stack up an end wall or a fat one on the ridge) and
the back windows.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/log_cabin.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import round_window, wall_y  # noqa: E402
from lib.shapes_forest import log, log_courses, roof_halves  # noqa: E402

TYPE = "log_cabin"
HITS_TO_COLLAPSE = 2
TRIANGLE_BUDGET = 900

WALL = 0.4
STOREY = 3.0
COURSES = 4  # fat logs: 0.75 m each
COURSE = STOREY / COURSES
PROUD = 0.17  # how far the logs' round faces stand out from the wall
OVERHANG = 0.55
VERGE = 0.7
ROOF_THICKNESS = 0.3


def build(building_id, seed, scheme=None, collection=None):
    """Build one log cabin. Returns (empty, stats)."""
    rng = random.Random(seed)

    width = rng.choice([8.4, 9.0, 9.6])
    depth = rng.choice([6.6, 7.0])
    pale = rng.choice([True, True, False])
    door_bay = rng.choice([0, 1, 1, 2])
    pitch = rng.choice([0.7, 0.85, 1.0])
    porch = rng.choice(["lean", "gabled"])
    chimney_style = rng.choice(["end", "end", "ridge"])
    chimney_side = rng.choice([-1, 1])
    back_windows = rng.choice([2, 3])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    if chimney_style == "ridge":  # both end walls have windows then, so the budget keeps the back to two
        back_windows = 2

    logs, dark = ("wood", "doorBrown") if pale else ("doorBrown", "wood")
    door_colour = pal["door"] if pal["door"] != "doorBrown" else pal["roof"]
    colours = {"wall": logs, "interior": "interiorCream", "trim": pal["trim"], "glass": "windowBlue", "shine": "windowShine", "door": door_colour}

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    x0, x1 = -width / 2, width / 2
    front, back = -depth / 2, depth / 2
    rise = pitch * depth / 2
    ridge = STOREY + rise
    eave_z = STOREY - pitch * OVERHANG

    def window(centre, half=0.8):
        return {"x0": centre - half, "x1": centre + half, "z0": COURSE, "z1": COURSE * 3, "kind": "window"}

    # --- front and back walls, three bays each ---
    bay = width / 3
    fronts, backs = [], []
    door_x = x0 + (door_bay + 0.5) * bay
    for i in range(3):
        a, b = x0 + i * bay, x0 + (i + 1) * bay
        mid = (a + b) / 2

        if i == door_bay:
            openings = [{"x0": mid - 0.75, "x1": mid + 0.75, "z0": 0.0, "z1": COURSE * 3, "kind": "door"}]
        else:
            openings = [window(mid)]
        kit = Kit()
        kit.wall(a, b, 0, STOREY, front, WALL, 1, openings, colours)
        log_courses(kit, lambda u, d, z: (u, front - d, z), a, b, 0, STOREY, COURSES, PROUD, logs, openings, end=dark)
        fronts.append(add(kit, "wall", "wood", 0))

        openings = [] if (i == 1 and back_windows == 2) else [window(mid)]
        kit = Kit()
        if openings:
            kit.wall(a, b, 0, STOREY, back, WALL, -1, openings, colours)
        else:
            kit.box((a, back - WALL, 0), (b, back, STOREY), logs, sides={"-y": "interiorCream"}, skip=("+y",))
        log_courses(kit, lambda u, d, z: (u, back + d, z), a, b, 0, STOREY, COURSES, PROUD, logs, openings, end=dark)
        backs.append(add(kit, "wall", "wood", 0))

    # --- side walls, with the gable above each ---
    sides, gables = {}, {}
    for sign in (-1, 1):
        x_out = sign * width / 2
        stack = chimney_style == "end" and sign == chimney_side
        openings = [] if stack else [window(0.0)]
        kit = Kit()
        if openings:
            wall_y(kit, front + WALL, back - WALL, 0, STOREY, x_out, WALL, -sign, openings, colours)
        else:
            lo, hi = sorted((x_out, x_out - sign * WALL))
            kit.box((lo, front + WALL, 0), (hi, back - WALL, STOREY), logs, sides={"+x" if sign < 0 else "-x": "interiorCream"})
        log_courses(kit, lambda u, d, z: (x_out + sign * d, u, z), front + WALL, back - WALL, 0, STOREY, COURSES, PROUD, logs, openings, end=dark)
        sides[sign] = add(kit, "wall", "wood", 0)

        xa, xb = sorted((x_out, x_out - sign * WALL))
        kit = Kit()
        kit.extrude_x([(front, STOREY), (back, STOREY), (0, ridge)], xa, xb, dark)
        if not stack:
            round_window(kit, (x_out, 0, STOREY + rise * 0.36), (sign, 0, 0), min(0.62, rise * 0.22), pal["trim"])
        gables[sign] = add(kit, "wall", "wood", 1, supports=(sides[sign],), collider="hull")

    # --- the crossed log ends at each corner ---
    for sx in (-1, 1):
        for sy in (-1, 1):
            kit = Kit()
            for k in range(COURSES):
                zm = (k + 0.5) * COURSE
                if k % 2 == 0:  # the front and back walls' logs run on past the corner
                    lo, hi = sorted((sx * (width / 2 - 0.05), sx * (width / 2 + 0.55)))
                    log(kit, "x", lo, hi, (sy * (depth / 2 - WALL / 2 + 0.02), zm), COURSE / 2 - 0.02, logs, end="interiorCream", sides=6, caps=(sx < 0, sx > 0))
                else:
                    lo, hi = sorted((sy * (depth / 2 - 0.05), sy * (depth / 2 + 0.55)))
                    log(kit, "y", lo, hi, (sx * (width / 2 - WALL / 2 + 0.02), zm), COURSE / 2 - 0.02, logs, end="interiorCream", sides=6, caps=(sy < 0, sy > 0))
            add(kit, "corner", "wood", 0, supports=(sides[sx], fronts[0 if sx < 0 else 2] if sy < 0 else backs[0 if sx < 0 else 2]), collider="box")

    # --- roof: each slope in two pieces ---
    halves = []
    for a, b, holders in ((x0 - VERGE, 0.0, (0, 1)), (0.0, x1 + VERGE, (1, 2))):
        for kit, walls in zip(roof_halves("x", a, b, depth / 2 + OVERHANG, eave_z, ridge, ROOF_THICKNESS, pal["roof"]), (fronts, backs)):
            halves.append(add(kit, "roof", "tile", 1, supports=[walls[h] for h in holders], collider="hull"))
    kit = Kit()  # ridge log
    kit.box((x0 - VERGE - 0.15, -0.26, ridge + ROOF_THICKNESS - 0.2), (x1 + VERGE + 0.15, 0.26, ridge + ROOF_THICKNESS + 0.24), pal["trim"])
    add(kit, "detail", "wood", 1, supports=halves, collider="hull")

    # --- porch over the door: a deck, two log posts and a little roof ---
    out = 1.7
    kit = Kit()
    kit.box((door_x - 1.5, front - out, 0), (door_x + 1.5, front - PROUD, 0.25), "stone", skip=("-z",))
    for side in (-1, 1):
        log(kit, "z", 0.25, 2.45, (door_x + side * 1.2, front - out + 0.3), 0.19, dark, sides=4, caps=(False, False))
    if porch == "gabled":
        kit.extrude_y([(door_x - 1.65, 2.45), (door_x + 1.65, 2.45), (door_x, 3.4)], front - out - 0.2, front, pal["roof"], colours={0: pal["trim"]})
    else:
        kit.extrude_x([(front - out - 0.2, 2.4), (front, 2.95), (front, 3.2), (front - out - 0.2, 2.65)], door_x - 1.6, door_x + 1.6, pal["roof"])
    add(kit, "detail", "wood", 0, supports=(fronts[door_bay],), collider="hull")

    # --- stone chimney ---
    kit = Kit()
    if chimney_style == "end":
        sign = chimney_side
        xa, xb = sorted((sign * (width / 2 + PROUD * 0.5), sign * (width / 2 + 0.85)))
        shoulder = STOREY * 0.8
        top_z = ridge + 1.3
        kit.extrude_x([(-1.2, 0), (1.2, 0), (1.2, shoulder), (0.6, shoulder + 0.8), (-0.6, shoulder + 0.8)], xa, xb, "stone")
        kit.box((xa, -0.6, shoulder + 0.8), (xb, 0.6, top_z), "stone", skip=("-z", "+z"))
        kit.box((xa - 0.12, -0.72, top_z), (xb + 0.12, 0.72, top_z + 0.25), pal["trim"])
        add(kit, "detail", "stone", 0, collider="hull")
    else:
        cx = chimney_side * width * 0.24
        kit.box((cx - 0.75, -0.6, ridge - 0.8), (cx + 0.75, 0.6, ridge + 1.5), "stone", skip=("-z", "+z"))
        kit.box((cx - 0.87, -0.72, ridge + 1.5), (cx + 0.87, 0.72, ridge + 1.75), pal["trim"])
        add(kit, "detail", "stone", 1, supports=halves[0:2] if chimney_side < 0 else halves[2:4])

    return building.finish(look=f"{width:g}x{depth:g}/{'pale' if pale else 'dark'}/door{door_bay}/pitch{pitch}/{porch}/{chimney_style}{chimney_side:+d}/back{back_windows}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(15, 14))


if __name__ == "__main__":
    previews()
