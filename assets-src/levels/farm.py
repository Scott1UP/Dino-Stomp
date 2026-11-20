"""Level 4: Sunny Farm. Big barns, farmhouses and silos, and fields of giant sunflowers,
pumpkins and scarecrows taller than the dinosaurs."""

import math
import random

from ._helpers import Layout

SIZE = 240
EDGE = 112

# How much bigger than normal the farm's buildings are, so there are big things to knock over.
FARMHOUSE = 1.8
BARN = 1.4
SILO = 1.35
SCARECROW = 3.4  # about 14 m tall
PUMPKIN = 3.2  # about 5 m across, and it rolls


def layout():
    farm = Layout("farm", size=SIZE, spawn=(0, -100), base="grass")
    rng = random.Random(12)

    farm.data["paths"] = [
        {"points": [(0, -EDGE), (0, -30), (-8, 0), (-50, 6), (-EDGE, 4)], "width": 9},
        {"points": [(-8, 0), (10, 40), (60, 56), (EDGE, 60)], "width": 8},
        {"points": [(0, -30), (60, -36), (EDGE, -30)], "width": 8},
        {"points": [(10, 40), (0, EDGE)], "width": 7},
    ]
    farm.data["paved"] = [{"rect": [-40, -24, 34, 30], "radius": 10, "colour": "#E3CFA0"}]

    # Fields, like a patchwork quilt: (x0, y0, x1, y1, ground colour, what grows there)
    fields = [
        (-106, -106, -54, -46, "#D8BE7A", "sunflowers"),
        (-44, -106, -10, -46, "#C9A46B", "crops"),
        (10, -106, 50, -50, "#B7CC8E", "pumpkins"),
        (60, -106, 106, -46, "#D8BE7A", "sunflowers"),
        (-106, 16, -56, 70, "#C9A46B", "crops"),
        (44, -22, 106, 44, "#B7CC8E", "sunflowers"),
        (-106, 80, -50, 106, "#D8BE7A", "pumpkins"),
        (24, 70, 106, 106, "#E3CFA0", "yard"),
        (-40, 50, 0, 106, "#9BBB80", "orchard"),
    ]
    for x0, y0, x1, y1, colour, _ in fields:
        farm.data["grass"].append({"rect": [x0, y0, x1, y1], "radius": 5, "colour": colour})

    # --- the big farmyard in the middle ---
    barn = farm.building("barn", -18, 16, scale=BARN, objective="barn")
    farm.building("farmhouse", 20, -8, rot=90, scale=FARMHOUSE, objective="barn")
    farm.building("silo", 14, 22, scale=SILO, objective="barn")
    farm.building("silo", 24, 16, scale=SILO, objective="barn")
    farm.building("chicken_coop", -32, -14, rot=30)
    farm.building("tractor_shed", -12, -16, rot=180)
    farm.building("farm_gate_arch", 0, -40)

    # --- more farms round the edges ---
    farm.building("barn", -84, -20, rot=90, scale=BARN, objective="barn")
    farm.building("silo", -96, -4, scale=SILO, objective="barn")
    farm.building("barn", 60, 90 - 2, rot=180, scale=BARN, objective="barn")
    farm.building("silo", 84, 92, scale=SILO, objective="barn")
    farm.building("farmhouse", 34, 92, rot=180, scale=FARMHOUSE, objective="barn")
    farm.building("windmill", -60, -32, scale=1.3, objective="barn")
    farm.building("chicken_coop", 30, -40)
    farm.building("stable", 84, 54, rot=-90)

    # --- giant things in the fields ---
    giants = []
    for x0, y0, x1, y1, _, grows in fields:
        if grows == "sunflowers":
            for i in range(int((x1 - x0) // 13)):
                for j in range(int((y1 - y0) // 14)):
                    x = x0 + 7 + i * 13 + rng.uniform(-1.5, 1.5)
                    y = y0 + 7 + j * 14 + rng.uniform(-1.5, 1.5)
                    giants.append(farm.building("giant_sunflower", x, y, rot=rng.uniform(-25, 25), objective="giant"))
        elif grows == "pumpkins":
            for i in range(int((x1 - x0) // 10)):
                for j in range(int((y1 - y0) // 10)):
                    farm.prop("pumpkin", x0 + 6 + i * 10, y0 + 6 + j * 10, rot=rng.uniform(0, 360), seed=rng.randint(1, 6), scale=PUMPKIN)
        elif grows == "crops":
            y = y0 + 4
            while y < y1 - 3:
                x = x0 + 5
                while x < x1 - 5:
                    farm.prop("crop_row", x, y, seed=rng.randint(1, 4))
                    x += 10
                y += 9
        elif grows == "orchard":
            for i in range(4):
                for j in range(5):
                    farm.prop("apple_tree", x0 + 6 + i * 9.5, y0 + 6 + j * 10 + (i % 2) * 4)
        # A giant scarecrow watches over every field.
        if grows not in ("orchard", "yard"):
            cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
            giants.append(farm.building("scarecrow", cx + rng.uniform(-4, 4), cy, rot=rng.uniform(-20, 20), scale=SCARECROW, kind="building", objective="giant"))

    # --- farm things round the yard ---
    for x, y in ((-30, 30), (-36, 26), (30, 32), (36, 34), (64, 10), (-70, 2), (8, -60), (-8, 60), (-100, 76)):
        farm.prop("hay_bale", x, y, rot=rng.uniform(0, 180), seed=rng.randint(1, 6), scale=1.6)
    for x, y, rot in ((6, -28, 0), (-46, -2, 90), (66, -30, 0), (16, 56, 180)):
        farm.prop("tractor", x, y, rot, scale=1.4)
    for x, y, rot in ((-20, -30, 90), (76, -26, 0), (-60, 10, 90)):
        farm.prop("trailer", x, y, rot, scale=1.4)
    for x, y in ((-34, 4), (32, 4), (-74, -40)):
        farm.prop("water_trough", x, y, scale=1.4)
    for x, y in ((-24, -4), (-28, 8)):
        farm.prop("milk_churns", x, y, scale=1.4)
    for x, y in ((-36, -24), (28, -22), (12, 64)):
        farm.prop("wheelbarrow", x, y, rot=rng.uniform(0, 180), scale=1.4)
    for i in range(5):
        farm.prop("beehive", -104 + i * 5, -40)
    for x, y in ((0, 6), (-60, -40), (100, 12)):
        farm.prop("toy_blocks", x, y, rot=rng.uniform(0, 90))
    for x, y in ((6, -18), (-6, 30)):
        farm.prop("market_umbrella", x, y)

    # Fences round the fields, with a wide gap in each side to get in.
    for x0, y0, x1, y1, _, grows in fields:
        if grows == "yard":
            continue
        gaps = [((x0 + x1) / 2, y0, 9), ((x0 + x1) / 2, y1, 9), (x0, (y0 + y1) / 2, 9), (x1, (y0 + y1) / 2, 9)]
        farm.line("fence", (x0, y0), (x1, y0), 6, skip=gaps)
        farm.line("fence", (x0, y1), (x1, y1), 6, skip=gaps)
        farm.line("fence", (x0, y0), (x0, y1), 6, rot=90, skip=gaps)
        farm.line("fence", (x1, y0), (x1, y1), 6, rot=90, skip=gaps)

    taken = [(e["pos"][0], e["pos"][1], 14) for e in farm.data["buildings"]]
    placed = 0
    while placed < 24:
        x, y = rng.uniform(-EDGE + 3, EDGE - 3), rng.uniform(-EDGE + 3, EDGE - 3)
        if any(x0 - 2 < x < x1 + 2 and y0 - 2 < y < y1 + 2 for x0, y0, x1, y1, _, _ in fields):
            continue
        if -42 < x < 36 and -26 < y < 32:
            continue
        if any(math.hypot(x - tx, y - ty) < tr for tx, ty, tr in taken):
            continue
        farm.prop("tree", x, y)
        placed += 1

    farm.data["icons"] = {"barn": [barn], "giant": giants[:1]}
    return farm.data
