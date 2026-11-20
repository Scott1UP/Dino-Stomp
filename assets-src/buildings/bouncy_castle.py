"""Bouncy castle generator.

An inflatable castle about 8 x 7 m: a fat base in two halves, four chunky
corner towers with pointed tops, low puffy walls round three sides, an arch
over the open front and a ramp to climb in. Everything is rubber. The seed
varies the colours, the towers (round or square, their height and tops), the
back wall's battlements and the front arch.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/bouncy_castle.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import BRIGHT, ball, prism  # noqa: E402

TYPE = "bouncy_castle"
HITS_TO_COLLAPSE = 1  # small building
TRIANGLE_BUDGET = 400

HALF_X = 4.0
HALF_Y = 3.1
BASE = 1.0
TOWER_X = 2.85
TOWER_Y = 2.0
TOWER_R = 1.0


def _puffy(z0, z1, half):
    """A fat, round-shouldered wall profile: (across, z) points."""
    soft = min(0.25, half * 0.6)
    return [(-half, z0), (half, z0), (half, z1 - soft), (half - soft, z1), (-half + soft, z1), (-half, z1 - soft)]


def build(building_id, seed, scheme=None, collection=None):
    """Build one bouncy castle. Returns (empty, stats)."""
    rng = random.Random(seed)

    colours = rng.sample(BRIGHT, 4)  # base, walls, towers, tops
    tower_sides = rng.choice([6, 6, 4])
    tower_h = rng.choice([2.6, 3.0, 3.4])
    tops = rng.choice(["cone", "cone", "ball"])
    merlons = rng.choice([0, 2, 3])
    arch = rng.random() < 0.65
    two_tone = rng.random() < 0.5
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add
    base_colour, wall_colour, tower_colour, top_colour = colours

    # --- the base: two fat halves, with a pale bouncing surface ---
    halves = {}
    for sx in (-1, 1):
        section = [
            (sx * HALF_X, 0.25),
            (sx * (HALF_X - 0.25), 0.0),
            (0.0, 0.0),
            (0.0, BASE),
            (sx * (HALF_X - 0.25), BASE),
            (sx * HALF_X, BASE - 0.25),
        ]
        kit = Kit()
        kit.extrude_y(section, -HALF_Y, HALF_Y, base_colour, {5: "trimWhite"})
        halves[sx] = add(kit, "wall", "rubber", 0, collider="hull")

    # --- four corner towers, each with a separate top ---
    tower_top = BASE + tower_h
    radius = TOWER_R * (1.25 if tower_sides == 4 else 1.0)
    for n, (sx, sy) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        x, y = sx * TOWER_X, sy * TOWER_Y
        shade = tower_colour if not two_tone or n % 2 == 0 else wall_colour
        kit = Kit()
        prism(kit, (x, y), 0.3, tower_top, radius, radius, tower_sides, shade, bottom=False, top=False)
        prism(kit, (x, y), tower_top - 0.45, tower_top, radius + 0.2, radius + 0.2, tower_sides, "trimWhite")
        tower = add(kit, "wall", "rubber", 0, supports=(halves[sx],), collider="hull")

        kit = Kit()
        if tops == "cone":
            prism(kit, (x, y), tower_top, tower_top + 1.6, radius + 0.1, 0.0, tower_sides, top_colour)
        else:
            ball(kit, (x, y, tower_top + 0.75), 0.95, 6, 3, top_colour)
        add(kit, "roof", "rubber", 1, supports=(tower,), collider="hull")

    # --- puffy walls: the back, and the two sides ---
    back_h = BASE + 1.9
    kit = Kit()
    kit.extrude_x([(y + TOWER_Y, z) for y, z in _puffy(BASE, back_h, 0.4)], -TOWER_X + 0.6, TOWER_X - 0.6, wall_colour)
    for m in range(merlons):
        x = (m - (merlons - 1) / 2) * (4.2 / merlons)
        kit.box((x - 0.45, TOWER_Y - 0.35, back_h), (x + 0.45, TOWER_Y + 0.35, back_h + 0.6), top_colour, skip=("-z",))
    add(kit, "detail", "rubber", 0, supports=(halves[-1], halves[1]), collider="hull")

    for sx in (-1, 1):
        kit = Kit()
        kit.extrude_y([(x + sx * TOWER_X, z) for x, z in _puffy(BASE, BASE + 1.2, 0.35)], -TOWER_Y + 0.6, TOWER_Y - 0.6, wall_colour)
        add(kit, "detail", "rubber", 0, supports=(halves[sx],), collider="hull")

    # --- the arch over the way in ---
    if arch:
        z = BASE + tower_h * 0.62
        kit = Kit()
        kit.extrude_x([(y - TOWER_Y, zz) for y, zz in _puffy(z, z + 0.8, 0.35)], -TOWER_X + 0.6, TOWER_X - 0.6, top_colour)
        kit.poly(
            [(-1.2, -TOWER_Y - 0.37, z + 0.2), (1.2, -TOWER_Y - 0.37, z + 0.2), (1.2, -TOWER_Y - 0.37, z + 0.6), (-1.2, -TOWER_Y - 0.37, z + 0.6)],
            (0, -1, 0),
            "trimWhite",
        )
        add(kit, "detail", "rubber", 1, supports=(halves[-1], halves[1]), collider="hull")

    # --- the ramp at the front ---
    kit = Kit()
    kit.extrude_x([(-HALF_Y, 0.0), (-HALF_Y, BASE * 0.8), (-HALF_Y - 1.1, 0.25), (-HALF_Y - 1.1, 0.0)], -1.6, 1.6, wall_colour)
    add(kit, "detail", "rubber", 0, collider="hull")

    return building.finish(
        look=f"{'/'.join(colours)} towers-{tower_sides}x{tower_h}/{tops}/merlons-{merlons}"
        + ("/arch" if arch else "")
        + ("/two-tone" if two_tone else "")
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(13, 13))


if __name__ == "__main__":
    previews()
