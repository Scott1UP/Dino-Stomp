"""Shapes for the fairground and playground generators.

Beams between any two points (legs, spokes, chains, slides), six-faced solids
from eight loose corners (spiral slide pieces), tapering pieces of an n-gon
tower, and profiles extruded inside a rotated frame (carousel horses).

Everything goes through `Kit.convex` or `Kit.poly`, so faces point outwards.
"""

from mathutils import Vector

from .shapes_parkcastle import corner_deg, polar


def beam(kit, a, b, width, colour, depth=None, up=(0, 0, 1), caps=True, flat=False, end_colour=None):
    """A square bar from point a to point b.

    `width` is measured sideways (across both the bar and `up`), `depth` the
    other way. `flat` cuts both ends level (legs standing on the ground)
    instead of square to the bar. `caps=False` leaves the ends open.
    """
    a = Vector(a)
    b = Vector(b)
    up = Vector(up)
    axis = (b - a).normalized()
    side = axis.cross(up)
    if side.length < 1e-4:
        side = axis.cross(Vector((1, 0, 0)))
    side.normalize()
    other = side.cross(axis).normalized()
    half_side = side * (width / 2)
    half_other = other * ((depth or width) / 2)
    if flat:
        level = up.cross(side).normalized()
        lean = other.dot(level)
        if abs(lean) > 0.2:
            half_other = level * ((depth or width) / 2 / lean)
    start = [a - half_side - half_other, a + half_side - half_other, a + half_side + half_other, a - half_side + half_other]
    end = [p + (b - a) for p in start]
    faces = [[start[i], start[(i + 1) % 4], end[(i + 1) % 4], end[i]] for i in range(4)]
    colours = {}
    if caps:
        faces += [start, end]
        if end_colour:
            colours = {4: end_colour, 5: end_colour}
    kit.convex(faces, colour, colours)


def hexa(kit, bottom, top, colour, colours=None, skip=()):
    """A six-faced solid from four bottom corners and the four above them.

    Face numbers, for `colours` and `skip`: 0 bottom, 1 top, 2-5 the sides
    (side 2 runs from corner 0 to corner 1, and so on round).
    """
    faces = [list(bottom), list(top)]
    for i in range(4):
        j = (i + 1) % 4
        faces.append([bottom[i], bottom[j], top[j], top[i]])
    every = [Vector(p) for face in faces for p in face]
    centre = sum(every, Vector()) / len(every)
    for index, face in enumerate(faces):
        if index in skip:
            continue
        middle = sum((Vector(p) for p in face), Vector()) / len(face)
        kit.poly(face, middle - centre, (colours or {}).get(index, colour))


def taper_wall(kit, i, r0, r1, thickness, z0, z1, colour, inner=None, sides=8):
    """Facet i of a tapering n-gon tower wall: corner radius r0 at z0, r1 at z1."""
    o0 = polar(r0, corner_deg(i, sides), z0)
    o1 = polar(r0, corner_deg(i + 1, sides), z0)
    o2 = polar(r1, corner_deg(i + 1, sides), z1)
    o3 = polar(r1, corner_deg(i, sides), z1)
    i0 = polar(r0 - thickness, corner_deg(i, sides), z0)
    i1 = polar(r0 - thickness, corner_deg(i + 1, sides), z0)
    i2 = polar(r1 - thickness, corner_deg(i + 1, sides), z1)
    i3 = polar(r1 - thickness, corner_deg(i, sides), z1)
    faces = [
        [o0, o1, o2, o3],  # outside
        [i0, i1, i2, i3],  # inside
        [o3, o2, i2, i3],  # top
        [o0, o1, i1, i0],  # bottom
        [o0, i0, i3, o3],
        [o1, i1, i2, o2],
    ]
    kit.convex(faces, colour, {1: inner or colour})


def taper_quad(kit, i, r0, r1, z0, z1, f0, f1, g0, g1, colour, proud=0.05, sides=8):
    """A flat decal on the outside of a `taper_wall` facet.

    f0..f1 is the part of the facet's width and g0..g1 the part of its height.
    """
    a0 = Vector(polar(r0, corner_deg(i, sides), z0))
    b0 = Vector(polar(r0, corner_deg(i + 1, sides), z0))
    a1 = Vector(polar(r1, corner_deg(i, sides), z1))
    b1 = Vector(polar(r1, corner_deg(i + 1, sides), z1))
    normal = (b0 - a0).cross(a1 - a0).normalized()
    middle = (a0 + b0 + a1 + b1) / 4
    if normal.dot(Vector((middle.x, middle.y, 0))) < 0:
        normal = -normal

    def at(f, g):
        low = a0.lerp(b0, f)
        high = a1.lerp(b1, f)
        return low.lerp(high, g) + normal * proud

    kit.poly([at(f0, g0), at(f1, g0), at(f1, g1), at(f0, g1)], normal, colour)


def fextrude(kit, frame, section, v0, v1, colour, colours=None):
    """Extrude a convex (u, z) profile across a frame, from v0 to v1."""
    near = [frame.at(u, v0, z) for u, z in section]
    far = [frame.at(u, v1, z) for u, z in section]
    faces = [near, far]
    count = len(section)
    for i in range(count):
        j = (i + 1) % count
        faces.append([near[i], near[j], far[j], far[i]])
    kit.convex(faces, colour, colours)


def mirror_x(kit):
    """Flip everything in a kit left to right, keeping the faces pointing outwards."""
    kit.faces = [([Vector((-p.x, p.y, p.z)) for p in reversed(points)], colour) for points, colour in kit.faces]
