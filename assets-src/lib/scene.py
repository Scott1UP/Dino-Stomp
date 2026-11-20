"""Scene reset, export and preview rendering."""

import math
import os

import bpy
from mathutils import Vector


def reset():
    """Start from an empty scene in metres."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    return scene


def export_glb(path):
    """Export the whole scene. Textures stay out: the atlas ships as its own file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=path,
        export_format="GLB",
        export_apply=True,
        export_extras=True,
        export_yup=True,
        export_texcoords=True,
        export_normals=True,
        export_materials="PLACEHOLDER",
        export_vertex_color="ACTIVE",
        export_all_vertex_colors=False,
        export_cameras=False,
        export_lights=False,
        export_animations=False,
    )


def _bounds(objects):
    lo = Vector((math.inf,) * 3)
    hi = Vector((-math.inf,) * 3)
    for obj in objects:
        if obj.type != "MESH":
            continue
        for corner in obj.bound_box:
            world = obj.matrix_world @ Vector(corner)
            lo = Vector(map(min, lo, world))
            hi = Vector(map(max, hi, world))
    return lo, hi


def _camera(scene, centre, size, pitch_deg, yaw_deg=0.0):
    """An orthographic camera looking at `centre`, `pitch_deg` below the horizon."""
    data = bpy.data.cameras.new("PreviewCamera")
    data.type = "ORTHO"
    data.ortho_scale = size
    data.clip_end = 2000
    camera = bpy.data.objects.new("PreviewCamera", data)
    scene.collection.objects.link(camera)

    pitch = math.radians(pitch_deg)
    yaw = math.radians(yaw_deg)
    distance = 500
    offset = Vector(
        (
            math.sin(yaw) * math.cos(pitch) * distance,
            -math.cos(yaw) * math.cos(pitch) * distance,
            math.sin(pitch) * distance,
        )
    )
    camera.location = centre + offset
    camera.rotation_euler = (centre - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera
    return camera


def render_preview(
    path,
    pitch_deg=50.0,
    yaw_deg=0.0,
    silhouette=False,
    resolution=(1600, 900),
    transparent=False,
    only=None,
    margin=1.12,
    light="FLAT",
    colour="TEXTURE",
):
    """Render every mesh in the scene with Workbench.

    `silhouette` draws solid black shapes on white, for the silhouette test.
    """
    scene = bpy.context.scene
    os.makedirs(os.path.dirname(path), exist_ok=True)

    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.film_transparent = transparent
    scene.render.image_settings.file_format = "WEBP" if path.endswith(".webp") else "PNG"
    scene.render.image_settings.color_mode = "RGBA" if transparent else "RGB"
    scene.display.shading.show_object_outline = transparent
    scene.display.shading.object_outline_color = (0.17, 0.18, 0.26)

    # `only` renders just those objects (for interface icons), hiding everything else.
    hidden = []
    if only is not None:
        keep = set(only)
        for obj in scene.objects:
            if obj not in keep and not obj.hide_render:
                obj.hide_render = True
                hidden.append(obj)
    scene.render.filepath = path
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0.9 if light == "STUDIO" and not silhouette else 0.0

    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.color = (1, 1, 1) if silhouette else (0.52, 0.76, 0.89)

    shading = scene.display.shading
    if silhouette:
        shading.light = "FLAT"
        shading.color_type = "SINGLE"
        shading.single_color = (0, 0, 0)
        shading.show_shadows = False
        shading.show_cavity = False
    else:
        shading.light = light
        shading.color_type = colour
        shading.show_shadows = False
        shading.show_cavity = False

    bpy.context.view_layer.update()  # world matrices, before measuring
    lo, hi = _bounds(only if only is not None else scene.objects)
    centre = (lo + hi) / 2
    aspect = resolution[0] / resolution[1]

    # Frame the bounding box as the tilted camera sees it, plus a margin.
    pitch = math.radians(pitch_deg)
    yaw = math.radians(yaw_deg)
    right = Vector((math.cos(yaw), math.sin(yaw), 0))
    up = Vector((-math.sin(yaw) * math.sin(pitch), math.cos(yaw) * math.sin(pitch), math.cos(pitch)))
    corners = [Vector((x, y, z)) - centre for x in (lo.x, hi.x) for y in (lo.y, hi.y) for z in (lo.z, hi.z)]
    seen_width = 2 * max(abs(c.dot(right)) for c in corners)
    seen_height = 2 * max(abs(c.dot(up)) for c in corners)
    size = max(seen_width, seen_height * aspect) * margin

    camera = _camera(scene, centre, size, pitch_deg, yaw_deg)
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(camera)
    for obj in hidden:
        obj.hide_render = False
