"""Terraced house row generator.

A row of 3-5 narrow two-storey houses under one pitched roof that runs along
the row, with chimney stacks, front doors with steps, and windows front and
back. The seed varies the row's proportions, roof ends (gabled or hipped),
roof features (front gables or dormers), bay windows, door canopies, window
style and chimneys.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/terraced_house.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "terraced_house"
HITS_TO_COLLAPSE = 2  # medium building
TRIANGLE_BUDGET = 1300  # terraced rows have their own budget: up to 5 houses, windows front and back

WALL = 0.35
OVERHANG = 0.45
ROOF_THICKNESS = 0.32


def _pattern(name, houses):
    """Which houses in the row get a feature."""
    if name == "all":
        return set(range(houses))
    if name == "alternate":
        return set(range(0, houses, 2))
    if name == "ends":
        return {0, houses - 1}
    return set(range(1, houses - 1))  # middle


def build(building_id, seed, scheme=None, collection=None):
    """Build one row. Returns (empty, stats)."""
    rng = random.Random(seed)

    # --- the row's character: one set of choices, used by every house in it ---
    houses = rng.choice([3, 4, 4, 5])
    house_width = rng.choice([3.9, 4.4, 5.0])
    depth = rng.choice([5.5, 6.0, 6.5])
    storey = rng.choice([2.8, 3.0, 3.2])
    rise = rng.choice([1.8, 2.3, 2.8, 3.2])
    roof_ends = rng.choice(["gable", "gable", "hipped"])
    roof_feature = rng.choice(["none", "gables", "gables", "dormers", "dormers"])
    feature_pattern = rng.choice(["all", "alternate", "ends", "middle"])
    window_style = rng.choice(["single", "double", "tall"])
    bay_style = rng.choice(["none", "single", "single", "double"])
    bay_pattern = rng.choice(["all", "alternate", "ends", "middle"])
    canopy = rng.choice(["none", "flat", "pitched"])
    chimney_style = rng.choice(["stack", "tall", "end"])
    mirrored = rng.random() < 0.6  # doors paired up, as on a real terrace
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    if roof_ends == "hipped" and chimney_style == "end":
        chimney_style = "tall"

    featured = _pattern(feature_pattern, houses) if roof_feature != "none" else set()
    if roof_ends == "hipped":
        featured -= {0, houses - 1}  # the hip leaves no room on the end houses
    bays = _pattern(bay_pattern, houses) if bay_style != "none" else set()

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

    row_x0 = -houses * house_width / 2
    row_x1 = -row_x0
    front = -depth / 2
    back = depth / 2
    eaves = storey * 2
    ridge = eaves + rise
    slope = rise / (depth / 2)
    eave_z = eaves - slope * OVERHANG

    def upper_windows(mid, z):
        if window_style == "single":
            return [{"x0": mid - 0.85, "x1": mid + 0.85, "z0": z + 0.9, "z1": z + 2.4, "kind": "window"}]
        if window_style == "tall":
            return [{"x0": mid - 0.65, "x1": mid + 0.65, "z0": z + 0.5, "z1": z + 2.5, "kind": "window"}]
        return [
            {"x0": mid - 1.5, "x1": mid - 0.4, "z0": z + 0.9, "z1": z + 2.4, "kind": "window"},
            {"x0": mid + 0.4, "x1": mid + 1.5, "z0": z + 0.9, "z1": z + 2.4, "kind": "window"},
        ]

    def bay(kit, wx0, wx1, z0, z1, cap):
        """A projecting bay window on the front."""
        bx0, bx1 = wx0 - 0.1, wx1 + 0.1
        by = front - 0.6
        g0, g1 = z0 + 0.35, z1 - 0.2
        kit.box((bx0, by, z0), (bx1, front, z1), pal["trim"], skip=("+y",))
        glass_y = by - 0.03
        kit.poly(
            [(bx0 + 0.2, glass_y, g0), (bx1 - 0.2, glass_y, g0), (bx1 - 0.2, glass_y, g1), (bx0 + 0.2, glass_y, g1)],
            (0, -1, 0),
            "windowBlue",
        )
        kit.shine(bx0 + 0.2, bx1 - 0.2, g0, g1, glass_y - 0.03, (0, -1, 0), "windowShine")
        for x, hint in ((bx0 - 0.03, (-1, 0, 0)), (bx1 + 0.03, (1, 0, 0))):
            kit.poly(
                [(x, by + 0.12, g0), (x, front - 0.12, g0), (x, front - 0.12, g1), (x, by + 0.12, g1)],
                hint,
                "windowBlue",
            )
        if cap:
            kit.box((bx0 - 0.12, by - 0.12, z1), (bx1 + 0.12, front, z1 + 0.2), pal["roof"], skip=("+y",))

    roof_front = []
    roof_back = []

    for h in range(houses):
        xa = row_x0 + h * house_width
        xb = xa + house_width
        mid = (xa + xb) / 2
        door_left = (h % 2 == 0) if mirrored else True
        has_bay = h in bays

        door_x0 = xa + 0.5 if door_left else xb - 0.5 - 1.3
        door = {"x0": door_x0, "x1": door_x0 + 1.3, "z0": 0.0, "z1": 2.4, "kind": "door"}
        win_centre = (door["x1"] + xb) / 2 if door_left else (xa + door["x0"]) / 2
        half = min(0.75, (house_width - 1.3 - 0.5) / 2 - 0.3)
        window = {"x0": win_centre - half, "x1": win_centre + half, "z0": 0.9, "z1": 2.4, "kind": "window"}

        # --- ground floor front: door, steps, canopy, and a window or bay ---
        kit = Kit()
        kit.wall(xa, xb, 0, storey, front, WALL, 1, [door] if has_bay else [door, window], colours)
        kit.box(
            (door["x0"] - 0.15, front - 0.6, 0),
            (door["x1"] + 0.15, front, 0.25),
            "stone",
            skip=("-z", "+y"),
        )
        if canopy == "flat":
            kit.box(
                (door["x0"] - 0.25, front - 0.7, 2.55),
                (door["x1"] + 0.25, front, 2.7),
                pal["roof"],
                skip=("+y",),
            )
        elif canopy == "pitched":
            kit.extrude_x(
                [(front - 0.75, 2.5), (front, 2.5), (front, 2.95)],
                door["x0"] - 0.25,
                door["x1"] + 0.25,
                pal["roof"],
            )
        if has_bay:
            if bay_style == "double":
                bay(kit, window["x0"], window["x1"], 0.4, storey, cap=False)
            else:
                bay(kit, window["x0"], window["x1"], 0.6, 2.5, cap=True)
        f0 = add(kit, "wall", "plaster", 0)

        # --- ground floor back: back door and a window ---
        kit = Kit()
        kit.wall(xa, xb, 0, storey, back, WALL, -1, [door, window], colours)
        b0 = add(kit, "wall", "plaster", 0)

        # --- upper floor slab: the dolls'-house floor ---
        kit = Kit()
        kit.box(
            (xa + (WALL if h == 0 else 0), front + WALL, storey - 0.2),
            (xb - (WALL if h == houses - 1 else 0), back - WALL, storey),
            "interiorCream",
        )
        add(kit, "floor", "wood", 1, supports=(f0, b0))

        # --- upper floor, front and back: one window style for the whole row ---
        kit = Kit()
        if has_bay and bay_style == "double":
            kit.wall(xa, xb, storey, eaves, front, WALL, 1, [], colours)
            bay(kit, window["x0"], window["x1"], storey, storey + 2.5, cap=True)
        else:
            kit.wall(xa, xb, storey, eaves, front, WALL, 1, upper_windows(mid, storey), colours)
        f1 = add(kit, "wall", "plaster", 1, supports=(f0,))

        kit = Kit()
        kit.wall(xa, xb, storey, eaves, back, WALL, -1, upper_windows(mid, storey), colours)
        b1 = add(kit, "wall", "plaster", 1, supports=(b0,))

        # --- roof halves: gabled ends overhang, hipped ends slope back to the ridge ---
        first, last = h == 0, h == houses - 1
        if roof_ends == "hipped":
            ex0 = xa - (OVERHANG if first else 0)
            ex1 = xb + (OVERHANG if last else 0)
            rx0 = xa + (depth / 2 if first else 0)
            rx1 = xb - (depth / 2 if last else 0)
        else:
            ex0 = rx0 = xa - (0.3 if first else 0)
            ex1 = rx1 = xb + (0.3 if last else 0)
        for sign, wall_id, bucket in ((-1, f1, roof_front), (1, b1, roof_back)):
            eave_y = sign * (depth / 2 + OVERHANG)
            kit = Kit()
            kit.slab(
                [(ex0, eave_y, eave_z), (ex1, eave_y, eave_z), (rx1, 0, ridge), (rx0, 0, ridge)],
                ROOF_THICKNESS,
                pal["roof"],
            )
            bucket.append(add(kit, "roof", "tile", 2, supports=(wall_id,), collider="hull"))

        # --- roof features ---
        if h in featured and roof_feature == "gables":
            # A front gable: a triangle of wall with its own little cross roof. Its face
            # sits just proud of the main eaves, or the overhang would hide it.
            gable_width = house_width * 0.7
            gable_height = min(gable_width / 2 * 0.95, rise * 0.9)
            gable_slope = gable_height / (gable_width / 2)
            face = front - OVERHANG - 0.05
            base = eave_z - 0.05
            y_back = min(front + (depth / 2) * (gable_height / rise) + 0.4, 0)
            kit = Kit()
            kit.extrude_y(
                [(mid - gable_width / 2, base), (mid + gable_width / 2, base), (mid, base + gable_height)],
                face,
                front + WALL,
                pal["wall"],
            )
            for side in (-1, 1):
                x_low = mid + side * (gable_width / 2 + 0.3)
                z_low = base - gable_slope * 0.3
                kit.extrude_y(
                    [
                        (x_low, z_low),
                        (mid, base + gable_height),
                        (mid, base + gable_height + 0.26),
                        (x_low, z_low + 0.26),
                    ],
                    face - 0.3,
                    y_back,
                    pal["roof"],
                )
            if gable_height > 1.2:
                kit.poly(
                    [
                        (mid - 0.32, face - 0.03, base + 0.25),
                        (mid + 0.32, face - 0.03, base + 0.25),
                        (mid + 0.32, face - 0.03, base + 0.85),
                        (mid - 0.32, face - 0.03, base + 0.85),
                    ],
                    (0, -1, 0),
                    "windowBlue",
                )
            add(kit, "roof", "tile", 2, supports=(f1,), collider="hull")
        elif h in featured and roof_feature == "dormers":
            y0, y1 = front + 0.5, front + 2.1
            top = eaves + slope * (y1 - front) + 0.15
            z_front = eaves + slope * (y0 - front)
            kit = Kit()
            kit.box((mid - 0.8, y0, z_front - 0.1), (mid + 0.8, y1, top), pal["wall"], skip=("-z",))
            g0 = z_front + 0.4
            kit.poly(
                [
                    (mid - 0.55, y0 - 0.03, g0),
                    (mid + 0.55, y0 - 0.03, g0),
                    (mid + 0.55, y0 - 0.03, top - 0.15),
                    (mid - 0.55, y0 - 0.03, top - 0.15),
                ],
                (0, -1, 0),
                "windowBlue",
            )
            kit.shine(mid - 0.55, mid + 0.55, g0, top - 0.15, y0 - 0.06, (0, -1, 0), "windowShine")
            kit.box((mid - 0.95, y0 - 0.2, top), (mid + 0.95, y1, top + 0.18), pal["roof"])
            add(kit, "detail", "tile", 2, supports=(roof_front[h],))

    # --- end walls, with a gable or a hip above ---
    end_tops = []
    for x0, x1 in ((row_x0, row_x0 + WALL), (row_x1 - WALL, row_x1)):
        left = x0 == row_x0
        inner = "+x" if left else "-x"
        kit = Kit()
        kit.box((x0, front + WALL, 0), (x1, back - WALL, storey), pal["wall"], sides={inner: "interiorCream"})
        s0 = add(kit, "wall", "plaster", 0)
        kit = Kit()
        kit.box((x0, front + WALL, storey), (x1, back - WALL, eaves), pal["wall"], sides={inner: "interiorCream"})
        s1 = add(kit, "wall", "plaster", 1, supports=(s0,))
        kit = Kit()
        if roof_ends == "hipped":
            ex = row_x0 - OVERHANG if left else row_x1 + OVERHANG
            apex = row_x0 + depth / 2 if left else row_x1 - depth / 2
            kit.slab(
                [(ex, -(depth / 2 + OVERHANG), eave_z), (ex, depth / 2 + OVERHANG, eave_z), (apex, 0, ridge)],
                ROOF_THICKNESS,
                pal["roof"],
            )
            end_tops.append(add(kit, "roof", "tile", 2, supports=(s1,), collider="hull"))
        else:
            kit.extrude_x([(front, eaves), (back, eaves), (0, ridge)], x0, x1, pal["wall"])
            end_tops.append(add(kit, "wall", "plaster", 2, supports=(s1,), collider="hull"))

    # --- chimneys ---
    def chimney(x, supports):
        kit = Kit()
        if chimney_style == "tall":
            kit.box((x - 0.4, -0.4, ridge - 0.5), (x + 0.4, 0.4, ridge + 2.0), pal["wall"], skip=("-z",))
            kit.box((x - 0.5, -0.5, ridge + 2.0), (x + 0.5, 0.5, ridge + 2.15), pal["trim"])
            for dy in (-0.22, 0.22):
                kit.box(
                    (x - 0.15, dy - 0.15, ridge + 2.15),
                    (x + 0.15, dy + 0.15, ridge + 2.6),
                    "tangerine",
                    skip=("-z",),
                )
        else:
            kit.box((x - 0.55, -0.45, ridge - 0.5), (x + 0.55, 0.45, ridge + 1.2), pal["wall"], skip=("-z",))
            kit.box((x - 0.65, -0.55, ridge + 1.2), (x + 0.65, 0.55, ridge + 1.4), pal["trim"])
        add(kit, "detail", "plaster", 2, supports=supports)

    if chimney_style == "end":
        chimney(row_x0 + 0.6, (end_tops[0],))
        chimney(row_x1 - 0.6, (end_tops[1],))
    else:
        boundaries = list(range(1, houses))
        chosen = [b for b in boundaries if rng.random() < 0.65] or [rng.choice(boundaries)]
        for b in chosen:
            chimney(
                row_x0 + b * house_width,
                (roof_front[b - 1], roof_back[b - 1], roof_front[b], roof_back[b]),
            )

    empty, stats = building.finish(
        look=f"houses={houses} {roof_ends}/{roof_feature}/{window_style}/bay-{bay_style}/{canopy}/{chimney_style}"
    )
    return empty, stats


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET)


if __name__ == "__main__":
    previews()
