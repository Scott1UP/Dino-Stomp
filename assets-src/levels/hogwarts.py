"""Level 6: Hogwarts. A grand gothic school castle on a rocky island in a lake: a cluster of tall
dark spires, a long great hall, school wings, a viaduct, a gatehouse at the top of a zig-zag
stair that winds down to the boathouse, and a sports pitch with tall hoops."""

import math
import os
import random

from ._helpers import Layout, mover

SIZE = 240
EDGE = 112
BUILDINGS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "buildings")


def layout():
    school = Layout("hogwarts", size=SIZE, spawn=(-6, -100), base="lake")
    rng = random.Random(31)

    # The island: overlapping blobs of grass with a rocky shore, in the lake.
    school.data["islands"] = [
        (0, 30, 60), (-38, 14, 42), (40, 16, 40), (12, -26, 30), (26, -54, 20),
        (-72, -2, 30), (-60, -40, 22), (60, 58, 30), (-50, 66, 28), (-8, -78, 14), (-6, -100, 12),
    ]
    school.data["paths"] = [
        {"points": [(-6, -100), (-8, -78), (-6, -50), (-6, -8)], "width": 7, "colour": "#C9BFA6"},
        {"points": [(-6, -8), (-6, 20), (20, 36)], "width": 8, "colour": "#C9BFA6"},
    ]
    school.data["paved"] = [
        {"rect": [-16, 8, 26, 18], "radius": 4, "colour": "#D8CFBA"},  # the forecourt inside the gate
        {"rect": [-90, -16, -50, 16], "radius": 8, "colour": "#9BBB80"},  # the pitch
    ]

    # --- the castle: one dense mass on the hilltop, like the reference. The great hall on the
    # left, wings joining it to a crown of tall dark spires on the right. ---
    crown = school.building("spire_cluster", 26, 46, objective="spire")
    school.building("spire_cluster", 48, 34, objective="spire")
    school.building("spire_cluster", 6, 58, objective="spire")
    for x, y in ((40, 56), (14, 38), (58, 48), (34, 30), (-2, 44), (20, 66), (-50, 56), (-54, 30), (62, 24), (-20, 60), (-8, 30)):
        school.building("spire_tower", x, y, objective="spire")
    school.building("great_hall", -34, 44, rot=90)
    school.building("school_wing", -12, 46, rot=90)
    school.building("school_wing", -30, 22)
    school.building("school_wing", 10, 24)
    school.building("school_wing", 44, 64, rot=180)
    school.building("gate_towers", -6, 2)
    school.building("viaduct", 34, 6, rot=90)

    # --- down the slope: the zig-zag stair, the boathouse on the water, the glasshouses and a hut ---
    if os.path.exists(os.path.join(BUILDINGS, "stair_path.py")):
        school.building("stair_path", 8, -34)
    boathouse = school.building("boathouse", 28, -70)
    school.building("glasshouse", -32, -16)
    school.building("glasshouse", -44, -30, rot=20)
    school.building("cottage", -62, -40, rot=40)

    # --- the sports pitch: tall hoops at each end, stands down the sides ---
    school.building("hoop_posts", -88, 0, rot=90)
    school.building("hoop_posts", -52, 0, rot=-90)
    for x, y, rot in ((-78, 18, 180), (-62, 18, 180), (-78, -18, 0), (-62, -18, 0)):
        school.building("stands", x, y, rot)

    # --- boats on the lake ---
    # Round the east and west of the lake and back: a full loop would cross the strip of land
    # from the shore to the island.
    def arc(start, end, steps=7):
        return [(96 * math.cos(math.radians(a)), 10 + 96 * math.sin(math.radians(a))) for a in (start + (end - start) * i / steps for i in range(steps + 1))]
    east = arc(-62, 85)
    west = arc(95, 238)
    mover(school, "canoe", east + east[-2:0:-1], speed=4, yaw=90, scale=2, seed=1)
    mover(school, "canoe", west + west[-2:0:-1], speed=4, yaw=90, scale=2, seed=2)
    mover(school, "canoe", [(40, -84), (70, -60)], speed=3, yaw=90, scale=1.8, seed=3)

    # --- the forest on the east of the island, rocks along the shore ---
    taken = [(e["pos"][0], e["pos"][1], 13) for e in school.data["buildings"]]

    def on_island(x, y, margin):
        return any(math.hypot(x - ix, y - iy) < r - margin for ix, iy, r in school.data["islands"])

    placed, tries = 0, 0
    while placed < 150 and tries < 8000:
        tries += 1
        x, y = rng.uniform(-EDGE, EDGE), rng.uniform(-EDGE, EDGE)
        if not on_island(x, y, 3) or any(math.hypot(x - tx, y - ty) < tr for tx, ty, tr in taken):
            continue
        if -60 < x < 70 and 14 < y < 72 or -90 < x < -50 and -16 < y < 16 or abs(x + 6) < 6 and y < 0:
            continue
        school.prop("pine_tree" if x > -20 or rng.random() < 0.4 else "tree", x, y, rot=rng.uniform(0, 360), seed=rng.randint(1, 6))
        taken.append((x, y, 4.5))
        placed += 1
    for i in range(30):
        ix, iy, r = school.data["islands"][i % len(school.data["islands"])]
        a = rng.uniform(0, math.tau)
        school.prop("boulder", ix + (r + 1) * math.cos(a), iy + (r + 1) * math.sin(a), rot=rng.uniform(0, 360), seed=rng.randint(1, 6))
    for x, y in ((-14, 30), (30, 30), (-14, 52), (10, 26)):
        school.prop("lamp_post", x, y)
    for x, y in ((-40, 0), (60, -10), (-80, 40)):
        school.prop("toy_blocks", x, y, rot=rng.uniform(0, 90))

    # --- the secret: a golden dino hidden in the boathouse ---
    next(e for e in school.data["buildings"] if e["id"] == boathouse)["secret"] = 1

    school.data["icons"] = {"spire": [crown]}
    return school.data
