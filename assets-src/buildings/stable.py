"""Stable generator: a low timber lean-to for the castle yard.

About 9 m wide and 5 m deep, open at the front (-Y). A plank back wall and
side walls with cross braces, stout posts along the front carrying a beam, and
a bright tiled roof: a single pitch falling to the front, or a ridge. The bays
between the posts have half-height stall doors, a horse looking out over one
of them, and one bay is left open and stacked with hay bales. A water trough
stands outside.

The seed varies the width, the number of bays, the roof (mono-pitch or
pitched), which bay is open, the horse and where the trough stands. The roof
and the stall doors take the scheme's roof and door colours.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/stable.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "stable"
HITS_TO_COLLAPSE = 1  # small and flimsy
TRIANGLE_BUDGET = 400

DEPTH = 5.0
EAVE = 2.7  # height of the front eave
PLANK = 0.25
POST = 0.36


def build(building_id, seed, scheme=None, collection=None):
    """Build one stable. Returns (empty, stats)."""
    rng = random.Random(seed)

    width = rng.choice([8.5, 9.0, 9.5])
    bays = rng.choice([3, 3, 4])
    roof_style = rng.choice(["mono", "pitched", "mono"])
    open_bay = rng.randrange(bays)
    horse_colour = rng.choice(["doorBrown", "trimWhite", "tyre"])
    trough_side = rng.choice([-1, 1])
    wall_colour = rng.choice(["wood", "wood", "doorBrown"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]
    frame_colour = "doorBrown" if wall_colour == "wood" else "wood"

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    hx = width / 2
    y_front, y_back = -DEPTH / 2, DEPTH / 2
    if roof_style == "mono":
        slope = 0.24  # rising to the back

        def roof_z(y):
            return EAVE + (y - y_front) * slope

    else:
        slope = 0.64

        def roof_z(y):
            return EAVE + (DEPTH / 2 - abs(y)) * slope

    back_h = roof_z(y_back - PLANK)
    edges = [-hx + width * k / bays for k in range(bays + 1)]

    # --- the back wall, in two halves, with the stall partitions ---
    backs = {}
    for side in (-1, 1):
        xa, xb = sorted((0.0, side * hx))
        kit = Kit()
        kit.box((xa, y_back - PLANK, 0), (xb, y_back, back_h), wall_colour, skip=("-z",))
        for x in edges[1:-1]:
            if xa < x <= xb or (side < 0 and abs(x) < 1e-6):
                kit.box((x - 0.09, -0.5, 0), (x + 0.09, y_back - PLANK, 1.5), frame_colour, skip=("-z", "+y"))
        # Framing on the outside, and a shuttered window in each half.
        rear = shapes.Frame((0, y_back, 0), 90)
        ua, ub = -xb, -xa
        shapes.fquad(kit, rear, ua, ub, 1.3, 1.55, 0.03, frame_colour)
        for u in (ua + 0.15, ub - 0.15):
            shapes.fquad(kit, rear, u - 0.15, u + 0.15, 0, back_h, 0.04, frame_colour)
        um = (ua + ub) / 2
        shapes.fquad(kit, rear, um - 0.6, um + 0.6, 1.7, 2.4, 0.03, "trimWhite")
        shapes.fquad(kit, rear, um - 0.45, um + 0.45, 1.8, 2.3, 0.06, pal["door"])
        backs[side] = add(kit, "wall", "wood", 0)

    # --- the side walls, cut to the roof, with a cross brace outside ---
    sides = {}
    for side in (-1, 1):
        xa, xb = sorted((side * hx, side * (hx - PLANK)))
        section = [(y_front, 0), (y_back - PLANK, 0), (y_back - PLANK, back_h)]
        if roof_style == "pitched":
            section.append((0, roof_z(0)))
        section.append((y_front, EAVE))
        kit = Kit()
        kit.extrude_x(section, xa, xb, wall_colour)
        x = side * (hx + 0.03)
        for (ya, za), (yb, zb) in (((y_front + 0.3, 0.2), (y_back - 0.6, EAVE - 0.3)), ((y_back - 0.6, 0.2), (y_front + 0.3, EAVE - 0.3))):
            kit.poly([(x, ya - 0.16, za), (x, ya + 0.16, za), (x, yb + 0.16, zb), (x, yb - 0.16, zb)], (side, 0, 0), frame_colour)
        sides[side] = add(kit, "wall", "wood", 0, collider="hull")

    # --- posts along the front, and the beam they carry ---
    posts = {}
    for index, x in enumerate(edges[1:-1], start=1):
        kit = Kit()
        kit.box((x - POST / 2, y_front, 0), (x + POST / 2, y_front + POST, EAVE - 0.3), frame_colour, skip=("-z", "+z"))
        posts[index] = add(kit, "pillar", "wood", 0)
    holders = {0: sides[-1], bays: sides[1], **posts}  # what stands at each bay edge

    kit = Kit()
    kit.box((-hx + PLANK, y_front, EAVE - 0.3), (hx - PLANK, y_front + POST, EAVE), frame_colour)
    beam = add(kit, "band", "wood", 1, supports=list(holders.values()))

    # --- the roof ---
    over = 0.4
    thick = 0.22

    def fascia(kit, xa, xb, y, facing):
        """A white board along the eave."""
        z = roof_z(y)
        y += facing * 0.02
        kit.poly([(xa, y, z - 0.06), (xb, y, z - 0.06), (xb, y, z + thick + 0.04), (xa, y, z + thick + 0.04)], (0, facing, 0), "trimWhite")

    if roof_style == "mono":
        for side in (-1, 1):
            xa, xb = sorted((0.0, side * (hx + over)))
            ya, yb = y_front - over, y_back + over * 0.6
            kit = Kit()
            kit.slab([(xa, ya, roof_z(ya)), (xb, ya, roof_z(ya)), (xb, yb, roof_z(yb)), (xa, yb, roof_z(yb))], thick, pal["roof"])
            fascia(kit, xa, xb, ya, -1)
            add(kit, "roof", "tile", 1, supports=(backs[side], sides[side], beam), collider="hull")
    else:
        for facing in (-1, 1):
            ya = facing * (DEPTH / 2 + over)
            xo = hx + over
            kit = Kit()
            kit.slab([(-xo, ya, roof_z(ya)), (xo, ya, roof_z(ya)), (xo, 0, roof_z(0)), (-xo, 0, roof_z(0))], thick, pal["roof"])
            fascia(kit, -xo, xo, ya, facing)
            holding = (beam, sides[-1], sides[1]) if facing < 0 else (backs[-1], backs[1], sides[-1], sides[1])
            add(kit, "roof", "tile", 1, supports=holding, collider="hull")

    # --- stall doors, a horse, hay ---
    horse_bay = next(k for k in range(bays) if k != open_bay) if seed % 2 else next(k for k in reversed(range(bays)) if k != open_bay)
    for k in range(bays):
        xa, xb = edges[k] + POST / 2 + 0.06, edges[k + 1] - POST / 2 - 0.06
        mid = (xa + xb) / 2
        if k == open_bay:
            kit = Kit()
            kit.box((mid - 1.0, 0.5, 0), (mid + 1.0, 1.7, 0.8), "sunny", skip=("-z",))
            kit.box((mid - 0.75, 0.6, 0.8), (mid + 0.35, 1.6, 1.55), "sunny", skip=("-z",))
            kit.box((mid - 0.2, -1.6, 0), (mid + 1.0, -0.6, 0.7), "sunny", skip=("-z",))
            add(kit, "detail", "leaves", 0)
            continue
        y = y_front + 0.08
        kit = Kit()
        kit.box((xa, y, 0.15), (xb, y + 0.16, 1.45), pal["door"])
        y -= 0.03
        for za in (0.15, 1.23):
            kit.poly([(xa, y, za), (xb, y, za), (xb, y, za + 0.22), (xa, y, za + 0.22)], (0, -1, 0), "trimWhite")
        kit.poly([(xa, y, 0.37), (xa + 0.3, y, 0.37), (xb, y, 1.23), (xb - 0.3, y, 1.23)], (0, -1, 0), "trimWhite")
        door = add(kit, "detail", "wood", 0, supports=(holders[k], holders[k + 1]))

        if k == horse_bay:
            # A horse looking out over the door: a neck and a long head.
            kit = Kit()
            kit.extrude_x([(-1.3, 1.2), (-0.7, 1.2), (y_front - 0.1, 2.35), (y_front - 0.55, 2.35), (y_front - 0.55, 1.9)], mid - 0.24, mid + 0.24, horse_colour)
            muzzle = "tyre" if horse_colour != "tyre" else "trimWhite"
            kit.box((mid - 0.22, y_front - 1.25, 1.7), (mid + 0.22, y_front - 0.5, 2.2), horse_colour, sides={"-y": muzzle})
            for x in (mid - 0.2, mid + 0.12):
                kit.box((x, y_front - 0.35, 2.35), (x + 0.1, y_front - 0.2, 2.6), horse_colour, skip=("-z",))
            add(kit, "detail", "rubber", 0, supports=(door,), collider="hull")

    # --- a water trough outside ---
    x = trough_side * (hx - 1.6)
    kit = Kit()
    kit.box((x - 0.9, y_front - 1.5, 0), (x + 0.9, y_front - 0.85, 0.6), frame_colour, skip=("-z",), sides={"+z": "windowBlue"})
    add(kit, "detail", "wood", 0)

    return building.finish(look=f"w={width} bays={bays} {roof_style} open={open_bay} horse={horse_colour}/{wall_colour}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(15, 12))


if __name__ == "__main__":
    previews()
