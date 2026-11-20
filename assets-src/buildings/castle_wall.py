"""Castle wall section generator.

One section of toy castle wall, 8 m long, 1.6 m thick and 5 m high to the top
of its battlements. It is built from big stone blocks in two courses (laid
like bricks, so the joints never line up) with a row of merlons on top. The
seed varies the block layout, the merlons (number, full-depth blocks or
parapets front and back, flat or pointed caps), the arrow slits, and a bright
banner, shield or flag.

On top of that it dresses the wall: buttresses or a sloped plinth at the foot,
a string course where the two courses meet, a timber walkway on posts along
the inside (+Y) face, wall torches, little shields on the merlons, and now and
then a wooden hoarding hanging out over the front.

Sections tile end to end along X. The buttresses and plinth stand about 0.5 m
proud of the front face and the walkway 1.1 m proud of the inside face.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/castle_wall.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_castle2 as castle  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "castle_wall"
HITS_TO_COLLAPSE = 1  # one good hit breaks a section
TRIANGLE_BUDGET = 600

LENGTH = 8.0
THICK = 1.6
HEIGHT = 5.0
FOOT = 0.18  # how far the lower course steps out
WALK = 1.1  # how far the timber walkway stands off the inside face
BRIGHTS = ["tomato", "sunny", "cobalt"]


def build(building_id, seed, scheme=None, collection=None):
    """Build one wall section. Returns (empty, stats)."""
    rng = random.Random(seed)

    lower_count = rng.choice([3, 4])
    split = rng.choice([1.9, 2.2, 2.5])  # height of the lower course
    body = rng.choice([3.7, 3.9, 4.1])  # height of the wall walk
    merlon_count = rng.choice([3, 4, 4])
    merlon_style = rng.choice(["full", "full", "parapets"])
    cap_style = rng.choice(["flat", "trim", "pointed"])
    slit_style = rng.choice(["cross", "plain", "none"])
    feature = rng.choice(["banner", "banner", "shield", "two banners"])
    colour = rng.choice(BRIGHTS)
    second = rng.choice([c for c in BRIGHTS if c != colour])
    with_flag = rng.random() < 0.5
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme

    # The dressing has its own stream, so the walls keep the looks their seeds always had.
    extra = random.Random(seed * 7919 + 13)
    base_style = extra.choice(["buttress", "plinth", "buttress"])
    course_colour = extra.choice(["trimWhite", "trimWhite", "doorBrown"])
    walkway = extra.random() < 0.75
    hoarding = extra.random() < 0.34
    merlon_shields = extra.random() < 0.4

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    x0 = -LENGTH / 2
    half = THICK / 2
    front = shapes.Frame((0, -half, 0), -90)
    rear = shapes.Frame((0, half, 0), 90)

    def spans(count):
        return [(x0 + LENGTH * k / count, x0 + LENGTH * (k + 1) / count) for k in range(count)]

    def resting_on(xa, xb, below):
        """The modules in `below` (id, xa, xb) that overlap this stretch of wall."""
        return [m for m, ma, mb in below if ma < xb - 0.05 and mb > xa + 0.05]

    # --- lower course: big blocks with a stepped-out foot and a buttress, or a sloped plinth ---
    lower = []
    for xa, xb in spans(lower_count):
        kit = Kit()
        kit.box((xa, -half, 0), (xb, half, split), "stone", skip=("-z",))
        if base_style == "plinth":
            castle.batter(kit, front, xa, xb, 0, 1.3, 0.42, "stone")
            castle.batter(kit, rear, -xb, -xa, 0, 1.3, 0.42, "stone")
        else:
            kit.box((xa, -half - FOOT, 0), (xb, half + FOOT, 0.7), "stone", skip=("-z",))
            mid = (xa + xb) / 2
            castle.buttress(kit, front, mid - 0.5, mid + 0.5, 0, split * 0.5, split - 0.15, 0.55, "stone", cap="trimWhite")
        lower.append((add(kit, "wall", "stone", 0, collider="hull" if base_style == "plinth" else "box"), xa, xb))

    # --- upper course: the other number of blocks, so the joints are staggered ---
    upper_count = 7 - lower_count
    joints = [xb for _, xb in spans(upper_count)[:-1]]  # banners hang over the joints, clear of the slits
    if feature == "shield":
        feature_xs = [0.0]
    elif feature == "two banners":
        feature_xs = [joints[0], joints[-1]]
    else:
        feature_xs = [rng.choice(joints)]
    upper = []
    for index, (xa, xb) in enumerate(spans(upper_count)):
        kit = Kit()
        kit.box((xa, -half, split), (xb, half, body - 0.3), "stone")
        kit.box((xa, -half - 0.12, body - 0.3), (xb, half + 0.12, body), "trimWhite")  # coping
        # The string course, front and back.
        shapes.fbox(kit, front, (xa, 0, split), (xb, 0.1, split + 0.24), course_colour, skip=("-v", "-u", "+u"))
        shapes.fbox(kit, rear, (-xb, 0, split), (-xa, 0.1, split + 0.24), course_colour, skip=("-v", "-u", "+u"))
        mid = (xa + xb) / 2
        clear = all(abs(mid - fx) > 1.1 for fx in feature_xs)
        if slit_style != "none" and clear:
            for frame, u in ((front, mid), (rear, -mid)):
                shapes.slit(kit, frame, split + 0.45, body - 0.6, u=u, width=0.3, cross=slit_style == "cross")
        else:
            castle.torch(kit, rear, -mid, split + 0.75)  # lights the walkway
            if clear:
                castle.torch(kit, front, mid, split + 0.75)
        upper.append((add(kit, "wall", "stone", 1, supports=resting_on(xa, xb, lower)), xa, xb))

    # --- a wooden hoarding hanging out over the front, in place of the middle merlons ---
    hoard_half = 1.5
    if hoarding:
        z = body
        y_out = -half - 0.75
        y_in = half * 0.3
        kit = Kit()
        kit.box((-hoard_half, y_out, z), (hoard_half, y_in, z + 1.3), "wood", sides={"-z": "doorBrown"})
        face = shapes.Frame((0, y_out, 0), -90)
        shapes.fquad(kit, face, -0.85, 0.85, z + 0.55, z + 0.95, 0.03, "windowBlue")
        for u in (-hoard_half + 0.16, hoard_half - 0.16):
            shapes.fquad(kit, face, u - 0.16, u + 0.16, z, z + 1.3, 0.03, "doorBrown")
        kit.extrude_x([(y_out - 0.3, z + 1.3), (y_in + 0.2, z + 1.3), (y_in + 0.2, z + 2.0)], -hoard_half - 0.25, hoard_half + 0.25, colour)
        bx = 0.55 if any(0.6 < abs(fx) < 2.0 for fx in feature_xs) else 1.3
        for side in (-1, 1):
            xa, xb = sorted((side * (bx - 0.12), side * (bx + 0.12)))
            kit.extrude_x([(-half, z - 0.9), (-half, z), (y_out, z)], xa, xb, "doorBrown")
        hoard = add(kit, "detail", "wood", 2, supports=resting_on(-hoard_half, hoard_half, upper), collider="hull")

    # --- merlons ---
    pitch = LENGTH / merlon_count
    width = pitch * 0.56
    merlons = []
    for k in range(merlon_count):
        xa = x0 + pitch * k + (pitch - width) / 2
        xb = xa + width
        if hoarding and xa < hoard_half + 0.1 and xb > -hoard_half - 0.1:
            merlons.append(None)
            continue
        kit = Kit()
        rows = ((-half, half),) if merlon_style == "full" else ((-half, -half + 0.5), (half - 0.5, half))
        top = HEIGHT - {"pointed": 0.35, "trim": 0.2, "flat": 0.0}[cap_style]
        for ya, yb in rows:
            kit.box((xa, ya, body), (xb, yb, top), "stone", skip=("-z",) if cap_style == "flat" else ("-z", "+z"))
            if cap_style == "trim":
                kit.box((xa - 0.08, ya - 0.08, top), (xb + 0.08, yb + 0.08, HEIGHT), "trimWhite", skip=("-z",) if merlon_style == "parapets" else ())
            elif cap_style == "pointed":
                ym = (ya + yb) / 2
                kit.extrude_x([(ya, top), (yb, top), (ym, HEIGHT + 0.15)], xa, xb, "trimWhite")
        if merlon_shields and merlon_style == "full":
            castle.shield(kit, front, (xa + xb) / 2, body + 0.9, 0.7, (colour, second)[k % 2], "trimWhite", v=0.06)
        merlons.append(
            add(kit, "detail", "stone", 2, supports=resting_on(xa, xb, upper), collider="hull" if cap_style == "pointed" else "box")
        )

    # --- something bright: banners or a shield on the front, maybe a flag ---
    def support_at(x):
        return resting_on(x - 0.3, x + 0.3, upper)

    banner_top = body - 0.5
    if feature == "shield":
        kit = Kit()
        p = front.at
        kit.poly(
            [p(-0.75, 0.14, banner_top), p(0.75, 0.14, banner_top), p(0.75, 0.14, banner_top - 0.8), p(0, 0.14, banner_top - 1.7), p(-0.75, 0.14, banner_top - 0.8)],
            front.normal(),
            colour,
        )
        kit.poly(
            [p(-0.75, 0.11, banner_top), p(0.75, 0.11, banner_top), p(0.75, 0.11, banner_top - 0.8), p(0, 0.11, banner_top - 1.7), p(-0.75, 0.11, banner_top - 0.8)],
            front.normal(-1),
            colour,
        )
        shapes.fquad(kit, front, -0.14, 0.14, banner_top - 1.3, banner_top - 0.12, 0.17, second)
        shapes.fquad(kit, front, -0.6, 0.6, banner_top - 0.62, banner_top - 0.36, 0.17, second)
        add(kit, "detail", "wood", 1, supports=support_at(0.0))
    else:
        for x, c in zip(feature_xs, (colour, second)):
            kit = Kit()
            shapes.banner(kit, front, x, banner_top, 1.2, 2.3, c, v=0.14)
            shapes.fquad(kit, front, x - 0.3, x + 0.3, banner_top - 1.1, banner_top - 0.5, 0.17, "trimWhite")
            add(kit, "detail", "wood", 1, supports=support_at(x))

    if hoarding:
        kit = Kit()
        shapes.flag(kit, 0.0, half * 0.3 + 0.1, body + 1.9, 1.9, second, size=1.2)
        add(kit, "detail", "wood", 3, supports=(hoard,))
    elif with_flag and merlon_count == 3 and merlon_style == "full":
        kit = Kit()
        shapes.flag(kit, 0.0, 0.0, HEIGHT - 0.2, 2.6, second, size=1.4)
        add(kit, "detail", "wood", 3, supports=(merlons[1],))

    # --- a timber walkway on posts along the inside face, in two lengths ---
    if walkway:
        deck_z = split
        for xa, xb in spans(2):
            kit = Kit()
            kit.box((xa + 0.04, half, deck_z - 0.2), (xb - 0.04, half + WALK, deck_z), "wood", skip=("-y",), sides={"-z": "doorBrown"})
            for x in (xa + 0.6, xb - 0.6):
                kit.box((x - 0.13, half + WALK - 0.28, 0), (x + 0.13, half + WALK - 0.02, deck_z + 0.95), "doorBrown", skip=("-z", "+z"))
            kit.box((xa + 0.2, half + WALK - 0.26, deck_z + 0.95), (xb - 0.2, half + WALK - 0.04, deck_z + 1.13), "wood")
            add(kit, "detail", "wood", 0, supports=resting_on(xa, xb, lower))

    return building.finish(
        look=f"blocks={lower_count}+{upper_count} split={split} walk={body} merlons-{merlon_count}/{merlon_style}/{cap_style} slits-{slit_style} {feature} {base_style}"
        + ("/walkway" if walkway else "")
        + ("/hoarding" if hoarding else "")
        + ("/shields" if merlon_shields and merlon_style == "full" else "")
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(14, 12))


if __name__ == "__main__":
    previews()
