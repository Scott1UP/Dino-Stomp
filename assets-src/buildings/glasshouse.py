"""Glasshouse generator.

A long park glasshouse: a thin white frame on a low coloured plinth, tinted
glass panels, a door in the middle of the front, a glass roof and plant pots
inside (they show once the glass comes away). The seed varies the number and
width of bays, the roof (pitched, faceted barrel curve, or pitched with a
raised lantern along the ridge), glazing bars, ridge finials and the plants.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/glasshouse.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "glasshouse"
HITS_TO_COLLAPSE = 2  # medium building
TRIANGLE_BUDGET = 900

FRAME = 0.25  # thickness of the frame
POST = 0.2  # width of a frame post
RAIL = 0.25  # height of the top rail
PLINTH = 0.55
SHEET = 0.14  # thickness of a roof pane
GLASS = "glassTint"


def build(building_id, seed, scheme=None, collection=None):
    """Build one glasshouse. Returns (empty, stats)."""
    rng = random.Random(seed)

    bays = rng.choice([4, 5, 5])
    bay_w = rng.choice([2.8, 3.0, 3.2])
    depth = rng.choice([5.5, 6.0, 6.5])
    wall_h = rng.choice([2.6, 2.9, 3.2])
    roof_form = rng.choice(["pitched", "curved", "lantern", "curved"])
    rise = rng.choice([1.8, 2.3, 2.8])
    mullions = rng.choice([0, 1, 1])
    finials = rng.random() < 0.6
    pot_count = rng.choice([3, 4])
    plants = [rng.choice(["bush", "spike", "tree"]) for _ in range(4)]
    porch = rng.random() < 0.5
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]
    trim = pal["trim"]
    if bays == 5 and roof_form == "curved":
        pot_count = 3  # the biggest glasshouse is at the edge of its triangle budget

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    x0 = -bays * bay_w / 2 - FRAME
    x1 = -x0
    front = -depth / 2
    back = depth / 2
    glass_top = wall_h - RAIL
    top = wall_h + rise
    door_bay = bays // 2

    def glazed_bay(xa, xb, y_out, inward, door):
        """One bay of a long wall: a post on its left, a top rail, a plinth and a pane."""
        kit = Kit()
        lo, hi = sorted((y_out, y_out + FRAME * inward))
        y_mid = (lo + hi) / 2
        out_hint = (0, -inward, 0)
        kit.box((xa, lo, 0), (xa + POST, hi, wall_h), trim, skip=("-z",))
        kit.box((xa + POST, lo, glass_top), (xb, hi, wall_h), trim, skip=("-x",))
        pane_z0 = 0 if door else PLINTH
        for y, hint in ((y_mid - 0.01 * inward, out_hint), (y_mid + 0.01 * inward, (0, inward, 0))):
            kit.poly([(xa + POST, y, pane_z0), (xb, y, pane_z0), (xb, y, glass_top), (xa + POST, y, glass_top)], hint, GLASS)
        if door:
            mid = (xa + POST + xb) / 2
            kit.box((mid - 0.75, lo - 0.04, 0), (mid + 0.75, hi + 0.04, 2.4), pal["door"], skip=("-z",))
            kit.box((xa + POST, lo, 0), (mid - 0.75, hi, PLINTH), pal["wall"], skip=("-z", "-x", "+x"))
            kit.box((mid + 0.75, lo, 0), (xb, hi, PLINTH), pal["wall"], skip=("-z", "-x"))
        else:
            kit.box((xa + POST, lo, 0), (xb, hi, PLINTH), pal["wall"], skip=("-z", "-x"))
            kit.shine(xa + POST, xb, PLINTH, glass_top, y_mid - 0.04 * inward, out_hint, "trimWhite")
            for m in range(mullions):
                x = xa + POST + (xb - xa - POST) * (m + 1) / (mullions + 1)
                kit.poly(
                    [(x - 0.06, y_out, PLINTH), (x + 0.06, y_out, PLINTH), (x + 0.06, y_out, glass_top), (x - 0.06, y_out, glass_top)],
                    out_hint,
                    trim,
                )
        return add(kit, "wall", "glass", 0)

    # --- long walls ---
    front_walls = []
    back_walls = []
    for b in range(bays):
        xa = x0 + FRAME + b * bay_w
        front_walls.append(glazed_bay(xa, xa + bay_w, front, 1, door=b == door_bay))
        back_walls.append(glazed_bay(xa, xa + bay_w, back, -1, door=False))

    # --- a little gabled porch over the door ---
    if porch:
        mid = x0 + FRAME + door_bay * bay_w + (POST + bay_w) / 2
        porch_z = min(2.6, wall_h - 0.2)
        kit = Kit()
        for x in (mid - 1.05, mid + 1.05):
            kit.box((x - 0.09, front - 1.4, 0), (x + 0.09, front - 1.22, porch_z), trim, skip=("-z", "+z"))
        kit.extrude_y([(mid - 1.4, porch_z), (mid + 1.4, porch_z), (mid, porch_z + 1.0)], front - 1.6, front, pal["roof"])
        add(kit, "detail", "glass", 0, supports=(front_walls[door_bay],), collider="hull")

    # --- roof shape: the front half's profile from eave to ridge, as (y, z) ---
    if roof_form == "curved":
        profile = [(front - 0.12, wall_h - 0.05), (front * 0.707, wall_h + rise * 0.707), (0.0, top)]
        gable = [(front, wall_h), (front * 0.707, wall_h + rise * 0.707), (0.0, top), (back * 0.707, wall_h + rise * 0.707), (back, wall_h)]
    else:
        slope = rise / (depth / 2)
        profile = [(front - 0.25, wall_h - 0.25 * slope), (0.0, top)]
        gable = [(front, wall_h), (0.0, top), (back, wall_h)]

    # --- end walls, each with a glass gable above ---
    for xa, outward in ((x0, -1), (x1 - FRAME, 1)):
        kit = Kit()
        kit.box((xa, front, 0), (xa + FRAME, back, wall_h), trim, skip=("-z",))
        x_out = xa - 0.03 if outward < 0 else xa + FRAME + 0.03
        x_in = xa + FRAME + 0.03 if outward < 0 else xa - 0.03
        for ya, yb in ((front + 0.3, -0.1), (0.1, back - 0.3)):
            for x, hint in ((x_out, (outward, 0, 0)), (x_in, (-outward, 0, 0))):
                kit.poly([(x, ya, PLINTH), (x, yb, PLINTH), (x, yb, glass_top), (x, ya, glass_top)], hint, GLASS)
        w = back - 0.3 - 0.1
        h = glass_top - PLINTH
        xs = x_out + 0.03 * outward
        kit.poly(
            [
                (xs, 0.1 + w * 0.18, PLINTH + h * 0.52),
                (xs, 0.1 + w * 0.32, PLINTH + h * 0.52),
                (xs, 0.1 + w * 0.62, PLINTH + h * 0.86),
                (xs, 0.1 + w * 0.48, PLINTH + h * 0.86),
            ],
            (outward, 0, 0),
            "trimWhite",
        )
        if outward < 0:
            kit.box((xa - 0.07, front, 0), (xa, back, PLINTH), pal["wall"], skip=("-z", "+x"))
        else:
            kit.box((xa + FRAME, front, 0), (xa + FRAME + 0.07, back, PLINTH), pal["wall"], skip=("-z", "-x"))
        end = add(kit, "wall", "glass", 0)

        kit = Kit()
        kit.extrude_x(gable, xa, xa + FRAME, GLASS)
        kit.poly(
            [(x_out, -0.08, wall_h), (x_out, 0.08, wall_h), (x_out, 0.08, top - 0.1), (x_out, -0.08, top - 0.1)],
            (outward, 0, 0),
            trim,
        )
        add(kit, "wall", "glass", 1, supports=(end,), collider="hull")

    # --- roof: one piece per bay, front and back ---
    roof_front = []
    roof_back = []
    for b in range(bays):
        xa = x0 + FRAME + b * bay_w - (FRAME + 0.15 if b == 0 else 0)
        xb = x0 + FRAME + (b + 1) * bay_w + (FRAME + 0.15 if b == bays - 1 else 0)
        for sign, walls, bucket in ((1, front_walls, roof_front), (-1, back_walls, roof_back)):
            kit = Kit()
            for k in range(len(profile) - 1):
                ya, za = profile[k]
                yb, zb = profile[k + 1]
                ya, yb = ya * sign, yb * sign
                kit.extrude_x([(ya, za), (yb, zb), (yb, zb + SHEET), (ya, za + SHEET)], xa, xb, GLASS)
                # Glazing bars, laid on the glass.
                e = SHEET + 0.02
                edges = ((xa, xa + 0.12),) if len(profile) > 2 else ((xa, xa + 0.12), (xb - 0.12, xb))
                for ea, eb in edges:
                    kit.poly([(ea, ya, za + e), (eb, ya, za + e), (eb, yb, zb + e), (ea, yb, zb + e)], (0, 0, 1), trim)
            bucket.append(add(kit, "roof", "glass", 1, supports=(walls[b],), collider="hull"))

    # --- ridge: a beam with finials, or a raised lantern ---
    ridge_z = top + SHEET
    if roof_form == "lantern":
        half = 0.9
        lz0 = top - rise * half / (depth / 2)
        lz1 = top + 0.75
        la = x0 + FRAME + bay_w * 0.6
        lb = x1 - FRAME - bay_w * 0.6
        for xa, xb, covered in ((la, 0.0, range(0, door_bay + 1)), (0.0, lb, range(door_bay, bays))):
            kit = Kit()
            kit.box((xa, -half, lz0), (xb, half, lz1), GLASS, skip=("-z",), sides={"-x": trim, "+x": trim})
            kit.extrude_x([(-half - 0.3, lz1), (half + 0.3, lz1), (0.0, lz1 + 0.75)], xa - (0.25 if xa == la else 0), xb + (0.25 if xb == lb else 0), pal["roof"])
            supports = [roof_front[b] for b in covered] + [roof_back[b] for b in covered]
            add(kit, "roof", "glass", 2, supports=supports, collider="hull")
    else:
        kit = Kit()
        kit.box((x0 - 0.3, -0.15, ridge_z - 0.06), (x1 + 0.3, 0.15, ridge_z + 0.2), trim)
        if finials:
            for x in (x0 - 0.1, x1 + 0.1):
                shapes.frustum(kit, 0.24, 0, ridge_z + 0.2, ridge_z + 1.1, pal["roof"], sides=4, cx=x, bottom=False)
        add(kit, "detail", "glass", 2, supports=roof_front + roof_back)

    # --- plant pots inside, along the back ---
    for n in range(pot_count):
        px = (x0 + x1) / 2 + (n - (pot_count - 1) / 2) * (x1 - x0 - 3.0) / max(pot_count - 1, 1)
        py = back - FRAME - 1.1
        kit = Kit()
        shapes.frustum(kit, 0.4, 0.58, 0, 0.75, "tangerine", sides=5, cx=px, cy=py, bottom=False)
        plant = plants[n]
        if plant == "bush":
            shapes.ball(kit, px, py, 1.3, 0.7, "leaf", sides=4)
        elif plant == "spike":
            shapes.frustum(kit, 0.5, 0, 0.75, min(2.4, wall_h - 0.4), "leaf", sides=5, cx=px, cy=py, bottom=False)
        else:
            kit.box((px - 0.09, py - 0.09, 0.75), (px + 0.09, py + 0.09, 1.5), "doorBrown", skip=("-z", "+z"))
            shapes.ball(kit, px, py, 1.9, 0.6, "leaf", sides=4)
        add(kit, "detail", "leaves", 0, collider="hull")

    return building.finish(
        look=f"bays={bays}x{bay_w} depth={depth} h={wall_h} {roof_form}/rise-{rise}/mullions-{mullions}"
        + ("/finials" if finials and roof_form != "lantern" else "")
        + ("/porch" if porch else "")
        + f"/pots-{pot_count}"
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(30, 24))


if __name__ == "__main__":
    previews()
