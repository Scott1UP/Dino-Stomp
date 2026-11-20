"""Canoe generator.

A bright canoe about 4.6 m long, pulled up on the ground, with a white rim,
two seats and a paddle. Two modules: the canoe, and the paddle (lying across
it or on the ground beside it). The seed varies the length and beam, how high
the ends sweep up, the colours and where the paddle is.

    blender --background --factory-startup --python assets-src/props/canoe.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from mathutils import Vector  # noqa: E402

from lib.shapes_blocktown import beam  # noqa: E402
from lib.shapes_props import BRIGHT  # noqa: E402

TYPE = "canoe"
KIND = "prop"
TRIANGLE_BUDGET = 150
SPACING = 6


def _face(kit, points, hint, colour):
    """A triangle, or a quad split in two (the hull's quads are not flat)."""
    unique = []
    for p in points:
        if all((Vector(p) - Vector(q)).length > 1e-6 for q in unique):
            unique.append(p)
    if len(unique) == 3:
        kit.poly(unique, hint, colour)
    elif len(unique) == 4:
        kit.poly(unique[:3], hint, colour)
        kit.poly([unique[0], unique[2], unique[3]], hint, colour)


def build(building_id, seed, scheme=None, collection=None):
    """Build one canoe. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    hull = BRIGHT[seed % len(BRIGHT)]  # cycled, so neighbouring seeds differ
    length = rng.choice([4.2, 4.6, 5.0])
    beam_w = rng.choice([0.55, 0.62])  # half the width amidships
    sweep = rng.choice([0.75, 0.9, 1.05])  # height of the ends
    paddle_place = rng.choice(["across", "beside"])
    paddle_colour = rng.choice([c for c in BRIGHT if c != hull])
    inside = rng.choice(["wood", "interiorCream"])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    side = 0.52  # height of the sides amidships
    half = length / 2
    rim = 0.09
    # Stations from end to end: (x, half width, side height). The ends are single points.
    stations = [(-half * 0.55, beam_w * 0.8, side + 0.04), (0.0, beam_w, side), (half * 0.55, beam_w * 0.8, side + 0.04)]

    def outer(x, w, h):
        return {"gl": (x, -w, h), "cl": (x, -w * 0.55, 0), "cr": (x, w * 0.55, 0), "gr": (x, w, h)}

    def inner(x, w, h):
        return {"gl": (x, -w + rim, h), "cl": (x, -w * 0.5, 0.1), "cr": (x, w * 0.5, 0.1), "gr": (x, w - rim, h)}

    def stem(sign, shell):
        top = (sign * (half - (0.3 if shell == "in" else 0)), 0, sweep)
        keel = (sign * (half - 0.45), 0, 0.06) if shell == "out" else top
        return {"gl": top, "cl": keel, "cr": keel, "gr": top}

    out = [stem(-1, "out")] + [outer(*s) for s in stations] + [stem(1, "out")]
    ins = [stem(-1, "in")] + [inner(*s) for s in stations] + [stem(1, "in")]

    kit = Kit()
    for a, b in zip(out, out[1:]):
        mid_x = (a["gl"][0] + b["gl"][0]) / 2
        tilt = mid_x * 0.25
        _face(kit, [a["gl"], a["cl"], b["cl"], b["gl"]], (tilt, -1, -0.3), hull)
        _face(kit, [a["gr"], a["cr"], b["cr"], b["gr"]], (tilt, 1, -0.3), hull)
        _face(kit, [a["cl"], a["cr"], b["cr"], b["cl"]], (tilt * 0.3, 0, -1), hull)
    for a, b in zip(ins, ins[1:]):
        mid_x = (a["gl"][0] + b["gl"][0]) / 2
        tilt = -mid_x * 0.25
        _face(kit, [a["gl"], a["cl"], b["cl"], b["gl"]], (tilt, 1, 0.3), inside)
        _face(kit, [a["gr"], a["cr"], b["cr"], b["gr"]], (tilt, -1, 0.3), inside)
        _face(kit, [a["cl"], a["cr"], b["cr"], b["cl"]], (tilt, 0, 1), inside)
    for (a, b), (c, d) in zip(zip(out, out[1:]), zip(ins, ins[1:])):
        _face(kit, [a["gl"], c["gl"], d["gl"], b["gl"]], (0, 0, 1), "trimWhite")
        _face(kit, [a["gr"], c["gr"], d["gr"], b["gr"]], (0, 0, 1), "trimWhite")
    for x in (-half * 0.3, half * 0.3):
        w = beam_w * 0.88 - rim
        kit.box((x - 0.16, -w, side - 0.16), (x + 0.16, w, side - 0.08), "wood", skip=("-y", "+y"))
    boat = building.add(kit, "detail", "wood", 0, collider="hull")

    kit = Kit()
    if paddle_place == "across":
        a, b = (half * 0.05, -beam_w - 0.9, side + 0.12), (half * 0.25, beam_w + 0.5, side + 0.12)
        holders = (boat,)
    else:
        y = -beam_w - 0.5
        a, b = (-half * 0.45, y, 0.07), (half * 0.35, y - 0.25, 0.07)
        holders = ()
    a, b = Vector(a), Vector(b)
    along = (b - a).normalized()
    beam(kit, a, b, 0.11, "wood")
    blade_a, blade_b = a - along * 0.75, a + along * 0.05
    beam(kit, blade_a, blade_b, 0.36, paddle_colour, depth=0.07)
    building.add(kit, "detail", "wood", 0, supports=holders, collider="box")

    return building.finish(look=f"{hull} len={length} beam={beam_w * 2:g} sweep={sweep} paddle-{paddle_place}/{paddle_colour}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
