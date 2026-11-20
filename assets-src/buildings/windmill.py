"""Windmill generator.

A tapering eight-sided tower about 12 m tall with a gallery round it, a cap
on top and four big sails on the front. Each sail is its own module: a spar
with a few chunky bars across it, and (on most) a cloth. The seed varies the
tower's height and taper, the cap (cone, dome or boat-shaped), the sails
(cloth, striped cloth or bare lattice) and the angle they have stopped at,
the gallery's height and the windows.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/windmill.py
"""

import math
import os
import random
import sys

from mathutils import Matrix

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_blocktown import beam, frustum, ring, round_window, shell  # noqa: E402
from lib.shapes_props import prism  # noqa: E402
from lib.shapes_town2 import arched_panel, place, ring_deck  # noqa: E402

TYPE = "windmill"
HITS_TO_COLLAPSE = 2  # medium building
TRIANGLE_BUDGET = 900

WALL = 0.4
SIDES = 8
PHASE = math.pi / SIDES
COS = math.cos(PHASE)  # flat-to-flat is this much less than corner-to-corner
QUARTERS = ((4, 5), (6, 7), (0, 1), (2, 3))  # facet 5 faces the front, 1 the back, 3 left, 7 right


def build(building_id, seed, scheme=None, collection=None):
    """Build one windmill. Returns (empty, stats)."""
    rng = random.Random(seed)

    # --- the windmill's character ---
    cap = ("cone", "boat", "dome")[seed % 3]  # cycled, so neighbouring seeds always differ
    height = rng.choice([10.5, 11.5, 12.5])
    base_r = rng.choice([3.5, 3.8, 4.1])
    taper = rng.choice([0.55, 0.62, 0.7])
    sail_style = rng.choice(["cloth", "cloth", "stripes", "lattice"])
    sail_turn = rng.choice([0, 22, 45, 68])
    gallery_level = rng.choice([0.31, 0.36, 0.41])  # how far up the tower the gallery (and the first floor) is
    windows = rng.choice(["round", "arched"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]
    accent = pal["door"] if pal["door"] != "doorBrown" else pal["roof"]

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    top_r = base_r * taper
    lean = (base_r - top_r) * COS / height  # how far each facet leans in per metre of height
    levels = [0.0, height * gallery_level, height * (gallery_level + 1) / 2, height]
    gallery_at = 1

    def radius(z):
        return base_r + (top_r - base_r) * z / height

    def on_facet(facet, z):
        """A point on the middle of a facet at height z, and the facet's outward normal."""
        angle = PHASE + (facet + 0.5) * 2 * math.pi / SIDES
        a = radius(z) * COS
        return (a * math.cos(angle), a * math.sin(angle), z), (math.cos(angle), math.sin(angle), lean)

    def opening(kit, facet, z, size=1.0):
        at, normal = on_facet(facet, z)
        if windows == "round":
            round_window(kit, at, normal, 0.75 * size, pal["trim"])
        else:
            at, normal = on_facet(facet, z - 0.8 * size)
            arched_panel(kit, at, normal, 1.0 * size, 1.7 * size, "round", pal["trim"], "windowBlue", "windowShine", depth=0.0)

    # --- the tower: three stages of four wall pieces, with a floor between ---
    window_plan = {0: (1,), 1: (5, 1, 3), 2: (7, 5)}
    below = None
    stage_ids = []
    for s in range(3):
        z0, z1 = levels[s], levels[s + 1]
        ids = []
        for q, facets in enumerate(QUARTERS):
            kit = Kit()
            shell(kit, 0, 0, [(z0, radius(z0)), (z1, radius(z1))], WALL, facets, pal["wall"], "interiorCream")
            for facet in facets:
                if s == 0 and facet == 5:
                    at, normal = on_facet(5, 0)
                    arched_panel(kit, at, normal, 1.5, 2.6, "round", pal["trim"], pal["door"], depth=0.12, is_door=True)
                elif facet in window_plan[s]:
                    opening(kit, facet, z0 + (z1 - z0) * (0.5 if s else 0.45))
            ids.append(add(kit, "wall", "plaster", s, supports=(below[q],) if below else (), collider="hull"))
        if s < 2:
            kit = Kit()
            kit.slab(ring(0, 0, z1 - 0.2, radius(z1) - WALL), 0.2, "interiorCream")
            add(kit, "floor", "wood", s + 1, supports=ids, collider="hull")
        stage_ids.append(ids)
        below = ids

    # --- the gallery: a deck with a chunky rail, in four pieces ---
    gz = levels[gallery_at]
    r_in = radius(gz) - 0.05
    r_out = radius(gz) + 1.5
    rail = ring(0, 0, gz + 1.0, r_out - 0.15)
    for q, facets in enumerate(QUARTERS):
        kit = Kit()
        ring_deck(kit, 0, 0, gz - 0.3, gz, r_in, r_out, facets, "wood", phase=PHASE, under="none")
        for facet in facets:
            a, b = rail[facet], rail[(facet + 1) % SIDES]
            beam(kit, a, b, 0.28, pal["trim"], caps=False)
            kit.box((a[0] - 0.2, a[1] - 0.2, gz), (a[0] + 0.2, a[1] + 0.2, gz + 1.2), pal["trim"], skip=("-z",))  # caps the rail's joint
        add(kit, "detail", "wood", gallery_at, supports=(stage_ids[gallery_at - 1][q],), collider="hull")

    # --- the cap, with the axle the sails turn on ---
    hub_z = height + 1.0
    hub_y = -(top_r * COS + 1.3)
    eave_r = top_r + 0.35
    kit = Kit()
    frustum(kit, 0, 0, height, eave_r, height + 0.3, eave_r, pal["trim"], bottom="interiorCream")
    if cap == "cone":
        cap_top = height + 3.2
        frustum(kit, 0, 0, height + 0.3, eave_r, cap_top, 0.0, pal["roof"])
    elif cap == "dome":
        cap_top = height + 2.5
        frustum(kit, 0, 0, height + 0.3, eave_r, height + 1.5, eave_r * 0.82, pal["roof"])
        frustum(kit, 0, 0, height + 1.5, eave_r * 0.82, cap_top, 0.0, pal["roof"])
    else:
        cap_top = height + 3.0
        w = eave_r * COS
        kit.extrude_y(
            [(-w, height + 0.3), (w, height + 0.3), (w * 0.95, height + 1.5), (0, cap_top), (-w * 0.95, height + 1.5)],
            -w - 0.25,
            w + 0.9,
            pal["roof"],
        )
    frustum(kit, 0, 0, cap_top - 0.05, 0.0, cap_top + 0.3, 0.28, "sunny", sides=4)
    frustum(kit, 0, 0, cap_top + 0.3, 0.28, cap_top + 0.8, 0.0, "sunny", sides=4)
    prism(kit, (0, hub_z), hub_y - 0.45, 0, 0.55, 0.55, 6, accent, axis="y", top=False)
    cap_id = add(kit, "roof", "tile", 3, supports=stage_ids[2], collider="hull")

    # --- four sails, each built pointing up and then turned round the axle ---
    reach = min(6.6, hub_z - (gz + 1.4))  # the sails swing clear of the gallery rail
    span = 1.9  # how wide the lattice stands off the spar
    start = 1.3
    for k in range(4):
        sail = Kit()
        beam(sail, (0, 0, 0.2), (0, 0, reach), 0.34, "wood", depth=0.3)
        beam(sail, (span, 0, start), (span, 0, reach), 0.3, "wood", depth=0.24)
        bars = 5 if sail_style == "lattice" else 3
        for b in range(bars):
            z = start + 0.15 + (reach - start - 0.3) * b / (bars - 1)
            beam(sail, (0.1, 0, z), (span, 0, z), 0.3, "wood", depth=0.24, caps=False)
        if sail_style != "lattice":
            panels = 3 if sail_style == "stripes" else 1
            step = (reach - start - 0.3) / panels
            for p in range(panels):
                za, zb = start + 0.15 + p * step, start + 0.15 + (p + 1) * step
                colour = accent if (sail_style == "stripes" and p % 2 == 0) else "trimWhite"
                quad = [(0.15, 0.06, za), (span - 0.1, 0.06, za), (span - 0.1, 0.06, zb), (0.15, 0.06, zb)]
                sail.poly(quad, (0, -1, 0), colour)
                sail.poly([(x, 0.1, z) for x, _, z in quad], (0, 1, 0), colour)
        kit = Kit()
        place(kit, sail, Matrix.Rotation(math.radians(sail_turn + 90 * k), 3, "Y"), (0, hub_y - 0.15, hub_z))
        add(kit, "detail", "wood", 3, supports=(cap_id,), collider="hull")

    return building.finish(
        look=(
            f"{cap}/h{height:g}/r{base_r:g}x{taper:g}/sails-{sail_style}@{sail_turn}/gallery{gz:.1f}/{windows}"
            f"/tip{hub_z + reach:.1f}"
        )
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(20, 26))


if __name__ == "__main__":
    previews()
