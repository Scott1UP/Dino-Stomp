"""Giant toy blocks generator.

A stack of giant toy building blocks: 1.6 m cubes, 3.2 m bricks, cylinders,
triangles and one arch, each block its own module in its own bright colour,
some with a big letter or shape painted on the front and back. In the game
every block is a loose physics body from the start, so the stack tumbles.

The seed picks the arrangement (pyramid, tower, wall, staircase or arch) and
then varies it. Blocks sit on a 0.8 m grid with flat faces touching exactly:
no overlaps and no gaps, and every block's centre is over what holds it up
(the layout is checked as it is built).

    blender --background --factory-startup --python assets-src/props/toy_blocks.py
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import prism  # noqa: E402

TYPE = "toy_blocks"
KIND = "block"
TRIANGLE_BUDGET = 300
BLOCK_BUDGET = 30  # triangles in any one block

U = 1.6  # a cube's edge
HALF = U / 2
PROUD = 0.02  # decals sit this far off the face
ARRANGEMENTS = ("pyramid", "tower", "wall", "staircase", "arch")
COLOURS = ("tomato", "sunny", "cobalt", "tangerine", "bubblegum", "leaf")
WIDTH = {"cube": U, "brick": 2 * U, "cyl": U, "tri1": U, "tri2": 2 * U, "arch": 3 * U}

# Painted shapes: rectangles (x0, z0, x1, z1) in a -1..1 square, or a polygon.
GLYPHS = {
    "T": [(-0.8, 0.35, 0.8, 0.8), (-0.22, -0.8, 0.22, 0.35)],
    "L": [(-0.6, -0.8, -0.15, 0.8), (-0.15, -0.8, 0.65, -0.35)],
    "I": [(-0.22, -0.8, 0.22, 0.8)],
    "equals": [(-0.75, 0.15, 0.75, 0.6), (-0.75, -0.6, 0.75, -0.15)],
    "square": [(-0.65, -0.65, 0.65, 0.65)],
    "diamond": [[(0, -0.85), (0.85, 0), (0, 0.85), (-0.85, 0)]],
    "triangle": [[(-0.8, -0.7), (0.8, -0.7), (0, 0.8)]],
    "circle": [[(0.8 * math.cos(i * math.pi / 3), 0.8 * math.sin(i * math.pi / 3)) for i in range(6)]],
}
GLYPH_NAMES = sorted(GLYPHS)


def _layout(arrangement, rng):
    """The blocks as (shape, x centre, row). Row 0 stands on the ground."""
    blocks = []

    def solid():
        return "cyl" if rng.random() < 0.25 else "cube"

    if arrangement == "pyramid":
        base = rng.choice([3, 4, 4])
        capped = base == 4 and rng.random() < 0.4
        rows = 2 if capped else base - 1
        for r in range(rows):
            n = base - r
            for i in range(n):
                blocks.append((solid(), (i - (n - 1) / 2) * U, r))
        if capped:
            blocks.append(("tri2", 0.0, 2))
        else:
            blocks.append((rng.choice(["tri1", "tri1", "cyl"]), 0.0, base - 1))
    elif arrangement == "tower":
        storeys = rng.choice([2, 3])
        for s in range(storeys):
            pair = solid()
            blocks.append((pair, -HALF, 2 * s))
            blocks.append((pair, HALF, 2 * s))
            blocks.append(("brick", 0.0, 2 * s + 1))
        if rng.random() < 0.5:
            blocks.append(("tri2", 0.0, 2 * storeys))
        else:
            blocks.append((solid(), 0.0, 2 * storeys))
            blocks.append(("tri1", 0.0, 2 * storeys + 1))
    elif arrangement == "wall":
        rows = rng.choice([3, 4])
        for r in range(rows):
            if r % 2 == 0:
                blocks += [("brick", -U, r), ("brick", U, r)]
            else:
                blocks += [("cube", -1.5 * U, r), ("brick", 0.0, r), ("cube", 1.5 * U, r)]
        toppers = rng.choice(["both", "both", "ends", "middle"])
        if toppers in ("both", "ends"):
            blocks += [("cyl", -1.5 * U, rows), ("cyl", 1.5 * U, rows)]
        if toppers in ("both", "middle"):
            blocks.append(("tri2", 0.0, rows))
    elif arrangement == "staircase":
        way = rng.choice([-1, 1])
        if rng.random() < 0.5:
            for column in range(4):
                for r in range(column + 1):
                    top = r == column
                    blocks.append(("cyl" if top and rng.random() < 0.4 else "cube", (column - 1.5) * U * way, r))
        else:
            blocks += [("brick", -U * way, 0), ("brick", U * way, 0)]
            blocks += [("cube", -0.5 * U * way, 1), ("brick", U * way, 1)]
            blocks += [("brick", U * way, 2)]
            blocks += [(solid(), 1.5 * U * way, 3)]
            blocks += [("tri1", 1.5 * U * way, 4)]
    else:  # arch
        height = rng.choice([2, 3])
        for r in range(height):
            shape = solid()
            blocks += [(shape, -U, r), (shape, U, r)]
        blocks.append(("arch", 0.0, height))
        blocks.append(("brick", 0.0, height + 1))
        blocks.append((rng.choice(["tri2", "tri1", "cyl"]), 0.0, height + 2))
        if rng.random() < 0.6:
            blocks += [("cube", -2 * U, 0), ("cube", 2 * U, 0)]
    return sorted(blocks, key=lambda b: b[2])


def _feet(shape, x):
    """Where a block touches whatever is under it: a list of (x0, x1)."""
    w = WIDTH[shape] / 2
    if shape == "arch":
        return [(x - w, x - w + U), (x + w - U, x + w)]
    return [(x - w, x + w)]


def _supports(blocks, index):
    """The blocks under block `index`, after checking that it can stand on them."""
    shape, x, row = blocks[index]
    if row == 0:
        return []
    under = []
    lo, hi = math.inf, -math.inf
    for other, (o_shape, o_x, o_row) in enumerate(blocks):
        if o_row != row - 1:
            continue
        o_w = WIDTH[o_shape] / 2
        for f0, f1 in _feet(shape, x):
            a, b = max(f0, o_x - o_w), min(f1, o_x + o_w)
            if b - a > 1e-6:
                if o_shape.startswith("tri"):
                    raise ValueError(f"{shape} cannot stand on a triangle")
                if other not in under:
                    under.append(other)
                lo, hi = min(lo, a), max(hi, b)
    if not under or not lo - 1e-6 <= x <= hi + 1e-6:
        raise ValueError(f"{shape} at x={x} row={row} is not held up")
    return under


def _glyph(kit, name, x, z, size, colour):
    """Paint a glyph on the front and back faces, centred on (x, z)."""
    for facing in (-1, 1):
        for n, piece in enumerate(GLYPHS[name]):
            y = facing * (HALF + PROUD + 0.004 * n)
            if isinstance(piece, tuple):
                x0, z0, x1, z1 = piece
                piece = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
            # Mirrored on the back, so letters read the right way round from both sides.
            kit.poly([(x - facing * px * size, y, z + pz * size) for px, pz in piece], (0, facing, 0), colour)


def _block(kit, shape, x, z0, colour):
    w = WIDTH[shape] / 2
    z1 = z0 + U
    if shape in ("cube", "brick"):
        kit.box((x - w, -HALF, z0), (x + w, HALF, z1), colour)
    elif shape == "cyl":
        # Eight sides, with flats touching the faces of the cube it fills.
        prism(kit, (x, 0), z0, z1, HALF / math.cos(math.pi / 8), HALF / math.cos(math.pi / 8), 8, colour)
    elif shape in ("tri1", "tri2"):
        kit.extrude_y([(x - w, z0), (x + w, z0), (x, z1)], -HALF, HALF, colour)
    else:  # arch: two legs and a lintel, with a tapering hole between
        zc = z0 + HALF
        xa, xb = x - w + U, x + w - U
        hole = [(xa, z0), (x - 0.4, zc), (x + 0.4, zc), (xb, z0)]
        for y, facing in ((-HALF, -1), (HALF, 1)):
            kit.poly([(x - w, y, z0), (xa, y, z0), (x - 0.4, y, zc), (x - w, y, zc)], (0, facing, 0), colour)
            kit.poly([(xb, y, z0), (x + w, y, z0), (x + w, y, zc), (x + 0.4, y, zc)], (0, facing, 0), colour)
            kit.poly([(x - w, y, zc), (x + w, y, zc), (x + w, y, z1), (x - w, y, z1)], (0, facing, 0), colour)
        for sx in (-1, 1):
            kit.poly([(x + sx * w, -HALF, z0), (x + sx * w, HALF, z0), (x + sx * w, HALF, z1), (x + sx * w, -HALF, z1)], (sx, 0, 0), colour)
        kit.poly([(x - w, -HALF, z1), (x + w, -HALF, z1), (x + w, HALF, z1), (x - w, HALF, z1)], (0, 0, 1), colour)
        kit.poly([(x - w, -HALF, z0), (xa, -HALF, z0), (xa, HALF, z0), (x - w, HALF, z0)], (0, 0, -1), colour)
        kit.poly([(xb, -HALF, z0), (x + w, -HALF, z0), (x + w, HALF, z0), (xb, HALF, z0)], (0, 0, -1), colour)
        for i in range(3):
            (ax, az), (bx, bz) = hole[i], hole[i + 1]
            hint = (x - (ax + bx) / 2, 0, z0 + 0.2 - (az + bz) / 2)
            kit.poly([(ax, -HALF, az), (bx, -HALF, bz), (bx, HALF, bz), (ax, HALF, az)], hint, colour)


def build(building_id, seed, scheme=None, collection=None):
    """Build one stack of blocks. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    arrangement = ARRANGEMENTS[seed % len(ARRANGEMENTS)]  # cycled, so neighbouring seeds always differ
    blocks = _layout(arrangement, rng)
    colours = list(COLOURS)
    rng.shuffle(colours)
    step = rng.choice([1, 5])  # walk the colour list forwards or backwards

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    ids = []
    for index, (shape, x, row) in enumerate(blocks):
        colour = colours[(index * step) % len(colours)]
        under = _supports(blocks, index)
        kit = Kit()
        _block(kit, shape, x, row * U, colour)
        if shape in ("cube", "brick") and rng.random() < 0.7:
            paint = "trimWhite" if colour != "sunny" else "tomato"
            _glyph(kit, rng.choice(GLYPH_NAMES), x, row * U + HALF, 0.62, paint)
        ids.append(
            building.add(
                kit,
                "detail",
                "wood",
                row,
                supports=[ids[i] for i in under],
                collider="box" if shape in ("cube", "brick") else "hull",
            )
        )

    empty, stats = building.finish(look=f"{arrangement} blocks={len(blocks)}")
    if stats["largestModule"] > BLOCK_BUDGET:
        stats["look"] += f" OVER block budget ({BLOCK_BUDGET})"
    return empty, stats


def report(stats):
    flags = []
    if stats["triangles"] > TRIANGLE_BUDGET:
        flags.append(f"OVER budget ({TRIANGLE_BUDGET})")
    if stats["largestModule"] > BLOCK_BUDGET:
        flags.append(f"OVER block budget ({BLOCK_BUDGET})")
    if not 6 <= stats["modules"] <= 14:
        flags.append("block count outside 6-14")
    print(
        f"[{stats['type']}] {stats['id']} seed={stats['seed']} {stats['look']} "
        f"modules={stats['modules']} triangles={stats['triangles']} largest={stats['largestModule']} "
        + " ".join(flags)
    )


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(13, 12))


if __name__ == "__main__":
    previews()
