"""Build levels: generate buildings and props, export the GLB, draw the playmat, render previews.

    blender --background --factory-startup --python assets-src/build_level.py -- --level block-town
    blender --background --factory-startup --python assets-src/build_level.py -- --level all
"""

import argparse
import importlib
import math
import os
import shutil
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, HERE)

from lib import palette, scene as scene_lib  # noqa: E402
from textures import detail, playmat  # noqa: E402

LEVELS = ["block-town", "playground-park", "farm", "forest", "castle-hill"]
LEVEL_TRIANGLE_BUDGET = 80_000
# Extra per-entry fields from the layout that the game reads.
PASS_THROUGH = ("objective", "order", "run", "speed", "yaw", "secret")


def generator(type_name):
    for package in ("buildings", "props"):
        try:
            return importlib.import_module(f"{package}.{type_name}")
        except ModuleNotFoundError as error:
            if error.name != f"{package}.{type_name}":
                raise
    raise SystemExit(f"No generator for {type_name!r} in buildings/ or props/")


def build(level_id):
    layout = importlib.import_module(f"levels.{level_id.replace('-', '_')}").layout()
    scene_lib.reset()
    scene = bpy.context.scene

    total = 0
    modules = 0
    by_id = {}
    for entry in layout["buildings"] + layout["props"]:
        empty, stats = generator(entry["type"]).build(entry["id"], entry["seed"], entry.get("scheme"))
        if entry.get("scale", 1) != 1:
            # Baked into the meshes, so the game's physics shapes come out the right size too.
            # A bigger thing costs no more triangles.
            grow = Matrix.Scale(entry["scale"], 4)
            for child in empty.children:
                child.data.transform(grow)
                child.location = child.location * entry["scale"]
        if "kind" in entry:
            empty["kind"] = entry["kind"]
        if "route" in entry:
            # A custom property can only hold a flat list: x0, y0, x1, y1...
            empty["route"] = [float(v) for point in entry["route"] for v in point]
        empty.location = (entry["pos"][0], entry["pos"][1], 0)
        empty.rotation_euler = (0, 0, math.radians(entry.get("rot", 0)))
        for key in PASS_THROUGH:
            if key in entry:
                empty[key] = entry[key]
        total += stats["triangles"]
        modules += stats["modules"]
        by_id[entry["id"]] = empty

    spawn = bpy.data.objects.new("SPAWN_dino", None)
    spawn.location = (layout["spawn"][0], layout["spawn"][1], 0)
    scene.collection.objects.link(spawn)

    level = bpy.data.objects.new("LEVEL", None)
    scene.collection.objects.link(level)
    level["id"] = layout["id"]
    level["size"] = layout["size"]
    if layout.get("pool"):
        level["pool"] = [float(v) for v in layout["pool"]]

    over = " OVER level budget" if total > LEVEL_TRIANGLE_BUDGET else ""
    print(
        f"[level] {level_id}: {len(layout['buildings'])} buildings, {len(layout['props'])} props, "
        f"{modules} modules, {total} triangles{over}"
    )

    model = os.path.join(REPO, "assets-out", "models", f"{level_id}.glb")
    atlas = os.path.join(REPO, "assets-out", "textures", "atlas.png")
    ground = os.path.join(REPO, "assets-out", "textures", f"{level_id}-ground.png")
    scene_lib.export_glb(model)
    palette.save_atlas(atlas)
    # Footprints of the real buildings (not street furniture), for their ground shadows.
    bpy.context.view_layer.update()
    footprints = []
    for entry in layout["buildings"]:
        xs, ys = [], []
        for child in by_id[entry["id"]].children:
            for corner in child.bound_box:
                world = child.matrix_world @ Vector(corner)
                xs.append(world.x)
                ys.append(world.y)
        footprints.append((min(xs), min(ys), max(xs), max(ys)))
    ground_image = playmat.draw(layout, ground, footprints)
    detail_path = os.path.join(REPO, "assets-out", "textures", "detail.png")
    detail.build(detail_path)

    for source, folder in ((model, "models"), (atlas, "textures"), (ground, "textures"), (detail_path, "textures")):
        target = os.path.join(REPO, "public", folder)
        os.makedirs(target, exist_ok=True)
        shutil.copy2(source, target)

    # --- previews and interface art (the ground is added after export, so it stays out of the GLB) ---
    size = layout["size"]
    bpy.ops.mesh.primitive_plane_add(size=size)
    plane = bpy.context.active_object
    plane.name = "GROUND"
    material = bpy.data.materials.new("Playmat")
    material.use_nodes = True
    bsdf = next(n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    texture = material.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = ground_image
    material.node_tree.links.new(texture.outputs["Color"], bsdf.inputs["Base Color"])
    plane.data.materials.append(material)

    previews = os.path.join(REPO, "assets-out", "previews")
    scene_lib.render_preview(os.path.join(previews, f"{level_id}_top.png"), pitch_deg=89.9, resolution=(1400, 1400), margin=1.0)
    scene_lib.render_preview(os.path.join(previews, f"{level_id}_angled.png"), pitch_deg=50)

    ui = os.path.join(REPO, "public", "ui")
    os.makedirs(ui, exist_ok=True)
    scene_lib.render_preview(os.path.join(ui, f"level-{level_id}.webp"), pitch_deg=42, yaw_deg=-28, resolution=(720, 720), margin=0.62)
    for name, ids in layout.get("icons", {}).items():
        objects = [child for i in ids if i in by_id for child in by_id[i].children]
        if objects:
            scene_lib.render_preview(
                os.path.join(ui, f"icon-{name}.webp"), pitch_deg=24, yaw_deg=-32, resolution=(360, 360), transparent=True, only=objects, margin=1.08
            )


def main():
    argv = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--level", default="all")
    args = parser.parse_args(argv)
    for level_id in LEVELS if args.level == "all" else [args.level]:
        build(level_id)


if __name__ == "__main__":
    main()
