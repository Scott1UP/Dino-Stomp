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


BOAT_CLEARANCE = 9  # metres of water between a boat's path and the rocky shore
SHORE = 4  # the rocky band drawn round each island


def in_water(x, y, islands):
    if abs(x) > EDGE - 6 or abs(y) > EDGE - 6:
        return False
    return all(math.hypot(x - ix, y - iy) > r + SHORE + BOAT_CLEARANCE for ix, iy, r in islands)


def lake_routes(islands, centre=(0, 10)):
    """Routes round the island through open water, as lists of points.

    Every 6 degrees round the island, take the nearest point out from the centre that is open water.
    Where no such point exists before the edge of the map, the way round is blocked (the strip of land
    to the shore), so the loop is split there. Each run of open water becomes one route, and every
    step along it is checked so a boat never cuts across a headland.
    """
    cx, cy = centre
    points = []
    for step in range(60):
        angle = math.radians(step * 6)
        spot = None
        for r in range(40, 112, 2):
            x, y = cx + r * math.cos(angle), cy + r * math.sin(angle)
            if in_water(x, y, islands):
                spot = (round(x, 1), round(y, 1))
                break
        points.append(spot)

    def clear_between(a, b):
        return all(in_water(a[0] + (b[0] - a[0]) * t / 10, a[1] + (b[1] - a[1]) * t / 10, islands) for t in range(11))

    # Start the walk at a blocked angle, so a run never wraps round the join.
    start = next((i for i, p in enumerate(points) if p is None), 0)
    runs, run = [], []
    for k in range(60):
        p = points[(start + k) % 60]
        if p is None or (run and not clear_between(run[-1], p)):
            if len(run) > 3:
                runs.append(run)
            run = [p] if p else []
        else:
            run.append(p)
    if len(run) > 3:
        runs.append(run)
    # The two longest stretches of water get a boat each.
    return sorted(runs, key=len, reverse=True)[:2]


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
    # Boats keep to open water: each route is worked out from the island outlines, hugging the shore
    # but never closer than BOAT_CLEARANCE to it, and turning back before the strip of land to the shore.
    for route in lake_routes(school.data["islands"]):
        mover(school, "canoe", route + route[-2:0:-1], speed=4, yaw=90, scale=2, seed=len(route))


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
