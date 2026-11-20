"""Block of flats generator.

Four or five storeys of flats under a flat roof: a cornice and parapet round
the top, a water tank and a stair-head hut on the roof, balconies with
railings up the front, and a grand double front door under a portico. The
seed varies the plan (a rectangle, or an L with a front corner cut away), the
size and number of storeys, where the balconies go and how they are railed,
the window style, the portico, the tank, and whether the ground floor is
picked out in the roof colour.

The walls take most of the triangle budget, so the generator measures the
bare building first and then spends what is left on balconies and side
windows, a storey at a time from the top.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/block_of_flats.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import beam, flat, frustum, wall_y  # noqa: E402

TYPE = "block_of_flats"
HITS_TO_COLLAPSE = 3  # tall building
TRIANGLE_BUDGET = 1800

WALL = 0.35
GROUND = 3.4
CORNICE = 0.3  # how far the roof slab sails past the walls
DOOR_COLUMN = 1  # the middle of the three front bays


def _balcony(kit, xa, xb, y, z, style, colour, trim):
    """A balcony on a front bay: a slab, and a railing or a solid front."""
    bx0, bx1 = xa + 0.35, xb - 0.35
    out = y - 1.15
    kit.box((bx0, out, z - 0.2), (bx1, y, z), trim, skip=("+y",))
    if style == "panel":
        kit.box((bx0, out, z), (bx1, out + 0.12, z + 1.0), colour, sides={"+z": trim}, skip=("-z",))
        for xs in (bx0, bx1 - 0.12):
            kit.box((xs, out + 0.12, z), (xs + 0.12, y, z + 1.0), colour, sides={"+z": trim}, skip=("-z", "-y"))
    else:
        kit.box((bx0, out, z + 0.95), (bx1, out + 0.1, z + 1.07), colour)
        kit.box((bx0, out, z + 0.45), (bx1, out + 0.08, z + 0.53), colour, skip=("-x", "+x"))
        for xs in (bx0, bx1 - 0.1):
            kit.box((xs, out + 0.1, z + 0.95), (xs + 0.1, y, z + 1.07), colour, skip=("-y", "+y"))
            kit.box((xs, out, z), (xs + 0.1, out + 0.1, z + 0.95), colour, skip=("-z", "+z"))


def build(building_id, seed, scheme=None, collection=None):
    """Build one block. Returns (empty, stats)."""
    rng = random.Random(seed)

    # --- the block's character ---
    storeys = rng.choice([4, 4, 5])
    plan = rng.choice(["rect", "L", "rect", "L"])
    width = rng.choice([11.0, 12.0, 13.0])
    depth = rng.choice([8.0, 9.0, 9.5])
    upper = rng.choice([2.9, 3.0, 3.1])
    notch_side = rng.choice([-1, 1])
    notch_depth = rng.choice([3.0, 3.8])
    balcony_pattern = rng.choice(["outer", "centre", "all", "stagger"])
    balcony_style = rng.choice(["rail", "rail", "panel"])
    window_style = rng.choice(["square", "wide", "tall"])
    portico = rng.choice(["columns", "pediment", "canopy"])
    tank_style = rng.choice(["round", "round", "box"])
    tank_side = rng.choice([-1, 1])
    base_pick = rng.choice(["wall", "roof", "roof"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    if storeys == 5:  # the tall ones are slimmer, with two wide bays across the back
        width -= 2.0
        depth = min(depth, 8.5)
    back_bays = 3 if storeys == 4 else 2
    accent = pal["door"] if pal["door"] != "doorBrown" else pal["roof"]

    colours = {
        "wall": pal["wall"],
        "interior": "interiorCream",
        "trim": pal["trim"],
        "glass": "windowBlue",
        "shine": "windowShine",
        "door": pal["door"],
    }
    ground_colours = dict(colours, wall=pal[base_pick])

    x0, x1 = -width / 2, width / 2
    front, back = -depth / 2, depth / 2
    levels = [0.0] + [GROUND + i * upper for i in range(storeys)]
    top = levels[storeys]
    bay_width = width / 3

    # --- the outline, as runs of wall. X runs own the corners; Y runs fit between them. ---
    if plan == "rect":
        runs = [
            {"kind": "front", "axis": "x", "at": front, "a": x0, "b": x1, "inward": 1, "bays": 3, "columns": [0, 1, 2]},
            {"kind": "back", "axis": "x", "at": back, "a": x0, "b": x1, "inward": -1, "bays": back_bays},
            {"kind": "side", "axis": "y", "at": x0, "a": front + WALL, "b": back - WALL, "inward": 1, "bays": 2},
            {"kind": "side", "axis": "y", "at": x1, "a": front + WALL, "b": back - WALL, "inward": -1, "bays": 2},
        ]
        floors = [((x0 + WALL, front + WALL), (x1 - WALL, back - WALL))]
        roofs = [((x0 - CORNICE, front - CORNICE), (x1 + CORNICE, back + CORNICE))]
    else:
        # An L: one front corner is cut away, so one of the three front bays sits back.
        step = front + notch_depth
        if notch_side > 0:
            corner = x1 - bay_width
            main = {"a": x0, "b": corner, "columns": [0, 1]}
            set_back = {"a": corner, "b": x1, "columns": [2]}
            notch_inward = -1
            floor_b = ((x0 + WALL, front + WALL), (corner - WALL, step + WALL))
            roof_b = ((x0 - CORNICE, front - CORNICE), (corner + CORNICE, step - CORNICE))
        else:
            corner = x0 + bay_width
            main = {"a": corner, "b": x1, "columns": [1, 2]}
            set_back = {"a": x0, "b": corner, "columns": [0]}
            notch_inward = 1
            floor_b = ((corner + WALL, front + WALL), (x1 - WALL, step + WALL))
            roof_b = ((corner - CORNICE, front - CORNICE), (x1 + CORNICE, step - CORNICE))
        left_a = step + WALL if notch_side < 0 else front + WALL
        right_a = step + WALL if notch_side > 0 else front + WALL
        runs = [
            {"kind": "front", "axis": "x", "at": front, "inward": 1, "bays": 2, **main},
            {"kind": "front", "axis": "x", "at": step, "inward": 1, "bays": 1, **set_back},
            {"kind": "notch", "axis": "y", "at": corner, "a": front + WALL, "b": step, "inward": notch_inward, "bays": 1},
            {"kind": "back", "axis": "x", "at": back, "a": x0, "b": x1, "inward": -1, "bays": back_bays},
            {"kind": "side", "axis": "y", "at": x0, "a": left_a, "b": back - WALL, "inward": 1, "bays": 2 if notch_side > 0 else 1},
            {"kind": "side", "axis": "y", "at": x1, "a": right_a, "b": back - WALL, "inward": -1, "bays": 2 if notch_side < 0 else 1},
        ]
        floors = [((x0 + WALL, step + WALL), (x1 - WALL, back - WALL)), floor_b]
        roofs = [((x0 - CORNICE, step - CORNICE), (x1 + CORNICE, back + CORNICE)), roof_b]

    def window(mid, z0, span):
        if window_style == "wide":
            half = min(1.2, span / 2 - 0.6)
            return {"x0": mid - half, "x1": mid + half, "z0": z0 + 0.95, "z1": z0 + 2.35, "kind": "window"}
        if window_style == "tall":
            return {"x0": mid - 0.6, "x1": mid + 0.6, "z0": z0 + 0.6, "z1": z0 + 2.45, "kind": "window"}
        return {"x0": mid - 0.75, "x1": mid + 0.75, "z0": z0 + 0.9, "z1": z0 + 2.4, "kind": "window"}

    def construct(add, balconies, side_storeys):
        """Build everything through `add`. Called once to measure, then for real."""
        below = {}
        by_storey = []
        door_bay = None
        for s in range(storeys):
            z0, z1 = levels[s], levels[s + 1]
            look = ground_colours if s == 0 else colours
            ids = []
            for r, run in enumerate(runs):
                span = (run["b"] - run["a"]) / run["bays"]
                for i in range(run["bays"]):
                    a = run["a"] + i * span
                    b = a + span
                    mid = (a + b) / 2
                    kit = Kit()
                    openings = []
                    balcony = None
                    if run["kind"] == "front":
                        column = run["columns"][i]
                        if s == 0 and column == DOOR_COLUMN:
                            openings = [{"x0": mid - 1.1, "x1": mid + 1.1, "z0": 0.0, "z1": 2.8, "kind": "door"}]
                        elif (column, s) in balconies:
                            openings = [{"x0": mid - 0.8, "x1": mid + 0.8, "z0": z0, "z1": z0 + 2.4, "kind": "window"}]
                            balcony = (a, b, run["at"], z0)
                        else:
                            openings = [window(mid, z0, span)]
                    elif run["kind"] == "back":
                        if s == 0 and i == 0:
                            openings = [{"x0": mid - 0.65, "x1": mid + 0.65, "z0": 0.0, "z1": 2.4, "kind": "door"}]
                        else:
                            openings = [window(mid, z0, span)]
                    elif s in side_storeys and (i == 0 or run["kind"] == "notch"):
                        openings = [window(mid, z0, span)]

                    if run["axis"] == "x":
                        kit.wall(a, b, z0, z1, run["at"], WALL, run["inward"], openings, look)
                        if openings and openings[0]["kind"] == "door" and run["kind"] == "front":
                            # The double doors: a split down the middle and a pane in each leaf.
                            y = run["at"] + 0.13
                            flat(kit, (mid, y, 1.4), (0, -1, 0), [(-0.04, -1.4), (0.04, -1.4), (0.04, 1.4), (-0.04, 1.4)], pal["trim"], lift=0.03)
                            for side in (-1, 1):
                                flat(kit, (mid + side * 0.55, y, 1.85), (0, -1, 0), [(-0.3, -0.45), (0.3, -0.45), (0.3, 0.45), (-0.3, 0.45)], "windowBlue", lift=0.03)
                    elif openings:
                        wall_y(kit, a, b, z0, z1, run["at"], WALL, run["inward"], openings, look)
                    else:
                        lo, hi = sorted((run["at"], run["at"] + run["inward"] * WALL))
                        inner = "+x" if run["inward"] > 0 else "-x"
                        kit.box((lo, a, z0), (hi, b, z1), look["wall"], sides={inner: "interiorCream"})
                    key = (r, i)
                    module = add(kit, "wall", "plaster", s, supports=(below[key],) if key in below else ())
                    below[key] = module
                    ids.append(module)
                    if s == 0 and run["kind"] == "front" and run["columns"][i] == DOOR_COLUMN:
                        door_bay = (module, mid, run["at"])
                    if balcony:
                        kit = Kit()
                        _balcony(kit, *balcony, balcony_style, accent, pal["trim"])
                        add(kit, "detail", "tin" if balcony_style == "rail" else "plaster", s, supports=(module,))
            by_storey.append(ids)

            if s > 0:
                for lo, hi in floors:
                    kit = Kit()
                    kit.box((lo[0], lo[1], z0 - 0.2), (hi[0], hi[1], z0), "interiorCream")
                    add(kit, "floor", "wood", s, supports=by_storey[s - 1])

        # --- the grand front door: steps and a portico ---
        module, dx, y = door_bay
        kit = Kit()
        kit.box((dx - 2.0, y - 1.6, 0), (dx + 2.0, y, 0.2), "stone", skip=("-z", "+y"))
        if portico == "canopy":
            kit.box((dx - 2.1, y - 1.7, 2.95), (dx + 2.1, y, 3.2), accent, sides={"-y": pal["trim"]}, skip=("+y",))
            for side in (-1, 1):
                beam(kit, (dx + side * 1.9, y - 1.55, 3.2), (dx + side * 1.9, y, 4.3), 0.1, "tyre", caps=False)
        else:
            for side in (-1, 1):
                px = dx + side * 1.6
                kit.box((px - 0.2, y - 1.45, 0.2), (px + 0.2, y - 1.05, 2.95), pal["trim"], skip=("-z", "+z"))
            kit.box((dx - 2.0, y - 1.6, 2.95), (dx + 2.0, y, 3.25), pal["trim"], skip=("+y",))
            if portico == "pediment":
                kit.extrude_y([(dx - 2.0, 3.25), (dx + 2.0, 3.25), (dx, 4.1)], y - 1.6, y, accent)
        add(kit, "detail", "plaster", 0, supports=(module,), collider="hull" if portico == "pediment" else "box")

        # --- flat roof: its edge is the cornice ---
        roof_ids = []
        for lo, hi in roofs:
            kit = Kit()
            kit.box(
                (lo[0], lo[1], top),
                (hi[0], hi[1], top + 0.35),
                pal["trim"],
                sides={"+z": pal["roof"], "-z": "interiorCream"},
            )
            roof_ids.append(add(kit, "roof", "plaster", storeys, supports=by_storey[-1]))
        roof_z = top + 0.35

        # --- parapet, a piece for each run of wall ---
        for run in runs:
            kit = Kit()
            lo, hi = sorted((run["at"], run["at"] + run["inward"] * WALL))
            if run["axis"] == "x":
                kit.box((run["a"], lo, roof_z), (run["b"], hi, roof_z + 0.7), pal["wall"], sides={"+z": pal["trim"]}, skip=("-z",))
                if run["kind"] == "front" and DOOR_COLUMN in run["columns"]:
                    # The parapet steps up over the front door's bay.
                    span = (run["b"] - run["a"]) / run["bays"]
                    mid = run["a"] + (run["columns"].index(DOOR_COLUMN) + 0.5) * span
                    kit.box((mid - span * 0.42, lo - 0.08, roof_z + 0.7), (mid + span * 0.42, hi + 0.08, roof_z + 1.9), pal["wall"], sides={"+z": pal["trim"]}, skip=("-z",))
            else:
                kit.box((lo, run["a"], roof_z), (hi, run["b"], roof_z + 0.7), pal["wall"], sides={"+z": pal["trim"]}, skip=("-z",))
            add(kit, "band", "plaster", storeys, supports=roof_ids)

        # --- water tank and stair-head hut ---
        tx = tank_side * width * 0.24
        tank_base = roof_z + 1.7  # up on legs, so it stands clear of the parapet in the silhouette
        ty = back - 2.4
        kit = Kit()
        for sx in (-1, 1):
            for sy in (-1, 1):
                px, py = tx + sx * 0.85, ty + sy * 0.85
                kit.box((px - 0.13, py - 0.13, roof_z), (px + 0.13, py + 0.13, tank_base), "tyre", skip=("-z", "+z"))
        if tank_style == "round":
            frustum(kit, tx, ty, tank_base, 1.55, tank_base + 2.1, 1.55, "wood", bottom="wood")
            frustum(kit, tx, ty, tank_base + 2.1, 1.85, tank_base + 3.4, 0, accent, bottom=accent)
        else:
            kit.box((tx - 1.5, ty - 1.2, tank_base), (tx + 1.5, ty + 1.2, tank_base + 1.9), accent)
            kit.box((tx - 1.65, ty - 1.35, tank_base + 1.9), (tx + 1.65, ty + 1.35, tank_base + 2.12), pal["trim"])
        add(kit, "detail", "tin", storeys, supports=roof_ids[:1], collider="hull" if tank_style == "round" else "box")

        hx = -tank_side * width * 0.2
        kit = Kit()
        kit.box((hx - 1.2, ty - 1.2, roof_z), (hx + 1.2, ty + 1.2, roof_z + 2.2), pal["wall"], skip=("-z", "+z"))
        kit.box((hx - 1.4, ty - 1.4, roof_z + 2.2), (hx + 1.4, ty + 1.4, roof_z + 2.42), pal["trim"])
        flat(kit, (hx, ty - 1.2, roof_z + 0.95), (0, -1, 0), [(-0.5, -0.95), (0.5, -0.95), (0.5, 0.95), (-0.5, 0.95)], pal["door"], lift=0.03)
        add(kit, "detail", "plaster", storeys, supports=roof_ids[:1])

    # --- measure the bare block, then spend what is left ---
    spent = [0]

    def measure(kit, *args, **kwargs):
        spent[0] += kit.triangles()
        return "measured"

    construct(measure, set(), set())
    probe = Kit()
    _balcony(probe, 0, 4, 0, 0, balcony_style, accent, pal["trim"])
    balcony_cost = probe.triangles()
    left = TRIANGLE_BUDGET - spent[0] - 8

    rows = []
    for s in range(storeys - 1, 0, -1):
        if balcony_pattern == "outer":
            columns = [0, 2]
        elif balcony_pattern == "centre":
            columns = [1]
        elif balcony_pattern == "all":
            columns = [0, 1, 2]
        else:
            columns = [0, 2] if s % 2 else [1]
        if s == 1:  # the portico is in the way above the front door
            columns = [c for c in columns if c != DOOR_COLUMN]
        rows.append((s, columns))

    balconies = set()
    side_storeys = set()
    side_cost = 24 * (3 if plan == "L" else 2)  # what a window adds to a plain bay, for each windowed bay on a storey
    # A first share of balconies, then side windows, then any balconies still wanted.
    for share in (0.55, 1.0):
        for s, columns in rows:
            cost = balcony_cost * len(columns)
            if columns and (columns[0], s) not in balconies and cost <= left * share:
                balconies.update((c, s) for c in columns)
                left -= cost
        if share < 1.0:
            for s in range(storeys - 1, -1, -1):
                if side_cost <= left:
                    side_storeys.add(s)
                    left -= side_cost

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    construct(building.add, balconies, side_storeys)

    empty, stats = building.finish(
        look=(
            f"{plan}/{storeys}st/{width:g}x{depth:g}/balconies-{balcony_pattern}-{balcony_style}x{len(balconies)}"
            f"/{window_style}/{portico}/tank-{tank_style}/base-{base_pick}/side-windows-{len(side_storeys)}"
        )
    )
    return empty, stats


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(24, 26))


if __name__ == "__main__":
    previews()
