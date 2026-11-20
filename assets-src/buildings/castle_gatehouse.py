"""Castle gatehouse generator.

The castle's open gate: two square stone towers either side of a clear gap
8 m wide. NOTHING spans the gap, at any height, so the tallest dino can walk
straight through. The gateway is suggested instead by half-arch brackets
springing from the towers' inner faces (they reach 1 m into the gap, high up),
by gate leaves folded back flat against the inner faces, and by banners and
flags on the towers themselves.

The seed varies the towers' width and height, their tops (battlements, bright
pyramid roofs, or both), the brackets (arched or stepped), the gate leaves,
slits and windows, and the banner and flag colours.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/castle_gatehouse.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "castle_gatehouse"
HITS_TO_COLLAPSE = 2  # medium building
TRIANGLE_BUDGET = 900

GAP = 8.0  # clear width between the towers, kept free of anything solid
WALL = 0.5
STOREYS = 3
FOOT = 0.15
BRIGHTS = ["tomato", "sunny", "cobalt"]
ROOFS = ["tomato", "cobalt", "tangerine", "bubblegum"]


def build(building_id, seed, scheme=None, collection=None):
    """Build one gatehouse. Returns (empty, stats)."""
    rng = random.Random(seed)

    tower = rng.choice([3.8, 4.0, 4.4])
    storey_h = rng.choice([2.8, 3.0, 3.2])
    top_style = rng.choice(["battlements", "roofs", "both"])
    roof_rise = rng.choice([2.6, 3.4])
    roof_colour = rng.choice(ROOFS)
    bracket = rng.choice(["arch", "arch", "steps"])
    leaves = rng.random() < 0.7
    slit_style = rng.choice(["cross", "plain"])
    windows = rng.random() < 0.5
    banner_colour = rng.choice(BRIGHTS)
    flag_colour = rng.choice(BRIGHTS)
    flag_shape = rng.choice(["pennant", "banner"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    half = tower / 2
    height = STOREYS * storey_h

    for side in (-1, 1):
        cx = side * (GAP / 2 + half)
        inner_x = side * GAP / 2  # the tower face on the gateway
        into_gap = -side
        # Frames on the tower's four faces. Front and back run along X; the others along Y.
        faces = {
            "front": shapes.Frame((cx, -half, 0), -90),
            "back": shapes.Frame((cx, half, 0), 90),
            "inner": shapes.Frame((inner_x, 0, 0), 0 if into_gap > 0 else 180),
            "outer": shapes.Frame((cx + side * half, 0, 0), 0 if side > 0 else 180),
        }

        # --- walls: four a storey ---
        below = None
        storeys = []
        for s in range(STOREYS):
            z0 = s * storey_h
            z1 = z0 + storey_h
            grow = FOOT if s == 0 else 0.0  # a stepped-out foot, except into the gateway
            here = {}
            for name in ("front", "back", "inner", "outer"):
                frame = faces[name]
                kit = Kit()
                if name in ("front", "back"):
                    xa = cx - half - (grow if side < 0 else 0)
                    xb = cx + half + (grow if side > 0 else 0)
                    ya, yb = (-half - grow, -half + WALL) if name == "front" else (half - WALL, half + grow)
                    kit.box((xa, ya, z0), (xb, yb, z1), "stone", sides={"+y" if name == "front" else "-y": "interiorCream"})
                    v = grow + 0.04
                    if s < 2:
                        # A white jamb up the gateway corner, front and back, to frame the opening.
                        ua, ub = sorted((-side * half * frame.t[0], -side * (half - 0.7) * frame.t[0]))
                        shapes.fbox(kit, frame, (ua, grow, z0), (ub, grow + 0.14, z1), "trimWhite", skip=("-v", "-z") if s == 0 else ("-v",))
                    if s == 0:
                        pass
                    elif s == STOREYS - 1 and windows:
                        shapes.fwindow(kit, frame, -0.5, 0.5, z0 + 0.9, z0 + 2.2, v=v)
                    elif not (name == "front" and s == 1):
                        shapes.slit(kit, frame, z0 + 0.7, z0 + 2.2, cross=slit_style == "cross", v=v)
                else:
                    on_gap = name == "inner"
                    x_face = inner_x if on_gap else cx + side * (half + grow)
                    x_in = inner_x + side * WALL if on_gap else cx + side * (half - WALL)
                    xa, xb = sorted((x_face, x_in))
                    inside = "+x" if x_in > x_face else "-x"
                    kit.box((xa, -half + WALL, z0), (xb, half - WALL, z1), "stone", sides={inside: "interiorCream"})
                    if s == 0 and on_gap and not leaves:
                        shapes.fquad(kit, frame, -0.65, 0.65, 0, 2.4, 0.04, "doorBrown")  # the guard's door
                    elif s > 0 and not on_gap:
                        shapes.slit(kit, frame, z0 + 0.7, z0 + 2.2, cross=slit_style == "cross", v=grow + 0.04)
                supports = (below[name],) if below else ()
                here[name] = add(kit, "wall", "stone", s, supports=supports)
            below = here
            storeys.append(here)

            if s < STOREYS - 1:
                kit = Kit()
                kit.box((cx - half + WALL, -half + WALL, z1 - 0.2), (cx + half - WALL, half - WALL, z1), "interiorCream")
                add(kit, "floor", "wood", s + 1, supports=list(here.values()))

        # --- top deck: a white band that oversails the walls a little ---
        over = 0.25
        kit = Kit()
        kit.box((cx - half - over, -half - over, height), (cx + half + over, half + over, height + 0.35), "trimWhite")
        deck = add(kit, "floor", "stone", STOREYS, supports=list(storeys[-1].values()))
        deck_z = height + 0.35
        edge = half + over

        # --- battlements: a front row and a back row ---
        crown = [deck]
        if top_style in ("battlements", "both"):
            m = 0.95
            for row, y in (("front", -edge), ("back", edge - m)):
                kit = Kit()
                xs = [cx - edge, cx - m / 2, cx + edge - m]
                for x in xs:
                    kit.box((x, y, deck_z), (x + m, y + m, deck_z + 1.1), "stone", skip=("-z",))
                # One more on the side, between the corners.
                sx = cx - edge if (row == "front") == (side < 0) else cx + edge - m
                kit.box((sx, -m / 2, deck_z), (sx + m, m / 2, deck_z + 1.1), "stone", skip=("-z",))
                add(kit, "detail", "stone", STOREYS, supports=(deck,))

        # --- pyramid roof ---
        flag_z = deck_z
        if top_style in ("roofs", "both"):
            r = edge + 0.3 if top_style == "roofs" else edge - 1.15
            rise = roof_rise if top_style == "roofs" else roof_rise * 0.85
            kit = Kit()
            base = [(cx - r, -r, deck_z), (cx + r, -r, deck_z), (cx + r, r, deck_z), (cx - r, r, deck_z)]
            apex = (cx, 0, deck_z + rise)
            kit.convex([base] + [[base[k], base[(k + 1) % 4], apex] for k in range(4)], roof_colour)
            crown = [add(kit, "roof", "stone", STOREYS + 1, supports=(deck,), collider="hull")]
            flag_z = deck_z + rise - 0.4

        kit = Kit()
        shapes.flag(kit, cx, 0, flag_z, 2.8, flag_colour, size=1.5, shape=flag_shape)
        add(kit, "detail", "wood", STOREYS + 2, supports=crown)

        # --- banner on the front ---
        kit = Kit()
        shapes.banner(kit, faces["front"], 0, storey_h * 2 - 0.1, 1.3, 2.4, banner_colour)
        shapes.fquad(kit, faces["front"], -0.32, 0.32, storey_h * 2 - 1.3, storey_h * 2 - 0.66, 0.09, "trimWhite")
        add(kit, "detail", "wood", 1, supports=(storeys[1]["front"],))

        # --- the springing of an arch, on the inner face: it reaches 1 m into the gap and stops ---
        reach = 1.0
        z_spring = storey_h * 2
        z_top = z_spring + 2.0
        d = into_gap
        ya, yb = -half, half
        kit = Kit()
        if bracket == "arch":
            corner = (inner_x, z_top)
            a0 = (inner_x, z_spring)
            a1 = (inner_x + d * reach * 0.3, z_spring + 2.0 * 0.72)
            a2 = (inner_x + d * reach, z_top)
            kit.extrude_y([corner, a0, a1], ya, yb, "trimWhite")
            kit.extrude_y([corner, a1, a2], ya, yb, "trimWhite")
        else:
            xa, xb = sorted((inner_x, inner_x + d * reach * 0.5))
            kit.box((xa, ya, z_spring + 0.4), (xb, yb, z_top), "trimWhite")
            xa, xb = sorted((inner_x + d * reach * 0.5, inner_x + d * reach))
            kit.box((xa, ya, z_spring + 1.2), (xb, yb, z_top), "trimWhite")
        add(kit, "detail", "stone", 2, supports=(storeys[2]["inner"],), collider="hull")

        # --- a gate leaf, folded back flat against the inner face ---
        if leaves:
            xa, xb = sorted((inner_x, inner_x + d * 0.22))
            kit = Kit()
            kit.box((xa, -half + 0.3, 0.15), (xb, half - 0.3, storey_h + 1.6), pal["door"])
            face = shapes.Frame((inner_x + d * 0.22, 0, 0), 0 if d > 0 else 180)
            for z in (1.0, storey_h + 0.7):
                shapes.fquad(kit, face, -half + 0.3, half - 0.3, z, z + 0.3, 0.03, "tyre")
            add(kit, "detail", "wood", 0, supports=(storeys[0]["inner"],))

    return building.finish(
        look=f"towers={tower} storey={storey_h} {top_style}/{roof_colour}/bracket-{bracket}"
        + ("/leaves" if leaves else "")
        + ("/windows" if windows else "")
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(30, 30))


if __name__ == "__main__":
    previews()
