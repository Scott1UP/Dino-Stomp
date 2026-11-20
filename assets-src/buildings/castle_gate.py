"""Castle gate generator: the CLOSED gate the dinosaur smashes through.

16 m wide and about 10 m tall: two square stone towers joined by a thick wall
with a big arched gateway 5 m wide. The gateway is FILLED: a pair of chunky
wooden doors with iron straps and studs, and a portcullis grille in the head
of the arch above them. Battlements and a banner run over the arch, and the
towers carry banners, torches and flags.

How it comes apart: the two door leaves stand on the ground on their own. The
portcullis rests on the doors, so it drops when both are gone. Each half of
the arch rests on its jamb and its door leaf; the wall, battlements and banner
over the arch rest on the arch halves.

The seed varies the towers' width and height, their tops (battlements, bright
pyramid roofs, or both), the arch (round or pointed), the doors (colour,
straps), the merlons over the arch, slits and windows, and the banner and flag
colours.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/castle_gate.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_castle2 as castle  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "castle_gate"
HITS_TO_COLLAPSE = 2  # medium building
TRIANGLE_BUDGET = 1300

HALF_WIDTH = 8.0  # 16 m overall, to the edge of the tower decks
OPEN = 2.5  # half the width of the gateway
THICK = 1.8  # the wall the gateway is cut through
WALL = 0.5
STOREYS = 3
FOOT = 0.15
OVER = 0.25  # how far the tower decks oversail the walls
SPRING = 3.3  # top of the doors, where the arch springs
BRIGHTS = castle.BRIGHTS
ROOFS = castle.ROOFS


def build(building_id, seed, scheme=None, collection=None):
    """Build one closed gate. Returns (empty, stats)."""
    rng = random.Random(seed)

    tower = rng.choice([4.0, 4.3, 4.6])
    storey_h = rng.choice([2.8, 3.0, 3.1])
    top_style = rng.choice(["battlements", "roofs", "both"])
    roof_rise = rng.choice([2.2, 2.8])
    roof_colour = rng.choice(ROOFS)
    pointed = rng.choice([False, False, True])
    door_colour = rng.choice(["wood", "doorBrown"])
    strap_count = rng.choice([2, 3])
    merlon_count = rng.choice([4, 6])
    merlon_cap = rng.choice([None, "trimWhite"])
    slit_style = rng.choice(["cross", "plain"])
    windows = rng.random() < 0.6
    crest = rng.choice(["banner", "banner", "shield"])
    banner_colour = rng.choice(BRIGHTS)
    flag_colour = rng.choice(BRIGHTS)
    flag_shape = rng.choice(["pennant", "banner"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    second = [c for c in BRIGHTS if c != banner_colour][seed % 2]
    door_edge = "doorBrown" if door_colour == "wood" else "wood"

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    half = tower / 2
    height = STOREYS * storey_h
    x_in = HALF_WIDTH - OVER - tower  # the towers' faces on the gateway wall
    y0, y1 = -THICK / 2, THICK / 2
    z_crown = SPRING + (2.5 if pointed else 2.0)
    z_arch = z_crown + 0.55  # top of the arch blocks
    walk = z_arch + 1.2  # the wall walk over the gate
    front = shapes.Frame((0, y0, 0), -90)
    rear = shapes.Frame((0, y1, 0), 90)

    # --- the gateway: jambs, doors, portcullis, arch, the wall over it ---
    jambs = {}
    doors = {}
    for side in (-1, 1):
        xa, xb = sorted((side * OPEN, side * x_in))
        kit = Kit()
        kit.box((xa, y0, 0), (xb, y1, SPRING), "stone", skip=("-z",))
        # White quoins up the edge of the opening, front and back.
        for frame, flip in ((front, 1), (rear, -1)):
            ua, ub = sorted((flip * side * OPEN, flip * side * (OPEN + 0.45)))
            shapes.fbox(kit, frame, (ua, 0, 0), (ub, 0.1, SPRING), "trimWhite", skip=("-v", "-z"))
        jambs[side] = add(kit, "wall", "stone", 0)

        # A door leaf: thick planks, iron straps with studs, a ring handle.
        xa, xb = sorted((0.0, side * OPEN))
        ya, yb = -0.28, 0.2
        kit = Kit()
        kit.box((xa, ya, 0), (xb, yb, SPRING), door_colour, skip=("-z",))
        face = shapes.Frame((0, ya, 0), -90)
        back = shapes.Frame((0, yb, 0), 90)
        for k in range(strap_count):
            z = SPRING * (k + 0.5) / strap_count - 0.16
            shapes.fquad(kit, face, xa, xb, z, z + 0.32, 0.03, "tyre")
            shapes.fquad(kit, back, -xb, -xa, z, z + 0.32, 0.03, "tyre")
            for f in (0.3, 0.72):
                u = side * OPEN * f
                shapes.fquad(kit, face, u - 0.1, u + 0.1, z + 0.06, z + 0.26, 0.06, "trimWhite")
        ua, ub = sorted((side * 0.02, side * 0.3))
        shapes.fquad(kit, face, ua, ub, 0, SPRING, 0.02, door_edge)  # the meeting stile
        if strap_count == 2:
            ua, ub = sorted((side * 0.42, side * 0.74))
            shapes.fquad(kit, face, ua, ub, SPRING * 0.5 - 0.16, SPRING * 0.5 + 0.16, 0.05, "sunny")  # handle
        doors[side] = add(kit, "wall", "wood", 0)

    # The portcullis in the head of the arch, on a timber lintel across the doors.
    curve = castle.arch_points(-OPEN, OPEN, SPRING, z_crown, 3, pointed)
    kit = Kit()
    kit.box((-OPEN, -0.3, SPRING), (OPEN, 0.3, SPRING + 0.3), "doorBrown")
    for k in range(-2, 3):
        x = k * OPEN * 0.38
        top = castle.arch_height(x, curve) + 0.05
        kit.box((x - 0.13, -0.13, SPRING + 0.3), (x + 0.13, 0.13, top), "tyre", skip=("-z", "+z"))
    z_bar = SPRING + 0.3 + (z_crown - SPRING - 0.3) * 0.42
    reach = OPEN
    while reach > 0.5 and castle.arch_height(reach, curve) < z_bar + 0.3:
        reach -= 0.05
    kit.box((-reach, -0.1, z_bar), (reach, 0.1, z_bar + 0.24), "tyre", skip=("-x", "+x"))
    add(kit, "detail", "tin", 1, supports=(doors[-1], doors[1]))

    arches = {}
    uppers = {}
    for side in (-1, 1):
        kit = Kit()
        castle.arch_half(kit, side, OPEN, x_in, y0, y1, SPRING, z_crown, z_arch, "stone", trim="trimWhite", steps=3, pointed=pointed)
        arches[side] = add(kit, "wall", "stone", 1, supports=(jambs[side], doors[side]), collider="hull")

        xa, xb = sorted((0.0, side * x_in))
        kit = Kit()
        kit.box((xa, y0, z_arch), (xb, y1, walk - 0.3), "stone")
        kit.box((xa, y0 - 0.12, walk - 0.3), (xb, y1 + 0.12, walk), "trimWhite")
        x = side * x_in * 0.66
        shapes.slit(kit, front, z_arch + 0.12, walk - 0.42, u=x, width=0.28, cross=False)
        shapes.slit(kit, rear, z_arch + 0.12, walk - 0.42, u=-x, width=0.28, cross=False)
        uppers[side] = add(kit, "wall", "stone", 2, supports=(arches[side],))

    spans = castle.merlon_spans(-x_in, x_in, merlon_count)
    for side in (-1, 1):
        mine = [s for s in spans if (s[0] + s[1]) / 2 * side > 0]
        kit = Kit()
        castle.merlons(kit, front, mine, THICK, walk, 1.0, "stone", cap=merlon_cap)
        add(kit, "detail", "stone", 3, supports=(uppers[side],))

    # Something bright over the arch.
    kit = Kit()
    if crest == "banner":
        shapes.banner(kit, front, 0, walk - 0.35, 1.7, 1.9, banner_colour, v=0.16)
        shapes.fquad(kit, front, -0.4, 0.4, walk - 1.45, walk - 0.75, 0.19, "trimWhite")
    else:
        castle.shield(kit, front, 0, walk - 0.2, 1.7, banner_colour, second, v=0.16)
    add(kit, "detail", "wood", 2, supports=(uppers[-1], uppers[1]))

    # --- the two towers ---
    for side in (-1, 1):
        cx = side * (HALF_WIDTH - OVER - half)
        frames = castle.rect_frames(cx, 0, half, half)
        outer = "right" if side > 0 else "left"
        inner = "left" if side > 0 else "right"

        below = None
        storeys = []
        for s in range(STOREYS):
            z0 = s * storey_h
            z1 = z0 + storey_h
            grow = FOOT if s == 0 else 0.0
            v = grow + 0.04
            here = {}
            for name in ("front", "back", "left", "right"):
                frame = frames[name]
                kit = Kit()
                castle.box_wall(kit, frame, name, half, half, z0, z1, WALL, grow=grow, skip=("-z",) if s == 0 else ())
                if name == "front":
                    if s == 0:
                        castle.torch(kit, frame, 0, 1.9, v=grow)
                    elif s == 2:
                        if windows:
                            castle.arched_window(kit, frame, -0.5, 0.5, z0 + 0.7, z0 + 2.2, v=v)
                        else:
                            shapes.slit(kit, frame, z0 + 0.7, z0 + 2.2, cross=slit_style == "cross", v=v)
                elif name == "back":
                    if s == 0:
                        shapes.fquad(kit, frame, -0.65, 0.65, 0, 2.3, v, "doorBrown")  # the guard's door
                        shapes.fbox(kit, frame, (-0.8, grow, 2.3), (0.8, grow + 0.14, 2.52), "trimWhite", skip=("-v",))
                    elif s == 2 and windows:
                        castle.arched_window(kit, frame, -0.5, 0.5, z0 + 0.7, z0 + 2.2, v=v)
                    else:
                        shapes.slit(kit, frame, z0 + 0.7, z0 + 2.2, cross=slit_style == "cross", v=v)
                elif name == outer and s > 0:
                    shapes.slit(kit, frame, z0 + 0.7, z0 + 2.2, cross=slit_style == "cross", v=v)
                supports = (below[name],) if below else ()
                here[name] = add(kit, "wall", "stone", s, supports=supports)
            below = here
            storeys.append(here)

            if s < STOREYS - 1:
                kit = Kit()
                kit.box((cx - half + WALL, -half + WALL, z1 - 0.2), (cx + half - WALL, half - WALL, z1), "interiorCream")
                add(kit, "floor", "wood", s + 1, supports=list(here.values()))

        # Top deck: a white band that oversails the walls a little.
        kit = Kit()
        kit.box((cx - half - OVER, -half - OVER, height), (cx + half + OVER, half + OVER, height + 0.35), "trimWhite")
        deck = add(kit, "floor", "stone", STOREYS, supports=list(storeys[-1].values()))
        deck_z = height + 0.35
        edge = half + OVER
        top_frames = castle.rect_frames(cx, 0, edge, edge)

        crown = [deck]
        if top_style in ("battlements", "both"):
            m = 0.95
            row = castle.merlon_spans(-edge, edge, 3)
            for name, side_name in (("front", "left"), ("back", "right")):
                kit = Kit()
                castle.merlons(kit, top_frames[name], row, m, deck_z, 1.1)
                castle.merlons(kit, top_frames[side_name], row[1:2], m, deck_z, 1.1)
                add(kit, "detail", "stone", STOREYS, supports=(deck,))

        flag_z = deck_z
        if top_style in ("roofs", "both"):
            r = edge + 0.3 if top_style == "roofs" else edge - 1.15
            rise = roof_rise if top_style == "roofs" else roof_rise * 0.85
            kit = Kit()
            castle.pyramid(kit, cx, 0, r, r, deck_z, rise, roof_colour)
            crown = [add(kit, "roof", "stone", STOREYS + 1, supports=(deck,), collider="hull")]
            flag_z = deck_z + rise - 0.4

        kit = Kit()
        shapes.flag(kit, cx, 0, flag_z, 2.8, flag_colour, size=1.5, shape=flag_shape)
        add(kit, "detail", "wood", STOREYS + 2, supports=crown)

        # A banner on the front of each tower.
        kit = Kit()
        shapes.banner(kit, frames["front"], 0, storey_h * 2 - 0.1, 1.3, 2.4, second if crest == "banner" else banner_colour)
        shapes.fquad(kit, frames["front"], -0.32, 0.32, storey_h * 2 - 1.3, storey_h * 2 - 0.66, 0.09, "trimWhite")
        add(kit, "detail", "wood", 1, supports=(storeys[1]["front"],))

    return building.finish(
        look=f"towers={tower} storey={storey_h} {top_style}/{roof_colour}/arch-{'pointed' if pointed else 'round'}"
        f"/doors-{door_colour}-{strap_count}/merlons-{merlon_count}/{crest}" + ("/windows" if windows else "")
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(26, 26))


if __name__ == "__main__":
    previews()
