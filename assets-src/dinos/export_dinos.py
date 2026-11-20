"""Export the three playable dinos as GLBs.

All three come straight from the Quaternius CC0 pack. Each is recoloured to its
signature colour, scaled to game size, stood on the origin facing -Y, and
exported with its animations under the game's clip names.

    blender --background --factory-startup --disable-autoexec --python assets-src/dinos/export_dinos.py
"""

import json
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.dirname(HERE))

from lib import scene as scene_lib  # noqa: E402

PACK = os.path.join(REPO, "Dinosaur-Animated-Pack-Quaternius-2018", "Blends")

with open(os.path.join(os.path.dirname(HERE), "palette.json")) as f:
    COLOURS = json.load(f)["colours"]

# Pack action suffix -> game clip name.
CLIPS = {"Idle": "idle", "Walk": "walk", "Run": "run", "Attack": "move", "Jump": "celebrate"}

DINOS = {
    "trex": {
        "blend": os.path.join(PACK, "Trex.blend"),
        "mesh": "Trex",
        "prefix": "TRex_",
        "height": 11.0,  # about 1.5x a two-storey house
        "materials": {
            "Green": "trexGreen",
            "LightGreen": "#7CCB86",
            "LightYellow": "interiorCream",
            "Red": "tomato",
            "Black": "tyre",
        },
    },
    "triceratops": {
        "blend": os.path.join(PACK, "Triceratops.blend"),
        "mesh": "Triceratops",
        "prefix": "Triceratops_",
        "length": 16.0,
        "materials": {"Purple": "triceratopsPurple", "LightBrown": "interiorCream", "Brown": "trimWhite"},
    },
    # The pack's own stegosaurus. Its Attack is a spinning tail swing.
    "stegosaurus": {
        "blend": os.path.join(PACK, "Stegosaurus.blend"),
        "mesh": "Stegosaurus",
        "prefix": "Stegosaurus_",
        "length": 17.0,
        "materials": {"DarkBrown": "stegosaurusTeal", "LightBrown": "interiorCream", "Brown": "#F7C531"},
    },
}


def linear(hex_colour):
    hex_colour = hex_colour.lstrip("#")
    out = []
    for i in (0, 2, 4):
        c = int(hex_colour[i : i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def flat_material(name, colour):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = next(n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = linear(COLOURS.get(colour, colour))
    bsdf.inputs["Roughness"].default_value = 1.0
    bsdf.inputs["Metallic"].default_value = 0.0
    material.diffuse_color = linear(COLOURS.get(colour, colour))  # the viewport colour, used for the portrait
    return material


def export(dino_id, spec):
    bpy.ops.wm.open_mainfile(filepath=spec["blend"])
    scene = bpy.context.scene
    arm = bpy.data.objects["Armature"]
    mesh = bpy.data.objects[spec["mesh"]]

    # Keep only the dino.
    for obj in list(bpy.data.objects):
        if obj not in (arm, mesh):
            bpy.data.objects.remove(obj, do_unlink=True)

    # Signature colours.
    for slot in mesh.material_slots:
        base = slot.material.name.split(".")[0]
        slot.material = flat_material(f"{dino_id}_{base}", spec["materials"].get(base, "trimWhite"))

    # Measure in the rest pose, then scale to game size and stand it on the origin.
    arm.data.pose_position = "REST"
    bpy.context.view_layer.update()
    evaluated = mesh.evaluated_get(bpy.context.evaluated_depsgraph_get())
    points = [evaluated.matrix_world @ v.co for v in evaluated.to_mesh().vertices]
    lo = Vector([min(p[i] for p in points) for i in range(3)])
    hi = Vector([max(p[i] for p in points) for i in range(3)])
    scale = spec["height"] / (hi.z - lo.z) if "height" in spec else spec["length"] / (hi.y - lo.y)
    arm.data.pose_position = "POSE"

    root = bpy.data.objects.new(f"DINO_{dino_id}", None)
    scene.collection.objects.link(root)
    arm.parent = root
    root.scale = (scale, scale, scale)
    root.location = (0, 0, -lo.z * scale)
    root["id"] = dino_id
    root["length"] = (hi.y - lo.y) * scale
    root["height"] = (hi.z - lo.z) * scale
    root["width"] = (hi.x - lo.x) * scale

    # A render to redraw its sticker from (scripts/art.mjs), mid-idle, before the animations are rearranged.
    idle = bpy.data.actions.get(spec["prefix"] + "Idle")
    if idle:
        arm.animation_data.action = idle
        if idle.slots:
            arm.animation_data.action_slot = idle.slots[0]
        scene.frame_set(int(idle.frame_range[0]) + 12)
    scene_lib.render_preview(
        os.path.join(REPO, "art", "refs", f"dino-{dino_id}.webp"),
        pitch_deg=14,
        yaw_deg=-48,
        resolution=(640, 520),
        transparent=True,
        only=[mesh],
        margin=1.04,
        light="STUDIO",
        colour="MATERIAL",
    )

    # One NLA track per clip, named as the game expects.
    arm.animation_data.action = None
    for track in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(track)
    for suffix, clip in CLIPS.items():
        action = bpy.data.actions.get(spec["prefix"] + suffix)
        if not action:
            print(f"[dinos] {dino_id}: no action {spec['prefix'] + suffix}")
            continue
        track = arm.animation_data.nla_tracks.new()
        track.name = clip
        strip = track.strips.new(clip, int(action.frame_range[0]), action)
        strip.name = clip

    out = os.path.join(REPO, "public", "models", "dinos", f"{dino_id}.glb")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=out,
        export_format="GLB",
        export_yup=True,
        export_extras=True,
        export_skins=True,
        export_animations=True,
        export_animation_mode="NLA_TRACKS",
        export_force_sampling=True,
        export_materials="EXPORT",
        export_cameras=False,
        export_lights=False,
    )
    print(
        f"[dinos] {dino_id}: scale={scale:.3f} length={root['length']:.1f} height={root['height']:.1f} "
        f"width={root['width']:.1f} -> {os.path.relpath(out, REPO)}"
    )


if __name__ == "__main__":
    for dino_id, spec in DINOS.items():
        export(dino_id, spec)
