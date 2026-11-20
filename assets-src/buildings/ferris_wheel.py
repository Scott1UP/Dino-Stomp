"""Ferris wheel generator.

A big fairground wheel, about 18 m tall: four splayed legs in two A-frames, a
fat hub, a double rim of sixteen faceted segments on eight pairs of spokes,
and eight bright gondolas hanging from the rim. The wheel faces the front
(-Y). The seed varies the wheel's size, how it has stopped (a gondola at the
very bottom, or two either side), an inner ring, the gondola style and
colours, and the braces on the legs.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/ferris_wheel.py
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
from lib.shapes_props import BRIGHT, panel_y, prism  # noqa: E402

TYPE = "ferris_wheel"
HITS_TO_COLLAPSE = 3  # landmark
TRIANGLE_BUDGET = 1800

RIM_Y = 1.0  # the two rims stand this far either side of the middle
RIM = 0.45  # thickness of a rim bar
SPOKE = 0.35
LEG = 0.6
LEG_Y = 1.8  # where the legs meet the hub
HANG = 3.0  # a gondola hangs this far below its pivot
SEGMENTS = 16


def _gondola(kit, x, z, style, colour, trim):
    """A gondola hanging from the pivot at (x, z)."""
    kit.box((x - 0.17, -0.17, z - 0.7), (x + 0.17, 0.17, z), trim, skip=("-z", "+z"))
    if style == "cone":
        prism(kit, (x, 0), z - 1.25, z - 0.5, 2.0, 0.3, 4, colour, scale=(1.0, 0.55), bottom_colour=trim)
    elif style == "flat":
        kit.box((x - 1.4, -0.8, z - 1.2), (x + 1.4, 0.8, z - 0.85), colour)
    else:  # hoop: two arms to a boxy top
        kit.box((x - 0.8, -0.55, z - 1.15), (x + 0.8, 0.55, z - 0.6), colour)
    for sx in (-1, 1):
        x0, x1 = sorted((x + sx * 0.85, x + sx * 1.2))
        kit.box((x0, -0.17, z - 2.05), (x1, 0.17, z - 1.2), trim, skip=("-z", "+z"))
    fair.hexa(
        kit,
        [(x - 1.0, -0.6, z - HANG), (x + 1.0, -0.6, z - HANG), (x + 1.0, 0.6, z - HANG), (x - 1.0, 0.6, z - HANG)],
        [(x - 1.3, -0.75, z - 2.05), (x + 1.3, -0.75, z - 2.05), (x + 1.3, 0.75, z - 2.05), (x - 1.3, 0.75, z - 2.05)],
        colour,
        colours={1: "interiorCream"},
    )
    for facing in (-1, 1):
        panel_y(kit, x - 1.1, x + 1.1, z - 2.55, z - 2.3, facing * 0.72, facing, trim)


def build(building_id, seed, scheme=None, collection=None):
    """Build one Ferris wheel. Returns (empty, stats)."""
    rng = random.Random(seed)

    radius = rng.choice([6.4, 6.9, 7.4])
    phase = rng.choice([0.0, 22.5])  # 0 stops with a gondola at the very bottom
    inner_ring = rng.random() < 0.4
    style = rng.choice(["cone", "flat", "hoop"])
    colouring = rng.choice(["rainbow", "pairs", "scheme"])
    brace = rng.choice(["low", "high", "none"])
    first = rng.randrange(len(BRIGHT))
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    hub_z = radius + HANG + 0.55
    spread = hub_z * 0.5
    rim_colour = pal["wall"]
    spoke_colour = pal["trim"]
    leg_colour = pal["roof"]
    accent = pal["door"] if pal["door"] != "doorBrown" else "sunny"

    def vertex(k, r=None, y=0.0):
        a = math.radians(-90.0 + phase + k * 360.0 / SEGMENTS)
        r = radius if r is None else r
        return (r * math.cos(a), y, hub_z + r * math.sin(a))

    def storey(z):
        return max(1, min(4, int(z // 4.5)))

    # --- legs: two A-frames, splayed front to back as well ---
    legs = []
    for sy in (-1, 1):
        for sx in (-1, 1):
            kit = Kit()
            foot = (sx * spread, sy * (LEG_Y + 1.0), 0.0)
            fair.beam(kit, foot, (sx * 0.25, sy * LEG_Y, hub_z + 0.2), LEG, leg_colour, flat=True)
            kit.box((foot[0] - 0.75, foot[1] - 0.75, 0), (foot[0] + 0.75, foot[1] + 0.75, 0.5), pal["trim"], skip=("-z",))
            legs.append(add(kit, "pillar", "tin", 0, collider="hull"))

    if brace != "none":
        f = 0.3 if brace == "low" else 0.55
        for side, sy in enumerate((-1, 1)):
            kit = Kit()
            y = sy * (LEG_Y + 1.0 - f * 1.0)
            x = spread - f * (spread - 0.25)
            fair.beam(kit, (-x, y, hub_z * f), (x, y, hub_z * f), 0.45, pal["trim"], caps=False)
            add(kit, "detail", "tin", 1, supports=(legs[side * 2], legs[side * 2 + 1]))

    # --- the hub ---
    kit = Kit()
    prism(kit, (0, hub_z), -LEG_Y - 0.5, LEG_Y + 0.5, 1.0, 1.0, 8, accent, axis="y")
    for facing in (-1, 1):
        y = facing * (LEG_Y + 0.52)
        kit.poly(
            [(0.55 * math.cos(i * math.pi / 2), y, hub_z + 0.55 * math.sin(i * math.pi / 2)) for i in range(4)],
            (0, facing, 0),
            pal["trim"],
        )
    hub = add(kit, "detail", "tin", 2, supports=legs, collider="hull")

    # --- spokes: eight pairs, one each side ---
    spokes = []
    for j in range(8):
        kit = Kit()
        for y in (-RIM_Y, RIM_Y):
            fair.beam(kit, vertex(2 * j, 0.8, y), vertex(2 * j, radius, y), SPOKE, spoke_colour, up=(0, 1, 0), caps=False)
            if inner_ring:
                fair.beam(
                    kit,
                    vertex(2 * j, radius * 0.55, y),
                    vertex(2 * j + 2, radius * 0.55, y),
                    SPOKE,
                    rim_colour,
                    up=(0, 1, 0),
                    caps=False,
                )
        spokes.append(add(kit, "detail", "tin", storey(vertex(2 * j, radius * 0.5)[2]), supports=(hub,), collider="hull"))

    # --- the rim: sixteen segments, front and back together, with the bar a gondola hangs from ---
    rims = []
    for k in range(SEGMENTS):
        kit = Kit()
        for y in (-RIM_Y, RIM_Y):
            a, b = vertex(k, y=y), vertex(k + 1, y=y)
            stretch = 0.06 / math.dist(a, b)  # a little overlap, so the corners close up
            a2 = tuple(a[n] + (a[n] - b[n]) * stretch for n in range(3))
            b2 = tuple(b[n] + (b[n] - a[n]) * stretch for n in range(3))
            fair.beam(kit, a2, b2, RIM, rim_colour if k % 2 == 0 else pal["trim"], up=(0, 1, 0))
        if k % 2 == 0:
            fair.beam(kit, vertex(k, y=-RIM_Y), vertex(k, y=RIM_Y), 0.32, spoke_colour, up=(1, 0, 0), caps=False)
        spoke = spokes[(k // 2) % 8] if k % 2 == 0 else spokes[((k + 1) // 2) % 8]
        rims.append(add(kit, "detail", "tin", storey(vertex(k)[2]), supports=(spoke,), collider="hull"))

    # --- gondolas ---
    for j in range(8):
        if colouring == "rainbow":
            colour = BRIGHT[(first + j) % len(BRIGHT)]
        elif colouring == "pairs":
            colour = (BRIGHT[first], BRIGHT[(first + 2) % len(BRIGHT)])[j % 2]
        else:
            colour = (pal["roof"], accent)[j % 2]
        x, _, z = vertex(2 * j)
        kit = Kit()
        _gondola(kit, x, z, style, colour, "trimWhite")
        add(kit, "detail", "tin", storey(z - 2), supports=(rims[2 * j], rims[(2 * j - 1) % SEGMENTS]), collider="hull")

    # --- the boarding deck, with steps at the front ---
    kit = Kit()
    kit.box((-3.2, -1.5, 0), (3.2, 1.5, 0.4), "wood", skip=("-z",))
    kit.box((-1.6, -2.4, 0), (1.6, -1.5, 0.2), pal["trim"], skip=("-z", "+y"))
    add(kit, "detail", "wood", 0)

    return building.finish(
        look=f"r={radius} phase={phase} {style}/{colouring}/brace-{brace}" + ("/inner-ring" if inner_ring else "")
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(24, 30))


if __name__ == "__main__":
    previews()
