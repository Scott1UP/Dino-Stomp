"""High-street shop generator.

A two-storey shop: a big shop window and a door under a striped awning, a
hanging sign with a picture on it (a loaf, an ice cream cone or a fish, never
words), and a top that makes the silhouette: a flat roof behind a stepped
parapet, a flat roof with a pediment, or a pitched roof hidden behind a tall
false front. The seed varies the proportions, which side the door is on, the
top, the awning (style, stripes, how far it reaches), the sign (picture,
board shape, which side), the upstairs windows and the roof clutter.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/high_street_shop.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import beam, flat, pictogram, polygon, wall_y  # noqa: E402

TYPE = "high_street_shop"
HITS_TO_COLLAPSE = 2  # medium building
TRIANGLE_BUDGET = 900

WALL = 0.35
DOOR_BAY = 2.3


def build(building_id, seed, scheme=None, collection=None):
    """Build one shop. Returns (empty, stats)."""
    rng = random.Random(seed)

    # --- the shop's character ---
    width = rng.choice([6.0, 6.5, 7.0])
    depth = rng.choice([6.5, 7.0, 7.5])
    ground = rng.choice([3.4, 3.6])
    upper = rng.choice([2.8, 3.0, 3.2])
    door_side = rng.choice([-1, 1])
    top_style = rng.choice(["stepped", "false_front", "pediment", "stepped", "false_front"])
    awning_style = rng.choice(["scalloped", "wedge"])
    awning_reach = rng.choice(["window", "full"])
    awning_out = rng.choice([1.0, 1.2, 1.4])
    stripes = rng.choice([5, 6, 7])
    stripe_pick = rng.choice(["roof", "door", "both"])
    picture = rng.choice(["loaf", "cone", "fish"])
    sign_shape = rng.choice(["board", "round"])
    sign_side = rng.choice([-1, 1])
    window_style = rng.choice(["square", "tall", "wide"])
    clutter = rng.choice(["none", "chimney", "vent"])
    rise = rng.choice([1.6, 2.0, 2.4])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    accent = pal["door"] if pal["door"] != "doorBrown" else pal["roof"]
    if stripe_pick == "roof":
        stripe_colours = (pal["roof"], "trimWhite")
    elif stripe_pick == "door":
        stripe_colours = (accent, "trimWhite")
    else:
        stripe_colours = (pal["roof"], accent if accent != pal["roof"] else "trimWhite")

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

    x0, x1 = -width / 2, width / 2
    front, back = -depth / 2, depth / 2
    top = ground + upper

    # The front is a narrow door bay and a wide shop-window bay.
    split = door_side * (width / 2 - DOOR_BAY)
    if door_side < 0:
        door_bay, shop_bay = (x0, split), (split, x1)
    else:
        shop_bay, door_bay = (x0, split), (split, x1)
    door_x = (door_bay[0] + door_bay[1]) / 2

    def upper_window(centre, z):
        if window_style == "tall":
            return {"x0": centre - 0.6, "x1": centre + 0.6, "z0": z + 0.55, "z1": z + upper - 0.45, "kind": "window"}
        if window_style == "wide":
            return {"x0": centre - 1.05, "x1": centre + 1.05, "z0": z + 0.95, "z1": z + upper - 0.55, "kind": "window"}
        return {"x0": centre - 0.75, "x1": centre + 0.75, "z0": z + 0.85, "z1": z + upper - 0.5, "kind": "window"}

    # --- ground floor front: the shopfront ---
    kit = Kit()
    door = {"x0": door_x - 0.65, "x1": door_x + 0.65, "z0": 0.0, "z1": 2.4, "kind": "door"}
    kit.wall(door_bay[0], door_bay[1], 0, ground, front, WALL, 1, [door], colours)
    kit.box((door["x0"] - 0.15, front - 0.5, 0), (door["x1"] + 0.15, front, 0.18), "stone", skip=("-z", "+y"))
    # A little pane in the door.
    flat(kit, (door_x, front + 0.13, 1.65), (0, -1, 0), [(-0.38, -0.4), (0.38, -0.4), (0.38, 0.4), (-0.38, 0.4)], "windowBlue", lift=0.03)
    front_door = add(kit, "wall", "plaster", 0)

    kit = Kit()
    shop_window = {"x0": shop_bay[0] + 0.4, "x1": shop_bay[1] - 0.4, "z0": 0.65, "z1": 2.75, "kind": "window"}
    kit.wall(shop_bay[0], shop_bay[1], 0, ground, front, WALL, 1, [shop_window], colours)
    # The sill under the shop window.
    kit.box(
        (shop_window["x0"] - 0.12, front - 0.14, 0.5),
        (shop_window["x1"] + 0.12, front, 0.65),
        pal["trim"],
        skip=("+y",),
    )
    front_shop = add(kit, "wall", "glass", 0)

    # --- ground floor back and sides ---
    back_ground = []
    for xa, xb, has_door in ((x0, 0.0, door_side > 0), (0.0, x1, door_side < 0)):
        mid = (xa + xb) / 2
        kit = Kit()
        if has_door:
            opening = {"x0": mid - 0.65, "x1": mid + 0.65, "z0": 0.0, "z1": 2.4, "kind": "door"}
        else:
            opening = {"x0": mid - 0.8, "x1": mid + 0.8, "z0": 1.0, "z1": 2.4, "kind": "window"}
        kit.wall(xa, xb, 0, ground, back, WALL, -1, [opening], colours)
        back_ground.append(add(kit, "wall", "plaster", 0))

    def side_bays(z0, z1, storey, below, windows):
        ids = []
        index = 0
        for sign in (-1, 1):
            x_out = sign * width / 2
            for ya, yb in ((front + WALL, 0.0), (0.0, back - WALL)):
                kit = Kit()
                if windows and ya < 0:
                    centre = (ya + yb) / 2
                    opening = {"x0": centre - 0.6, "x1": centre + 0.6, "z0": z0 + 0.85, "z1": z1 - 0.5, "kind": "window"}
                    wall_y(kit, ya, yb, z0, z1, x_out, WALL, -sign, [opening], colours)
                else:
                    lo, hi = sorted((x_out, x_out - sign * WALL))
                    kit.box((lo, ya, z0), (hi, yb, z1), pal["wall"], sides={"+x" if sign < 0 else "-x": "interiorCream"})
                ids.append(add(kit, "wall", "plaster", storey, supports=(below[index],) if below else ()))
                index += 1
        return ids

    side_ground = side_bays(0, ground, 0, None, windows=False)
    ground_walls = [front_door, front_shop] + back_ground + side_ground

    # --- fascia: the band over the shopfront that the awning hangs from ---
    fascia_z = ground - 0.5
    kit = Kit()
    kit.box((x0 - 0.06, front - 0.16, fascia_z), (x1 + 0.06, front, ground - 0.02), stripe_colours[0], skip=("+y",))
    add(kit, "band", "wood", 0, supports=(front_door, front_shop))

    # --- striped awning ---
    if awning_reach == "full":
        ax0, ax1 = x0 + 0.1, x1 - 0.1
        holders = (front_door, front_shop)
    else:
        ax0, ax1 = shop_bay[0] + 0.15, shop_bay[1] - 0.15
        holders = (front_shop,)
    z_wall = fascia_z
    z_edge = fascia_z - awning_out * 0.38
    y_edge = front - awning_out
    strip = (ax1 - ax0) / stripes
    kit = Kit()
    for i in range(stripes):
        xa = ax0 + i * strip
        xb = xa + strip
        colour = stripe_colours[i % 2]
        slope = [(xa, front, z_wall), (xb, front, z_wall), (xb, y_edge, z_edge), (xa, y_edge, z_edge)]
        kit.poly(slope, (0, -0.4, 1), colour)
        if awning_style == "wedge":
            drop = z_edge - 0.28
            kit.poly([(xa, y_edge, z_edge), (xb, y_edge, z_edge), (xb, y_edge, drop), (xa, y_edge, drop)], (0, -1, 0), colour)
            kit.poly([(xa, front, drop), (xb, front, drop), (xb, y_edge, drop), (xa, y_edge, drop)], (0, 0, -1), colour)
        else:
            kit.poly(slope, (0, 0.4, -1), colour)
            xm = (xa + xb) / 2
            points = [(xa, y_edge, z_edge), (xb, y_edge, z_edge), (xb, y_edge, z_edge - 0.16), (xm, y_edge, z_edge - 0.42), (xa, y_edge, z_edge - 0.16)]
            kit.poly(points, (0, -1, 0), colour)
            kit.poly(points, (0, 1, 0), colour)
    if awning_style == "wedge":
        drop = z_edge - 0.28
        for x, hint, colour in ((ax0, (-1, 0, 0), stripe_colours[0]), (ax1, (1, 0, 0), stripe_colours[(stripes - 1) % 2])):
            kit.poly([(x, front, z_wall), (x, y_edge, z_edge), (x, y_edge, drop), (x, front, drop)], hint, colour)
        kit.poly([(ax0, front, drop), (ax1, front, drop), (ax1, front, z_wall), (ax0, front, z_wall)], (0, 1, 0), stripe_colours[0])
    add(kit, "detail", "wood", 0, supports=holders, collider="hull")

    # --- upper floor ---
    kit = Kit()
    kit.box((x0 + WALL, front + WALL, ground - 0.2), (x1 - WALL, back - WALL, ground), "interiorCream")
    add(kit, "floor", "wood", 1, supports=ground_walls)

    front_upper = []
    back_upper = []
    for y_out, inward, below, bucket in (
        (front, 1, (front_door, front_shop) if door_side < 0 else (front_shop, front_door), front_upper),
        (back, -1, back_ground, back_upper),
    ):
        for index, (xa, xb) in enumerate(((x0, 0.0), (0.0, x1))):
            kit = Kit()
            kit.wall(xa, xb, ground, top, y_out, WALL, inward, [upper_window((xa + xb) / 2, ground)], colours)
            bucket.append(add(kit, "wall", "plaster", 1, supports=(below[index],)))
    side_upper = side_bays(ground, top, 1, side_ground, windows=True)
    upper_walls = front_upper + back_upper + side_upper

    # --- hanging sign: a picture on a board, swinging from a bracket ---
    sign_x = sign_side * (width / 2 - 0.45)
    arm_z = ground + 1.35
    board_y = front - 1.0
    board_z = ground + 0.5
    half = 0.62
    kit = Kit()
    beam(kit, (sign_x, front, arm_z), (sign_x, front - 1.6, arm_z), 0.1, "tyre")
    if sign_shape == "round":
        section = [(board_y + a, board_z + b) for a, b in polygon(half * 1.12)]
        kit.extrude_x(section, sign_x - 0.07, sign_x + 0.07, pal["trim"])
        kit.box((sign_x - 0.03, board_y - 0.04, board_z + half), (sign_x + 0.03, board_y + 0.04, arm_z), "tyre", skip=("-z", "+z"))
    else:
        kit.box((sign_x - 0.07, board_y - half, board_z - half), (sign_x + 0.07, board_y + half, board_z + half), pal["trim"])
        for dy in (-0.42, 0.42):
            kit.box((sign_x - 0.03, board_y + dy - 0.03, board_z + half), (sign_x + 0.03, board_y + dy + 0.03, arm_z), "tyre", skip=("-z", "+z"))
    for side in (-1, 1):
        pictogram(kit, picture, (sign_x + side * 0.07, board_y, board_z), (side, 0, 0), half * 1.75, lift=0.02)
    add(kit, "detail", "wood", 1, supports=(front_upper[0 if sign_side < 0 else 1],))

    def medallion(kit, face_y, z, size):
        """The shop's picture again, big, on the front of the top."""
        centre = (0, face_y, z)
        flat(kit, centre, (0, -1, 0), polygon(size * 0.62), pal["trim"], lift=0.02)
        pictogram(kit, picture, centre, (0, -1, 0), size, lift=0.05)

    # --- the top ---
    if top_style == "false_front":
        # A pitched roof running front to back, hidden from the street by a tall false front.
        ridge = top + rise
        slope = rise / (width / 2)
        halves = []
        for sign in (-1, 1):
            eave_x = sign * (width / 2 + 0.35)
            kit = Kit()
            kit.slab(
                [
                    (eave_x, front + WALL, top - slope * 0.35),
                    (eave_x, back + 0.3, top - slope * 0.35),
                    (0, back + 0.3, ridge),
                    (0, front + WALL, ridge),
                ],
                0.28,
                pal["roof"],
            )
            holders = (side_upper[0], side_upper[1]) if sign < 0 else (side_upper[2], side_upper[3])
            halves.append(add(kit, "roof", "tile", 2, supports=holders, collider="hull"))

        kit = Kit()
        kit.extrude_y([(x0, top), (x1, top), (0, ridge)], back - WALL, back, pal["wall"])
        add(kit, "wall", "plaster", 2, supports=back_upper, collider="hull")

        crown = ridge + 0.75
        kit = Kit()
        kit.box((x0 - 0.1, front - 0.08, top), (x1 + 0.1, front + WALL, crown), pal["wall"], sides={"+z": pal["trim"]})
        kit.box((x0 - 0.22, front - 0.2, top - 0.02), (x1 + 0.22, front + WALL, top + 0.22), pal["trim"], skip=("+y",))
        false_front = add(kit, "wall", "plaster", 2, supports=front_upper)

        kit = Kit()
        kit.box((-width * 0.27, front - 0.08, crown), (width * 0.27, front + WALL, crown + 0.55), pal["wall"], sides={"+z": pal["trim"]})
        medallion(kit, front - 0.08, top + (crown - top) * 0.55, min(1.9, (crown - top) * 0.66))
        add(kit, "detail", "wood", 2, supports=(false_front,))
        roof_ids = halves
        roof_z = None
    else:
        # A flat roof, its edge showing as a cornice, with a parapet round it.
        kit = Kit()
        kit.box(
            (x0 - 0.14, front - 0.14, top),
            (x1 + 0.14, back + 0.14, top + 0.22),
            pal["trim"],
            sides={"+z": pal["roof"], "-z": "interiorCream"},
        )
        roof = add(kit, "roof", "plaster", 2, supports=upper_walls)
        roof_z = top + 0.22
        roof_ids = [roof]

        kit = Kit()
        low = roof_z + 0.5
        kit.box((x0, back - 0.3, roof_z), (x1, back, low), pal["wall"], sides={"+z": pal["trim"]}, skip=("-z",))
        for xa, xb in ((x0, x0 + 0.3), (x1 - 0.3, x1)):
            kit.box((xa, front + 0.3, roof_z), (xb, back - 0.3, low), pal["wall"], sides={"+z": pal["trim"]}, skip=("-z",))
        add(kit, "band", "plaster", 2, supports=(roof,))

        flank = roof_z + 0.85
        kit = Kit()
        kit.box((x0, front, roof_z), (x1, front + 0.3, flank), pal["wall"], sides={"+z": pal["trim"]}, skip=("-z",))
        parapet = add(kit, "band", "plaster", 2, supports=(roof,))

        kit = Kit()
        if top_style == "stepped":
            # Three steps up to the middle, so the top reads as a stepped gable from any side.
            kit.box((-width * 0.34, front - 0.06, roof_z), (width * 0.34, front + 0.36, flank + 0.9), pal["wall"], sides={"+z": pal["trim"]}, skip=("-z",))
            kit.box((-width * 0.2, front - 0.06, flank + 0.9), (width * 0.2, front + 0.36, flank + 1.8), pal["wall"], sides={"+z": pal["trim"]}, skip=("-z",))
            medallion(kit, front - 0.06, flank + 0.75, 1.6)
        else:
            base = flank
            peak = base + width * 0.3
            kit.box((-width * 0.36, front - 0.06, roof_z), (width * 0.36, front + 0.36, base), pal["wall"], skip=("-z", "+z"))
            kit.extrude_y([(-width * 0.36, base), (width * 0.36, base), (0, peak)], front - 0.06, front + 0.36, pal["wall"])
            for side in (-1, 1):  # the raking cornice
                kit.extrude_y(
                    [(side * (width * 0.36 + 0.2), base - 0.02), (0, peak + 0.02), (0, peak + 0.24), (side * (width * 0.36 + 0.2), base + 0.2)],
                    front - 0.18,
                    front + 0.36,
                    pal["trim"],
                )
            medallion(kit, front - 0.06, base + (peak - base) * 0.3, min(1.3, (peak - base) * 0.85))
        add(kit, "detail", "wood", 2, supports=(parapet,), collider="hull" if top_style == "pediment" else "box")

    # --- roof clutter ---
    if clutter != "none":
        cx = -sign_side * width * 0.22
        cy = depth * 0.2
        kit = Kit()
        if roof_z is None:
            # On the slope of the pitched roof.
            base = top + (rise / (width / 2)) * (width / 2 - abs(cx)) - 0.3
        else:
            base = roof_z
        if clutter == "chimney":
            kit.box((cx - 0.45, cy - 0.45, base), (cx + 0.45, cy + 0.45, base + 1.6), pal["wall"], skip=("-z", "+z"))
            kit.box((cx - 0.55, cy - 0.55, base + 1.6), (cx + 0.55, cy + 0.55, base + 1.8), pal["trim"])
            kit.box((cx - 0.17, cy - 0.17, base + 1.8), (cx + 0.17, cy + 0.17, base + 2.2), "tangerine", skip=("-z",))
        else:
            kit.box((cx - 0.6, cy - 0.5, base), (cx + 0.6, cy + 0.5, base + 0.8), "stone", skip=("-z",))
            kit.box((cx - 0.75, cy - 0.65, base + 0.8), (cx + 0.75, cy + 0.65, base + 0.95), "tyre")
        add(kit, "detail", "tin" if clutter == "vent" else "plaster", 2, supports=roof_ids)

    empty, stats = building.finish(
        look=f"{top_style}/{awning_style}-{awning_reach}x{stripes}/{picture}-{sign_shape}/{window_style}/{clutter}/door{door_side:+d}"
    )
    return empty, stats


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(15, 17))


if __name__ == "__main__":
    previews()
