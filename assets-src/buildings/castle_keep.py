"""Castle keep generator: the main hall in the middle of the castle.

A chunky rectangular stone keep, three storeys (11 m) tall and about 14 m by
11 m over its corner turrets (the walls are 11.5-12.5 m by 8.5-9.5 m). An arched door with steps and torches in the middle of the front,
arrow slits on the ground floor and arched windows above, white bands at each
floor, a flat roof ringed with battlements, a little turret corbelled out from
each corner, and big banners down the front.

Inside it is a dolls' house: cream walls and a floor slab at every storey.
Each storey's walls are ten pieces (three front, three back, two each side),
each resting on the piece below.

The seed varies the size, the storey height, the corner turrets (bright cones
or flat tops), what stands on the roof (a cap house with a bright gabled roof,
or a great flag), the windows on the top floor, the ground floor, and the
banners' layout and colours. The door takes the scheme's door colour.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/castle_keep.py
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

TYPE = "castle_keep"
HITS_TO_COLLAPSE = 3  # tall landmark
TRIANGLE_BUDGET = 1800

WALL = 0.6
STOREYS = 3
FOOT = 0.2
OVER = 0.3  # how far the roof deck oversails the walls
PIECES = {"front": 3, "back": 3, "left": 2, "right": 2}
BRIGHTS = castle.BRIGHTS
ROOFS = castle.ROOFS


def build(building_id, seed, scheme=None, collection=None):
    """Build one keep. Returns (empty, stats)."""
    rng = random.Random(seed)

    width = rng.choice([11.5, 12.0, 12.5])
    depth = rng.choice([8.5, 9.5])
    storey_h = rng.choice([3.1, 3.3, 3.5])
    turret_style = rng.choice(["cone", "cone", "flat"])
    turret_colour = rng.choice(ROOFS)
    roof_feature = rng.choice(["caphouse", "flag", "caphouse"])
    top_windows = rng.choice(["arched", "pointed", "slits"])
    ground = rng.choice(["slits", "slits", "windows"])
    banner_layout = rng.choice(["pair", "pair", "centre", "trio"])
    banner_colour = rng.choice(BRIGHTS)
    second = rng.choice([c for c in BRIGHTS if c != banner_colour])
    slit_style = rng.choice(["cross", "plain"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]
    door_colour = pal["door"]

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    hx, hy = width / 2, depth / 2
    height = STOREYS * storey_h
    frames = castle.rect_frames(0, 0, hx, hy)
    banner_us = {"pair": [-width / 6, width / 6], "centre": [0.0], "trio": [-width / 6, 0.0, width / 6]}[banner_layout]
    centre_banner = 0.0 in banner_us

    def window(kit, frame, u, z0, v, style, wide=0.65):
        if style == "slits":
            shapes.slit(kit, frame, z0 + 0.8, z0 + 2.3, u=u, width=0.34, cross=slit_style == "cross", v=v)
        else:
            castle.arched_window(kit, frame, u - wide, u + wide, z0 + 0.85, z0 + 2.55, v=v, pointed=style == "pointed")

    def side_of(frame, u):
        """-1 or +1: which half of the keep a point on a face is in (0 on the centre line)."""
        x = frame.at(u, 0, 0)[0]
        return 0 if abs(x) < 0.05 else (1 if x > 0 else -1)

    # --- walls: ten pieces a storey, each on the piece below ---
    walls = []  # per storey: {(name, k): (module id, side)}
    for s in range(STOREYS):
        z0 = s * storey_h
        z1 = z0 + storey_h
        grow = FOOT if s == 0 else 0.0
        v = grow + 0.04
        here = {}
        for name, count in PIECES.items():
            frame = frames[name]
            full = hx if name in ("front", "back") else hy - WALL
            for k in range(count):
                ua = -full + 2 * full * k / count
                ub = -full + 2 * full * (k + 1) / count
                mid = (ua + ub) / 2
                kit = Kit()
                ends = name in ("front", "back")
                shapes.fbox(
                    kit,
                    frame,
                    (ua - (grow if ends and k == 0 else 0), -WALL, z0),
                    (ub + (grow if ends and k == count - 1 else 0), grow, z1),
                    "stone",
                    skip=("-z",) if s == 0 else (),
                    sides={"-v": "interiorCream"},
                )
                middle = count == 3 and k == 1
                if name == "front":
                    if s == 0 and middle:
                        # The great door, with a pale surround and a torch either side.
                        castle.arched_panel(kit, frame, -1.4, 1.4, 0, 3.0, v, "trimWhite", steps=3)
                        castle.arched_panel(kit, frame, -1.1, 1.1, 0, 2.72, v + 0.03, door_colour, steps=3)
                        shapes.fquad(kit, frame, -0.06, 0.06, 0, 2.72, v + 0.06, "tyre")
                        for u in (-1.66, 1.66):
                            castle.torch(kit, frame, u, 1.9, v=grow)
                    elif s == 0:
                        window(kit, frame, mid, z0, v, "slits" if ground == "slits" else "arched", wide=0.5)
                    elif middle and centre_banner:
                        pass  # the banner hangs here
                    else:
                        window(kit, frame, mid, z0, v, "arched" if s == 1 else top_windows)
                elif name == "back":
                    if s == 0 and middle:
                        shapes.fquad(kit, frame, -0.7, 0.7, 0, 2.3, v, "doorBrown")
                        shapes.fbox(kit, frame, (-0.9, grow, 2.3), (0.9, grow + 0.14, 2.54), "trimWhite", skip=("-v",))
                    elif s == 0:
                        window(kit, frame, mid, z0, v, "slits")
                    else:
                        window(kit, frame, mid, z0, v, "arched" if s == 1 else top_windows)
                else:
                    window(kit, frame, mid, z0, v, "slits" if s == 0 else ("arched" if s == 1 else top_windows))
                supports = (walls[-1][(name, k)][0],) if walls else ()
                here[(name, k)] = (add(kit, "wall", "stone", s, supports=supports), side_of(frame, mid))
        walls.append(here)

        def holders(side, storey=here):
            return [m for m, where in storey.values() if where in (side, 0)]

        # A floor slab on top of this storey, in two halves: it pokes out as a white band.
        if s < STOREYS - 1:
            for side in (-1, 1):
                xa, xb = sorted((0.0, side * (hx + 0.15)))
                kit = Kit()
                kit.box((xa, -hy - 0.15, z1 - 0.25), (xb, hy + 0.15, z1), "trimWhite", sides={"+z": "interiorCream", "-z": "interiorCream"})
                add(kit, "floor", "wood", s + 1, supports=holders(side))

    # --- the roof deck, in two halves ---
    deck_z = height + 0.35
    ex, ey = hx + OVER, hy + OVER
    decks = {}
    for side in (-1, 1):
        xa, xb = sorted((0.0, side * ex))
        kit = Kit()
        kit.box((xa, -ey, height), (xb, ey, deck_z), "trimWhite", sides={"-z": "interiorCream"})
        decks[side] = add(kit, "floor", "stone", STOREYS, supports=[m for m, where in walls[-1].values() if where in (side, 0)])

    # --- battlements between the corner turrets ---
    top_frames = castle.rect_frames(0, 0, ex, ey)
    corner = 1.55  # left clear at each end for the turrets
    for name in ("front", "back"):
        spans = castle.merlon_spans(-ex + corner, ex - corner, 6)
        for part in (spans[:3], spans[3:]):
            kit = Kit()
            castle.merlons(kit, top_frames[name], part, 0.7, deck_z, 1.1)
            add(kit, "detail", "stone", STOREYS, supports=(decks[side_of(top_frames[name], part[1][0])],))
    for name in ("left", "right"):
        spans = castle.merlon_spans(-ey + corner, ey - corner, 4)
        kit = Kit()
        castle.merlons(kit, top_frames[name], spans, 0.7, deck_z, 1.1)
        add(kit, "detail", "stone", STOREYS, supports=(decks[-1 if name == "left" else 1],))

    # --- a little turret corbelled out from each corner ---
    r = 1.1
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * (ex - 0.45), sy * (ey - 0.45)
            z_top = deck_z + (1.7 if turret_style == "cone" else 2.1)
            kit = Kit()
            shapes.frustum(kit, 0.0, r, height - 1.7, height - 0.3, "stone", sides=6, cx=cx, cy=cy, top=False)
            shapes.frustum(kit, r, r, height - 0.3, z_top, "stone", sides=6, cx=cx, cy=cy, bottom=False, top=False)
            if turret_style == "cone":
                shapes.frustum(kit, r + 0.35, 0, z_top, z_top + 2.4, turret_colour, sides=6, cx=cx, cy=cy)
            else:
                shapes.frustum(kit, r + 0.22, r + 0.22, z_top, z_top + 0.35, "trimWhite", sides=6, cx=cx, cy=cy)
            facet = {(-1, -1): 5, (1, -1): 1, (1, 1): 2, (-1, 1): 4}[(sx, sy)]
            shapes.slit(kit, shapes.facet_frame(facet, r, sides=6, cx=cx, cy=cy), deck_z + 0.3, z_top - 0.3, width=0.3, cross=False)
            add(kit, "detail", "stone", STOREYS, supports=(decks[sx],), collider="hull")

    # --- on the roof: a cap house with a bright gable, or a great flag ---
    both = (decks[-1], decks[1])
    if roof_feature == "caphouse":
        cw, cd, ch = 2.3, 1.7, 2.1
        kit = Kit()
        kit.box((-cw, -cd, deck_z), (cw, cd, deck_z + ch), "stone", skip=("-z", "+z"))
        face = shapes.Frame((0, -cd, 0), -90)
        shapes.fquad(kit, face, -0.55, 0.55, deck_z, deck_z + 1.6, 0.04, "doorBrown")
        for u in (-1.5, 1.5):
            shapes.fwindow(kit, face, u - 0.35, u + 0.35, deck_z + 0.7, deck_z + 1.5)
        cap = add(kit, "wall", "stone", STOREYS + 1, supports=both)
        kit = Kit()
        z = deck_z + ch
        kit.extrude_x([(-cd - 0.4, z), (cd + 0.4, z), (0, z + 1.7)], -cw - 0.4, cw + 0.4, turret_colour, colours={0: "trimWhite", 1: "trimWhite"})
        roof = add(kit, "roof", "stone", STOREYS + 2, supports=(cap,), collider="hull")
        kit = Kit()
        shapes.flag(kit, 0, 0, z + 1.4, 3.2, banner_colour, size=1.8, thick=0.1)
        add(kit, "detail", "wood", STOREYS + 3, supports=(roof,))
    else:
        kit = Kit()
        kit.box((-1.1, -1.1, deck_z), (1.1, 1.1, deck_z + 0.4), "stone", skip=("-z",))
        kit.box((-0.6, -0.6, deck_z + 0.4), (0.6, 0.6, deck_z + 0.9), "stone", skip=("-z",))
        kit.box((2.2, -0.8, deck_z), (3.8, 0.8, deck_z + 0.12), "wood", skip=("-z",), sides={s: "doorBrown" for s in ("-x", "+x", "-y", "+y")})  # the roof hatch
        shapes.flag(kit, 0, 0, deck_z + 0.9, 5.0, banner_colour, size=2.6, shape="banner", thick=0.12)
        add(kit, "detail", "wood", STOREYS + 1, supports=both)

    # --- steps up to the door ---
    y = -hy - FOOT
    kit = Kit()
    kit.box((-2.3, y - 1.5, 0), (2.3, y, 0.22), "stone", skip=("-z",))
    kit.box((-1.8, y - 0.8, 0.22), (1.8, y, 0.44), "trimWhite", skip=("-z",))
    add(kit, "detail", "stone", 0)

    # --- big banners down the front ---
    front = frames["front"]
    top = walls[STOREYS - 1]
    for index, u in enumerate(banner_us):
        colour = second if (banner_layout == "trio" and u == 0.0) or (banner_layout == "pair" and index == 1 and seed % 2) else banner_colour
        wide = 2.0 if u == 0.0 else 1.6
        z_top = height - 0.45
        kit = Kit()
        shapes.banner(kit, front, u, z_top, wide, 5.0 if u == 0.0 else 4.4, colour, v=0.22)
        shapes.fquad(kit, front, u - wide * 0.26, u + wide * 0.26, z_top - 2.0, z_top - 2.0 + wide * 0.52, 0.25, "trimWhite")
        shapes.fquad(kit, front, u - wide / 2, u + wide / 2, z_top - 0.75, z_top - 0.45, 0.25, "trimWhite")
        if u == 0.0:
            holders = (top[("front", 1)][0],)
        else:
            holders = (top[("front", 0 if u < 0 else 2)][0], top[("front", 1)][0])
        add(kit, "detail", "wood", STOREYS - 1, supports=holders)

    return building.finish(
        look=f"{width}x{depth} storey={storey_h} turrets-{turret_style}/{turret_colour}/{roof_feature}/top-{top_windows}/ground-{ground}/banners-{banner_layout}"
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(30, 28))


if __name__ == "__main__":
    previews()
