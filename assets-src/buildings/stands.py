"""Stands generator: a tall spectator tower beside the sports pitch.

A tall wooden tower about 6 m by 4 m and 10 m tall: four timber legs carry a
viewing box wrapped in bright striped cloth, under a pointed striped canopy
with a pennant. Below the box the legs are either braced open scaffolding or
wrapped in more striped cloth down to the ground, like a tall tent.

The four legs are the storey-0 pillars. The braces (or the lower cloth) hang
on the legs, the box's floor rests on all four, the cloth walls and their
corner posts rest on the floor, and the canopy rests on the cloth walls.

The seed varies the stripe colours, the platform height, the canopy (a
four-sided pyramid or an eight-sided cone), open or wrapped legs, and the
pennant.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/stands.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_fair as fair  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib import shapes_wizard as wiz  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_parkcastle import Frame  # noqa: E402

TYPE = "stands"
HITS_TO_COLLAPSE = 1  # light structure
TRIANGLE_BUDGET = 400

HX, HY = 3.0, 2.0  # 6 m by 4 m
LEG = 0.2  # half the leg's thickness
STRIPES = [
    ("tomato", "sunny"),
    ("cobalt", "sunny"),
    ("bubblegum", "trimWhite"),
    ("tangerine", "cobalt"),
    ("tomato", "trimWhite"),
    ("cobalt", "trimWhite"),
]


def build(building_id, seed, scheme=None, collection=None):
    """Build one spectator stand. Returns (empty, stats)."""
    rng = random.Random(seed)

    colours = list(STRIPES[(seed + rng.choice([0, 0, 3])) % len(STRIPES)])  # mostly cycled, so neighbours differ
    platform = rng.choice([5.0, 5.4, 5.8])
    canopy = rng.choice(["pyramid", "cone"])
    lower = ("open", "wrapped")[seed % 2]
    rise = rng.choice([2.0, 2.5])
    timber = rng.choice(["wood", "doorBrown"])
    pennant = rng.choice(["tomato", "cobalt", "sunny", "bubblegum"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    box_top = platform + 1.15  # the cloth wall round the box
    eave = box_top + 1.4  # the canopy sits on the corner posts
    frames = {
        "front": Frame((0, -HY, 0), -90),
        "back": Frame((0, HY, 0), 90),
        "left": Frame((-HX, 0, 0), 180),
        "right": Frame((HX, 0, 0), 0),
    }

    # --- the four legs ---
    legs = {}
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (HX - LEG), sy * (HY - LEG)
            kit = Kit()
            kit.box((x - LEG, y - LEG, 0), (x + LEG, y + LEG, platform), timber, skip=("-z",))
            legs[(sx, sy)] = add(kit, "pillar", "wood", 0)

    def legs_of(name):
        return {
            "front": (legs[(-1, -1)], legs[(1, -1)]),
            "back": (legs[(-1, 1)], legs[(1, 1)]),
            "left": (legs[(-1, -1)], legs[(-1, 1)]),
            "right": (legs[(1, -1)], legs[(1, 1)]),
        }[name]

    # --- below the box: cross braces, or striped cloth to the ground ---
    if lower == "open":
        for name in ("front", "back", "left", "right"):
            frame = frames[name]
            half = (HX if name in ("front", "back") else HY) - LEG
            kit = Kit()
            a = frame.at(-half, -LEG, 0.3)
            b = frame.at(half, -LEG, platform * 0.5)
            c = frame.at(-half, -LEG, platform * 0.5)
            d = frame.at(half, -LEG, platform - 0.2)
            fair.beam(kit, a, b, 0.22, timber, caps=False)
            fair.beam(kit, c, d, 0.22, timber, caps=False)
            add(kit, "detail", "wood", 0, supports=legs_of(name))
    else:
        for names in (("front", "left"), ("back", "right")):
            kit = Kit()
            for name in names:
                half = (HX if name in ("front", "back") else HY) - LEG
                count = 6 if name in ("front", "back") else 4
                wiz.stripes(kit, frames[name], -half, half, 1.2, platform - 0.1, -0.02, colours, count, point=0.35)
            add(kit, "detail", "wood", 0, supports=legs_of(names[0]) + legs_of(names[1]))

    # --- the box's floor ---
    kit = Kit()
    kit.box((-HX - 0.15, -HY - 0.15, platform), (HX + 0.15, HY + 0.15, platform + 0.25), timber, sides={"+z": "interiorCream"})
    floor = add(kit, "floor", "wood", 1, supports=list(legs.values()))

    # --- striped cloth round the box, and the corner posts that carry the canopy ---
    walls = []
    for names, corners in ((("front", "left"), ((-1, -1), (1, -1))), (("back", "right"), ((1, 1), (-1, 1)))):
        kit = Kit()
        for name in names:
            half = (HX if name in ("front", "back") else HY) - LEG
            count = 6 if name in ("front", "back") else 4
            wiz.stripes(kit, frames[name], -half, half, platform + 0.25, box_top, 0.1, colours, count)
            shapes.fquad(kit, frames[name], -half, half, box_top - 0.18, box_top, 0.13, "trimWhite")
        for sx, sy in corners:
            x, y = sx * (HX - LEG), sy * (HY - LEG)
            kit.box((x - 0.15, y - 0.15, platform + 0.25), (x + 0.15, y + 0.15, eave), timber, skip=("-z", "+z"))
        walls.append(add(kit, "wall", "wood", 1, supports=(floor,)))

    # --- the pointed striped canopy and its pennant ---
    kit = Kit()
    if canopy == "pyramid":
        r = (HX + 0.4, HY + 0.4)
        base = [(-r[0], -r[1], eave), (r[0], -r[1], eave), (r[0], r[1], eave), (-r[0], r[1], eave)]
        apex = (0, 0, eave + rise + 0.6)
        faces = [base] + [[base[k], base[(k + 1) % 4], apex] for k in range(4)]
        kit.convex(faces, colours[0], {1: colours[0], 2: colours[1], 3: colours[0], 4: colours[1], 0: "trimWhite"})
        tip = apex[2]
    else:
        lower_ring = shapes.ring(HX + 0.5, eave, 8)
        apex = (0, 0, eave + rise + 1.0)
        faces = [lower_ring] + [[lower_ring[k], lower_ring[(k + 1) % 8], apex] for k in range(8)]
        cols = {0: "trimWhite"}
        for k in range(8):
            cols[k + 1] = colours[k % 2]
        kit.convex(faces, colours[0], cols)
        tip = apex[2]
    shapes.flag(kit, 0, 0, tip - 0.3, 1.9, pennant, size=1.3, thick=0.07)
    add(kit, "roof", "wood", 2, supports=walls, collider="hull")

    return building.finish(look=f"{colours[0]}/{colours[1]} platform{platform} {canopy} rise{rise} {lower} {timber} apex{tip:.1f}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(11, 0), columns=6)


if __name__ == "__main__":
    previews()
