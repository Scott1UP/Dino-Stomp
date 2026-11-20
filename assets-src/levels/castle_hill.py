"""Level 3: Castle Hill. Two rings of walls, shut gates, and a giant tower standing on three pillars."""

import math
import random

from ._helpers import Layout

SIZE = 240
EDGE = 114
CENTRE = (0, 18)
OUTER = 44  # half the width of the outer curtain wall
INNER = 28  # half the width of the inner bailey wall
SECTION = 8


def layout():
    castle = Layout("castle-hill", size=SIZE, spawn=(0, -96), base="grass")
    rng = random.Random(6)
    cx, cy = CENTRE

    # The hill is drawn on the mat: the ground itself stays flat.
    castle.data["grass"] = [
        {"circle": [cx, cy, 82], "colour": "#9BBB80"},
        {"circle": [cx, cy, 70], "colour": "#B4CE9A"},
    ]
    castle.data["paved"] = [
        {"rect": [cx - OUTER + 2, cy - OUTER + 2, cx + OUTER - 2, cy + OUTER - 2], "radius": 8, "colour": "#E6DCC6"},
        {"rect": [cx - INNER + 2, cy - INNER + 2, cx + INNER - 2, cy + INNER - 2], "radius": 6, "colour": "#F3E9D2"},
    ]
    castle.data["paths"] = [{"points": [(0, -EDGE), (0, cy - OUTER)], "width": 10}, {"points": [(0, cy - OUTER), (0, cy - INNER)], "width": 9, "colour": "#D9C7A0"}]

    walls = []

    def ring(half, count, gate_side=True):
        """A square of wall sections with towers at the corners and along the sides, and a shut gate in the south."""
        offsets = [(i - (count - 1) / 2) * SECTION for i in range(count)]
        for d in offsets:
            walls.append(castle.building("castle_wall", cx + d, cy + half, 180, scheme="postbox"))  # north
            walls.append(castle.building("castle_wall", cx + half, cy + d, 90, scheme="postbox"))  # east, facing out
            walls.append(castle.building("castle_wall", cx - half, cy + d, -90, scheme="postbox"))  # west
            if abs(d) > 9:
                walls.append(castle.building("castle_wall", cx + d, cy - half, 0, scheme="postbox"))  # south, either side of the gate
        for sx in (-1, 1):
            for sy in (-1, 1):
                castle.building("castle_turret", cx + sx * half, cy + sy * half)
            castle.building("castle_turret", cx + sx * 10.6, cy - half)
        castle.building("castle_gate", cx, cy - half)

    ring(OUTER, 11)
    ring(INNER, 7)
    # Tall square towers part-way along the outer walls.
    for d in (-20, 20):
        castle.building("castle_tower", cx + d, cy + OUTER + 1.2, 180)
        castle.building("castle_tower", cx + d * 1.4, cy - OUTER - 1.2, 0)
    castle.building("castle_tower", cx + OUTER + 1.2, cy, 90)
    castle.building("castle_tower", cx - OUTER - 1.2, cy, -90)

    # Fourteen marked wall sections to smash: he has to break in.
    marked = [w for i, w in enumerate(walls) if i % 4 == 1][:14]
    for entry in castle.data["buildings"]:
        if entry["id"] in marked:
            entry["objective"] = "wall"

    # --- the inner bailey: the giant tower and the keep ---
    tower = castle.building("giant_tower", cx, cy - 7, objective="giantTower")
    castle.building("castle_keep", cx, cy + 17, rot=0)
    for x, y in ((-18, -16), (18, -16), (-20, 2), (20, 2)):
        castle.prop("banner_pole", cx + x, cy + y)
    for x, y in ((-12, -20), (12, -20), (-22, 14), (22, 14)):
        castle.prop("barrel", cx + x, cy + y)
        castle.prop("barrel", cx + x + 1.6, cy + y + 0.8)
    castle.prop("well", cx - 16, cy - 6)
    castle.prop("cannon", cx + 16, cy - 8, rot=180)

    # --- the outer ward, between the walls: a busy little town ---
    ward = (INNER + OUTER) / 2
    for x, y, rot in ((-ward, -20, 90), (-ward, 22, 90), (ward, -20, -90), (ward, 22, -90)):
        castle.building("cottage", cx + x, cy + y, rot)
    castle.building("stable", cx - 24, cy - ward, 0)
    castle.building("stable", cx + 26, cy - ward, 0)
    castle.building("stable", cx + ward, cy + 2, -90)
    for i, (x, y, rot) in enumerate(((-ward, 0, 90), (-ward, 8, 90), (0, ward, 180), (8, ward, 180), (-8, ward, 180), (ward, 36, -90))):
        castle.building("market_stall", cx + x, cy + y, rot)
    for x, y in ((-ward - 4, -36), (ward + 4, 36), (-36, ward + 4), (36, -ward - 2)):
        castle.prop("well", cx + x, cy + y)
    for x, y in ((-ward, 16), (ward, -6), (16, ward), (-16, -ward)):
        castle.prop("market_umbrella", cx + x, cy + y)
    for x, y in ((-ward + 5, -8), (ward - 5, 12), (30, ward - 4), (-30, -ward + 4), (-ward - 5, 30), (ward - 4, -30)):
        castle.prop("hay_cart", cx + x, cy + y, rot=rng.uniform(0, 180))
        castle.prop("haystack", cx + x + 3, cy + y + 1.5)
    for x, y in ((-10, -ward), (10, -ward), (-ward, -34), (ward, -34), (-34, ward), (34, ward)):
        castle.prop("training_dummy", cx + x, cy + y)
        castle.prop("barrel", cx + x + 2, cy + y)
    for d in (-30, -12, 12, 30):
        castle.prop("banner_pole", cx + d, cy - OUTER + 6)
        castle.prop("cannon", cx + d, cy + OUTER - 7, rot=180)
    for x, y in ((-ward, 14), (ward, 30), (14, ward), (-14, -ward - 2), (ward - 2, -10), (-ward + 2, -30)):
        castle.prop("crate", cx + x, cy + y, rot=rng.uniform(0, 45))
        castle.prop("tree", cx + x + 4, cy + y + 3)

    # --- the village and the siege outside the walls ---
    for x, y, rot in ((-84, -40, 90), (-90, -8, 90), (84, -40, -90), (90, -8, -90), (-88, 40, 90), (88, 40, -90)):
        castle.building("cottage", x, y, rot)
    castle.building("terraced_house", -50, -92)
    castle.building("terraced_house", 52, -92)
    castle.building("stable", -40, 96)
    castle.building("cottage", 44, 98)
    for x, rot in ((-28, 12), (28, -12), (-64, 30), (64, -30)):
        castle.prop("catapult", x, cy - OUTER - 22, rot=rot)
    for d in range(-78, -40, 9):
        castle.prop("banner_pole", -7.5, d)
        castle.prop("banner_pole", 7.5, d)

    taken = [(e["pos"][0], e["pos"][1], 12) for e in castle.data["buildings"] if e["type"] not in ("castle_wall",)]
    placed = 0
    while placed < 30:
        x, y = rng.uniform(-EDGE + 3, EDGE - 3), rng.uniform(-EDGE + 3, EDGE - 3)
        if abs(x - cx) < OUTER + 8 and abs(y - cy) < OUTER + 8:
            continue  # nothing grows on the castle
        if abs(x) < 12 and y < 0:
            continue  # keep the road to the gate clear
        if any(math.hypot(x - tx, y - ty) < tr for tx, ty, tr in taken):
            continue
        castle.prop("tree", x, y)
        placed += 1
    castle.line("hedge", (-EDGE + 2, -EDGE + 1), (-14, -EDGE + 1), 6.2)
    castle.line("hedge", (14, -EDGE + 1), (EDGE - 2, -EDGE + 1), 6.2)
    castle.line("hedge", (-EDGE + 1, -EDGE + 4), (-EDGE + 1, EDGE - 4), 6.2, rot=90)
    castle.line("hedge", (EDGE - 1, -EDGE + 4), (EDGE - 1, EDGE - 4), 6.2, rot=90)
    castle.line("hedge", (-EDGE + 2, EDGE - 1), (EDGE - 2, EDGE - 1), 6.2)
    castle.line("fence", (-13, -44), (-13, -EDGE + 6), 6, rot=90)
    castle.line("fence", (13, -44), (13, -EDGE + 6), 6, rot=90)
    for x, y in ((-36, -70), (36, -70), (-70, -56), (70, -56), (-96, 70), (96, 70), (-40, -52), (40, -52)):
        castle.prop("haystack", x, y)
        castle.prop("crate", x + 3, y - 2, rot=rng.uniform(0, 45))
    for x, y in ((-24, -84), (24, -84), (-72, 10), (72, 10)):
        castle.prop("toy_blocks", x, y, rot=rng.uniform(0, 90))

    castle.data["icons"] = {"wall": [marked[0]], "giantTower": [tower]}
    return castle.data
