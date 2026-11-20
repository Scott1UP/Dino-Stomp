"""Chicken coop generator.

A small raised hen house about 5 m wide and 3.5 m deep: a plank house on four
stout legs under a pitched roof, a nesting box with a sloping lid on one end,
and at the other a pop-hole with a ramp down into a run, drawn as an open
timber frame with rails for the wire.

The seed varies which end the run is on, the leg height, the roof pitch,
whether the planks are bare or painted in the scheme's wall colour, the
window and the run's height. The roof and lid take the scheme's roof colour.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/chicken_coop.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_farm as farm  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_fair import beam, mirror_x  # noqa: E402
from lib.shapes_parkcastle import fquad  # noqa: E402

TYPE = "chicken_coop"
HITS_TO_COLLAPSE = 1  # small and flimsy
TRIANGLE_BUDGET = 400

WALL = 0.2
HX0, HX1 = -2.0, 0.6  # the house; the nesting box is on its left and the run on its right
HY = 1.4
RUN_X = 2.5
LEG = 0.34


def build(building_id, seed, scheme=None, collection=None):
    """Build one coop. Returns (empty, stats)."""
    rng = random.Random(seed)

    flip = seed % 2 == 0  # run on the left instead; cycled, so neighbouring seeds always differ
    legs = rng.choice([0.9, 1.1, 1.3])
    rise = rng.choice([0.9, 1.1, 1.3])
    painted = rng.random() < 0.5
    window_style = rng.choice(["square", "wide"])
    run_h = rng.choice([1.5, 1.8])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]
    wall_colour = pal["wall"] if painted else "wood"
    frame_colour = "doorBrown" if not painted else "wood"

    colours = {
        "wall": wall_colour,
        "interior": "interiorCream",
        "trim": "trimWhite",
        "glass": "windowBlue",
        "shine": "windowShine",
        "door": pal["door"],
    }

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)

    def add(kit, *args, **kwargs):
        if flip:
            mirror_x(kit)
        return building.add(kit, *args, **kwargs)

    floor_z = legs + 0.2
    eaves = floor_z + 1.7
    ridge = eaves + rise
    half_window = 0.45 if window_style == "square" else 0.7

    # --- four legs and the floor they carry ---
    leg_ids = []
    for x in (HX0 + 0.05, HX1 - 0.05 - LEG):
        for y in (-HY + 0.05, HY - 0.05 - LEG):
            kit = Kit()
            kit.box((x, y, 0), (x + LEG, y + LEG, legs), frame_colour, skip=("-z", "+z"))
            leg_ids.append(add(kit, "pillar", "wood", 0))
    kit = Kit()
    kit.box((HX0 - 0.1, -HY - 0.1, legs), (HX1 + 0.1, HY + 0.1, floor_z), frame_colour, sides={"+z": "interiorCream"})
    floor = add(kit, "floor", "wood", 1, supports=leg_ids)

    # --- front and back walls, each with a window ---
    mid = (HX0 + HX1) / 2
    hole = {"x0": mid - half_window, "x1": mid + half_window, "z0": floor_z + 0.6, "z1": floor_z + 1.3, "kind": "window"}
    kit = Kit()
    kit.wall(HX0 + WALL, HX1 - WALL, floor_z, eaves, -HY, WALL, 1, [hole], colours)
    front = add(kit, "wall", "wood", 1, supports=(floor,))
    kit = Kit()
    kit.wall(HX0 + WALL, HX1 - WALL, floor_z, eaves, HY, WALL, -1, [hole], colours)
    back = add(kit, "wall", "wood", 1, supports=(floor,))

    # --- the gable ends: the right one has the pop-hole ---
    section = [(-HY, floor_z), (HY, floor_z), (HY, eaves), (0, ridge), (-HY, eaves)]
    kit = Kit()
    kit.extrude_x(section, HX0, HX0 + WALL, wall_colour, colours={1: "interiorCream"})
    left = add(kit, "wall", "wood", 1, supports=(floor,), collider="hull")
    kit = Kit()
    kit.extrude_x(section, HX1 - WALL, HX1, wall_colour, colours={0: "interiorCream"})
    right_face = farm.face("right", HX1)
    fquad(kit, right_face, -0.6, 0.6, floor_z, floor_z + 1.2, 0.02, "trimWhite")
    fquad(kit, right_face, -0.45, 0.45, floor_z, floor_z + 1.05, 0.04, "tyre")
    right = add(kit, "wall", "wood", 1, supports=(floor,), collider="hull")

    # --- the roof ---
    slope = rise / HY
    over = 0.35
    for sign, holder in ((-1, front), (1, back)):
        ye = sign * (HY + over)
        ze = eaves - over * slope
        kit = Kit()
        farm.slab(
            kit,
            [(HX0 - 0.3, ye, ze), (HX1 + 0.3, ye, ze), (HX1 + 0.3, 0, ridge), (HX0 - 0.3, 0, ridge)],
            0.2,
            pal["roof"],
            {2: "trimWhite"},
        )
        add(kit, "roof", "tile", 2, supports=(holder, left, right), collider="hull")

    # --- the nesting box, with a sloping lid ---
    kit = Kit()
    kit.extrude_y(
        [(HX0 - 0.5, floor_z + 0.15), (HX0, floor_z + 0.15), (HX0, floor_z + 1.15), (HX0 - 0.5, floor_z + 0.85)],
        -0.95,
        0.95,
        wall_colour,
        colours={4: pal["roof"]},
    )
    add(kit, "detail", "wood", 1, supports=(left,), collider="hull")

    # --- the ramp down into the run, with cleats ---
    kit = Kit()
    x_foot = HX1 + floor_z * 1.25
    beam(kit, (HX1, 0, floor_z - 0.06), (x_foot, 0, 0.02), 0.8, frame_colour, depth=0.12)
    for t in (0.25, 0.5, 0.75):
        x = HX1 + (x_foot - HX1) * t
        z = floor_z * (1 - t) + 0.06
        kit.box((x - 0.07, -0.4, z - 0.02), (x + 0.07, 0.4, z + 0.1), "trimWhite", skip=("-z",))
    add(kit, "detail", "wood", 0, supports=(floor,), collider="hull")

    # --- the run: corner posts, a top rail and a rail half-way for the wire ---
    kit = Kit()
    post = 0.2
    for y in (-HY, HY - post):
        kit.box((RUN_X - post, y, 0), (RUN_X, y + post, run_h), "trimWhite", skip=("-z",))
    for z0, z1 in ((run_h - 0.16, run_h), (run_h * 0.45, run_h * 0.45 + 0.12)):
        kit.box((HX1, -HY, z0), (RUN_X - post, -HY + 0.14, z1), "trimWhite", skip=("-x", "+x"))
        kit.box((HX1, HY - 0.14, z0), (RUN_X - post, HY, z1), "trimWhite", skip=("-x", "+x"))
        kit.box((RUN_X - 0.17, -HY + post, z0), (RUN_X - 0.03, HY - post, z1), "trimWhite", skip=("-y", "+y"))
    add(kit, "detail", "wood", 0)

    return building.finish(
        look=f"run-{'left' if flip else 'right'} legs={legs} rise={rise} {'painted' if painted else 'bare'} {window_style} run={run_h}"
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(9, 8))


if __name__ == "__main__":
    previews()
