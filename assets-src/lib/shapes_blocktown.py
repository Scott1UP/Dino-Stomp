"""Shapes shared by the Block Town building generators.

Everything here adds faces to a `meshkit.Kit`, in the same building frame:
X along the frontage, the front faces -Y, Z is up.
"""

import math

from mathutils import Vector

from .meshkit import Kit


def wall_y(kit, y0, y1, z0, z1, x_out, thickness, inward, openings, colours):
    """`Kit.wall` turned to run along Y: a side wall with recessed openings.

    `x_out` is the outside face and `inward` is +1 or -1: the X direction from
    the outside face towards the inside of the building. The openings' `x0`
    and `x1` are positions along Y.
    """
    turned = Kit()
    turned.wall(y0, y1, z0, z1, x_out, thickness, inward, openings, colours)
    for points, colour in turned.faces:
        # Swapping X and Y mirrors the wall, so the winding is reversed to match.
        kit.faces.append(([Vector((p.y, p.x, p.z)) for p in reversed(points)], colour))


def ring(cx, cy, z, radius, sides=8, phase=None):
    """Points of a regular polygon in the XY plane. By default its flats face the axes."""
    if phase is None:
        phase = math.pi / sides
    step = 2 * math.pi / sides
    return [(cx + radius * math.cos(phase + i * step), cy + radius * math.sin(phase + i * step), z) for i in range(sides)]


def frustum(kit, cx, cy, z0, r0, z1, r1, colour, sides=8, bottom=None, top=None, phase=None, only=None):
    """A low-poly cylinder, cone or tapered drum standing on Z.

    `bottom` and `top` are cap colours (None leaves the end open). A radius of
    0 makes a point. `only` lists the facets to build, for round things that
    break into pieces.
    """
    if phase is None:
        phase = math.pi / sides
    step = 2 * math.pi / sides
    lower = ring(cx, cy, z0, r0, sides, phase)
    upper = ring(cx, cy, z1, r1, sides, phase)
    lean = 0.5 if r0 > r1 else (-0.5 if r1 > r0 else 0.0)
    for i in range(sides) if only is None else only:
        j = (i + 1) % sides
        angle = phase + (i + 0.5) * step
        hint = (math.cos(angle), math.sin(angle), lean)
        if r1 < 1e-6:
            points = [lower[i], lower[j], (cx, cy, z1)]
        elif r0 < 1e-6:
            points = [(cx, cy, z0), upper[j], upper[i]]
        else:
            points = [lower[i], lower[j], upper[j], upper[i]]
        kit.poly(points, hint, colour)
    if bottom and r0 > 1e-6:
        kit.poly(lower, (0, 0, -1), bottom)
    if top and r1 > 1e-6:
        kit.poly(upper, (0, 0, 1), top)


def shell(kit, cx, cy, profile, thickness, facets, colour, interior, sides=8):
    """Part of a hollow round wall: the given facets of a drum with real thickness.

    `profile` is a list of (z, outside radius) from bottom to top.
    """
    phase = math.pi / sides
    step = 2 * math.pi / sides
    facets = list(facets)

    def point(angle, radius, z):
        return (cx + radius * math.cos(angle), cy + radius * math.sin(angle), z)

    for (za, ra), (zb, rb) in zip(profile, profile[1:]):
        for i in facets:
            a0 = phase + i * step
            a1 = a0 + step
            mid = a0 + step / 2
            out = (math.cos(mid), math.sin(mid), 0)
            kit.poly([point(a0, ra, za), point(a1, ra, za), point(a1, rb, zb), point(a0, rb, zb)], out, colour)
            kit.poly(
                [
                    point(a0, ra - thickness, za),
                    point(a1, ra - thickness, za),
                    point(a1, rb - thickness, zb),
                    point(a0, rb - thickness, zb),
                ],
                (-out[0], -out[1], 0),
                interior,
            )
        # The cut ends, where this piece meets its neighbours.
        for angle, side in ((phase + facets[0] * step, -1), (phase + (facets[-1] + 1) * step, 1)):
            tangent = (-math.sin(angle) * side, math.cos(angle) * side, 0)
            kit.poly(
                [point(angle, ra, za), point(angle, ra - thickness, za), point(angle, rb - thickness, zb), point(angle, rb, zb)],
                tangent,
                colour,
            )
    for (z, r), hint in ((profile[0], (0, 0, -1)), (profile[-1], (0, 0, 1))):
        for i in facets:
            a0 = phase + i * step
            a1 = a0 + step
            kit.poly([point(a0, r, z), point(a1, r, z), point(a1, r - thickness, z), point(a0, r - thickness, z)], hint, colour)


def hoop(kit, cx, cy, z0, z1, radius, facets, colour, sides=8):
    """A band standing proud of a round wall: outside, top and bottom faces only."""
    phase = math.pi / sides
    step = 2 * math.pi / sides
    inner = radius - 0.25

    def point(angle, r, z):
        return (cx + r * math.cos(angle), cy + r * math.sin(angle), z)

    for i in facets:
        a0 = phase + i * step
        a1 = a0 + step
        mid = a0 + step / 2
        kit.poly([point(a0, radius, z0), point(a1, radius, z0), point(a1, radius, z1), point(a0, radius, z1)], (math.cos(mid), math.sin(mid), 0), colour)
        kit.poly([point(a0, radius, z1), point(a1, radius, z1), point(a1, inner, z1), point(a0, inner, z1)], (0, 0, 1), colour)
        kit.poly([point(a0, radius, z0), point(a1, radius, z0), point(a1, inner, z0), point(a0, inner, z0)], (0, 0, -1), colour)


def _frame(normal, up=(0, 0, 1)):
    """Right and up vectors of a plane facing `normal`, as seen from outside it."""
    n = Vector(normal).normalized()
    up = Vector(up)
    if abs(n.dot(up)) > 0.99:
        up = Vector((0, 1, 0))
    u = up.cross(n).normalized()
    v = n.cross(u).normalized()
    return n, u, v


def flat(kit, centre, normal, points, colour, lift=0.0, scale=1.0):
    """A flat polygon drawn in a plane facing `normal`.

    `points` are (right, up) pairs as seen from outside, in units of `scale`.
    `lift` moves it out along the normal, to sit proud of what is behind it.
    """
    n, u, v = _frame(normal)
    origin = Vector(centre) + n * lift
    kit.poly([origin + u * (a * scale) + v * (b * scale) for a, b in points], n, colour)


def polygon(radius, sides=8, cx=0.0, cy=0.0, squash=1.0, phase=None):
    """(right, up) points of a regular polygon, for `flat`."""
    if phase is None:
        phase = math.pi / sides
    step = 2 * math.pi / sides
    return [(cx + radius * math.cos(phase + i * step), cy + radius * squash * math.sin(phase + i * step)) for i in range(sides)]


def round_window(kit, centre, normal, radius, trim, glass="windowBlue", shine="windowShine"):
    """An octagonal window: a trim ring, dark glass and the diagonal shine."""
    flat(kit, centre, normal, polygon(radius), trim, lift=0.03)
    flat(kit, centre, normal, polygon(radius * 0.76), glass, lift=0.06)
    r = radius * 0.76
    flat(
        kit,
        centre,
        normal,
        [(-0.42 * r, -0.05 * r), (-0.14 * r, -0.05 * r), (0.38 * r, 0.52 * r), (0.1 * r, 0.52 * r)],
        shine,
        lift=0.09,
    )


def beam(kit, start, end, width, colour, depth=None, caps=True):
    """A square-section bar between two points, at any angle."""
    start = Vector(start)
    end = Vector(end)
    axis = (end - start).normalized()
    side = axis.cross(Vector((0, 0, 1)))
    if side.length < 1e-6:
        side = Vector((1, 0, 0))
    side.normalize()
    other = side.cross(axis).normalized()
    a = side * (width / 2)
    b = other * ((depth or width) / 2)
    near = [start + a + b, start - a + b, start - a - b, start + a - b]
    far = [end + a + b, end - a + b, end - a - b, end + a - b]
    faces = [[near[i], near[(i + 1) % 4], far[(i + 1) % 4], far[i]] for i in range(4)]
    if caps:
        faces += [near, far]
    kit.convex(faces, colour)


def pictogram(kit, name, centre, normal, size, lift=0.03):
    """A shop's picture sign, made of a few flat polygons: "loaf", "cone" or "fish"."""

    def draw(points, colour, layer=0):
        flat(kit, centre, normal, points, colour, lift=lift + 0.03 * layer, scale=size)

    if name == "loaf":
        draw(polygon(0.48, 8, squash=0.62), "wood")
        for x in (-0.22, 0.0, 0.22):
            draw([(x - 0.1, -0.12), (x - 0.03, -0.12), (x + 0.1, 0.16), (x + 0.03, 0.16)], "doorBrown", 1)
    elif name == "cone":
        draw([(-0.2, 0.02), (0.2, 0.02), (0.0, -0.5)], "wood")
        draw(polygon(0.27, 8, cy=0.2), "bubblegum", 1)
        draw(polygon(0.08, 6, cy=0.45), "tomato", 2)
    else:  # fish, swimming left
        draw([(-0.48, 0.0), (-0.22, 0.24), (0.12, 0.24), (0.3, 0.0), (0.12, -0.24), (-0.22, -0.24)], "cobalt")
        draw([(0.24, 0.0), (0.5, 0.26), (0.5, -0.26)], "cobalt")
        draw([(-0.34, 0.03), (-0.25, 0.03), (-0.25, 0.12), (-0.34, 0.12)], "trimWhite", 1)


def plaque(kit, centre, normal, points, depth, colour, face=None):
    """A flat shape standing `depth` proud of a wall: its edge and its front face.

    `points` are (right, up) pairs as seen from outside, like `flat`.
    """
    n, u, v = _frame(normal)
    centre = Vector(centre)
    back = [centre + u * a + v * b for a, b in points]
    front = [p + n * depth for p in back]
    count = len(points)
    for i in range(count):
        j = (i + 1) % count
        middle = (back[i] + back[j]) / 2 - centre
        kit.poly([back[i], back[j], front[j], front[i]], middle, colour)
    kit.poly(front, n, face or colour)


def clock_face(kit, centre, normal, radius, rim, hour, minute, face="trimWhite", hands="tyre"):
    """An octagonal clock standing proud of a wall, with four hour marks and two hands."""
    depth = 0.22
    plaque(kit, centre, normal, polygon(radius), depth, rim)
    flat(kit, centre, normal, polygon(radius * 0.84), face, lift=depth + 0.03)
    r = radius * 0.84
    for quarter in range(4):
        angle = quarter * math.pi / 2
        c, s = math.cos(angle), math.sin(angle)
        mark = [(0.78, -0.06), (0.94, -0.06), (0.94, 0.06), (0.78, 0.06)]
        flat(kit, centre, normal, [(a * c - b * s, a * s + b * c) for a, b in mark], hands, lift=depth + 0.06, scale=r)
    hour_angle = (hour % 12 + minute / 60) / 12 * 2 * math.pi
    minute_angle = minute / 60 * 2 * math.pi
    for angle, length, half in ((hour_angle, 0.5, 0.07), (minute_angle, 0.78, 0.05)):
        along = (math.sin(angle), math.cos(angle))  # clockwise from twelve
        across = (along[1], -along[0])
        hand = [
            (-along[0] * 0.12 + across[0] * half, -along[1] * 0.12 + across[1] * half),
            (along[0] * length + across[0] * half, along[1] * length + across[1] * half),
            (along[0] * length - across[0] * half, along[1] * length - across[1] * half),
            (-along[0] * 0.12 - across[0] * half, -along[1] * 0.12 - across[1] * half),
        ]
        flat(kit, centre, normal, hand, hands, lift=depth + 0.09, scale=r)
