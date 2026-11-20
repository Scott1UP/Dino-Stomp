"""Level 1: Block Town. Three streets of houses and shops, with five landmark towers."""

import random

from ._helpers import Layout, mover

SIZE = 250
STREETS = [(-56, 10), (0, 12), (56, 10)]  # east-west streets: (y, width)
AVENUES = [(-66, 10), (0, 12), (66, 10)]  # north-south roads: (x, width)
EDGE = 118

# Roughly how much frontage each type needs.
FRONTAGE = {
    "terraced_house": 25,
    "cottage": 10,
    "high_street_shop": 8.5,
    "detached_house": 13,
    "block_of_flats": 15,
    "fire_station": 15,
}
HIGH_STREET = ["high_street_shop", "high_street_shop", "terraced_house", "high_street_shop", "cottage", "high_street_shop", "detached_house"]
BACK_STREET = ["terraced_house", "cottage", "detached_house", "cottage", "high_street_shop", "cottage", "detached_house"]


def layout():
    town = Layout("block-town", size=SIZE, spawn=(0, -28))
    rng = random.Random(4)

    for y, width in STREETS:
        town.road((-EDGE, y), (EDGE, y), width)
    for x, width in AVENUES:
        town.road((x, -EDGE), (x, EDGE), width)
    town.data["junctions"] = [(x, y, max(wx, wy) + 1) for x, wx in AVENUES for y, wy in STREETS]
    town.data["crossings"] = []
    for x, wx in AVENUES:
        for y, wy in STREETS:
            town.data["crossings"] += [(x - wx / 2 - 5, y, "x", wy), (x + wx / 2 + 5, y, "x", wy), (x, y - wy / 2 - 5, "y", wx), (x, y + wy / 2 + 5, "y", wx)]

    # The blocks between the avenues, as (from x, to x).
    blocks = [(-EDGE + 2, -66 - 9), (-66 + 9, -10), (10, 66 - 9), (66 + 9, EDGE - 2)]
    plaza = (10, 6, 34, 30)  # the clock tower's square, north-east of the middle crossroads

    town.data["grass"] = []

    # --- rows of buildings along both sides of every street ---
    picks = {"high": 0, "back": 0}
    for y, width in STREETS:
        kinds = HIGH_STREET if y == 0 else BACK_STREET
        which = "high" if y == 0 else "back"
        for side in (1, -1):  # north side faces south (rot 0), south side faces north
            row_y = y + side * (width / 2 + 9.5)
            for index, (x0, x1) in enumerate(blocks):
                # A few plots are left as little pocket parks, so the town is not wall-to-wall houses.
                if (y > 0 and side == -1 and index % 2 == 1) or (y < 0 and side == 1 and index % 2 == 0):
                    town.data["grass"].append({"rect": [x0, row_y - 5, x1, row_y + 5], "radius": 3})
                    town.line("tree", (x0 + 5, row_y), (x1 - 5, row_y), 10)
                    town.prop("bench", (x0 + x1) / 2, row_y - side * 3, 0 if side == 1 else 180)
                    town.prop("toy_blocks", (x0 + x1) / 2 + 10, row_y)
                    continue
                cursor = x0
                while True:
                    kind = kinds[picks[which] % len(kinds)]
                    need = FRONTAGE[kind]
                    if cursor + need > x1:
                        # Try to fit something small in what is left.
                        kind, need = "cottage", FRONTAGE["cottage"]
                        if cursor + need > x1:
                            break
                    else:
                        picks[which] += 1
                    x = cursor + need / 2
                    cursor += need + 8.5
                    if y == 0 and side == 1 and plaza[0] - 6 < x < plaza[2] + 4:
                        continue  # keep the plaza clear
                    deeper = 2.5 if kind in ("block_of_flats", "fire_station") else 0
                    town.building(kind, x, row_y + side * deeper, rot=0 if side == 1 else 180)
                    if kind in ("cottage", "detached_house"):
                        # A front garden.
                        for dx in (-3, 3):
                            town.prop("fence" if rng.random() < 0.5 else "hedge", x + dx, row_y - side * 6.2, 0 if side == 1 else 180)

    # --- the five landmarks, each with a star over it ---
    clock = town.building("clock_tower", 22, 19, objective="tower")
    church = town.building("church", -92, 96, objective="tower")
    town.building("water_tower", 96, 100, objective="tower")
    town.building("windmill", 34, 100, objective="tower")
    flats = town.building("block_of_flats", -34, -98, rot=180, objective="tower")

    # --- the north edge: church, school, a green with the windmill ---
    town.building("school", -30, 96)
    town.building("detached_house", 68, 92)
    town.building("cottage", -62, 94)
    # --- the south edge: fire station, market square, more homes ---
    town.building("fire_station", -92, -98, rot=180)
    town.building("detached_house", 26, -98, rot=180)
    town.building("detached_house", 44, -98, rot=180)
    town.building("cottage", 94, -98, rot=180)
    town.building("fountain", 0, -100)
    for x, y, rot in ((-12, -92, 90), (-12, -108, 90), (12, -92, -90), (12, -108, -90)):
        town.building("market_stall", x, y, rot)
    town.building("fountain", 22, 12)

    town.data["grass"] += [
        {"rect": [-EDGE, 74, -6, EDGE]},
        {"rect": [6, 74, EDGE, EDGE]},
        {"rect": [-EDGE, -EDGE, -18, -76]},
        {"rect": [18, -EDGE, EDGE, -76]},
    ]
    # Back gardens between the rows.
    for y_lo, y_hi in ((22, 36), (-36, -22)):
        for x0, x1 in blocks:
            town.data["grass"].append({"rect": [x0, y_lo, x1, y_hi], "radius": 3})
            town.line("tree", (x0 + 4, (y_lo + y_hi) / 2), (x1 - 4, (y_lo + y_hi) / 2), 12)
            town.line("hedge" if y_lo > 0 else "fence", (x0 + 2, y_lo - 0.5), (x1 - 2, y_lo - 0.5), 9)
    town.data["paved"] = [
        {"rect": [plaza[0], plaza[1], plaza[2], plaza[3]], "radius": 3},
        {"rect": [-18, -116, 18, -84], "radius": 4},
    ]

    # --- street furniture ---
    clear = [(x, y, 11) for x, _ in AVENUES for y, _ in STREETS]
    for y, width in STREETS:
        offset = width / 2 + 1.6
        town.line("lamp_post", (-EDGE + 6, y + offset), (EDGE - 6, y + offset), 28, skip=clear)
        town.line("lamp_post", (-EDGE + 16, y - offset), (EDGE - 16, y - offset), 28, rot=180, skip=clear)
    for x, width in AVENUES:
        offset = width / 2 + 1.6
        town.line("tree", (x + offset + 1, -EDGE + 8), (x + offset + 1, EDGE - 8), 19, skip=clear + [(0, -100, 20)])
        town.line("street_sign", (x - offset, -EDGE + 30), (x - offset, EDGE - 30), 56, skip=clear)
    for x, wx in AVENUES:
        for y, wy in STREETS:
            town.prop("traffic_light", x + wx / 2 + 1.4, y + wy / 2 + 1.4)

    for y, width in STREETS:
        for i in range(7):
            x = -104 + i * 34 + rng.uniform(-4, 4)
            if any(abs(x - ax) < 10 for ax, _ in AVENUES):
                continue
            side = 1 if i % 2 else -1
            town.prop("car", x, y + side * (width / 2 - 2.2), 90 if side < 0 else -90)
    for x, width in AVENUES:
        for i in range(4):
            y = -96 + i * 62 + rng.uniform(-4, 4)
            if any(abs(y - sy) < 10 for sy, _ in STREETS):
                continue
            town.prop("car", x + (width / 2 - 2.2) * (1 if i % 2 else -1), y, 0 if i % 2 else 180)
    town.prop("bus", -44, -3.4, 90)
    town.prop("bus", 88, 59, -90)
    town.prop("ice_cream_van", 50, 78, 90)
    town.prop("ice_cream_van", -6, -80, 90)

    for x, y in ((13, 9), (31, 9), (13, 27), (31, 27)):
        town.prop("bench", x, y)
        town.prop("flower_planter", x, y + 2.4)
    for x, y in ((16, 14), (28, 14), (-8, 9.4), (-20, 9.4), (60, 9.4), (-80, -9.4), (-100, 9.4), (90, -9.4)):
        town.prop("bin", x, y)
    town.prop("post_box", 8.6, 9.2)
    town.prop("post_box", -74, 65)
    # Fruit carts under big umbrellas: in the market square, the plaza and by the green.
    for x, y in ((-6, -92), (6, -108), (16, 22), (28, 22), (-50, 9.6), (56, 78)):
        town.prop("market_umbrella", x, y)
    for x, y, rot in ((-112, 30, 90), (112, -30, -90), (-112, -84, 90), (112, 84, -90)):
        town.prop("billboard", x, y, rot)

    # --- the greens at the north and south edges: trees, toy blocks, benches ---
    for i in range(34):
        x = rng.uniform(-EDGE + 4, EDGE - 4)
        y = rng.choice([rng.uniform(78, EDGE - 4), rng.uniform(-EDGE + 4, -78)])
        if abs(x) < 20 and y < 0:
            continue
        if any(abs(x - bx) < 13 and abs(y - by) < 13 for bx, by in ((-92, 96), (-30, 96), (34, 100), (96, 100), (68, 92), (-62, 94), (-92, -98), (-34, -98), (26, -98), (44, -98), (94, -98))):
            continue
        town.prop("tree", x, y)
    for x, y in ((-112, 110), (-8, 110), (60, 110), (112, 110), (-112, -110), (-60, -84), (66, -84), (112, -84), (-110, 84), (0, 84)):
        town.prop("toy_blocks", x, y, rot=rng.uniform(0, 90))
    for x, y in ((-104, 44), (104, 44), (-104, -44), (104, -44), (-40, 78), (40, -78), (80, 30), (-80, -30), (100, 12), (-100, -12)):
        town.prop("crate", x, y, rot=rng.uniform(0, 45))
    town.line("hedge", (-EDGE + 2, EDGE - 2), (EDGE - 2, EDGE - 2), 6.2)
    town.line("hedge", (-EDGE + 2, -EDGE + 2), (EDGE - 2, -EDGE + 2), 6.2)

    # --- traffic: cars, a bus and an ice cream van driving the streets (down the middle of the
    # road, clear of the parked cars). Each loop has its own roads, so they never meet head on.
    mover(town, "car", [(-66, 0), (0, 0), (0, 56), (-66, 56)], speed=8, seed=11)
    mover(town, "car", [(0, -56), (66, -56), (66, 0), (0, 0)], speed=8.5, seed=12)
    mover(town, "bus", [(6, 56), (114, 56)], speed=6)
    mover(town, "ice_cream_van", [(-114, -56), (-6, -56)], speed=6.5)

    # --- the secret: a golden dino hidden inside one ordinary house ---
    hideout = next(e for e in town.data["buildings"] if e["type"] == "cottage" and e["pos"][1] < -60)
    hideout["secret"] = 1

    house = next(e["id"] for e in town.data["buildings"] if e["type"] == "terraced_house")
    town.data["icons"] = {"tower": [clock], "house": [house], "church": [church], "flats": [flats]}
    return town.data
