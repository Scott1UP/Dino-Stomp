"""Carousel generator.

A fairground roundabout about 5 m in radius: a round wooden platform, a fat
striped centre column, a striped canopy with a valance, and six or eight
chunky horses on poles, bobbing at different heights. The seed varies the
size, the number of horses and their colours, the canopy (a plain cone or a
two-slope tent), its stripes and the finial.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/carousel.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_fair as fair  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import BRIGHT  # noqa: E402

TYPE = "carousel"
HITS_TO_COLLAPSE = 2  # medium building
TRIANGLE_BUDGET = 900

PLAT = 0.5
POLE = 0.16  # half-thickness of a horse's pole


def _horse(kit, frame, lift, colour, mane, saddle, s=1.15):
    """A chunky horse in a frame: u is forwards, v is sideways, z is up from the platform."""
    h = lift

    def box(lo, hi, shade, skip=()):
        shapes.fbox(kit, frame, (lo[0] * s, lo[1] * s, h + lo[2] * s), (hi[0] * s, hi[1] * s, h + hi[2] * s), shade, skip=skip)

    def profile(section, half, shade, colours=None):
        fair.fextrude(kit, frame, [(u * s, h + z * s) for u, z in section], -half * s, half * s, shade, colours)

    box((-0.85, -0.32, 0), (0.7, 0.32, 0.75), colour)
    # Neck and head in one leaning wedge.
    profile([(0.15, 0.6), (0.7, 0.6), (1.45, 1.2), (1.35, 1.6), (0.75, 1.75)], 0.22, colour, {6: mane})
    box((0.3, -0.28, -0.65), (0.65, 0.28, 0), colour, skip=("+z",))
    box((-0.8, -0.28, -0.65), (-0.45, 0.28, 0), colour, skip=("+z",))
    profile([(-0.85, 0.7), (-0.85, 0.3), (-1.35, 0.1)], 0.12, mane)
    box((-0.4, -0.36, 0.45), (0.15, 0.36, 0.85), saddle, skip=("-z", "-u", "+u"))


def build(building_id, seed, scheme=None, collection=None):
    """Build one carousel. Returns (empty, stats)."""
    rng = random.Random(seed)

    radius = rng.choice([4.6, 5.0, 5.4])
    count = rng.choice([6, 8, 8])
    post_h = rng.choice([4.6, 5.0, 5.4])
    canopy = rng.choice(["cone", "tent", "tent"])
    rise = rng.choice([2.2, 2.8, 3.4])
    finial = rng.choice(["ball", "flag", "ball"])
    horse_colours = rng.choice(["white", "bright", "mixed"])
    first = rng.randrange(len(BRIGHT))
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add
    stripes = [pal["roof"], pal["trim"]]
    accent = pal["door"] if pal["door"] != "doorBrown" else "sunny"

    # --- platform: four quarters ---
    quarters = []
    for q in range(4):
        kit = Kit()
        shapes.wedge(kit, 2 * q, 2, radius, radius, 0, PLAT, "wood", stripes=[pal["wall"], pal["trim"]])
        quarters.append(add(kit, "wall", "wood", 0, collider="hull"))

    def quarter_under(deg):
        return quarters[int(((deg - shapes.corner_deg(0)) % 360.0) // 90.0)]

    # --- centre column, on a drum ---
    eave_z = PLAT + post_h
    kit = Kit()
    shapes.frustum(kit, 1.5, 1.3, PLAT, PLAT + 0.9, accent, bottom=False)
    shapes.frustum(kit, 0.95, 0.95, PLAT + 0.9, eave_z + 0.2, pal["wall"], stripes=[pal["wall"], pal["trim"]], bottom=False, top=False)
    column = add(kit, "pillar", "wood", 0, supports=quarters, collider="hull")

    # --- horses on poles ---
    ride_r = radius - 1.0
    for m in range(count):
        deg = -90.0 + (m + 0.5) * 360.0 / count
        frame = shapes.Frame(shapes.polar(ride_r, deg, PLAT), deg)
        if horse_colours == "white":
            colour, mane = "trimWhite", BRIGHT[(first + m) % len(BRIGHT)]
        elif horse_colours == "bright":
            colour, mane = BRIGHT[(first + m) % len(BRIGHT)], "trimWhite"
        else:
            colour, mane = (("trimWhite", pal["roof"]), (accent, "trimWhite"))[m % 2]
        saddle = BRIGHT[(first + m + 2) % len(BRIGHT)]
        if saddle == colour:
            saddle = "tyre"
        kit = Kit()
        shapes.fbox(kit, frame, (-POLE, -POLE, 0), (POLE, POLE, post_h), "sunny" if colour != "sunny" else "trimWhite", skip=("-z", "+z"))
        _horse(kit, frame, 0.85 if m % 2 == 0 else 1.5, colour, mane, saddle)
        add(kit, "detail", "wood", 0, supports=(quarter_under(deg),), collider="hull")

    # --- canopy: four quarters, each with its stretch of valance ---
    eave_r = radius - 0.7
    if canopy == "cone":
        low_r1, low_z1 = 0.0, eave_z + rise
    else:
        low_r1, low_z1 = eave_r * 0.55, eave_z + rise * 0.35
    roof_quarters = []
    for q in range(4):
        kit = Kit()
        shapes.wedge(kit, 2 * q, 2, eave_r, low_r1, eave_z, low_z1, pal["roof"], stripes=stripes, under="interiorCream")
        for i in (2 * q, 2 * q + 1):
            shapes.wall_segment(
                kit, i, eave_r + 0.05, eave_r - 0.25, eave_z - 0.7, eave_z, pal["trim"] if i % 2 == 0 else pal["roof"]
            )
        roof_quarters.append(add(kit, "roof", "tin", 1, supports=(column,), collider="hull"))

    # --- crown and finial ---
    kit = Kit()
    if canopy == "tent":
        top_z = eave_z + rise
        shapes.frustum(kit, low_r1, 0, low_z1, top_z, pal["roof"], stripes=stripes[::-1])
    else:
        top_z = low_z1
    if finial == "ball":
        kit.box((-0.15, -0.15, top_z - 0.4), (0.15, 0.15, top_z + 0.4), pal["trim"], skip=("-z", "+z"))
        shapes.ball(kit, 0, 0, top_z + 0.85, 0.6, accent)
    else:
        shapes.flag(kit, 0, 0, top_z - 0.4, 2.1, accent, size=1.4, thick=0.15)
    add(kit, "detail", "tin", 2, supports=roof_quarters, collider="hull")

    return building.finish(look=f"r={radius} horses={count}/{horse_colours} posts={post_h} {canopy}/rise-{rise}/{finial}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(18, 20))


if __name__ == "__main__":
    previews()
