"""Billboard generator.

Two chunky posts holding up a big board, about 6 m wide and 6 m tall, with a
bright picture made of a few flat shapes (never words): a sun over hills, an
ice cream, a fish or a balloon. Two modules: the posts, and the board that
drops when they go. The seed picks the picture, the board's size and frame
colour, and the lamps along the top.

    blender --background --factory-startup --python assets-src/props/billboard.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import beam, flat, pictogram, polygon  # noqa: E402

TYPE = "billboard"
KIND = "prop"
TRIANGLE_BUDGET = 150
SPACING = (10, 9)

PICTURES = ("sun", "cone", "fish", "balloon")
BACKDROP = {"sun": "cobalt", "cone": "sunny", "fish": "glassTint", "balloon": "leaf"}


def build(building_id, seed, scheme=None, collection=None):
    """Build one billboard. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    picture = PICTURES[seed % len(PICTURES)]  # cycled, so neighbouring seeds always differ
    width = rng.choice([5.6, 6.0, 6.4])
    board_h = rng.choice([2.9, 3.2, 3.5])
    top = rng.choice([5.8, 6.0, 6.2])
    frame = rng.choice(["trimWhite", "tomato", "tyre"])
    post = rng.choice(["wood", "stone", "tyre"])
    lamps = rng.choice([0, 2, 3])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    z0 = top - board_h
    half = width / 2
    post_x = half - 1.1

    # --- the posts, braced behind ---
    kit = Kit()
    for sx in (-1, 1):
        kit.box((sx * post_x - 0.2, 0.0, 0), (sx * post_x + 0.2, 0.4, top - 0.4), post, skip=("-z",))
        beam(kit, (sx * post_x, 1.5, 0.1), (sx * post_x, 0.4, z0 - 0.2), 0.3, post, caps=False)
    kit.box((-post_x, 0.1, z0 - 0.75), (post_x, 0.34, z0 - 0.45), post, skip=("-x", "+x"))
    posts = building.add(kit, "detail", "wood", 0, collider="hull")

    # --- the board and its picture ---
    face = -0.25
    kit = Kit()
    kit.box((-half, face, z0), (half, 0.0, top), frame, sides={"+y": "wood"})
    b = 0.22
    centre = (0, face, (z0 + top) / 2)
    w, h = half - b, board_h / 2 - b

    def draw(points, colour, layer=1):
        flat(kit, centre, (0, -1, 0), points, colour, lift=0.02 + 0.02 * layer)

    draw([(-w, -h), (w, -h), (w, h), (-w, h)], BACKDROP[picture], 0)
    if picture == "sun":
        draw(polygon(h * 0.42, 8, cx=w * 0.45, cy=h * 0.35), "sunny")
        draw([(-w, -h), (-w * 0.1, -h), (-w * 0.55, h * 0.2)], "leaf")
        draw([(-w * 0.5, -h), (w, -h), (w, -h * 0.55), (w * 0.2, -h * 0.05)], "hedge", 2)
    elif picture == "balloon":
        draw(polygon(h * 0.55, 8, cx=-w * 0.3, cy=h * 0.25, squash=1.15), "tomato")
        draw([(-w * 0.3 - 0.05, -h * 0.9), (-w * 0.3 + 0.05, -h * 0.9), (-w * 0.3 + 0.05, -h * 0.35), (-w * 0.3 - 0.05, -h * 0.35)], "trimWhite")
        draw(polygon(h * 0.4, 8, cx=w * 0.35, cy=-h * 0.05, squash=1.15), "sunny")
        draw(polygon(h * 0.3, 8, cx=w * 0.72, cy=h * 0.5, squash=1.15), "bubblegum")
    else:
        if picture == "cone":
            draw([(-w, -h), (w, -h), (w, -h * 0.45), (-w, -h * 0.45)], "tomato")
        pictogram(kit, picture, centre, (0, -1, 0), board_h * 0.86, lift=0.06)

    # --- lamps peering over the top ---
    for i in range(lamps):
        x = (i - (lamps - 1) / 2) * (width / (lamps + 0.5))
        kit.box((x - 0.3, face - 0.55, top), (x + 0.3, 0.0, top + 0.25), "sunny", sides={"+z": "tyre"})
    building.add(kit, "detail", "wood", 1, supports=(posts,))

    return building.finish(look=f"{picture} {width}x{board_h} top={top} frame={frame} lamps={lamps}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=SPACING)


if __name__ == "__main__":
    previews()
