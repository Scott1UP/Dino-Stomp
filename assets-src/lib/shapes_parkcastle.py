"""Shapes shared by the Playground Park and Castle Hill generators.

Low-poly round things (8-sided by default), pieces of n-gon rings, and boxes
and quads placed in a rotated local frame (for the facets of a round building).

An n-gon here always has a flat facet facing the front (-Y). Facet 0 is the
front one and they count anticlockwise seen from above, so on an octagon
facet 2 faces +X, facet 4 faces the back and facet 6 faces -X. Corner i is
where facet i starts: facet i runs from corner i to corner i + 1.
"""

import math


def polar(r, deg, z=0.0, cx=0.0, cy=0.0):
    a = math.radians(deg)
    return (cx + r * math.cos(a), cy + r * math.sin(a), z)


def facet_deg(i, sides=8):
    """The direction facet i faces."""
    return -90.0 + i * 360.0 / sides


def corner_deg(i, sides=8):
    return -90.0 + (i - 0.5) * 360.0 / sides


def apothem(r, sides=8):
    """Centre-to-facet distance of an n-gon with corner radius r."""
    return r * math.cos(math.pi / sides)


def side_length(r, sides=8):
    return 2 * r * math.sin(math.pi / sides)


def ring(r, z, sides=8, cx=0.0, cy=0.0):
    return [polar(r, corner_deg(i, sides), z, cx, cy) for i in range(sides)]


def frustum(kit, r0, r1, z0, z1, colour, sides=8, cx=0.0, cy=0.0, bottom=True, top=True, stripes=None):
    """A prism, frustum or cone. r1 = 0 makes a cone, r0 = 0 an upside-down one.

    `stripes` is a list of colours cycled round the side faces.
    """
    faces = []
    lower = ring(r0, z0, sides, cx, cy) if r0 > 1e-6 else None
    upper = ring(r1, z1, sides, cx, cy) if r1 > 1e-6 else None
    for i in range(sides):
        j = (i + 1) % sides
        if upper is None:
            faces.append([lower[i], lower[j], (cx, cy, z1)])
        elif lower is None:
            faces.append([(cx, cy, z0), upper[j], upper[i]])
        else:
            faces.append([lower[i], lower[j], upper[j], upper[i]])
    colours = {}
    if stripes:
        for i in range(sides):
            colours[i] = stripes[i % len(stripes)]
    if bottom and lower is not None:
        faces.append(lower)
    if top and upper is not None:
        faces.append(upper)
    kit.convex(faces, colour, colours)


def ball(kit, cx, cy, cz, r, colour, sides=6, squash=1.0):
    """A chunky low-poly ball: two cones and a band. `squash` flattens it."""
    h = r * squash
    lower = ring(r, cz - h * 0.4, sides, cx, cy)
    upper = ring(r, cz + h * 0.4, sides, cx, cy)
    faces = []
    for i in range(sides):
        j = (i + 1) % sides
        faces.append([(cx, cy, cz - h), lower[j], lower[i]])
        faces.append([lower[i], lower[j], upper[j], upper[i]])
        faces.append([upper[i], upper[j], (cx, cy, cz + h)])
    kit.convex(faces, colour)


def wall_segment(
    kit, i, r_out, r_in, z0, z1, colour, inner=None, sides=8, cx=0.0, cy=0.0, f0=0.0, f1=1.0, top=None, bottom=None
):
    """The piece of an n-gon ring wall on facet i, between heights z0 and z1.

    f0..f1 picks part of the facet's width (0 = corner i, 1 = corner i + 1),
    for jambs either side of an opening. `top` and `bottom` recolour those faces.
    """

    def lerp(a, b, f):
        return tuple(a[k] + (b[k] - a[k]) * f for k in range(3))

    def corners(r, z):
        a = polar(r, corner_deg(i, sides), z, cx, cy)
        b = polar(r, corner_deg(i + 1, sides), z, cx, cy)
        return lerp(a, b, f0), lerp(a, b, f1)

    o0, o1 = corners(r_out, z0)
    o2, o3 = corners(r_out, z1)
    i0, i1 = corners(r_in, z0)
    i2, i3 = corners(r_in, z1)
    faces = [
        [o0, o1, o3, o2],  # outside
        [i0, i1, i3, i2],  # inside
        [o2, o3, i3, i2],  # top
        [o0, o1, i1, i0],  # bottom
        [o0, i0, i2, o2],
        [o1, i1, i3, o3],
    ]
    colours = {1: inner or colour}
    if top:
        colours[2] = top
    if bottom:
        colours[3] = bottom
    kit.convex(faces, colour, colours)


def wedge(kit, i, span, r0, r1, z0, z1, colour, sides=8, cx=0.0, cy=0.0, stripes=None, under=None):
    """A solid slice of a frustum or cone, from the centre out to `span` facets starting at facet i.

    Quarter roofs and quarter platforms. r1 = 0 brings the slice to a point.
    `stripes` cycles colours round the outside faces; `under` recolours the underside.
    """
    lower = [polar(r0, corner_deg(i + k, sides), z0, cx, cy) for k in range(span + 1)]
    faces = []
    colours = {}
    if r1 > 1e-6:
        upper = [polar(r1, corner_deg(i + k, sides), z1, cx, cy) for k in range(span + 1)]
        for k in range(span):
            faces.append([lower[k], lower[k + 1], upper[k + 1], upper[k]])
        faces.append([(cx, cy, z1)] + upper)  # top
        faces.append([(cx, cy, z0), lower[0], upper[0], (cx, cy, z1)])
        faces.append([(cx, cy, z0), lower[-1], upper[-1], (cx, cy, z1)])
    else:
        for k in range(span):
            faces.append([lower[k], lower[k + 1], (cx, cy, z1)])
        faces.append([(cx, cy, z0), lower[0], (cx, cy, z1)])
        faces.append([(cx, cy, z0), lower[-1], (cx, cy, z1)])
    if stripes:
        for k in range(span):
            colours[k] = stripes[(i + k) % len(stripes)]
    faces.append([(cx, cy, z0)] + lower)  # underside
    if under:
        colours[len(faces) - 1] = under
    kit.convex(faces, colour, colours)


class Frame:
    """A local frame standing on a wall face: u runs along the face, v points out of it, z is up."""

    def __init__(self, origin, deg):
        a = math.radians(deg)
        self.origin = origin
        self.n = (math.cos(a), math.sin(a))
        self.t = (-math.sin(a), math.cos(a))

    def at(self, u, v, z):
        ox, oy, oz = self.origin
        return (ox + u * self.t[0] + v * self.n[0], oy + u * self.t[1] + v * self.n[1], oz + z)

    def normal(self, facing=1):
        return (self.n[0] * facing, self.n[1] * facing, 0.0)


def facet_frame(i, r, z=0.0, sides=8, cx=0.0, cy=0.0):
    """Frame at the middle of facet i of an n-gon with corner radius r."""
    return Frame(polar(apothem(r, sides), facet_deg(i, sides), z, cx, cy), facet_deg(i, sides))


def corner_frame(i, r, z=0.0, sides=8, cx=0.0, cy=0.0):
    """Frame at corner i, pointing straight out from the centre."""
    return Frame(polar(r, corner_deg(i, sides), z, cx, cy), corner_deg(i, sides))


def fbox(kit, frame, lo, hi, colour, skip=(), sides=None):
    """A box in a frame. lo and hi are (u, v, z). Sides are named -u +u -v +v -z +z."""
    u0, v0, z0 = lo
    u1, v1, z1 = hi
    p = frame.at
    quads = {
        "-u": [p(u0, v0, z0), p(u0, v1, z0), p(u0, v1, z1), p(u0, v0, z1)],
        "+u": [p(u1, v0, z0), p(u1, v1, z0), p(u1, v1, z1), p(u1, v0, z1)],
        "-v": [p(u0, v0, z0), p(u1, v0, z0), p(u1, v0, z1), p(u0, v0, z1)],
        "+v": [p(u0, v1, z0), p(u1, v1, z0), p(u1, v1, z1), p(u0, v1, z1)],
        "-z": [p(u0, v0, z0), p(u1, v0, z0), p(u1, v1, z0), p(u0, v1, z0)],
        "+z": [p(u0, v0, z1), p(u1, v0, z1), p(u1, v1, z1), p(u0, v1, z1)],
    }
    centre = p((u0 + u1) / 2, (v0 + v1) / 2, (z0 + z1) / 2)
    for name, quad in quads.items():
        if name in skip:
            continue
        mid = [sum(q[k] for q in quad) / 4 for k in range(3)]
        hint = tuple(mid[k] - centre[k] for k in range(3))
        kit.poly(quad, hint, (sides or {}).get(name, colour))


def fquad(kit, frame, u0, u1, z0, z1, v, colour, facing=1):
    """A flat panel parallel to the frame's face, v out from it."""
    p = frame.at
    kit.poly([p(u0, v, z0), p(u1, v, z0), p(u1, v, z1), p(u0, v, z1)], frame.normal(facing), colour)


def fshine(kit, frame, u0, u1, z0, z1, v, colour="windowShine"):
    """The diagonal glass shine, on a frame's face."""
    w = u1 - u0
    h = z1 - z0
    p = frame.at
    kit.poly(
        [
            p(u0 + w * 0.18, v, z0 + h * 0.52),
            p(u0 + w * 0.32, v, z0 + h * 0.52),
            p(u0 + w * 0.62, v, z0 + h * 0.86),
            p(u0 + w * 0.48, v, z0 + h * 0.86),
        ],
        frame.normal(),
        colour,
    )


def fwindow(kit, frame, u0, u1, z0, z1, v=0.04, glass="windowBlue", shine="windowShine"):
    """A dark pane with its shine, laid just proud of a face."""
    fquad(kit, frame, u0, u1, z0, z1, v, glass)
    fshine(kit, frame, u0, u1, z0, z1, v + 0.03, shine)


def slit(kit, frame, z0, z1, u=0.0, width=0.3, cross=True, v=0.04, colour="windowBlue"):
    """An arrow slit: a tall dark slot, with a short cross-bar."""
    fquad(kit, frame, u - width / 2, u + width / 2, z0, z1, v, colour)
    if cross:
        mid = z0 + (z1 - z0) * 0.62
        fquad(kit, frame, u - width * 1.4, u + width * 1.4, mid - width / 2, mid + width / 2, v, colour)


def flag(kit, x, y, z0, height, colour, direction=1, size=1.3, pole="trimWhite", shape="pennant", thick=0.08):
    """A flagpole standing at (x, y, z0) with a flag flying along X."""
    kit.box((x - thick, y - thick, z0), (x + thick, y + thick, z0 + height), pole, skip=("-z",))
    top = z0 + height - 0.1
    xa = x + thick * direction
    xb = xa + size * direction
    if shape == "pennant":
        section = [(xa, top), (xa, top - size * 0.75), (xb, top - size * 0.375)]
    else:
        section = [(xa, top), (xa, top - size * 0.7), (xb, top - size * 0.7), (xb, top)]
    kit.extrude_y(section, y - 0.04, y + 0.04, colour)


def banner(kit, frame, u, z_top, width, length, colour, v=0.06, trim="trimWhite"):
    """A cloth banner hanging flat on a face, with a pointed tail and a rail."""
    p = frame.at
    h = width / 2
    points = [
        p(u - h, v, z_top),
        p(u + h, v, z_top),
        p(u + h, v, z_top - length + h * 0.8),
        p(u, v, z_top - length),
        p(u - h, v, z_top - length + h * 0.8),
    ]
    kit.poly(points, frame.normal(), colour)
    kit.poly([frame.at(u + du, v - 0.03, z) for du, z in ((-h, z_top), (h, z_top), (h, z_top - length + h * 0.8), (0, z_top - length), (-h, z_top - length + h * 0.8))], frame.normal(-1), colour)
    fbox(kit, frame, (u - h - 0.12, 0.0, z_top), (u + h + 0.12, 0.16, z_top + 0.14), trim, skip=("-v",))


def crenels(kit, facets, r, z, colour, thickness=0.45, low=0.45, high=1.15, sides=8, cx=0.0, cy=0.0, cap=None):
    """Battlements on some facets of an n-gon: a low parapet with one merlon in the middle of each facet."""
    for i in facets:
        wall_segment(kit, i, r, r - thickness, z, z + low, colour, sides=sides, cx=cx, cy=cy)
        wall_segment(kit, i, r, r - thickness, z + low, z + high, colour, sides=sides, cx=cx, cy=cy, f0=0.22, f1=0.78, top=cap)
