"""Apple tree generator.

A round fruit tree about 5 m tall in two modules: a stout trunk (with a few
windfalls round its foot), and a broad leafy top resting on it, dotted with
apples: small flat-ish blobs standing just proud of the leaves. The seed
varies the trunk, the size and squash of the top, how many apples there are
and their colour (tomato red mostly, sometimes sunny yellow).

    blender --background --factory-startup --python assets-src/props/apple_tree.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import shapes_farm as farm  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import ball, prism  # noqa: E402

TYPE = "apple_tree"
KIND = "prop"
TRIANGLE_BUDGET = 150


def _leaves(segment, ring):
    """Darker underneath, so the top reads as round even in flat light."""
    return "hedge" if ring == 0 else "leaf"


def build(building_id, seed, scheme=None, collection=None):
    """Build one apple tree. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    trunk_height = rng.choice([1.8, 2.1, 2.4])
    radius = rng.choice([2.0, 2.2, 2.4])
    squash = (0.72, 0.82, 0.92)[seed % 3]  # cycled, so neighbouring seeds always differ
    apple = "sunny" if seed % 4 == 0 else "tomato"
    apples = rng.choice([6, 7, 8])
    trunk_colour = rng.choice(["doorBrown", "doorBrown", "wood"])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    kit = Kit()
    prism(kit, (0, 0), 0, trunk_height, 0.5, 0.34, 6, trunk_colour)
    for k in range(rng.choice([2, 3])):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(1.0, 1.8)
        farm.stud(kit, (d * math.cos(a), d * math.sin(a), 0), (0, 0, 1), 0.3, 0.3, apple)
    trunk = building.add(kit, "detail", "wood", 0, collider="hull")

    kit = Kit()
    cz = trunk_height - 0.35 + radius * squash  # the top sits down over the trunk
    ball(kit, (0, 0, cz), radius, 8, 4, "leaf", _leaves, squash=squash)
    # Apples: on the upper rings, where the camera sees them.
    start = rng.uniform(0, 1)
    for k in range(apples):
        lon = (k + start) * 2 * math.pi / apples * 1.0 + (0.4 if k % 2 else 0.0)
        lat = math.radians(48 if k % 2 else 8) + rng.uniform(-0.08, 0.08)
        n = (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat) / squash)
        r = radius * 0.96
        at = (r * math.cos(lat) * math.cos(lon), r * math.cos(lat) * math.sin(lon), cz + r * math.sin(lat) * squash)
        farm.stud(kit, at, n, 0.44, 0.4, apple)
    building.add(kit, "detail", "leaves", 0, supports=(trunk,), collider="hull")

    return building.finish(look=f"trunk={trunk_height} r={radius} squash={squash} {apples} {apple} apples")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(8, 8))


if __name__ == "__main__":
    previews()
