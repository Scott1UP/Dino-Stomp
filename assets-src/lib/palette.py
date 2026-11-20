"""Palette, colour schemes and the shared atlas.

Every model samples one atlas. Flat-coloured faces point their UVs at the
centre of a 32 px swatch block. The swatch layout is derived from the order of
the colours in palette.json, so adding colours at the end never moves existing
swatches.
"""

import json
import os

import bpy
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

with open(os.path.join(ROOT, "palette.json")) as f:
    _DATA = json.load(f)

COLOURS = _DATA["colours"]
SCHEMES = _DATA["schemes"]
SCHEME_NAMES = list(SCHEMES.keys())

ATLAS_SIZE = _DATA["atlas"]["size"]
SWATCH = _DATA["atlas"]["swatch"]
PADDING = _DATA["atlas"]["padding"]
CELL = SWATCH + 2 * PADDING
PER_ROW = ATLAS_SIZE // CELL

_ORDER = list(COLOURS.keys())

MATERIAL_NAME = "Atlas"
IMAGE_NAME = "atlas"


def hex_to_rgb(value):
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) / 255 for i in (0, 2, 4))


def _cell(name):
    index = _ORDER.index(name)
    return index % PER_ROW, index // PER_ROW


def swatch_uv(name):
    """UV at the centre of a colour's swatch block (Blender UV, origin bottom-left).

    Swatches start at the top-left of the atlas, which is how the image reads
    when opened in an image viewer.
    """
    col, row = _cell(name)
    u = (col * CELL + CELL / 2) / ATLAS_SIZE
    v = 1 - (row * CELL + CELL / 2) / ATLAS_SIZE
    return u, v


def build_atlas_image():
    """Create the atlas as a Blender image: swatches only for now.

    The padding around each swatch is filled with the swatch's own colour, so
    lower mip levels never bleed a neighbour in.
    """
    old = bpy.data.images.get(IMAGE_NAME)
    if old:
        bpy.data.images.remove(old)

    image = bpy.data.images.new(IMAGE_NAME, ATLAS_SIZE, ATLAS_SIZE, alpha=True)
    pixels = np.zeros((ATLAS_SIZE, ATLAS_SIZE, 4), dtype=np.float32)
    for name in _ORDER:
        col, row = _cell(name)
        r, g, b = hex_to_rgb(COLOURS[name])
        x0 = col * CELL
        # Row 0 is the top of the image; Blender's pixel rows start at the bottom.
        y1 = ATLAS_SIZE - row * CELL
        pixels[y1 - CELL : y1, x0 : x0 + CELL] = (r, g, b, 1.0)
    image.pixels.foreach_set(pixels.ravel())
    image.update()
    return image


def save_atlas(path):
    image = bpy.data.images.get(IMAGE_NAME) or build_atlas_image()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    image.filepath_raw = path
    image.file_format = "PNG"
    image.save()


def atlas_material():
    """The one material every model shares."""
    material = bpy.data.materials.get(MATERIAL_NAME)
    if material:
        return material

    image = bpy.data.images.get(IMAGE_NAME) or build_atlas_image()
    material = bpy.data.materials.new(MATERIAL_NAME)
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = next(n for n in nodes if n.type == "BSDF_PRINCIPLED")
    texture = nodes.new("ShaderNodeTexImage")
    texture.image = image
    links.new(texture.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 1.0
    return material
