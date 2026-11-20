"""Farm gate arch generator: a timber ranch entrance.

About 10 m wide and 7 m tall: two thick posts on stone feet with knee braces,
a cross beam (straight, peaked, or doubled with struts), a sign board hanging
from it on two chains with a simple picture on both sides (no words), and a
lantern hanging near each post.

The seed varies the beam, the picture (apple, sunflower, carrot, barn, sun or
wheat), the board's colour and shape, the timber colour and what stands on
top (a wagon wheel, a weather vane or nothing). The board takes the scheme's
wall colour.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/farm_gate_arch.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_farm as farm  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_castle2 import pyramid  # noqa: E402
from lib.shapes_fair import beam  # noqa: E402
from lib.shapes_props import prism  # noqa: E402

TYPE = "farm_gate_arch"
HITS_TO_COLLAPSE = 1  # two posts and a beam
TRIANGLE_BUDGET = 400

POST_X = 4.4  # centre of each post
POST = 0.8
BEAMS = ("straight", "peaked", "double")
# Pictures that would vanish on a board of the same colour.
CLASH = {"tomato": ("apple", "barn"), "sunny": ("sunflower", "sun", "wheat"), "tangerine": ("carrot", "sun")}


def build(building_id, seed, scheme=None, collection=None):
    """Build one gate arch. Returns (empty, stats)."""
    rng = random.Random(seed)

    style = BEAMS[seed % len(BEAMS)]  # cycled, so neighbouring seeds always differ
    picture = farm.PICTURES[(seed * 5) % len(farm.PICTURES)]
    timber = rng.choice(["doorBrown", "doorBrown", "wood"])
    topper = rng.choice(["wheel", "vane", "none"])
    if topper == "wheel" and style != "straight":
        topper = "vane"  # a wheel on the taller beams would stand well over 7 m
    pointed = rng.random() < 0.5
    beam_z = rng.choice([4.9, 5.2])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]
    board = pal["wall"]
    if picture in CLASH.get(board, ()):
        board = "cobalt"
    accent = "wood" if timber == "doorBrown" else "doorBrown"

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add
    half = POST / 2

    # --- two thick posts on stone feet, each with a knee brace ---
    posts = []
    for sign in (-1, 1):
        x = sign * POST_X
        kit = Kit()
        kit.box((x - half, -half, 0), (x + half, half, beam_z), timber, skip=("-z", "+z"))
        kit.box((x - half - 0.15, -half - 0.15, 0), (x + half + 0.15, half + 0.15, 0.7), "stone", skip=("-z",))
        beam(kit, (x - sign * half, 0, beam_z - 1.7), (x - sign * 1.9, 0, beam_z - 0.05), 0.36, timber, caps=False)
        posts.append(add(kit, "pillar", "wood", 0, collider="hull"))

    # --- the cross beam ---
    out = POST_X + half + 0.4
    top_z = beam_z + 0.6
    if style == "straight":
        kit = Kit()
        kit.box((-out, -0.38, beam_z), (out, 0.38, beam_z + 0.6), timber, sides={"-x": accent, "+x": accent})
        beams = [add(kit, "band", "wood", 1, supports=posts)]
    elif style == "double":
        kit = Kit()
        kit.box((-out, -0.38, beam_z), (out, 0.38, beam_z + 0.45), timber, sides={"-x": accent, "+x": accent})
        lower = add(kit, "band", "wood", 1, supports=posts)
        kit = Kit()
        top_z = beam_z + 1.35
        kit.box((-out + 0.5, -0.32, top_z - 0.4), (out - 0.5, 0.32, top_z), timber, sides={"-x": accent, "+x": accent})
        for x in (-POST_X, -POST_X / 3, POST_X / 3, POST_X):
            kit.box((x - 0.2, -0.2, beam_z + 0.45), (x + 0.2, 0.2, top_z - 0.4), accent, skip=("-z", "+z"))
        beams = [lower, add(kit, "band", "wood", 2, supports=(lower,))]
    else:  # peaked: a tie beam, and two rafters meeting over the middle
        kit = Kit()
        kit.box((-out, -0.38, beam_z), (out, 0.38, beam_z + 0.45), timber, sides={"-x": accent, "+x": accent})
        lower = add(kit, "band", "wood", 1, supports=posts)
        top_z = beam_z + 1.6
        beams = [lower]
        for sign in (-1, 1):
            kit = Kit()
            kit.extrude_y(
                [(sign * out, beam_z + 0.45), (sign * out, beam_z + 0.85), (0, top_z), (0, top_z - 0.5)],
                -0.32,
                0.32,
                timber,
            )
            if sign < 0:
                kit.box((-0.2, -0.2, beam_z + 0.45), (0.2, 0.2, top_z - 0.45), accent, skip=("-z", "+z"))
            beams.append(add(kit, "band", "wood", 2, supports=(lower,), collider="hull"))

    # --- the hanging sign: a board with a picture on both sides ---
    bw, bh = 1.75, 0.95  # half sizes
    bz = beam_z - 0.55 - bh  # the board's centre
    kit = Kit()
    if pointed:
        outline = [(-bw, bz - bh + 0.35), (0, bz - bh - 0.3), (bw, bz - bh + 0.35), (bw, bz + bh), (-bw, bz + bh)]
    else:
        outline = [(-bw, bz - bh), (bw, bz - bh), (bw, bz + bh), (-bw, bz + bh)]
    kit.extrude_y(outline, -0.12, 0.12, "trimWhite", colours={0: board, 1: board})
    for name, at in (("front", -0.12), ("back", 0.12)):
        farm.picture(kit, picture, farm.face(name, at), 0.0, bz + 0.05, 1.6)
    for x in (-bw + 0.35, bw - 0.35):
        kit.box((x - 0.06, -0.06, bz + bh), (x + 0.06, 0.06, beam_z), "tyre", skip=("-z", "+z"))
    add(kit, "detail", "wood", 1, supports=(beams[0],), collider="hull")

    # --- a lantern hanging near each post ---
    for sign in (-1, 1):
        x = sign * (POST_X - 1.25)
        z = beam_z - 1.25
        kit = Kit()
        kit.box((x - 0.05, -0.05, z + 0.75), (x + 0.05, 0.05, beam_z), "tyre", skip=("-z", "+z"))
        pyramid(kit, x, 0, 0.42, 0.42, z + 0.5, 0.3, "tyre")
        kit.box((x - 0.28, -0.28, z), (x + 0.28, 0.28, z + 0.5), "sunny", skip=("+z",))
        kit.box((x - 0.34, -0.34, z - 0.1), (x + 0.34, 0.34, z), "tyre", skip=("+z",))
        add(kit, "detail", "glass", 1, supports=(beams[0],), collider="hull")

    # --- something on top ---
    if topper == "wheel":
        kit = Kit()
        prism(kit, (0, top_z + 0.85), -0.12, 0.12, 0.9, 0.9, 8, accent, axis="y")
        for name, at in (("front", -0.12), ("back", 0.12)):
            face = farm.face(name, at)
            farm.fpoly(kit, face, [(-0.62, top_z + 0.76), (0.62, top_z + 0.76), (0.62, top_z + 0.94), (-0.62, top_z + 0.94)], 0.02, "trimWhite")
            farm.fpoly(kit, face, [(-0.09, top_z + 0.23), (0.09, top_z + 0.23), (0.09, top_z + 1.47), (-0.09, top_z + 1.47)], 0.02, "trimWhite")
        add(kit, "detail", "wood", 3, supports=(beams[-1],), collider="hull")
    elif topper == "vane":
        kit = Kit()
        kit.box((-0.07, -0.07, top_z), (0.07, 0.07, top_z + 1.0), "tyre", skip=("-z",))
        kit.box((-0.9, -0.05, top_z + 0.55), (0.6, 0.05, top_z + 0.75), "sunny")
        kit.extrude_y([(0.6, top_z + 0.35), (1.1, top_z + 0.65), (0.6, top_z + 0.95)], -0.05, 0.05, "tomato")
        add(kit, "detail", "tin", 3, supports=(beams[-1],), collider="hull")

    return building.finish(look=f"{style} {picture} board={board} {timber} top-{topper} z={beam_z}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(14, 9))


if __name__ == "__main__":
    previews()
