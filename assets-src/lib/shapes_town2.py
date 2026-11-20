"""Shapes shared by the second wave of town generators (church, school, fire station...).

Everything here adds faces to a `meshkit.Kit` or modules to a `Building`, in
the usual building frame: X along the frontage, the front faces -Y, Z is up.
"""

import math

from mathutils import Vector

from .meshkit import Kit
from .shapes_blocktown import flat, plaque, wall_y

WALL = 0.35
SIDES = ("front", "back", "left", "right")


def wall_colours(pal, wall=None, door=None):
    """The colour set `Kit.wall` wants, from a scheme."""
    return {
        "wall": wall or pal["wall"],
        "interior": "interiorCream",
        "trim": pal["trim"],
        "glass": "windowBlue",
        "shine": "windowShine",
        "door": door or pal["door"],
    }


def split(a, b, target):
    """Cut the span a..b into equal bays about `target` wide."""
    count = max(1, round((b - a) / target))
    step = (b - a) / count
    return [(a + i * step, a + (i + 1) * step) for i in range(count)]


def window(centre, z, width=1.5, height=1.5, sill=0.9):
    """A window opening for `Kit.wall`, `sill` above the floor at `z`."""
    return {"x0": centre - width / 2, "x1": centre + width / 2, "z0": z + sill, "z1": z + sill + height, "kind": "window"}


def door(centre, z, width=1.3, height=2.4):
    return {"x0": centre - width / 2, "x1": centre + width / 2, "z0": z, "z1": z + height, "kind": "door"}


def flatten(ids):
    """Every module id in a dict of lists, as `shell_storey` returns."""
    return [i for bucket in ids.values() for i in bucket]


def place(kit, part, matrix=None, offset=(0, 0, 0)):
    """Add another kit's faces, rotated by `matrix` (3x3) and then moved by `offset`."""
    offset = Vector(offset)
    for points, colour in part.faces:
        kit.faces.append(([(matrix @ p if matrix is not None else p) + offset for p in points], colour))


# --- arched doors and windows -------------------------------------------------


def arch_points(width, height, style="pointed", base=0.0):
    """(right, up) outline of an opening: "pointed", "round" or "square" headed."""
    w = width / 2
    if style == "square":
        return [(-w, base), (w, base), (w, base + height), (-w, base + height)]
    if style == "pointed":
        spring = max(height - width * 0.8, height * 0.3)
        return [(-w, base), (w, base), (w, base + spring), (0, base + height), (-w, base + spring)]
    spring = max(height - w, height * 0.3)
    r = height - spring
    k = math.sqrt(0.5)
    return [
        (-w, base),
        (w, base),
        (w, base + spring),
        (w * k, base + spring + r * k),
        (0, base + height),
        (-w * k, base + spring + r * k),
        (-w, base + spring),
    ]


def arched_panel(kit, centre, normal, width, height, style, trim, fill, shine=None, frame=0.16, depth=0.1, is_door=False):
    """An arched window or door standing proud of a wall.

    `centre` is the middle of its bottom edge on the wall face. A trim frame
    `depth` thick, the fill (glass or door colour) and, for windows, the shine.
    """
    outline = arch_points(width, height, style)
    if depth > 0:
        plaque(kit, centre, normal, outline, depth, trim)
    else:
        flat(kit, centre, normal, outline, trim, lift=0.03)
    base = 0.0 if is_door else frame
    inner_w = width - 2 * frame
    inner_h = height - frame - base
    flat(kit, centre, normal, arch_points(inner_w, inner_h, style, base), fill, lift=depth + 0.03)
    if shine:
        w = inner_w
        h = inner_h * 0.7
        flat(
            kit,
            centre,
            normal,
            [
                (-w * 0.32, base + h * 0.25),
                (-w * 0.1, base + h * 0.25),
                (w * 0.3, base + h * 0.8),
                (w * 0.08, base + h * 0.8),
            ],
            shine,
            lift=depth + 0.06,
        )


# --- rectangular shells ---------------------------------------------------------


def side_wall(kit, sign, x_out, y0, y1, z0, z1, openings, colours, wall=WALL):
    """A wall along Y on the left (sign -1) or right (+1): recessed openings, or a plain slab."""
    if openings:
        wall_y(kit, y0, y1, z0, z1, x_out, wall, -sign, openings, colours)
    else:
        lo, hi = sorted((x_out, x_out - sign * wall))
        kit.box((lo, y0, z0), (hi, y1, z1), colours["wall"], sides={"+x" if sign < 0 else "-x": colours["interior"]})


def shell_storey(
    add, bounds, z0, z1, storey, colours, material="plaster", below=None, openings=None, extra=None, wall=WALL, bays=None, skip=()
):
    """One storey of a rectangular building: a wall module per bay on each side.

    `bounds` is (x0, x1, y0, y1). The front and back walls run the full width
    and the side walls fit between them. `bays` maps a side to its list of
    (a, b) spans; `openings(side, index, a, b)` returns that bay's openings and
    `extra(kit, side, index, a, b)` may add more to it. `below` is the dict
    this returned for the storey underneath. Returns {side: [module ids]}.
    """
    x0, x1, y0, y1 = bounds
    bays = dict(bays or {})
    bays.setdefault("front", split(x0, x1, 4.0))
    bays.setdefault("back", split(x0, x1, 4.0))
    bays.setdefault("left", split(y0 + wall, y1 - wall, 5.0))
    bays.setdefault("right", split(y0 + wall, y1 - wall, 5.0))
    ids = {}
    for side in SIDES:
        ids[side] = []
        if side in skip:
            continue
        for i, (a, b) in enumerate(bays[side]):
            kit = Kit()
            holes = openings(side, i, a, b) if openings else []
            if side == "front":
                kit.wall(a, b, z0, z1, y0, wall, 1, holes, colours)
            elif side == "back":
                kit.wall(a, b, z0, z1, y1, wall, -1, holes, colours)
            else:
                sign = -1 if side == "left" else 1
                side_wall(kit, sign, x0 if sign < 0 else x1, a, b, z0, z1, holes, colours, wall)
            if extra:
                extra(kit, side, i, a, b)
            supports = (below[side][i],) if below and below.get(side) else ()
            ids[side].append(add(kit, "wall", material, storey, supports=supports))
    return ids


def floor_slab(add, bounds, z, storey, supports, wall=WALL, pieces=1, thickness=0.2):
    """The dolls'-house floor of an upper storey, in `pieces` along X."""
    x0, x1, y0, y1 = bounds
    out = []
    for a, b in split(x0 + wall, x1 - wall, (x1 - x0) / pieces):
        kit = Kit()
        kit.box((a, y0 + wall, z - thickness), (b, y1 - wall, z), "interiorCream")
        out.append(add(kit, "floor", "wood", storey, supports=supports))
    return out


# --- roofs -------------------------------------------------------------------------


def roof_gabled(
    add,
    bounds,
    eaves,
    rise,
    roof,
    storey,
    front,
    back,
    ends,
    wall_colour,
    material="plaster",
    overhang=0.45,
    verge=0.35,
    thickness=0.3,
    wall=WALL,
    gable_extra=None,
):
    """A pitched roof with its ridge along X, and the two gable walls under it.

    `front` and `back` are lists of ((a, b), supporting module id): a roof slab
    each. `ends` is {-1: [ids], 1: [ids]}, the side walls under the gables.
    Returns {"front": [...], "back": [...], "gable": {sign: id}}.
    """
    x0, x1, y0, y1 = bounds
    mid = (y0 + y1) / 2
    slope = rise / ((y1 - y0) / 2)
    ridge = eaves + rise
    eave_z = eaves - slope * overhang
    out = {"front": [], "back": [], "gable": {}}
    for key, pieces, eave_y in (("front", front, y0 - overhang), ("back", back, y1 + overhang)):
        for i, ((a, b), holder) in enumerate(pieces):
            a = a - verge if i == 0 else a
            b = b + verge if i == len(pieces) - 1 else b
            kit = Kit()
            kit.slab([(a, eave_y, eave_z), (b, eave_y, eave_z), (b, mid, ridge), (a, mid, ridge)], thickness, roof)
            out[key].append(add(kit, "roof", "tile", storey, supports=(holder,), collider="hull"))
    for sign in (-1, 1):
        xa, xb = sorted((x0 if sign < 0 else x1, (x0 + wall) if sign < 0 else (x1 - wall)))
        kit = Kit()
        kit.extrude_x([(y0, eaves), (y1, eaves), (mid, ridge)], xa, xb, wall_colour)
        if gable_extra:
            gable_extra(kit, sign)
        out["gable"][sign] = add(kit, "wall", material, storey, supports=ends[sign], collider="hull")
    return out


def roof_hipped(add, bounds, eaves, rise, roof, storey, front, back, ends, overhang=0.45, thickness=0.3):
    """A hipped roof with its ridge along X. The building must be wider than it is deep.

    Arguments as `roof_gabled`. Returns {"front": [...], "back": [...], "end": {sign: id}}.
    """
    x0, x1, y0, y1 = bounds
    mid = (y0 + y1) / 2
    half = (y1 - y0) / 2
    slope = rise / half
    ridge = eaves + rise
    eave_z = eaves - slope * overhang
    ex0, ex1 = x0 - overhang, x1 + overhang
    rx0, rx1 = x0 + half, x1 - half
    out = {"front": [], "back": [], "end": {}}
    for key, pieces, eave_y in (("front", front, y0 - overhang), ("back", back, y1 + overhang)):

        def top(x):
            if x < rx0:
                t = (x - ex0) / (rx0 - ex0)
            elif x > rx1:
                t = (ex1 - x) / (ex1 - rx1)
            else:
                t = 1.0
            return (x, eave_y + t * (mid - eave_y), eave_z + t * (ridge - eave_z))

        for i, ((a, b), holder) in enumerate(pieces):
            a = ex0 if i == 0 else a
            b = ex1 if i == len(pieces) - 1 else b
            points = [(a, eave_y, eave_z), (b, eave_y, eave_z), top(b)]
            if a < rx1 < b:
                points.append(top(rx1))
            if a < rx0 < b:
                points.append(top(rx0))
            points.append(top(a))
            clean = []
            for p in points:
                if not any((Vector(p) - Vector(q)).length < 1e-4 for q in clean):
                    clean.append(p)
            kit = Kit()
            kit.slab(clean, thickness, roof)
            out[key].append(add(kit, "roof", "tile", storey, supports=(holder,), collider="hull"))
    for sign, ex, apex in ((-1, ex0, rx0), (1, ex1, rx1)):
        kit = Kit()
        kit.slab([(ex, y0 - overhang, eave_z), (ex, y1 + overhang, eave_z), (apex, mid, ridge)], thickness, roof)
        out["end"][sign] = add(kit, "roof", "tile", storey, supports=ends[sign], collider="hull")
    return out


def cross_gable(kit, mid, width, base, height, face, back, wall_colour, roof, verge=0.3, eave=0.3, thickness=0.26, depth=WALL):
    """A little gable facing the street: a triangle of wall and its own two roof slopes.

    The triangle's face is at y = `face` (it is `depth` thick) and the roof runs back to y = `back`.
    """
    half = width / 2
    slope = height / half
    kit.extrude_y([(mid - half, base), (mid + half, base), (mid, base + height)], face, face + depth, wall_colour)
    for side in (-1, 1):
        x_low = mid + side * (half + eave)
        z_low = base - slope * eave
        kit.extrude_y(
            [(x_low, z_low), (mid, base + height), (mid, base + height + thickness), (x_low, z_low + thickness)],
            face - verge,
            back,
            roof,
        )


# --- round things ---------------------------------------------------------------------


def ngon(cx, cy, z, radius, sides=8, phase=None):
    """Points of a regular polygon in the XY plane. By default a flat faces -Y."""
    if phase is None:
        phase = -math.pi / 2 + math.pi / sides
    step = 2 * math.pi / sides
    return [(cx + radius * math.cos(phase + i * step), cy + radius * math.sin(phase + i * step), z) for i in range(sides)]


def ring_deck(kit, cx, cy, z0, z1, r_in, r_out, facets, colour, sides=8, under=None, phase=None, inside=None):
    """Part of a flat ring (a gallery deck, a basin rim): top, bottom and outside faces.

    `inside` is the colour of the inner face, if it shows, and `under="none"`
    leaves the bottom off for decks nobody can see beneath. Pass `phase=pi/sides`
    to number the facets the way `shapes_blocktown.shell` does.
    """
    lo_in, lo_out = ngon(cx, cy, z0, r_in, sides, phase), ngon(cx, cy, z0, r_out, sides, phase)
    hi_in, hi_out = ngon(cx, cy, z1, r_in, sides, phase), ngon(cx, cy, z1, r_out, sides, phase)
    for i in facets:
        j = (i + 1) % sides
        out = Vector(lo_out[i]) + Vector(lo_out[j]) - Vector((cx, cy, z0)) * 2
        out.z = 0
        kit.poly([hi_in[i], hi_in[j], hi_out[j], hi_out[i]], (0, 0, 1), colour)
        if under != "none":
            kit.poly([lo_in[i], lo_in[j], lo_out[j], lo_out[i]], (0, 0, -1), under or colour)
        kit.poly([lo_out[i], lo_out[j], hi_out[j], hi_out[i]], out, colour)
        if inside:
            kit.poly([lo_in[i], lo_in[j], hi_in[j], hi_in[i]], -out, inside)


def flag(kit, x, y, z0, height, pole, cloth, radius=0.16, size=(1.7, 1.1), facing=1):
    """A flagpole with a ball on top and a flag flying towards +X (or -X)."""
    sides = 6
    lower = ngon(x, y, z0, radius, sides)
    upper = ngon(x, y, z0 + height, radius, sides)
    for i in range(sides):
        j = (i + 1) % sides
        out = Vector(lower[i]) + Vector(lower[j]) - Vector((x, y, z0)) * 2
        kit.poly([lower[i], lower[j], upper[j], upper[i]], out, pole)
    top = z0 + height
    kit.poly(upper, (0, 0, 1), pole)
    kit.convex(
        [
            [(x - 0.26, y, top + 0.26), (x, y - 0.26, top + 0.26), (x, y, top)],
            [(x, y - 0.26, top + 0.26), (x + 0.26, y, top + 0.26), (x, y, top)],
            [(x + 0.26, y, top + 0.26), (x, y + 0.26, top + 0.26), (x, y, top)],
            [(x, y + 0.26, top + 0.26), (x - 0.26, y, top + 0.26), (x, y, top)],
            [(x - 0.26, y, top + 0.26), (x, y - 0.26, top + 0.26), (x, y, top + 0.52)],
            [(x, y - 0.26, top + 0.26), (x + 0.26, y, top + 0.26), (x, y, top + 0.52)],
            [(x + 0.26, y, top + 0.26), (x, y + 0.26, top + 0.26), (x, y, top + 0.52)],
            [(x, y + 0.26, top + 0.26), (x - 0.26, y, top + 0.26), (x, y, top + 0.52)],
        ],
        "sunny",
    )
    xa, xb = sorted((x + facing * radius, x + facing * (radius + size[0])))
    kit.box((xa, y - 0.05, top - 0.15 - size[1]), (xb, y + 0.05, top - 0.15), cloth)
