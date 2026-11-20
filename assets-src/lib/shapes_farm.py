"""Shapes for the farm generators (barn, silo, coop, tractor, crops...).

Decals drawn in a wall face's own frame (windows, shutters, X-braced doors,
picture signs), pieces of a hollow banded drum (the silo), slabs with coloured
edges, and a few small solids. Everything goes through `Kit.poly` or
`Kit.convex`, so faces are flat coloured and point outwards.
"""

import math

from mathutils import Vector

from .shapes_parkcastle import Frame, fquad, fshine


def face(side, at, along=0.0):
    """A frame on an axis-aligned face: "front" (-Y), "back", "left" (-X) or "right".

    `at` is the face's Y (front, back) or X (left, right); `along` is where
    u = 0 sits along the face. u runs to the right as seen from outside.
    """
    if side == "front":
        return Frame((along, at, 0), -90)
    if side == "back":
        return Frame((along, at, 0), 90)
    if side == "left":
        return Frame((at, along, 0), 180)
    return Frame((at, along, 0), 0)


def fpoly(kit, frame, points, v, colour, facing=1):
    """A flat polygon of (u, z) points on a frame's face, v out from it."""
    kit.poly([frame.at(u, v, z) for u, z in points], frame.normal(facing), colour)


def window(kit, frame, u0, u1, z0, z1, trim="trimWhite", border=0.14, v=0.03):
    """A window laid on a face: trim surround, dark glass and the diagonal shine."""
    fquad(kit, frame, u0 - border, u1 + border, z0 - border, z1 + border, v, trim)
    fquad(kit, frame, u0, u1, z0, z1, v + 0.03, "windowBlue")
    fshine(kit, frame, u0, u1, z0, z1, v + 0.06)


def shutters(kit, frame, u0, u1, z0, z1, colour, width=0.42, v=0.05):
    """A pair of shutters either side of an opening u0..u1."""
    fquad(kit, frame, u0 - width - 0.04, u0 - 0.04, z0, z1, v, colour)
    fquad(kit, frame, u1 + 0.04, u1 + width + 0.04, z0, z1, v, colour)


def x_brace(kit, frame, u0, u1, z0, z1, v, colour, width=0.22, border=True):
    """White barn-door bracing: a border and two diagonals."""
    w = width
    if border:
        fquad(kit, frame, u0, u1, z0, z0 + w, v, colour)
        fquad(kit, frame, u0, u1, z1 - w, z1, v, colour)
        fquad(kit, frame, u0, u0 + w, z0 + w, z1 - w, v, colour)
        fquad(kit, frame, u1 - w, u1, z0 + w, z1 - w, v, colour)
        u0, u1, z0, z1 = u0 + w, u1 - w, z0 + w, z1 - w
    k = w * 1.3
    fpoly(kit, frame, [(u0, z0), (u0 + k, z0), (u1, z1), (u1 - k, z1)], v + 0.012, colour)
    fpoly(kit, frame, [(u1, z0), (u1 - k, z0), (u0, z1), (u0 + k, z1)], v + 0.012, colour)


def slab(kit, bottom, thickness, colour, colours=None):
    """`Kit.slab` with coloured faces: 0 underside, 1 top, 2 + i the edge from corner i."""
    top = [(x, y, z + thickness) for x, y, z in bottom]
    faces = [bottom, top]
    count = len(bottom)
    for i in range(count):
        j = (i + 1) % count
        faces.append([bottom[i], bottom[j], top[j], top[i]])
    kit.convex(faces, colour, colours)


# --- round things in pieces ---------------------------------------------------


def _pt(angle, radius, z):
    return (radius * math.cos(angle), radius * math.sin(angle), z)


def facet_angle(i, sides=8):
    """The direction facet i faces, in radians. With 8 sides facet 5 faces the front, 7 the right."""
    return math.pi / sides + (i + 0.5) * 2 * math.pi / sides


def ring_piece(kit, r, thick, z0, z1, facets, colour, interior, hoops=(), hoop_colour=None, proud=0.14, sides=8):
    """Some facets of a hollow drum with real thickness, banded with hoops.

    `facets` must be consecutive. `hoops` is a list of (z0, z1) bands standing
    `proud` of the wall.
    """
    phase = math.pi / sides
    step = 2 * math.pi / sides
    facets = list(facets)
    ri = r - thick
    for i in facets:
        a0 = phase + i * step
        a1 = a0 + step
        mid = a0 + step / 2
        out = (math.cos(mid), math.sin(mid), 0)
        kit.poly([_pt(a0, r, z0), _pt(a1, r, z0), _pt(a1, r, z1), _pt(a0, r, z1)], out, colour)
        kit.poly([_pt(a0, ri, z0), _pt(a1, ri, z0), _pt(a1, ri, z1), _pt(a0, ri, z1)], (-out[0], -out[1], 0), interior)
        kit.poly([_pt(a0, r, z1), _pt(a1, r, z1), _pt(a1, ri, z1), _pt(a0, ri, z1)], (0, 0, 1), colour)
        kit.poly([_pt(a0, r, z0), _pt(a1, r, z0), _pt(a1, ri, z0), _pt(a0, ri, z0)], (0, 0, -1), colour)
        for h0, h1 in hoops:
            rh = r + proud
            kit.poly([_pt(a0, rh, h0), _pt(a1, rh, h0), _pt(a1, rh, h1), _pt(a0, rh, h1)], out, hoop_colour or colour)
            kit.poly([_pt(a0, rh, h1), _pt(a1, rh, h1), _pt(a1, r, h1), _pt(a0, r, h1)], (0, 0, 1), hoop_colour or colour)
    for angle, way in ((phase + facets[0] * step, -1), (phase + (facets[-1] + 1) * step, 1)):
        tangent = (-math.sin(angle) * way, math.cos(angle) * way, 0)
        kit.poly([_pt(angle, r, z0), _pt(angle, ri, z0), _pt(angle, ri, z1), _pt(angle, r, z1)], tangent, colour)


def cap_piece(kit, profile, facets, colour, under=None, sides=8):
    """Some facets of a solid dome or cone: `profile` is (z, radius) from the rim up to the tip (radius 0)."""
    phase = math.pi / sides
    step = 2 * math.pi / sides
    facets = list(facets)
    z_base = profile[0][0]
    z_tip = profile[-1][0]
    for (za, ra), (zb, rb) in zip(profile, profile[1:]):
        lean = (ra - rb) / max(zb - za, 1e-6)
        for i in facets:
            a0 = phase + i * step
            a1 = a0 + step
            mid = a0 + step / 2
            hint = (math.cos(mid), math.sin(mid), lean)
            if rb < 1e-6:
                kit.poly([_pt(a0, ra, za), _pt(a1, ra, za), (0, 0, zb)], hint, colour)
            else:
                kit.poly([_pt(a0, ra, za), _pt(a1, ra, za), _pt(a1, rb, zb), _pt(a0, rb, zb)], hint, colour)
    for angle, way in ((phase + facets[0] * step, -1), (phase + (facets[-1] + 1) * step, 1)):
        tangent = (-math.sin(angle) * way, math.cos(angle) * way, 0)
        points = [(0, 0, z_base)] + [_pt(angle, r, z) for z, r in profile if r > 1e-6] + [(0, 0, z_tip)]
        kit.poly(points, tangent, colour)
    rim = [_pt(phase + i * step, profile[0][1], z_base) for i in range(facets[0], facets[-1] + 2)]
    kit.poly([(0, 0, z_base)] + rim, (0, 0, -1), under or colour)


def blob(kit, centre, radius, height, sides, colour, top_colour=None, turn=0.0, waist=0.45):
    """A little dome sitting on the ground: a ring of sloped sides and a pointed cap."""
    cx, cy, cz = centre
    step = 2 * math.pi / sides
    low = [(cx + radius * math.cos(turn + i * step), cy + radius * math.sin(turn + i * step), cz) for i in range(sides)]
    mid = [
        (cx + radius * 0.8 * math.cos(turn + i * step), cy + radius * 0.8 * math.sin(turn + i * step), cz + height * waist)
        for i in range(sides)
    ]
    tip = (cx, cy, cz + height)
    for i in range(sides):
        j = (i + 1) % sides
        a = turn + (i + 0.5) * step
        kit.poly([low[i], low[j], mid[j], mid[i]], (math.cos(a), math.sin(a), 0.3), colour)
        kit.poly([mid[i], mid[j], tip], (math.cos(a), math.sin(a), 1.0), top_colour or colour)


def stud(kit, centre, normal, radius, height, colour, sides=4):
    """A low pyramid standing on a surface: an apple on a tree, a knob."""
    n = Vector(normal).normalized()
    up = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((1, 0, 0))
    u = up.cross(n).normalized()
    w = n.cross(u)
    c = Vector(centre)
    base = [c + (u * math.cos(k * 2 * math.pi / sides) + w * math.sin(k * 2 * math.pi / sides)) * radius for k in range(sides)]
    tip = c + n * height
    for k in range(sides):
        a, b = base[k], base[(k + 1) % sides]
        kit.poly([a, b, tip], (a + b) / 2 - c + n * radius, colour)


def leaf_blade(kit, a, b, c, colour):
    """A free-standing triangle, visible from both sides."""
    a, b, c = Vector(a), Vector(b), Vector(c)
    n = (b - a).cross(c - a)
    kit.poly([a, b, c], n, colour)
    kit.poly([a, b, c], -n, colour)


# --- picture signs (no words) --------------------------------------------------

PICTURES = ("apple", "sunflower", "carrot", "barn", "sun", "wheat")


def picture(kit, name, frame, u, z, size, v=0.03):
    """A simple farm picture about `size` across, centred on (u, z) of a frame's face."""

    def draw(points, colour, layer=0):
        fpoly(kit, frame, [(u + a * size, z + b * size) for a, b in points], v + 0.025 * layer, colour)

    def disc(radius, sides=8, cx=0.0, cy=0.0, squash=1.0):
        return [
            (cx + radius * math.cos(math.pi / sides + i * 2 * math.pi / sides), cy + radius * squash * math.sin(math.pi / sides + i * 2 * math.pi / sides))
            for i in range(sides)
        ]

    if name == "apple":
        draw(disc(0.4, 8, cy=-0.06), "tomato")
        draw([(-0.04, 0.26), (0.04, 0.26), (0.08, 0.48), (0.0, 0.48)], "doorBrown", 1)
        draw([(0.06, 0.34), (0.3, 0.3), (0.34, 0.5), (0.14, 0.5)], "leaf", 1)
    elif name == "sunflower":
        draw([(-0.05, -0.5), (0.05, -0.5), (0.05, 0.0), (-0.05, 0.0)], "hedge")
        draw([(0.05, -0.36), (0.3, -0.3), (0.05, -0.16)], "hedge")
        draw(disc(0.36, 8, cy=0.12), "sunny", 1)
        draw(disc(0.17, 6, cy=0.12), "doorBrown", 2)
    elif name == "carrot":
        draw([(-0.2, 0.2), (0.2, 0.2), (0.0, -0.5)], "tangerine")
        draw([(-0.2, 0.2), (-0.06, 0.2), (-0.16, 0.5)], "leaf", 1)
        draw([(-0.06, 0.2), (0.08, 0.2), (0.02, 0.52)], "hedge", 1)
        draw([(0.06, 0.2), (0.2, 0.2), (0.2, 0.48)], "leaf", 1)
    elif name == "barn":
        draw([(-0.42, -0.42), (0.42, -0.42), (0.42, 0.06), (0.26, 0.34), (0.0, 0.46), (-0.26, 0.34), (-0.42, 0.06)], "tomato")
        draw([(-0.16, -0.42), (0.16, -0.42), (0.16, -0.02), (-0.16, -0.02)], "trimWhite", 1)
    elif name == "sun":
        draw([(0, 0.5), (0.13, 0.13), (0.5, 0), (0.13, -0.13), (0, -0.5), (-0.13, -0.13), (-0.5, 0), (-0.13, 0.13)], "tangerine")
        draw(disc(0.3, 8), "sunny", 1)
    else:  # wheat: a stalk with three pairs of grains
        draw([(-0.04, -0.5), (0.04, -0.5), (0.04, 0.3), (-0.04, 0.3)], "sunny")
        for k in range(3):
            y = -0.12 + k * 0.2
            draw([(0.04, y), (0.3, y + 0.14), (0.04, y + 0.2)], "sunny", 1)
            draw([(-0.04, y), (-0.3, y + 0.14), (-0.04, y + 0.2)], "sunny", 1)
        draw([(-0.07, 0.3), (0.07, 0.3), (0.0, 0.52)], "sunny", 1)
