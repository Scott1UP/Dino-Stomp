"""Wooden crate generator.

A crate about 2 m across, built from six panel modules: a floor, four sides
and a lid. It is hollow, so a golden egg can sit inside. Side panels and the
lid have brown edging and a diagonal brace on the outside. The seed varies the
size and the braces. Set `LID = False` for an open-topped crate (five modules).

    blender --background --factory-startup --python assets-src/props/crate.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "crate"
KIND = "crate"
TRIANGLE_BUDGET = 150

LID = True
THICK = 0.16
EDGE = 0.22  # width of the edging strips
PROUD = 0.03  # how far the edging sits off the panel


def _panel(place, u0, u1, v0, v1, brace):
    """One panel. `place(u, v, w)` maps panel coordinates to the crate: u and v
    across the face, w from the outside face (0) inwards."""
    kit = Kit()
    corners = lambda w: [place(u0, v0, w), place(u1, v0, w), place(u1, v1, w), place(u0, v1, w)]  # noqa: E731
    outer, inner = corners(0), corners(THICK)
    faces = [outer, inner] + [[outer[i], outer[(i + 1) % 4], inner[(i + 1) % 4], inner[i]] for i in range(4)]
    kit.convex(faces, "wood", {index: "doorBrown" for index in range(2, 6)})

    out = [a - b for a, b in zip(place(0, 0, -1), place(0, 0, 0))]

    def strip(points):
        kit.poly([place(u, v, -PROUD) for u, v in points], out, "doorBrown")

    strip([(u0, v0), (u1, v0), (u1, v0 + EDGE), (u0, v0 + EDGE)])
    strip([(u0, v1 - EDGE), (u1, v1 - EDGE), (u1, v1), (u0, v1)])
    strip([(u0, v0 + EDGE), (u0 + EDGE, v0 + EDGE), (u0 + EDGE, v1 - EDGE), (u0, v1 - EDGE)])
    strip([(u1 - EDGE, v0 + EDGE), (u1, v0 + EDGE), (u1, v1 - EDGE), (u1 - EDGE, v1 - EDGE)])
    if brace:
        a0, a1 = u0 + EDGE, u1 - EDGE
        b0, b1 = v0 + EDGE, v1 - EDGE
        if brace < 0:
            a0, a1 = a1, a0
        step = EDGE * 1.2 * (1 if a1 > a0 else -1)
        strip([(a0, b0), (a0 + step, b0), (a1, b1), (a1 - step, b1)])
    return kit


def build(building_id, seed, scheme=None, collection=None):
    """Build one crate. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    half = rng.choice([0.95, 1.0, 1.1])
    height = rng.choice([1.8, 2.0, 2.1])
    braces = rng.choice(["same", "mirrored", "none"])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    kit.box((-half, -half, 0), (half, half, THICK), "wood", sides={s: "doorBrown" for s in ("-x", "+x", "-y", "+y")})
    floor = building.add(kit, "detail", "wood", 0)

    top = height - (THICK if LID else 0)
    inset = half - THICK
    sides = [
        (lambda u, v, w: (u, -half + w, v), half),  # front
        (lambda u, v, w: (u, half - w, v), half),  # back
        (lambda u, v, w: (-half + w, u, v), inset),  # left, between front and back
        (lambda u, v, w: (half - w, u, v), inset),  # right
    ]
    walls = []
    for index, (place, reach) in enumerate(sides):
        brace = 0 if braces == "none" else (1 if braces == "same" or index % 2 == 0 else -1)
        kit = _panel(place, -reach, reach, THICK, top, brace)
        walls.append(building.add(kit, "detail", "wood", 0, supports=(floor,)))

    if LID:
        kit = _panel(lambda u, v, w: (u, v, height - w), -half, half, -half, half, 0)
        building.add(kit, "detail", "wood", 0, supports=walls)

    return building.finish(look=f"w={half * 2} h={height} braces={braces}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 8))


if __name__ == "__main__":
    previews()
