"""Spire tower generator: the signature tower of the wizard school.

A slender grey stone tower, 4-5.5 m across, four or five storeys of about
3.5 m, under a very tall, steep dark slate spire (6-10 m) with a gold finial
and a pennant. Tall narrow pointed windows glow warm on every storey, front
and back. Partway up there is a balcony ring on corbels, or a plain corbelled
band.

The seed picks the plan (eight-sided or square), the girth, the number of
storeys, the balcony, the top (a plain spire, a top storey corbelled out
wider, or a spire ringed with little spirelets), the spire's height and slate,
a slender stair turret with its own needle spire up one side, and the pennant.

Each storey is its own ring of wall pieces (four of two facets, or four
walls), resting on the storey below, so the tower topples storey by storey.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/spire_tower.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_castle2 as castle  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib import shapes_wizard as wiz  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "spire_tower"
HITS_TO_COLLAPSE = 3  # tall landmark
TRIANGLE_BUDGET = 1300

WALL = 0.45
BAND = 0.24


def build(building_id, seed, scheme=None, collection=None):
    """Build one spire tower. Returns (empty, stats)."""
    rng = random.Random(seed)

    plan = ("round", "square", "round")[seed % 3]  # cycled, so neighbouring seeds differ
    across = rng.choice([4.0, 4.4, 4.8, 5.2])
    storeys = rng.choice([4, 4, 5])
    storey_h = rng.choice([3.3, 3.4, 3.5])
    balcony = rng.choice(["balcony", "balcony", "corbel"])
    balcony_at = rng.choice([2, 3]) if storeys == 5 else 2
    top = rng.choice(["plain", "flared", "spirelets"])
    tip = rng.choice([23.0, 24.5, 26.0])
    slate = rng.choice(wiz.SLATES)
    turret = rng.choice([None, "left", "right", None, "right"])
    gold = rng.choice(wiz.GOLDS)
    pennant = rng.choice(["tomato", "cobalt", "sunny", "bubblegum"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    half = across / 2
    r = half / math.cos(math.pi / 8)  # corner radius of the octagon
    round_plan = plan == "round"
    win_w = 0.62 if across < 4.8 else 0.72

    def storey_size(s):
        """Corner radius (round) or half-width (square) of storey s."""
        grow = 0.45 if top == "flared" and s == storeys - 1 else 0.0
        return (r if round_plan else half) + grow

    # --- walls: one ring of four pieces a storey ---
    rings = []
    maps = []  # per storey: facet or wall name -> module id
    below = {}
    for s in range(storeys):
        z0 = s * storey_h
        z1 = z0 + storey_h
        size = storey_size(s)
        flared_top = top == "flared" and s == storeys - 1
        here = {}
        if round_plan:
            for q in range(4):
                facets = [(2 * q + s) % 8, (2 * q + s + 1) % 8]
                kit = Kit()
                for i in facets:
                    shapes.wall_segment(kit, i, size, size - WALL, z0, z1, "stone", "interiorCream")
                    frame = shapes.facet_frame(i, size)
                    if s == 0 and i == 0:
                        wiz.pointed_door(kit, frame, 0, 1.3, 2.6, "doorBrown")
                    elif s == 0 and i in (1, 7):
                        pass
                    elif (i + s) % 2 == 0 or flared_top:
                        glass, shine = wiz.pane(rng)
                        wiz.lancet(kit, frame, 0, z0 + 0.7, win_w, storey_h - 1.35, glass=glass, shine=shine)
                supports = sorted({below[i] for i in facets}) if below else ()
                module = add(kit, "wall", "stone", s, supports=supports, collider="hull")
                for i in facets:
                    here[i] = module
        else:
            frames = castle.rect_frames(0, 0, size, size)
            for name in ("front", "back", "left", "right"):
                frame = frames[name]
                kit = Kit()
                castle.box_wall(kit, frame, name, size, size, z0, z1, WALL)
                if s == 0 and name == "front":
                    wiz.pointed_door(kit, frame, 0, 1.4, 2.7, "doorBrown")
                else:
                    pair = across >= 4.6 or flared_top
                    for u in ((-0.75, 0.75) if pair else (0.0,)):
                        glass, shine = wiz.pane(rng)
                        wiz.lancet(kit, frame, u, z0 + 0.7, win_w * 0.9, storey_h - 1.35, glass=glass, shine=shine)
                supports = (below[name],) if below else ()
                here[name] = add(kit, "wall", "stone", s, supports=supports)
        below = here
        maps.append(here)
        rings.append(sorted(set(here.values())))

        if s == storeys - 1:
            break
        # --- between storeys: a white band, the balcony, or a corbel stepping out ---
        nxt = storey_size(s + 1)
        out = max(size, nxt)
        kit = Kit()
        if s + 1 == balcony_at or nxt > size:
            reach = out + (0.85 if s + 1 == balcony_at and balcony == "balcony" else 0.3)
            if round_plan:
                wiz.drum(kit, size, reach, z1 - 0.9, z1 - BAND, "stone", cap_top=False)
                wiz.band_ring(kit, reach, z1 - BAND, z1)
            else:
                wiz.corbel_square(kit, size, reach, z1 - 0.9, z1 - BAND)
                wiz.band_box(kit, -reach, -reach, reach, reach, z1 - BAND, z1)
            floor = add(kit, "floor", "stone", s + 1, supports=rings[s], collider="hull")
            if s + 1 == balcony_at and balcony == "balcony":
                # A parapet round the walkway, in two halves.
                for part in (0, 1):
                    kit = Kit()
                    if round_plan:
                        for i in range(part * 4, part * 4 + 4):
                            shapes.wall_segment(kit, i, reach, reach - 0.22, z1, z1 + 0.9, "stone", top="trimWhite")
                    else:
                        tf = castle.rect_frames(0, 0, reach, reach)
                        for name in (("front", "left") if part == 0 else ("back", "right")):
                            castle.box_wall(kit, tf[name], name, reach, reach, z1, z1 + 0.9, 0.22)
                    add(kit, "detail", "stone", s + 1, supports=(floor,), collider="hull" if round_plan else "box")
        else:
            band = out + 0.14
            if round_plan:
                wiz.band_ring(kit, band, z1 - BAND, z1)
            else:
                wiz.band_box(kit, -band, -band, band, band, z1 - BAND, z1)
            add(kit, "floor", "stone", s + 1, supports=rings[s], collider="hull" if round_plan else "box")

    # --- eaves deck on top of the walls ---
    height = storeys * storey_h
    size = storey_size(storeys - 1)
    eave = size + 0.35
    kit = Kit()
    if round_plan:
        wiz.drum(kit, size, eave, height - 0.5, height, "stone", cap_top=False)
        wiz.band_ring(kit, eave, height, height + 0.3)
    else:
        wiz.corbel_square(kit, size, eave, height - 0.5, height)
        wiz.band_box(kit, -eave, -eave, eave, eave, height, height + 0.3)
    deck = add(kit, "floor", "stone", storeys, supports=rings[-1], collider="hull")
    deck_z = height + 0.3

    # --- the spire, in two pieces: a lower part and a tip ---
    sides = 8 if round_plan else 4
    spire_r = (eave + 0.12) if round_plan else (eave + 0.1) * math.sqrt(2)
    if top == "spirelets":
        spire_r *= 0.78
    tip_z = min(max(tip, deck_z + 7.5), deck_z + 10.0)
    cut = 0.45
    split_z = deck_z + (tip_z - deck_z) * cut
    # The lower part: kick at the eaves, then straight up to the split.
    kit = Kit()
    wiz.kicked_spire(kit, spire_r, deck_z, tip_z, slate, sides, cut=split_z, part="lower")
    lower = add(kit, "roof", "tile", storeys + 1, supports=(deck,), collider="hull")
    kit = Kit()
    wiz.kicked_spire(kit, spire_r, deck_z, tip_z, slate, sides, cut=split_z, part="upper")
    wiz.finial(kit, 0, 0, tip_z - 0.25, size=1.1, colour=gold)
    upper = add(kit, "roof", "tile", storeys + 2, supports=(lower,), collider="hull")

    kit = Kit()
    shapes.flag(kit, 0, 0, tip_z + 0.9, 1.9, pennant, size=1.4, thick=0.07)
    add(kit, "detail", "wood", storeys + 3, supports=(upper,))

    # --- little spirelets round the spire's foot ---
    if top == "spirelets":
        at = (eave - 0.5) if round_plan else (eave - 0.45) * math.sqrt(2)
        corners = [shapes.polar(at, deg)[:2] for deg in (-45, 135, -135, 45)]
        spots = corners[:2], corners[2:]
        for pair in spots:
            kit = Kit()
            for x, y in pair:
                kit.box((x - 0.4, y - 0.4, deck_z), (x + 0.4, y + 0.4, deck_z + 1.3), "stone", skip=("-z",))
                wiz.cone_part(kit, 0.62, 0.0, deck_z + 1.3, deck_z + 5.2, slate, 4, cx=x, cy=y)
                wiz.finial(kit, x, y, deck_z + 5.0, size=0.5, colour=gold, stem=False)
            add(kit, "roof", "tile", storeys + 1, supports=(deck,), collider="hull")

    # --- a slender stair turret up one side, with its own needle spire ---
    if turret:
        sx = -1 if turret == "left" else 1
        tr = 0.95
        if round_plan:
            cx, cy = sx * (half + 0.55), 0.35
        else:
            cx, cy = sx * (half + 0.5), 0.4
        levels = storeys - 1
        lowest = None
        for s in range(levels):
            z0, z1 = s * storey_h, (s + 1) * storey_h
            kit = Kit()
            wiz.drum(kit, tr, tr, z0, z1, "stone", sides=6, cx=cx, cy=cy, top="interiorCream", bottom="interiorCream")
            if s % 2 == 1:
                f = shapes.facet_frame(1 if sx > 0 else 5, tr, sides=6, cx=cx, cy=cy)
                wiz.lancet(kit, f, 0, z0 + 0.9, 0.36, 1.4, rim=0.08, glass=wiz.LIT, shine=None)
            holder = maps[s][(2 if sx > 0 else 6) if round_plan else ("right" if sx > 0 else "left")]
            lowest = add(kit, "detail", "stone", s, supports=(holder, lowest) if lowest else (holder,), collider="hull")
        zt = levels * storey_h
        kit = Kit()
        wiz.band_ring(kit, tr + 0.2, zt, zt + 0.25, sides=6, cx=cx, cy=cy)
        wiz.cone_part(kit, tr + 0.25, 0.0, zt + 0.25, zt + 5.0, slate, 6, cx=cx, cy=cy)
        wiz.finial(kit, cx, cy, zt + 4.8, size=0.6, colour=gold, stem=False)
        add(kit, "roof", "tile", levels, supports=(lowest,), collider="hull")

    return building.finish(
        look=f"{plan} {across}m x{storeys}@{storey_h} {balcony}@{balcony_at} top-{top}/{slate} tip{tip_z:.1f} turret-{turret}"
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(11, 0), columns=6)


if __name__ == "__main__":
    previews()
