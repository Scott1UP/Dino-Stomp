"""Toy train generator.

A toy steam engine pulling two or three carriages, in a line along X and
about 14 m long: a round boiler with a funnel, a dome and a cow-catcher, a
boxy cab, and chunky roller wheels. The carriages are open wagons with a
load, coaches with windows, or tankers. The seed varies which way the train
is heading, the number and kinds of carriage, and the colours.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/toy_train.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_fair as fair  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import BRIGHT, apothem, panel_y, prism  # noqa: E402

TYPE = "toy_train"
HITS_TO_COLLAPSE = 1  # small building
TRIANGLE_BUDGET = 400

HALF = 0.95  # half the width of a body
WHEEL_HALF = 1.2  # the rollers stick out either side
BIG = 0.8
SMALL = 0.52
FLOOR = 0.55
DECK = 0.95
GAP = 0.45
ENGINE = 4.4
NOSE = 0.9  # the cow-catcher sticks out this far in front
KINDS = ("wagon", "coach", "tanker")


def _roller(kit, x, radius, hub=None):
    """A pair of wheels as one fat roller across the train, standing on the ground."""
    z = apothem(radius, 6)
    prism(kit, (x, z), -WHEEL_HALF, WHEEL_HALF, radius, radius, 6, "tyre", axis="y")
    if hub:
        for facing in (-1, 1):
            panel_y(kit, x - radius * 0.4, x + radius * 0.4, z - radius * 0.4, z + radius * 0.4, facing * (WHEEL_HALF + 0.02), facing, hub)


def build(building_id, seed, scheme=None, collection=None):
    """Build one train. Returns (empty, stats)."""
    rng = random.Random(seed)

    heading = -1 if seed % 2 else 1  # alternates, so neighbouring seeds always differ
    count = rng.choice([2, 3, 3])
    kinds = [rng.choice(KINDS) for _ in range(3)]
    if count == 3:
        # Tankers cost the most triangles: a long train gets one at most.
        seen = False
        for n, kind in enumerate(kinds):
            if kind == "tanker":
                if seen:
                    kinds[n] = ("wagon", "coach")[n % 2]
                seen = True
    colours = rng.sample(BRIGHT, 5)  # engine, cab, then the carriages
    funnel = rng.choice(["flared", "straight"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)

    car_len = 2.7 if count == 3 else 3.9
    total = ENGINE + count * (GAP + car_len)
    shift = -(total - NOSE) / 2  # s = 0 is the front of the chassis; centre the whole train, cow-catcher included

    def add(kit, *args, **kwargs):
        for points, _ in kit.faces:
            for p in points:
                p.x += shift
        if heading == 1:
            fair.mirror_x(kit)
        return building.add(kit, *args, **kwargs)

    engine_colour, cab_colour = colours[0], colours[1]
    trim = "trimWhite"

    # --- engine: wheels ---
    kit = Kit()
    _roller(kit, 0.85, SMALL)
    _roller(kit, 2.25, BIG, cab_colour)
    _roller(kit, 3.75, BIG, cab_colour)
    wheels = add(kit, "wall", "tin", 0, collider="hull")

    # --- engine: chassis, boiler, funnel, dome and cow-catcher ---
    boiler_z = DECK + 0.8
    kit = Kit()
    kit.box((0.0, -HALF, FLOOR), (ENGINE, HALF, DECK), cab_colour)
    prism(kit, (0, boiler_z), 0.2, 2.9, 0.9, 0.9, 6, engine_colour, axis="x", bottom_colour=trim)
    if funnel == "flared":
        prism(kit, (0.85, 0), boiler_z + 0.7, boiler_z + 1.9, 0.32, 0.58, 6, "tyre", bottom=False)
    else:
        prism(kit, (0.85, 0), boiler_z + 0.7, boiler_z + 1.8, 0.42, 0.42, 6, "tyre", bottom=False, top_colour=trim)
    prism(kit, (2.0, 0), boiler_z + 0.7, boiler_z + 1.15, 0.45, 0.25, 4, "sunny" if engine_colour != "sunny" else "tomato", bottom=False)
    kit.extrude_y([(0.0, 0.15), (0.0, DECK), (-NOSE, 0.15)], -HALF, HALF, trim)
    body = add(kit, "detail", "tin", 0, supports=(wheels,), collider="hull")

    # --- engine: the cab ---
    kit = Kit()
    kit.box((2.9, -HALF, DECK), (ENGINE, HALF, 3.1), cab_colour, skip=("-z",))
    kit.box((2.65, -HALF - 0.2, 3.1), (ENGINE + 0.25, HALF + 0.2, 3.4), engine_colour)
    for facing in (-1, 1):
        panel_y(kit, 3.2, 4.1, 2.0, 2.8, facing * (HALF + 0.02), facing, "windowBlue")
    add(kit, "detail", "tin", 1, supports=(wheels, body))

    # --- carriages ---
    for n in range(count):
        s0 = ENGINE + GAP + n * (car_len + GAP)
        s1 = s0 + car_len
        kind = kinds[n]
        colour = colours[2 + n]

        kit = Kit()
        _roller(kit, s0 + 0.7, SMALL)
        _roller(kit, s1 - 0.7, SMALL)
        under = add(kit, "wall", "tin", 0, collider="hull")

        kit = Kit()
        # The coupling to whatever is in front.
        kit.box((s0 - GAP, -0.2, FLOOR + 0.05), (s0, 0.2, FLOOR + 0.35), "tyre", skip=("-x", "+x", "-z"))
        if kind == "wagon":
            kit.box((s0, -HALF, FLOOR), (s1, HALF, 1.75), colour, sides={"+z": "tyre"})
            load = ("wood", "sunny", "stone")[(seed + n) % 3]
            if load == colour:
                load = "wood"
            prism(kit, ((s0 + s1) / 2, 0), 1.75, 2.45, car_len * 0.62, car_len * 0.3, 4, load, bottom=False, scale=(1.0, 0.75 / (car_len * 0.44)))
        elif kind == "coach":
            kit.box((s0, -HALF, FLOOR), (s1, HALF, 2.6), colour)
            kit.extrude_x([(-HALF - 0.15, 2.6), (HALF + 0.15, 2.6), (HALF - 0.3, 3.0), (-HALF + 0.3, 3.0)], s0 - 0.15, s1 + 0.15, trim)
            for facing in (-1, 1):
                panel_y(kit, s0 + 0.35, s1 - 0.35, 1.6, 2.3, facing * (HALF + 0.02), facing, "windowBlue")
        else:
            kit.box((s0, -HALF, FLOOR), (s1, HALF, DECK), "tyre")
            prism(kit, (0, DECK + 0.85), s0 + 0.1, s1 - 0.1, 1.0, 1.0, 6, colour, axis="x", bottom_colour=trim, top_colour=trim)
            kit.box(((s0 + s1) / 2 - 0.35, -0.35, DECK + 1.6), ((s0 + s1) / 2 + 0.35, 0.35, DECK + 2.05), trim, skip=("-z",))
        add(kit, "detail", "tin", 0, supports=(under,), collider="hull" if kind != "coach" else "box")

    return building.finish(look=f"heading{heading:+d} {'/'.join(kinds[:count])} {funnel} {'/'.join(colours[: 2 + count])}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(19, 9))


if __name__ == "__main__":
    previews()
