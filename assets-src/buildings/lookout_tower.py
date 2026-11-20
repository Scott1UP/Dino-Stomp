"""Lookout tower generator: a forest landmark.

A ranger's lookout about 18 m tall: a square cabin with big windows all round
and a wrap-around balcony, under a bright roof with a flag, standing on four
tall braced timber legs. Zig-zag stairs climb the front from landing to
landing.

The seed varies the legs (three or four tiers, how far they splay, their
colour), the bracing (crosses or zig-zags), the roof (pyramid, or a ridge
either way), the cabin's size, which way the stairs start and the flag.

How it comes down: the legs are role "pillar", one module per tier, each
resting on the one below. Each quarter of the deck rests on the top of a leg,
the cabin and railings on the deck and the roof on the cabin, so breaking the
legs brings the cabin down.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/lookout_tower.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_fair as fair  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import beam, wall_y  # noqa: E402
from lib.shapes_castle2 import pyramid  # noqa: E402
from lib.shapes_forest import railing, roof_halves  # noqa: E402
from lib.shapes_town2 import flag  # noqa: E402

TYPE = "lookout_tower"
HITS_TO_COLLAPSE = 3  # landmark
TRIANGLE_BUDGET = 1300

DECK = 0.3
WALL = 0.3
CABIN_H = 2.7
LEGS = ((-1, -1), (1, -1), (1, 1), (-1, 1))
FACES = ((0, 1), (1, 2), (2, 3), (3, 0))  # front, right, back, left


def build(building_id, seed, scheme=None, collection=None):
    """Build one lookout tower. Returns (empty, stats)."""
    rng = random.Random(seed)

    tiers = rng.choice([3, 3, 4])
    leg_height = rng.choice([10.2, 10.6, 11.0])
    splay = rng.choice([0.5, 1.0, 1.5])
    brace_style = rng.choice(["cross", "zigzag"])
    roof_style = ("pyramid", "ridge-x", "ridge-y")[seed % 3]  # cycled, so neighbouring seeds differ
    cabin = rng.choice([2.5, 2.8])  # half the cabin's width
    stair_way = rng.choice([-1, 1])
    leg_colour = rng.choice(["wood", "doorBrown", "doorBrown"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    brace_colour = "wood" if leg_colour == "doorBrown" else "doorBrown"
    accent = pal["door"] if pal["door"] != "doorBrown" else pal["roof"]
    colours = {"wall": pal["wall"], "interior": "interiorCream", "trim": pal["trim"], "glass": "windowBlue", "shine": "windowShine", "door": accent}

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    half = cabin + 1.5  # the deck, with the balcony all round
    tier = leg_height / tiers
    spread_top = cabin - 0.1
    spread_bottom = spread_top + splay

    def spread(z):
        return spread_bottom + (spread_top - spread_bottom) * z / leg_height

    def leg_point(index, z):
        sx, sy = LEGS[index]
        return (sx * spread(z), sy * spread(z), z)

    # --- legs: role "pillar", a piece for each tier ---
    legs = [[] for _ in LEGS]
    for t in range(tiers):
        for index in range(4):
            kit = Kit()
            fair.beam(kit, leg_point(index, t * tier), leg_point(index, (t + 1) * tier), 0.6, leg_colour, flat=True)  # ends cut level
            if t == 0:
                px, py, _ = leg_point(index, 0)
                kit.box((px - 0.7, py - 0.7, 0), (px + 0.7, py + 0.7, 0.35), "stone", skip=("-z",))
            legs[index].append(add(kit, "pillar", "wood", t, supports=legs[index][-1:], collider="hull"))

    # --- bracing between the legs, a piece for each face of each tier ---
    for t in range(tiers):
        z0, z1 = t * tier + 0.25, (t + 1) * tier - 0.25
        for f, (i, j) in enumerate(FACES):
            kit = Kit()
            if brace_style == "cross" or (t + f) % 2 == 0:
                beam(kit, leg_point(i, z0), leg_point(j, z1), 0.26, brace_colour, caps=False)
            if brace_style == "cross" or (t + f) % 2 == 1:
                beam(kit, leg_point(j, z0), leg_point(i, z1), 0.26, brace_colour, caps=False)
            if t < tiers - 1:
                beam(kit, leg_point(i, z1 + 0.25), leg_point(j, z1 + 0.25), 0.32, leg_colour, caps=False)
            add(kit, "detail", "wood", t, supports=(legs[i][t], legs[j][t]), collider="hull")

    # --- zig-zag stairs up the front: a flight and a landing for each tier ---
    stair_y = -(half + 0.7)
    reach = spread_top + 0.3
    for t in range(tiers):
        way = stair_way if t % 2 == 0 else -stair_way
        z0, z1 = t * tier, (t + 1) * tier
        xa, xb = -way * reach, way * reach
        kit = Kit()
        fair.beam(kit, (xa, stair_y, z0), (xb, stair_y, z1 - 0.1), 1.2, accent, depth=0.22, flat=True)
        fair.beam(kit, (xa, stair_y - 0.55, z0 + 1.0), (xb, stair_y - 0.55, z1 + 0.9), 0.14, pal["trim"], caps=False)
        lo, hi = sorted((xb, xb + way * 1.3))
        if t < tiers - 1:
            kit.box((lo, stair_y - 0.6, z1 - 0.2), (hi, -spread(z1) + 0.3, z1), brace_colour)
        else:
            kit.box((lo, stair_y - 0.6, z1 - 0.2), (hi, -half, z1 + DECK), brace_colour)
        add(kit, "detail", "wood", t, supports=(legs[0][t], legs[1][t]), collider="hull")

    # --- the deck, a quarter on each leg ---
    floor_z = leg_height + DECK
    decks = {}
    for index, (sx, sy) in enumerate(LEGS):
        xa, xb = sorted((0.0, sx * half))
        ya, yb = sorted((0.0, sy * half))
        kit = Kit()
        kit.box((xa, ya, leg_height), (xb, yb, floor_z), brace_colour, sides={"+z": "interiorCream"})
        decks[sx, sy] = add(kit, "floor", "wood", tiers, supports=(legs[index][-1],))

    # --- balcony railings: the front one leaves a gap at the head of the stairs ---
    edge = half - 0.12
    top_way = stair_way if (tiers - 1) % 2 == 0 else -stair_way
    for sx in (-1, 1):
        for sy in (-1, 1):
            kit = Kit()
            stop = edge - 1.5 if (sy < 0 and sx == top_way) else edge
            railing(kit, (0, sy * edge, floor_z), (sx * stop, sy * edge, floor_z), 1.1, pal["trim"], posts=3)
            railing(kit, (sx * edge, sy * edge, floor_z), (sx * edge, 0, floor_z), 1.1, pal["trim"], posts=2)
            add(kit, "detail", "wood", tiers, supports=(decks[sx, sy],))

    # --- the cabin: big windows on every side ---
    c = cabin
    top = floor_z + CABIN_H
    walls = {}

    def pane(a, b):
        return {"x0": a, "x1": b, "z0": floor_z + 0.9, "z1": floor_z + 2.2, "kind": "window"}

    kit = Kit()
    kit.wall(-c, c, floor_z, top, -c, WALL, 1, [{"x0": -0.6, "x1": 0.6, "z0": floor_z, "z1": floor_z + 2.2, "kind": "door"}, pane(-c + 0.5, -1.0), pane(1.0, c - 0.5)], colours)
    walls["front"] = add(kit, "wall", "wood", tiers, supports=(decks[-1, -1], decks[1, -1]))
    kit = Kit()
    kit.wall(-c, c, floor_z, top, c, WALL, -1, [pane(-c + 0.5, -0.25), pane(0.25, c - 0.5)], colours)
    walls["back"] = add(kit, "wall", "wood", tiers, supports=(decks[-1, 1], decks[1, 1]))
    for sx, name in ((-1, "left"), (1, "right")):
        kit = Kit()
        wall_y(kit, -c + WALL, c - WALL, floor_z, top, sx * c, WALL, -sx, [pane(-c + 0.8, c - 0.8)], colours)
        walls[name] = add(kit, "wall", "wood", tiers, supports=(decks[sx, -1], decks[sx, 1]))

    # --- roof ---
    over = 0.9
    rise = 2.2
    roofs = []
    if roof_style == "pyramid":
        kit = Kit()
        pyramid(kit, 0, 0, c + over, c + over, top, rise + 0.5, pal["roof"], under="interiorCream")
        roofs.append(add(kit, "roof", "tile", tiers + 1, supports=list(walls.values()), collider="hull"))
        peak = top + rise + 0.5
    else:
        axis = "x" if roof_style == "ridge-x" else "y"
        slope = rise / c
        ends = ("left", "right") if axis == "x" else ("front", "back")
        holders = ("front", "back") if axis == "x" else ("left", "right")
        for sign, name in zip((-1, 1), ends):
            lo, hi = sorted((sign * c, sign * (c - WALL)))
            kit = Kit()
            section = [(-c, top), (c, top), (0, top + rise)]
            if axis == "x":
                kit.extrude_x(section, lo, hi, pal["wall"])
            else:
                kit.extrude_y(section, lo, hi, pal["wall"])
            add(kit, "wall", "wood", tiers + 1, supports=(walls[name],), collider="hull")
        for kit, name in zip(roof_halves(axis, -c - 0.6, c + 0.6, c + over, top - slope * over, top + rise, 0.3, pal["roof"]), holders):
            roofs.append(add(kit, "roof", "tile", tiers + 1, supports=(walls[name],), collider="hull"))
        peak = top + rise + 0.3

    kit = Kit()
    flag(kit, 0, 0, peak - 0.4, 2.2, pal["trim"], accent, facing=stair_way)
    add(kit, "detail", "wood", tiers + 2, supports=roofs, collider="box")

    return building.finish(look=f"tiers{tiers}/legs{leg_height:g}/splay{splay:g}/{brace_style}/{roof_style}/cabin{cabin * 2:g}/stairs{stair_way:+d}/{leg_colour}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(22, 30))


if __name__ == "__main__":
    previews()
