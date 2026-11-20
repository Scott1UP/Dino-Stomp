"""Small helpers for writing level layouts.

Coordinates are Blender's: X east, Y north, in metres. A building's front
faces -Y (south) at rot 0, so `rot` turns it anticlockwise seen from above:
180 faces north, 90 faces east, -90 faces west.
"""

import math

SCHEMES = ["postbox", "custard", "seaside", "marmalade", "candyfloss", "sunset", "bluebell", "lemonade"]


class Layout:
    def __init__(self, level_id, size, spawn, base="ground"):
        self.data = {
            "id": level_id,
            "size": size,
            "spawn": list(spawn),
            "base": base,
            "buildings": [],
            "props": [],
            "roads": [],
            "junctions": [],
            "crossings": [],
            "grass": [],
            "paths": [],
            "paved": [],
            "icons": {},
        }
        self._count = {}
        self._scheme = 0

    def _id(self, type_name):
        self._count[type_name] = self._count.get(type_name, 0) + 1
        return f"{type_name}{self._count[type_name]}"

    def building(self, type_name, x, y, rot=0, seed=None, scheme=None, objective=None, **extra):
        """Add a building. Schemes rotate so neighbours never share one."""
        if scheme is None:
            scheme = SCHEMES[self._scheme % len(SCHEMES)]
            self._scheme += 3  # step by 3 so consecutive buildings look well apart
        entry = {
            "id": self._id(type_name),
            "type": type_name,
            "seed": seed if seed is not None else self._count[type_name],
            "scheme": scheme,
            "pos": [x, y],
            "rot": rot,
        }
        if objective:
            entry["objective"] = objective
        entry.update(extra)
        self.data["buildings"].append(entry)
        return entry["id"]

    def prop(self, type_name, x, y, rot=0, seed=None, objective=None, **extra):
        entry = {
            "id": self._id(type_name),
            "type": type_name,
            "seed": seed if seed is not None else self._count[type_name],
            "pos": [x, y],
            "rot": rot,
        }
        if objective:
            entry["objective"] = objective
        entry.update(extra)
        self.data["props"].append(entry)
        return entry["id"]

    def line(self, type_name, a, b, spacing, rot=0, skip=()):
        """Props evenly spaced from a to b. `skip` is a list of (x, y, radius) to leave clear."""
        (ax, ay), (bx, by) = a, b
        length = math.hypot(bx - ax, by - ay)
        count = max(int(length // spacing), 1)
        for i in range(count + 1):
            x, y = ax + (bx - ax) * i / count, ay + (by - ay) * i / count
            if any(math.hypot(x - sx, y - sy) < sr for sx, sy, sr in skip):
                continue
            self.prop(type_name, x, y, rot)

    def road(self, a, b, width=12):
        self.data["roads"].append({"a": list(a), "b": list(b), "width": width})


def squeeze(data, k):
    """Pull a whole layout in towards the centre by a factor k, so the map feels fuller.

    Positions move; the things themselves stay the same size.
    """
    data["size"] = round(data["size"] * k)
    data["spawn"] = [v * k for v in data["spawn"]]
    for entry in data["buildings"] + data["props"]:
        entry["pos"] = [v * k for v in entry["pos"]]
    for path in data["paths"]:
        path["points"] = [(x * k, y * k) for x, y in path["points"]]
    for patch in data["grass"] + data["paved"]:
        if "circle" in patch:
            x, y, r = patch["circle"]
            patch["circle"] = [x * k, y * k, r * k]
        else:
            patch["rect"] = [v * k for v in patch["rect"]]
    if data.get("pool"):
        x, y, r = data["pool"]
        data["pool"] = [x * k, y * k, r]
    return data
