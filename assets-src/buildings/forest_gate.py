"""Forest gate generator.

A rustic park entrance about 10 m wide and 7 m tall: two thick log posts on
stone feet, a carved cross-log through them with painted bands and its cut
ends sticking out, and a big sign hanging under it with a simple picture on
both sides (a pine, a tree, a leaf, a toadstool or a mountain; no words).

The seed varies the width, the posts (their girth, colour and tops), the
cross-log (plain, doubled, or with a peak of two sloping logs above it), knee
braces, the sign's shape and the picture.

The two posts are role "pillar" at storey 0; the cross-log rests on both and
the sign hangs from it.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/forest_gate.py
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
from lib.shapes_forest import COS8, PICTURES, cone, log, picture  # noqa: E402
from lib.shapes_props import prism  # noqa: E402

TYPE = "forest_gate"
HITS_TO_COLLAPSE = 1
TRIANGLE_BUDGET = 400

BAR_Z = 5.6  # the middle of the cross-log
TOPS = ("plain", "peak", "double")
SIGNS = ("board", "plaque")


def build(building_id, seed, scheme=None, collection=None):
    """Build one forest gate. Returns (empty, stats)."""
    rng = random.Random(seed)

    top = TOPS[seed % len(TOPS)]  # cycled, so neighbouring seeds differ
    image = PICTURES[seed % len(PICTURES)]
    sign_shape = SIGNS[(seed // 2) % len(SIGNS)]
    span = rng.choice([4.0, 4.3, 4.6])  # half the distance between the posts
    girth = rng.choice([0.48, 0.55, 0.62])  # the posts' apothem
    dark = rng.choice([True, False])
    caps = rng.choice(["cone", "cut"])
    braces = rng.choice([True, False])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    bark, other = ("doorBrown", "wood") if dark else ("wood", "doorBrown")
    post_h = 6.6 if caps == "cone" else 6.9
    bar = 0.42

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    # --- the two posts ---
    posts = []
    for sign in (-1, 1):
        x = sign * span
        kit = Kit()
        prism(kit, (x, 0), 0, 0.5, (girth + 0.28) / COS8, (girth + 0.18) / COS8, 8, "stone", bottom=False, top_colour="stone")
        log(kit, "z", 0.5, post_h, (x, 0), girth, bark, end="interiorCream", ring=other if caps == "cut" else None, caps=(False, True))
        prism(kit, (x, 0), 3.9, 4.25, (girth + 0.06) / COS8, (girth + 0.06) / COS8, 8, pal["roof"], bottom=False, top=False)
        if caps == "cone":
            cone(kit, (x, 0, post_h), girth / COS8 + 0.2, (x, 0, post_h + 0.9), 8, pal["roof"], under=pal["roof"])
        posts.append(add(kit, "pillar", "wood", 0, collider="hull"))

    # --- the cross-log, with painted bands ---
    reach = span + 1.2
    kit = Kit()
    log(kit, "x", -reach, reach, (0, BAR_Z), bar, bark, end="interiorCream", ring=other)
    for x in (-reach + 0.5, reach - 0.8):
        prism(kit, (0, BAR_Z), x, x + 0.3, (bar + 0.05) / COS8, (bar + 0.05) / COS8, 8, pal["wall"], bottom=False, top=False, axis="x")
    cross = add(kit, "band", "wood", 1, supports=posts, collider="hull")
    if top == "peak":
        kit = Kit()
        for sign in (-1, 1):
            beam(kit, (sign * (span - 0.3), 0, BAR_Z + 0.3), (0, 0, BAR_Z + 1.5), 0.36, other)
        add(kit, "detail", "wood", 2, supports=(cross,), collider="hull")

    hang_z = BAR_Z - bar
    if top == "double":  # a second, thinner log; the sign hangs from this one
        hang_z = BAR_Z - 1.25
        kit = Kit()
        log(kit, "x", -span, span, (0, hang_z + 0.24), 0.24, other, end=other)
        add(kit, "band", "wood", 1, supports=posts, collider="hull")
    if braces:
        kit = Kit()
        for sign in (-1, 1):
            beam(kit, (sign * span, 0, hang_z - 1.3), (sign * (span - 1.5), 0, hang_z + 0.1), 0.3, other, caps=False)
        add(kit, "detail", "wood", 1, supports=posts, collider="hull")

    # --- the hanging sign: a picture on both sides ---
    drop = 0.45
    sign_w, sign_h = (3.4, 2.1) if sign_shape == "board" else (2.7, 2.5)
    mid_z = hang_z - drop - sign_h / 2
    kit = Kit()
    if sign_shape == "board":
        kit.box((-sign_w / 2, -0.12, mid_z - sign_h / 2), (sign_w / 2, 0.12, mid_z + sign_h / 2), pal["wall"])
        inner = [(-sign_w / 2 + 0.2, -sign_h / 2 + 0.2), (sign_w / 2 - 0.2, -sign_h / 2 + 0.2), (sign_w / 2 - 0.2, sign_h / 2 - 0.2), (-sign_w / 2 + 0.2, sign_h / 2 - 0.2)]
    else:
        prism(kit, (0, mid_z), -0.12, 0.12, sign_h / 2 / COS8, sign_h / 2 / COS8, 8, pal["wall"], axis="y", scale=(sign_w / sign_h, 1.0))
        r = (sign_h / 2 - 0.2) / COS8
        inner = [(r * math.cos(k * math.pi / 2) * sign_w / sign_h, r * math.sin(k * math.pi / 2)) for k in range(4)]  # a diamond
    for facing in (-1, 1):
        flat(kit, (0, facing * 0.12, mid_z), (0, facing, 0), inner, "interiorCream", lift=0.02)
        picture(kit, image, (0, facing * 0.12, mid_z), (0, facing, 0), min(sign_w, sign_h) * 0.86, lift=0.04)
    for sign in (-1, 1):  # the ropes
        x = sign * sign_w * 0.32
        beam(kit, (x, 0, mid_z + sign_h / 2 - 0.05), (x, 0, hang_z + 0.05), 0.1, "trimWhite", caps=False)
    add(kit, "detail", "wood", 1, supports=(cross,), collider="box")

    return building.finish(look=f"{top}/{image}/{sign_shape}/span{span * 2:g}/girth{girth}/{bark}/{caps}/braces-{int(braces)}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(15, 9))


if __name__ == "__main__":
    previews()
