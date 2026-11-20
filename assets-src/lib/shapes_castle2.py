"""More castle shapes: square-tower walls, arches, merlon rows, torches, shields, buttresses.

Used by the second batch of Castle Hill generators (castle_gate, castle_keep,
castle_tower, the richer castle_wall) and the castle props. Everything is laid
out on `shapes_parkcastle.Frame`s: u runs along a wall face, v points out of
it and z is up.
"""

import math

from mathutils import Vector

from .shapes_parkcastle import Frame, fbox, fquad, fshine

BRIGHTS = ["tomato", "sunny", "cobalt"]
ROOFS = ["tomato", "cobalt", "tangerine", "bubblegum"]


def rect_frames(cx, cy, hx, hy):
    """Frames on the four faces of a rectangle: front (-Y), back, left (-X) and right."""
    return {
        "front": Frame((cx, cy - hy, 0), -90),
        "back": Frame((cx, cy + hy, 0), 90),
        "right": Frame((cx + hx, cy, 0), 0),
        "left": Frame((cx - hx, cy, 0), 180),
    }


def box_wall(kit, frame, name, hx, hy, z0, z1, thick, colour="stone", inner="interiorCream", grow=0.0, skip=()):
    """One wall of a hollow rectangular tower. Front and back run the full width;
    left and right fit between them. `grow` steps the outside face out (a foot)."""
    half = hx + grow if name in ("front", "back") else hy - thick
    fbox(kit, frame, (-half, -thick, z0), (half, grow, z1), colour, skip=skip, sides={"-v": inner})


# --- arches -----------------------------------------------------------------


def _profile(t, pointed):
    t = min(1.0, abs(t))
    return (1 - t) ** 0.6 if pointed else math.sqrt(max(0.0, 1 - t * t))


def arch_points(u0, u1, z_spring, z_top, steps=3, pointed=False):
    """The curve of an arch from (u0, z_spring) over the crown to (u1, z_spring)."""
    mid = (u0 + u1) / 2
    half = (u1 - u0) / 2
    rise = z_top - z_spring
    count = 2 * steps
    points = []
    for k in range(count + 1):
        c = math.cos(math.pi * k / count)
        points.append((mid - half * c, z_spring + rise * _profile(c, pointed)))
    return points


def arch_height(u, points):
    """Height of the arch curve (from `arch_points`) at u."""
    for (ua, za), (ub, zb) in zip(points, points[1:]):
        if ua - 1e-9 <= u <= ub + 1e-9:
            f = 0.0 if ub - ua < 1e-9 else (u - ua) / (ub - ua)
            return za + (zb - za) * f
    return points[0][1]


def arched_panel(kit, frame, u0, u1, z0, z1, v, colour, steps=2, pointed=False, facing=1):
    """A flat panel with an arched top: a door leaf, a window pane or its surround."""
    width = u1 - u0
    rise = min(width * (0.8 if pointed else 0.5), (z1 - z0) * 0.7)
    outline = [(u0, z0), (u1, z0)] + arch_points(u0, u1, z1 - rise, z1, steps, pointed)[::-1]
    kit.poly([frame.at(u, v, z) for u, z in outline], frame.normal(facing), colour)


def arched_window(kit, frame, u0, u1, z0, z1, v=0.04, surround="trimWhite", glass="windowBlue", pointed=False):
    """A dark arched pane with its shine and a pale surround, laid just proud of a face."""
    if surround:
        arched_panel(kit, frame, u0 - 0.16, u1 + 0.16, z0 - 0.16, z1 + 0.16, v, surround, pointed=pointed)
    arched_panel(kit, frame, u0, u1, z0, z1, v + 0.03, glass, pointed=pointed)
    fshine(kit, frame, u0, u1, z0, z1 - (z1 - z0) * 0.12, v + 0.06)


def arch_half(kit, side, x_open, x_out, y0, y1, z_spring, z_crown, z_top, colour, trim=None, steps=3, pointed=False, ring=0.45, proud=0.06):
    """The masonry over one half of an arch centred on x = 0, running along X.

    side is -1 (the left half) or +1. The opening is 2 * x_open wide; the block
    runs out to x_out and up to z_top. `trim` adds a ring of voussoirs round
    the arch, front and back.
    """
    points = arch_points(-x_open, x_open, z_spring, z_crown, steps, pointed)
    curve = points[: steps + 1] if side < 0 else points[steps:][::-1]  # from the springing to the crown
    for (xa, za), (xb, zb) in zip(curve, curve[1:]):
        for y, facing in ((y0, -1), (y1, 1)):
            kit.poly([(xa, y, za), (xb, y, zb), (xb, y, z_top), (xa, y, z_top)], (0, facing, 0), colour)
        kit.poly([(xa, y0, za), (xb, y0, zb), (xb, y1, zb), (xa, y1, za)], (-side * 0.3, 0, -1), colour)
        if trim:
            def out(x, z):
                dx, dz = x, z - z_spring
                length = math.hypot(dx, dz) or 1.0
                return x + dx / length * ring, z + dz / length * ring

            (xc, zc), (xd, zd) = out(xa, za), out(xb, zb)
            zc, zd = min(zc, z_top), min(zd, z_top)
            for y, facing in ((y0 - proud, -1), (y1 + proud, 1)):
                kit.poly([(xa, y, za), (xb, y, zb), (xd, y, zd), (xc, y, zc)], (0, facing, 0), trim)
    xo = side * x_out
    xs = side * x_open
    if x_out > x_open + 1e-6:
        for y, facing in ((y0, -1), (y1, 1)):
            kit.poly([(xo, y, z_spring), (xs, y, z_spring), (xs, y, z_top), (xo, y, z_top)], (0, facing, 0), colour)
    kit.poly([(xo, y0, z_top), (0, y0, z_top), (0, y1, z_top), (xo, y1, z_top)], (0, 0, 1), colour)
    kit.poly([(xo, y0, z_spring), (xo, y1, z_spring), (xo, y1, z_top), (xo, y0, z_top)], (side, 0, 0), colour)
    kit.poly([(0, y0, z_crown), (0, y1, z_crown), (0, y1, z_top), (0, y0, z_top)], (-side, 0, 0), colour)


# --- battlements --------------------------------------------------------------


def merlon_spans(u0, u1, count):
    """`count` merlons evenly spaced from u0 to u1, with one at each end."""
    width = (u1 - u0) / (2 * count - 1)
    return [(u0 + 2 * k * width, u0 + (2 * k + 1) * width) for k in range(count)]


def merlons(kit, frame, spans, depth, z, height, colour="stone", cap=None):
    """Merlon blocks standing on a deck, `depth` in from the frame's face."""
    for ua, ub in spans:
        fbox(kit, frame, (ua, -depth, z), (ub, 0, z + height), colour, skip=("-z",), sides={"+z": cap} if cap else None)


# --- wall furniture -----------------------------------------------------------


def torch(kit, frame, u, z, v=0.0, flame="tangerine"):
    """A wall torch: a bracket with a chunky flame."""
    fbox(kit, frame, (u - 0.1, v, z), (u + 0.1, v + 0.42, z + 0.18), "doorBrown", skip=("-v",))
    p = frame.at
    base = [p(u - 0.24, v + 0.1, z + 0.18), p(u + 0.24, v + 0.1, z + 0.18), p(u + 0.24, v + 0.56, z + 0.18), p(u - 0.24, v + 0.56, z + 0.18)]
    apex = p(u, v + 0.33, z + 0.95)
    kit.convex([base] + [[base[k], base[(k + 1) % 4], apex] for k in range(4)], flame)


def shield(kit, frame, u, z_top, width, colour, second, v=0.07):
    """A heater shield with a cross, hung flat on a face."""
    h = width / 2
    outline = [(u - h, z_top), (u + h, z_top), (u + h, z_top - width * 0.55), (u, z_top - width * 1.15), (u - h, z_top - width * 0.55)]
    kit.poly([frame.at(a, v, z) for a, z in outline], frame.normal(), colour)
    kit.poly([frame.at(a, v - 0.03, z) for a, z in outline], frame.normal(-1), colour)
    fquad(kit, frame, u - width * 0.09, u + width * 0.09, z_top - width * 0.9, z_top - width * 0.08, v + 0.03, second)
    fquad(kit, frame, u - width * 0.4, u + width * 0.4, z_top - width * 0.42, z_top - width * 0.24, v + 0.03, second)


def batter(kit, frame, u0, u1, z0, z1, out, colour):
    """A sloped plinth: a wedge leaning against a face, `out` deep at the bottom."""
    p = frame.at
    n = frame.normal()
    kit.poly([p(u0, out, z0), p(u1, out, z0), p(u1, 0, z1), p(u0, 0, z1)], (n[0], n[1], 0.5), colour)
    t = frame.t
    kit.poly([p(u0, 0, z0), p(u0, out, z0), p(u0, 0, z1)], (-t[0], -t[1], 0), colour)
    kit.poly([p(u1, 0, z0), p(u1, out, z0), p(u1, 0, z1)], (t[0], t[1], 0), colour)


def buttress(kit, frame, u0, u1, z0, z_mid, z_top, out, colour, cap=None):
    """A buttress against a face: upright to z_mid, then sloping back to the wall at z_top."""
    p = frame.at
    n = frame.normal()
    t = frame.t
    kit.poly([p(u0, out, z0), p(u1, out, z0), p(u1, out, z_mid), p(u0, out, z_mid)], n, colour)
    kit.poly([p(u0, out, z_mid), p(u1, out, z_mid), p(u1, 0, z_top), p(u0, 0, z_top)], (n[0], n[1], 1), cap or colour)
    for u, facing in ((u0, -1), (u1, 1)):
        kit.poly([p(u, 0, z0), p(u, out, z0), p(u, out, z_mid), p(u, 0, z_top)], (t[0] * facing, t[1] * facing, 0), colour)


def pyramid(kit, cx, cy, hx, hy, z, rise, colour, under=None):
    """A four-sided pyramid roof on a rectangle."""
    base = [(cx - hx, cy - hy, z), (cx + hx, cy - hy, z), (cx + hx, cy + hy, z), (cx - hx, cy + hy, z)]
    apex = (cx, cy, z + rise)
    kit.convex([base] + [[base[k], base[(k + 1) % 4], apex] for k in range(4)], colour, {0: under} if under else None)


def beam(kit, a, b, width, depth, colour):
    """A straight timber from point a to point b (it must not be vertical): `width` across, `depth` deep."""
    ax, ay, az = a
    bx, by, bz = b
    dx, dy = bx - ax, by - ay
    length = math.hypot(dx, dy) or 1.0
    sx, sy = -dy / length * width / 2, dx / length * width / 2
    lower = [(ax - sx, ay - sy, az), (ax + sx, ay + sy, az), (bx + sx, by + sy, bz), (bx - sx, by - sy, bz)]
    kit.slab(lower, depth, colour)


def mirror_x(kit):
    """Flip everything in a kit left to right, keeping the faces pointing outwards."""
    kit.faces = [([Vector((-p.x, p.y, p.z)) for p in reversed(points)], colour) for points, colour in kit.faces]
