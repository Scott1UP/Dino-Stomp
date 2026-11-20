"""Tent generator.

A bright camping tent 4-5 m across with a little flag. The seed picks the kind
(a ridge tent with striped sides, a tipi with its poles crossing at the top,
or a dome of coloured panels) and varies its size, its two colours and the
flag.

Every tent stands as a few storey-0 "wall" pieces of rubbery cloth, so one
stomp flattens it.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/tent.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import beam, flat  # noqa: E402
from lib.shapes_forest import COS8, dome, facet_normal, facet_point, pennant  # noqa: E402

TYPE = "tent"
HITS_TO_COLLAPSE = 1
TRIANGLE_BUDGET = 400

STYLES = ("ridge", "tipi", "dome")
CLOTH = 0.12


def build(building_id, seed, scheme=None, collection=None):
    """Build one tent. Returns (empty, stats)."""
    rng = random.Random(seed)

    style = STYLES[seed % len(STYLES)]  # cycled, so neighbouring seeds differ
    size = rng.choice([0.9, 1.0, 1.1])
    partner = rng.choice(["trim", "trim", "roof"])
    flag_way = rng.choice([-1, 1])
    stripes = rng.choice([3, 4])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    main, second = pal["wall"], pal[partner]
    flag_colour = pal["door"] if pal["door"] != "doorBrown" else pal["roof"]
    dark = "windowBlue"

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    if style == "ridge":
        half, length, height = 2.2 * size, 4.6 * size, 2.7 * size
        y0, y1 = -length / 2, length / 2
        walls = []
        for sign in (-1, 1):
            kit = Kit()
            step = length / stripes
            for n in range(stripes):
                ya, yb = y0 + n * step, y0 + (n + 1) * step
                bottom = [(sign * half, ya, 0), (sign * half, yb, 0), (0, yb, height), (0, ya, height)]
                colour = main if n % 2 == 0 else second
                kit.poly(bottom, (-sign, 0, -1), "interiorCream")
                kit.poly([(x + sign * CLOTH, y, z + CLOTH * 0.6) for x, y, z in bottom], (sign, 0, 1), colour)
            for y, facing in ((y0, -1), (y1, 1)):  # the cloth's cut edges
                kit.poly([(sign * half, y, 0), (sign * (half + CLOTH), y, CLOTH * 0.6), (sign * CLOTH, y, height + CLOTH * 0.6), (0, y, height)], (0, facing, 0), main)
            walls.append(add(kit, "wall", "rubber", 0, collider="hull"))

        # The ends: the front with its flaps tied back, the back with a window.
        for y, facing in ((y0 + 0.25, -1), (y1 - 0.25, 1)):
            kit = Kit()
            lo, hi = sorted((y, y - facing * 0.08))
            inset = 0.9
            kit.extrude_y([(-half * inset, 0), (half * inset, 0), (0, height * inset)], lo, hi, second, colours={0: second, 1: second})
            if facing < 0:
                flat(kit, (0, y, 0), (0, -1, 0), [(-half * 0.42, 0), (half * 0.42, 0), (0, height * 0.62)], dark, lift=0.03)
            else:
                flat(kit, (0, y, height * 0.3), (0, 1, 0), [(-0.45, 0), (0.45, 0), (0.45, 0.7), (-0.45, 0.7)], dark, lift=0.03)
                flat(kit, (0, y, height * 0.3), (0, 1, 0), [(-0.25, 0.3), (-0.12, 0.3), (0.2, 0.62), (0.07, 0.62)], "windowShine", lift=0.06)
            walls.append(add(kit, "wall", "rubber", 0, collider="hull"))

        kit = Kit()
        beam(kit, (0, y0 - 0.1, height + 0.12), (0, y1 + 0.1, height + 0.12), 0.16, "wood")
        pennant(kit, 0, y0 + 0.1, height, 1.5, "wood", flag_colour, facing=flag_way)
        add(kit, "detail", "wood", 1, supports=walls[:2], collider="box")
        look = f"{length:g}x{half * 2:g} stripes{stripes}"

    elif style == "tipi":
        radius, height = 2.5 * size, 4.0 * size
        tip = 0.28
        lean = (radius - tip) * COS8 / height
        walls = []
        for q in range(4):
            kit = Kit()
            dome(kit, 0, 0, [(0, radius), (height, tip)], main, facets=(q * 2, q * 2 + 1), cut="interiorCream", stripes=[main, second], top=False)
            if q == 2:  # the doorway, on the front facet
                flat(kit, facet_point(5, radius, 0), facet_normal(5, lean), [(-0.62, 0), (0.62, 0), (0.22, 2.0 * size), (-0.22, 2.0 * size)], dark, lift=0.03)
            walls.append(add(kit, "wall", "rubber", 0, collider="hull"))
        kit = Kit()
        for n in range(3):  # the poles, crossing where they poke out of the top
            a = n * math.tau / 3 + 0.5
            d = (math.cos(a) * 0.5, math.sin(a) * 0.5)
            beam(kit, (d[0], d[1], height - 0.9), (-d[0] * 1.3, -d[1] * 1.3, height + 1.0), 0.13, "doorBrown", caps=False)
        pennant(kit, 0, 0, height - 0.2, 2.0, "doorBrown", flag_colour, facing=flag_way)
        add(kit, "detail", "wood", 1, supports=walls, collider="box")
        look = f"r{radius:g} h{height:g}"

    else:  # dome
        radius, height = 2.4 * size, 2.5 * size
        profile = [(0, radius * 0.97), (height * 0.3, radius), (height * 0.68, radius * 0.72), (height * 0.92, radius * 0.34), (height, 0)]
        walls = []
        for q in range(4):
            kit = Kit()
            dome(kit, 0, 0, profile, main, facets=(q * 2, q * 2 + 1), cut="interiorCream", stripes=[main, second])
            if q == 2:
                lean = -0.03 * radius * COS8 / (height * 0.3)
                arch = [(-0.6, 0), (0.6, 0), (0.6, 0.8 * size), (0.3, 1.25 * size), (-0.3, 1.25 * size), (-0.6, 0.8 * size)]
                flat(kit, facet_point(5, radius, 0.03), facet_normal(5, lean), arch, dark, lift=0.1)
            walls.append(add(kit, "wall", "rubber", 0, collider="hull"))
        kit = Kit()
        kit.box((-0.22, -0.22, height - 0.12), (0.22, 0.22, height + 0.2), second)
        pennant(kit, 0, 0, height + 0.2, 1.5, "wood", flag_colour, facing=flag_way)
        add(kit, "detail", "wood", 1, supports=walls, collider="box")
        look = f"r{radius:g} h{height:g}"

    return building.finish(look=f"{style}/{look}/{main}+{second}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(9, 9))


if __name__ == "__main__":
    previews()
