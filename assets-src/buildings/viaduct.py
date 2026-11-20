"""Viaduct generator: the tall arched stone bridge of the wizard school.

A grey stone bridge about 24 m long (along X) and 4 m wide, 8-9 m to the
deck, on three tall arches (or four narrower ones). The piers have pointed
cutwaters up and down stream; a white string course runs under a parapet
with a dark slate coping line on each side. Some seeds roof the deck over as
a covered bridge: timber posts under a dark pitched roof.

The space under the arches is open: the piers are the only pieces at ground
level, and the arches spring 4 m or more up, at least 6 m clear at the crown.
The piers (and the end abutments) are the storey-0 "pillar" modules. Each
arch is two halves, each resting on its own pier; each span of deck rests on
its two halves, and the parapets (and roof) rest on the deck.

The seed varies the deck height, the arch layout (three even arches, a wide
middle arch, or four arches), round or pointed arches, the coping colour, the
covered roof, end pinnacles and the lamps.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/viaduct.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_castle2 as castle  # noqa: E402
from lib import shapes_wizard as wiz  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "viaduct"
HITS_TO_COLLAPSE = 2  # medium structure
TRIANGLE_BUDGET = 1300

HALF_W = 2.0  # 4 m wide
END = 1.6  # abutment width at each end
LAYOUTS = {
    "three": [-12.0, -4.0, 4.0, 12.0],
    "wide": [-12.0, -5.2, 5.2, 12.0],
    "four": [-12.0, -6.0, 0.0, 6.0, 12.0],
}


def build(building_id, seed, scheme=None, collection=None):
    """Build one viaduct. Returns (empty, stats)."""
    rng = random.Random(seed)

    deck_z = rng.choice([8.0, 8.5, 9.0])
    layout = rng.choice(["three", "three", "wide", "four"])
    head = rng.choice(["round", "round", "pointed"])
    coping = rng.choice(wiz.SLATES)
    covered = (False, True)[seed % 2]  # alternated, so neighbouring seeds differ
    pinnacles = rng.random() < 0.6
    lamps = rng.random() < 0.5
    gold = rng.choice(wiz.GOLDS)
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    lines = LAYOUTS[layout]
    pier_half = 0.8 if layout != "four" else 0.7
    slab = 0.5
    z_top = deck_z - slab  # top of the arch masonry, under the deck slab
    crown = z_top - 0.4

    # --- piers and abutments: the only pieces on the ground ---
    pier_ids = []
    faces = []  # (x_lo, x_hi) of each pier's face to the arches
    for k, x in enumerate(lines):
        end = k in (0, len(lines) - 1)
        if end:
            sign = -1 if k == 0 else 1
            x0, x1 = sorted((x, x - sign * END))
        else:
            x0, x1 = x - pier_half, x + pier_half
        faces.append((x0, x1))
        pier_ids.append((Kit(), x0, x1, end))

    spans = []
    for k in range(len(lines) - 1):
        left = faces[k][1]
        right = faces[k + 1][0]
        spans.append((left, right))
    widest = max(b - a for a, b in spans)

    def spring_of(width):
        half = width / 2
        rise = half * (1.25 if head == "pointed" else 1.0)
        return crown - rise

    # Every arch shares one crown height, so narrower arches spring higher.
    ids = []
    for k, (kit, x0, x1, end) in enumerate(pier_ids):
        neighbours = [spans[j] for j in (k - 1, k) if 0 <= j < len(spans)]
        spring = max(spring_of(b - a) for a, b in neighbours)
        kit.box((x0, -HALF_W, 0), (x1, HALF_W, spring), "stone", skip=("-z",))
        if not end:
            # Pointed cutwaters up and down stream, with a sloping cap.
            for sy in (-1, 1):
                y0 = sy * HALF_W
                tip = sy * (HALF_W + 1.0)
                points = [(x0, y0), (x1, y0), ((x0 + x1) / 2, tip)]
                low = [(px, py, 0) for px, py in points]
                high = [(px, py, spring * 0.6) for px, py in points]
                apex = ((x0 + x1) / 2, y0, spring * 0.6 + 1.2)
                kit.convex([low, [low[0], low[1], high[1], high[0]], [low[1], low[2], high[2], high[1]], [low[2], low[0], high[0], high[2]]], "stone")
                kit.convex([high, [high[0], high[1], apex], [high[1], high[2], apex], [high[2], high[0], apex]], "stone", {0: "stone"})
        else:
            kit.box((x0, -HALF_W - 0.3, 0), (x1, HALF_W + 0.3, 0.6), "stone", skip=("-z",))
        ids.append(add(kit, "pillar", "stone", 0))

    # --- the arches: two halves each, each on its own pier ---
    halves = []
    for k, (a, b) in enumerate(spans):
        mid = (a + b) / 2
        x_open = (b - a) / 2
        spring = spring_of(b - a)
        pair = []
        for side, pier in ((-1, k), (1, k + 1)):
            pa, pb = faces[pier]
            # Reach over this pier: half of it, or all of an abutment.
            if pier in (0, len(lines) - 1):
                reach = (pb - pa)
            else:
                reach = (pb - pa) / 2
            # The pier under this half might spring lower (beside a wider arch): fill down to its top.
            pier_spring = max(spring_of(bb - aa) for aa, bb in [spans[j] for j in (pier - 1, pier) if 0 <= j < len(spans)])
            kit = Kit()
            castle.arch_half(kit, side, x_open, x_open + reach, -HALF_W, HALF_W, spring, crown, z_top, "stone", trim="trimWhite", steps=3, pointed=head == "pointed", ring=0.4)
            if pier_spring < spring - 0.01:
                xs = sorted((side * x_open, side * (x_open + reach)))
                kit.box((xs[0], -HALF_W, pier_spring), (xs[1], HALF_W, spring), "stone", skip=("-z", "+z"))
            wiz.shift(kit, dx=mid)
            pair.append(add(kit, "wall", "stone", 1, supports=(ids[pier],), collider="hull"))
        halves.append(pair)

    # --- the deck: one slab per span, from pier centre to pier centre ---
    decks = []
    xs = [lines[0]] + [(faces[k][0] + faces[k][1]) / 2 for k in range(1, len(lines) - 1)] + [lines[-1]]
    for k in range(len(spans)):
        x0, x1 = xs[k], xs[k + 1]
        kit = Kit()
        kit.box((x0, -HALF_W - 0.3, z_top), (x1, HALF_W + 0.3, deck_z), "trimWhite", sides={"+z": "stone"})
        decks.append(add(kit, "floor", "stone", 2, supports=halves[k]))

    # --- parapets with a dark coping line, or a covered timber gallery ---
    rails = []
    for k in range(len(spans)):
        x0, x1 = xs[k], xs[k + 1]
        side_ids = []
        for sy in (-1, 1):
            y_out = sy * (HALF_W + 0.25)
            y_in = sy * (HALF_W - 0.1)
            ya, yb = sorted((y_out, y_in))
            kit = Kit()
            kit.box((x0, ya, deck_z), (x1, yb, deck_z + 0.85), "stone", skip=("-z",))
            kit.box((x0, ya - 0.08, deck_z + 0.85), (x1, yb + 0.08, deck_z + 1.1), coping, skip=("-z",))
            if covered:
                n = 3 if x1 - x0 > 5 else 2
                for j in range(n + 1):
                    px = x0 + 0.2 + (x1 - x0 - 0.4) * j / n
                    kit.box((px - 0.16, (ya + yb) / 2 - 0.16, deck_z + 1.1), (px + 0.16, (ya + yb) / 2 + 0.16, deck_z + 3.2), "wood", skip=("-z", "+z"))
            side_ids.append(add(kit, "wall", "stone", 3, supports=(decks[k],)))
        rails.append(side_ids)
        if covered:
            z0 = deck_z + 3.2
            kit = Kit()
            reach = HALF_W + 0.7
            kit.box((x0, -HALF_W - 0.1, z0 - 0.25), (x1, HALF_W + 0.1, z0), "wood")
            kit.extrude_x([(-reach, z0 - 0.1), (reach, z0 - 0.1), (0, z0 + 2.4)], x0, x1, coping)
            add(kit, "roof", "tile", 4, supports=side_ids, collider="hull")

    # --- pinnacles or lamps at the ends ---
    for k, x in ((0, lines[0] + 0.5), (len(spans) - 1, lines[-1] - 0.5)):
        if not (pinnacles or lamps):
            break
        kit = Kit()
        for sy in (-1, 1):
            y = sy * (HALF_W + 0.05)
            if pinnacles:
                wiz.pinnacle(kit, x, y, deck_z + 1.1, 0.35, 0.9, 2.2, "stone", coping, gold)
            else:
                kit.box((x - 0.1, y - 0.1, deck_z + 1.1), (x + 0.1, y + 0.1, deck_z + 3.0), "tyre", skip=("-z",))
                kit.box((x - 0.3, y - 0.3, deck_z + 3.0), (x + 0.3, y + 0.3, deck_z + 3.6), "sunny")
                wiz.cone_part(kit, 0.42, 0.0, deck_z + 3.6, deck_z + 4.1, "tyre", 4, cx=x, cy=y)
        add(kit, "detail", "stone", 3, supports=rails[k])

    return building.finish(look=f"deck{deck_z} {layout}/{head} coping-{coping} covered-{covered} pinnacles-{pinnacles} lamps-{lamps} widest{widest:.1f}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(30, 16), columns=2)


if __name__ == "__main__":
    previews()
