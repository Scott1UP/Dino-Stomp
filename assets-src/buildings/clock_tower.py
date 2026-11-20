"""Clock tower generator.

A square stone shaft about 20 m tall: a ground stage with a door, one or two
plain stages, a clock stage with an octagonal clock face (two hands, never
numbers), an open belfry with a bell in it, and a pointed spire. Every corner
is a pier with quoin blocks. The seed varies the shaft (straight, stepping in,
or with a wider head), its width and number of stages, the spire (pyramid,
octagonal, pyramid with corner pinnacles, or a cupola), the belfry openings,
the clock's rim and the time it shows, the little windows up
the shaft, and the plinth.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/clock_tower.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import clock_face, frustum, round_window, wall_y  # noqa: E402

TYPE = "clock_tower"
HITS_TO_COLLAPSE = 3  # tall building
TRIANGLE_BUDGET = 1800

WALL = 0.5
PIER = 0.85  # the square corner piers
BAND = 0.3  # the ledges between stages
SIDES = ("front", "back", "left", "right")
CORNERS = ((-1, -1), (1, -1), (-1, 1), (1, 1))


def build(building_id, seed, scheme=None, collection=None):
    """Build one clock tower. Returns (empty, stats)."""
    rng = random.Random(seed)

    # --- the tower's character ---
    shaft = rng.choice([4.6, 5.0, 5.4])
    mids = rng.choice([1, 2, 2])
    shape = rng.choice(["straight", "stepped", "headed"])
    belfry_style = rng.choice(["single", "double", "single"])
    rim_pick = rng.choice(["accent", "roof", "tyre"])
    plinth = rng.choice([0.0, 0.3])
    shaft_windows = rng.choice(["slit", "round"])
    quoin_pick = rng.choice(["trim", "trim", "roof"])
    hour = rng.randrange(12)
    minute = rng.choice([0, 10, 15, 20, 30, 40, 45, 50])
    spire_stretch = rng.choice([0.0, 0.6, 1.2])
    spire = rng.choice(["cupola", "octagon", "pinnacles", "pyramid"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    accent = pal["door"] if pal["door"] != "doorBrown" else pal["roof"]
    quoin = pal[quoin_pick]
    rim = {"accent": accent, "roof": pal["roof"], "tyre": "tyre"}[rim_pick]

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

    half = shaft / 2
    head = {"straight": 0.0, "stepped": -0.3, "headed": 0.35}[shape]
    belfry_step = {"straight": 0.0, "stepped": -0.55, "headed": 0.35}[shape]

    # Stages from the ground up: (kind, half-width, height, has a ledge on top).
    stages = [("ground", half + plinth, 3.4, True)]
    for m in range(mids):
        stages.append(("mid", half, 3.0 if mids == 2 else 3.4, m == mids - 1))
    stages.append(("clock", half + head, 3.7, True))
    belfry_half = half + belfry_step
    belfry_height = 3.4

    wall_ids = {}  # side -> module of the stage below
    corner_ids = {}

    def quoin_pier(sx, sy, hw, z0, z1, blocks=True):
        """A corner pier, with quoin blocks standing proud of it on alternate courses."""
        kit = Kit()
        xa, xb = sorted((sx * hw, sx * (hw - PIER)))
        ya, yb = sorted((sy * hw, sy * (hw - PIER)))
        kit.box((xa, ya, z0), (xb, yb, z1), pal["wall"] if blocks else quoin)
        if blocks:
            course = (z1 - z0) / 4
            for k in (0, 2):
                kit.box(
                    (xa - 0.12, ya - 0.12, z0 + k * course + 0.04),
                    (xb + 0.12, yb + 0.12, z0 + (k + 1) * course - 0.04),
                    quoin,
                )
        return kit

    z = 0.0
    for s, (kind, hw, height, ledge) in enumerate(stages):
        z0 = z
        z1 = z + height - (BAND if ledge else 0)
        inner = hw - PIER  # the walls run between the corner piers

        # Storey-0 structure all uses role "wall", piers included, so the game's
        # 40% rule counts every piece that holds the tower up.
        for sx, sy in CORNERS:
            kit = quoin_pier(sx, sy, hw, z0, z1)
            corner_ids[(sx, sy)] = add(
                kit,
                "wall" if s == 0 else "corner",
                "stone",
                s,
                supports=(corner_ids[(sx, sy)],) if s else (),
            )

        for side in SIDES:
            kit = Kit()
            openings = []
            mid_z = (z0 + z1) / 2
            if kind == "ground" and side == "front":
                openings = [{"x0": -0.8, "x1": 0.8, "z0": 0.0, "z1": 2.5, "kind": "door"}]
            elif kind == "ground" and side == "back":
                openings = [{"x0": -0.4, "x1": 0.4, "z0": 1.0, "z1": 2.5, "kind": "window"}]
            elif kind == "mid" and shaft_windows == "slit" and side in ("front", "back", "left"):
                openings = [{"x0": -0.4, "x1": 0.4, "z0": z0 + 0.7, "z1": z1 - 0.6, "kind": "window"}]

            if side in ("front", "back"):
                sign = -1 if side == "front" else 1
                kit.wall(-inner, inner, z0, z1, sign * hw, WALL, -sign, openings, colours)
                normal = (0, sign, 0)
                centre = (0, sign * hw, mid_z)
            else:
                sign = -1 if side == "left" else 1
                if openings:
                    wall_y(kit, -inner, inner, z0, z1, sign * hw, WALL, -sign, openings, colours)
                else:
                    xa, xb = sorted((sign * hw, sign * (hw - WALL)))
                    kit.box((xa, -inner, z0), (xb, inner, z1), pal["wall"], sides={"+x" if sign < 0 else "-x": "interiorCream"})
                normal = (sign, 0, 0)
                centre = (sign * hw, 0, mid_z)

            if kind == "ground" and side == "front":
                # A doorstep and a little hood over the door.
                kit.box((-1.1, -hw - 0.6, 0), (1.1, -hw, 0.2), "stone", skip=("-z", "+y"))
                kit.extrude_y([(-1.15, 2.7), (1.15, 2.7), (0, 3.25)], -hw - 0.35, -hw, quoin)
            elif kind == "mid" and shaft_windows == "round":
                round_window(kit, centre, normal, 0.6, pal["trim"])
            elif kind == "clock":  # a face on every side, so the clock shows from wherever the camera is
                radius = min(inner + 0.25, (z1 - z0) / 2 - 0.2)
                clock_face(kit, centre, normal, radius, rim, hour, minute)

            wall_ids[side] = add(kit, "wall", "stone", s, supports=(wall_ids[side],) if s else ())

        # The top of the stage: a ledge that shows outside, or just a floor inside.
        z = z0 + height
        holders = list(wall_ids.values()) + list(corner_ids.values())
        kit = Kit()
        if ledge:
            next_hw = stages[s + 1][1] if s + 1 < len(stages) else belfry_half
            reach = max(hw, next_hw) + 0.22
            kit.box((-reach, -reach, z1), (reach, reach, z), pal["trim"], sides={"+z": "interiorCream", "-z": "interiorCream"})
            add(kit, "band", "stone", s + 1, supports=holders)
        else:
            kit.box((-inner, -inner, z - 0.2), (inner, inner, z), "interiorCream")
            add(kit, "floor", "wood", s + 1, supports=holders)

    # --- belfry: four piers, with a lintel over each opening ---
    s = len(stages)
    hw = belfry_half
    inner = hw - PIER
    z0 = z
    z1 = z + belfry_height
    lintel_z = z1 - 0.5
    piers = {}
    for sx, sy in CORNERS:
        kit = quoin_pier(sx, sy, hw, z0, lintel_z, blocks=False)
        piers[(sx, sy)] = add(kit, "corner", "stone", s, supports=(corner_ids[(sx, sy)],))

    lintels = {}
    for side in SIDES:
        sign = -1 if side in ("front", "left") else 1
        ya, yb = sorted((sign * hw, sign * (hw - PIER)))
        kit = Kit()
        if side in ("front", "back"):
            kit.box((-hw, ya, lintel_z), (hw, yb, z1), pal["wall"])
            for end in (-1, 1):  # the haunches that round the top of the opening
                xe = end * inner
                kit.extrude_y([(xe, lintel_z), (xe - end * 0.75, lintel_z), (xe, lintel_z - 0.75)], ya, yb, pal["wall"])
            if belfry_style == "double":
                kit.box((-0.22, ya + 0.15, z0), (0.22, yb - 0.15, lintel_z), quoin, skip=("-z", "+z"))
            holders = (piers[(-1, sign)], piers[(1, sign)])
        else:
            kit.box((ya, -inner, lintel_z), (yb, inner, z1), pal["wall"])
            for end in (-1, 1):
                ye = end * inner
                kit.extrude_x([(ye, lintel_z), (ye - end * 0.75, lintel_z), (ye, lintel_z - 0.75)], ya, yb, pal["wall"])
            if belfry_style == "double":
                kit.box((ya + 0.15, -0.22, z0), (yb - 0.15, 0.22, lintel_z), quoin, skip=("-z", "+z"))
            holders = (piers[(sign, -1)], piers[(sign, 1)])
        lintels[side] = add(kit, "wall", "stone", s, supports=holders, collider="hull")

    # --- the bell, hanging from a beam across the belfry ---
    kit = Kit()
    kit.box((-inner, -0.14, lintel_z - 0.3), (inner, 0.14, lintel_z), "wood")
    bell_top = z0 + 1.95  # hung low, so it shows through the openings from the high camera
    kit.box((-0.1, -0.1, bell_top), (0.1, 0.1, lintel_z - 0.3), "wood", skip=("-z", "+z"))
    frustum(kit, 0, 0, bell_top - 0.6, 0.72, bell_top, 0.35, "sunny", sides=6, top="sunny")
    frustum(kit, 0, 0, bell_top - 1.6, min(1.2, inner - 0.2), bell_top - 0.6, 0.72, "sunny", sides=6, bottom="tyre")
    add(kit, "detail", "tin", s, supports=(lintels["left"], lintels["right"]), collider="hull")

    # --- spire ---
    total = z1
    spire_height = max(4.4, min(7.2, 20.0 - total + spire_stretch))
    eave = hw + 0.4
    base_z = z1 + 0.3
    body = hw + 0.1
    kit = Kit()
    kit.box((-eave, -eave, z1), (eave, eave, base_z), pal["trim"], sides={"-z": "interiorCream"})

    def finial(kit, at):
        frustum(kit, 0, 0, at - 0.05, 0.0, at + 0.3, 0.3, "sunny", sides=4)
        frustum(kit, 0, 0, at + 0.3, 0.3, at + 0.85, 0.0, "sunny", sides=4)

    if spire == "cupola":
        # An eight-sided dome in two steps, a little lantern, and a point.
        r = body / math.cos(math.pi / 8)
        h1 = spire_height * 0.24
        h2 = spire_height * 0.42
        frustum(kit, 0, 0, base_z, r, base_z + h1, r * 0.82, pal["roof"])
        frustum(kit, 0, 0, base_z + h1, r * 0.82, base_z + h2, r * 0.42, pal["roof"], top=pal["roof"])
        lower = add(kit, "roof", "stone", s + 1, supports=list(lintels.values()), collider="hull")
        lantern = base_z + h2
        lantern_top = lantern + spire_height * 0.2
        kit = Kit()
        frustum(kit, 0, 0, lantern, r * 0.28, lantern_top, r * 0.28, pal["trim"], bottom=pal["trim"])
        frustum(kit, 0, 0, lantern_top, r * 0.42, base_z + spire_height, 0.0, pal["roof"], bottom=pal["roof"])
        finial(kit, base_z + spire_height)
        add(kit, "roof", "stone", s + 2, supports=(lower,), collider="hull")
    else:
        if spire == "octagon":
            sides, r = 8, body / math.cos(math.pi / 8)
        elif spire == "pinnacles":
            sides, r = 4, (body - 0.55) * math.sqrt(2)
        else:
            sides, r = 4, body * math.sqrt(2)
        cut = 0.45  # the spire breaks into a lower part and a tip
        split_z = base_z + spire_height * cut
        frustum(kit, 0, 0, base_z, r, split_z, r * (1 - cut), pal["roof"], sides=sides, top=pal["roof"])
        lower = add(kit, "roof", "stone", s + 1, supports=list(lintels.values()), collider="hull")
        kit = Kit()
        frustum(kit, 0, 0, split_z, r * (1 - cut), base_z + spire_height, 0.0, pal["roof"], sides=sides, bottom=pal["roof"])
        finial(kit, base_z + spire_height)
        add(kit, "roof", "stone", s + 2, supports=(lower,), collider="hull")

        if spire == "pinnacles":
            for sy in (-1, 1):
                kit = Kit()
                for sx in (-1, 1):
                    px, py = sx * (eave - 0.5), sy * (eave - 0.5)
                    kit.box((px - 0.4, py - 0.4, base_z), (px + 0.4, py + 0.4, base_z + 0.9), pal["trim"], skip=("-z", "+z"))
                    frustum(kit, px, py, base_z + 0.9, 0.5 * math.sqrt(2), base_z + 2.5, 0.0, pal["roof"], sides=4, bottom=pal["roof"])
                add(kit, "detail", "stone", s + 1, supports=(lower,), collider="hull")

    empty, stats = building.finish(
        look=(
            f"{shape}/{shaft:g}m/mids{mids}/{spire}/belfry-{belfry_style}/rim-{rim_pick}/{shaft_windows}"
            f"/plinth{plinth:g}/quoin-{quoin_pick}/{hour}:{minute:02d}/height{base_z + spire_height:.1f}"
        )
    )
    return empty, stats


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(22, 34))


if __name__ == "__main__":
    previews()
