"""Gate towers generator: the grand entrance of the wizard school.

Two square grey stone towers, five storeys tall under dark slate spires with
gold finials and pennants, stand either side of an OPEN gateway 9 m wide,
about 20 m across in all. High above the gap (nothing spans it below 9 m) a
low stone arch carries a covered gallery with warm windows under a dark
roof, and a lantern hangs from the crown of the arch. The great gate leaves
stand open, folded back against the towers.

Each tower is four walls a storey, each on the wall below, with a floor slab
between storeys. The arch is two halves, each resting on its own tower; the
gallery rests on both halves, and its roof on the gallery.

The seed varies the tower width and storey height, the spires (a plain
pyramid, an eight-sided needle, or a needle ringed by little spirelets), the
slate, the gallery (covered, or an open bridge with a parapet), the gate
leaves and the pennant colours.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/gate_towers.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_castle2 as castle  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib import shapes_wizard as wiz  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_parkcastle import Frame  # noqa: E402

TYPE = "gate_towers"
HITS_TO_COLLAPSE = 2  # medium structure
TRIANGLE_BUDGET = 1300

GAP = 9.0  # clear width of the gateway
CLEAR = 9.0  # nothing spans the gateway below this
WALL = 0.5
STOREYS = 5


def build(building_id, seed, scheme=None, collection=None):
    """Build one pair of gate towers. Returns (empty, stats)."""
    rng = random.Random(seed)

    tower_w = rng.choice([5.0, 5.4])
    storey_h = rng.choice([3.2, 3.4])
    spire_style = ("pyramid", "needle", "spirelets")[seed % 3]  # cycled, so neighbouring seeds differ
    spire_rise = rng.choice([7.5, 8.5, 9.5])
    slate = rng.choice(wiz.SLATES)
    gallery = rng.choice(["covered", "covered", "open"])
    leaves = rng.random() < 0.6
    gold = rng.choice(wiz.GOLDS)
    pennants = [rng.choice(["tomato", "cobalt", "sunny", "bubblegum"]) for _ in range(2)]
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    th = tower_w / 2
    inner = GAP / 2 + 0.25  # the floor bands and folded-back leaves stay outside the 9 m gap
    height = STOREYS * storey_h
    names = ("front", "back", "left", "right")
    arch_spring = CLEAR + 0.15
    arch_storey = int(arch_spring // storey_h)

    towers = []
    for sx in (-1, 1):
        cx = sx * (inner + th)
        frames = castle.rect_frames(cx, 0, th, th)
        gate_side = "left" if sx > 0 else "right"  # the face towards the gateway
        rows = []
        below = None
        for s in range(STOREYS):
            z0, z1 = s * storey_h, (s + 1) * storey_h
            here = {}
            for name in names:
                frame = frames[name]
                kit = Kit()
                castle.box_wall(kit, frame, name, th, th, z0, z1, WALL)
                if s == 0 and name == gate_side:
                    pass  # the gate leaf folds back here
                elif s == 0:
                    shapes.slit(kit, frame, z0 + 0.8, z0 + 2.4, width=0.32, cross=False)
                elif name == gate_side and s >= arch_storey:
                    pass  # the arch and gallery meet the tower here
                else:
                    glass, shine = wiz.pane(rng, 0.15)
                    wiz.lancet(kit, frame, 0, z0 + 0.7, 0.75, storey_h - 1.35, glass=glass, shine=shine, rim=0.13)
                here[name] = add(kit, "wall", "stone", s, supports=(below[name],) if below else ())
            rows.append(here)
            below = here
            if s < STOREYS - 1:
                kit = Kit()
                b = th + 0.14
                wiz.band_box(kit, cx - b, -b, cx + b, b, z1 - 0.22, z1)
                add(kit, "floor", "wood", s + 1, supports=list(here.values()))

        # --- the top: a corbelled deck and the spire ---
        eave = th + 0.35
        kit = Kit()
        wiz.corbel_square(kit, th, eave, height - 0.5, height, cx=cx)
        wiz.band_box(kit, cx - eave, -eave, cx + eave, eave, height, height + 0.3)
        deck = add(kit, "floor", "stone", STOREYS, supports=list(rows[-1].values()), collider="hull")
        z = height + 0.3
        tip = z + spire_rise
        kit = Kit()
        if spire_style == "pyramid":
            r = (eave + 0.1) * math.sqrt(2)
            wiz.kicked_spire(kit, r, z, tip, slate, 4, cx=cx)
        else:
            r = (eave + 0.1) / math.cos(math.pi / 8) if spire_style == "needle" else eave * 0.85
            wiz.kicked_spire(kit, r, z, tip, slate, 8, cx=cx)
        wiz.finial(kit, cx, 0, tip - 0.3, size=1.0, colour=gold)
        spire = add(kit, "roof", "tile", STOREYS + 1, supports=(deck,), collider="hull")
        kit = Kit()
        shapes.flag(kit, cx, 0, tip + 0.6, 1.8, pennants[0 if sx < 0 else 1], size=1.4, direction=sx, thick=0.07)
        add(kit, "detail", "wood", STOREYS + 2, supports=(spire,))
        if spire_style == "spirelets":
            kit = Kit()
            for px in (-1, 1):
                for py in (-1, 1):
                    x, y = cx + px * (eave - 0.45), py * (eave - 0.45)
                    kit.box((x - 0.35, y - 0.35, z), (x + 0.35, y + 0.35, z + 1.0), "stone", skip=("-z", "+z"))
                    wiz.cone_part(kit, 0.55, 0.0, z + 1.0, z + 4.4, slate, 4, cx=x, cy=y)
            add(kit, "roof", "tile", STOREYS + 1, supports=(deck,), collider="hull")

        # --- the gate leaf, folded back against the tower ---
        if leaves:
            kit = Kit()
            xf = sx * inner
            xa, xb = sorted((xf, xf - sx * 0.18))
            kit.box((xa, -th + 0.3, 0), (xb, th - 0.3, 6.2), "doorBrown", skip=("-z",))
            for zb in (1.2, 4.6):
                kit.box((xa - 0.04, -th + 0.4, zb), (xb + 0.04, th - 0.4, zb + 0.3), "tyre")
            add(kit, "detail", "wood", 0, supports=(rows[0][gate_side],))
        towers.append(rows)

    # --- the high arch over the gateway: two halves, each on its own tower ---
    z_crown = arch_spring + 1.3
    z_top = z_crown + 0.5
    halves = []
    for side, rows in ((-1, towers[0]), (1, towers[1])):
        kit = Kit()
        castle.arch_half(kit, side, inner, inner, -th + 0.6, th - 0.6, arch_spring, z_crown, z_top, "stone", trim="trimWhite", steps=3, ring=0.35)
        holder = rows[arch_storey]["right" if side < 0 else "left"]
        halves.append(add(kit, "wall", "stone", arch_storey, supports=(holder,), collider="hull"))

    # --- the gallery on top of the arch ---
    hy = th - 0.6
    g_top = z_top + 2.5
    kit = Kit()
    if gallery == "covered":
        for name, y in (("front", -hy), ("back", hy)):
            frame = Frame((0, y, 0), -90 if name == "front" else 90)
            castle.box_wall(kit, frame, name, inner, hy, z_top, g_top, 0.35)
            for u in (-2.6, 0.0, 2.6):
                wiz.lancet(kit, frame, u, z_top + 0.5, 0.75, 1.4, glass=wiz.LIT, shine=None, rim=0.12)
        gal = add(kit, "wall", "stone", arch_storey + 1, supports=halves)
        kit = Kit()
        reach = hy + 0.5
        kit.extrude_x([(-reach, g_top - 0.1), (reach, g_top - 0.1), (0, g_top + 1.9)], -inner, inner, slate)
        add(kit, "roof", "tile", arch_storey + 2, supports=(gal,), collider="hull")
    else:
        for y in (-hy, hy):
            ya, yb = sorted((y, y - math.copysign(0.3, y)))
            kit.box((-inner, ya, z_top), (inner, yb, z_top + 1.0), "stone", skip=("-z",))
            kit.box((-inner, ya - 0.06, z_top + 1.0), (inner, yb + 0.06, z_top + 1.25), slate, skip=("-z",))
        add(kit, "wall", "stone", arch_storey + 1, supports=halves)

    # --- a lantern hanging from the crown, its foot still above the clear height ---
    kit = Kit()
    wiz.lantern(kit, 0, 0, z_crown, 0.25, size=0.6)
    add(kit, "detail", "wood", arch_storey, supports=halves)

    width = 2 * (inner + tower_w)
    return building.finish(look=f"w{width:.1f} tower{tower_w} storey{storey_h} {spire_style}/{slate} rise{spire_rise} gallery-{gallery} leaves-{leaves}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(26, 20))


if __name__ == "__main__":
    previews()
