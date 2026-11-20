"""Park café generator.

A one-storey café with a flat roof, big windows, a striped awning across the
front and café tables with parasols outside. The seed varies its size, where
the door is, the window shape, the awning's colours and depth, the parapet
(a raised sign board, steps or corner blocks) and the tables and parasols.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/cafe.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "cafe"
HITS_TO_COLLAPSE = 1  # small building
TRIANGLE_BUDGET = 400

WALL = 0.35
BRIGHTS = ["tomato", "sunny", "cobalt", "tangerine", "bubblegum"]


def build(building_id, seed, scheme=None, collection=None):
    """Build one café. Returns (empty, stats)."""
    rng = random.Random(seed)

    width = rng.choice([8.4, 9.0, 9.6])
    depth = rng.choice([6.4, 7.0, 7.4])
    height = rng.choice([3.1, 3.4, 3.7])
    door_bay = rng.choice([0, 1, 1, 2])
    window_style = rng.choice(["big", "tall", "wide"])
    awning_reach = rng.choice([1.2, 1.5, 1.8])
    parapet = rng.choice(["sign", "steps", "corners"])
    table_count = rng.choice([2, 3, 3])
    parasols = rng.sample(BRIGHTS, 3)
    parasol_style = rng.choice(["solid", "stripes"])
    awning_accent = rng.choice(BRIGHTS)
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    colours = {
        "wall": pal["wall"],
        "interior": "interiorCream",
        "trim": pal["trim"],
        "glass": "windowBlue",
        "shine": "windowShine",
        "door": pal["door"],
    }
    stripe_a = pal["roof"] if pal["roof"] != pal["wall"] else awning_accent
    stripe_b = pal["trim"]

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    x0 = -width / 2
    x1 = width / 2
    front = -depth / 2
    back = depth / 2
    bay = width / 3

    def window(mid):
        if window_style == "tall":
            return {"x0": mid - 0.95, "x1": mid + 0.95, "z0": 0.35, "z1": height - 0.9, "kind": "window"}
        if window_style == "wide":
            return {"x0": mid - 1.2, "x1": mid + 1.2, "z0": 1.0, "z1": height - 0.9, "kind": "window"}
        return {"x0": mid - 1.1, "x1": mid + 1.1, "z0": 0.7, "z1": height - 0.9, "kind": "window"}

    # --- front: a door bay and two big windows, each under a striped awning ---
    front_walls = []
    awn_top = height - 0.3
    awn_low = height - 0.95
    for b in range(3):
        xa = x0 + b * bay
        xb = xa + bay
        mid = (xa + xb) / 2
        kit = Kit()
        if b == door_bay:
            opening = {"x0": mid - 0.75, "x1": mid + 0.75, "z0": 0.0, "z1": 2.5, "kind": "door"}
        else:
            opening = window(mid)
        kit.wall(xa, xb, 0, height, front, WALL, 1, [opening], colours)
        wall = add(kit, "wall", "plaster", 0)
        front_walls.append(wall)

        kit = Kit()
        ya = front - awning_reach
        kit.extrude_x(
            [(front, awn_top), (ya, awn_low), (ya, awn_low - 0.3), (front, awn_top - 0.15)],
            xa + 0.04,
            xb - 0.04,
            stripe_a,
        )
        # Two lighter stripes on the slope and down the front edge.
        for s in (1, 3):
            sa = xa + 0.04 + (bay - 0.08) * s / 4
            sb = sa + (bay - 0.08) / 4
            kit.poly([(sa, front, awn_top + 0.02), (sb, front, awn_top + 0.02), (sb, ya, awn_low + 0.02), (sa, ya, awn_low + 0.02)], (0, 0, 1), stripe_b)
            kit.poly([(sa, ya - 0.02, awn_low), (sb, ya - 0.02, awn_low), (sb, ya - 0.02, awn_low - 0.3), (sa, ya - 0.02, awn_low - 0.3)], (0, -1, 0), stripe_b)
        add(kit, "detail", "wood", 0, supports=(wall,), collider="hull")

    # --- back: plain bays either side of a window ---
    back_walls = []
    for b in range(3):
        xa = x0 + b * bay
        xb = xa + bay
        mid = (xa + xb) / 2
        kit = Kit()
        openings = [{"x0": mid - 0.8, "x1": mid + 0.8, "z0": 1.1, "z1": height - 0.9, "kind": "window"}] if b == 1 else []
        kit.wall(xa, xb, 0, height, back, WALL, -1, openings, colours)
        back_walls.append(add(kit, "wall", "plaster", 0))

    # --- side walls ---
    side_walls = []
    for xa, inner in ((x0, "+x"), (x1 - WALL, "-x")):
        kit = Kit()
        kit.box((xa, front + WALL, 0), (xa + WALL, back - WALL, height), pal["wall"], sides={inner: "interiorCream"}, skip=("-z",))
        side_walls.append(add(kit, "wall", "plaster", 0))

    # --- flat roof in two halves, with a parapet feature at the front ---
    over = 0.3
    roofs = []
    for xa, xb, walls in (
        (x0 - over, 0.0, (front_walls[0], back_walls[0], side_walls[0])),
        (0.0, x1 + over, (front_walls[2], back_walls[2], side_walls[1])),
    ):
        kit = Kit()
        kit.box((xa, front - over, height), (xb, back + over, height + 0.28), pal["trim"])
        roofs.append(add(kit, "roof", "plaster", 1, supports=walls))

    kit = Kit()
    rz = height + 0.28
    if parapet == "sign":
        kit.box((-width * 0.28, front - over, rz), (width * 0.28, front + 0.15, rz + 1.2), pal["roof"], skip=("-z",))
        # A cup on the sign board.
        kit.poly(
            [(-0.5, front - over - 0.03, rz + 0.25), (0.5, front - over - 0.03, rz + 0.25), (0.7, front - over - 0.03, rz + 0.95), (-0.7, front - over - 0.03, rz + 0.95)],
            (0, -1, 0),
            "trimWhite",
        )
    elif parapet == "steps":
        kit.box((-width * 0.36, front - over, rz), (width * 0.36, front + 0.15, rz + 0.55), pal["wall"], skip=("-z",))
        kit.box((-width * 0.16, front - over, rz + 0.55), (width * 0.16, front + 0.15, rz + 1.1), pal["wall"], skip=("-z",))
    else:
        for x in (x0 - over, x1 + over - 0.9):
            kit.box((x, front - over, rz), (x + 0.9, front - over + 0.9, rz + 0.8), pal["roof"], skip=("-z",))
    add(kit, "detail", "plaster", 1, supports=roofs)

    # --- café tables with parasols, out past the awning ---
    table_y = front - awning_reach - 2.3
    for t in range(table_count):
        tx = (t - (table_count - 1) / 2) * (width / table_count) + (0.3 if t % 2 else -0.3)
        ty = table_y + (0.5 if t % 2 else 0.0)
        colour = parasols[t]
        kit = Kit()
        kit.box((tx - 0.07, ty - 0.07, 0), (tx + 0.07, ty + 0.07, 2.5), "trimWhite", skip=("-z", "+z"))
        shapes.frustum(kit, 0.85, 0.85, 0.85, 0.97, "trimWhite", sides=6, cx=tx, cy=ty)
        shapes.frustum(
            kit,
            1.5,
            0,
            2.3,
            3.05,
            colour,
            sides=6,
            cx=tx,
            cy=ty,
            stripes=[colour, "trimWhite"] if parasol_style == "stripes" else None,
        )
        add(kit, "detail", "wood", 0, collider="hull")

    return building.finish(
        look=f"{width}x{depth} h={height} door-{door_bay}/{window_style}/awning-{awning_reach}/{parapet}/tables-{table_count}/{parasol_style}"
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(22, 24))


if __name__ == "__main__":
    previews()
