"""Swing set generator.

An A-frame swing set about 7 m wide and 4 m tall: two splayed pairs of legs,
a top bar, and two or three swings hanging on thick chains, each caught at a
different point of its swing. The seed varies the number of swings, their
kind (plank, bucket seat or tyre), how far each has swung, and the colours.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/swings.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_fair as fair  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import BRIGHT, prism  # noqa: E402

TYPE = "swings"
HITS_TO_COLLAPSE = 1  # small building
TRIANGLE_BUDGET = 400

LEG = 0.36
CHAIN = 0.2
KINDS = ("plank", "bucket", "tyre")


def build(building_id, seed, scheme=None, collection=None):
    """Build one swing set. Returns (empty, stats)."""
    rng = random.Random(seed)

    count = rng.choice([2, 3, 3])
    top = rng.choice([3.5, 3.8, 4.1])
    half = rng.choice([3.1, 3.4])
    splay = rng.choice([1.6, 1.9])
    kinds = [rng.choice(KINDS) for _ in range(3)]
    angles = [rng.choice([-32, -18, 0, 15, 30]) for _ in range(3)]
    first = rng.randrange(len(BRIGHT))
    brace = rng.random() < 0.6
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add
    frame_colour = pal["wall"]

    # --- legs: an A at each end ---
    legs = []
    for sx in (-1, 1):
        pair = []
        for sy in (-1, 1):
            kit = Kit()
            fair.beam(kit, (sx * half, sy * splay, 0), (sx * (half - 0.15), 0, top + 0.1), LEG, frame_colour, flat=True)
            pair.append(add(kit, "pillar", "tin", 0, collider="hull"))
        if brace:
            z = top * 0.42
            y = splay * (1 - 0.42)
            kit = Kit()
            kit.box((sx * half - 0.14, -y, z - 0.14), (sx * half + 0.14, y, z + 0.14), pal["trim"], skip=("-y", "+y"))
            add(kit, "detail", "tin", 0, supports=pair)
        legs.extend(pair)

    # --- the top bar ---
    kit = Kit()
    kit.box((-half - 0.3, -0.2, top - 0.2), (half + 0.3, 0.2, top + 0.2), pal["roof"])
    bar = add(kit, "band", "tin", 1, supports=legs)

    # --- the swings ---
    room = 2 * half - 1.6
    for n in range(count):
        x = -room / 2 + (n + 0.5) * room / count
        kind = kinds[n]
        colour = BRIGHT[(first + n * 2) % len(BRIGHT)]
        lean = math.radians(angles[n])
        length = top - (1.0 if kind == "tyre" else 0.75)
        down = (0.0, math.sin(lean), -math.cos(lean))  # along the chains
        pivot_z = top - 0.15

        def hang(dx, far):
            return (x + dx, down[1] * far, pivot_z + down[2] * far)

        kit = Kit()
        if kind == "tyre":
            fair.beam(kit, hang(0, 0), hang(0, length - 0.1), CHAIN + 0.05, "trimWhite", caps=False)
            prism(kit, (x, 0), -0.22, 0.22, 0.75, 0.75, 6, "tyre")
            # Move the tyre from the origin to the end of the chain, tilted with it.
            for points, _ in kit.faces[-8:]:
                for p in points:
                    y, z = p.y, p.z
                    p.y = y * math.cos(lean) + z * math.sin(lean) + down[1] * length
                    p.z = -y * math.sin(lean) + z * math.cos(lean) + pivot_z + down[2] * length
        else:
            for dx in (-0.5, 0.5):
                fair.beam(kit, hang(dx, 0), hang(dx, length), CHAIN, "trimWhite", caps=False)
            fair.beam(kit, hang(-0.65, length), hang(0.65, length), 0.6, colour, depth=0.2, up=down)
            if kind == "bucket":
                back = (0.0, math.cos(lean) * 0.3, math.sin(lean) * 0.3)  # behind the seat
                a = hang(-0.65, length - 0.45)
                b = hang(0.65, length - 0.45)
                fair.beam(
                    kit,
                    tuple(a[k] + back[k] for k in range(3)),
                    tuple(b[k] + back[k] for k in range(3)),
                    0.2,
                    colour,
                    depth=0.9,
                    up=down,
                )
        add(kit, "detail", "tin", 1, supports=(bar,), collider="hull")

    return building.finish(
        look=f"swings={count} {'/'.join(kinds[:count])} angles={angles[:count]} top={top} half={half}"
        + ("/brace" if brace else "")
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(12, 10))


if __name__ == "__main__":
    previews()
