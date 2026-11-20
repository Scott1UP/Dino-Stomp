"""Fire station generator.

A two-storey engine house about 12 x 9 m with two big bright-red engine doors,
a flat roof behind a parapet, and a tall hose tower at one side with an open
look-out and a bell at the top. The seed varies which side the tower stands
on and how far back, its height and its top (pyramid, flat cap or dome), the
engine doors (glazed panels or stripes), the upper windows, the badge over
the doors and the stripe round the building.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/fire_station.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import flat, frustum, plaque, polygon, round_window  # noqa: E402
from lib.shapes_town2 import door, flatten, floor_slab, shell_storey, split, wall_colours, window  # noqa: E402

TYPE = "fire_station"
HITS_TO_COLLAPSE = 2  # medium building
TRIANGLE_BUDGET = 1300

WALL = 0.35
DOOR_RED = "tomato"


def build(building_id, seed, scheme=None, collection=None):
    """Build one fire station. Returns (empty, stats)."""
    rng = random.Random(seed)

    # --- the station's character ---
    tower_side = -1 if seed % 2 else 1  # cycled, so neighbouring seeds always differ
    tower_at = rng.choice(["front", "front", "back"])
    tower_stages = rng.choice([3, 3, 4])
    tower_top = ("pyramid", "dome", "flat")[seed % 3]
    tower_w = rng.choice([3.0, 3.3])
    hall_w = rng.choice([8.6, 9.0, 9.4])
    depth = rng.choice([8.5, 9.0, 9.5])
    ground = rng.choice([3.8, 4.1])
    upper = rng.choice([2.9, 3.1])
    door_style = rng.choice(["glazed", "stripes", "glazed"])
    upper_windows = rng.choice(["pair", "wide"])
    badge = rng.choice(["badge", "badge", "none"])
    parapet = rng.choice(["plain", "stepped"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    # The engine doors are always red, so a red-walled scheme gets white walls instead.
    wall_colour = pal["wall"] if pal["wall"] != DOOR_RED else "trimWhite"
    stripe = "sunny" if wall_colour != "sunny" else "tomato"
    colours = wall_colours(pal, wall=wall_colour, door=DOOR_RED)

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    total_w = hall_w + tower_w
    if tower_side < 0:
        tx0 = -total_w / 2
        hx0, hx1 = tx0 + tower_w, total_w / 2
    else:
        hx0, hx1 = -total_w / 2, total_w / 2 - tower_w
        tx0 = hx1
    tx1 = tx0 + tower_w
    front, back = -depth / 2, depth / 2
    ty0 = front if tower_at == "front" else back - tower_w
    ty1 = ty0 + tower_w
    bounds = (hx0, hx1, front, back)
    top = ground + upper
    bay_w = hall_w / 2
    door_w = bay_w - 1.0
    door_h = ground - 0.75

    # --- ground floor: the two engine doors, and a back door and windows ---
    def ground_openings(side, i, a, b):
        mid = (a + b) / 2
        if side == "front":
            return [door(mid, 0, door_w, door_h)]
        if side == "back":
            if i == 0:
                return [door(a + 1.3, 0), window(b - 1.4, 0, 1.4, 1.5, 1.0)]
            return [window(mid, 0, 2.0, 1.5, 1.0)]
        if (side == "left") == (tower_side > 0):  # only the open side has windows
            return [window(mid, 0, 1.6, 1.6, 1.0)]
        return []

    def ground_extra(kit, side, i, a, b):
        if side != "front":
            return
        mid = (a + b) / 2
        y = front + 0.13 - 0.03
        x0, x1 = mid - door_w / 2 + 0.3, mid + door_w / 2 - 0.3
        if door_style == "glazed":
            # A row of little panes across the top of the door, and a white rail under them.
            panes = 3
            step = (x1 - x0) / panes
            for p in range(panes):
                pa, pb = x0 + p * step + 0.1, x0 + (p + 1) * step - 0.1
                z0, z1 = door_h - 1.25, door_h - 0.35
                kit.poly([(pa, y, z0), (pb, y, z0), (pb, y, z1), (pa, y, z1)], (0, -1, 0), "windowBlue")
            kit.shine(x0 + 0.1, x0 + step - 0.1, door_h - 1.25, door_h - 0.35, y - 0.03, (0, -1, 0), "windowShine")
            kit.poly([(x0, y, 0.9), (x1, y, 0.9), (x1, y, 1.15), (x0, y, 1.15)], (0, -1, 0), "trimWhite")
        else:
            for z in (0.7, 1.5, 2.3):
                if z + 0.3 < door_h:
                    kit.poly([(x0, y, z), (x1, y, z), (x1, y, z + 0.28), (x0, y, z + 0.28)], (0, -1, 0), "trimWhite")
        # The apron the engines roll out over.
        kit.box((mid - door_w / 2, front - 0.9, 0), (mid + door_w / 2, front, 0.08), "stone", skip=("-z", "+y"))

    bays = {"front": split(hx0, hx1, bay_w), "back": split(hx0, hx1, bay_w)}
    walls0 = shell_storey(add, bounds, 0, ground, 0, colours, below=None, openings=ground_openings, extra=ground_extra, bays=bays)

    # --- upper floor ---
    def upper_openings(side, i, a, b):
        mid = (a + b) / 2
        if side in ("front", "back"):
            if upper_windows == "pair" and side == "front":
                return [window(mid - 1.05, ground, 1.3, 1.5, 0.8), window(mid + 1.05, ground, 1.3, 1.5, 0.8)]
            return [window(mid, ground, 2.6, 1.4, 0.85)]
        if (side == "left") == (tower_side > 0):
            return [window(mid, ground, 1.6, 1.4, 0.85)]
        return []

    def upper_extra(kit, side, i, a, b):
        if side == "front":
            # The stripe that runs over the engine doors.
            kit.box((a, front - 0.1, ground + 0.05), (b, front, ground + 0.45), stripe, skip=("+y",))

    floor_slab(add, bounds, ground, 1, flatten(walls0), pieces=2)
    walls1 = shell_storey(add, bounds, ground, top, 1, colours, below=walls0, openings=upper_openings, extra=upper_extra, bays=bays)

    # --- the badge between the upper windows ---
    if badge == "badge":
        kit = Kit()
        centre = ((hx0 + hx1) / 2, front - 0.02, ground + upper * 0.55)
        plaque(kit, centre, (0, -1, 0), polygon(0.95), 0.18, "sunny")
        flat(kit, centre, (0, -1, 0), polygon(0.6), DOOR_RED, lift=0.21)
        flat(kit, centre, (0, -1, 0), polygon(0.25, 4, phase=0), "trimWhite", lift=0.24)
        add(kit, "detail", "tin", 1, supports=walls1["front"])

    # --- flat roof in two halves, each with its share of the parapet ---
    para = 0.7
    roof_ids = []
    for i, (a, b) in enumerate(bays["front"]):
        kit = Kit()
        kit.box((a, front, top), (b, back, top + 0.25), "stone", sides={"-z": "interiorCream"})
        z0, z1 = top + 0.25, top + 0.25 + para
        lift = 0.5 if parapet == "stepped" else 0.0
        kit.box((a, front, z0), (b, front + 0.35, z1), wall_colour, skip=("-z",))
        kit.box((a, back - 0.35, z0), (b, back, z1), wall_colour, skip=("-z",))
        xa, xb = (a, a + 0.35) if i == 0 else (b - 0.35, b)
        kit.box((xa, front + 0.35, z0), (xb, back - 0.35, z1), wall_colour, skip=("-z",))
        if lift:  # a raised middle to the front parapet
            xm0, xm1 = (b - 2.2, b) if i == 0 else (a, a + 2.2)
            kit.box((xm0, front, z1), (xm1, front + 0.35, z1 + lift), pal["trim"], skip=("-z",))
        holders = [walls1["front"][i], walls1["back"][i]]
        roof_ids.append(add(kit, "roof", "stone", 2, supports=holders))

    # --- a roof light, so the big flat roof is not bare from the high camera ---
    lx = (hx0 + hx1) / 2 + rng.choice([-1.6, 0.0, 1.6])
    kit = Kit()
    kit.box((lx - 1.3, 0.2, top + 0.25), (lx + 1.3, 2.4, top + 1.0), "trimWhite", sides={"+z": "windowBlue"}, skip=("-z",))
    kit.poly(
        [(lx - 0.7, 1.0, top + 1.03), (lx - 0.3, 1.0, top + 1.03), (lx + 0.6, 1.9, top + 1.03), (lx + 0.2, 1.9, top + 1.03)],
        (0, 0, 1),
        "windowShine",
    )
    kit.box((lx - 0.5, -2.2, top + 0.25), (lx + 0.5, -1.2, top + 0.9), stripe, skip=("-z",))
    add(kit, "detail", "tin", 2, supports=roof_ids)

    # --- hose tower: closed stages, then an open look-out with a bell ---
    stage_h = 3.0 if tower_stages == 3 else 2.6
    tmx, tmy = (tx0 + tx1) / 2, (ty0 + ty1) / 2
    out_normal = (tower_side, 0, 0)
    x_out = tx0 if tower_side < 0 else tx1
    below = None
    for s in range(tower_stages):
        z0, z1 = s * stage_h, (s + 1) * stage_h
        kit = Kit()
        kit.box((tx0, ty0, z0), (tx1, ty1, z1 - 0.25), wall_colour)
        kit.box((tx0 - 0.12, ty0 - 0.12, z1 - 0.25), (tx1 + 0.12, ty1 + 0.12, z1), stripe if s == tower_stages - 1 else pal["trim"])
        if s == 0:
            y_face, normal = (ty0, (0, -1, 0)) if tower_at == "front" else (ty1, (0, 1, 0))
            flat(kit, (tmx, y_face, 0), normal, [(-0.65, 0), (0.65, 0), (0.65, 2.3), (-0.65, 2.3)], pal["trim"], lift=0.03)
            flat(kit, (tmx, y_face, 0), normal, [(-0.5, 0), (0.5, 0), (0.5, 2.15), (-0.5, 2.15)], DOOR_RED, lift=0.06)
        else:
            round_window(kit, (tmx, ty0, (z0 + z1) / 2 - 0.1), (0, -1, 0), 0.7, pal["trim"])
            round_window(kit, (tmx, ty1, (z0 + z1) / 2 - 0.1), (0, 1, 0), 0.7, pal["trim"])
            round_window(kit, (x_out, tmy, (z0 + z1) / 2 - 0.1), out_normal, 0.7, pal["trim"])
        below = add(kit, "wall", "plaster", s, supports=(below,) if below else ())

    z = tower_stages * stage_h
    s = tower_stages
    look = 2.4
    kit = Kit()
    for sx in (-1, 1):
        for sy in (-1, 1):
            xa, xb = sorted((tmx + sx * tower_w / 2, tmx + sx * (tower_w / 2 - 0.45)))
            ya, yb = sorted((tmy + sy * tower_w / 2, tmy + sy * (tower_w / 2 - 0.45)))
            kit.box((xa, ya, z), (xb, yb, z + look), pal["trim"], skip=("-z", "+z"))
    posts = add(kit, "corner", "plaster", s, supports=(below,))

    kit = Kit()
    kit.box((tmx - 0.1, tmy - 0.1, z + 1.55), (tmx + 0.1, tmy + 0.1, z + look), "tyre", skip=("-z", "+z"))
    frustum(kit, tmx, tmy, z + 1.1, 0.55, z + 1.6, 0.25, "sunny", sides=6, top="sunny")
    frustum(kit, tmx, tmy, z + 0.4, 0.95, z + 1.1, 0.55, "sunny", sides=6, bottom="tyre")
    add(kit, "detail", "tin", s, supports=(posts,), collider="hull")

    eave = tower_w / 2 + 0.35
    cap_z = z + look
    kit = Kit()
    kit.box((tmx - eave, tmy - eave, cap_z), (tmx + eave, tmy + eave, cap_z + 0.3), DOOR_RED, sides={"-z": "interiorCream"})
    if tower_top == "pyramid":
        frustum(kit, tmx, tmy, cap_z + 0.3, eave * math.sqrt(2), cap_z + 2.6, 0.0, DOOR_RED, sides=4)
        tip = cap_z + 2.6
    elif tower_top == "dome":
        r = (eave - 0.15) / math.cos(math.pi / 8)
        frustum(kit, tmx, tmy, cap_z + 0.3, r, cap_z + 1.1, r * 0.75, DOOR_RED)
        frustum(kit, tmx, tmy, cap_z + 1.1, r * 0.75, cap_z + 1.7, 0.0, DOOR_RED)
        tip = cap_z + 1.7
    else:
        kit.box((tmx - eave + 0.4, tmy - eave + 0.4, cap_z + 0.3), (tmx + eave - 0.4, tmy + eave - 0.4, cap_z + 0.7), "sunny", skip=("-z",))
        tip = cap_z + 0.7
    # A plain finial: a post and a ball.
    kit.box((tmx - 0.1, tmy - 0.1, tip - 0.1), (tmx + 0.1, tmy + 0.1, tip + 0.8), "tyre", skip=("-z",))
    frustum(kit, tmx, tmy, tip + 0.7, 0.0, tip + 1.0, 0.3, "sunny", sides=4)
    frustum(kit, tmx, tmy, tip + 1.0, 0.3, tip + 1.3, 0.0, "sunny", sides=4)
    add(kit, "roof", "tin", s + 1, supports=(posts,), collider="hull")

    return building.finish(
        look=(
            f"tower-{'left' if tower_side < 0 else 'right'}-{tower_at}/{tower_stages}st/{tower_top}/hall{hall_w:g}x{depth:g}"
            f"/doors-{door_style}/{upper_windows}/{badge}/parapet-{parapet}/height{tip + 1.3:.1f}"
        )
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(22, 26))


if __name__ == "__main__":
    previews()
