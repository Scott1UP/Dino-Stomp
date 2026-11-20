"""Extra shapes for the prop generators: n-gon prisms, cones, faceted balls and flat panels.

Everything goes through `Kit.poly`, so faces are flat coloured and wound to
point outwards.
"""

import math

from mathutils import Vector

BRIGHT = ("tomato", "sunny", "cobalt", "tangerine", "bubblegum")


def _ring(radius, sides, phase):
    """Points of a regular n-gon. The default phase puts a flat side towards -v."""
    if phase is None:
        phase = -math.pi / 2 + math.pi / sides
    step = 2 * math.pi / sides
    return [(radius * math.cos(phase + i * step), radius * math.sin(phase + i * step)) for i in range(sides)]


def apothem(radius, sides):
    """Distance from the centre of an n-gon to the middle of a flat side."""
    return radius * math.cos(math.pi / sides)


def prism(
    kit,
    origin,
    lo,
    hi,
    r0,
    r1,
    sides,
    colour,
    bottom=True,
    top=True,
    bottom_colour=None,
    top_colour=None,
    side_colours=None,
    axis="z",
    phase=None,
    scale=(1.0, 1.0),
):
    """An n-gon prism, frustum or cone (r1 = 0, or r0 = 0 for a point at the bottom).

    axis "z": `origin` is (x, y) and the prism runs from z = lo to z = hi.
    axis "x": `origin` is (y, z) and it runs from x = lo to x = hi (wheels).
    axis "y": `origin` is (x, z) and it runs from y = lo to y = hi.
    `side_colours` is an optional list, cycled round the sides.
    """
    a, b = origin

    def place(u, v, w):
        u *= scale[0]
        v *= scale[1]
        if axis == "z":
            return Vector((a + u, b + v, w))
        if axis == "x":
            return Vector((w, a + u, b + v))
        return Vector((a + u, w, b + v))

    def direction(u, v, w):
        if axis == "z":
            return Vector((u, v, w))
        if axis == "x":
            return Vector((w, u, v))
        return Vector((u, w, v))

    unit = _ring(1.0, sides, phase)
    low = [place(u * r0, v * r0, lo) for u, v in unit]
    high = [place(u * r1, v * r1, hi) for u, v in unit]
    for i in range(sides):
        j = (i + 1) % sides
        shade = side_colours[i % len(side_colours)] if side_colours else colour
        mid = direction(unit[i][0] + unit[j][0], unit[i][1] + unit[j][1], 0)
        if r1 < 1e-6:
            kit.poly([low[i], low[j], high[i]], mid, shade)
        elif r0 < 1e-6:
            kit.poly([high[i], high[j], low[i]], mid, shade)
        else:
            kit.poly([low[i], low[j], high[j], high[i]], mid, shade)
    if bottom and r0 > 1e-6:
        kit.poly(low, direction(0, 0, -1), bottom_colour or colour)
    if top and r1 > 1e-6:
        kit.poly(high, direction(0, 0, 1), top_colour or colour)


def ball(kit, centre, radius, segments, rings, colour, colour_fn=None, squash=1.0, matrix=None):
    """A faceted ball: `segments` round, `rings` bands from bottom to top.

    `colour_fn(segment, ring)` overrides the colour (ring 0 is the bottom fan).
    `squash` scales the height. `matrix` (3x3) tilts the ball about its centre.
    """
    centre = Vector(centre)

    def point(segment, ring):
        lat = -math.pi / 2 + math.pi * ring / rings
        lon = 2 * math.pi * segment / segments
        local = Vector(
            (
                radius * math.cos(lat) * math.cos(lon),
                radius * math.cos(lat) * math.sin(lon),
                radius * math.sin(lat) * squash,
            )
        )
        if matrix is not None:
            local = matrix @ local
        return centre + local

    for ring in range(rings):
        for segment in range(segments):
            nxt = (segment + 1) % segments
            if ring == 0:
                points = [point(0, 0), point(nxt, 1), point(segment, 1)]
            elif ring == rings - 1:
                points = [point(segment, ring), point(nxt, ring), point(0, rings)]
            else:
                points = [point(segment, ring), point(nxt, ring), point(nxt, ring + 1), point(segment, ring + 1)]
            middle = sum(points, Vector()) / len(points)
            shade = colour_fn(segment, ring) if colour_fn else colour
            kit.poly(points, middle - centre, shade)


def panel_y(kit, x0, x1, z0, z1, y, facing, colour):
    """A flat quad in the XZ plane. `facing` is -1 (faces -Y, the front) or +1."""
    kit.poly([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], (0, facing, 0), colour)


def panel_x(kit, y0, y1, z0, z1, x, facing, colour):
    """A flat quad in the YZ plane. `facing` is -1 (faces -X) or +1."""
    kit.poly([(x, y0, z0), (x, y1, z0), (x, y1, z1), (x, y0, z1)], (facing, 0, 0), colour)


def panel_z(kit, x0, x1, y0, y1, z, facing, colour):
    """A flat quad in the XY plane. `facing` is +1 (faces up) or -1."""
    kit.poly([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], (0, 0, facing), colour)
