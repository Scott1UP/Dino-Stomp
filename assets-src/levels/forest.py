"""Level 5: Pine Forest. A ranger's camp, a treehouse and lookout towers deep in the woods."""

import math
import random

from ._helpers import Layout

SIZE = 240
EDGE = 112


def layout():
    forest = Layout("forest", size=SIZE, spawn=(0, -98), base="grass")
    rng = random.Random(21)

    # A winding river crossed by covered bridges, and trails through the trees.
    river = [(-EDGE, 46), (-70, 40), (-40, 52), (-6, 44), (30, 30), (64, 38), (EDGE, 24)]
    forest.data["paths"] = [
        {"points": river, "width": 14, "colour": "#8FD3E8"},
        {"points": [(0, -EDGE), (0, -40), (-10, 0), (-6, 44), (-14, 80), (-30, EDGE)], "width": 7},
        {"points": [(-10, 0), (-60, -10), (-EDGE, -30)], "width": 6},
        {"points": [(-10, 0), (40, -16), (90, -8), (EDGE, -20)], "width": 6},
        {"points": [(30, 30), (50, 70), (80, 96)], "width": 6},
    ]
    forest.data["grass"] = [
        {"circle": [-10, -6, 26], "colour": "#B4CE9A"},  # the camp clearing
        {"circle": [-70, 80, 18], "colour": "#B4CE9A"},
        {"circle": [70, -64, 20], "colour": "#B4CE9A"},
        {"circle": [70, 80, 16], "colour": "#B4CE9A"},
    ]

    # --- the landmarks: treehouses and lookouts to bring down ---
    lookout = forest.building("lookout_tower", -70, 80, objective="lookout")
    forest.building("treehouse", 70, -64, objective="lookout")
    forest.building("lookout_tower", 86, 60, objective="lookout")
    forest.building("treehouse", -84, -60, objective="lookout")
    forest.building("treehouse", 20, 84, objective="lookout")
    # More landmarks all through the woods, so there is a choice of which to bring down.
    forest.building("lookout_tower", -96, -84, objective="lookout")
    forest.building("treehouse", 96, -10, objective="lookout")
    forest.building("treehouse", -46, -40, objective="lookout")
    forest.building("lookout_tower", 30, -36, objective="lookout")
    forest.building("treehouse", -84, 24, objective="lookout")
    forest.building("lookout_tower", 54, 102, objective="lookout")
    forest.building("treehouse", -40, 98, objective="lookout")
    forest.building("lookout_tower", 100, -96, objective="lookout")

    # Giant toadstool houses, two or three times the normal size.
    for x, y, grow in ((-60, 60, 2.6), (40, 56, 2.2), (-20, -64, 2.4), (76, 30, 2.0), (-100, -40, 2.2)):
        forest.building("mushroom_house", x, y, rot=rng.uniform(0, 360), scale=grow, objective="lookout")

    # --- the ranger's camp in the middle clearing ---
    forest.building("log_cabin", -24, 6, rot=90)
    forest.building("log_cabin", 6, 14, rot=180)
    forest.building("sawmill", -22, -18, rot=0)
    for x, y in ((6, -10), (12, -2), (-4, -24), (14, -18)):
        forest.building("tent", x, y, rot=rng.uniform(0, 360))
    forest.prop("camp_table", 0, 0)
    forest.prop("camp_table", -8, 22, rot=40)

    # --- bridges over the river (the river runs east-west, so they turn to cross it) ---
    forest.building("covered_bridge", -6, 44, rot=90)
    forest.building("covered_bridge", 50, 70 - 37, rot=75)

    # --- more cabins, mushroom houses and sawmills through the woods ---
    for x, y, rot in ((-90, 12, 90), (90, 10, -90), (-50, -70, 0), (46, -92, 0), (-96, 92, 0), (100, 98, 180)):
        forest.building("log_cabin", x, y, rot)
    for x, y in ((-40, 80), (-80, -30), (84, -30), (30, -60), (-104, -100), (104, -100)):
        forest.building("mushroom_house", x, y, rot=rng.uniform(0, 360))
    forest.building("sawmill", 80, 18, rot=-90)
    forest.building("sawmill", -60, -96, rot=0)
    for x, y in ((56, -40), (-16, 92), (80, 100), (10, -56)):
        forest.building("mushroom_house", x, y, rot=rng.uniform(0, 360))
    for x, y, rot in ((-100, -12, 90), (100, -60, -90), (-40, -96, 0), (60, -100, 0), (-104, 60, 90), (-76, 100, 180), (104, 74, -90)):
        forest.building("log_cabin", x, y, rot)
    for x, y in ((-86, 28), (-20, -70), (24, -76), (96, 40), (-50, 14), (44, 14), (-30, 70), (62, 84)):
        forest.building("tent", x, y, rot=rng.uniform(0, 360))
    forest.building("covered_bridge", -70, 40, rot=80)
    forest.building("forest_gate", 0, -80)
    for x, y in ((-60, 30), (60, 0), (-30, 100), (90, -84)):
        forest.building("tent", x, y, rot=rng.uniform(0, 360))

    # --- log piles, boulders and camp things ---
    for x, y in ((-34, -26), (-40, -10), (88, 30), (72, 8), (-70, -80), (40, -100), (-10, 62), (100, 46)):
        forest.prop("log_pile", x, y, rot=rng.uniform(0, 180), seed=rng.randint(1, 6))
    for x, y in ((-6, -40), (40, -36), (-80, 50), (20, 100), (-100, -46), (100, -40), (60, 100), (-50, 100)):
        forest.prop("boulder", x, y, seed=rng.randint(1, 6))
    for x, y in ((-14, -4), (12, 8), (-60, 76), (64, -56), (-90, -66)):
        forest.prop("signpost", x, y, rot=rng.uniform(0, 180))
    for x, y, rot in ((-40, 44, 90), (16, 40, 0), (60, 30, 30)):
        forest.prop("canoe", x, y, rot)
    for x, y in ((-30, 14), (20, 22), (70, -40), (-80, 60)):
        forest.prop("bird_house", x, y)
    for x, y in ((0, 30), (-60, -40), (50, -20), (30, 60), (-100, 70)):
        forest.prop("toy_blocks", x, y, rot=rng.uniform(0, 90))

    # --- the forest itself: hundreds of pines, with stumps, ferns and toadstools between ---
    taken = [(e["pos"][0], e["pos"][1], 11) for e in forest.data["buildings"]] + [(-10, -6, 24)]

    def near_path(x, y):
        for path in forest.data["paths"]:
            points = path["points"]
            for (ax, ay), (bx, by) in zip(points, points[1:]):
                dx, dy = bx - ax, by - ay
                t = max(0, min(1, ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)))
                if math.hypot(x - ax - dx * t, y - ay - dy * t) < path["width"] / 2 + 3:
                    return True
        return False

    def scatter(kind, count, spacing, seeds=6):
        placed, tries = [], 0
        while len(placed) < count and tries < count * 40:
            tries += 1
            x, y = rng.uniform(-EDGE + 3, EDGE - 3), rng.uniform(-EDGE + 3, EDGE - 3)
            if any(math.hypot(x - tx, y - ty) < tr for tx, ty, tr in taken) or near_path(x, y):
                continue
            if any(math.hypot(x - px, y - py) < spacing for px, py in placed):
                continue
            forest.prop(kind, x, y, rot=rng.uniform(0, 360), seed=rng.randint(1, seeds))
            placed.append((x, y))
        taken.extend((x, y, spacing * 0.6) for x, y in placed)

    scatter("pine_tree", 360, 5)
    scatter("tree", 30, 7)
    scatter("stump", 26, 5)
    scatter("fern", 60, 4)
    scatter("toadstool", 30, 4)

    forest.data["icons"] = {"lookout": [lookout]}
    return forest.data
