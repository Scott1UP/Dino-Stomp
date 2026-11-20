"""Level 2: Playground Park. A fairground, a playground, four giant domino runs and a paddling pool."""

import math
import random

from ._helpers import Layout, mover

SIZE = 230
EDGE = 108
DOMINO_SPACING = 3.6


def along(points, spacing):
    """Walk a polyline, yielding (x, y, heading in degrees) every `spacing` metres."""
    travelled = spacing
    for (ax, ay), (bx, by) in zip(points, points[1:]):
        length = math.hypot(bx - ax, by - ay)
        if length < 1e-6:
            continue
        heading = math.degrees(math.atan2(by - ay, bx - ax))
        at = 0.0
        while travelled + (length - at) >= spacing:
            at += spacing - travelled
            travelled = 0.0
            yield ax + (bx - ax) * at / length, ay + (by - ay) * at / length, heading
        travelled += length - at


def wave(x0, x1, y, height, turns, steps=160):
    return [(x0 + (x1 - x0) * i / steps, y + height * math.sin(i / steps * math.pi * 2 * turns)) for i in range(steps + 1)]


def spiral(cx, cy, r0, r1, turns, steps=220):
    return [
        (cx + (r0 + (r1 - r0) * i / steps) * math.cos(i / steps * math.tau * turns), cy + (r0 + (r1 - r0) * i / steps) * math.sin(i / steps * math.tau * turns))
        for i in range(steps + 1)
    ]


def zigzag(x0, y0, leg, legs, rise):
    points = [(x0, y0)]
    for i in range(legs):
        x0 += leg
        y0 += rise if i % 2 == 0 else -rise
        points.append((x0, y0))
    return points


def layout():
    park = Layout("playground-park", size=SIZE, spawn=(-92, -92), base="grass")
    rng = random.Random(8)

    pool = (52, -34, 13)
    park.data["pool"] = list(pool)
    park.data["paths"] = [
        {"points": [(-EDGE, 0), (-40, 6), (0, 20), (50, 30), (EDGE, 36)], "width": 7},
        {"points": [(0, 20), (6, -24), (36, -34)], "width": 6},
        {"points": [(0, 20), (-10, 64), (-40, EDGE)], "width": 6},
        {"points": [(50, 30), (66, 66), (72, EDGE)], "width": 6},
        {"points": [(66, -34), (EDGE, -46)], "width": 6},
        {"points": [(-40, 6), (-70, -40), (-96, -96)], "width": 6},
    ]
    park.data["grass"] = [
        {"circle": [0, 22, 16], "colour": "#9BBB80"},
        {"circle": [-70, 62, 24], "colour": "#9BBB80"},
        {"circle": [70, 76, 30], "colour": "#B4CE9A"},
    ]
    park.data["paved"] = [{"rect": [34, 52, 106, 104], "radius": 10, "colour": "#F3E9D2"}]

    # --- the fairground, north-east: these are the rides to knock down ---
    ferris = park.building("ferris_wheel", 84, 88, objective="ride")
    park.building("helter_skelter", 50, 90, objective="ride")
    park.building("carousel", 66, 64, objective="ride")
    park.building("bouncy_castle", 94, 60, objective="ride")
    park.building("carousel", -52, -64, objective="ride")
    park.building("helter_skelter", -92, 20, objective="ride")
    park.building("kiosk", 46, 72)
    park.building("kiosk", 95, 76)
    park.building("cafe", 22, 96)
    for x, y in ((22, 84), (30, 82), (38, 84), (44, 100)):
        park.prop("cafe_table", x, y)
    for x, y in ((48, 60), (78, 72), (98, 96), (-36, 62)):
        park.prop("market_umbrella", x, y)

    # --- the playground, west ---
    park.building("climbing_frame", -76, 70)
    park.building("climbing_frame", -56, 52)
    park.building("swings", -84, 52)
    park.building("swings", -60, 78)
    for x, y in ((-70, 60), (-90, 66), (-66, 44)):
        park.prop("seesaw", x, y, rot=rng.uniform(0, 180))
    for x, y in ((-80, 80), (-50, 66)):
        park.prop("sandpit", x, y)

    # --- the middle: bandstand, glasshouse, picnic lawn ---
    bandstand = park.building("bandstand", 0, 22)
    park.building("glasshouse", -30, 84)
    park.building("glasshouse", 34, -101, rot=180)
    for x, y in ((-22, 40), (-14, 48), (18, 44), (26, 36), (-28, 30), (-6, -6), (10, -4)):
        park.prop("picnic_table", x, y, rot=rng.uniform(0, 180))

    # --- homes round the edge ---
    park.building("terraced_house", -6, 100)
    park.building("cottage", -62, 102)
    park.building("cottage", 100, 20, rot=-90)
    park.building("terraced_house", 100, -4, rot=-90)
    park.building("cottage", -100, -30, rot=90)
    park.building("detached_house", -100, -54, rot=90)
    park.building("cottage", 62, -100, rot=180)
    park.building("detached_house", 86, -98, rot=180)
    park.building("terraced_house", 8, 80)
    park.building("cottage", -100, 96, rot=90)
    park.building("terraced_house", -100, -84, rot=90)
    park.building("cottage", 100, -70, rot=-90)
    park.building("cottage", 100, 44, rot=-90)
    park.building("cottage", -24, -102, rot=180)
    park.building("bouncy_castle", -40, 34, objective="ride")
    park.building("kiosk", -44, 70)

    # --- four giant domino runs ---
    runs = [
        wave(-96, -8, -74, 16, 1.6),  # a long S along the south
        spiral(-56, -16, 10, 27, 1.9),  # a spiral in the west (wide at the centre: the dominoes are big)
        zigzag(2, -76, 16, 6, 8),  # a gentle zig-zag along the south-east
        spiral(34, 6, 9, 22, 1.6),  # a second spiral by the path
    ]
    first = None
    order = 0
    for run, points in enumerate(runs):
        for x, y, heading in along(points, DOMINO_SPACING):
            # A domino's thin side (its local Y) points along the run.
            domino = park.prop("domino", x, y, rot=heading - 90, seed=order % 5 + 1, objective="domino", order=order, run=run)
            first = first or domino
            order += 1

    # --- beach balls round the pool, and toy blocks everywhere ---
    for index in range(8):
        angle = index / 8 * math.tau
        park.prop("beach_ball", pool[0] + 22 * math.cos(angle), pool[1] + 22 * math.sin(angle), seed=index + 1)
    for i in range(10):
        angle = i / 10 * math.tau
        if abs(angle - math.pi) > 0.5:
            park.prop("flower_planter", pool[0] + 17.5 * math.cos(angle), pool[1] + 17.5 * math.sin(angle), rot=math.degrees(angle) + 90)
    for x, y in ((-20, -30), (16, 60), (-36, 14), (40, -56), (88, -60), (-96, 80), (-28, 64), (76, 14), (-84, -8), (4, -100), (96, -22), (-44, -98), (60, 14), (-16, 6), (-70, 20), (20, -40), (-96, -6), (76, -84), (-8, 40), (90, 100), (-76, 94), (46, -12), (-30, -50), (16, 100)):
        park.prop("toy_blocks", x, y, rot=rng.uniform(0, 90))

    # --- trees, hedges, benches, lamps ---
    taken = [(e["pos"][0], e["pos"][1], 11) for e in park.data["buildings"]] + [(pool[0], pool[1], 20)]
    dominoes = [(e["pos"][0], e["pos"][1]) for e in park.data["props"] if e["type"] == "domino"]
    placed = 0
    while placed < 150:
        x, y = rng.uniform(-EDGE + 3, EDGE - 3), rng.uniform(-EDGE + 3, EDGE - 3)
        if any(math.hypot(x - tx, y - ty) < tr for tx, ty, tr in taken):
            continue
        if any(math.hypot(x - dx, y - dy) < 8 for dx, dy in dominoes):
            continue
        if 34 < x < 106 and 52 < y < 104:
            continue  # the fairground is paved
        park.prop("tree", x, y)
        placed += 1
    park.line("hedge", (-EDGE + 2, EDGE - 1), (EDGE - 2, EDGE - 1), 6.2)
    park.line("hedge", (-EDGE + 2, -EDGE + 1), (EDGE - 2, -EDGE + 1), 6.2)
    park.line("hedge", (EDGE - 1, -EDGE + 4), (EDGE - 1, EDGE - 4), 6.2, rot=90)
    park.line("hedge", (-EDGE + 1, -EDGE + 4), (-EDGE + 1, EDGE - 4), 6.2, rot=90)
    park.line("fence", (34, 51), (106, 51), 3.1, skip=[(60, 44, 12), (50, 51, 6)])
    # A picket fence round the playground, with gaps to walk in.
    park.line("fence", (-96, 40), (-48, 40), 3.1, skip=[(-72, 40, 5)])
    park.line("fence", (-96, 88), (-48, 88), 3.1, skip=[(-72, 88, 5)])
    park.line("fence", (-97, 42), (-97, 86), 3.1, rot=90)
    park.line("fence", (-46, 42), (-46, 86), 3.1, rot=90, skip=[(-46, 64, 5)])
    for x, y in ((-60, -4), (-44, -40), (22, 8), (48, 18), (-4, -40), (64, -60), (-84, -60), (10, 44)):
        park.prop("picnic_table", x, y, rot=rng.uniform(0, 180))
    for i in range(16):
        angle = i / 16 * math.tau
        park.prop("flower_planter", 20 * math.cos(angle), 22 + 20 * math.sin(angle), rot=math.degrees(angle) + 90)
    for x, y, rot in ((-14, 10, 0), (12, 12, 0), (-10, 38, 0), (14, 36, 0), (36, -16, 0), (70, -22, 90), (52, -54, 180), (-50, 4, 0), (44, 26, 0), (-4, 62, 90), (-80, -44, 60), (80, 40, 0)):
        park.prop("bench", x, y, rot)
    for x, y in ((-12, 22), (12, 26), (38, 36), (56, 34), (0, -8), (-34, 4), (72, -40), (-20, 70), (60, 58), (90, 70), (44, 80), (-70, -30)):
        park.prop("lamp_post", x, y)
    for x, y in ((-40, 76), (-20, 76), (10, -72), (30, -72), (-76, 40), (46, 60), (86, 50)):
        park.prop("flower_planter", x, y)
    for x, y in ((44, 40), (30, 40), (-6, 14), (66, -16), (70, 72), (-66, 66)):
        park.prop("bin", x, y)

    # --- the fairground train runs round the fairground, and an ice cream van drives the main path ---
    train_loop = [(40, 54), (98, 54), (102, 58), (102, 98), (98, 102), (44, 102), (40, 98)]
    mover(park, "toy_train", train_loop, speed=7, yaw=90, kind_is_building=True, seed=3)
    mover(park, "toy_train", train_loop[3:] + train_loop[:3], speed=7, yaw=90, kind_is_building=True, seed=5)
    mover(park, "ice_cream_van", [(-104, 2), (-40, 6), (-16, 12)], speed=6)

    # --- the secret: a golden dino hidden inside a glasshouse ---
    next(e for e in park.data["buildings"] if e["type"] == "glasshouse")["secret"] = 1

    park.data["icons"] = {"domino": [first], "ride": [ferris], "bandstand": [bandstand]}
    return park.data
