"""Helter-skelter generator.

A tall fairground helter-skelter: a tapering eight-sided tower in candy
stripes, a spiral slide winding down round the outside, a gallery at the top
with a little cabin, a striped roof and a flag. About 16 m tall. The seed
varies the height and taper, the stripes (upright, spiralling or hooped), the
slide's direction and number of turns, the roof and the finial.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/helter_skelter.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_fair as fair  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "helter_skelter"
HITS_TO_COLLAPSE = 3  # landmark
TRIANGLE_BUDGET = 1800

WALL = 0.4
SLIDE_WIDTH = 1.6
SLIDE_THICK = 0.3
LIP = 0.3
LIP_HEIGHT = 0.65
GALLERY = 0.35


def build(building_id, seed, scheme=None, collection=None):
    """Build one helter-skelter. Returns (empty, stats)."""
    rng = random.Random(seed)

    tiers, tier_h = rng.choice([(4, 2.6), (4, 2.8), (4, 3.0), (5, 2.2), (5, 2.4)])
    base_r = rng.choice([3.3, 3.6, 3.9])
    top_r = base_r * rng.choice([0.5, 0.58, 0.66])
    stripe = rng.choice(["upright", "spiral", "hoops", "spiral"])
    turns = rng.choice([2.0, 2.5, 3.0])
    direction = rng.choice([1, -1])  # +1 winds anticlockwise seen from above
    roof_form = rng.choice(["cone", "onion", "cone"])
    finial = rng.choice(["flag", "flag", "ball"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    body_h = tiers * tier_h
    slide_colour = pal["door"] if pal["door"] != "doorBrown" else "sunny"
    lip_colour = pal["roof"]

    def radius(z):
        return base_r + (top_r - base_r) * min(max(z / body_h, 0.0), 1.0)

    def wall_colour(i, t):
        if stripe == "upright":
            odd = i % 2
        elif stripe == "spiral":
            odd = (i + t * direction) % 2
        else:
            odd = t % 2
        return pal["trim"] if odd else pal["wall"]

    # --- the tower: one module per facet per tier ---
    walls = []
    for t in range(tiers):
        z0, z1 = t * tier_h, (t + 1) * tier_h
        r0, r1 = radius(z0), radius(z1)
        row = []
        for i in range(8):
            kit = Kit()
            fair.taper_wall(kit, i, r0, r1, WALL, z0, z1, wall_colour(i, t), "interiorCream")
            if t == 0 and i == 0:
                # The way in, at the front.
                fair.taper_quad(kit, i, r0, r1, z0, z1, 0.22, 0.78, 0.0, 0.8, "windowBlue")
                fair.taper_quad(kit, i, r0, r1, z0, z1, 0.14, 0.86, 0.8, 0.9, slide_colour, proud=0.07)
            elif t > 0 and (i + t) % 4 == 0:
                # A porthole window here and there.
                fair.taper_quad(kit, i, r0, r1, z0, z1, 0.32, 0.68, 0.35, 0.7, "windowBlue")
                fair.taper_quad(kit, i, r0, r1, z0, z1, 0.4, 0.5, 0.5, 0.64, "windowShine", proud=0.08)
            row.append(
                add(kit, "wall", "wood", t, supports=(walls[t - 1][i],) if t else (), collider="hull")
            )
        walls.append(row)

    # --- the gallery at the top, where the slide starts ---
    gallery_r = top_r + SLIDE_WIDTH
    gallery_top = body_h + GALLERY
    kit = Kit()
    shapes.frustum(kit, gallery_r - 0.25, gallery_r, body_h, gallery_top, pal["roof"])
    gallery = add(kit, "floor", "wood", tiers, supports=walls[-1], collider="hull")

    # --- the spiral slide: one sloping piece per facet, winding down to the ground ---
    count = int(turns * 8)
    # The last piece runs down one side, so the slide shoots out towards the front.
    end_deg = shapes.corner_deg(7) if direction == 1 else shapes.corner_deg(2)
    start_deg = end_deg - direction * 45.0 * count
    slide_top = gallery_top
    slide_end = 0.45
    drop = (slide_top - slide_end) / count
    first_facet = None
    for k in range(count):
        a0 = start_deg + direction * 45.0 * k
        a1 = a0 + direction * 45.0
        z0 = slide_top - k * drop
        z1 = z0 - drop
        facet = int(round((min(a0, a1) - shapes.corner_deg(0)) / 45.0)) % 8
        if first_facet is None:
            first_facet = facet
        tier = min(tiers - 1, max(0, int(((z0 + z1) / 2 - 0.4) // tier_h)))
        ri0, ri1 = radius(z0) - 0.12, radius(z1) - 0.12
        ro0, ro1 = radius(z0) + SLIDE_WIDTH, radius(z1) + SLIDE_WIDTH

        kit = Kit()
        fair.hexa(
            kit,
            [
                shapes.polar(ri0, a0, z0 - SLIDE_THICK),
                shapes.polar(ro0, a0, z0 - SLIDE_THICK),
                shapes.polar(ro1, a1, z1 - SLIDE_THICK),
                shapes.polar(ri1, a1, z1 - SLIDE_THICK),
            ],
            [shapes.polar(ri0, a0, z0), shapes.polar(ro0, a0, z0), shapes.polar(ro1, a1, z1), shapes.polar(ri1, a1, z1)],
            slide_colour,
        )
        fair.hexa(
            kit,
            [
                shapes.polar(ro0 - LIP, a0, z0),
                shapes.polar(ro0, a0, z0),
                shapes.polar(ro1, a1, z1),
                shapes.polar(ro1 - LIP, a1, z1),
            ],
            [
                shapes.polar(ro0 - LIP, a0, z0 + LIP_HEIGHT),
                shapes.polar(ro0, a0, z0 + LIP_HEIGHT),
                shapes.polar(ro1, a1, z1 + LIP_HEIGHT),
                shapes.polar(ro1 - LIP, a1, z1 + LIP_HEIGHT),
            ],
            lip_colour,
            skip=(0,),
        )
        add(kit, "detail", "tin", tier, supports=(walls[tier][facet],), collider="hull")

    # --- the run-out at the bottom, with a landing mat ---
    r_in, r_out = radius(slide_end) - 0.12, radius(slide_end) + SLIDE_WIDTH
    frame = shapes.Frame(shapes.polar((r_in + r_out) / 2, end_deg, 0), end_deg)
    half = (r_out - r_in) / 2
    kit = Kit()
    along = direction  # the frame's u runs anticlockwise
    u0, u1 = sorted((0.0, along * 2.6))
    m0, m1 = sorted((along * 2.6, along * 4.4))
    shapes.fbox(kit, frame, (u0, -half, 0), (u1, half, slide_end), slide_colour, skip=("-z",))
    shapes.fbox(kit, frame, (u0, half - LIP, slide_end), (u1, half, slide_end + LIP_HEIGHT), lip_colour, skip=("-z",))
    shapes.fbox(kit, frame, (m0, -half - 0.2, 0), (m1, half + 0.2, 0.22), pal["wall"], skip=("-z",))
    add(kit, "detail", "tin", 0, supports=(walls[0][6 if direction == 1 else 2],))

    # --- gallery railings, left open where the slide sets off ---
    for q in range(4):
        facets = [i for i in (2 * q, 2 * q + 1) if i != first_facet]
        if not facets:
            continue
        kit = Kit()
        for i in facets:
            shapes.wall_segment(kit, i, gallery_r, gallery_r - 0.3, gallery_top, gallery_top + 0.9, pal["trim"])
        add(kit, "detail", "wood", tiers, supports=(gallery,))

    # --- the cabin ---
    cabin_r = top_r * 0.82
    cabin_top = gallery_top + 2.1
    kit = Kit()
    shapes.frustum(
        kit, cabin_r, cabin_r, gallery_top, cabin_top, pal["wall"], stripes=[pal["trim"], pal["wall"]], bottom=False
    )
    for i in (0, 2, 4, 6):
        frame = shapes.facet_frame(i, cabin_r, gallery_top)
        w = shapes.side_length(cabin_r) * 0.3
        if i == first_facet or (first_facet % 2 and i == (first_facet + 1) % 8):
            shapes.fquad(kit, frame, -w, w, 0, 1.8, 0.04, "windowBlue")
        else:
            shapes.fwindow(kit, frame, -w, w, 0.9, 1.8)
    cabin = add(kit, "wall", "wood", tiers + 1, supports=(gallery,), collider="hull")

    # --- the roof ---
    eave = cabin_r + 0.8
    stripes = [pal["roof"], pal["trim"]]
    kit = Kit()
    if roof_form == "cone":
        roof_top = cabin_top + 2.2
        shapes.frustum(kit, eave, 0, cabin_top, roof_top, pal["roof"], stripes=stripes)
    else:
        mid = cabin_top + 1.0
        roof_top = cabin_top + 2.4
        shapes.frustum(kit, eave * 0.8, eave * 1.05, cabin_top, mid, pal["roof"], stripes=stripes, top=False)
        shapes.frustum(kit, eave * 1.05, 0, mid, roof_top, pal["roof"], stripes=stripes, bottom=False)
    roof = add(kit, "roof", "tin", tiers + 2, supports=(cabin,), collider="hull")

    # --- finial ---
    kit = Kit()
    if finial == "flag":
        shapes.flag(kit, 0, 0, roof_top - 0.4, 2.6, slide_colour, direction=direction, size=1.6, thick=0.15)
    else:
        kit.box((-0.15, -0.15, roof_top - 0.4), (0.15, 0.15, roof_top + 0.5), pal["trim"], skip=("-z",))
        shapes.ball(kit, 0, 0, roof_top + 0.95, 0.6, slide_colour)
    add(kit, "detail", "tin", tiers + 3, supports=(roof,), collider="hull")

    return building.finish(
        look=f"tiers={tiers}x{tier_h} r={base_r}->{top_r:.1f} {stripe}/turns-{turns}/dir{direction:+d}/{roof_form}/{finial}"
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(24, 30))


if __name__ == "__main__":
    previews()
