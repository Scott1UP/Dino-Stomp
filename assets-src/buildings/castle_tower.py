"""Castle wall tower generator.

A tall SQUARE stone tower, 5 m by 5 m and 13-17 m tall, to stand along the
castle walls between the round turrets. Four storeys of four walls each, with
a white band at every floor, a guard's door and a torch at the back, slits,
arched windows and a banner. The seed picks the top: a bright pitched roof
(pyramid or gable), a wooden hoarding gallery hanging out all round under a
bright roof, or battlements. It also varies the storey height, the foot (a
sloped plinth or a step), the slits and windows, and the banner and flag.

Run directly to render the preview sheets:

    blender --background --factory-startup --python assets-src/buildings/castle_tower.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib import palette  # noqa: E402
from lib import shapes_castle2 as castle  # noqa: E402
from lib import shapes_parkcastle as shapes  # noqa: E402
from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402

TYPE = "castle_tower"
HITS_TO_COLLAPSE = 2  # medium building
TRIANGLE_BUDGET = 900

HALF = 2.5  # 5 m square
WALL = 0.5
STOREYS = 4
TOPS = ("roof", "hoarding", "battlements")
BRIGHTS = castle.BRIGHTS
ROOFS = castle.ROOFS


def build(building_id, seed, scheme=None, collection=None):
    """Build one wall tower. Returns (empty, stats)."""
    rng = random.Random(seed)

    storey_h = rng.choice([3.0, 3.2, 3.4])
    top_style = TOPS[(seed + rng.choice([0, 0, 1])) % len(TOPS)]  # mostly cycled, so neighbouring seeds differ
    roof_shape = rng.choice(["pyramid", "pyramid", "gable"])
    roof_rise = rng.choice([2.8, 3.3])
    roof_colour = rng.choice(ROOFS)
    base_style = rng.choice(["batter", "foot"])
    slit_style = rng.choice(["cross", "plain"])
    top_windows = rng.random() < 0.6
    banner_colour = rng.choice(BRIGHTS)
    flag_colour = rng.choice(BRIGHTS)
    flag_shape = rng.choice(["pennant", "banner"])
    seeded_scheme = rng.choice(palette.SCHEME_NAMES)  # always drawn, so the layout's scheme never shifts the seed
    scheme = scheme or seeded_scheme

    building = Building(building_id, TYPE, seed, scheme, HITS_TO_COLLAPSE, collection)
    add = building.add

    height = STOREYS * storey_h
    frames = castle.rect_frames(0, 0, HALF, HALF)
    names = ("front", "back", "left", "right")

    # --- walls: four a storey ---
    below = None
    storeys = []
    for s in range(STOREYS):
        z0 = s * storey_h
        z1 = z0 + storey_h
        grow = 0.18 if s == 0 and base_style == "foot" else 0.0
        v = grow + 0.04
        here = {}
        for name in names:
            frame = frames[name]
            wide = name in ("front", "back")
            kit = Kit()
            castle.box_wall(kit, frame, name, HALF, HALF, z0, z1, WALL, grow=grow, skip=("-z",) if s == 0 else ())
            if s == 0:
                if base_style == "batter":
                    reach = HALF + 0.5 if wide else HALF
                    castle.batter(kit, frame, -reach, reach, 0, 1.7, 0.5, "stone")
                if name == "back":
                    # The guard's door stands in a little porch, with a torch beside it.
                    shapes.fbox(kit, frame, (-0.75, grow, 0), (0.75, 0.62, 2.3), "doorBrown", skip=("-v", "-z"), sides={"-u": "stone", "+u": "stone", "+z": "trimWhite"})
                    castle.torch(kit, frame, 1.55, 2.0, v=grow)
                elif name == "front":
                    castle.shield(kit, frame, 0, storey_h - 0.15, 1.0, banner_colour, "trimWhite", v=v + 0.03)
            elif s == 2 and name == "front":
                pass  # the banner hangs here
            elif s == STOREYS - 1 and top_style == "hoarding":
                shapes.slit(kit, frame, z0 + 0.35, z0 + 1.6, cross=slit_style == "cross", v=v)  # the gallery covers the rest
            elif s == STOREYS - 1 and top_windows:
                castle.arched_window(kit, frame, -0.55, 0.55, z0 + 0.6, z0 + 2.2, v=v)
            elif s == 2 and name == "back":
                castle.arched_window(kit, frame, -0.55, 0.55, z0 + 0.6, z0 + 2.2, v=v)
            else:
                shapes.slit(kit, frame, z0 + 0.7, z0 + 2.2, cross=slit_style == "cross", v=v)
            supports = (below[name],) if below else ()
            here[name] = add(kit, "wall", "stone", s, supports=supports, collider="hull" if s == 0 and base_style == "batter" else "box")
        below = here
        storeys.append(here)

        # A floor slab that pokes out as a white band.
        if s < STOREYS - 1:
            kit = Kit()
            kit.box((-HALF - 0.12, -HALF - 0.12, z1 - 0.22), (HALF + 0.12, HALF + 0.12, z1), "trimWhite", sides={"+z": "interiorCream", "-z": "interiorCream"})
            add(kit, "floor", "wood", s + 1, supports=list(here.values()))

    top_walls = list(storeys[-1].values())

    # --- the banner on the front ---
    kit = Kit()
    z_top = 3 * storey_h - 0.45
    shapes.banner(kit, frames["front"], 0, z_top, 1.5, 2.6, banner_colour)
    shapes.fquad(kit, frames["front"], -0.38, 0.38, z_top - 1.45, z_top - 0.7, 0.09, "trimWhite")
    add(kit, "detail", "wood", 2, supports=(storeys[2]["front"],))

    # --- the top ---
    over = {"roof": 0.25, "hoarding": 0.0, "battlements": 0.4}[top_style]
    edge = HALF + over
    deck_z = height + 0.35
    kit = Kit()
    if top_style == "battlements":
        # Corbelled out: a flared stone course under the white deck.
        kit.convex(
            [[(sx * HALF, sy * HALF, height - 0.55) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]]
            + [
                [(a * HALF, b * HALF, height - 0.55), (c * HALF, d * HALF, height - 0.55), (c * edge, d * edge, height), (a * edge, b * edge, height)]
                for (a, b), (c, d) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1)))
            ],
            "stone",
        )
    kit.box((-edge, -edge, height), (edge, edge, deck_z), "trimWhite", sides={"-z": "interiorCream"})
    deck = add(kit, "floor", "stone", STOREYS, supports=top_walls, collider="hull" if top_style == "battlements" else "box")
    top_frames = castle.rect_frames(0, 0, edge, edge)
    crown = [deck]
    flag_z = deck_z

    def roof(reach, base_z, supports):
        rise = min(roof_rise, 17.0 - base_z)
        kit = Kit()
        if roof_shape == "pyramid":
            castle.pyramid(kit, 0, 0, reach, reach, base_z, rise, roof_colour)
        else:
            kit.extrude_x([(-reach, base_z), (reach, base_z), (0, base_z + rise)], -reach, reach, roof_colour, colours={0: "trimWhite", 1: "trimWhite"})
        return [add(kit, "roof", "stone", STOREYS + 1, supports=supports, collider="hull")], base_z + rise - 0.4

    if top_style == "battlements":
        row = castle.merlon_spans(-edge, edge, 3)
        for name, side_name in (("front", "left"), ("back", "right")):
            kit = Kit()
            castle.merlons(kit, top_frames[name], row, 1.0, deck_z, 1.2)
            castle.merlons(kit, top_frames[side_name], row[1:2], 1.0, deck_z, 1.2)
            add(kit, "detail", "stone", STOREYS, supports=(deck,))
    elif top_style == "roof":
        crown, flag_z = roof(edge + 0.4, deck_z, (deck,))
    else:
        # A timber gallery hanging out all round, with shooting slots, under the roof.
        out = 0.95
        z0, z1 = height - 1.4, deck_z + 0.95
        gallery = []
        for name in names:
            frame = frames[name]
            reach = HALF + out if name in ("front", "back") else HALF - 0.3
            kit = Kit()
            shapes.fbox(kit, frame, (-reach, -0.3, z0), (reach, out, z1), "wood", sides={"-z": "doorBrown"})
            for u in (-1.5, 0.0, 1.5):
                shapes.fquad(kit, frame, u - 0.45, u + 0.45, z0 + 1.25, z0 + 1.75, out + 0.03, "windowBlue")
            shapes.fquad(kit, frame, -reach, reach, z0, z0 + 0.3, out + 0.03, "doorBrown")
            shapes.fquad(kit, frame, -reach, reach, z1 - 0.3, z1, out + 0.03, "doorBrown")
            gallery.append(add(kit, "detail", "wood", STOREYS, supports=(storeys[-1][name],)))
        crown, flag_z = roof(HALF + out + 0.45, z1, gallery)

    kit = Kit()
    shapes.flag(kit, 0, 0, flag_z, 3.0, flag_colour, size=1.7, shape=flag_shape, thick=0.09)
    add(kit, "detail", "wood", STOREYS + 2, supports=crown)

    return building.finish(
        look=f"storey={storey_h} {top_style}/{roof_shape}/{roof_colour}/base-{base_style}/slits-{slit_style}" + ("/windows" if top_windows else "")
    )


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=(12, 0), columns=6)


if __name__ == "__main__":
    previews()
