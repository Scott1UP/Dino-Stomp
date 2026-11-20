"""Log pile generator.

A stack of three to six big cut logs: eight-sided, about 4 m long and 1.1 m
across, lying along X with pale cut ends. In the game every log is a loose
physics body from the start, so the pile rolls apart when the dino walks in.

The logs sit flat side down on the ground with a 1 cm gap between neighbours,
and each upper log rests in the groove between two below, its slanting faces
flat against theirs: no overlaps, and the faces touch exactly. The seed picks
the stack (3-2-1, 3-2, 2-1 or 3-1) and varies the logs' lengths, how far their
ends are staggered, and the bark.

    blender --background --factory-startup --python assets-src/props/log_pile.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_forest import log  # noqa: E402

TYPE = "log_pile"
KIND = "block"
TRIANGLE_BUDGET = 300
SPACING = 8

APOTHEM = 0.55  # middle of a log to a flat side: 1.1 m across the flats
GAP = 0.01  # between neighbours in a row
STACKS = ((3, 2, 1), (3, 2), (2, 1), (3, 1))
PITCH = 2 * APOTHEM + GAP  # centre to centre along a row
# A log in a groove sits half a pitch across from each log under it. Their
# slanting faces touch when the centres are 2 * APOTHEM apart along the slant.
RISE = 2 * math.sqrt(2) * APOTHEM - PITCH / 2


def build(building_id, seed, scheme=None, collection=None):
    """Build one log pile. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    stack = STACKS[seed % len(STACKS)]  # cycled, so neighbouring seeds differ
    shift = rng.choice([0, 1]) if stack == (3, 1) else 0  # which groove the single top log lies in
    bark_mix = rng.choice([("wood",), ("wood", "wood", "doorBrown"), ("wood", "doorBrown")])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    rows = []  # each row: list of (y, module id)
    for r, count in enumerate(stack):
        z = APOTHEM + r * RISE
        if r == 0:
            ys = [(i - (count - 1) / 2) * PITCH for i in range(count)]
            under = [()] * count
        else:
            below = rows[-1]
            grooves = [((below[i][0] + below[i + 1][0]) / 2, (below[i][1], below[i + 1][1])) for i in range(len(below) - 1)]
            grooves = grooves[shift : shift + count]
            ys = [g[0] for g in grooves]
            under = [g[1] for g in grooves]
        row = []
        for y, holders in zip(ys, under):
            length = rng.choice([3.7, 4.0, 4.0, 4.3])
            x = rng.choice([-0.2, 0.0, 0.0, 0.2])
            bark = rng.choice(bark_mix)
            kit = Kit()
            log(kit, "x", x - length / 2, x + length / 2, (y, z), APOTHEM, bark, end="interiorCream", ring="wood" if bark == "doorBrown" else "doorBrown")
            row.append((y, building.add(kit, "detail", "wood", r, supports=holders, collider="hull")))
        rows.append(row)

    return building.finish(look=f"{'-'.join(str(n) for n in stack)} logs={sum(stack)}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(SPACING, SPACING))


if __name__ == "__main__":
    previews()
