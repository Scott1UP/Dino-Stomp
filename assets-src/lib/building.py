"""Shared scaffolding for building and prop generators.

A generator makes one `Building`, adds modules to it (each built with a
`meshkit.Kit`), and calls `finish()`. Everything the game needs to break the
building apart is recorded as custom properties, which the glTF exporter
writes out as extras.
"""

import os

import bpy

from . import palette, scene as scene_lib

MODULE_BUDGET = 80


class Building:
    """One building, or one prop.

    kind:
      "building"   a normal building: fixed until hit, then comes apart
      "prop"       street furniture: never blocks the dino, knocked over by walking into it
      "crate"      a prop that may hold a golden egg
      "domino"     stands as a loose physics body from the start, never breaks
      "ball"       a loose ball, never breaks
      "block"      loose toy blocks: every module is its own physics body from the start, so stacks tumble
      "giantTower" only its pillars can be hit; when they are gone it tips over whole
    """

    def __init__(self, building_id, type_name, seed, scheme, hits_to_collapse, collection=None, kind="building"):
        self.id = building_id
        self.type = type_name
        self.seed = seed
        self.scheme = scheme
        self.collection = collection or bpy.context.scene.collection
        self.modules = []

        self.empty = bpy.data.objects.new(f"BLD_{building_id}", None)
        self.collection.objects.link(self.empty)
        self.empty["id"] = building_id
        self.empty["type"] = type_name
        self.empty["seed"] = seed
        self.empty["scheme"] = scheme or ""
        self.empty["hitsToCollapse"] = hits_to_collapse
        self.empty["kind"] = kind

    def add(self, kit, role, material, storey, supports=(), collider="box"):
        """Add a module and return its id, for other modules to name as a support.

        role:     wall | corner | floor | band | roof | detail | pillar
        material: plaster | tile | wood | glass | tin | stone | rubber | leaves (picks the sound)
        storey:   0 is the ground floor
        supports: ids of the modules holding this one up; it falls when all of them are gone
        collider: "box", or "hull" for sloped or round pieces
        """
        module_id = f"MOD_{self.id}_{len(self.modules)}"
        obj = kit.to_object(module_id, self.collection, detail=material)
        obj.parent = self.empty
        obj["id"] = module_id
        obj["buildingId"] = self.id
        obj["role"] = role
        obj["material"] = material
        obj["storey"] = storey
        obj["supports"] = ",".join(s for s in supports if s)
        obj["collider"] = collider
        self.modules.append({"id": module_id, "triangles": kit.triangles()})
        return module_id

    def finish(self, look=""):
        """Returns (empty, stats)."""
        return self.empty, {
            "id": self.id,
            "type": self.type,
            "seed": self.seed,
            "scheme": self.scheme,
            "look": look,
            "modules": len(self.modules),
            "triangles": sum(m["triangles"] for m in self.modules),
            "largestModule": max(m["triangles"] for m in self.modules),
        }


def report(stats, budget):
    flags = []
    if stats["triangles"] > budget:
        flags.append(f"OVER budget ({budget})")
    if stats["largestModule"] > MODULE_BUDGET:
        flags.append(f"OVER module budget ({MODULE_BUDGET})")
    print(
        f"[{stats['type']}] {stats['id']} seed={stats['seed']} scheme={stats['scheme']} {stats['look']} "
        f"modules={stats['modules']} triangles={stats['triangles']} largest={stats['largestModule']} "
        + " ".join(flags)
    )


def previews(type_name, build, budget, spacing=(36, 40), seeds=6, columns=3):
    """Render the contact sheets (front and back) and the silhouette sheet for one type."""
    scene_lib.reset()
    for index in range(seeds):
        seed = index + 1
        empty, stats = build(f"preview{seed}", seed)
        empty.location = ((index % columns - (columns - 1) / 2) * spacing[0], -(index // columns) * spacing[1], 0)
        report(stats, budget)

    out = os.path.join(palette.ROOT, "..", "assets-out", "previews")
    scene_lib.render_preview(os.path.join(out, f"{type_name}_contact.png"), pitch_deg=35, yaw_deg=-35)
    scene_lib.render_preview(os.path.join(out, f"{type_name}_contact_back.png"), pitch_deg=35, yaw_deg=145)
    scene_lib.render_preview(os.path.join(out, f"{type_name}_silhouette.png"), pitch_deg=30, yaw_deg=-35, silhouette=True)
