"""School wing generator: a long classroom wing of the wizard school.

A long grey stone wing, about 22 m by 9 m and three storeys tall, under a
steep dark slate roof with pointed dormer windows, chimney stacks along the
ridge and a round turret with a tall spire at one front corner. Rows of small
pointed windows glow warm on every storey, front and back; the door is in
the middle of the front.

Each long wall is five pieces a storey and each end wall one, every piece on
the piece below. A floor slab in two halves sits on each storey. The roof is
one slab per wall piece on each side, the dormers and chimneys sit on the
roof slabs, and the turret is one drum a storey.

The seed varies the length, the storey height, the roof pitch and slate,
which corner has the turret (and sometimes a second, smaller one at the back),
a cross gable over the door, how many dormers, the chimneys, and the window
width.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/school_wing.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib import shapes_wizard as wiz  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_parkcastle import Frame, fbox  # noqa: E402

TYPE = "school_wing"
HITS_TO_COLLAPSE = 3  # big building
TRIANGLE_BUDGET = 1800

WALL = 0.5
STOREYS = 3
PIECES = 5
OVERHANG = 0.35
VERGE = 0.35
ROOF_THICKNESS = 0.3


def build(building_id, seed, scheme=None, collection=None):
    """Build one school wing. Returns (empty, stats)."""
    rng = random.Random(seed)

    length = rng.choice([21.0, 22.0, 23.0])
    depth = rng.choice([8.5, 9.0])
    storey_h = rng.choice([3.2, 3.4])
    pitch = rng.choice([52, 56, 60])
    slate = rng.choice(wiz.SLATES)
    turret_side = (-1, 1)[seed % 2]  # alternated, so neighbouring seeds differ
    back_turret = rng.random() < 0.4
    cross_gable = rng.random() < 0.5
    dormer_pieces = rng.choice([(0, 2, 4), (1, 3), (0, 1, 3, 4), (1, 2, 3)])
    chimneys = rng.choice([(1, 3), (0, 2, 4), (2,), (1, 4)])
    win_w = rng.choice([0.6, 0.7])
    turret_rise = rng.choice([7.0, 8.0, 9.0])
    gold = rng.choice(wiz.GOLDS)
    spire_slate = "windowBlue" if slate == "tyre" else "tyre"  # stands out against the roof behind it
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    hx, hy = length / 2, depth / 2
    wall_h = STOREYS * storey_h
    rise = hy * math.tan(math.radians(pitch))
    ridge = wall_h + rise
    slope = rise / hy
    eave_z = wall_h - slope * OVERHANG
    piece = length / PIECES
    if cross_gable:
        dormer_pieces = tuple(k for k in dormer_pieces if k != PIECES // 2)

    def piece_u(name, k):
        """The u range of piece k on the front or back (u runs left to right as seen from outside)."""
        x0, x1 = -hx + k * piece, -hx + (k + 1) * piece
        return (x0, x1) if name == "front" else (-x1, -x0)

    frames = {
        "front": Frame((0, -hy, 0), -90),
        "back": Frame((0, hy, 0), 90),
        "left": Frame((-hx, 0, 0), 180),
        "right": Frame((hx, 0, 0), 0),
    }

    # --- walls: five pieces on each long side and one on each end, a storey ---
    walls = []  # per storey: {(name, k): id}
    for s in range(STOREYS):
        z0, z1 = s * storey_h, (s + 1) * storey_h
        here = {}
        for name in ("front", "back"):
            frame = frames[name]
            for k in range(PIECES):
                ua, ub = piece_u(name, k)
                kit = Kit()
                fbox(kit, frame, (ua, -WALL, z0), (ub, 0, z1), "stone", skip=("-z",) if s == 0 else (), sides={"-v": "interiorCream"})
                um = (ua + ub) / 2
                if s == 0 and name == "front" and k == PIECES // 2:
                    wiz.pointed_door(kit, frame, um, 1.6, 2.7, "doorBrown")
                    kit.box((um - 1.5, -hy - 0.9, 0), (um + 1.5, -hy, 0.2), "stone", skip=("-z",))
                else:
                    for du in (-piece / 4, piece / 4):
                        glass, shine = wiz.pane(rng, 0.15)
                        wiz.lancet(kit, frame, um + du, z0 + 0.8, win_w, storey_h - 1.5, glass=glass, shine=shine, rim=0.12)
                supports = (walls[-1][(name, k)],) if walls else ()
                here[(name, k)] = add(kit, "wall", "stone", s, supports=supports)
        for name in ("left", "right"):
            frame = frames[name]
            kit = Kit()
            inner = hy - WALL
            fbox(kit, frame, (-inner, -WALL, z0), (inner, 0, z1), "stone", skip=("-z",) if s == 0 else (), sides={"-v": "interiorCream"})
            for du in (-1.6, 1.6):
                wiz.lancet(kit, frame, du, z0 + 0.8, win_w, storey_h - 1.5, glass=wiz.LIT, shine=None, rim=0.12)
            supports = (walls[-1][(name, 0)],) if walls else ()
            here[(name, 0)] = add(kit, "wall", "stone", s, supports=supports)
        walls.append(here)

        def half_of(key):
            name, k = key
            if name in ("left", "right"):
                return -1 if name == "left" else 1
            x0, x1 = -hx + k * piece, -hx + (k + 1) * piece
            mid = (x0 + x1) / 2
            return 0 if abs(mid) < 0.1 else (-1 if mid < 0 else 1)

        # A floor slab in two halves on top of the storey, poking out as a white band.
        if s < STOREYS - 1:
            for side in (-1, 1):
                xa, xb = sorted((0.0, side * (hx + 0.12)))
                kit = Kit()
                wiz.band_box(kit, xa, -hy - 0.12, xb, hy + 0.12, z1 - 0.22, z1)
                add(kit, "floor", "wood", s + 1, supports=[m for key, m in here.items() if half_of(key) in (side, 0)])

    top = walls[-1]

    # --- the roof: a slab over each wall piece, front and back ---
    roofs = {}
    for name, sign in (("front", -1), ("back", 1)):
        eave_y = sign * (hy + OVERHANG)
        for k in range(PIECES):
            x0, x1 = -hx + k * piece, -hx + (k + 1) * piece
            if k == 0:
                x0 -= VERGE
            if k == PIECES - 1:
                x1 += VERGE
            kit = Kit()
            kit.slab([(x0, eave_y, eave_z), (x1, eave_y, eave_z), (x1, 0, ridge), (x0, 0, ridge)], ROOF_THICKNESS, slate)
            roofs[(name, k)] = add(kit, "roof", "tile", STOREYS, supports=(top[(name, k)],), collider="hull")

    # --- the gable ends ---
    for name, sign in (("left", -1), ("right", 1)):
        x0, x1 = sorted((sign * hx, sign * (hx - WALL)))
        kit = Kit()
        kit.extrude_x([(-hy, wall_h), (hy, wall_h), (0, ridge)], x0, x1, "stone")
        wiz.lancet(kit, frames[name], 0, wall_h + 0.5, 0.8, rise * 0.4, glass=wiz.LIT, shine=None, rim=0.12)
        add(kit, "wall", "stone", STOREYS, supports=(top[(name, 0)],), collider="hull")

    # --- a cross gable over the door ---
    if cross_gable:
        k = PIECES // 2
        x0, x1 = -hx + k * piece, -hx + (k + 1) * piece
        xm = (x0 + x1) / 2
        w = piece / 2 - 0.3
        g_rise = (w + 0.35) * 1.5
        kit = Kit()
        y0, y1 = -hy - 0.05, -hy + 2.6
        section = [(xm - w - 0.35, wall_h - 0.1), (xm + w + 0.35, wall_h - 0.1), (xm, wall_h + g_rise)]
        kit.extrude_y(section, y0, y1, "stone", colours={3: slate, 4: slate})
        frame = Frame((0, y0, 0), -90)
        wiz.lancet(kit, frame, xm, wall_h + 0.3, 1.0, g_rise * 0.55, glass=wiz.LIT, shine=None, rim=0.14)
        wiz.finial(kit, xm, y0 + 0.2, wall_h + g_rise - 0.2, size=0.8, colour=gold)
        add(kit, "roof", "tile", STOREYS, supports=(top[("front", k)], roofs[("front", k)]), collider="hull")

    # --- pointed dormers on the roof ---
    for name, sign in (("front", -1), ("back", 1)):
        for k in dormer_pieces:
            x0, x1 = -hx + k * piece, -hx + (k + 1) * piece
            xm = (x0 + x1) / 2
            w = 0.85
            y_face = sign * (hy - 0.7)
            z_base = wall_h + slope * 0.7 - 0.1
            z_eave = z_base + 1.6
            z_apex = z_eave + 1.5
            ya, yb = sorted((y_face, y_face - sign * 2.6))
            kit = Kit()
            section = [(xm - w, z_base), (xm + w, z_base), (xm + w, z_eave), (xm, z_apex), (xm - w, z_eave)]
            kit.extrude_y(section, ya, yb, "stone", colours={4: slate, 5: slate})
            frame = Frame((0, y_face, 0), -90 if sign < 0 else 90)
            wiz.lancet(kit, frame, xm if sign < 0 else -xm, z_base + 0.3, 0.7, 1.4, glass=wiz.LIT, shine=None, rim=0.1)
            add(kit, "detail", "stone", STOREYS + 1, supports=(roofs[(name, k)],), collider="hull")

    # --- chimney stacks along the ridge ---
    for k in chimneys:
        x0, x1 = -hx + k * piece, -hx + (k + 1) * piece
        xm = (x0 + x1) / 2 + (0.6 if k % 2 else -0.6)
        y = 1.0
        z_low = wall_h + slope * (hy - y - 0.5) - 0.3
        kit = Kit()
        kit.box((xm - 0.55, y - 0.45, z_low), (xm + 0.55, y + 0.45, ridge + 1.5), "stone", skip=("-z",))
        kit.box((xm - 0.7, y - 0.6, ridge + 1.5), (xm + 0.7, y + 0.6, ridge + 1.8), "trimWhite")
        for dx in (-0.25, 0.25):
            kit.box((xm + dx - 0.14, y - 0.14, ridge + 1.8), (xm + dx + 0.14, y + 0.14, ridge + 2.2), "tyre", skip=("-z",))
        add(kit, "detail", "stone", STOREYS + 1, supports=(roofs[("back", k)],))

    # --- the corner turret(s) ---
    def turret(sx, sy, r, levels, rise, lift):
        cx, cy = sx * (hx + r * 0.35), sy * (hy + r * 0.35)
        out_deg = math.degrees(math.atan2(sy, sx))
        below = None
        for s in range(levels):
            z0 = s * storey_h
            z1 = z0 + storey_h if s < levels - 1 else wall_h + lift
            kit = Kit()
            wiz.drum(kit, r, r, z0, z1, "stone", cx=cx, cy=cy, top="interiorCream", bottom="interiorCream")
            for turn in (-1, 1):
                facet = round((out_deg + 90 + turn * 45) / 45) % 8
                frame = shapes.facet_frame(facet, r, cx=cx, cy=cy)
                zt = z0 + 0.8 if s < levels - 1 else wall_h + lift - 2.0
                wiz.lancet(kit, frame, 0, zt, 0.45, 1.3, glass=wiz.LIT, shine=None, rim=0.09)
            if s == levels - 1:
                wiz.band_ring(kit, r + 0.2, z1 - 0.25, z1, cx=cx, cy=cy)
            below = add(kit, "wall", "stone", s, supports=(below,) if below else (), collider="hull")
        z = wall_h + lift
        kit = Kit()
        wiz.kicked_spire(kit, r + 0.3, z, z + rise, spire_slate, cx=cx, cy=cy, kick=0.06, knee=0.85)
        wiz.finial(kit, cx, cy, z + rise - 0.25, size=0.8, colour=gold, stem=False)
        roof = add(kit, "roof", "tile", levels, supports=(below,), collider="hull")
        return roof, (cx, cy, z + rise)

    roof, (fx, fy, fz) = turret(turret_side, -1, 1.8, STOREYS, turret_rise, rise * 0.6)
    kit = Kit()
    shapes.flag(kit, fx, fy, fz + 0.4, 1.8, rng.choice(["tomato", "cobalt", "sunny"]), size=1.3, thick=0.06)
    add(kit, "detail", "wood", STOREYS + 1, supports=(roof,))
    if back_turret:
        turret(-turret_side, 1, 1.35, STOREYS, turret_rise - 1.5, rise * 0.45)

    return building.finish(
        look=f"{length}x{depth} storey{storey_h} pitch{pitch} {slate} turret{turret_side:+d}{'+back' if back_turret else ''} gable-{cross_gable} dormers{dormer_pieces} chimneys{chimneys}"
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(30, 26))


if __name__ == "__main__":
    previews()
