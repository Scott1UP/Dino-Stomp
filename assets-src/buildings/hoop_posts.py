"""Hoop posts generator: the three tall goal posts of the wizard school's sports pitch.

Three thick bright poles, 12-16 m tall and all different heights (the rings
add about 3 m more), each on a small stepped stone base and each topped by a big chunky open ring about
3 m across. They stand in a row about 10 m long (along X), facing -Y.

Each post (base and pole) is one module on the ground; its ring is a
separate module resting on it, so knocking a post brings its ring down.

The seed varies which post is tallest, the heights, the ring size, the pole
colours (two-tone bands), the ring colour, and whether the row is straight
or the middle post stands back.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/hoop_posts.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_wizard as wiz  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "hoop_posts"
HITS_TO_COLLAPSE = 1  # light structure
TRIANGLE_BUDGET = 400

POLES = ["cobalt", "tomato", "bubblegum", "tangerine"]
SPACING = 4.6


def build(building_id, seed, scheme=None, collection=None):
    """Build one set of hoop posts. Returns (empty, stats)."""
    rng = random.Random(seed)

    heights = [12.0, 14.0, 16.0]
    rng.shuffle(heights)
    heights = [max(12.0, h + rng.choice([-0.5, 0.0, 0.0])) for h in heights]
    ring_r = rng.choice([1.35, 1.5])  # to the middle of the rim: about 3 m across
    thick = rng.choice([0.4, 0.46])
    pole_r = rng.choice([0.34, 0.38])  # 8-sided, so 0.6-0.7 m thick
    main = rng.choice(POLES)
    band = rng.choice(["trimWhite", "sunny"] + [c for c in POLES if c != main])
    ring_colour = rng.choice(["starGold", "sunny", "starGold"])
    layout = ("straight", "arc")[seed % 2]  # alternated, so neighbouring seeds differ
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    for k, height in enumerate(heights):
        x = (k - 1) * SPACING
        y = 1.4 if layout == "arc" and k == 1 else (-0.4 if layout == "arc" else 0.0)
        top = height  # the pole is 12-16 m; the ring sits on top of it
        kit = Kit()
        kit.box((x - 0.85, y - 0.85, 0), (x + 0.85, y + 0.85, 0.45), "stone", skip=("-z",))
        kit.box((x - 0.6, y - 0.6, 0.45), (x + 0.6, y + 0.6, 0.8), "trimWhite", skip=("-z",))
        split = 0.8 + (top - 0.8) * 0.5
        wiz.pole_ngon(kit, x, y, 0.8, split, pole_r, main, top=False)
        wiz.pole_ngon(kit, x, y, split, top, pole_r * 0.92, band if k % 2 else main, top=True)
        post = add(kit, "wall", "wood", 0, collider="hull")

        kit = Kit()
        wiz.upright_ring(kit, x, y, top + ring_r + thick / 2 - 0.05, ring_r, thick, ring_colour)
        add(kit, "detail", "wood", 1, supports=(post,), collider="hull")

    return building.finish(look=f"heights{[round(h, 1) for h in heights]} ring{ring_r} {main}/{band}/{ring_colour} {layout}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(24, 0), columns=6)


if __name__ == "__main__":
    previews()
