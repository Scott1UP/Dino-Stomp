"""Shapes for the wizard-school castle generators.

Tall pointed (lancet) windows, steep spires with a kick at the eaves, gold
finials, pinnacles, floor bands with cream insides, chunky upright rings (the
hoop posts), striped cloth panels, a hanging lantern, and a helper that moves
everything in a kit (for building a piece at the origin and then placing it).

Like the other shape libraries, everything goes through `Kit.convex` or
`Kit.poly`, so faces point outwards. Panels laid on a wall use the
`shapes_parkcastle.Frame`s: u runs along the face, v points out of it, z is up.
"""

import math

from mathutils import Vector

from .shapes_parkcastle import corner_deg, fbox, fquad, fshine, polar, ring

# The castle reads as grey stone under dark slate: near-black navy most often,
# then slate blue. Windows mostly glow warm (lit), a few stay dark.
SLATES = ["tyre", "tyre", "windowBlue"]
SPIRES = SLATES
LIT = "sunny"
BRIGHTS = ["tomato", "sunny", "cobalt", "bubblegum"]
GOLDS = ["sunny", "starGold"]


def pane(rng, dark_share=0.2):
    """(glass, shine) for one window: mostly lit and warm, sometimes dark with a shine."""
    if rng.random() < dark_share:
        return "windowBlue", "windowShine"
    return LIT, None


# --- windows and doors ----------------------------------------------------------


def lancet_outline(u, base, width, height, sill=True, rim=0.0):
    """(u, z) outline of a tall pointed window, widened by `rim` all round.

    Without a sill the outline starts at `base` (the lower part of a window
    split between two storeys is drawn by `window_shaft`).
    """
    w = width / 2 + rim
    z0 = base - (rim if sill else 0.0)
    top = base + height + rim * 1.4
    spring = top - width * 0.95 - rim
    spring = max(spring, z0 + 0.1)
    return [(u - w, z0), (u + w, z0), (u + w, spring), (u, top), (u - w, spring)]


def lancet(kit, frame, u, base, width, height, v=0.04, surround="trimWhite", glass="windowBlue", shine="windowShine", sill=True, rim=0.15, facing=1):
    """A tall narrow pointed window laid on a face: a pale surround, dark glass and its shine.

    8 triangles (5 without the surround).
    """
    p = frame.at
    n = frame.normal(facing)
    if surround:
        kit.poly([p(a, v, z) for a, z in lancet_outline(u, base, width, height, sill, rim)], n, surround)
    kit.poly([p(a, v + 0.03, z) for a, z in lancet_outline(u, base, width, height, sill)], n, glass)
    if shine:
        fshine(kit, frame, u - width / 2, u + width / 2, base, base + height * 0.75, v + 0.06, shine)


def window_shaft(kit, frame, u, z0, z1, width, v=0.04, surround="trimWhite", glass="windowBlue", rim=0.15, sill=True):
    """The straight lower part of a tall window that carries on into the storey above."""
    hw = width / 2
    if surround:
        fquad(kit, frame, u - hw - rim, u + hw + rim, z0 - (rim if sill else 0.0), z1, v, surround)
    fquad(kit, frame, u - hw, u + hw, z0, z1, v + 0.03, glass)


def pointed_door(kit, frame, u, width, height, colour, v=0.04, surround="trimWhite", rim=0.22, z0=0.0):
    """A pointed-arch door with a pale surround and a dark centre line."""
    p = frame.at
    n = frame.normal()
    kit.poly([p(a, v, z) for a, z in lancet_outline(u, z0, width, height, False, rim)], n, surround)
    kit.poly([p(a, v + 0.03, z) for a, z in lancet_outline(u, z0, width, height, False)], n, colour)
    fquad(kit, frame, u - 0.05, u + 0.05, z0, z0 + height - width * 0.45, v + 0.06, "tyre")


def rose_window(kit, frame, u, z, radius, v=0.04, trim="trimWhite", glass="windowBlue", second=None, sides=8):
    """A round window: a pale ring, dark glass, a coloured centre and a shine."""
    p = frame.at
    n = frame.normal()

    def disc(r, lift, colour, phase=0.0):
        points = []
        for k in range(sides):
            a = math.pi * 2 * k / sides + math.pi / sides + phase
            points.append(p(u + r * math.cos(a), lift, z + r * math.sin(a)))
        kit.poly(points, n, colour)

    disc(radius, v, trim)
    disc(radius * 0.78, v + 0.03, glass)
    if second:
        disc(radius * 0.3, v + 0.06, second)
    r = radius * 0.78
    kit.poly(
        [p(u - 0.55 * r, v + 0.07, z + 0.05 * r), p(u - 0.3 * r, v + 0.07, z + 0.05 * r), p(u + 0.2 * r, v + 0.07, z + 0.62 * r), p(u - 0.05 * r, v + 0.07, z + 0.62 * r)],
        n,
        "windowShine",
    )


# --- spires, finials and pinnacles ------------------------------------------------


def _ring_faces(lower, upper, apex_low=None, apex_high=None):
    faces = []
    count = len(lower) if lower else len(upper)
    for i in range(count):
        j = (i + 1) % count
        if upper is None:
            faces.append([lower[i], lower[j], apex_high])
        elif lower is None:
            faces.append([apex_low, upper[j], upper[i]])
        else:
            faces.append([lower[i], lower[j], upper[j], upper[i]])
    return faces


def drum(kit, r0, r1, z0, z1, colour, sides=8, cx=0.0, cy=0.0, top=None, bottom=None, cap_top=True, cap_bottom=True):
    """A prism or frustum with its end caps coloured separately (cream insides for floors)."""
    lower = ring(r0, z0, sides, cx, cy)
    upper = ring(r1, z1, sides, cx, cy)
    faces = _ring_faces(lower, upper)
    colours = {}
    if cap_bottom:
        faces.append(lower)
        if bottom:
            colours[len(faces) - 1] = bottom
    if cap_top:
        faces.append(upper)
        if top:
            colours[len(faces) - 1] = top
    kit.convex(faces, colour, colours)


def spire(kit, r, z0, z1, colour, sides=8, cx=0.0, cy=0.0, kick=0.16, under=None, r_top=0.0):
    """A steep pointed spire with a little kick out at the eaves, like a witch's hat.

    It runs from z0 to z1 (or stops at radius `r_top` for the lower half of a
    spire split in two). One convex solid, so it makes one good hull.
    """
    rise = z1 - z0
    if kick > 0:
        k_z = z0 + rise * kick
        k_r = r * 0.74
    else:
        k_z, k_r = z0, r
    full = z1
    base = ring(r, z0, sides, cx, cy)
    faces = [base]
    colours = {0: under} if under else {}
    if kick > 0:
        knee = ring(k_r, k_z, sides, cx, cy)
        faces += _ring_faces(base, knee)
    else:
        knee = base
    if r_top > 1e-6:
        top = ring(r_top, full, sides, cx, cy)
        faces += _ring_faces(knee, top)
        faces.append(top)
        colours[len(faces) - 1] = under or colour
    else:
        faces += _ring_faces(knee, None, apex_high=(cx, cy, z1))
    kit.convex(faces, colour, colours)


def cone_part(kit, r0, r1, z0, z1, colour, sides=8, cx=0.0, cy=0.0, under=None):
    """A piece of a spire between two heights: r1 = 0 brings it to a point."""
    lower = ring(r0, z0, sides, cx, cy)
    if r1 > 1e-6:
        upper = ring(r1, z1, sides, cx, cy)
        faces = _ring_faces(lower, upper) + [lower, upper]
        colours = {len(faces) - 2: under or colour, len(faces) - 1: under or colour}
    else:
        faces = _ring_faces(lower, None, apex_high=(cx, cy, z1)) + [lower]
        colours = {len(faces) - 1: under or colour}
    kit.convex(faces, colour, colours)


def finial(kit, x, y, z, size=0.9, colour="starGold", stem=True):
    """A gold finial: a short stem and a diamond. 8-16 triangles."""
    if stem:
        s = size * 0.09
        kit.box((x - s, y - s, z), (x + s, y + s, z + size * 0.45), colour, skip=("-z", "+z"))
    zc = z + size * 0.45 + size * 0.3
    r = size * 0.32
    mid = [(x + r * math.cos(a), y + r * math.sin(a), zc) for a in (0, math.pi / 2, math.pi, 1.5 * math.pi)]
    low = (x, y, zc - size * 0.3)
    high = (x, y, zc + size * 0.55)
    faces = []
    for i in range(4):
        j = (i + 1) % 4
        faces.append([mid[i], mid[j], high])
        faces.append([mid[j], mid[i], low])
    kit.convex(faces, colour)


def pinnacle(kit, x, y, z0, half, shaft, rise, colour="stone", tip="cobalt", knob="starGold"):
    """A small square pinnacle: a shaft, a steep pyramid and a gold knob. About 20 triangles."""
    kit.box((x - half, y - half, z0), (x + half, y + half, z0 + shaft), colour, skip=("-z", "+z"))
    zb = z0 + shaft
    h = half + 0.08
    base = [(x - h, y - h, zb), (x + h, y - h, zb), (x + h, y + h, zb), (x - h, y + h, zb)]
    apex = (x, y, zb + rise)
    kit.convex([base] + [[base[k], base[(k + 1) % 4], apex] for k in range(4)], tip)
    if knob:
        finial(kit, x, y, zb + rise - 0.15, size=0.55, colour=knob, stem=False)


# --- floors and bands -------------------------------------------------------------


def band_ring(kit, r, z0, z1, colour="trimWhite", sides=8, cx=0.0, cy=0.0, inside="interiorCream"):
    """A floor slab that pokes out of a round tower as a white band."""
    drum(kit, r, r, z0, z1, colour, sides, cx, cy, top=inside, bottom=inside)


def band_box(kit, x0, y0, x1, y1, z0, z1, colour="trimWhite", inside="interiorCream"):
    """A floor slab that pokes out of a square building as a white band."""
    kit.box((x0, y0, z0), (x1, y1, z1), colour, sides={"+z": inside, "-z": inside})


def corbel_square(kit, half_in, half_out, z0, z1, colour="stone", cx=0.0, cy=0.0):
    """A sloping corbel course stepping a square tower out from half_in to half_out."""
    corners = ((-1, -1), (1, -1), (1, 1), (-1, 1))
    lower = [(cx + a * half_in, cy + b * half_in, z0) for a, b in corners]
    upper = [(cx + a * half_out, cy + b * half_out, z1) for a, b in corners]
    faces = [lower, upper] + [[lower[i], lower[(i + 1) % 4], upper[(i + 1) % 4], upper[i]] for i in range(4)]
    kit.convex(faces, colour)


# --- moving pieces about ------------------------------------------------------------


def shift(kit, dx=0.0, dy=0.0, dz=0.0, start=0):
    """Move the faces of a kit (from face index `start` on) by (dx, dy, dz)."""
    d = Vector((dx, dy, dz))
    kit.faces[start:] = [([p + d for p in points], colour) for points, colour in kit.faces[start:]]


def rotate_z(kit, deg, start=0):
    """Turn the faces of a kit about the Z axis through the origin."""
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    kit.faces[start:] = [([Vector((p.x * c - p.y * s, p.x * s + p.y * c, p.z)) for p in points], colour) for points, colour in kit.faces[start:]]


# --- sport and fairground bits ------------------------------------------------------


def upright_ring(kit, cx, cy, cz, radius, thick, colour, sides=8, depth=None, stripes=None):
    """A chunky open ring standing upright in the XZ plane (facing -Y), centred at (cx, cy, cz).

    `radius` is to the middle of the rim; the rim is `thick` across and `depth`
    deep. A flat segment sits at the bottom. 8 triangles a segment.
    """
    depth = depth or thick
    r_out = radius + thick / 2
    r_in = radius - thick / 2
    y0, y1 = cy - depth / 2, cy + depth / 2

    def at(r, k, y):
        a = -math.pi / 2 + (k - 0.5) * 2 * math.pi / sides
        return Vector((cx + r * math.cos(a), y, cz + r * math.sin(a)))

    for k in range(sides):
        colour_k = stripes[k % len(stripes)] if stripes else colour
        a = -math.pi / 2 + k * 2 * math.pi / sides
        out = Vector((math.cos(a), 0, math.sin(a)))
        o0, o1 = at(r_out, k, y0), at(r_out, k + 1, y0)
        o2, o3 = at(r_out, k, y1), at(r_out, k + 1, y1)
        i0, i1 = at(r_in, k, y0), at(r_in, k + 1, y0)
        i2, i3 = at(r_in, k, y1), at(r_in, k + 1, y1)
        kit.poly([o0, o1, o3, o2], out, colour_k)
        kit.poly([i0, i1, i3, i2], -out, colour_k)
        kit.poly([o0, o1, i1, i0], (0, -1, 0), colour_k)
        kit.poly([o2, o3, i3, i2], (0, 1, 0), colour_k)


def stripes(kit, frame, u0, u1, z0, z1, v, colours, count, back=True, point=0.0):
    """Upright cloth stripes hung on a frame, cycling `colours`; `back` draws the far side too.

    `point` drops the bottom of every stripe into a shallow V (bunting edge).
    """
    width = (u1 - u0) / count
    p = frame.at
    for k in range(count):
        ua, ub = u0 + k * width, u0 + (k + 1) * width
        colour = colours[k % len(colours)]
        outline = [(ua, z0), (ub, z0), (ub, z1), (ua, z1)]
        if point > 0:
            outline = [(ua, z0), ((ua + ub) / 2, z0 - point), (ub, z0), (ub, z1), (ua, z1)]
        kit.poly([p(a, v, z) for a, z in outline], frame.normal(), colour)
        if back:
            kit.poly([p(a, v - 0.03, z) for a, z in outline], frame.normal(-1), colour)


def lantern(kit, x, y, z_top, chain, colour="tyre", glow="sunny", size=0.8):
    """A lantern hanging on a chain from (x, y, z_top). Its bottom is at z_top - chain - size * 1.3."""
    c = 0.06
    kit.box((x - c, y - c, z_top - chain), (x + c, y + c, z_top), colour, skip=("-z", "+z"))
    zt = z_top - chain
    h = size / 2
    roof = [(x - h - 0.1, y - h - 0.1, zt - 0.35), (x + h + 0.1, y - h - 0.1, zt - 0.35), (x + h + 0.1, y + h + 0.1, zt - 0.35), (x - h - 0.1, y + h + 0.1, zt - 0.35)]
    kit.convex([roof] + [[roof[k], roof[(k + 1) % 4], (x, y, zt)] for k in range(4)], colour)
    zb = zt - 0.35 - size
    kit.box((x - h, y - h, zb), (x + h, y + h, zt - 0.35), glow, skip=("+z",))
    kit.box((x - h - 0.08, y - h - 0.08, zb - 0.18), (x + h + 0.08, y + h + 0.08, zb), colour, skip=("+z",))


def pole_ngon(kit, x, y, z0, z1, radius, colour, sides=8, top=True, stripes_list=None):
    """An upright n-gon pole."""
    lower = ring(radius, z0, sides, x, y)
    upper = ring(radius, z1, sides, x, y)
    faces = _ring_faces(lower, upper)
    colours = {}
    if stripes_list:
        for k in range(sides):
            colours[k] = stripes_list[k % len(stripes_list)]
    if top:
        faces.append(upper)
    kit.convex(faces, colour, colours)


__all__ = [
    "SPIRES",
    "BRIGHTS",
    "GOLDS",
    "lancet",
    "lancet_outline",
    "window_shaft",
    "pointed_door",
    "rose_window",
    "drum",
    "spire",
    "cone_part",
    "finial",
    "pinnacle",
    "band_ring",
    "band_box",
    "corbel_square",
    "shift",
    "rotate_z",
    "upright_ring",
    "stripes",
    "lantern",
    "pole_ngon",
    "corner_deg",
    "polar",
    "fbox",
]
