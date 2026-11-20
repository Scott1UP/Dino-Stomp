"""Crop row generator.

ONE strip of crops on a ridge of soil, 6 m long (along X) and 1.4 m wide, in a
single module. The seed picks the crop: cabbages (leafy blobs), corn (tall
stalks with sunny cobs), pumpkins (tangerine, with leaves) or sunflowers
(facing the front), and nudges the plants' sizes and spacing.

    blender --background --factory-startup --python assets-src/props/crop_row.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import shapes_farm as farm  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import prism  # noqa: E402

TYPE = "crop_row"
KIND = "prop"
TRIANGLE_BUDGET = 150  # one module, so really 80

CROPS = ("cabbages", "corn", "pumpkins", "sunflowers")
LENGTH = 6.0
WIDTH = 1.4
SOIL = 0.22  # height of the ridge


def build(building_id, seed, scheme=None, collection=None):
    """Build one crop row. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    crop = CROPS[seed % len(CROPS)]  # cycled, so neighbouring seeds always differ
    size = rng.choice([0.9, 1.0, 1.1])
    hx, hy = LENGTH / 2, WIDTH / 2

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    # The ridge of soil: sloping sides and ends, no underside.
    low = [(-hx, -hy), (hx, -hy), (hx, hy), (-hx, hy)]
    high = [(-hx + 0.2, -hy + 0.3), (hx - 0.2, -hy + 0.3), (hx - 0.2, hy - 0.3), (-hx + 0.2, hy - 0.3)]
    for i in range(4):
        j = (i + 1) % 4
        mid = ((low[i][0] + low[j][0]) / 2, (low[i][1] + low[j][1]) / 2, 0.5)
        kit.poly([(*low[i], 0), (*low[j], 0), (*high[j], SOIL), (*high[i], SOIL)], mid, "doorBrown")
    kit.poly([(x, y, SOIL) for x, y in high], (0, 0, 1), "doorBrown")

    def spots(count, margin):
        """Plant centres along the row, kept `margin` in from each end so nothing overhangs the strip."""
        step = (LENGTH - 2 * margin) / (count - 1)
        return [-hx + margin + k * step + rng.uniform(-0.06, 0.06) for k in range(count)]

    def inward(x):
        """Which way a leaf should point from x so it stays over the strip."""
        return (1 if x < 0 else -1) if abs(x) > 1.0 else rng.choice([-1, 1])

    if crop == "cabbages":
        for x in spots(4, 0.8):
            r = 0.58 * size * rng.choice([0.92, 1.0, 1.08])
            farm.blob(kit, (x, rng.uniform(-0.05, 0.05), SOIL - 0.02), r, r * 1.15, 5, "hedge", "leaf", turn=rng.uniform(0, 1))
    elif crop == "corn":
        for x in spots(4, 0.95):
            h = 2.7 * size * rng.choice([0.9, 1.0, 1.08])
            prism(kit, (x, 0), SOIL, h, 0.2, 0.0, 4, "leaf", bottom=False)
            way = rng.choice([-1, 1])
            # A cob: two pyramids base to base.
            cz = h * 0.52
            cx = x + way * 0.3
            ring = [(cx + 0.19 * math.cos(a), 0.19 * math.sin(a), cz) for a in (0, math.pi / 2, math.pi, 3 * math.pi / 2)]
            for k in range(4):
                a, b = ring[k], ring[(k + 1) % 4]
                out = ((a[0] + b[0]) / 2 - cx, (a[1] + b[1]) / 2, 0)
                kit.poly([a, b, (cx + way * 0.12, 0, cz + 0.6)], (out[0], out[1], 0.2), "sunny")
                kit.poly([a, b, (cx - way * 0.1, 0, cz - 0.3)], (out[0], out[1], -0.2), "sunny")
            farm.leaf_blade(kit, (x, 0, h * 0.3), (x - way * 0.75, 0.0, h * 0.62), (x, 0, h * 0.55), "hedge")
            farm.leaf_blade(kit, (x, 0, h * 0.12), (x + way * 0.7, 0.0, h * 0.4), (x, 0, h * 0.34), "hedge")
    elif crop == "pumpkins":
        for x in spots(3, 0.85):
            r = 0.62 * size * rng.choice([0.85, 1.0, 1.1])
            y = rng.uniform(-0.06, 0.06)
            prism(kit, (x, y), SOIL - 0.03, SOIL + r * 0.7, r * 0.8, r, 6, "tangerine", bottom=False, top=False)
            prism(kit, (x, y), SOIL + r * 0.7, SOIL + r * 1.1, r, 0.0, 6, "tangerine", bottom=False)
            prism(kit, (x, y), SOIL + r * 1.0, SOIL + r * 1.5, 0.14, 0.0, 3, "hedge", bottom=False)
            way = inward(x)
            farm.leaf_blade(kit, (x + way * r, y - 0.3, SOIL + 0.05), (x + way * (r + 0.75), y, SOIL + 0.3), (x + way * r, y + 0.3, SOIL + 0.05), "leaf")
    else:
        for k, x in enumerate(spots(4, 0.65)):
            h = 2.4 * size * rng.choice([0.88, 1.0, 1.1])
            prism(kit, (x, 0), SOIL, h, 0.1, 0.08, 3, "hedge", bottom=False, top=False)
            r = 0.52
            head = [(x + r * math.cos(k * math.pi / 3), -0.14, h + r * math.sin(k * math.pi / 3)) for k in range(6)]
            kit.poly(head, (0, -1, 0), "sunny")
            kit.poly([(px, -0.1, pz) for px, _, pz in head], (0, 1, 0), "leaf")
            c = r * 0.5
            kit.poly([(x - c, -0.17, h), (x, -0.17, h - c), (x + c, -0.17, h), (x, -0.17, h + c)], (0, -1, 0), "doorBrown")
            if k % 2 == 0:  # a leaf on every other stem: all the one module can afford
                way = inward(x)
                farm.leaf_blade(kit, (x, 0, h * 0.35), (x + way * 0.6, 0, h * 0.58), (x, 0, h * 0.55), "leaf")
    building.add(kit, "detail", "leaves", 0, collider="hull")

    return building.finish(look=f"{crop} size={size}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 5))


if __name__ == "__main__":
    previews()
