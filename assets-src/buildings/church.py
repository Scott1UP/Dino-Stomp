"""Toy church generator.

A long nave under a steep pitched roof, with tall arched windows between
buttresses, and a square tower carrying a pointed steeple about 18 m to its
tip. The arched door is in the tower. The seed varies where the tower stands
(in front of the nave, or beside it at either front corner), the length and
height of the nave, the roof pitch, the window heads (pointed or round), the
buttresses, and the steeple (pyramid, octagon, pinnacles or a needle on a
skirt).

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/church.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import frustum, round_window  # noqa: E402
from lib.shapes_town2 import arched_panel  # noqa: E402

TYPE = "church"
HITS_TO_COLLAPSE = 3  # tall building
TRIANGLE_BUDGET = 1800

WALL = 0.45
OVERHANG = 0.5
VERGE = 0.4
ROOF_THICKNESS = 0.32
BAND = 0.3


def build(building_id, seed, scheme=None, collection=None):
    """Build one church. Returns (empty, stats)."""
    rng = random.Random(seed)

    # --- the church's character ---
    tower_pos = ("centre", "left", "centre", "right")[seed % 4]  # cycled, so neighbouring seeds always differ
    nave_w = rng.choice([7.5, 8.0, 8.5])
    bays, bay_len = rng.choice([(3, 4.2), (4, 3.3), (4, 3.5)])
    wall_h = rng.choice([5.0, 5.5, 6.0])
    rise = rng.choice([4.2, 4.8, 5.4])
    tower_w = rng.choice([4.4, 4.8, 5.2])
    steeple = rng.choice(["pyramid", "octagon", "pinnacles", "needle"])
    head = rng.choice(["pointed", "pointed", "round"])
    buttress_pick = rng.choice(["trim", "wall", "none"])
    tip = rng.choice([17.0, 17.5, 18.5])  # the finial adds another metre
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]
    wall_colour, trim, roof = pal["wall"], pal["trim"], pal["roof"]
    # The steeple is never the roof's colour: seen from above it would vanish against the nave roof.
    spire = next(c for c in (pal["door"], "sunny", "tomato", "cobalt") if c not in (roof, wall_colour, "doorBrown"))

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    nave_len = bays * bay_len
    if tower_pos == "centre":
        total_d = tower_w + nave_len
        ty0 = -total_d / 2
        ny0, ny1 = ty0 + tower_w, total_d / 2
        nx0, nx1 = -nave_w / 2, nave_w / 2
        tx0 = -tower_w / 2
    else:
        sign = -1 if tower_pos == "left" else 1
        total_w = nave_w + tower_w
        ny0, ny1 = -nave_len / 2, nave_len / 2
        ty0 = ny0
        if sign < 0:
            tx0 = -total_w / 2
            nx0, nx1 = tx0 + tower_w, total_w / 2
        else:
            nx0, nx1 = -total_w / 2, total_w / 2 - tower_w
            tx0 = nx1
    tx1, ty1 = tx0 + tower_w, ty0 + tower_w
    tmx, tmy = (tx0 + tx1) / 2, (ty0 + ty1) / 2
    nmx = (nx0 + nx1) / 2
    ridge = wall_h + rise
    slope = rise / (nave_w / 2)
    eave_z = wall_h - slope * OVERHANG

    def lancet(kit, centre, normal, width=1.3, height=None, style=None):
        arched_panel(kit, centre, normal, width, height or wall_h - 2.3, style or head, trim, "windowBlue", "windowShine")

    # --- nave side walls: a tall window and a buttress to each bay, and the roof above ---
    for sign in (-1, 1):
        x_out = nx0 if sign < 0 else nx1
        xa, xb = sorted((x_out, x_out - sign * WALL))
        inner = "+x" if sign < 0 else "-x"
        for i in range(bays):
            ya = ny0 + WALL + i * (nave_len - 2 * WALL) / bays
            yb = ny0 + WALL + (i + 1) * (nave_len - 2 * WALL) / bays
            ym = (ya + yb) / 2
            # The tower hides the bays it stands against.
            hidden = tower_pos != "centre" and (tx0 < x_out + sign * 0.1 < tx1) and ym < ty1 + 0.8
            kit = Kit()
            kit.box((xa, ya, 0), (xb, yb, wall_h), wall_colour, sides={inner: "interiorCream"})
            if not hidden:
                lancet(kit, (x_out, ym, 1.2), (sign, 0, 0))
                if buttress_pick != "none":
                    reach = x_out + sign * 0.75
                    kit.extrude_y(
                        [(x_out, 0), (reach, 0), (reach, wall_h * 0.55), (x_out, wall_h * 0.88)],
                        yb - 0.65,
                        yb - 0.05,
                        pal[buttress_pick],
                    )
            wall_id = add(kit, "wall", "stone", 0, collider="box")

            eave_x = x_out + sign * OVERHANG
            ra = ya - (WALL + VERGE if i == 0 else 0)
            rb = yb + (WALL + VERGE if i == bays - 1 else 0)
            kit = Kit()
            kit.slab(
                [(eave_x, ra, eave_z), (eave_x, rb, eave_z), (nmx, rb, ridge), (nmx, ra, ridge)],
                ROOF_THICKNESS,
                roof,
            )
            add(kit, "roof", "tile", 1, supports=(wall_id,), collider="hull")

    # --- nave end walls, in two halves, with a gable over each end ---
    for sign, y_out in ((-1, ny0), (1, ny1)):
        ya, yb = sorted((y_out, y_out - sign * WALL))
        inner = "+y" if sign < 0 else "-y"
        covered = sign < 0 and tower_pos == "centre"
        halves = []
        for xa, xb in ((nx0, nmx), (nmx, nx1)):
            kit = Kit()
            kit.box((xa, ya, 0), (xb, yb, wall_h), wall_colour, sides={inner: "interiorCream"})
            if not covered:
                lancet(kit, ((xa + xb) / 2, y_out, 1.2), (0, sign, 0), width=1.5, height=wall_h - 1.8)
            halves.append(add(kit, "wall", "stone", 0))
        kit = Kit()
        kit.extrude_y([(nx0, wall_h), (nx1, wall_h), (nmx, ridge)], ya, yb, wall_colour)
        if not covered:
            round_window(kit, (nmx, y_out, wall_h + rise * 0.3), (0, sign, 0), min(1.1, rise * 0.24), trim)
        add(kit, "wall", "stone", 1, supports=halves, collider="hull")

    # --- tower: three stages, each four walls and a ledge ---
    stages = [("ground", 4.3), ("mid", 3.3), ("belfry", 3.5)]
    below = {}
    z = 0.0
    for s, (kind, height) in enumerate(stages):
        z0, z1 = z, z + height - BAND
        mid_z = (z0 + z1) / 2
        ids = {}
        for side, normal in (("front", (0, -1, 0)), ("back", (0, 1, 0)), ("left", (-1, 0, 0)), ("right", (1, 0, 0))):
            kit = Kit()
            if side in ("front", "back"):
                y_out = ty0 if side == "front" else ty1
                ya, yb = sorted((y_out, y_out - normal[1] * WALL))
                kit.box((tx0, ya, z0), (tx1, yb, z1), wall_colour, sides={"+y" if side == "front" else "-y": "interiorCream"})
                face = (tmx, y_out)
            else:
                x_out = tx0 if side == "left" else tx1
                xa, xb = sorted((x_out, x_out - normal[0] * WALL))
                kit.box((xa, ty0 + WALL, z0), (xb, ty1 - WALL, z1), wall_colour, sides={"+x" if side == "left" else "-x": "interiorCream"})
                face = (x_out, tmy)
            if kind == "ground" and side == "front":
                arched_panel(kit, (tmx, ty0, 0), normal, 2.0, 3.2, head, trim, pal["door"], frame=0.22, depth=0.16, is_door=True)
                kit.box((tmx - 1.4, ty0 - 0.7, 0), (tmx + 1.4, ty0, 0.22), "stone", skip=("-z", "+y"))
            elif kind == "ground" and side != "back":
                lancet(kit, (face[0], face[1], 1.3), normal, width=1.0, height=2.2)
            elif kind == "mid":
                round_window(kit, (face[0], face[1], mid_z), normal, 0.85, trim)
            elif kind == "belfry":
                for dx in (-0.85, 0.85):
                    at = (face[0] + dx, face[1], z0 + 0.5) if side in ("front", "back") else (face[0], face[1] + dx, z0 + 0.5)
                    arched_panel(kit, at, normal, 1.0, z1 - z0 - 1.0, head, trim, "windowBlue", "windowShine", depth=0.0)
            ids[side] = add(kit, "wall", "stone", s, supports=(below[side],) if below else ())
        z += height
        kit = Kit()
        kit.box(
            (tx0 - 0.22, ty0 - 0.22, z1),
            (tx1 + 0.22, ty1 + 0.22, z),
            trim,
            sides={"+z": "interiorCream", "-z": "interiorCream"},
        )
        add(kit, "band", "stone", s + 1, supports=list(ids.values()))
        below = ids

    # --- steeple ---
    s = len(stages)
    holders = list(below.values())
    half = tower_w / 2
    base_z = z
    height = tip - base_z

    def finial(kit, at):
        gold = "sunny" if spire != "sunny" else "trimWhite"
        frustum(kit, tmx, tmy, at - 0.05, 0.0, at + 0.35, 0.34, gold, sides=4)
        frustum(kit, tmx, tmy, at + 0.35, 0.34, at + 1.0, 0.0, gold, sides=4)

    if steeple == "needle":
        # A low skirt roof, then a thin eight-sided needle.
        r = (half + 0.3) * math.sqrt(2)
        skirt = 1.6
        kit = Kit()
        frustum(kit, tmx, tmy, base_z, r, base_z + skirt, r * 0.5, roof, sides=4, top=roof, bottom=roof)
        lower = add(kit, "roof", "tile", s, supports=holders, collider="hull")
        kit = Kit()
        frustum(kit, tmx, tmy, base_z + skirt, r * 0.5, base_z + height, 0.0, spire, sides=8, bottom=spire)
        finial(kit, base_z + height)
        add(kit, "roof", "tile", s + 1, supports=(lower,), collider="hull")
    else:
        if steeple == "octagon":
            sides, r = 8, (half + 0.25) / math.cos(math.pi / 8)
        elif steeple == "pinnacles":
            sides, r = 4, (half - 0.5) * math.sqrt(2)
        else:
            sides, r = 4, (half + 0.3) * math.sqrt(2)
        cut = 0.42  # the spire breaks into a lower part and a tip
        split_z = base_z + height * cut
        kit = Kit()
        frustum(kit, tmx, tmy, base_z, r, split_z, r * (1 - cut), spire, sides=sides, top=spire, bottom=spire)
        lower = add(kit, "roof", "tile", s, supports=holders, collider="hull")
        kit = Kit()
        frustum(kit, tmx, tmy, split_z, r * (1 - cut), base_z + height, 0.0, spire, sides=sides, bottom=spire)
        finial(kit, base_z + height)
        add(kit, "roof", "tile", s + 1, supports=(lower,), collider="hull")
        if steeple == "pinnacles":
            for sy in (-1, 1):
                kit = Kit()
                for sx in (-1, 1):
                    px, py = tmx + sx * (half - 0.35), tmy + sy * (half - 0.35)
                    kit.box((px - 0.45, py - 0.45, base_z), (px + 0.45, py + 0.45, base_z + 1.0), trim, skip=("-z", "+z"))
                    frustum(kit, px, py, base_z + 1.0, 0.55 * math.sqrt(2), base_z + 2.8, 0.0, spire, sides=4, bottom=spire)
                add(kit, "detail", "stone", s, supports=holders, collider="hull")

    return building.finish(
        look=f"tower-{tower_pos}/{tower_w:g}m/{steeple}/tip{tip:g}/nave{nave_w:g}x{nave_len:g}/wall{wall_h:g}/rise{rise:g}/{head}/buttress-{buttress_pick}"
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(26, 34))


if __name__ == "__main__":
    previews()
