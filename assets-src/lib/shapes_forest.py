"""Shapes for the forest generators.

Logs lying along an axis, leaning cones for conifers, domes that break into
pieces (toadstool caps, dome tents), jittered rocks, log-course walls, pitched
roof slopes, railings, ladders and little picture signs.

Everything goes through `Kit.poly` or `Kit.convex`, so faces are flat coloured
and wound to point outwards.
"""

import math

from mathutils import Vector

from .meshkit import Kit
from .shapes_blocktown import beam, flat, polygon
from .shapes_props import ball, prism

COS8 = math.cos(math.pi / 8)


# --- logs -------------------------------------------------------------------


def log(kit, axis, lo, hi, centre, apothem, colour, end="interiorCream", ring=None, sides=8, caps=(True, True)):
    """A log lying along `axis` from lo to hi, with a flat side down.

    axis "x": `centre` is (y, z); axis "y": (x, z); axis "z": (x, y).
    `apothem` is the distance from the middle to a flat side, so logs of the
    same apothem stack and sit side by side exactly. `end` colours the cut
    ends and `ring` paints a growth ring on them.
    """
    radius = apothem / math.cos(math.pi / sides)
    prism(kit, centre, lo, hi, radius, radius, sides, colour, bottom=caps[0], top=caps[1], bottom_colour=end, top_colour=end, axis=axis)
    if ring:
        a, b = centre
        for w, facing, shown in ((lo, -1, caps[0]), (hi, 1, caps[1])):
            if not shown:
                continue
            if axis == "x":
                point, normal = (w, a, b), (facing, 0, 0)
            elif axis == "y":
                point, normal = (a, w, b), (0, facing, 0)
            else:
                point, normal = (a, b, w), (0, 0, facing)
            flat(kit, point, normal, polygon(apothem * 0.55, 6), ring, lift=0.012)


def cone(kit, base, radius, apex, sides, colour, under=None, phase=None):
    """A cone whose point may sit off to one side (a leaning conifer tier)."""
    bx, by, bz = base
    if phase is None:
        phase = math.pi / sides
    step = 2 * math.pi / sides
    points = [Vector((bx + radius * math.cos(phase + i * step), by + radius * math.sin(phase + i * step), bz)) for i in range(sides)]
    tip = Vector(apex)
    middle = Vector((bx, by, bz))
    for i in range(sides):
        j = (i + 1) % sides
        kit.poly([points[i], points[j], tip], (points[i] + points[j]) / 2 - middle + Vector((0, 0, 0.2)), colour)
    if under:
        kit.poly(points, (0, 0, -1), under)


def leaf_blob(kit, centre, radius, segments=8, rings=4, squash=0.85, top="leaf", under="hedge", dark_rings=1):
    """A big faceted ball of leaves, darker underneath."""
    ball(kit, centre, radius, segments, rings, top, lambda segment, ring: under if ring < dark_rings else top, squash=squash)


# --- domes ------------------------------------------------------------------


def dome(kit, cx, cy, profile, colour, facets=None, sides=8, under=None, cut=None, spots=(), spot_colour="trimWhite", stripes=None, top=True, spot_sides=6):
    """Part of a round, domed solid: a toadstool cap, a dome tent.

    `profile` is a list of (z, radius) from the rim up; it must bulge outwards
    (convex). `facets` picks the wedge to build (facet i runs from corner i to
    corner i + 1; facet 5 of 8 faces the front). `under` colours the underside,
    `cut` the flat faces where a wedge meets its neighbours. `stripes` is a list
    of colours cycled round the facets. `spots` is a list of (band, facet, size).
    """
    phase = math.pi / sides
    step = 2 * math.pi / sides
    whole = facets is None
    facets = list(range(sides)) if whole else list(facets)

    def point(k, r, z):
        a = phase + k * step
        return Vector((cx + r * math.cos(a), cy + r * math.sin(a), z))

    quads = {}
    for band, ((z0, r0), (z1, r1)) in enumerate(zip(profile, profile[1:])):
        for i in facets:
            mid = phase + (i + 0.5) * step
            hint = Vector((math.cos(mid), math.sin(mid), 0.6 if r0 > r1 else (-0.6 if r1 > r0 else 0.0)))
            if r1 < 1e-6:
                points = [point(i, r0, z0), point(i + 1, r0, z0), Vector((cx, cy, z1))]
            else:
                points = [point(i, r0, z0), point(i + 1, r0, z0), point(i + 1, r1, z1), point(i, r1, z1)]
            shade = stripes[i % len(stripes)] if stripes else colour
            kit.poly(points, hint, shade)
            quads[(band, i)] = (points, hint)

    for band, i, size in spots:
        points, hint = quads[(band, i)]
        middle = sum(points, Vector()) / len(points)
        normal = (points[1] - points[0]).cross(points[2] - points[0]).normalized()
        if normal.dot(hint) < 0:
            normal = -normal
        flat(kit, middle, normal, polygon(size, spot_sides), spot_colour, lift=0.04)

    corners = facets if whole else facets + [facets[-1] + 1]
    z_rim, r_rim = profile[0]
    z_top, r_top = profile[-1]
    if under and r_rim > 1e-6:
        outline = [point(k, r_rim, z_rim) for k in corners]
        if not whole and len(facets) * 2 != sides:
            outline.append(Vector((cx, cy, z_rim)))
        kit.poly(outline, (0, 0, -1), under)
    if top and r_top > 1e-6:
        outline = [point(k, r_top, z_top) for k in corners]
        if not whole and len(facets) * 2 != sides:
            outline.append(Vector((cx, cy, z_top)))
        kit.poly(outline, (0, 0, 1), stripes[0] if stripes else colour)
    if cut and not whole:
        for k, side in ((facets[0], -1), (facets[-1] + 1, 1)):
            a = phase + k * step
            tangent = (-math.sin(a) * side, math.cos(a) * side, 0)
            outline = [point(k, r, z) for z, r in profile if r > 1e-6]
            outline.append(Vector((cx, cy, z_top)))
            if abs(z_top - z_rim) > 1e-6:
                outline.append(Vector((cx, cy, z_rim)))
            kit.poly(outline, tangent, cut)


# --- rocks ------------------------------------------------------------------


def rock(kit, centre, size, rng, colour="stone", segments=6, jitter=0.16, cap=None):
    """A chunky faceted rock standing flat on the ground.

    `size` is (half width in X, half width in Y, height). `cap` recolours the
    top facets (moss).
    """
    cx, cy = centre
    sx, sy, sz = size
    turn = rng.uniform(0, math.tau)
    levels = ((0.0, 0.86), (0.42, 1.0), (0.8, 0.6))
    rings = []
    for z_part, r_part in levels:
        row = []
        for k in range(segments):
            a = turn + k * math.tau / segments
            wobble = 1 + rng.uniform(-jitter, jitter)
            lift = 1 + (rng.uniform(-jitter, jitter) if z_part else 0)
            row.append(Vector((cx + sx * r_part * wobble * math.cos(a), cy + sy * r_part * wobble * math.sin(a), sz * z_part * lift)))
        rings.append(row)
    top = Vector((cx + rng.uniform(-0.2, 0.2) * sx, cy + rng.uniform(-0.2, 0.2) * sy, sz))
    middle = Vector((cx, cy, sz * 0.4))

    def tri(a, b, c, shade):
        kit.poly([a, b, c], (a + b + c) / 3 - middle, shade)

    for band in range(len(rings) - 1):
        low, high = rings[band], rings[band + 1]
        for k in range(segments):
            j = (k + 1) % segments
            if (k + band) % 2:
                tri(low[k], low[j], high[j], colour)
                tri(low[k], high[j], high[k], colour)
            else:
                tri(low[k], low[j], high[k], colour)
                tri(low[j], high[j], high[k], colour)
    for k in range(segments):
        tri(rings[-1][k], rings[-1][(k + 1) % segments], top, cap or colour)
    kit.poly(rings[0], (0, 0, -1), colour)


# --- walls and roofs --------------------------------------------------------


def log_courses(kit, at, u0, u1, z0, z1, count, out, colour, openings=(), cap0=False, cap1=False, end=None):
    """Courses of faceted logs standing proud of a flat wall.

    `at(u, d, z)` gives the point u along the wall, d out from its face and z
    up. The logs stop either side of `openings` (dicts as `Kit.wall` takes),
    which must line up with the courses. `cap0` and `cap1` close the logs' ends
    at u0 and u1.
    """
    origin = Vector(at(0, 0, 0))
    t = Vector(at(1, 0, 0)) - origin
    n = Vector(at(0, 1, 0)) - origin
    up = Vector((0, 0, 1))
    step = (z1 - z0) / count
    for k in range(count):
        za, zb = z0 + k * step, z0 + (k + 1) * step
        zm = (za + zb) / 2
        blocked = sorted((o["x0"], o["x1"]) for o in openings if o["z0"] < zb - 1e-3 and o["z1"] > za + 1e-3)
        spans = []
        cursor, capped = u0, cap0
        for a, b in blocked:
            if a - cursor > 1e-3:
                spans.append((cursor, a, capped, True))
            cursor, capped = max(cursor, b), True
        if u1 - cursor > 1e-3:
            spans.append((cursor, u1, capped, cap1))
        for a, b, cap_a, cap_b in spans:
            kit.poly([at(a, 0, za), at(b, 0, za), at(b, out, zm), at(a, out, zm)], n - up, colour)
            kit.poly([at(a, out, zm), at(b, out, zm), at(b, 0, zb), at(a, 0, zb)], n + up, colour)
            if cap_a:
                kit.poly([at(a, 0, za), at(a, out, zm), at(a, 0, zb)], -t, end or colour)
            if cap_b:
                kit.poly([at(b, 0, za), at(b, out, zm), at(b, 0, zb)], t, end or colour)


def roof_halves(axis, lo, hi, half, eave_z, ridge_z, thickness, colour, mid=0.0):
    """The two slopes of a pitched roof, as two Kits (the low side first).

    The ridge runs along `axis` ("x" or "y") from lo to hi, at `mid` on the
    other axis; the eaves are `half` out from it.
    """
    kits = []
    for sign in (-1, 1):
        e = mid + sign * half
        if axis == "x":
            bottom = [(lo, e, eave_z), (hi, e, eave_z), (hi, mid, ridge_z), (lo, mid, ridge_z)]
        else:
            bottom = [(e, lo, eave_z), (e, hi, eave_z), (mid, hi, ridge_z), (mid, lo, ridge_z)]
        kit = Kit()
        kit.slab(bottom, thickness, colour)
        kits.append(kit)
    return kits


def railing(kit, a, b, height, colour, posts=3, width=0.14, mid_rail=False):
    """A handrail from a to b (points at deck level) on `posts` posts."""
    a = Vector(a)
    b = Vector(b)
    up = Vector((0, 0, height))
    beam(kit, a + up, b + up, width, colour, caps=False)
    if mid_rail:
        beam(kit, a + up * 0.5, b + up * 0.5, width * 0.8, colour, caps=False)
    for k in range(posts):
        p = a + (b - a) * (k / (posts - 1) if posts > 1 else 0.5)
        beam(kit, p, p + up, width, colour, caps=False)


def ladder(kit, a, b, across, colour, width=0.8, rung=0.75, rail=0.12, rung_colour=None):
    """A ladder from a up to b: two rails and flat rungs. `across` is the direction the rungs run."""
    a = Vector(a)
    b = Vector(b)
    side = Vector(across).normalized() * (width / 2)
    along = (b - a).normalized()
    facing = side.cross(along).normalized()
    for sign in (-1, 1):
        beam(kit, a + side * sign, b + side * sign, rail, colour, caps=False)
    length = (b - a).length
    count = max(2, round(length / rung))
    for k in range(count):
        p = a + along * ((k + 0.5) * length / count)
        quad = [p - side - along * 0.06, p + side - along * 0.06, p + side + along * 0.06, p - side + along * 0.06]
        kit.poly(quad, facing, rung_colour or colour)
        kit.poly(quad, -facing, rung_colour or colour)


def arrow_board(kit, centre, angle, length, height, thickness, colour, stripe=None):
    """A signpost board pointing along `angle` (radians in the XY plane) from `centre`."""
    cx, cy, cz = centre
    d = Vector((math.cos(angle), math.sin(angle), 0))
    n = Vector((-math.sin(angle), math.cos(angle), 0))
    c = Vector((cx, cy, cz))
    h = height / 2
    outline = [(-length * 0.28, -h), (length * 0.5, -h), (length * 0.72, 0), (length * 0.5, h), (-length * 0.28, h)]
    near = [c + d * u + Vector((0, 0, v)) - n * (thickness / 2) for u, v in outline]
    far = [p + n * thickness for p in near]
    faces = [near, far]
    for i in range(len(outline)):
        j = (i + 1) % len(outline)
        faces.append([near[i], near[j], far[j], far[i]])
    kit.convex(faces, colour)
    if stripe:
        band = [(-length * 0.18, -h * 0.3), (length * 0.48, -h * 0.3), (length * 0.48, h * 0.3), (-length * 0.18, h * 0.3)]
        for sign in (-1, 1):
            kit.poly([c + d * u + Vector((0, 0, v)) + n * sign * (thickness / 2 + 0.015) for u, v in band], n * sign, stripe)


# --- pictures (no words) ----------------------------------------------------

PICTURES = ("pine", "tree", "leaf", "toadstool", "mountain")


def picture(kit, name, centre, normal, size, lift=0.03):
    """A simple picture made of a few flat polygons, about `size` across."""

    def draw(points, colour, layer=0):
        flat(kit, centre, normal, points, colour, lift=lift + 0.02 * layer, scale=size)

    if name == "pine":
        draw([(-0.07, -0.5), (0.07, -0.5), (0.07, -0.3), (-0.07, -0.3)], "doorBrown")
        draw([(-0.4, -0.32), (0.4, -0.32), (0.0, 0.2)], "hedge", 1)
        draw([(-0.28, 0.0), (0.28, 0.0), (0.0, 0.5)], "hedge", 2)
    elif name == "tree":
        draw([(-0.08, -0.5), (0.08, -0.5), (0.08, -0.1), (-0.08, -0.1)], "doorBrown")
        draw(polygon(0.34, 8, cy=0.12), "leaf", 1)
    elif name == "leaf":
        draw([(0.0, -0.42), (0.3, -0.12), (0.26, 0.2), (0.0, 0.5), (-0.26, 0.2), (-0.3, -0.12)], "leaf")
        draw([(-0.035, -0.52), (0.035, -0.52), (0.035, 0.3), (-0.035, 0.3)], "hedge", 1)
    elif name == "toadstool":
        draw([(-0.12, -0.45), (0.12, -0.45), (0.1, 0.0), (-0.1, 0.0)], "trimWhite")
        draw([(-0.45, -0.02), (0.45, -0.02), (0.3, 0.3), (0.0, 0.42), (-0.3, 0.3)], "tomato", 1)
        draw(polygon(0.07, 6, cx=-0.18, cy=0.14), "trimWhite", 2)
        draw(polygon(0.07, 6, cx=0.16, cy=0.18), "trimWhite", 2)
    else:  # mountain
        draw([(-0.5, -0.4), (0.5, -0.4), (0.12, 0.42)], "stone")
        draw([(-0.03, 0.1), (0.27, 0.1), (0.12, 0.42)], "trimWhite", 1)
        draw([(-0.5, -0.4), (0.1, -0.4), (-0.22, 0.12)], "hedge", 2)


def pennant(kit, x, y, z0, height, pole, cloth, facing=1, size=(0.9, 0.6), width=0.1):
    """A thin pole with a little triangular flag flying towards +X (or -X)."""
    top = z0 + height
    beam(kit, (x, y, z0), (x, y, top), width, pole)
    points = [(x, y, top - 0.05), (x, y, top - 0.05 - size[1]), (x + facing * size[0], y, top - 0.05 - size[1] / 2)]
    kit.poly(points, (0, -1, 0), cloth)
    kit.poly(points, (0, 1, 0), cloth)


def facet_point(i, radius, z, sides=8, cx=0.0, cy=0.0):
    """The middle of facet i (numbered as `dome` and `shapes_blocktown.shell` do) of an n-gon of corner `radius`."""
    a = math.pi / sides + (i + 0.5) * 2 * math.pi / sides
    r = radius * math.cos(math.pi / sides)
    return (cx + r * math.cos(a), cy + r * math.sin(a), z)


def facet_normal(i, lean=0.0, sides=8):
    """The way facet i faces. `lean` tips it up (a wall that tapers in by `lean` metres per metre of height)."""
    a = math.pi / sides + (i + 0.5) * 2 * math.pi / sides
    return (math.cos(a), math.sin(a), lean)
