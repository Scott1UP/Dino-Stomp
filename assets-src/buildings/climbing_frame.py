"""Climbing frame generator.

A playground climbing frame, about 8 x 5 m and 4 m tall: a platform tower on
four posts, a slide off one side, a ladder up the front, and monkey bars
running out to a pair of end posts. The seed varies the roof (pyramid, flat
or just a flag), which side the slide and the bars are on, the back of the
tower (a panel or a climbing wall) and the colours.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/climbing_frame.py
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
from lib.shapes_props import BRIGHT, panel_y, prism  # noqa: E402

TYPE = "climbing_frame"
HITS_TO_COLLAPSE = 1  # small building
TRIANGLE_BUDGET = 400

HALF = 1.3  # half the tower's width
POST = 0.16  # half-thickness of a post
BAR = 0.24
SLIDE_RUN = 2.9


def build(building_id, seed, scheme=None, collection=None):
    """Build one climbing frame. Returns (empty, stats)."""
    rng = random.Random(seed)

    flip = 1 if seed % 2 else -1  # -1 puts the slide on the left and the bars on the right; alternates so neighbours differ
    deck = rng.choice([1.5, 1.7, 1.9])
    roof = rng.choice(["pyramid", "flat", "flag", "pyramid"])
    back = rng.choice(["panel", "wall"])
    bars_len = rng.choice([2.2, 2.6])
    rungs = rng.choice([3, 4])
    wavy = rng.random() < 0.4
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)

    def add(kit, *args, **kwargs):
        if flip == -1:
            fair.mirror_x(kit)
        return building.add(kit, *args, **kwargs)

    accent = pal["door"] if pal["door"] != "doorBrown" else "sunny"
    frame_colour = pal["wall"]
    tx = (bars_len - SLIDE_RUN) / 2  # the tower's centre: bars one side, slide the other
    post_h = deck + 1.6
    bars_z = deck + 0.85

    # --- four posts ---
    posts = {}
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = tx + sx * (HALF - POST), sy * (HALF - POST)
            kit = Kit()
            kit.box((x - POST, y - POST, 0), (x + POST, y + POST, post_h), frame_colour, skip=("-z",))
            posts[sx, sy] = add(kit, "pillar", "wood", 0)
    all_posts = list(posts.values())

    # --- the deck ---
    kit = Kit()
    kit.box((tx - HALF, -HALF, deck - 0.25), (tx + HALF, HALF, deck), "wood")
    floor = add(kit, "floor", "wood", 1, supports=all_posts)

    # --- roof ---
    if roof == "pyramid":
        kit = Kit()
        prism(kit, (tx, 0), post_h, post_h + 1.0, (HALF + 0.35) * 1.414, 0.0, 4, pal["roof"], bottom_colour="interiorCream")
        add(kit, "roof", "wood", 2, supports=all_posts, collider="hull")
    elif roof == "flat":
        kit = Kit()
        kit.box((tx - HALF - 0.3, -HALF - 0.3, post_h), (tx + HALF + 0.3, HALF + 0.3, post_h + 0.3), pal["roof"])
        add(kit, "roof", "wood", 2, supports=all_posts)
    else:
        kit = Kit()
        x, y = tx + (HALF - POST), HALF - POST
        shapes.flag(kit, x, y, post_h, 1.3, pal["roof"], size=1.0, thick=0.1)
        add(kit, "detail", "wood", 2, supports=(posts[1, 1],), collider="hull")

    # --- the slide, off the right-hand side ---
    x0 = tx + HALF
    x1 = x0 + SLIDE_RUN
    kit = Kit()
    if wavy:
        mid = (x0 + SLIDE_RUN * 0.47, 0, deck * 0.38)
        pieces = [((x0 - 0.1, 0, deck), mid), (mid, (x1, 0, 0.15))]
    else:
        pieces = [((x0 - 0.1, 0, deck), (x1, 0, 0.15))]
    for a, b in pieces:
        fair.beam(kit, a, b, 1.3, accent, depth=0.2, caps=len(pieces) == 1)
        for sy in (-1, 1):
            fair.beam(
                kit,
                (a[0], sy * 0.65, a[2] + 0.25),
                (b[0], sy * 0.65, b[2] + 0.25),
                0.3,
                pal["roof"],
                depth=0.4,
                caps=len(pieces) == 1,
            )
    add(kit, "detail", "tin", 0, supports=(floor,), collider="hull")

    # --- the ladder, up the front ---
    kit = Kit()
    foot_y = -HALF - 1.0
    for sx in (-1, 1):
        fair.beam(kit, (tx + sx * 0.5, foot_y, 0), (tx + sx * 0.5, -HALF, deck + 0.7), BAR, pal["trim"], flat=True)
    for n in range(3):
        f = (n + 1) / 4.0
        y = foot_y + (1.0) * f * deck / (deck + 0.7)
        z = deck * f
        kit.box((tx - 0.5, y - 0.12, z - 0.12), (tx + 0.5, y + 0.12, z + 0.12), accent, skip=("-x", "+x"))
    add(kit, "detail", "wood", 0, supports=(floor,), collider="hull")

    # --- monkey bars, out to a pair of end posts ---
    bx0 = tx - HALF
    bx1 = bx0 - bars_len
    kit = Kit()
    for sy in (-1, 1):
        kit.box((bx1 - POST, sy * 0.85 - POST, 0), (bx1 + POST, sy * 0.85 + POST, bars_z + 0.15), frame_colour, skip=("-z",))
    end = add(kit, "pillar", "wood", 0)

    kit = Kit()
    for sy in (-1, 1):
        kit.box((bx1, sy * 0.85 - BAR / 2, bars_z - BAR / 2), (bx0, sy * 0.85 + BAR / 2, bars_z + BAR / 2), pal["trim"], skip=("-x", "+x"))
    for n in range(rungs):
        x = bx1 + (n + 0.5) * bars_len / rungs
        kit.box((x - 0.11, -0.85, bars_z - 0.11), (x + 0.11, 0.85, bars_z + 0.11), accent, skip=("-y", "+y"))
    add(kit, "detail", "tin", 1, supports=(end, posts[-1, -1], posts[-1, 1]))

    # --- the back of the tower: a safety panel, or a climbing wall with holds ---
    kit = Kit()
    if back == "panel":
        kit.box((tx - HALF + 0.32, HALF - 0.25, deck), (tx + HALF - 0.32, HALF - 0.05, deck + 1.0), pal["roof"])
        panel_y(kit, tx - 0.35, tx + 0.35, deck + 0.3, deck + 0.75, HALF - 0.03, 1, "windowBlue")
        add(kit, "detail", "wood", 1, supports=(floor,))
    else:
        fair.beam(kit, (tx, HALF + 1.1, 0), (tx, HALF, deck), 2.0, pal["roof"], depth=0.25, flat=True)
        lean = 1.1 / deck
        for n, (dx, f) in enumerate(((-0.5, 0.25), (0.45, 0.4), (-0.2, 0.62), (0.5, 0.8))):
            z = deck * f
            y = HALF + 1.1 - lean * z + 0.2
            kit.box((tx + dx - 0.15, y, z - 0.12), (tx + dx + 0.15, y + 0.14, z + 0.12), BRIGHT[(n + seed) % len(BRIGHT)], skip=("-y",))
        add(kit, "detail", "wood", 0, supports=(floor,), collider="hull")

    # --- a rail at the front, either side of the ladder ---
    kit = Kit()
    for sx in (-1, 1):
        xa, xb = sorted((tx + sx * 0.65, tx + sx * (HALF - 0.32)))
        kit.box((xa, -HALF + 0.05, deck + 0.75), (xb, -HALF + 0.25, deck + 1.0), pal["trim"])
    add(kit, "detail", "wood", 1, supports=(floor,))

    return building.finish(
        look=f"deck={deck} {roof}/{back}/bars-{bars_len}x{rungs}/flip{flip:+d}" + ("/wavy" if wavy else "")
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(13, 12))


if __name__ == "__main__":
    previews()
