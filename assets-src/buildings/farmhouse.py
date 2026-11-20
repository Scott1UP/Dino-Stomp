"""Farmhouse generator.

A homely two-storey farmhouse about 11 m wide and 8 m deep (6 m of house and
a 2.2 m veranda right across the front), under a pitched roof with a chimney.
Shuttered windows on the front, plain ones on the back and ends.

The seed varies the width, the veranda (a lean-to roof, one with a little
pediment over the steps, or a flat one with a balcony rail), which bay the
front door is in, the roof pitch and the chimney (a stack up an end wall or a
fat one on the ridge). Colours come from the scheme.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/farmhouse.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_farm as farm  # noqa: E402
from lib import shapes_town2 as town  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import round_window  # noqa: E402

TYPE = "farmhouse"
HITS_TO_COLLAPSE = 2  # medium building
TRIANGLE_BUDGET = 900

WALL = town.WALL
STOREY = 3.0
HOUSE_DEPTH = 6.0
VERANDA_DEPTH = 2.2
VERANDAS = ("lean", "pediment", "balcony")


def build(building_id, seed, scheme=None, collection=None):
    """Build one farmhouse. Returns (empty, stats)."""
    rng = random.Random(seed)

    # --- the farmhouse's character ---
    veranda = VERANDAS[seed % len(VERANDAS)]  # cycled, so neighbouring seeds always differ
    width = rng.choice([10.5, 11.0, 11.5])
    door_bay = rng.choice([1, 1, 0, 2])
    pitch = rng.choice([0.75, 0.9, 1.05])  # rise per metre
    chimney = rng.choice(["end", "ridge"])
    chimney_side = rng.choice([-1, 1])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]
    colours = town.wall_colours(pal)
    shutter = pal["roof"]

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    depth = HOUSE_DEPTH + VERANDA_DEPTH
    x0, x1 = -width / 2, width / 2
    y0, y1 = -depth / 2 + VERANDA_DEPTH, depth / 2  # the house; the veranda is in front of y0
    y_mid = (y0 + y1) / 2
    bounds = (x0, x1, y0, y1)
    front_face = farm.face("front", y0)
    front_bays = town.split(x0, x1, width / 3)
    back_bays = town.split(x0, x1, width / 2)
    side_bays = [(y0 + WALL, y1 - WALL)]
    bays = {"front": front_bays, "back": back_bays, "left": side_bays, "right": side_bays}

    def is_door(s, side, i):
        return s == 0 and side == "front" and i == door_bay

    def storey(s, below):
        z = s * STOREY

        def openings(side, i, a, b):
            mid = (a + b) / 2
            if is_door(s, side, i):
                return [town.door(mid, 0, 1.4, 2.4)]
            if side == "front":
                return [town.window(mid, z, 1.5, 1.5)]
            if side == "back":
                return [town.window(mid, z, 2.0, 1.4)]
            return [town.window(mid, z, 1.4, 1.5)]

        def extra(kit, side, i, a, b):
            if side == "front" and not is_door(s, side, i):
                mid = (a + b) / 2
                farm.shutters(kit, front_face, mid - 0.75, mid + 0.75, z + 0.9, z + 2.4, shutter)

        return town.shell_storey(add, bounds, z, z + STOREY, s, colours, below=below, openings=openings, extra=extra, bays=bays)

    ground = storey(0, None)
    upper = storey(1, ground)
    town.floor_slab(add, bounds, STOREY, 1, town.flatten(ground))

    # --- the roof and its gables ---
    eaves = 2 * STOREY
    rise = pitch * HOUSE_DEPTH / 2
    ridge = eaves + rise

    def gable_extra(kit, sign):
        if chimney == "end" and sign == chimney_side:
            return
        round_window(kit, (sign * width / 2, y_mid, eaves + rise * 0.38), (sign, 0, 0), min(0.7, rise * 0.26), pal["trim"])

    roof = town.roof_gabled(
        add,
        bounds,
        eaves,
        rise,
        pal["roof"],
        2,
        list(zip(front_bays, upper["front"])),
        list(zip(back_bays, upper["back"])),
        {-1: upper["left"], 1: upper["right"]},
        pal["wall"],
        gable_extra=gable_extra,
    )

    # --- the veranda: a deck, posts, rails and a roof right across the front ---
    yf = y0 - VERANDA_DEPTH
    door_mid = sum(front_bays[door_bay]) / 2
    kit = Kit()
    kit.box((x0 - 0.2, yf, 0), (x1 + 0.2, y0, 0.3), "wood", skip=("-z",))
    kit.box((door_mid - 1.2, yf - 0.6, 0), (door_mid + 1.2, yf, 0.15), "stone", skip=("-z", "+y"))
    deck = add(kit, "floor", "wood", 0)

    post_top = 3.0 if veranda == "balcony" else 2.75
    post_xs = [x0 + 0.05] + [b for _, b in front_bays[:-1]] + [x1 - 0.05]
    posts = []
    for x in post_xs:
        kit = Kit()
        kit.box((x - 0.15, yf + 0.12, 0.3), (x + 0.15, yf + 0.42, post_top), pal["trim"], skip=("-z", "+z"))
        posts.append(add(kit, "detail", "wood", 0, supports=(deck,)))

    for i in range(len(front_bays)):
        if i == door_bay:
            continue
        xa, xb = post_xs[i] + 0.15, post_xs[i + 1] - 0.15
        kit = Kit()
        kit.box((xa, yf + 0.2, 1.0), (xb, yf + 0.34, 1.18), pal["trim"], skip=("-x", "+x"))
        kit.box((xa, yf + 0.22, 0.5), (xb, yf + 0.32, 0.64), pal["trim"], skip=("-x", "+x"))
        add(kit, "detail", "wood", 0, supports=(posts[i], posts[i + 1]))

    halves = [(x0 - 0.35, 0.0, posts[:2] + ground["front"][:2]), (0.0, x1 + 0.35, posts[2:] + ground["front"][1:])]
    canopy = []
    if veranda == "balcony":
        for xa, xb, holders in halves:
            kit = Kit()
            kit.box((xa, yf - 0.3, post_top), (xb, y0, post_top + 0.25), pal["roof"], sides={"-y": "trimWhite"})
            canopy.append(add(kit, "roof", "tile", 1, supports=holders))
        # A white rail round the balcony.
        zr = post_top + 0.25
        kit = Kit()
        kit.box((x0 - 0.3, yf - 0.25, zr + 0.75), (x1 + 0.3, yf - 0.1, zr + 0.95), pal["trim"])
        for x in (x0 - 0.2, x0 + width / 3, x1 - width / 3, x1 + 0.2):
            kit.box((x - 0.1, yf - 0.27, zr), (x + 0.1, yf - 0.08, zr + 0.75), pal["trim"], skip=("-z", "+z"))
        for sign in (-1, 1):
            xa, xb = sorted((sign * (width / 2 + 0.3), sign * (width / 2 + 0.15)))
            kit.box((xa, yf - 0.1, zr + 0.75), (xb, y0, zr + 0.95), pal["trim"], skip=("-y",))
        add(kit, "detail", "wood", 1, supports=canopy)
    else:
        z_wall, z_front = 3.35, 2.75
        slope = (z_wall - z_front) / VERANDA_DEPTH
        ye = yf - 0.35
        ze = z_front - 0.35 * slope
        for xa, xb, holders in halves:
            kit = Kit()
            farm.slab(kit, [(xa, ye, ze), (xb, ye, ze), (xb, y0, z_wall), (xa, y0, z_wall)], 0.2, pal["roof"], {2: "trimWhite"})
            canopy.append(add(kit, "roof", "tile", 1, supports=holders, collider="hull"))
        if veranda == "pediment":
            kit = Kit()
            kit.extrude_y(
                [(door_mid - 1.7, z_front - 0.05), (door_mid + 1.7, z_front - 0.05), (door_mid, z_front + 1.25)],
                ye - 0.1,
                ye + 1.5,
                pal["roof"],
                colours={0: pal["trim"]},
            )
            farm.fpoly(kit, farm.face("front", ye - 0.1), farm_disc(door_mid, z_front + 0.4, 0.3), 0.03, shutter)
            add(kit, "detail", "wood", 1, supports=canopy, collider="hull")

    # --- the chimney ---
    kit = Kit()
    if chimney == "end":
        sign = chimney_side
        xa, xb = sorted((sign * (width / 2), sign * (width / 2 + 0.65)))
        shoulder = eaves * 0.8
        top_z = ridge + 1.3
        kit.extrude_x(
            [(y_mid - 1.0, 0), (y_mid + 1.0, 0), (y_mid + 1.0, shoulder), (y_mid + 0.55, shoulder + 0.7), (y_mid - 0.55, shoulder + 0.7)],
            xa,
            xb,
            "stone",
        )
        kit.box((xa, y_mid - 0.55, shoulder + 0.7), (xb, y_mid + 0.55, top_z), "stone", skip=("-z", "+z"))
        kit.box((xa - 0.1, y_mid - 0.65, top_z), (xb + 0.1, y_mid + 0.65, top_z + 0.24), pal["trim"])
        add(kit, "detail", "stone", 0, collider="hull")
    else:
        cx = chimney_side * width * 0.24
        kit.box((cx - 0.7, y_mid - 0.55, ridge - 0.7), (cx + 0.7, y_mid + 0.55, ridge + 1.5), "stone", skip=("-z", "+z"))
        kit.box((cx - 0.82, y_mid - 0.67, ridge + 1.5), (cx + 0.82, y_mid + 0.67, ridge + 1.74), pal["trim"])
        kit.box((cx - 0.22, y_mid - 0.22, ridge + 1.74), (cx + 0.22, y_mid + 0.22, ridge + 2.2), "tangerine", skip=("-z",))
        add(kit, "detail", "stone", 3, supports=roof["front"] + roof["back"])

    return building.finish(look=f"w={width} veranda-{veranda} door-bay{door_bay} pitch{pitch} chimney-{chimney}")


def farm_disc(u, z, radius, sides=6):
    """(u, z) points of a little polygon, for a painted roundel."""
    return [(u + radius * math.cos(i * 2 * math.pi / sides), z + radius * math.sin(i * 2 * math.pi / sides)) for i in range(sides)]


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(17, 15))


if __name__ == "__main__":
    previews()
