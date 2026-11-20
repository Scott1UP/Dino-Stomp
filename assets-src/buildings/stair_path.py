"""Stair path generator: the zig-zag stone stair down to the lake.

A walled path about 3 m wide that zig-zags up a bank in switchbacks: long
gently sloping runs across the slope (along X), joined at alternate ends by
straight flights of steps climbing the slope (along Y). Low grey parapet
walls with a dark slate coping line both sides of the path, with lantern
posts or little pinnacles at the turns. About 20 m by 30 m, rising 6-8 m from
the bottom (the front, -Y) to the top (the back, +Y).

The ground in the game is flat, so the stair is built as solid masonry from
the ground up: from the side it reads as a stepped stone terrace. Every
piece stands on the ground (storey 0): each run is three blocks, and each
flight is split into blocks of a few steps, each carrying its own parapets.

The seed varies the number of runs (three or four), which side the bottom
run starts from, the total rise, the path and coping colours, and the posts
at the turns (lanterns or pinnacles).

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/stair_path.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_wizard as wiz  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_fair import hexa  # noqa: E402

TYPE = "stair_path"
HITS_TO_COLLAPSE = 2  # long, low structure
TRIANGLE_BUDGET = 1300

HX, HY = 10.0, 15.0  # 20 m by 30 m
PATH = 3.0  # width of the path, walls included
PARAPET = 0.3  # wall thickness
WALL_H = 0.85  # parapet height above the path
RUN_RISE = 0.35  # how much each run climbs along its length
KERB = 0.3  # the bottom of the path stands this far off the ground
STEP = 1.0  # depth of a step


def build(building_id, seed, scheme=None, collection=None):
    """Build one stair path. Returns (empty, stats)."""
    rng = random.Random(seed)

    runs = (4, 3)[seed % 2]  # alternated, so neighbouring seeds differ
    start = (-1, 1)[(seed // 2 + rng.choice([0, 0, 1])) % 2]  # the x side the bottom run starts from
    rise = rng.choice([6.0, 7.0, 8.0])
    path = rng.choice(["ground", "ground", "dust"])
    coping = rng.choice(wiz.SLATES)
    posts = rng.choice(["lanterns", "pinnacles", "lanterns"])
    gold = rng.choice(wiz.GOLDS)
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    half = PATH / 2
    ys = [-HY + half + k * (2 * HY - PATH) / (runs - 1) for k in range(runs)]
    climb = (rise - KERB - runs * RUN_RISE) / (runs - 1)  # each flight of steps

    def block(kit, x0, x1, y0, y1, za, zb, along="x"):
        """A solid block from the ground up to a path surface sloping from za to zb (along x or y)."""
        if along == "x":
            top = [(x0, y0, za), (x1, y0, zb), (x1, y1, zb), (x0, y1, za)]
        else:
            top = [(x0, y0, za), (x1, y0, za), (x1, y1, zb), (x0, y1, zb)]
        bottom = [(x, y, 0.0) for x, y, _ in top]
        hexa(kit, bottom, top, "stone", colours={1: path}, skip=(0,))

    def parapet(kit, x0, x1, y0, y1, za, zb, along="x"):
        """A low wall standing on the path, its dark coping following the slope."""
        if along == "x":
            low = [(x0, y0, za), (x1, y0, zb), (x1, y1, zb), (x0, y1, za)]
        else:
            low = [(x0, y0, za), (x1, y0, za), (x1, y1, zb), (x0, y1, zb)]
        high = [(x, y, z + WALL_H) for x, y, z in low]
        hexa(kit, low, high, "stone", colours={1: coping}, skip=(0,))

    def post(kit, x, y, z):
        if posts == "lanterns":
            kit.box((x - 0.12, y - 0.12, z), (x + 0.12, y + 0.12, z + 2.2), "tyre", skip=("-z",))
            kit.box((x - 0.32, y - 0.32, z + 2.2), (x + 0.32, y + 0.32, z + 2.85), "sunny")
            wiz.cone_part(kit, 0.46, 0.0, z + 2.85, z + 3.4, "tyre", 4, cx=x, cy=y)
        else:
            wiz.pinnacle(kit, x, y, z, 0.32, 0.9, 1.9, "stone", coping, gold)

    # --- the runs across the slope ---
    run_ends = []  # (z at start, z at end, direction, module ids by third)
    z = KERB
    for k, y in enumerate(ys):
        d = start * (1 if k % 2 == 0 else -1)  # +1 runs towards +X
        z_start, z_end = z, z + RUN_RISE
        y0, y1 = y - half, y + half
        thirds = []
        for t in range(3):
            # Thirds counted in the direction of travel.
            fa, fb = t / 3, (t + 1) / 3
            xa, xb = -d * HX + d * 2 * HX * fa, -d * HX + d * 2 * HX * fb
            za, zb = z_start + RUN_RISE * fa, z_start + RUN_RISE * fb
            x0, x1 = sorted((xa, xb))
            z0, z1 = (za, zb) if xa < xb else (zb, za)
            kit = Kit()
            block(kit, x0, x1, y0, y1, z0, z1)
            # Downhill wall (-Y): open where the flight below arrives, at the start of the run.
            # Uphill wall (+Y): open where the flight above leaves, at the end of the run.
            for side, open_at in ((-1, 0 if k > 0 else None), (1, 2 if k < runs - 1 else None)):
                ya, yb = (y0, y0 + PARAPET) if side < 0 else (y1 - PARAPET, y1)
                if open_at == t:
                    # Keep only the part of the wall clear of the flight's mouth.
                    gate = (-d if t == 0 else d) * (HX - PATH)
                    if t == 0:
                        cut_a, cut_b = sorted((gate, xb))
                    else:
                        cut_a, cut_b = sorted((xa, gate))
                    fz = lambda x: z0 + (z1 - z0) * (x - x0) / (x1 - x0)  # noqa: E731
                    parapet(kit, cut_a, cut_b, ya, yb, fz(cut_a), fz(cut_b))
                else:
                    parapet(kit, x0, x1, ya, yb, z0, z1)
            # End walls across the path at the outer ends (not at the bottom entrance or the top exit).
            if t == 0 and k > 0:
                xe = -d * HX
                ea, eb = sorted((xe, xe + d * PARAPET))
                kit.box((ea, y0, za), (eb, y1, za + WALL_H), "stone", skip=("-z",), sides={"+z": coping})
            if t == 2 and k < runs - 1:
                xe = d * HX
                ea, eb = sorted((xe, xe - d * PARAPET))
                kit.box((ea, y0, zb), (eb, y1, zb + WALL_H), "stone", skip=("-z",), sides={"+z": coping})
            thirds.append(add(kit, "wall", "stone", 0))
        run_ends.append((z_start, z_end, d, thirds))
        z = z_end + climb

    # --- the flights of steps up the slope, at alternate ends ---
    for k in range(runs - 1):
        _, z_end, d, thirds = run_ends[k]
        xc = d * (HX - half)
        x0, x1 = xc - half, xc + half
        ya, yb = ys[k] + half, ys[k + 1] - half
        count = max(3, round((yb - ya) / STEP))
        depth = (yb - ya) / count
        rise_step = climb / count
        chunk = 4
        for c0 in range(0, count, chunk):
            c1 = min(count, c0 + chunk)
            kit = Kit()
            for s in range(c0, c1):
                top = z_end + rise_step * (s + 1)
                kit.box((x0, ya + s * depth, 0), (x1, ya + (s + 1) * depth, top), "stone", skip=("-z",), sides={"+z": path})
            ga, gb = ya + c0 * depth, ya + c1 * depth
            za, zb = z_end + rise_step * (c0 + 1), z_end + rise_step * c1
            for xa, xb in ((x0, x0 + PARAPET), (x1 - PARAPET, x1)):
                parapet(kit, xa, xb, ga, gb, za, zb, along="y")
            add(kit, "wall", "stone", 0)

        # A post at the outer corner of each turn, top and bottom.
        kit = Kit()
        post(kit, d * (HX - 0.15), ys[k] - half + 0.15, z_end + WALL_H)
        add(kit, "detail", "stone", 0, supports=(thirds[2],))
        kit = Kit()
        z_next = run_ends[k + 1][0]
        post(kit, d * (HX - 0.15), ys[k + 1] + half - 0.15, z_next + WALL_H)
        add(kit, "detail", "stone", 0, supports=(run_ends[k + 1][3][0],))

    return building.finish(look=f"runs{runs} start{start:+d} rise{rise} climb{climb:.2f} {path}/{coping} {posts}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(26, 36))


if __name__ == "__main__":
    previews()
