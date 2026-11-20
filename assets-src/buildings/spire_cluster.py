"""Spire cluster generator: the wizard school's crown of towers.

A tall eight-sided grey stone tower, five or six storeys, under a very tall
dark slate spire (25-35 m to the tip), with two to four slimmer towers of
different heights huddled round its foot, each under its own needle spire.
All of them glow with rows of small warm windows, front and back.

The main tower is a ring of four wall pieces a storey, each on the storey
below, with a white floor band between storeys. Each slim tower is one solid
drum a storey, on the drum below. The spires break in two (a lower part and a
tip) and the tips carry gold finials and pennants.

The seed varies the main tower's girth, storeys and spire height, whether
little spirelets ring its spire, how many slim towers there are, where they
stand, how tall each one is and whether it is six- or eight-sided, the slate
colours, and the pennants.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/spire_cluster.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib import shapes_wizard as wiz  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "spire_cluster"
HITS_TO_COLLAPSE = 3  # tall landmark
TRIANGLE_BUDGET = 1800

WALL = 0.5
BAND = 0.24

# Where the slim towers can stand round the main one: degrees from +X, anticlockwise.
LAYOUTS = {
    2: [(-150, 30), (-30, 150), (-120, 0)],
    3: [(-150, -30, 90), (-120, 0, 135), (-60, 180, 60)],
    4: [(-135, -45, 45, 135), (-160, -20, 60, 120), (-110, -70, 30, 180)],
}


def build(building_id, seed, scheme=None, collection=None):
    """Build one spire cluster. Returns (empty, stats)."""
    rng = random.Random(seed)

    across = rng.choice([5.4, 5.8, 6.2])
    storeys = rng.choice([5, 6, 6])
    storey_h = rng.choice([3.2, 3.4])
    tip = rng.choice([28.0, 31.0, 34.0])
    spirelets = rng.random() < 0.5
    slate = rng.choice(wiz.SLATES)
    count = (2, 3, 4)[seed % 3]  # cycled, so neighbouring seeds differ
    layout = rng.choice(LAYOUTS[count])
    slims = []
    for k, deg in enumerate(layout):
        slims.append(
            {
                "deg": deg + rng.choice([-10, 0, 10]),
                "r": rng.choice([1.3, 1.5, 1.7]),
                "storeys": rng.choice([2, 3, 3, 4]) if k else rng.choice([3, 4]),
                "sides": rng.choice([6, 8]),
                "rise": rng.choice([6.5, 7.5, 8.5]),
                "slate": rng.choice(wiz.SLATES),
            }
        )
    if count == 4:
        storeys = 5  # four slim towers and six storeys would run over the budget
    gold = rng.choice(wiz.GOLDS)
    pennants = [rng.choice(["tomato", "cobalt", "sunny", "bubblegum"]) for _ in range(2)]
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    half = across / 2
    r = half / math.cos(math.pi / 8)

    # --- the main tower: four wall pieces a storey ---
    rings = []
    below = {}
    for s in range(storeys):
        z0, z1 = s * storey_h, (s + 1) * storey_h
        here = {}
        for q in range(4):
            facets = [(2 * q + s) % 8, (2 * q + s + 1) % 8]
            kit = Kit()
            for i in facets:
                shapes.wall_segment(kit, i, r, r - WALL, z0, z1, "stone", "interiorCream")
                frame = shapes.facet_frame(i, r)
                if s == 0 and i == 0:
                    wiz.pointed_door(kit, frame, 0, 1.4, 2.6, "doorBrown")
                elif s > 0 or i in (2, 4, 6):
                    glass, shine = wiz.pane(rng, 0.15)
                    wiz.lancet(kit, frame, 0, z0 + 0.7, 0.62, storey_h - 1.35, glass=glass, shine=shine, rim=0.13)
            supports = sorted({below[i] for i in facets}) if below else ()
            module = add(kit, "wall", "stone", s, supports=supports, collider="hull")
            for i in facets:
                here[i] = module
        below = here
        rings.append(sorted(set(here.values())))
        if s < storeys - 1:
            kit = Kit()
            wiz.band_ring(kit, r + 0.14, z1 - BAND, z1)
            add(kit, "floor", "stone", s + 1, supports=rings[s], collider="hull")

    # --- its eaves and spire ---
    height = storeys * storey_h
    eave = r + 0.35
    kit = Kit()
    wiz.drum(kit, r, eave, height - 0.6, height, "stone", cap_top=False)
    wiz.band_ring(kit, eave, height, height + 0.3)
    deck = add(kit, "floor", "stone", storeys, supports=rings[-1], collider="hull")
    deck_z = height + 0.3

    tip_z = min(max(tip, deck_z + 9.0), deck_z + 14.0)
    spire_r = eave + 0.1 if not spirelets else eave * 0.8
    split_z = deck_z + (tip_z - deck_z) * 0.45
    kit = Kit()
    wiz.kicked_spire(kit, spire_r, deck_z, tip_z, slate, kick=0.07, knee=0.82, cut=split_z, part="lower")
    lower = add(kit, "roof", "tile", storeys + 1, supports=(deck,), collider="hull")
    kit = Kit()
    wiz.kicked_spire(kit, spire_r, deck_z, tip_z, slate, kick=0.07, knee=0.82, cut=split_z, part="upper")
    wiz.finial(kit, 0, 0, tip_z - 0.3, size=1.2, colour=gold)
    upper = add(kit, "roof", "tile", storeys + 2, supports=(lower,), collider="hull")
    kit = Kit()
    shapes.flag(kit, 0, 0, tip_z + 1.0, 2.2, pennants[0], size=1.6, thick=0.08)
    add(kit, "detail", "wood", storeys + 3, supports=(upper,))

    if spirelets:
        at = eave - 0.5
        spots = [shapes.polar(at, d)[:2] for d in (-67.5, 112.5, -157.5, 22.5)]
        for pair in (spots[:2], spots[2:]):
            kit = Kit()
            for x, y in pair:
                kit.box((x - 0.4, y - 0.4, deck_z), (x + 0.4, y + 0.4, deck_z + 1.2), "stone", skip=("-z", "+z"))
                wiz.cone_part(kit, 0.62, 0.0, deck_z + 1.2, deck_z + 5.4, slate, 4, cx=x, cy=y)
                wiz.finial(kit, x, y, deck_z + 5.2, size=0.5, colour=gold, stem=False)
            add(kit, "roof", "tile", storeys + 1, supports=(deck,), collider="hull")

    # --- the slim towers huddled round its foot ---
    tallest = None
    for k, slim in enumerate(slims):
        sr = slim["r"]
        sides = slim["sides"]
        dist = half + sr * 0.55
        cx, cy, _ = shapes.polar(dist, slim["deg"])
        n = min(slim["storeys"], storeys - 1)
        out_deg = slim["deg"]
        lowest = None
        for s in range(n):
            z0, z1 = s * storey_h, (s + 1) * storey_h
            kit = Kit()
            wiz.drum(kit, sr, sr, z0, z1, "stone", sides=sides, cx=cx, cy=cy, top="interiorCream", bottom="interiorCream")
            # Windows on the two facets facing out (one towards the front, one to the back when it can).
            for turn in ((-1, 1)[(s + k) % 2],) if s else (0,):
                facet = round((out_deg + 90 + turn * 360 / sides) * sides / 360) % sides
                frame = shapes.facet_frame(facet, sr, sides=sides, cx=cx, cy=cy)
                width = min(0.5, shapes.side_length(sr, sides) * 0.45)
                wiz.lancet(kit, frame, 0, z0 + 0.8, width, storey_h - 1.55, rim=0.1, glass=wiz.LIT, shine=None)
            if s == n - 1:
                wiz.band_ring(kit, sr + 0.12, z1 - 0.2, z1, sides=sides, cx=cx, cy=cy)
            lowest = add(kit, "wall", "stone", s, supports=(lowest,) if lowest else (), collider="hull")
        top_z = n * storey_h
        kit = Kit()
        wiz.kicked_spire(kit, sr + 0.3, top_z, top_z + slim["rise"], slim["slate"], sides, cx=cx, cy=cy, kick=0.07, knee=0.82)
        wiz.finial(kit, cx, cy, top_z + slim["rise"] - 0.2, size=0.7, colour=gold, stem=False)
        roof = add(kit, "roof", "tile", n, supports=(lowest,), collider="hull")
        if tallest is None or top_z > tallest[0]:
            tallest = (top_z + slim["rise"], roof, cx, cy)

    # A pennant on the tallest slim spire too.
    z, roof, cx, cy = tallest
    kit = Kit()
    shapes.flag(kit, cx, cy, z + 0.4, 1.6, pennants[1], size=1.2, thick=0.06)
    add(kit, "detail", "wood", storeys, supports=(roof,))

    return building.finish(
        look=f"{across}m x{storeys}@{storey_h} tip{tip_z:.1f}/{slate} spirelets-{spirelets} slims-{count}:"
        + ",".join(f"{m['storeys']}s{m['sides']}" for m in slims)
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(16, 0), columns=6)


if __name__ == "__main__":
    previews()
