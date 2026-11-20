"""Barn generator: the classic big toy barn.

About 14 m wide and 10 m deep with its gable to the front. A gambrel
(two-slope) roof, big double doors with white X-bracing, a hayloft door under
a hoist beam, white trim, small windows and, usually, a lean-to down one or
both sides. The lean-tos make up the 14 m: the barn itself is 9.5-12.5 m wide.

The seed varies the wall colour (tomato red most often), the lean-tos, the
eave height, whether a door is slid open, the cupola on the ridge, the back
door and what hangs from the hoist. The scheme only picks the roof colour.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/barn.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_farm as farm  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import round_window, wall_y  # noqa: E402
from lib.shapes_castle2 import pyramid  # noqa: E402
from lib.shapes_parkcastle import fquad  # noqa: E402

TYPE = "barn"
HITS_TO_COLLAPSE = 2  # medium building
TRIANGLE_BUDGET = 1300

DEPTH = 10.0
WALL = 0.35
OVERHANG = 0.4
VERGE = 0.45
ROOF_THICKNESS = 0.3
DOOR_HALF = 2.3  # half the width of the big doorway
LEANS = ("left", "none", "right", "both")
MAIN_WIDTH = {"none": 12.5, "left": 10.4, "right": 10.4, "both": 9.4}
LEAN_WIDTH = {"none": 0.0, "left": 3.4, "right": 3.4, "both": 2.4}


def build(building_id, seed, scheme=None, collection=None):
    """Build one barn. Returns (empty, stats)."""
    rng = random.Random(seed)

    # --- the barn's character ---
    lean = LEANS[seed % len(LEANS)]  # cycled, so neighbouring seeds always differ
    wall_colour = rng.choice(["tomato", "tomato", "tomato", "cobalt", "sunny", "tangerine"])
    eave = rng.choice([3.6, 4.0])
    doors = rng.choice(["closed", "open", "closed"])
    open_side = rng.choice([-1, 1])
    cupola = rng.random() < 0.65
    hoist_load = rng.random() < 0.6
    back_door = rng.choice([0, -1, 1])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]
    roof_colour = pal["roof"] if pal["roof"] in ("cobalt", "tomato") and pal["roof"] != wall_colour else "stone"

    colours = {
        "wall": wall_colour,
        "interior": "interiorCream",
        "trim": "trimWhite",
        "glass": "windowBlue",
        "shine": "windowShine",
        "door": "doorBrown",
    }

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    main_w = MAIN_WIDTH[lean]
    lean_w = LEAN_WIDTH[lean]
    lean_signs = {"none": (), "left": (-1,), "right": (1,), "both": (-1, 1)}[lean]
    total = main_w + lean_w * len(lean_signs)
    x0 = -total / 2 + (lean_w if -1 in lean_signs else 0.0)
    x1 = x0 + main_w
    cx = (x0 + x1) / 2
    h = main_w / 2
    front, back = -DEPTH / 2, DEPTH / 2
    knee_x = 0.64 * h
    knee_z = eave + 0.46 * h
    ridge = eave + 0.74 * h
    door_h = eave - 0.55
    front_face = farm.face("front", front)
    back_face = farm.face("back", back)

    def window(centre, z0=1.5, half=0.55, height=1.1):
        return {"x0": centre - half, "x1": centre + half, "z0": z0, "z1": z0 + height, "kind": "window"}

    # --- the front: a pier either side of the doorway, and a lintel over it ---
    piers = []
    for sign in (-1, 1):
        xa, xb = sorted((cx + sign * h, cx + sign * DOOR_HALF))
        kit = Kit()
        kit.wall(xa, xb, 0, eave, front, WALL, 1, [window((xa + xb) / 2)], colours)
        ua, ub = sorted((cx + sign * h, cx + sign * (h - 0.3)))
        fquad(kit, front_face, ua, ub, 0, eave, 0.02, "trimWhite")  # corner board
        piers.append(add(kit, "wall", "wood", 0))

    kit = Kit()
    kit.box((cx - DOOR_HALF, front, door_h), (cx + DOOR_HALF, front + WALL, eave), wall_colour, sides={"+y": "interiorCream"})
    fquad(kit, front_face, cx - DOOR_HALF, cx + DOOR_HALF, door_h, door_h + 0.24, 0.02, "trimWhite")
    lintel = add(kit, "band", "wood", 0, supports=piers)

    # --- the big doors: two leaves with white X-bracing; one may be slid open ---
    for index, sign in enumerate((-1, 1)):
        xa, xb = sorted((cx, cx + sign * DOOR_HALF))
        y_a = front + 0.06
        if doors == "open" and sign == open_side:
            xa += sign * (DOOR_HALF - 0.25)
            xb += sign * (DOOR_HALF - 0.25)
            y_a = front - 0.26
        kit = Kit()
        kit.box((xa + 0.03, y_a, 0), (xb - 0.03, y_a + 0.2, door_h), wall_colour)
        farm.x_brace(kit, farm.face("front", y_a), xa + 0.03, xb - 0.03, 0, door_h, 0.02, "trimWhite", width=0.26)
        add(kit, "detail", "wood", 0, supports=(piers[index],))

    # Hay just inside the doorway.
    kit = Kit()
    kit.box((cx - 1.9, front + 1.2, 0), (cx - 0.2, front + 2.3, 0.85), "sunny", skip=("-z",))
    kit.box((cx - 0.1, front + 1.4, 0), (cx + 1.6, front + 2.5, 0.85), "sunny", skip=("-z",))
    kit.box((cx - 1.2, front + 1.3, 0.85), (cx + 0.5, front + 2.4, 1.7), "sunny", skip=("-z",))
    add(kit, "detail", "leaves", 0)

    # --- the back: two bays ---
    backs = []
    for sign in (-1, 1):
        xa, xb = sorted((cx, cx + sign * h))
        mid = (xa + xb) / 2
        if sign == back_door:
            hole = {"x0": mid - 0.75, "x1": mid + 0.75, "z0": 0.0, "z1": 2.5, "kind": "door"}
        else:
            hole = window(mid, half=0.7)
        kit = Kit()
        kit.wall(xa, xb, 0, eave, back, WALL, -1, [hole], colours)
        ua, ub = sorted((-(cx + sign * h), -(cx + sign * (h - 0.3))))
        fquad(kit, back_face, ua, ub, 0, eave, 0.02, "trimWhite")
        backs.append(add(kit, "wall", "wood", 0))

    # --- the long side walls, two bays each ---
    spans = [(front + WALL, 0.0), (0.0, back - WALL)]
    sides = {-1: [], 1: []}
    for sign, x_out in ((-1, x0), (1, x1)):
        for ya, yb in spans:
            kit = Kit()
            if sign in lean_signs:
                lo, hi = sorted((x_out, x_out - sign * WALL))
                kit.box((lo, ya, 0), (hi, yb, eave), wall_colour, sides={"+x" if sign < 0 else "-x": "interiorCream"})
            else:
                wall_y(kit, ya, yb, 0, eave, x_out, WALL, -sign, [window((ya + yb) / 2, half=0.65)], colours)
            sides[sign].append(add(kit, "wall", "wood", 0))

    # --- the hayloft floor ---
    for sign, index in ((-1, 0), (1, 1)):
        xa, xb = sorted((cx, cx + sign * (h - WALL)))
        kit = Kit()
        kit.box((xa, front + WALL, eave - 0.2), (xb, back - WALL, eave), "interiorCream")
        add(kit, "floor", "wood", 1, supports=(piers[index], backs[index], *sides[sign]))

    # --- the gambrel gables ---
    section = [(x0, eave), (x1, eave), (cx + knee_x, knee_z), (cx, ridge), (cx - knee_x, knee_z)]
    loft_z0, loft_z1 = eave + 0.5, eave + 2.3
    kit = Kit()
    kit.extrude_y(section, front, front + WALL, wall_colour, colours={1: "interiorCream"})
    fquad(kit, front_face, x0, x1, eave, eave + 0.24, 0.02, "trimWhite")
    fquad(kit, front_face, cx - 1.0, cx + 1.0, loft_z0 - 0.13, loft_z1 + 0.13, 0.03, "trimWhite")
    fquad(kit, front_face, cx - 0.86, cx + 0.86, loft_z0, loft_z1, 0.05, "doorBrown")
    farm.x_brace(kit, front_face, cx - 0.86, cx + 0.86, loft_z0, loft_z1, 0.07, "trimWhite", width=0.15, border=False)
    gable_front = add(kit, "wall", "wood", 1, supports=(*piers, lintel), collider="hull")

    kit = Kit()
    kit.extrude_y(section, back - WALL, back, wall_colour, colours={0: "interiorCream"})
    fquad(kit, back_face, -x1, -x0, eave, eave + 0.24, 0.02, "trimWhite")
    round_window(kit, (cx, back, eave + (ridge - eave) * 0.45), (0, 1, 0), 0.85, "trimWhite")
    gable_back = add(kit, "wall", "wood", 1, supports=backs, collider="hull")

    # --- the roof: a steep lower slope and a shallow upper one each side, front and back halves ---
    lower_slope = (knee_z - eave) / (h - knee_x)
    eave_z = eave - OVERHANG * lower_slope
    uppers = []
    for half, (ya, yb) in enumerate(((front - VERGE, 0.0), (0.0, back + VERGE))):
        verge_edge = 5 if half == 0 else 3  # the slab edge that shows at the gable end
        gable = gable_front if half == 0 else gable_back
        for sign in (-1, 1):
            xe = cx + sign * (h + OVERHANG)
            xk = cx + sign * knee_x
            kit = Kit()
            farm.slab(
                kit,
                [(xe, ya, eave_z), (xe, yb, eave_z), (xk, yb, knee_z), (xk, ya, knee_z)],
                ROOF_THICKNESS,
                roof_colour,
                {2: "trimWhite", verge_edge: "trimWhite"},
            )
            lower = add(kit, "roof", "tile", 1, supports=(sides[sign][half],), collider="hull")
            kit = Kit()
            farm.slab(
                kit,
                [(xk, ya, knee_z), (xk, yb, knee_z), (cx, yb, ridge), (cx, ya, ridge)],
                ROOF_THICKNESS,
                roof_colour,
                {verge_edge: "trimWhite"},
            )
            uppers.append(add(kit, "roof", "tile", 2, supports=(gable, lower), collider="hull"))

    # --- the hoist beam over the hayloft door ---
    kit = Kit()
    kit.box((cx - 0.17, front - 1.7, ridge - 0.9), (cx + 0.17, front + 0.2, ridge - 0.58), "doorBrown")
    kit.box((cx - 0.05, front - 1.45, ridge - 1.9), (cx + 0.05, front - 1.35, ridge - 0.9), "tyre", skip=("+z", "-z"))
    if hoist_load:
        kit.box((cx - 0.55, front - 1.75, ridge - 2.55), (cx + 0.55, front - 1.05, ridge - 1.9), "sunny")
    else:
        kit.box((cx - 0.16, front - 1.5, ridge - 2.15), (cx + 0.16, front - 1.3, ridge - 1.9), "stone")
    add(kit, "detail", "wood", 2, supports=(gable_front,))

    # --- a cupola with a weather vane on the ridge ---
    if cupola:
        kit = Kit()
        kit.box((cx - 0.8, -0.8, ridge - 0.4), (cx + 0.8, 0.8, ridge + 1.0), "trimWhite", skip=("-z", "+z"))
        for side, at in (("front", -0.8), ("back", 0.8), ("left", cx - 0.8), ("right", cx + 0.8)):
            along = cx if side in ("front", "back") else 0.0
            fquad(kit, farm.face(side, at, along), -0.45, 0.45, ridge + 0.25, ridge + 0.8, 0.02, wall_colour)
        pyramid(kit, cx, 0, 1.15, 1.15, ridge + 1.0, 1.0, wall_colour)  # not the roof colour, or it vanishes against the roof
        kit.box((cx - 0.06, -0.06, ridge + 1.9), (cx + 0.06, 0.06, ridge + 2.9), "tyre", skip=("-z",))
        kit.box((cx - 0.75, -0.05, ridge + 2.45), (cx + 0.75, 0.05, ridge + 2.7), "sunny")
        add(kit, "detail", "wood", 3, supports=uppers, collider="hull")

    # --- the lean-tos ---
    for sign in lean_signs:
        xi = x0 if sign < 0 else x1
        xo = xi + sign * lean_w
        ya, yb = front + 1.6, back
        z_out, z_in = 2.5, eave - 0.9
        slope = (z_in - z_out) / lean_w
        mid = (ya + yb) / 2
        quarter = (yb - ya) / 4

        kit = Kit()
        wall_y(kit, ya, yb, 0, z_out, xo, WALL, -sign, [window(mid - quarter, 1.0, 0.6, 1.0), window(mid + quarter, 1.0, 0.6, 1.0)], colours)
        outer = add(kit, "wall", "wood", 0)

        xw = xo - sign * WALL
        wedge = [(xi, 0), (xw, 0), (xw, z_out + slope * WALL), (xi, z_in)]
        kit = Kit()
        kit.extrude_y(wedge, ya, ya + WALL, wall_colour, colours={1: "interiorCream"})
        door_x = (xi + xw) / 2
        fquad(kit, farm.face("front", ya), door_x - 0.65, door_x + 0.65, 0, 2.15, 0.02, "trimWhite")
        fquad(kit, farm.face("front", ya), door_x - 0.5, door_x + 0.5, 0, 2.0, 0.04, "doorBrown")
        add(kit, "wall", "wood", 0, collider="hull")
        kit = Kit()
        kit.extrude_y(wedge, yb - WALL, yb, wall_colour, colours={0: "interiorCream"})
        add(kit, "wall", "wood", 0, collider="hull")

        xe = xo + sign * OVERHANG
        ze = z_out - OVERHANG * slope
        for half, (ra, rb) in enumerate(((ya - 0.3, mid), (mid, yb + 0.3))):
            kit = Kit()
            farm.slab(kit, [(xe, ra, ze), (xe, rb, ze), (xi, rb, z_in), (xi, ra, z_in)], 0.25, roof_colour, {2: "trimWhite"})
            add(kit, "roof", "tile", 1, supports=(outer, sides[sign][half]), collider="hull")

    return building.finish(
        look=f"{wall_colour}/{roof_colour} lean-{lean} eave={eave} doors-{doors} cupola={int(cupola)} footprint={total:.1f}x{DEPTH}"
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(24, 20))


if __name__ == "__main__":
    previews()
