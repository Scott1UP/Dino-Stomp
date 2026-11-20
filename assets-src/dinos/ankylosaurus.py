"""Ankylosaurus, built to match the Quaternius CC0 dinosaur pack.

The pack has no ankylosaurus, so this script makes one in the same style:
flat-shaded low poly, a few plain colour materials, and the pack's own
quadruped skeleton. It opens the pack's Stegosaurus, keeps the armature and
its six actions (the Attack is a spinning tail swing), and replaces the mesh
with a new one weighted to the same bones.

    blender --background --factory-startup --disable-autoexec --python assets-src/dinos/ankylosaurus.py

Writes assets-out/dinos/Ankylosaurus.blend and previews in assets-out/previews/.
"""

import math
import os
import random

import bmesh
import bpy
from mathutils import Matrix, Vector

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACK = os.path.join(REPO, "Dinosaur-Animated-Pack-Quaternius-2018")
OUT_BLEND = os.path.join(REPO, "assets-out", "dinos", "Ankylosaurus.blend")
PREVIEWS = os.path.join(REPO, "assets-out", "previews")

TRIANGLE_BUDGET = 2500
TAIL_RAISE_DEG = 14  # the stegosaurus tail droops to the ground; a club wants carrying

# Material slots. Brown and LightBrown are the pack's own; Teal sits at the same
# dark value as the pack's Green and Purple.
TEAL, BELLY, HORN, BLACK = 0, 1, 2, 3

# Body cross-sections from beak to tail base: (y, half width, top z, z of the
# widest point, bottom z). The head is at -Y, as in the pack.
STATIONS = [
    (-8.5, 0.35, 3.75, 3.45, 3.15),
    (-8.0, 0.75, 4.25, 3.60, 3.00),
    (-7.1, 1.20, 4.85, 3.90, 2.95),
    (-6.2, 1.50, 5.25, 4.30, 3.00),
    (-5.4, 1.30, 5.30, 4.40, 3.20),
    (-4.6, 1.05, 5.30, 4.40, 3.40),
    (-3.7, 1.80, 6.00, 4.40, 3.10),
    (-2.6, 2.80, 6.70, 4.10, 2.30),
    (-1.2, 3.45, 7.25, 4.00, 1.90),
    (0.3, 3.75, 7.60, 4.00, 1.75),
    (1.8, 3.60, 7.60, 4.30, 1.95),
    (3.2, 2.90, 7.20, 4.80, 2.80),
]
BEAK_SEGMENTS = 2  # the first segments from the snout are horn-coloured
TAIL_RADII = [1.3, 0.95, 0.68, 0.5, 0.42]  # at Tail2..Tail5 heads and the tail tip

SPINE = ["Head", "Neck", "Shoulders", "Torso", "Hips", "Back", "Tail1", "Tail2", "Tail3", "Tail4", "Tail5"]


class Builder:
    def __init__(self):
        self.verts = []
        self.weights = []
        self.faces = []
        self.materials = []

    def vert(self, co, weights):
        self.verts.append(Vector(co))
        self.weights.append(weights)
        return len(self.verts) - 1

    def face(self, indices, material):
        self.faces.append(list(indices))
        self.materials.append(material)

    def pyramid(self, centre, axis, along, half_along, half_across, height, material, weights):
        """A closed four-sided spike: scutes, flank spikes, horns, toes."""
        centre = Vector(centre)
        axis = Vector(axis).normalized()
        along = Vector(along)
        along = (along - axis * along.dot(axis)).normalized()
        across = axis.cross(along)
        base = [
            centre + along * half_along * sa + across * half_across * sb
            for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1))
        ]
        ids = [self.vert(p, weights) for p in base]
        apex = self.vert(centre + axis * height, weights)
        self.face(ids, material)
        for i in range(4):
            self.face([ids[i], ids[(i + 1) % 4], apex], material)


def profile(hw, zt, zw, zb, notch=0.0):
    """Half of a body cross-section, top to bottom, as (x, z): a low, wide dome."""
    height = zt - zb
    return [
        (0.0, zt - notch),
        (0.5 * hw, zt - 0.07 * height),
        (0.88 * hw, zw + 0.5 * (zt - zw)),
        (hw, zw),
        (0.78 * hw, zb + 0.3 * (zw - zb)),
        (0.4 * hw, zb),
        (0.0, zb + notch),
    ]


def build():
    bpy.ops.wm.open_mainfile(filepath=os.path.join(PACK, "Blends", "Stegosaurus.blend"))
    arm = bpy.data.objects["Armature"]
    old = bpy.data.objects["Stegosaurus"]
    world = arm.matrix_world

    # --- carry the tail higher ---
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    bones = arm.data.edit_bones
    pivot = bones["Tail1"].head.copy()
    lift = Matrix.Translation(pivot) @ Matrix.Rotation(math.radians(TAIL_RAISE_DEG), 4, "X") @ Matrix.Translation(-pivot)
    # Connected bones share their joints, so work out each new position once
    # (transforming bone by bone would rotate the shared joints twice).
    moved = {
        name: (lift @ bones[name].head, lift @ bones[name].tail)
        for name in ("Tail1", "Tail2", "Tail3", "Tail4", "Tail5")
    }
    for name, (new_head, new_tail) in moved.items():
        bones[name].head = new_head
        bones[name].tail = new_tail
    bpy.ops.object.mode_set(mode="OBJECT")

    def head(name):
        return world @ arm.data.bones[name].head_local

    def tail(name):
        return world @ arm.data.bones[name].tail_local

    spine_mid = [(name, ((head(name) + tail(name)) / 2).y) for name in SPINE]

    def spine_weights(y):
        """Blend between the two spine bones either side of y."""
        if y <= spine_mid[0][1]:
            return {spine_mid[0][0]: 1.0}
        for (a, ya), (b, yb) in zip(spine_mid, spine_mid[1:]):
            if y <= yb:
                t = (y - ya) / (yb - ya)
                return {a: 1 - t, b: t}
        return {spine_mid[-1][0]: 1.0}

    rng = random.Random(7)
    mesh = Builder()

    # --- body, head, tail and club: one closed loft ---
    rings = []  # (y, half width, zt, zw, zb, notch, weights or None)
    for y, hw, zt, zw, zb in STATIONS:
        rings.append((y, hw, zt, zw, zb, 0.0, None))
    joints = [head("Tail2"), head("Tail3"), head("Tail4"), head("Tail5"), tail("Tail5")]
    for joint, radius in zip(joints, TAIL_RADII):
        zt = joint.z + 0.22
        rings.append((joint.y, radius * 1.12, zt, zt - radius * 0.8, zt - radius * 1.7, 0.0, None))
    tip = joints[-1]
    club_z = tip.z - 0.15
    club = {"Tail5": 1.0}
    for dy, hw, up, down, notch in (
        (0.35, 0.55, 0.42, 0.40, 0.0),
        (1.00, 1.65, 0.70, 0.62, 0.22),
        (2.00, 1.75, 0.74, 0.66, 0.26),
        (2.75, 0.95, 0.45, 0.42, 0.10),
    ):
        rings.append((tip.y + dy, hw, club_z + up, club_z, club_z - down, notch, club))
    club_start = len(rings) - 4

    ring_ids = []
    for index, (y, hw, zt, zw, zb, notch, fixed) in enumerate(rings):
        half = profile(hw, zt, zw, zb, notch)
        # The same small wobble on both sides keeps the facets lively but symmetrical.
        wobble = [(rng.uniform(-0.16, 0.16), rng.uniform(0.96, 1.04)) for _ in half]
        ids = []
        for k in range(12):
            source = k if k <= 6 else 12 - k
            x, z = half[source]
            dy, scale = wobble[source]
            if k > 6:
                x = -x
            if index in (0, len(rings) - 1):
                dy = 0.0
            ids.append(mesh.vert((x * scale, y + dy, z), fixed or spine_weights(y)))
        ring_ids.append(ids)

    diagonals = [[rng.random() < 0.5 for _ in range(6)] for _ in rings]
    for index in range(len(rings) - 1):
        a, b = ring_ids[index], ring_ids[index + 1]
        for k in range(12):
            n = (k + 1) % 12
            if index >= club_start - 1 or index < BEAK_SEGMENTS:
                material = HORN
            elif 4 <= k <= 7:
                material = BELLY
            else:
                material = TEAL
            # The pack's bodies are big uneven planes, not tidy rings of quads: split
            # each quad along a diagonal picked at random (the same on both sides).
            mirror = k >= 6
            if diagonals[index][11 - k if mirror else k] != mirror:
                mesh.face([a[k], a[n], b[n]], material)
                mesh.face([a[k], b[n], b[k]], material)
            else:
                mesh.face([a[k], a[n], b[k]], material)
                mesh.face([a[n], b[n], b[k]], material)
    mesh.face(ring_ids[0], HORN)
    mesh.face(ring_ids[-1], HORN)

    # --- where is the carapace at (y, fraction across)? ---
    def carapace(y, fraction):
        """Point and outward normal on the back, `fraction` of the way to the flank."""
        for (ya, *pa), (yb, *pb) in zip(rings, rings[1:]):
            if ya <= y <= yb:
                t = (y - ya) / (yb - ya)
                hw, zt, zw, zb = (pa[i] + (pb[i] - pa[i]) * t for i in range(4))
                break
        else:
            raise ValueError(y)
        top = profile(hw, zt, zw, zb)[:4]
        x = abs(fraction) * hw
        for (xa, za), (xb, zb_) in zip(top, top[1:]):
            if x <= xb + 1e-6:
                s = (x - xa) / (xb - xa)
                z = za + (zb_ - za) * s
                normal = Vector((-(zb_ - za), 0, xb - xa)).normalized()
                break
        sign = -1 if fraction < 0 else 1
        return Vector((x * sign, y, z)), Vector((normal.x * sign, 0, normal.z)), hw

    # --- armour: rows of scutes across the back, staggered like brickwork ---
    # Sizes, lean and spacing all vary, the same on both sides; the row either
    # side of the spine carries the biggest ones.
    scute_rows = [-4.0, -3.0, -1.9, -0.8, 0.4, 1.6, 2.7]
    for row, y in enumerate(scute_rows):
        fractions = (0.0, 0.4, 0.78) if row % 2 == 0 else (0.2, 0.6)
        for fraction in fractions:
            vary = rng.uniform(0.8, 1.25)
            lean = rng.uniform(0.05, 0.45)
            shift = rng.uniform(-0.25, 0.25)
            big = 1.35 if 0.3 < fraction < 0.5 else 1.0
            for sign in (1,) if fraction == 0 else (1, -1):
                point, normal, hw = carapace(y + shift, fraction * sign)
                if hw < 1.4 and fraction > 0.5:
                    continue
                size = (0.28 + 0.1 * min(hw, 3.5)) * vary * big
                mesh.pyramid(
                    point - normal * 0.12,
                    normal + Vector((0, lean, 0)),
                    (0, 1, 0),
                    size * 1.15,
                    size * 0.7,
                    size * (0.75 if big == 1.0 else 1.0),
                    HORN,
                    spine_weights(y),
                )

    # A ridge of scutes down the tail.
    for index in range(club_start - len(STATIONS)):
        y, hw, zt = rings[len(STATIONS) + index][:3]
        if index == club_start - len(STATIONS) - 1:
            break
        size = 0.25 + hw * 0.3
        mesh.pyramid((0, y, zt - 0.08), (0, 0.25, 1), (0, 1, 0), size, size * 0.8, size, HORN, spine_weights(y))

    # --- spikes along the flanks, largest at the shoulders ---
    for y, length in ((-3.6, 0.9), (-2.7, 1.35), (-1.7, 1.2), (-0.6, 1.05), (0.5, 1.0), (1.6, 0.95), (2.6, 0.85), (3.6, 0.7)):
        sweep, rise, stretch = rng.uniform(0.15, 0.5), rng.uniform(0.0, 0.25), rng.uniform(0.85, 1.2)
        for sign in (-1, 1):
            point, _, hw = carapace(y, sign * 1.0)
            mesh.pyramid(
                point - Vector((sign * 0.15, 0, 0)),
                (sign, sweep, rise),
                (0, 1, 0),
                0.46,
                0.24,
                length * stretch,
                HORN,
                spine_weights(y),
            )
    for index in (0, 1, 2):
        y, hw, zt, zw = rings[len(STATIONS) + index][:4]
        for sign in (-1, 1):
            mesh.pyramid((sign * hw * 0.9, y, zw), (sign, 0.35, 0.1), (0, 1, 0), 0.3, 0.2, 0.55, HORN, spine_weights(y))

    # --- head: two horns a side at the back of the skull, and eyes ---
    skull = {"Head": 1.0}
    for sign in (-1, 1):
        mesh.pyramid((sign * 1.2, -5.85, 4.95), (sign, 0.55, 0.45), (0, 1, 0), 0.36, 0.3, 0.85, HORN, skull)
        mesh.pyramid((sign * 1.3, -6.05, 3.75), (sign, 0.35, -0.4), (0, 1, 0), 0.34, 0.28, 0.7, HORN, skull)
        mesh.pyramid((sign * 1.2, -7.0, 4.42), (sign, -0.2, 0.35), (0, 1, 0), 0.17, 0.13, 0.07, BLACK, skull)

    # --- legs: short, thick and mostly hidden under the shell ---
    def leg(side, prefix, size):
        """A shaped leg like the pack's: a slab of thigh, a knee, a tapering shin, a wedge of foot."""
        suffix = ".R" if side < 0 else ".L"
        up, low, foot = f"{prefix}UpLeg{suffix}", f"{prefix}LowLeg{suffix}", f"{prefix}Foot{suffix}"
        hip, knee, ankle = head(up), head(low), tail(low)
        out = Vector((side, 0, 0))
        # (centre, half width across, half length front to back, weights)
        sections = [
            (hip + Vector((0, 0.15, 0.7)) + out * 0.2, 0.7, 1.35, {up: 1.0}),
            (hip + Vector((0, 0.1, -0.5)) + out * 0.35, 0.95, 1.7, {up: 1.0}),
            (hip.lerp(knee, 0.72) + out * 0.2, 0.85, 1.25, {up: 1.0}),
            (knee + Vector((0, -0.3, 0.05)), 0.74, 0.98, {up: 0.5, low: 0.5}),
            (knee.lerp(ankle, 0.5) + Vector((0, 0.1, 0)), 0.6, 0.72, {low: 1.0}),
            (Vector((ankle.x, ankle.y + 0.05, 0.62)), 0.56, 0.66, {low: 0.6, foot: 0.4}),
            (Vector((ankle.x, ankle.y - 0.2, 0.5)), 0.74, 0.98, {foot: 1.0}),
            (Vector((ankle.x, ankle.y - 0.4, 0.0)), 0.86, 1.22, {foot: 1.0}),
        ]
        loops = []
        for number, (centre, across, along, weights) in enumerate(sections):
            turn = 22.5 if number % 2 else 0.0  # alternate rings twist, so the facets are not a tidy grid
            loops.append(
                [
                    mesh.vert(
                        centre
                        + Vector((math.cos(a) * across * size * side, math.sin(a) * along * size, 0)),
                        weights,
                    )
                    for a in (math.radians(turn + 45 * i) for i in range(8))
                ]
            )
        for a, b in zip(loops, loops[1:]):
            for k in range(8):
                n = (k + 1) % 8
                mesh.face([a[k], a[n], b[n]], TEAL)
                mesh.face([a[k], b[n], b[k]], TEAL)
        mesh.face(loops[0], TEAL)
        mesh.face(loops[-1], TEAL)

        # Three blunt toenails across the front of the foot.
        sole = sections[-1][0]
        for dx in (-0.6, 0.0, 0.6):
            mesh.pyramid(
                sole + Vector((dx * 0.9 * size, -1.05 * size * (1 - abs(dx) * 0.3), 0.2)),
                (dx * 0.6, -1, 0.1),
                (1, 0, 0),
                0.3 * size,
                0.2,
                0.38,
                BELLY,
                {foot: 1.0},
            )

    for side in (-1, 1):
        leg(side, "Back", 1.0)
        leg(side, "Front", 0.82)

    # --- make the object ---
    data = bpy.data.meshes.new("Ankylosaurus")
    data.from_pydata(mesh.verts, [], mesh.faces)
    for polygon, material in zip(data.polygons, mesh.materials):
        polygon.material_index = material
        polygon.use_smooth = False

    teal = bpy.data.materials.new("Teal")
    teal.diffuse_color = (0.047, 0.072, 0.077, 1.0)
    black = bpy.data.materials.new("Black")
    black.diffuse_color = (0.006, 0.006, 0.006, 1.0)
    for material in (teal, bpy.data.materials["LightBrown"], bpy.data.materials["Brown"], black):
        data.materials.append(material)

    # Every shell is closed, so this reliably turns all the faces outwards.
    bm = bmesh.new()
    bm.from_mesh(data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(data)
    bm.free()
    data.update()

    obj = bpy.data.objects.new("Ankylosaurus", data)
    for collection in old.users_collection:
        collection.objects.link(obj)
    groups = {bone.name: obj.vertex_groups.new(name=bone.name) for bone in arm.data.bones}
    for index, weights in enumerate(mesh.weights):
        for bone, weight in weights.items():
            if weight > 0:
                groups[bone].add([index], weight, "REPLACE")
    obj.parent = arm
    obj.matrix_parent_inverse = world.inverted()
    modifier = obj.modifiers.new("Armature", "ARMATURE")
    modifier.object = arm

    old_mesh = old.data
    bpy.data.objects.remove(old, do_unlink=True)
    bpy.data.meshes.remove(old_mesh)

    for action in bpy.data.actions:
        action.name = action.name.replace("Stegosaurus_", "Ankylosaurus_")

    triangles = sum(len(p.vertices) - 2 for p in data.polygons)
    over = " OVER dino budget" if triangles > TRIANGLE_BUDGET else ""
    print(f"[ankylosaurus] vertices={len(data.vertices)} triangles={triangles}{over}")
    return arm, obj


def render_previews(arm):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = False
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 2.6  # the pack's colours are very dark; lift them to judge the form
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (0.8, 0.8, 0.8)

    camera = bpy.data.objects.new("PreviewCamera", bpy.data.cameras.new("PreviewCamera"))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.type = "ORTHO"
    camera.data.clip_end = 10000

    def shot(name, direction, centre=(0, 2.5, 4), scale=30, size=(1100, 700)):
        scene.render.resolution_x, scene.render.resolution_y = size
        camera.data.ortho_scale = scale
        centre = Vector(centre)
        camera.location = centre + Vector(direction).normalized() * 300
        camera.rotation_euler = (centre - camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = os.path.join(PREVIEWS, f"ankylosaurus_{name}.png")
        bpy.ops.render.render(write_still=True)

    def play(action_name, fraction):
        action = bpy.data.actions[action_name]
        arm.animation_data.action = action
        if action.slots:
            arm.animation_data.action_slot = action.slots[0]
        start, end = action.frame_range
        scene.frame_set(int(start + (end - start) * fraction))

    arm.data.pose_position = "REST"
    shot("side", (1, 0, 0.12))
    shot("front", (0, -1, 0.15), scale=20)
    shot("top", (0.001, 0, 1))
    shot("three_quarter", (1, -1, 0.7))
    shot("rear", (-0.8, 1, 0.6))

    arm.data.pose_position = "POSE"
    for action, fraction in (("Idle", 0.5), ("Walk", 0.3), ("Run", 0.4), ("Attack", 0.33), ("Attack", 0.66)):
        play(f"Ankylosaurus_{action}", fraction)
        shot(f"pose_{action.lower()}_{int(fraction * 100)}", (1, -1, 0.7), scale=36)

    # Beside the pack's own dinos, to judge the match.
    play("Ankylosaurus_Idle", 0.0)
    for index, name in enumerate(("Stegosaurus", "Triceratops")):
        path = os.path.join(PACK, "Blends", f"{name}.blend")
        with bpy.data.libraries.load(path) as (source, target):
            target.objects = list(source.objects)
        root = bpy.data.objects.new(f"Lineup_{name}", None)
        scene.collection.objects.link(root)
        root.location = ((index + 1) * 11, 0, 0)
        for obj in target.objects:
            if obj is None or obj.type not in {"MESH", "ARMATURE"}:
                continue
            scene.collection.objects.link(obj)
            if obj.parent is None:
                obj.parent = root
    shot("lineup", (0.35, -1, 0.45), centre=(11, 2, 5), scale=44, size=(1600, 700))

    bpy.data.objects.remove(camera)


def main():
    arm, obj = build()
    arm.data.pose_position = "POSE"
    os.makedirs(os.path.dirname(OUT_BLEND), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=OUT_BLEND, compress=True)
    render_previews(arm)  # after saving, so the lineup dinos stay out of the file


if __name__ == "__main__":
    main()
