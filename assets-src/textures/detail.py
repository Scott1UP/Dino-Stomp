"""Draws the surface-detail texture the game multiplies over the flat colours.

One small repeating image whose three channels hold three patterns:

  red    scalloped roof tiles (also used for leaves)
  green  brick courses (used bigger for stone blocks)
  blue   planks (also wallpaper stripes and tin panel seams)

White leaves the colour alone; darker lines and tones add the detail. Each
pattern repeats seamlessly. Runs inside Blender (numpy and Blender's image API).
"""

import os

import bpy
import numpy as np

SIZE = 512


def _tiles(rng):
    """Rows of overlapping scallops."""
    img = np.ones((SIZE, SIZE), dtype=np.float32)
    rows, per_row = 4, 4
    row_h = SIZE / rows
    w = SIZE / per_row
    ys, xs = np.mgrid[0:SIZE, 0:SIZE].astype(np.float32)
    for row in range(rows + 1):
        offset = (row % 2) * w / 2
        top = row * row_h
        for i in range(-1, per_row + 1):
            cx = i * w + w / 2 + offset
            # Each tile is a rounded tongue hanging down from the row above it.
            d = np.hypot((xs - cx) / (w * 0.5), (ys - top) / (row_h * 1.0))
            inside = (d < 1.0) & (ys >= top)
            for wrap in (-SIZE, 0, SIZE):
                dd = np.hypot((xs - cx - wrap) / (w * 0.5), (ys - top) / (row_h * 1.0))
                inside = inside | ((dd < 1.0) & (ys >= top))
                edge = (np.abs(dd - 1.0) < 0.09) & (ys >= top)
                img[edge] = 0.72
            tone = 0.9 + 0.1 * rng.random()
            img[inside & (img > 0.8)] *= tone
    # A little shading down each tile: lighter at the bottom edge.
    img *= 0.94 + 0.06 * ((ys % row_h) / row_h)
    return np.clip(img, 0, 1)


def _bricks(rng):
    """Four staggered courses with mortar lines."""
    img = np.ones((SIZE, SIZE), dtype=np.float32)
    courses, per_course = 4, 2
    h = SIZE // courses
    w = SIZE // per_course
    mortar = 9
    for course in range(courses):
        y0 = course * h
        offset = (course % 2) * w // 2
        for i in range(per_course):
            x0 = (i * w + offset) % SIZE
            tone = 0.9 + 0.1 * rng.random()
            cols = np.arange(x0, x0 + w) % SIZE
            img[y0:y0 + h, cols] = tone
            img[y0:y0 + h, np.arange(x0, x0 + mortar) % SIZE] = 0.74
        img[y0:y0 + mortar, :] = 0.74
    return img


def _planks(rng):
    """Four boards with dark joints and a faint grain."""
    img = np.ones((SIZE, SIZE), dtype=np.float32)
    boards = 4
    h = SIZE // boards
    for board in range(boards):
        y0 = board * h
        img[y0:y0 + h, :] = 0.92 + 0.08 * rng.random()
        for _ in range(5):
            y = y0 + 12 + int(rng.random() * (h - 24))
            img[y:y + 3, :] *= 0.94
        img[y0:y0 + 8, :] = 0.72
    return img


def build(path):
    rng = np.random.default_rng(11)
    # Image rows run bottom-up, so the scallops are flipped to hang downwards on a roof.
    rgb = np.stack([np.flipud(_tiles(rng)), _bricks(rng), _planks(rng)], axis=-1)
    rgba = np.ones((SIZE, SIZE, 4), dtype=np.float32)
    rgba[..., :3] = rgb
    image = bpy.data.images.new("detail", SIZE, SIZE, alpha=False)
    image.pixels.foreach_set(rgba.ravel())
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.filepath_raw = path
    image.file_format = "PNG"
    image.save()
