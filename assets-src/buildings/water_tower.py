"""Water tower generator.

A round (eight-sided) tin tank about 16 m up on four legs, under a cone cap,
with cross-bracing between the legs and a ladder up one side. The tank breaks
into quarter shells with a block of water inside. The seed varies the tank
(straight drum, barrel, tub or hopper-bottomed, its size and its hoops), the
cap, the legs (two or three tiers, straight or splayed), the bracing, the
walkway and railing round the tank, the riser pipe, and which side the ladder
is on.

How it comes down: the legs are role "pillar", one module per tier, each
resting on the one below. The deck under the tank lists the four top leg
pieces as its supports, the tank rests on the deck and the cap on the tank,
so breaking the legs brings the whole tank down. There are no storey-0 "wall"
modules, so the game's 40% rule does not apply here: only the legs hold it up.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/water_tower.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import beam, frustum, hoop, ring, shell  # noqa: E402

TYPE = "water_tower"
HITS_TO_COLLAPSE = 3  # tall building
TRIANGLE_BUDGET = 1800

HEIGHT = 16.0
DECK = 0.3
SHELL = 0.3  # thickness of the tank wall
LEGS = ((-1, -1), (1, -1), (1, 1), (-1, 1))
FACES = ((0, 1), (1, 2), (2, 3), (3, 0))  # front, right, back, left: the legs each face runs between
COS8 = math.cos(math.pi / 8)


def build(building_id, seed, scheme=None, collection=None):
    """Build one water tower. Returns (empty, stats)."""
    rng = random.Random(seed)

    # --- the tower's character ---
    radius = rng.choice([3.0, 3.4, 3.8])
    tank_height = rng.choice([4.0, 4.8, 5.5])
    tank_shape = rng.choice(["drum", "barrel", "tub", "hopper"])
    cap_style = rng.choice(["cone", "witch", "low"])
    tiers = rng.choice([2, 3, 3])
    splay = rng.choice([0.0, 0.9, 1.6])
    brace_style = rng.choice(["cross", "cross", "zigzag"])
    walkway = rng.choice([True, True, False])
    pipe = rng.choice([True, False])
    ladder_side = rng.choice(["front", "left"])
    leg_pick = rng.choice(["trim", "stone", "accent"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    accent = pal["door"] if pal["door"] != "doorBrown" else pal["roof"]
    leg_colour = {"trim": pal["trim"], "stone": "stone", "accent": accent}[leg_pick]
    brace_colour = leg_colour if leg_pick != "stone" else pal["trim"]

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    # The tank's outline from the deck up, as (height, outside radius).
    h = tank_height
    if tank_shape == "barrel":
        profile = [(0, radius * 0.82), (h * 0.5, radius), (h, radius * 0.82)]
    elif tank_shape == "tub":
        profile = [(0, radius * 0.76), (h, radius)]
    elif tank_shape == "hopper":
        profile = [(0, radius * 0.6), (h * 0.32, radius), (h, radius)]
    else:
        profile = [(0, radius), (h, radius)]
    bottom_radius = profile[0][1]
    top_radius = profile[-1][1]

    cap_height = {"cone": radius * 0.8, "witch": radius * 1.05, "low": radius * 0.4}[cap_style]
    cap_reach = 0.7 if cap_style == "witch" else 0.3
    leg_height = HEIGHT - cap_height - tank_height - DECK
    tier = leg_height / tiers
    deck_radius = bottom_radius + (1.1 if walkway else 0.25)
    spread_top = min(radius * 0.6, (deck_radius - 0.35) / math.sqrt(2))
    spread_bottom = spread_top + splay

    def spread(z):
        return spread_bottom + (spread_top - spread_bottom) * z / leg_height

    def leg_point(index, z):
        sx, sy = LEGS[index]
        return (sx * spread(z), sy * spread(z), z)

    # --- legs: role "pillar", a piece for each tier ---
    legs = [[] for _ in LEGS]
    for t in range(tiers):
        z0, z1 = t * tier, (t + 1) * tier
        for index in range(4):
            kit = Kit()
            beam(kit, leg_point(index, z0), leg_point(index, z1), 0.5, leg_colour)
            if t == 0:
                px, py, _ = leg_point(index, 0)
                kit.box((px - 0.6, py - 0.6, 0), (px + 0.6, py + 0.6, 0.3), "stone", skip=("-z",))
            legs[index].append(
                add(kit, "pillar", "tin", t, supports=legs[index][-1:], collider="hull" if splay else "box")
            )

    # --- bracing between the legs, a piece for each face of each tier ---
    for t in range(tiers):
        z0, z1 = t * tier + 0.2, (t + 1) * tier - 0.2
        for f, (i, j) in enumerate(FACES):
            kit = Kit()
            if brace_style == "cross" or (t + f) % 2 == 0:
                beam(kit, leg_point(i, z0), leg_point(j, z1), 0.2, brace_colour, caps=False)
            if brace_style == "cross" or (t + f) % 2 == 1:
                beam(kit, leg_point(j, z0), leg_point(i, z1), 0.2, brace_colour, caps=False)
            if t < tiers - 1:
                beam(kit, leg_point(i, z1 + 0.2), leg_point(j, z1 + 0.2), 0.24, brace_colour, caps=False)
            add(kit, "detail", "tin", t, supports=(legs[i][t], legs[j][t]), collider="hull")

    # --- riser pipe up the middle ---
    if pipe:
        below = []
        for t in range(tiers):
            kit = Kit()
            frustum(kit, 0, 0, t * tier, 0.55, (t + 1) * tier, 0.55, "stone", sides=6, bottom="stone", top="stone")
            below = [add(kit, "detail", "tin", t, supports=below, collider="hull")]

    # --- deck under the tank ---
    deck_z = leg_height
    tank_z = deck_z + DECK
    kit = Kit()
    frustum(kit, 0, 0, deck_z, deck_radius, tank_z, deck_radius, "wood", bottom="wood", top="wood")
    deck = add(kit, "floor", "wood", tiers, supports=[column[-1] for column in legs], collider="hull")

    # --- walkway railing, in quarters ---
    if walkway:
        rail = ring(0, 0, tank_z + 1.0, deck_radius - 0.12)
        foot = ring(0, 0, tank_z, deck_radius - 0.12)
        for q in range(4):
            kit = Kit()
            for i in (q * 2, q * 2 + 1):
                j = (i + 1) % 8
                beam(kit, rail[i], rail[j], 0.12, pal["trim"], caps=False)
                beam(kit, foot[i], rail[i], 0.12, pal["trim"], caps=False)
            add(kit, "detail", "tin", tiers + 1, supports=(deck,), collider="hull")

    # --- the tank: four quarter shells, with hoops ---
    outline = [(tank_z + z, r) for z, r in profile]

    def radius_at(z):
        for (za, ra), (zb, rb) in zip(profile, profile[1:]):
            if za <= z <= zb:
                return ra + (rb - ra) * (z - za) / (zb - za)
        return top_radius

    hoop_heights = [h - 0.4]
    hoop_heights.append(profile[1][0] - 0.2 if len(profile) == 3 else h * 0.42)
    shells = []
    for q in range(4):
        facets = (q * 2, q * 2 + 1)
        kit = Kit()
        shell(kit, 0, 0, outline, SHELL, facets, pal["wall"], "interiorCream")
        for z in hoop_heights:
            reach = max(radius_at(z), radius_at(z + 0.4)) + 0.1
            hoop(kit, 0, 0, tank_z + z, tank_z + z + 0.4, reach, facets, pal["trim"])
        shells.append(add(kit, "wall", "tin", tiers + 1, supports=(deck,), collider="hull"))

    # --- the water inside, left standing when the shells come away ---
    level = h * 0.82
    kit = Kit()
    frustum(
        kit,
        0,
        0,
        tank_z,
        bottom_radius - SHELL - 0.08,
        tank_z + level,
        min(radius_at(level), top_radius) - SHELL - 0.08,
        "glassTint",
        bottom="glassTint",
        top="glassTint",
    )
    add(kit, "detail", "glass", tiers + 1, supports=(deck,), collider="hull")

    # --- cone cap, in two halves ---
    cap_z = tank_z + h
    apex = (0, 0, cap_z + cap_height)
    brim = ring(0, 0, cap_z, top_radius + cap_reach)
    step = math.pi / 4
    halves = []
    for start in (0, 4):
        kit = Kit()
        frustum(kit, 0, 0, cap_z, top_radius + cap_reach, cap_z + cap_height, 0.0, pal["roof"], only=range(start, start + 4))
        kit.poly([brim[(start + k) % 8] for k in range(5)], (0, 0, -1), pal["roof"])
        middle = math.pi / 8 + (start + 2) * step
        kit.poly([brim[start], brim[(start + 4) % 8], apex], (-math.cos(middle), -math.sin(middle), 0), pal["roof"])
        holders = (shells[0], shells[1]) if start == 0 else (shells[2], shells[3])
        halves.append(add(kit, "roof", "tin", tiers + 2, supports=holders, collider="hull"))

    # --- finial ---
    tip = cap_z + cap_height
    kit = Kit()
    if cap_style == "low":
        kit.box((-0.1, -0.1, tip - 0.3), (0.1, 0.1, tip + 1.3), pal["trim"], skip=("-z", "+z"))
        tip += 1.3
    frustum(kit, 0, 0, tip - 0.1, 0.0, tip + 0.3, 0.36, accent, sides=4)
    frustum(kit, 0, 0, tip + 0.3, 0.36, tip + 0.8, 0.0, accent, sides=4)
    add(kit, "detail", "tin", tiers + 2, supports=halves, collider="hull")

    # --- ladder: up the legs to the deck, then up the side of the tank ---
    if ladder_side == "front":
        out, along, face, quarter = (0, -1), (1, 0), 0, 2
    else:
        out, along, face, quarter = (-1, 0), (0, 1), 3, 1

    def ladder(kit, z0, z1, stand_off):
        """Two rails and flat rungs. `stand_off(z)` is the distance out from the tower's centre."""

        def point(z, side):
            d = stand_off(z)
            return (out[0] * d + along[0] * side * 0.38, out[1] * d + along[1] * side * 0.38, z)

        for side in (-1, 1):
            beam(kit, point(z0, side), point(z1, side), 0.12, "tyre", caps=False)
        count = max(2, round((z1 - z0) / 0.8))
        for k in range(count):
            z = z0 + (k + 0.5) * (z1 - z0) / count
            rung = [point(z - 0.05, -1), point(z - 0.05, 1), point(z + 0.05, 1), point(z + 0.05, -1)]
            kit.poly(rung, (out[0], out[1], 0), "tyre")
            kit.poly(rung, (-out[0], -out[1], 0), "tyre")

    i, j = FACES[face]
    for t in range(tiers):
        kit = Kit()
        ladder(kit, t * tier, (t + 1) * tier, lambda z: spread(z) + 0.45)
        add(kit, "detail", "tin", t, supports=(legs[i][t], legs[j][t]), collider="hull")
    kit = Kit()
    widest = max(r for _, r in profile)
    ladder(kit, tank_z, cap_z, lambda z: widest * COS8 + 0.28)
    add(kit, "detail", "tin", tiers + 1, supports=(shells[quarter],), collider="hull")

    empty, stats = building.finish(
        look=(
            f"{tank_shape}/r{radius:g}xh{tank_height:g}/cap-{cap_style}/tiers{tiers}/splay{splay:g}/{brace_style}"
            f"/walkway-{int(walkway)}/pipe-{int(pipe)}/ladder-{ladder_side}/legs-{leg_pick}"
        )
    )
    return empty, stats


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(22, 30))


if __name__ == "__main__":
    previews()
