"""Phone box generator.

A tomato phone box: one frame module (base, four corner posts, a roof with
white sign bands and a crown) and four glass panel modules that pop out of it.
The seed varies its proportions and crown.

    blender --background --factory-startup --python assets-src/props/phone_box.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import panel_x, panel_y, prism  # noqa: E402

TYPE = "phone_box"
KIND = "prop"
TRIANGLE_BUDGET = 150

POST = 0.26
BASE = 0.18
GLASS = 0.1


def build(building_id, seed, scheme=None, collection=None):
    """Build one phone box. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    half = rng.choice([0.75, 0.8, 0.85])  # half the width and depth
    height = rng.choice([3.0, 3.2, 3.4])
    crown = rng.choice(["dome", "dome", "step"])
    glass = rng.choice(["glassTint", "glassTint", "windowBlue"])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    roof_z = height - 0.7
    kit = Kit()
    kit.box((-half, -half, 0), (half, half, BASE), "tomato")
    for sx in (-1, 1):
        for sy in (-1, 1):
            x0, x1 = sorted((sx * half, sx * (half - POST)))
            y0, y1 = sorted((sy * half, sy * (half - POST)))
            kit.box((x0, y0, BASE), (x1, y1, roof_z), "tomato", skip=("-z", "+z"))
    kit.box((-half - 0.06, -half - 0.06, roof_z), (half + 0.06, half + 0.06, roof_z + 0.45), "tomato")
    out = half + 0.09
    for facing in (-1, 1):
        panel_y(kit, -half + 0.12, half - 0.12, roof_z + 0.1, roof_z + 0.35, facing * out, facing, "trimWhite")
        panel_x(kit, -half + 0.12, half - 0.12, roof_z + 0.1, roof_z + 0.35, facing * out, facing, "trimWhite")
    corner = (half + 0.06) * math.sqrt(2)  # a four-sided prism is measured to its corners
    if crown == "dome":
        prism(kit, (0, 0), roof_z + 0.45, height, corner, corner * 0.45, 4, "tomato", bottom=False)
    else:
        prism(kit, (0, 0), roof_z + 0.45, height, corner * 0.7, corner * 0.7, 4, "tomato", bottom=False)
    frame = building.add(kit, "detail", "tin", 0)

    # Glass panels fill the gaps between the posts, with two glazing bars on the outside.
    inner = half - POST
    mid = half - POST / 2
    bars = [BASE + (roof_z - BASE) * f for f in (1 / 3, 2 / 3)]
    for facing in (-1, 1):
        kit = Kit()
        y = facing * mid
        kit.box((-inner, y - GLASS / 2, BASE), (inner, y + GLASS / 2, roof_z), glass)
        for z in bars:
            panel_y(kit, -inner, inner, z - 0.07, z + 0.07, y + facing * (GLASS / 2 + 0.02), facing, "tomato")
        building.add(kit, "detail", "glass", 0, supports=(frame,))

        kit = Kit()
        x = facing * mid
        kit.box((x - GLASS / 2, -inner, BASE), (x + GLASS / 2, inner, roof_z), glass)
        for z in bars:
            panel_x(kit, -inner, inner, z - 0.07, z + 0.07, x + facing * (GLASS / 2 + 0.02), facing, "tomato")
        building.add(kit, "detail", "glass", 0, supports=(frame,))

    return building.finish(look=f"w={half * 2} h={height} {crown} {glass}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 8))


if __name__ == "__main__":
    previews()
