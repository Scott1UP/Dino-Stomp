"""Small mesh-building kit.

Geometry is collected as flat-coloured polygons, then turned into a Blender
object whose UVs point at the centre of each face's swatch in the shared atlas.
Faces never share vertices, so everything is flat shaded.

Coordinates are in the building's local frame: X along the frontage, the front
faces -Y, Z is up, and the origin is at the centre of the base.
"""

import bpy
from mathutils import Vector

from . import palette

SIDES = ("-x", "+x", "-y", "+y", "-z", "+z")


class Kit:
    def __init__(self):
        self.faces = []  # (list[Vector], colour name)

    # --- primitives -----------------------------------------------------

    def poly(self, points, hint, colour):
        """Add a polygon, wound so its normal agrees with `hint`."""
        points = [Vector(p) for p in points]
        normal = (points[1] - points[0]).cross(points[2] - points[0])
        if normal.dot(Vector(hint)) < 0:
            points.reverse()
        self.faces.append((points, colour))

    def convex(self, faces, colour, colours=None):
        """Add a convex solid from its faces (lists of points).

        Each face is wound to point away from the solid's centre. `colours`
        optionally overrides the colour by face index.
        """
        every = [Vector(p) for face in faces for p in face]
        centre = sum(every, Vector()) / len(every)
        for index, face in enumerate(faces):
            face_centre = sum((Vector(p) for p in face), Vector()) / len(face)
            self.poly(face, face_centre - centre, (colours or {}).get(index, colour))

    def box(self, lo, hi, colour, sides=None, skip=()):
        """Axis-aligned box. `sides` overrides colours, e.g. {"+y": "interiorCream"}."""
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        quads = {
            "-x": [(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)],
            "+x": [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
            "-y": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
            "+y": [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)],
            "-z": [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)],
            "+z": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
        }
        hints = {
            "-x": (-1, 0, 0),
            "+x": (1, 0, 0),
            "-y": (0, -1, 0),
            "+y": (0, 1, 0),
            "-z": (0, 0, -1),
            "+z": (0, 0, 1),
        }
        for side in SIDES:
            if side in skip:
                continue
            self.poly(quads[side], hints[side], (sides or {}).get(side, colour))

    def extrude_x(self, section, x0, x1, colour, colours=None):
        """Extrude a convex (y, z) cross-section along X."""
        near = [(x0, y, z) for y, z in section]
        far = [(x1, y, z) for y, z in section]
        faces = [near, far]
        count = len(section)
        for i in range(count):
            j = (i + 1) % count
            faces.append([near[i], near[j], far[j], far[i]])
        self.convex(faces, colour, colours)

    def extrude_y(self, section, y0, y1, colour, colours=None):
        """Extrude a convex (x, z) cross-section along Y."""
        near = [(x, y0, z) for x, z in section]
        far = [(x, y1, z) for x, z in section]
        faces = [near, far]
        count = len(section)
        for i in range(count):
            j = (i + 1) % count
            faces.append([near[i], near[j], far[j], far[i]])
        self.convex(faces, colour, colours)

    def slab(self, bottom, thickness, colour):
        """A convex slab: the `bottom` polygon raised by `thickness` in Z."""
        top = [(x, y, z + thickness) for x, y, z in bottom]
        faces = [bottom, top]
        count = len(bottom)
        for i in range(count):
            j = (i + 1) % count
            faces.append([bottom[i], bottom[j], top[j], top[i]])
        self.convex(faces, colour)

    def wall(self, x0, x1, z0, z1, y_out, thickness, inward, openings, colours):
        """A wall in the XZ plane with recessed windows and doors.

        `y_out` is the outside face and `inward` is +1 or -1: the Y direction
        from the outside face towards the inside of the building.
        `openings` is a list of dicts: x0, x1, z0, z1, kind ("window" | "door").
        `colours` needs wall, interior, trim, glass, shine and door.
        """
        y_in = y_out + thickness * inward
        out_hint = (0, -inward, 0)
        in_hint = (0, inward, 0)
        openings = sorted(openings, key=lambda o: o["x0"])

        def both(xa, xb, za, zb):
            if xb - xa < 1e-6 or zb - za < 1e-6:
                return
            for y, hint, colour in (
                (y_out, out_hint, colours["wall"]),
                (y_in, in_hint, colours["interior"]),
            ):
                self.poly([(xa, y, za), (xb, y, za), (xb, y, zb), (xa, y, zb)], hint, colour)

        cursor = x0
        for o in openings:
            both(cursor, o["x0"], z0, z1)  # full-height strip before the opening
            both(o["x0"], o["x1"], o["z1"], z1)  # above
            both(o["x0"], o["x1"], z0, o["z0"])  # below
            cursor = o["x1"]
        both(cursor, x1, z0, z1)

        # Outside edges of the slab.
        self.poly([(x0, y_out, z1), (x1, y_out, z1), (x1, y_in, z1), (x0, y_in, z1)], (0, 0, 1), colours["wall"])
        self.poly([(x0, y_out, z0), (x1, y_out, z0), (x1, y_in, z0), (x0, y_in, z0)], (0, 0, -1), colours["wall"])
        self.poly([(x0, y_out, z0), (x0, y_in, z0), (x0, y_in, z1), (x0, y_out, z1)], (-1, 0, 0), colours["wall"])
        self.poly([(x1, y_out, z0), (x1, y_in, z0), (x1, y_in, z1), (x1, y_out, z1)], (1, 0, 0), colours["wall"])

        for o in openings:
            ox0, ox1, oz0, oz1 = o["x0"], o["x1"], o["z0"], o["z1"]
            trim = colours["trim"]
            # Reveals: the depth that gives each opening a crisp toon shadow line.
            self.poly([(ox0, y_out, oz0), (ox0, y_in, oz0), (ox0, y_in, oz1), (ox0, y_out, oz1)], (1, 0, 0), trim)
            self.poly([(ox1, y_out, oz0), (ox1, y_in, oz0), (ox1, y_in, oz1), (ox1, y_out, oz1)], (-1, 0, 0), trim)
            self.poly([(ox0, y_out, oz1), (ox1, y_out, oz1), (ox1, y_in, oz1), (ox0, y_in, oz1)], (0, 0, -1), trim)
            if oz0 > z0 + 1e-6:
                self.poly([(ox0, y_out, oz0), (ox1, y_out, oz0), (ox1, y_in, oz0), (ox0, y_in, oz0)], (0, 0, 1), trim)

            # The pane sits 13 cm in from the outside face.
            y_pane = y_out + 0.13 * inward
            pane = colours["door"] if o["kind"] == "door" else colours["glass"]
            self.poly([(ox0, y_pane, oz0), (ox1, y_pane, oz0), (ox1, y_pane, oz1), (ox0, y_pane, oz1)], out_hint, pane)

            if o["kind"] == "window":
                self.shine(ox0, ox1, oz0, oz1, y_pane - 0.03 * inward, out_hint, colours["shine"])

    def shine(self, x0, x1, z0, z1, y, hint, colour):
        """The light diagonal stripe that makes a dark pane read as glass."""
        w = x1 - x0
        h = z1 - z0
        self.poly(
            [
                (x0 + w * 0.18, y, z0 + h * 0.52),
                (x0 + w * 0.32, y, z0 + h * 0.52),
                (x0 + w * 0.62, y, z0 + h * 0.86),
                (x0 + w * 0.48, y, z0 + h * 0.86),
            ],
            hint,
            colour,
        )

    # --- output -----------------------------------------------------------

    def triangles(self):
        return sum(len(points) - 2 for points, _ in self.faces)

    def to_object(self, name, collection=None, detail=None):
        """Create the object, with its origin at the centre of its bounding box.

        `detail` is the module's sound material (plaster, tile, wood...). It picks
        the surface pattern the game multiplies over the flat colour: roof tiles,
        brick courses, planks. See DETAIL below.
        """
        every = [p for points, _ in self.faces for p in points]
        lo = Vector((min(p.x for p in every), min(p.y for p in every), min(p.z for p in every)))
        hi = Vector((max(p.x for p in every), max(p.y for p in every), max(p.z for p in every)))
        centre = (lo + hi) / 2

        vertices = []
        polygons = []
        for points, _ in self.faces:
            start = len(vertices)
            vertices.extend(p - centre for p in points)
            polygons.append(list(range(start, start + len(points))))

        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(vertices, [], polygons)
        uv_layer = mesh.uv_layers.new(name="UVMap")
        for polygon, (_, colour) in zip(mesh.polygons, self.faces):
            uv = palette.swatch_uv(colour)
            for loop_index in polygon.loop_indices:
                uv_layer.data[loop_index].uv = uv
            polygon.use_smooth = False
        mesh.materials.append(palette.atlas_material())

        # Second UV set and a vertex colour: which detail pattern, and where on it.
        detail_uv = mesh.uv_layers.new(name="Detail")
        selector = mesh.color_attributes.new("Detail", "FLOAT_COLOR", "CORNER")
        mesh.color_attributes.active_color = selector
        for polygon, (points, colour) in zip(mesh.polygons, self.faces):
            channel, uvs = detail_mapping(points, colour, detail)
            for loop_index, uv in zip(polygon.loop_indices, uvs):
                detail_uv.data[loop_index].uv = uv
                selector.data[loop_index].color = channel
        mesh.uv_layers.active = uv_layer
        mesh.update()

        obj = bpy.data.objects.new(name, mesh)
        obj.location = centre
        (collection or bpy.context.scene.collection).objects.link(obj)
        return obj


# --- surface detail ---------------------------------------------------------
#
# The game multiplies a small repeating greyscale texture over the flat colours.
# Its three channels hold three patterns; a face's vertex colour picks one
# (or none), and its second UV set says where on the pattern it sits, in
# building-local metres, so courses line up from one module to the next.

RED, GREEN, BLUE, NONE = (1, 0, 0, 1), (0, 1, 0, 1), (0, 0, 1, 1), (0, 0, 0, 1)

# material -> (channel, metres per repeat)
DETAIL = {
    "tile": (RED, 1.8),  # scalloped roof tiles
    "leaves": (RED, 1.5),  # the same scallops read as leaves
    "plaster": (GREEN, 2.4),  # brick courses
    "stone": (GREEN, 3.4),  # the same courses, bigger: stone blocks
    "wood": (BLUE, 1.6),  # planks
    "tin": (BLUE, 3.2),  # panel seams
}
# These colours are always flat: trim, glass, tyres.
FLAT = {"trimWhite", "windowBlue", "windowShine", "glassTint", "tyre", "starGold", "dust", "water", "foam"}


def detail_mapping(points, colour, material):
    """(channel, [uv per vertex]) for one face."""
    flat = (NONE, [(0.0, 0.0)] * len(points))
    if colour in FLAT:
        return flat
    upright = False
    if colour == "interiorCream":
        channel, size, upright = BLUE, 1.1, True  # wallpaper stripes inside
    elif material in DETAIL:
        channel, size = DETAIL[material]
    else:
        return flat

    normal = (points[1] - points[0]).cross(points[2] - points[0])
    if normal.length < 1e-9:
        return flat
    normal.normalize()
    up = Vector((0, 0, 1))
    across = up.cross(normal) if abs(normal.z) < 0.95 else Vector((1, 0, 0))
    across.normalize()
    along = normal.cross(across)  # up the wall, or up the slope of a roof
    uvs = [(p.dot(across) / size, p.dot(along) / size) for p in points]
    if upright:
        uvs = [(v, u) for u, v in uvs]
    return channel, uvs
