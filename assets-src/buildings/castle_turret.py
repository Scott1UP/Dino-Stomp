"""Castle turret generator.

A round (8-sided) stone turret, three storeys tall, with a door at the foot,
arrow slits, white bands at each floor and a top that the seed picks: a bright
cone roof, battlements, or battlements with a smaller cone inside them. The
seed also varies the girth, the storey height, whether the top storey flares
out, the slits and windows, and the flag.

Each storey's wall is four pieces of two sides each, staggered from the storey
below like brickwork.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/castle_turret.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "castle_turret"
HITS_TO_COLLAPSE = 2  # medium building
TRIANGLE_BUDGET = 900

WALL = 0.5
STOREYS = 3
BRIGHTS = ["tomato", "sunny", "cobalt"]
ROOFS = ["tomato", "cobalt", "tangerine", "bubblegum"]


def build(building_id, seed, scheme=None, collection=None):
    """Build one turret. Returns (empty, stats)."""
    rng = random.Random(seed)

    radius = rng.choice([2.3, 2.6, 2.9])
    storey_h = rng.choice([3.0, 3.2, 3.4])
    top_style = rng.choice(["cone", "battlements", "both", "cone"])
    flare = rng.choice([0.0, 0.0, 0.4])
    cone_rise = rng.choice([3.4, 4.2, 5.0])
    cone_colour = rng.choice(ROOFS)
    flag_colour = rng.choice(BRIGHTS)
    flag_shape = rng.choice(["pennant", "banner"])
    slit_style = rng.choice(["cross", "plain"])
    slit_turn = rng.choice([0, 1])
    top_windows = rng.random() < 0.5
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    def storey_radius(s):
        if s == 0:
            return radius + 0.2  # a stout foot
        if s == STOREYS - 1:
            return radius + flare
        return radius

    # --- walls: four pieces a storey, turned one side round on each storey ---
    below = {}  # facet -> module id, on the storey beneath
    walls = []
    for s in range(STOREYS):
        z0 = s * storey_h
        z1 = z0 + storey_h
        r = storey_radius(s)
        here = {}
        for q in range(4):
            facets = [(2 * q + s) % 8, (2 * q + s + 1) % 8]
            kit = Kit()
            for i in facets:
                shapes.wall_segment(kit, i, r, r - WALL, z0, z1, "stone", "interiorCream")
                frame = shapes.facet_frame(i, r)
                if s == 0 and i == 0:
                    shapes.fquad(kit, frame, -0.65, 0.65, 0, 2.4, 0.04, pal["door"])
                    shapes.fbox(kit, frame, (-0.8, 0, 2.4), (0.8, 0.14, 2.62), "trimWhite", skip=("-v",))
                elif s == STOREYS - 1 and top_windows and i % 2 == 0:
                    shapes.fwindow(kit, frame, -0.42, 0.42, z0 + 1.0, z0 + 2.2)
                elif (i + s + slit_turn) % 2 == 0 and not (s == 0 and i in (7, 1)):
                    shapes.slit(kit, frame, z0 + 0.9, z0 + 2.3, cross=slit_style == "cross")
            supports = sorted({below[i] for i in facets}) if below else ()
            module = add(kit, "wall", "stone", s, supports=supports, collider="hull")
            for i in facets:
                here[i] = module
        below = here
        walls.append(sorted(set(here.values())))

        # A floor slab on top of this storey: it pokes out as a white band.
        if s < STOREYS - 1:
            kit = Kit()
            band_r = max(r, storey_radius(s + 1)) + 0.15
            shapes.frustum(kit, band_r, band_r, z1 - 0.25, z1, "trimWhite")
            add(kit, "floor", "stone", s + 1, supports=walls[s], collider="hull")

    # --- top deck ---
    top_z = STOREYS * storey_h
    top_r = radius + flare
    deck_r = top_r + 0.35
    kit = Kit()
    shapes.frustum(kit, top_r, deck_r, top_z - 0.4, top_z, "stone", top=False)
    shapes.frustum(kit, deck_r, deck_r, top_z, top_z + 0.3, "trimWhite")
    deck = add(kit, "floor", "stone", STOREYS, supports=walls[-1], collider="hull")
    deck_z = top_z + 0.3

    # --- battlements, in four pieces ---
    crown = [deck]
    if top_style in ("battlements", "both"):
        for q in range(4):
            kit = Kit()
            shapes.crenels(kit, (2 * q, 2 * q + 1), deck_r, deck_z, "stone")
            add(kit, "detail", "stone", STOREYS, supports=(deck,), collider="hull")

    # --- cone roof ---
    flag_z = deck_z
    if top_style in ("cone", "both"):
        cone_r = deck_r + 0.45 if top_style == "cone" else deck_r - 0.75
        rise = cone_rise if top_style == "cone" else cone_rise * 0.8
        kit = Kit()
        if top_style == "both":
            shapes.frustum(kit, cone_r - 0.3, cone_r - 0.3, deck_z, deck_z + 1.2, "stone", bottom=False, top=False)
            base = deck_z + 1.2
        else:
            base = deck_z
        # A little kick at the eaves, then the steep cone: a witch's hat.
        shapes.frustum(kit, cone_r, cone_r * 0.62, base, base + rise * 0.22, cone_colour, top=False)
        shapes.frustum(kit, cone_r * 0.62, 0, base + rise * 0.22, base + rise, cone_colour, bottom=False)
        crown = [add(kit, "roof", "stone", STOREYS + 1, supports=(deck,), collider="hull")]
        flag_z = base + rise - 0.4

    # --- flag ---
    kit = Kit()
    shapes.flag(kit, 0, 0, flag_z, 2.8, flag_colour, size=1.5, shape=flag_shape)
    add(kit, "detail", "wood", STOREYS + 2, supports=crown)

    return building.finish(
        look=f"r={radius} storey={storey_h} {top_style}/flare-{flare}/rise-{cone_rise}/{cone_colour}/slits-{slit_style}"
        + ("/windows" if top_windows else "")
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(11, 0), columns=6)


if __name__ == "__main__":
    previews()
