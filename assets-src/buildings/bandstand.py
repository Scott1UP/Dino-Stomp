"""Bandstand generator.

An octagonal park bandstand: a raised wooden platform with steps at the open
front, eight posts, railings between the posts and a tin roof on top. The seed
varies its size, the roof (cone, dome or two-tier pagoda, plain or striped),
the railing style, the finial and whether the back is open too.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/bandstand.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "bandstand"
HITS_TO_COLLAPSE = 2  # medium building
TRIANGLE_BUDGET = 900

POST = 0.17  # half-thickness of a post
BEAM = 0.4


def build(building_id, seed, scheme=None, collection=None):
    """Build one bandstand. Returns (empty, stats)."""
    rng = random.Random(seed)

    radius = rng.choice([4.0, 4.5, 5.0])
    plat = rng.choice([0.6, 0.8, 1.0])
    post_h = rng.choice([3.0, 3.4, 3.8])
    roof_form = rng.choice(["dome", "cone", "pagoda"])
    rise = radius * rng.choice([0.6, 0.75, 0.9])
    roof_style = rng.choice(["solid", "stripes"])
    rail_style = rng.choice(["bars", "panel", "rails"])
    finial = rng.choice(["ball", "flag", "spike"])
    open_back = rng.random() < 0.3
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme
    pal = palette.SCHEMES[scheme]

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    post_r = radius - 0.3  # the posts stand just in from the platform's edge
    stripes = [pal["roof"], pal["trim"]] if roof_style == "stripes" else None

    # --- platform: four quarters, each under one whole side and half of its two neighbours ---
    quarters = []
    for q in range(4):
        m0 = shapes.polar(shapes.apothem(radius), shapes.facet_deg(2 * q - 1))
        m1 = shapes.polar(shapes.apothem(radius), shapes.facet_deg(2 * q + 1))
        c0 = shapes.polar(radius, shapes.corner_deg(2 * q))
        c1 = shapes.polar(radius, shapes.corner_deg(2 * q + 1))
        bottom = [(0, 0, 0), m0, c0, c1, m1]
        top = [(x, y, plat) for x, y, _ in bottom]
        faces = [bottom, top]
        for k in range(5):
            j = (k + 1) % 5
            faces.append([bottom[k], bottom[j], top[j], top[k]])
        kit = Kit()
        kit.convex(faces, pal["wall"], {1: "wood"})
        quarters.append(add(kit, "wall", "wood", 0, collider="hull"))

    def under_facet(i):
        """The platform quarters beneath side i."""
        i %= 8
        if i % 2 == 0:
            return (quarters[i // 2],)
        return (quarters[(i - 1) // 2], quarters[((i + 1) // 2) % 4])

    # --- steps up to the open front ---
    kit = Kit()
    frame = shapes.facet_frame(0, radius)
    shapes.fbox(kit, frame, (-1.3, 0, 0), (1.3, 0.55, plat * 0.66), "stone", skip=("-z", "-v"))
    shapes.fbox(kit, frame, (-1.3, 0.55, 0), (1.3, 1.1, plat * 0.33), "stone", skip=("-z", "-v"))
    add(kit, "detail", "wood", 0, supports=(quarters[0],))

    # --- posts: one at each corner, on a chunky foot ---
    posts = []
    for i in range(8):
        frame = shapes.corner_frame(i, post_r, plat)
        kit = Kit()
        shapes.fbox(kit, frame, (-POST, -POST, 0), (POST, POST, post_h), pal["trim"], skip=("-z", "+z"))
        shapes.fbox(kit, frame, (-0.28, -0.28, 0), (0.28, 0.28, 0.4), pal["roof"], skip=("-z",))
        posts.append(add(kit, "wall", "wood", 0, supports=(quarters[(i // 2) % 4],)))

    # --- railings between the posts, leaving the front open ---
    open_sides = {0, 4} if open_back else {0}
    span = shapes.side_length(post_r) / 2 - POST
    for i in range(8):
        if i in open_sides:
            continue
        frame = shapes.facet_frame(i, post_r, plat)
        kit = Kit()
        shapes.fbox(kit, frame, (-span, -0.09, 0.95), (span, 0.09, 1.1), pal["trim"], skip=("-u", "+u"))
        if rail_style == "bars":
            for u in (-span * 0.5, 0.0, span * 0.5):
                shapes.fbox(kit, frame, (u - 0.07, -0.05, 0), (u + 0.07, 0.05, 0.95), pal["trim"], skip=("-z", "+z"))
        elif rail_style == "panel":
            shapes.fbox(kit, frame, (-span, -0.05, 0.15), (span, 0.05, 0.95), pal["wall"], skip=("-u", "+u"))
        else:
            shapes.fbox(kit, frame, (-span, -0.06, 0.45), (span, 0.06, 0.58), pal["trim"], skip=("-u", "+u"))
            shapes.fbox(kit, frame, (-0.08, -0.05, 0), (0.08, 0.05, 0.95), pal["trim"], skip=("-z", "+z"))
        add(kit, "detail", "wood", 0, supports=under_facet(i))

    # --- roof: a ring beam on the posts and a roof in four quarters ---
    beam_z = plat + post_h
    eave_z = beam_z + BEAM
    eave_r = radius + 0.6
    if roof_form == "cone":
        low_r1, low_z1 = eave_r * 0.4, eave_z + rise * 0.6
    elif roof_form == "dome":
        low_r1, low_z1 = eave_r * 0.8, eave_z + rise * 0.5
    else:  # pagoda: a shallow skirt, then a lantern and a little upper roof
        low_r1, low_z1 = eave_r * 0.5, eave_z + rise * 0.35

    roof_quarters = []
    for q in range(4):
        kit = Kit()
        for i in (2 * q, 2 * q + 1):
            shapes.wall_segment(kit, i, radius - 0.05, radius - 0.5, beam_z, eave_z, pal["trim"])
        shapes.wedge(kit, 2 * q, 2, eave_r, low_r1, eave_z, low_z1, pal["roof"], stripes=stripes, under="interiorCream")
        roof_quarters.append(
            add(
                kit,
                "roof",
                "tin",
                1,
                supports=(posts[2 * q], posts[2 * q + 1], posts[(2 * q + 2) % 8]),
                collider="hull",
            )
        )

    top_z = low_z1
    crown = roof_quarters
    crown_colour = pal["roof"] if stripes else pal["door"]  # a plain roof gets a contrasting crown
    if roof_form == "cone":
        kit = Kit()
        top_z = eave_z + rise
        shapes.frustum(kit, low_r1, 0, low_z1, top_z, crown_colour, stripes=stripes)
        crown = (add(kit, "roof", "tin", 2, supports=roof_quarters, collider="hull"),)
    elif roof_form == "dome":
        kit = Kit()
        mid_z = eave_z + rise * 0.85
        top_z = eave_z + rise
        shapes.frustum(kit, eave_r * 0.8, eave_r * 0.45, low_z1, mid_z, pal["roof"], stripes=stripes, top=False)
        shapes.frustum(kit, eave_r * 0.45, 0, mid_z, top_z, crown_colour, stripes=stripes, bottom=False)
        crown = (add(kit, "roof", "tin", 2, supports=roof_quarters, collider="hull"),)
    elif roof_form == "pagoda":
        kit = Kit()
        drum_top = low_z1 + 0.8
        top_z = drum_top + rise * 0.55
        shapes.frustum(kit, eave_r * 0.4, eave_r * 0.4, low_z1, drum_top, pal["trim"], top=False)
        shapes.frustum(kit, eave_r * 0.62, 0, drum_top, top_z, crown_colour, stripes=stripes)
        crown = (add(kit, "roof", "tin", 2, supports=roof_quarters, collider="hull"),)

    # --- finial ---
    kit = Kit()
    if finial == "ball":
        kit.box((-0.1, -0.1, top_z - 0.3), (0.1, 0.1, top_z + 0.45), pal["trim"], skip=("-z",))
        shapes.ball(kit, 0, 0, top_z + 0.8, 0.45, "sunny" if pal["door"] != "sunny" else "tomato")
    elif finial == "flag":
        shapes.flag(kit, 0, 0, top_z - 0.3, 2.6, pal["door"], size=1.5)
    else:
        shapes.frustum(kit, 0.3, 0, top_z - 0.25, top_z + 1.5, pal["trim"], sides=4, bottom=False)
    add(kit, "detail", "tin", 3, supports=crown, collider="hull")

    return building.finish(
        look=f"r={radius} plat={plat} posts={post_h} {roof_form}/{roof_style}/rise-{rise:.1f}/{rail_style}/{finial}"
        + ("/open-back" if open_back else "")
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(20, 22))


if __name__ == "__main__":
    previews()
