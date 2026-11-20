"""Draws each level's playmat ground from its layout.

Roads, pavements, crossings, paths, grass and water are drawn in flat, soft
colours with rounded corners and a faint stitched edge, like a real playmat.
Because it is drawn from the same layout that places the buildings, the roads
always line up with them.

Runs inside Blender (it only needs numpy and Blender's image API).
"""

import math
import os

import bpy
import numpy as np

SIZE_PX = 2048

GROUND = "#EADBB8"
GRASS = "#A9C48E"
GRASS_DARK = "#9BBB80"
ROAD = "#B9BEC6"
PAVEMENT = "#F3E9D2"
MARKING = "#FFFDF6"
PATH = "#E3CFA0"
WATER = "#8FD3E8"
STITCH = "#CDB98C"


def _rgb(value):
    value = value.lstrip("#")
    return np.array([int(value[i : i + 2], 16) / 255 for i in (0, 2, 4)], dtype=np.float32)


class Mat:
    def __init__(self, size_m):
        self.size = size_m
        self.scale = SIZE_PX / size_m  # px per metre
        self.pixels = np.empty((SIZE_PX, SIZE_PX, 3), dtype=np.float32)
        self.pixels[:] = _rgb(GROUND)

    def _window(self, x0, y0, x1, y1):
        """Pixel slices and metre coordinate grids for a bounding box (row 0 is the south edge)."""
        half = self.size / 2
        c0 = max(int((x0 + half) * self.scale), 0)
        c1 = min(int(math.ceil((x1 + half) * self.scale)), SIZE_PX)
        r0 = max(int((y0 + half) * self.scale), 0)
        r1 = min(int(math.ceil((y1 + half) * self.scale)), SIZE_PX)
        if c1 <= c0 or r1 <= r0:
            return None
        xs = (np.arange(c0, c1) + 0.5) / self.scale - half
        ys = (np.arange(r0, r1) + 0.5) / self.scale - half
        gx, gy = np.meshgrid(xs, ys)
        return (slice(r0, r1), slice(c0, c1)), gx, gy

    def _paint(self, window, mask, colour, opacity=1.0, soft=0.0):
        region = self.pixels[window]
        if soft:
            # A wide, gentle falloff: for shadows.
            alpha = np.clip(0.5 - mask / soft, 0, 1)[..., None] ** 1.5 * opacity
        else:
            # One pixel of soft edge keeps the shapes from looking jagged.
            alpha = np.clip(0.5 - mask * self.scale, 0, 1)[..., None] * opacity
        region[:] = region * (1 - alpha) + _rgb(colour) * alpha

    def shadow(self, x0, y0, x1, y1, soft=3.0, opacity=0.28):
        """A soft dark patch under a building: it sits the building on the ground."""
        found = self._window(x0 - soft, y0 - soft, x1 + soft, y1 + soft)
        if not found:
            return
        window, gx, gy = found
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        dx = np.abs(gx - cx) - (x1 - x0) / 2
        dy = np.abs(gy - cy) - (y1 - y0) / 2
        distance = np.hypot(np.maximum(dx, 0), np.maximum(dy, 0)) + np.minimum(np.maximum(dx, dy), 0)
        self._paint(window, distance - soft * 0.2, "#4B5547", opacity=opacity, soft=soft)

    def near(self, colours, tolerance=0.035):
        """Mask of the pixels that are (close to) any of these colours."""
        mask = np.zeros(self.pixels.shape[:2], dtype=bool)
        for colour in colours:
            mask |= np.abs(self.pixels - _rgb(colour)).max(axis=-1) < tolerance
        return mask

    def enrich(self, seed=3):
        """Printed-playmat detail: mottled grass with tufts and flowers, paving slabs, speckled roads."""
        rng = np.random.default_rng(seed)
        half = self.size / 2
        ys, xs = np.mgrid[0:SIZE_PX, 0:SIZE_PX]
        metres_x = (xs + 0.5) / self.scale - half
        metres_y = (ys + 0.5) / self.scale - half

        def blotches(cell):
            """Soft value noise, 0..1, with features about `cell` metres across."""
            n = max(int(self.size / cell), 2)
            coarse = rng.random((n + 1, n + 1)).astype(np.float32)
            fy = np.linspace(0, n, SIZE_PX, endpoint=False)
            fx = np.linspace(0, n, SIZE_PX, endpoint=False)
            iy, ix = fy.astype(int), fx.astype(int)
            ty, tx = (fy - iy)[:, None], (fx - ix)[None, :]
            ty, tx = ty * ty * (3 - 2 * ty), tx * tx * (3 - 2 * tx)
            a = coarse[iy][:, ix]
            b = coarse[iy][:, ix + 1]
            c = coarse[iy + 1][:, ix]
            d = coarse[iy + 1][:, ix + 1]
            return (a * (1 - tx) + b * tx) * (1 - ty) + (c * (1 - tx) + d * tx) * ty

        grass = self.near([GRASS, GRASS_DARK, "#B4CE9A"])
        ground = self.near([GROUND])
        road = self.near([ROAD])
        pavement = self.near([PAVEMENT, "#E6DCC6"])
        path = self.near([PATH])

        # Grass: big soft patches of lighter and darker green, then tufts and flowers.
        tone = 0.9 + 0.2 * blotches(14)
        tone = tone * (0.96 + 0.08 * blotches(3))
        self.pixels[grass] *= tone[grass][:, None]
        count = int(self.size * self.size * 0.5)
        py = rng.integers(2, SIZE_PX - 2, count)
        px = rng.integers(2, SIZE_PX - 2, count)
        keep = grass[py, px]
        py, px = py[keep], px[keep]
        kinds = rng.random(len(py))
        for dy, dx in ((0, 0), (0, 1), (1, 0), (1, 1), (-1, 0)):
            tufts = kinds < 0.86
            self.pixels[py[tufts] + dy, px[tufts] + dx] *= 0.86
        for colour, lo, hi in (("#FFFDF6", 0.86, 0.93), ("#F7C531", 0.93, 0.97), ("#EE6FA8", 0.97, 1.0)):
            pick = (kinds >= lo) & (kinds < hi)
            for dy, dx in ((0, 0), (0, 1), (1, 0), (1, 1)):
                self.pixels[py[pick] + dy, px[pick] + dx] = _rgb(colour)

        # Bare ground and paths: a gentle sandy mottle.
        for mask, amount in ((ground, 0.1), (path, 0.12)):
            tone = (1 - amount / 2) + amount * blotches(5) * (0.9 + 0.2 * rng.random((SIZE_PX, SIZE_PX)).astype(np.float32))
            self.pixels[mask] *= tone[mask][:, None]

        # The lake: soft lighter and darker patches, like light on water.
        water = self.near(["#3E7FA8"])
        tone = 0.92 + 0.16 * blotches(10)
        self.pixels[water] *= tone[water][:, None]

        # Roads: fine speckle, like printed tarmac.
        speckle = 0.95 + 0.07 * rng.random((SIZE_PX, SIZE_PX)).astype(np.float32)
        self.pixels[road] *= speckle[road][:, None]

        # Pavements and plazas: paving slabs.
        slab = 2.4
        lines = ((metres_x % slab) < 0.14) | ((metres_y % slab) < 0.14)
        self.pixels[pavement & lines] *= 0.9
        slab_tone = 0.97 + 0.05 * rng.random((int(self.size / slab) + 2, int(self.size / slab) + 2)).astype(np.float32)
        tones = slab_tone[((metres_y + half) / slab).astype(int), ((metres_x + half) / slab).astype(int)]
        self.pixels[pavement] *= tones[pavement][:, None]
        np.clip(self.pixels, 0, 1, out=self.pixels)

    def rect(self, x0, y0, x1, y1, colour, radius=1.2):
        found = self._window(x0 - 1, y0 - 1, x1 + 1, y1 + 1)
        if not found:
            return
        window, gx, gy = found
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        hx, hy = (x1 - x0) / 2 - radius, (y1 - y0) / 2 - radius
        dx = np.abs(gx - cx) - hx
        dy = np.abs(gy - cy) - hy
        distance = np.hypot(np.maximum(dx, 0), np.maximum(dy, 0)) + np.minimum(np.maximum(dx, dy), 0) - radius
        self._paint(window, distance, colour)

    def circle(self, x, y, radius, colour):
        found = self._window(x - radius - 1, y - radius - 1, x + radius + 1, y + radius + 1)
        if not found:
            return
        window, gx, gy = found
        self._paint(window, np.hypot(gx - x, gy - y) - radius, colour)

    def stroke(self, points, width, colour):
        """A thick line through the points, with round joints."""
        for (ax, ay), (bx, by) in zip(points, points[1:]):
            length = math.hypot(bx - ax, by - ay)
            steps = max(int(length / (width * 0.25)), 1)
            for i in range(steps + 1):
                t = i / steps
                self.circle(ax + (bx - ax) * t, ay + (by - ay) * t, width / 2, colour)

    def dashes(self, a, b, colour, dash=2.4, gap=2.4, width=0.45):
        (ax, ay), (bx, by) = a, b
        length = math.hypot(bx - ax, by - ay)
        ux, uy = (bx - ax) / length, (by - ay) / length
        at = 0.0
        while at < length:
            end = min(at + dash, length)
            x0, y0, x1, y1 = ax + ux * at, ay + uy * at, ax + ux * end, ay + uy * end
            pad = width / 2
            self.rect(min(x0, x1) - pad * abs(uy), min(y0, y1) - pad * abs(ux), max(x0, x1) + pad * abs(uy), max(y0, y1) + pad * abs(ux), colour, radius=0.1)
            at += dash + gap

    def save(self, path):
        image = bpy.data.images.new(os.path.basename(path), SIZE_PX, SIZE_PX, alpha=False)
        rgba = np.ones((SIZE_PX, SIZE_PX, 4), dtype=np.float32)
        rgba[..., :3] = self.pixels
        image.pixels.foreach_set(rgba.ravel())
        os.makedirs(os.path.dirname(path), exist_ok=True)
        image.filepath_raw = path
        image.file_format = "PNG"
        image.save()
        return image


def draw(layout, path, footprints=()):
    size = layout["size"]
    half = size / 2
    mat = Mat(size)

    if layout.get("base") == "grass":
        mat.rect(-half + 3, -half + 3, half - 3, half - 3, GRASS, radius=10)
    elif layout.get("base") == "lake":
        # A lake, with islands drawn as overlapping blobs: a rocky shore, then grass on top.
        mat.rect(-half + 3, -half + 3, half - 3, half - 3, "#3E7FA8", radius=10)
        for x, y, r in layout.get("islands", []):
            mat.circle(x, y, r + 4, "#B7A98F")
        for x, y, r in layout.get("islands", []):
            mat.circle(x, y, r + 1.5, "#9E9078")
        for x, y, r in layout.get("islands", []):
            mat.circle(x, y, r, GRASS)

    for patch in layout.get("grass", []):
        if "circle" in patch:
            x, y, r = patch["circle"]
            mat.circle(x, y, r, patch.get("colour", GRASS))
        else:
            x0, y0, x1, y1 = patch["rect"]
            mat.rect(x0, y0, x1, y1, patch.get("colour", GRASS), radius=patch.get("radius", 4))

    # Pavements first, then every road on top, so junctions join up cleanly.
    roads = layout.get("roads", [])
    for road in roads:
        (ax, ay), (bx, by), w = road["a"], road["b"], road["width"] / 2 + 3
        mat.rect(min(ax, bx) - (w if ax == bx else 0), min(ay, by) - (w if ay == by else 0),
                 max(ax, bx) + (w if ax == bx else 0), max(ay, by) + (w if ay == by else 0), PAVEMENT, radius=2)
    for road in roads:
        (ax, ay), (bx, by), w = road["a"], road["b"], road["width"] / 2
        mat.rect(min(ax, bx) - (w if ax == bx else 0), min(ay, by) - (w if ay == by else 0),
                 max(ax, bx) + (w if ax == bx else 0), max(ay, by) + (w if ay == by else 0), ROAD, radius=1)
    for road in roads:
        mat.dashes(road["a"], road["b"], MARKING)
    # Clear the markings out of the junctions.
    for junction in layout.get("junctions", []):
        x, y, w = junction
        mat.rect(x - w / 2, y - w / 2, x + w / 2, y + w / 2, ROAD, radius=0.5)
    for crossing in layout.get("crossings", []):
        x, y, direction, width = crossing
        for i in range(-3, 4):
            offset = i * (width / 7.5)
            if direction == "x":  # the road runs along x; stripes are spaced across it
                mat.rect(x - 2, y + offset - 0.45, x + 2, y + offset + 0.45, MARKING, radius=0.15)
            else:
                mat.rect(x + offset - 0.45, y - 2, x + offset + 0.45, y + 2, MARKING, radius=0.15)

    for path_points in layout.get("paths", []):
        mat.stroke(path_points["points"], path_points.get("width", 5), path_points.get("colour", PATH))
    for paved in layout.get("paved", []):
        x0, y0, x1, y1 = paved["rect"]
        mat.rect(x0, y0, x1, y1, paved.get("colour", PAVEMENT), radius=paved.get("radius", 2))

    pool = layout.get("pool")
    if pool:
        x, y, r = pool
        mat.circle(x, y, r + 1.4, MARKING)
        mat.circle(x, y, r, WATER)
        mat.circle(x - r * 0.3, y + r * 0.3, r * 0.22, "#BFE9F5")

    mat.enrich()

    # Soft shadows under every building, so nothing looks like it is floating on the mat.
    for x0, y0, x1, y1 in footprints:
        mat.shadow(x0, y0, x1, y1)

    # The stitched edge of the mat.
    inset = half - 2.2
    for a, b in (((-inset, -inset), (inset, -inset)), ((inset, -inset), (inset, inset)),
                 ((inset, inset), (-inset, inset)), ((-inset, inset), (-inset, -inset))):
        mat.dashes(a, b, STITCH, dash=1.6, gap=1.2, width=0.4)

    return mat.save(path)
