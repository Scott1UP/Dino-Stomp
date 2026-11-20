"""Market umbrella generator.

A big striped street umbrella, about 4.6 m across, shading a little fruit
cart. Two modules: the umbrella and the cart. The seed picks the stripe
colours, the umbrella's size and pitch, and the fruit piled on the cart.

    blender --background --factory-startup --python assets-src/props/market_umbrella.py
"""

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.building import Building, previews as building_previews, report as building_report  # noqa: E402
from lib.meshkit import Kit  # noqa: E402
from lib.shapes_props import BRIGHT, apothem, prism  # noqa: E402

TYPE = "market_umbrella"
KIND = "prop"
TRIANGLE_BUDGET = 150
SPACING = (8, 8)

SIDES = 8
FRUIT = ("tomato", "sunny", "leaf", "tangerine", "bubblegum")


def build(building_id, seed, scheme=None, collection=None):
    """Build one umbrella and cart. Returns (empty, stats). `scheme` is ignored."""
    rng = random.Random(seed)
    stripe = BRIGHT[seed % len(BRIGHT)]  # cycled, so neighbouring seeds always differ
    other = rng.choice(["trimWhite", "trimWhite", "sunny" if stripe != "sunny" else "tomato"])
    radius = rng.choice([2.1, 2.3, 2.5])
    pitch = rng.choice([0.7, 1.0, 1.3])
    pole_side = rng.choice([-1, 1])
    fruit = rng.sample(FRUIT, 3)
    cart = rng.choice(["wood", "cobalt", "tomato"])

    building = Building(building_id, TYPE, seed, None, 1, collection, kind=KIND)

    # --- the umbrella: its pole stands beside the cart ---
    px = pole_side * 1.35
    rim = 2.75
    kit = Kit()
    prism(kit, (px, 0), 0, 0.3, 0.42, 0.34, 6, "stone", bottom=False)
    prism(kit, (px, 0), 0.3, rim + pitch, 0.13, 0.13, 6, "wood", bottom=False, top=False)
    prism(kit, (px, 0), rim, rim + pitch, radius, 0.0, SIDES, stripe, side_colours=[stripe, other], bottom=False)
    prism(kit, (px, 0), rim - 0.3, rim, radius, radius, SIDES, stripe, side_colours=[other, stripe], bottom=False, top=False)
    # The underside, so it is not see-through from below.
    under = Kit()
    prism(under, (px, 0), rim, rim + pitch - 0.05, radius - 0.02, 0.0, SIDES, "interiorCream", bottom=False)
    for points, colour in under.faces:
        kit.faces.append((list(reversed(points)), colour))
    prism(kit, (px, 0), rim + pitch - 0.05, rim + pitch + 0.4, 0.2, 0.0, 4, "sunny", bottom=False)
    building.add(kit, "detail", "wood", 0, collider="hull")

    # --- the fruit cart ---
    wheel_r = 0.42
    wheel_z = apothem(wheel_r, 6)
    kit = Kit()
    kit.box((-1.0, -0.6, 0.6), (1.0, 0.6, 1.05), cart, skip=("+z",))
    # Three trays of fruit side by side cover the top.
    for i, colour in enumerate(fruit):
        xa = -1.0 + i * 2 / 3
        hidden = ("-z",) + (("-x",) if i > 0 else ()) + (("+x",) if i < 2 else ())
        kit.box((xa, -0.6, 1.05), (xa + 2 / 3, 0.6, 1.36), colour, skip=hidden)
    for sy in (-1, 1):
        ya, yb = sorted((sy * 0.62, sy * 0.8))
        prism(kit, (-0.2, wheel_z), ya, yb, wheel_r, wheel_r, 6, "tyre", axis="y", bottom=sy < 0, top=sy > 0)
    kit.box((-1.6, -0.5, 0.85), (-1.0, 0.5, 0.99), "wood", skip=("+x",))  # the push bar
    building.add(kit, "detail", "wood", 0, collider="hull")

    return building.finish(look=f"{stripe}/{other} r={radius} pitch={pitch} pole{pole_side:+d} cart={cart} fruit={'+'.join(fruit)}")


def report(stats):
    building_report(stats, TRIANGLE_BUDGET)


def previews():
    building_previews(TYPE, build, TRIANGLE_BUDGET, spacing=SPACING)


if __name__ == "__main__":
    previews()
