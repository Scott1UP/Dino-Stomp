"""Giant tower generator: the finale of Castle Hill.

A giant 8-sided stone tower, about 7 m across and five storeys of wall,
standing on THREE chunky pillars 4 m tall. Only the pillars can be hit; when
they are gone the tower tips over whole. Everything rests, in the end, on the
pillars: a base slab sits on all three, each storey's ring of four wall pieces
sits on the ring below (turned one side round, like brickwork), and the top
deck, battlements, roof and big flag sit on the top ring.

The seed varies the storey height, whether the upper storeys step in or the
top storey flares out, the top (battlements, a bright cone, or both), corner
turrets, the pillars (round or square), windows and slits, and the banner and
flag colours.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/giant_tower.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "giant_tower"
HITS_TO_COLLAPSE = 3  # tall landmark
TRIANGLE_BUDGET = 1800

RADIUS = 5.2  # corner radius: about 10 m across
WALL = 0.6
PILLAR_H = 4.6
PILLAR_R = 0.95  # 1.8 m thick, near enough
SLAB = 0.7
STOREYS = 6  # wall storeys above the base
BRIGHTS = ["tomato", "sunny", "cobalt"]
ROOFS = ["tomato", "cobalt", "tangerine", "bubblegum"]


def build(building_id, seed, scheme=None, collection=None):
    """Build the giant tower. Returns (empty, stats)."""
    rng = random.Random(seed)

    storey_h = rng.choice([3.3, 3.5, 3.7])
    profile = rng.choice(["straight", "stepped", "flared", "flared"])
    top_style = rng.choice(["battlements", "cone", "both", "both"])
    cone_rise = rng.choice([4.5, 5.5, 6.5])
    cone_colour = rng.choice(ROOFS)
    turrets = rng.choice([0, 0, 2, 4])
    pillar_style = rng.choice(["round", "square"])
    slit_style = rng.choice(["cross", "plain"])
    window_turn = rng.choice([0, 1])
    banner_colour = rng.choice(BRIGHTS)
    flag_colour = rng.choice(BRIGHTS)
    flag_shape = rng.choice(["pennant", "banner"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection, kind="giantTower")
    add = building.add

    def storey_radius(s):
        """s counts wall storeys from 0, the one on the base slab."""
        if profile == "stepped" and s >= 3:
            return RADIUS - 0.55
        if profile == "flared" and s == STOREYS - 1:
            return RADIUS + 0.5
        return RADIUS

    # --- the base: a ring of eight great sloping stone blocks. These are what he has to
    # smash (they keep the role "pillar"): when the last one goes, the whole tower tips over.
    pillars = []
    for i in range(8):
        kit = Kit()
        shapes.wall_segment(kit, i, RADIUS + 1.1, 1.4, 0, PILLAR_H * 0.45, "stone", "stone")
        shapes.wall_segment(kit, i, RADIUS + 0.7, 1.4, PILLAR_H * 0.45, PILLAR_H - 0.5, "stone", "stone")
        shapes.wall_segment(kit, i, RADIUS + 0.9, 1.4, PILLAR_H - 0.5, PILLAR_H, "trimWhite", "stone")
        pillars.append(add(kit, "pillar", "stone", 0, collider="hull"))

    # --- base slab, resting on the ring of base blocks ---
    base_z = PILLAR_H + SLAB
    kit = Kit()
    shapes.frustum(kit, RADIUS + 0.1, RADIUS + 0.35, PILLAR_H, base_z - 0.25, "stone", top=False)
    shapes.frustum(kit, RADIUS + 0.35, RADIUS + 0.35, base_z - 0.25, base_z, "trimWhite", bottom=False)
    slab = add(kit, "floor", "stone", 1, supports=pillars, collider="hull")

    # --- wall rings: four pieces a storey, turned one side round on each storey ---
    below = {}
    rings = []
    for s in range(STOREYS):
        z0 = base_z + s * storey_h
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
                    # The great door, high above the ground, with a white surround.
                    shapes.fquad(kit, frame, -0.75, 0.75, z0, z0 + 2.3, 0.05, "doorBrown")
                    shapes.fbox(kit, frame, (-0.95, 0, z0 + 2.3), (0.95, 0.16, z0 + 2.55), "trimWhite", skip=("-v",))
                elif (i + s + window_turn) % 2 == 0 and not (s in (1, 2) and i in (7, 1)):  # banners hang there
                    if s % 2 == 1:
                        shapes.fwindow(kit, frame, -0.55, 0.55, z0 + 0.8, z0 + 2.2)
                        shapes.fbox(kit, frame, (-0.7, 0, z0 + 0.62), (0.7, 0.16, z0 + 0.8), "trimWhite", skip=("-v",))
                    else:
                        shapes.slit(kit, frame, z0 + 0.7, z0 + 2.3, width=0.34, cross=slit_style == "cross")
            supports = sorted({below[i] for i in facets}) if below else (slab,)
            module = add(kit, "wall", "stone", s + 1, supports=supports, collider="hull")
            for i in facets:
                here[i] = module
        below = here
        rings.append(here)

    def ring_ids(s):
        return sorted(set(rings[s].values()))

    # --- white bands (floor slabs that poke out) above the second and fourth storeys ---
    for s in (1, 3):
        z = base_z + (s + 1) * storey_h
        band_r = max(storey_radius(s), storey_radius(s + 1)) + 0.18
        kit = Kit()
        shapes.frustum(kit, band_r, band_r, z - 0.3, z, "trimWhite")
        add(kit, "band", "stone", s + 2, supports=ring_ids(s), collider="hull")

    # --- long banners down the front ---
    for i in (7, 1):
        s = 2
        frame = shapes.facet_frame(i, storey_radius(s))
        kit = Kit()
        z_top = base_z + (s + 1) * storey_h - 0.5
        shapes.banner(kit, frame, 0, z_top, 1.5, min(4.6, storey_h * 2 - 1.2), banner_colour)
        shapes.fquad(kit, frame, -0.4, 0.4, z_top - 1.5, z_top - 0.7, 0.09, "trimWhite")
        add(kit, "detail", "wood", s + 1, supports=(rings[s][i],))

    # --- top deck ---
    top_z = base_z + STOREYS * storey_h
    top_r = storey_radius(STOREYS - 1)
    deck_r = top_r + 0.4
    kit = Kit()
    shapes.frustum(kit, top_r, deck_r, top_z - 0.5, top_z, "stone", top=False)
    shapes.frustum(kit, deck_r, deck_r, top_z, top_z + 0.35, "trimWhite")
    deck = add(kit, "floor", "stone", STOREYS + 1, supports=ring_ids(STOREYS - 1), collider="hull")
    deck_z = top_z + 0.35

    # --- battlements ---
    if top_style in ("battlements", "both"):
        for q in range(4):
            kit = Kit()
            shapes.crenels(kit, (2 * q, 2 * q + 1), deck_r, deck_z, "stone", thickness=0.55, low=0.55, high=1.4)
            add(kit, "detail", "stone", STOREYS + 1, supports=(deck,), collider="hull")

    # --- cone roof ---
    crown = [deck]
    flag_z = deck_z
    if top_style in ("cone", "both"):
        kit = Kit()
        if top_style == "both":
            cone_r = deck_r - 0.9
            base = deck_z + 1.6
            rise = cone_rise * 0.85
            shapes.frustum(kit, cone_r - 0.4, cone_r - 0.4, deck_z, base, "stone", bottom=False, top=False)
        else:
            cone_r = deck_r + 0.5
            base = deck_z
            rise = cone_rise
        shapes.frustum(kit, cone_r, cone_r * 0.62, base, base + rise * 0.22, cone_colour, top=False)
        shapes.frustum(kit, cone_r * 0.62, 0, base + rise * 0.22, base + rise, cone_colour, bottom=False)
        crown = [add(kit, "roof", "stone", STOREYS + 2, supports=(deck,), collider="hull")]
        flag_z = base + rise - 0.5

    # --- the big flag ---
    kit = Kit()
    shapes.flag(kit, 0, 0, flag_z, 4.2, flag_colour, size=2.4, shape=flag_shape, thick=0.11)
    add(kit, "detail", "wood", STOREYS + 3, supports=crown)

    # --- little corner turrets hanging off the top storey ---
    corners = {0: (), 2: (0, 1), 4: (0, 2, 4, 6)}[turrets]
    for i in corners:
        tx, ty, _ = shapes.polar(top_r + 0.15, shapes.corner_deg(i))
        z0 = top_z - storey_h * 0.75
        z1 = deck_z + 1.3
        kit = Kit()
        shapes.frustum(kit, 0.0, 0.95, z0 - 1.3, z0, "stone", sides=6, cx=tx, cy=ty, top=False)
        shapes.frustum(kit, 0.95, 0.95, z0, z1, "stone", sides=6, cx=tx, cy=ty, bottom=False, top=False)
        shapes.frustum(kit, 1.3, 0, z1, z1 + 2.4, cone_colour, sides=6, cx=tx, cy=ty)
        holders = sorted({rings[STOREYS - 1][i % 8], rings[STOREYS - 1][(i - 1) % 8]})
        add(kit, "detail", "stone", STOREYS, supports=holders, collider="hull")

    return building.finish(
        look=f"storey={storey_h} {profile}/{top_style}/{cone_colour}/turrets-{turrets}/pillars-{pillar_style}/slits-{slit_style}"
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(15, 0), columns=6)


if __name__ == "__main__":
    previews()
