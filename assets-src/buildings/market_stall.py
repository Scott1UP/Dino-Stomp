"""Market stall generator.

A small stall for the castle yard, about 3.5 m wide and 2.5 m deep: a wooden
counter across the front (-Y), four posts, a striped cloth canopy with a
scalloped valance, a painted sign on the counter, and open crates of bright
produce on top of it.

The seed varies the width, the canopy (one slope falling to the front, or a
ridge), its stripes, the produce, and whether a sack or a spare crate stands
beside the stall. The canopy's colour comes from the scheme's wall colour.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/market_stall.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_castle2 as castle  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "market_stall"
HITS_TO_COLLAPSE = 1  # small and flimsy
TRIANGLE_BUDGET = 400

DEPTH = 2.5
POST = 0.24
COUNTER = 1.05  # counter height
PRODUCE = ["tomato", "leaf", "tangerine", "sunny", "bubblegum"]


def build(building_id, seed, scheme=None, collection=None):
    """Build one stall. Returns (empty, stats)."""
    rng = random.Random(seed)

    width = rng.choice([3.2, 3.5, 3.8])
    canopy_style = rng.choice(["slope", "ridge", "slope"])
    stripes = rng.choice([5, 7])
    produce = rng.sample(PRODUCE, 3)
    extra = rng.choice(["sack", "crate", "none"])
    extra_side = rng.choice([-1, 1])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]
    cloth = pal["wall"]

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    hx, hy = width / 2, DEPTH / 2
    z_front = 2.5
    z_back = 3.1 if canopy_style == "slope" else 2.5
    z_ridge = 3.3

    # --- the counter: a plank box with a darker top and a painted sign ---
    kit = Kit()
    kit.box((-hx + POST, -hy + 0.04, 0), (hx - POST, -hy + 0.85, COUNTER - 0.12), "wood", skip=("-z", "+z"))
    kit.box((-hx - 0.08, -hy - 0.1, COUNTER - 0.12), (hx + 0.08, -hy + 0.95, COUNTER), "doorBrown")
    face = shapes.Frame((0, -hy + 0.04, 0), -90)
    shapes.fquad(kit, face, -hx * 0.62, hx * 0.62, 0.25, 0.75, 0.03, "trimWhite")
    for k in (-1, 0, 1):
        shapes.fquad(kit, face, k * hx * 0.36 - 0.14, k * hx * 0.36 + 0.14, 0.36, 0.64, 0.06, produce[k + 1])
    counter = add(kit, "wall", "wood", 0)

    # --- four posts ---
    posts = []
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (hx - POST / 2), sy * (hy - POST / 2)
            top = z_front if sy < 0 else z_back
            kit = Kit()
            kit.box((x - POST / 2, y - POST / 2, 0), (x + POST / 2, y + POST / 2, top), "doorBrown", skip=("-z", "+z"))
            posts.append(add(kit, "pillar", "wood", 0))

    # --- the striped canopy ---
    over = 0.35
    xo = hx + over
    ya, yb = -hy - over, hy + over * 0.5
    if canopy_style == "slope":
        rise = (z_back - z_front) / DEPTH

        def top_z(y):
            return z_front + 0.08 + (y + hy) * rise

        runs = [(ya, yb)]
    else:

        def top_z(y):
            return z_front + 0.08 + (z_ridge - z_front) * (1 - abs(y) / (hy + over))

        yb = hy + over
        runs = [(ya, 0.0), (0.0, yb)]
    kit = Kit()
    for k in range(stripes):
        xa = -xo + 2 * xo * k / stripes
        xb = -xo + 2 * xo * (k + 1) / stripes
        colour = cloth if k % 2 == 0 else "trimWhite"
        for y0, y1 in runs:
            kit.poly([(xa, y0, top_z(y0)), (xb, y0, top_z(y0)), (xb, y1, top_z(y1)), (xa, y1, top_z(y1))], (0, 0, 1), colour)
        # The valance: a scallop hanging off the front edge.
        z = top_z(ya)
        kit.poly([(xa, ya, z), (xb, ya, z), (xb, ya, z - 0.3), ((xa + xb) / 2, ya, z - 0.48), (xa, ya, z - 0.3)], (0, -1, 0), colour)
    for y0, y1 in runs:  # the underside
        kit.poly([(-xo, y0, top_z(y0) - 0.07), (xo, y0, top_z(y0) - 0.07), (xo, y1, top_z(y1) - 0.07), (-xo, y1, top_z(y1) - 0.07)], (0, 0, -1), cloth)
    kit.poly([(-xo, ya + 0.04, top_z(ya)), (xo, ya + 0.04, top_z(ya)), (xo, ya + 0.04, top_z(ya) - 0.3), (-xo, ya + 0.04, top_z(ya) - 0.3)], (0, 1, 0), cloth)
    for x, facing in ((-xo, -1), (xo, 1)):
        outline = [(x, ya, top_z(ya)), (x, ya, top_z(ya) - 0.07), (x, yb, top_z(yb) - 0.07), (x, yb, top_z(yb))]
        if canopy_style == "ridge":
            outline.append((x, 0, top_z(0)))
        kit.poly(outline, (facing, 0, 0), cloth)
    kit.poly([(-xo, yb, top_z(yb)), (xo, yb, top_z(yb)), (xo, yb, top_z(yb) - 0.07), (-xo, yb, top_z(yb) - 0.07)], (0, 1, 0), cloth)
    add(kit, "roof", "rubber", 1, supports=posts, collider="hull")

    # --- crates of produce on the counter, tipped towards the customer ---
    count = 3
    for k in range(count):
        x = (k - 1) * (width - 0.9) / count
        colour = produce[k]
        y0, y1 = -hy + 0.02, -hy + 0.8
        z0, z1 = COUNTER + 0.34, COUNTER + 0.55  # front and back rim heights
        xa, xb = x - 0.42, x + 0.42
        kit = Kit()
        bottom = [(xa, y0, COUNTER), (xb, y0, COUNTER), (xb, y1, COUNTER), (xa, y1, COUNTER)]
        rim = [(xa, y0, z0), (xb, y0, z0), (xb, y1, z1), (xa, y1, z1)]
        kit.convex([bottom, rim] + [[bottom[i], bottom[(i + 1) % 4], rim[(i + 1) % 4], rim[i]] for i in range(4)], "wood", {1: colour})
        # A heap of produce.
        inner = [(xa + 0.1, y0 + 0.1, z0 + 0.03), (xb - 0.1, y0 + 0.1, z0 + 0.03), (xb - 0.1, y1 - 0.1, z1 - 0.02), (xa + 0.1, y1 - 0.1, z1 - 0.02)]
        apex = (x, (y0 + y1) / 2, z1 + 0.3)
        for i in range(4):
            kit.poly([inner[i], inner[(i + 1) % 4], apex], (inner[i][0] + inner[(i + 1) % 4][0] - 2 * x, inner[i][1] + inner[(i + 1) % 4][1] - y0 - y1, 1), colour)
        add(kit, "detail", "wood", 0, supports=(counter,), collider="hull")

    # --- something standing beside the stall ---
    if extra != "none":
        x = extra_side * (hx + 0.75)
        kit = Kit()
        if extra == "sack":
            shapes.frustum(kit, 0.42, 0.5, 0, 0.6, "interiorCream", sides=6, cx=x, cy=0.2, top=False, bottom=False)
            shapes.frustum(kit, 0.5, 0.2, 0.6, 1.0, "interiorCream", sides=6, cx=x, cy=0.2, bottom=False)
            add(kit, "detail", "leaves", 0, collider="hull")
        else:
            kit.box((x - 0.45, -0.3, 0), (x + 0.45, 0.6, 0.7), "wood", skip=("-z",), sides={"+z": produce[0]})
            castle.pyramid(kit, x, 0.15, 0.33, 0.33, 0.7, 0.3, produce[0])
            add(kit, "detail", "wood", 0, collider="hull")

    return building.finish(look=f"w={width} {canopy_style}/stripes-{stripes}/{cloth}/{'-'.join(produce)}/{extra}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 8))


if __name__ == "__main__":
    previews()
