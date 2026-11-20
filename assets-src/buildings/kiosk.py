"""Ice cream kiosk generator.

A little round (8-sided) kiosk with a serving hatch and counter at the front,
a door at the back, a cone roof and a GIANT ice cream cone standing on top.
The seed varies its size, the roof's pitch and stripes, how far the hatch
wraps round, the awning, and the ice cream itself (scoops, flavours, a flake,
a cherry).

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/kiosk.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "kiosk"
HITS_TO_COLLAPSE = 1  # small building
TRIANGLE_BUDGET = 400

WALL = 0.3
FLAVOURS = ["bubblegum", "trimWhite", "sunny", "leaf", "tomato"]


def build(building_id, seed, scheme=None, collection=None):
    """Build one kiosk. Returns (empty, stats)."""
    rng = random.Random(seed)

    radius = rng.choice([2.2, 2.5, 2.8])
    height = rng.choice([2.8, 3.1, 3.4])
    rise = rng.choice([1.6, 2.1, 2.7])
    wall_style = rng.choice(["solid", "stripes", "stripes", "skirt"])
    roof_style = rng.choice(["solid", "stripes"])
    wrap = rng.choice([False, False, True])  # hatch on three facets instead of one
    awning = rng.choice(["none", "sloped", "sloped", "flat"])
    scoops = rng.choice([1, 2, 2, 3])
    topping = rng.choice(["flake", "cherry", "both"])
    flavours = rng.sample(FLAVOURS, 3)
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    hatch_facets = {7, 0, 1} if wrap else {0}
    sill = 1.1
    lintel = height - 0.75
    side = shapes.side_length(radius)

    def wall_colour(i):
        if wall_style == "stripes" and i % 2 == 1:
            return pal["trim"]
        return pal["wall"]

    # --- walls: one module per facet ---
    walls = []
    for i in range(8):
        kit = Kit()
        colour = wall_colour(i)
        frame = shapes.facet_frame(i, radius)
        if i in hatch_facets:
            # A real opening: sill, lintel and two jambs, so the inside shows.
            shapes.wall_segment(kit, i, radius, radius - WALL, 0, sill, colour, "interiorCream")
            shapes.wall_segment(kit, i, radius, radius - WALL, lintel, height, colour, "interiorCream")
            shapes.wall_segment(kit, i, radius, radius - WALL, sill, lintel, colour, "interiorCream", f1=0.14)
            shapes.wall_segment(kit, i, radius, radius - WALL, sill, lintel, colour, "interiorCream", f0=0.86)
        else:
            shapes.wall_segment(kit, i, radius, radius - WALL, 0, height, colour, "interiorCream")
            if i == 4:
                # The back door.
                shapes.fquad(kit, frame, -0.6, 0.6, 0, 2.3, 0.04, pal["door"])
                shapes.fquad(kit, frame, -0.3, 0.3, 1.4, 2.0, 0.07, "windowBlue")
            elif i in (2, 6) and not wrap:
                # A little round-ish side window.
                shapes.fwindow(kit, frame, -0.45, 0.45, 1.3, 2.3)
        if wall_style == "skirt":
            shapes.fbox(kit, frame, (-side / 2, 0, 0), (side / 2, 0.08, 0.7), pal["roof"], skip=("-v", "-z", "-u", "+u"))
        walls.append(add(kit, "wall", "plaster", 0))

    # --- counter and awning: one detail per hatch facet ---
    for i in sorted(hatch_facets):
        frame = shapes.facet_frame(i, radius)
        kit = Kit()
        shapes.fbox(kit, frame, (-side / 2 + 0.05, -WALL, sill), (side / 2 - 0.05, 0.45, sill + 0.12), pal["trim"])
        if awning == "sloped":
            p = frame.at
            u0, u1 = -side / 2, side / 2
            kit.convex(
                [
                    [p(u0, 0, lintel + 0.55), p(u1, 0, lintel + 0.55), p(u1 + 0.1, 0.95, lintel + 0.05), p(u0 - 0.1, 0.95, lintel + 0.05)],
                    [p(u0, 0, lintel + 0.4), p(u1, 0, lintel + 0.4), p(u1 + 0.1, 0.95, lintel - 0.1), p(u0 - 0.1, 0.95, lintel - 0.1)],
                    [p(u0, 0, lintel + 0.4), p(u0, 0, lintel + 0.55), p(u0 - 0.1, 0.95, lintel + 0.05), p(u0 - 0.1, 0.95, lintel - 0.1)],
                    [p(u1, 0, lintel + 0.4), p(u1, 0, lintel + 0.55), p(u1 + 0.1, 0.95, lintel + 0.05), p(u1 + 0.1, 0.95, lintel - 0.1)],
                    [p(u0 - 0.1, 0.95, lintel + 0.05), p(u1 + 0.1, 0.95, lintel + 0.05), p(u1 + 0.1, 0.95, lintel - 0.1), p(u0 - 0.1, 0.95, lintel - 0.1)],
                ],
                pal["door"] if i == 0 else pal["trim"],
            )
        elif awning == "flat":
            shapes.fbox(kit, frame, (-side / 2, 0, lintel + 0.1), (side / 2, 0.8, lintel + 0.25), pal["door"], skip=("-v",))
        add(kit, "detail", "wood", 0, supports=(walls[i],), collider="hull" if awning == "sloped" else "box")

    # --- roof: a cone with a good overhang, flattened at the tip for the ice cream to stand on ---
    eave = radius + 0.5
    tip = 0.4
    roof_top = height + rise
    kit = Kit()
    shapes.frustum(
        kit,
        eave,
        tip,
        height,
        roof_top,
        pal["roof"],
        stripes=[pal["roof"], pal["trim"]] if roof_style == "stripes" else None,
    )
    roof = add(kit, "roof", "wood", 1, supports=walls, collider="hull")

    # --- the giant ice cream cone ---
    kit = Kit()
    wafer_top = roof_top + 1.9
    wafer_r = 1.0
    shapes.frustum(kit, 0, wafer_r, roof_top - 0.3, wafer_top, "wood", sides=6, top=False)
    z = wafer_top + 0.3
    r = 1.3
    top = z
    for s in range(scoops):
        shapes.ball(kit, 0, 0, z, r, flavours[s], squash=0.8)
        top = z + r * 0.8 - 0.2  # just inside the top scoop
        z += r * 1.0
        r *= 0.8
    spare = scoops < 3
    if topping in ("flake", "both") and spare:
        kit.box((0.25, -0.12, top - 0.3), (0.5, 0.12, top + 0.9), "doorBrown", skip=("-z",))
    if topping in ("cherry", "both") and scoops < 2 or (topping == "cherry" and spare):
        shapes.ball(kit, -0.15, 0, top + 0.2, 0.32, "tomato" if flavours[scoops - 1] != "tomato" else "sunny", sides=4)
    add(kit, "detail", "wood", 2, supports=(roof,), collider="hull")

    return building.finish(
        look=f"r={radius} h={height} rise={rise} {wall_style}/{roof_style}/wrap-{wrap}/{awning}/scoops-{scoops}/{topping}"
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(13, 14))


if __name__ == "__main__":
    previews()
