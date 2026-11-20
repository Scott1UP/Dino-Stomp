"""A giant toy sunflower, taller than a house: a thick stalk, two big leaves and a huge flower head.

It stands like a building (he has to knock it over), and comes apart into stalk,
leaves and head. About 100 triangles, so a field of them is cheap.

    blender --background --factory-startup --python assets-src/buildings/giant_sunflower.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "giant_sunflower"
HITS_TO_COLLAPSE = 1
TRIANGLE_BUDGET = 160
SIDES = 6


def prism(kit, cx, cy, z0, z1, r0, r1, colour, lean=(0.0, 0.0)):
    """A tapering six-sided post from z0 to z1, its top shifted by `lean`."""
    bottom = [(cx + r0 * math.cos(a), cy + r0 * math.sin(a), z0) for a in (i * math.tau / SIDES for i in range(SIDES))]
    top = [(cx + lean[0] + r1 * math.cos(a), cy + lean[1] + r1 * math.sin(a), z1) for a in (i * math.tau / SIDES for i in range(SIDES))]
    faces = [bottom, top] + [[bottom[i], bottom[(i + 1) % SIDES], top[(i + 1) % SIDES], top[i]] for i in range(SIDES)]
    kit.convex(faces, colour)


def build(building_id, seed, scheme=None, collection=None):
    rng = random.Random(seed)
    height = rng.uniform(11, 15)
    head_r = rng.uniform(2.2, 2.8)
    petals = rng.choice([8, 10, 12])
    petal_colour = rng.choice(["sunny", "sunny", "tangerine", "starGold"])
    tilt = math.radians(rng.uniform(15, 35))  # the face turns towards the sun, and the camera
    lean = (rng.uniform(-0.6, 0.6), rng.uniform(-1.2, -0.4))
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)
    building = Building(building_id, TYPE, seed, scheme or seeded_scheme, HITS_TO_COLLAPSE, collection)

    # --- the stalk, in two pieces so it snaps in the middle ---
    mid = height * 0.5
    kit = Kit()
    prism(kit, 0, 0, 0, mid, 0.75, 0.6, "leaf", lean=(lean[0] / 2, lean[1] / 2))
    lower = building.add(kit, "wall", "leaves", 0, collider="hull")
    kit = Kit()
    prism(kit, lean[0] / 2, lean[1] / 2, mid, height - 0.4, 0.6, 0.5, "leaf", lean=(lean[0] / 2, lean[1] / 2))
    upper = building.add(kit, "wall", "leaves", 1, supports=(lower,), collider="hull")

    # --- two big leaves, one each side ---
    for side, z in ((-1, height * 0.3), (1, height * 0.55)):
        kit = Kit()
        root = (lean[0] * z / height, lean[1] * z / height)
        reach = rng.uniform(3.2, 4.2)
        tip = (root[0] + side * reach, root[1], z + 1.2)
        wide = 1.1
        points = [
            (root[0], root[1] - 0.2, z),
            (root[0] + side * reach * 0.5, root[1] - wide, z + 0.9),
            tip,
            (root[0] + side * reach * 0.5, root[1] + wide, z + 0.9),
        ]
        kit.poly(points, (0, 0, 1), "hedge")
        kit.poly(list(reversed(points)), (0, 0, -1), "leaf")
        building.add(kit, "detail", "leaves", 1, supports=(lower if side < 0 else upper,))

    # --- the head: a brown seed disc ringed with petals, tipped to face forwards ---
    centre = (lean[0], lean[1] - 0.3, height)
    normal = (0.0, -math.sin(tilt), math.cos(tilt))

    def place(u, v, out=0.0):
        """A point on the head: u across, v up its face, `out` towards the viewer."""
        across = (1.0, 0.0, 0.0)
        up = (0.0, math.cos(tilt), math.sin(tilt))
        return tuple(centre[k] + across[k] * u + up[k] * v + normal[k] * out for k in range(3))

    kit = Kit()
    ring = [place(head_r * 0.55 * math.cos(a), head_r * 0.55 * math.sin(a), 0.35) for a in (i * math.tau / 8 for i in range(8))]
    back = [place(head_r * 0.55 * math.cos(a), head_r * 0.55 * math.sin(a), -0.35) for a in (i * math.tau / 8 for i in range(8))]
    kit.convex([ring, back] + [[ring[i], ring[(i + 1) % 8], back[(i + 1) % 8], back[i]] for i in range(8)], "doorBrown", colours={1: "leaf"})
    for i in range(petals):
        a = i * math.tau / petals
        b = a + math.pi / petals
        c = a - math.pi / petals
        inner = head_r * 0.45
        quad = [
            place(inner * math.cos(c), inner * math.sin(c), 0.1),
            place(head_r * 0.95 * math.cos(c + 0.02), head_r * 0.95 * math.sin(c + 0.02), 0.15),
            place(head_r * 1.35 * math.cos(a), head_r * 1.35 * math.sin(a), 0.2),
            place(head_r * 0.95 * math.cos(b - 0.02), head_r * 0.95 * math.sin(b - 0.02), 0.15),
        ]
        kit.poly([quad[0], quad[2], quad[1]], normal, petal_colour)
        kit.poly([quad[0], quad[3], quad[2]], normal, petal_colour)
    building.add(kit, "detail", "leaves", 2, supports=(upper,), collider="hull")

    return building.finish(look=f"h={height:.1f} petals={petals}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(12, 12))


if __name__ == "__main__":
    previews()
