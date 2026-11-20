"""Water trough generator.

A wooden trough full of water, about 3 m long, with a hand pump at one end.
Two modules: the trough, and the pump standing beside it. The seed varies the
trough's length and timber, whether it stands on feet or is a tapered tub,
which end the pump is at and the pump's colour.

    blender --background --factory-startup --python assets-src/props/water_trough.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_fair import beam  # noqa: E402
from lib.shapes_props import panel_z, prism  # noqa: E402

TYPE = "water_trough"
KIND = "prop"
TRIANGLE_BUDGET = 150

STYLES = ("feet", "tub")
PUMPS = ("tomato", "cobalt", "leaf", "tangerine")


def build(building_id, seed, scheme=None, collection=None):
    """Build one trough and pump. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    style = STYLES[seed % len(STYLES)]  # cycled, so neighbouring seeds always differ
    end = 1 if (seed // 2) % 2 else -1
    pump = PUMPS[seed % len(PUMPS)]
    length = rng.choice([2.6, 3.0, 3.3])
    timber = rng.choice(["wood", "doorBrown"])
    band = "doorBrown" if timber == "wood" else "wood"

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    hx, hy = length / 2, 0.6
    rim = 0.16
    kit = Kit()
    if style == "feet":
        z0, z1 = 0.3, 1.05
        kit.box((-hx, -hy, z0), (hx, hy, z1), timber, skip=("+z",))
        for x in (-hx + 0.3, hx - 0.6):
            kit.box((x, -hy - 0.12, 0), (x + 0.3, hy + 0.12, z0), band, skip=("-z",))
    else:
        z0, z1 = 0.0, 1.0
        kit.extrude_x([(-hy + 0.2, z0), (hy - 0.2, z0), (hy, z1), (-hy, z1)], -hx, hx, timber)
        del kit.faces[-2]  # the top face; the rim and the water go there instead
        for x in (-hx - 0.03, hx + 0.03 - 0.2):
            kit.box((x, -hy - 0.05, z1 - 0.3), (x + 0.2, hy + 0.05, z1 - 0.12), band, skip=("-z",))
    # The rim, and the water inside it.
    panel_z(kit, -hx, hx, -hy, -hy + rim, z1, 1, timber)
    panel_z(kit, -hx, hx, hy - rim, hy, z1, 1, timber)
    panel_z(kit, -hx, -hx + rim, -hy + rim, hy - rim, z1, 1, timber)
    panel_z(kit, hx - rim, hx, -hy + rim, hy - rim, z1, 1, timber)
    panel_z(kit, -hx + rim, hx - rim, -hy + rim, hy - rim, z1 - 0.1, 1, "water")
    panel_z(kit, -end * hx * 0.2 - 0.45, -end * hx * 0.2 + 0.45, -0.12, 0.2, z1 - 0.08, 1, "foam")
    building.add(kit, "detail", "wood", 0, collider="hull" if style == "tub" else "box")

    # The hand pump, with its spout over the water.
    px = end * (hx + 0.55)
    kit = Kit()
    kit.box((px - 0.4, -0.4, 0), (px + 0.4, 0.4, 0.22), "stone", skip=("-z",))
    prism(kit, (px, 0), 0.22, 1.9, 0.26, 0.22, 6, pump, bottom=False)
    prism(kit, (px, 0), 1.9, 2.15, 0.34, 0.2, 6, pump, bottom=False)
    kit.box(*sorted_box((px, -0.13, 1.35), (px - end * 0.75, 0.13, 1.6)), pump)
    beam(kit, (px, 0, 1.95), (px + end * 0.85, 0, 1.2), 0.14, "tyre")
    building.add(kit, "detail", "tin", 0, collider="hull")

    return building.finish(look=f"{style} length={length} {timber} pump={pump} end{end:+d}")


def sorted_box(a, b):
    """Two opposite corners, as (lo, hi)."""
    return tuple(min(p, q) for p, q in zip(a, b)), tuple(max(p, q) for p, q in zip(a, b))


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(7, 5))


if __name__ == "__main__":
    previews()
