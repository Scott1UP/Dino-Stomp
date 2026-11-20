"""Sawmill generator.

An open-sided timber sawmill about 14 m by 8 m. A shed of stout posts under a
bright pitched tin roof, walled only along the back; a log deck out in the
open at one end with a fat log on it, lying against a big round saw blade;
a lean-to at the other end; and a stack of cut planks and a heap of sawdust
out the front.

The seed flips the whole mill left to right and varies the shed's length and
roof pitch, the timber colour, the blade's colour, how many logs wait on the
deck, the height of the plank stack and the lean-to's size.

How it comes down: the three front posts are role "pillar" and the two bays of
the back wall role "wall", all storey 0. The eave beams and gables rest on
them and the six roof sheets on those.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/sawmill.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import beam, flat, polygon  # noqa: E402
from lib.shapes_fair import mirror_x  # noqa: E402
from lib.shapes_forest import cone, log, roof_halves  # noqa: E402
from lib.shapes_props import prism  # noqa: E402

TYPE = "sawmill"
HITS_TO_COLLAPSE = 2
TRIANGLE_BUDGET = 1300

EAVE = 3.7
POST = 0.5
WALL = 0.3
FRONT, BACK = -3.0, 3.0  # the shed's post lines
LEFT = -7.0  # the far end of the log deck
SHED = -2.5  # where the shed starts


def build(building_id, seed, scheme=None, collection=None):
    """Build one sawmill. Returns (empty, stats)."""
    rng = random.Random(seed)

    flip = seed % 2 == 1  # cycled, so neighbouring seeds differ
    shed_end = rng.choice([4.2, 4.6, 5.0])
    pitch = rng.choice([0.55, 0.7, 0.85])
    dark = rng.choice([True, False])
    blade_pick = rng.choice(["sunny", "trimWhite", "tangerine"])
    spare_logs = rng.choice([0, 1, 2])
    planks = rng.choice([3, 4, 5])
    lean_out = rng.choice([2.0, 2.4])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    frame, boards = ("doorBrown", "wood") if dark else ("wood", "doorBrown")
    blade = blade_pick if blade_pick != pal["roof"] else "sunny"
    hub = "tomato" if blade != "tomato" and pal["roof"] != "tomato" else "cobalt"
    colours = {"wall": boards, "interior": "interiorCream", "trim": pal["trim"], "glass": "windowBlue", "shine": "windowShine", "door": pal["door"]}

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)

    def add(kit, *args, **kwargs):
        if flip:
            mirror_x(kit)
        return building.add(kit, *args, **kwargs)

    rise = pitch * (BACK - FRONT) / 2
    ridge = EAVE + rise
    mid = (SHED + shed_end) / 2
    lean_end = shed_end + lean_out

    # --- the three front posts, with knee braces ---
    posts = []
    for x in (SHED + POST / 2, mid, shed_end - POST / 2):
        kit = Kit()
        kit.box((x - POST / 2, FRONT - POST / 2, 0), (x + POST / 2, FRONT + POST / 2, EAVE), frame, skip=("-z", "+z"))
        kit.box((x - 0.4, FRONT - 0.4, 0), (x + 0.4, FRONT + 0.4, 0.3), "stone", skip=("-z",))
        for sign in (-1, 1):
            if SHED < x + sign * 1.1 < shed_end:
                beam(kit, (x, FRONT, EAVE - 1.2), (x + sign * 1.1, FRONT, EAVE - 0.05), 0.22, frame, caps=False)
        posts.append(add(kit, "pillar", "wood", 0))

    # --- the back wall, in two bays with a window each ---
    backs = []
    for a, b in ((SHED, mid), (mid, shed_end)):
        c = (a + b) / 2
        kit = Kit()
        kit.wall(a, b, 0, EAVE, BACK + WALL / 2, WALL, -1, [{"x0": c - 0.9, "x1": c + 0.9, "z0": 1.2, "z1": 2.6, "kind": "window"}], colours)
        kit.box((a, BACK - POST / 2, 0), (a + POST * 0.6, BACK + POST / 2, EAVE), frame, skip=("-z", "+z"))
        kit.box((b - POST * 0.6, BACK - POST / 2, 0), (b, BACK + POST / 2, EAVE), frame, skip=("-z", "+z"))
        backs.append(add(kit, "wall", "wood", 0))

    # --- eave beams along the front and back ---
    kit = Kit()
    kit.box((SHED - 0.3, FRONT - 0.22, EAVE), (shed_end + 0.3, FRONT + 0.22, EAVE + 0.4), frame)
    front_beam = add(kit, "band", "wood", 1, supports=posts)
    kit = Kit()
    kit.box((SHED - 0.3, BACK - 0.22, EAVE), (shed_end + 0.3, BACK + 0.22, EAVE + 0.4), frame)
    back_beam = add(kit, "band", "wood", 1, supports=backs)

    # --- the gable at each end: a tie beam, a king post and bright boards above ---
    top = EAVE + 0.4
    for x, holders in ((SHED, (posts[0], backs[0])), (shed_end, (posts[2], backs[1]))):
        xa, xb = (x, x + 0.25) if x == SHED else (x - 0.25, x)
        kit = Kit()
        kit.box((xa - 0.05, FRONT, top - 0.4), (xb + 0.05, BACK, top), frame, skip=("-y", "+y"))
        kit.extrude_x([(FRONT, top), (BACK, top), (0, top + rise)], xa, xb, pal["wall"])
        outward = (-1, 0, 0) if x == SHED else (1, 0, 0)
        flat(kit, (xa if x == SHED else xb, 0, top + rise * 0.4), outward, polygon(min(0.55, rise * 0.24)), pal["trim"], lift=0.03)
        add(kit, "wall", "wood", 1, supports=holders, collider="hull")

    # --- the tin roof: three sheets a side ---
    over = 0.7
    cuts = [SHED - 0.45, SHED + (shed_end - SHED) / 3, SHED + 2 * (shed_end - SHED) / 3, shed_end + 0.45]
    sheets = []
    for a, b in zip(cuts, cuts[1:]):
        for kit, holder in zip(roof_halves("x", a, b, (BACK - FRONT) / 2 + over, top - pitch * over, top + rise, 0.25, pal["roof"]), (front_beam, back_beam)):
            sheets.append(add(kit, "roof", "tin", 2, supports=(holder,), collider="hull"))
    kit = Kit()
    kit.box((cuts[0] - 0.1, -0.22, top + rise + 0.1), (cuts[-1] + 0.1, 0.22, top + rise + 0.42), pal["trim"])
    add(kit, "detail", "tin", 2, supports=sheets, collider="box")

    # --- the lean-to on the far end: a plank back wall, two posts and a sloping roof ---
    kit = Kit()
    kit.wall(shed_end, lean_end, 0, 2.6, BACK + WALL / 2, WALL, -1, [{"x0": shed_end + 0.5, "x1": lean_end - 0.5, "z0": 1.1, "z1": 2.1, "kind": "window"}], colours)
    kit.box((lean_end - 0.35, 0.2, 0), (lean_end, 0.55, 2.55), frame, skip=("-z", "+z"))
    lean_wall = add(kit, "wall", "wood", 0)
    kit = Kit()
    kit.slab([(shed_end + 0.05, -0.2, 3.3), (shed_end + 0.05, BACK + 0.5, 3.3), (lean_end + 0.5, BACK + 0.5, 2.5), (lean_end + 0.5, -0.2, 2.5)], 0.22, pal["roof"])
    add(kit, "roof", "tin", 1, supports=(lean_wall,), collider="hull")
    kit = Kit()  # a workbench under it
    kit.box((shed_end + 0.3, 1.2, 0), (lean_end - 0.5, 2.4, 0.9), boards, sides={"+z": "interiorCream"}, skip=("-z",))
    add(kit, "detail", "wood", 0)

    # --- the log deck: two rails on trestles, out in the open ---
    rail_z = 0.8
    kit = Kit()
    for y in (0.35, 1.45):
        kit.box((LEFT, y - 0.14, rail_z - 0.25), (SHED + 1.2, y + 0.14, rail_z), frame)
    for x in (LEFT + 0.5, (LEFT + SHED) / 2 + 0.6, SHED + 0.8):
        kit.box((x - 0.2, 0.0, 0), (x + 0.2, 1.8, rail_z - 0.25), boards, skip=("-z", "+z"))
    deck = add(kit, "detail", "wood", 0)

    kit = Kit()  # the log being sawn
    log(kit, "x", LEFT + 0.2, SHED - 0.3, (0.9, rail_z + 0.62), 0.62, frame if dark else "doorBrown", ring="wood")
    add(kit, "detail", "wood", 0, supports=(deck,), collider="hull")
    for n in range(spare_logs):  # logs waiting behind the deck
        kit = Kit()
        log(kit, "x", LEFT + 0.3 + n * 0.5, LEFT + 4.2 + n * 0.3, (2.6 + n * 1.14, 0.55), 0.55, "doorBrown" if n == 0 else "wood", ring="wood" if n == 0 else "doorBrown")
        add(kit, "detail", "wood", 0, collider="hull")

    # --- the big round saw blade, standing in its bench in front of the log ---
    bx = (LEFT + SHED) / 2 - 0.2
    kit = Kit()
    prism(kit, (bx, 1.6), 0.1, 0.24, 1.55, 1.55, 8, blade, axis="y")
    prism(kit, (bx, 1.6), 0.12, 0.22, 1.55, 1.55, 8, blade, axis="y", phase=0.0)  # a second octagon, turned: the teeth
    for y, facing in ((0.1, -1), (0.24, 1)):
        flat(kit, (bx, y, 1.6), (0, facing, 0), polygon(0.5, 8), hub, lift=0.02)
    kit.box((bx - 1.2, -0.75, 0), (bx + 1.2, 0.04, 0.85), "tyre", sides={"+z": "stone"}, skip=("-z",))
    add(kit, "detail", "tin", 0, collider="box")

    # --- out the front: a stack of cut planks and a heap of sawdust ---
    kit = Kit()
    for n in range(planks):
        inset = 0.12 if n % 2 else 0.0
        kit.box((0.6 + inset, -4.9 + inset, n * 0.34), (shed_end - 0.2 - inset, -3.85 - inset, (n + 1) * 0.34), "interiorCream" if n % 2 == 0 else "wood", skip=("-z",) if n else ("-z",))
    add(kit, "detail", "wood", 0)
    kit = Kit()
    cone(kit, (bx + 0.4, -2.2, 0), 1.2, (bx + 0.4, -2.2, 0.9), 6, "interiorCream")
    add(kit, "detail", "wood", 0, collider="hull")

    return building.finish(
        look=f"{'flipped' if flip else 'plain'}/shed{shed_end - SHED:g}/pitch{pitch}/{frame}/blade-{blade}/spare{spare_logs}/planks{planks}/lean{lean_out}"
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(20, 15))


if __name__ == "__main__":
    previews()
