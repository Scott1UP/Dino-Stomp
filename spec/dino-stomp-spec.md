# Dino Stomp — spec

A toy-box destruction game for a young child. He picks a T. rex, triceratops or ankylosaurus and stomps through a bright, low-poly toy town where everything breaks in satisfying, noisy, physics-driven ways.

There are two modes: **story mode** (three levels with two objectives each) and **sandbox mode** (endless smashing).

---

## Principles

1. **Toy-box chaos, never real destruction.** The town is a toy playset. Smashing it should feel like knocking over a block tower: joyful, loud and harmless. There are no people, no fire, no smoke and no sharp shattering glass.
2. **Bright means smashable.** Anything in a saturated toy colour can be broken. The world around it (ground, hills, edges) uses soft colours and can't be broken.
3. **No failing and no timers.** He works through objectives at his own pace, in any order.
4. **Every objective works with every dino.** Some dinos are faster or more fun for certain objectives, but none is ever required.
5. **No reading needed.** Objectives, progress and prompts use pictures, markers, sound and voice clips.
6. **Tablet first.** Touch controls, steady frame rate during big collapses, and short load times.
7. **The interface is part of the game.** It must feel childlike and be genuinely easy for him. He should get from the title screen to stomping, and back, without help (see "Interface design").
8. **Mistakes are harmless.** An accidental tap on pause, home or a different dino never costs him anything.

## Scope

### In the first build

- Story mode: 3 levels, 2 objectives each.
- Sandbox mode: endless, on any of the 3 level maps.
- 3 dinos, each with its own signature move.
- A procedural building kit with 9 building types and a set of street props.
- Physics-driven breaking, in which buildings come apart along their architectural lines.
- The full audio design: layered breaks, dino sound sets, adaptive music.
- A childlike interface, designed for him and tested with him early.
- Textures and 2D art: interface art and small details from GPT Image, and a script-drawn playmat ground.
- Progress saved on the device.

### Out of scope (see "Later")

- Hidden secrets in each level and the secret finale.
- Beach, farm and forest settings.
- More dinos.

---

## Modes

### Story mode

- Levels unlock in order (Block Town → Playground Park → Castle Hill), and any unlocked level can be replayed.
- A level starts with its **two objective cards**: big pictures, with a voice clip explaining each one.
- The top of the screen shows progress for both objectives as icons, such as three tower icons that fill in.
- Objectives can be done **in any order**, and there's **no timer**.
- When both are done, there's a celebration (confetti, fanfare and a dino roar) and two buttons: **keep stomping** (stay in the level) and **next level**.

### Sandbox mode

- Pick a dino, then a map. All three maps are available from the start (open decision).
- No objectives and no end.
- **Rebuild:**
  - Once about 80% of the town is destroyed, it rebuilds itself. Buildings pop back up one by one with a springy "boing", spreading outwards from the dino.
  - A rebuild button does the same whenever he likes.
- The dino can be swapped at any time from the pause menu.

### Saving

Story progress (levels unlocked and completed) is a few flags kept in `localStorage`.

**Why localStorage:** it's a handful of small values, and `localStorage` is simple and synchronous. (Dino Safari needed IndexedDB for photos. Nothing here needs it.)

---

## Dinos

| | T. rex | Triceratops | Ankylosaurus |
|---|---|---|---|
| Size | Tall (about 1.5× a two-storey house) | Medium-long | Low and wide |
| Speed | Medium | Fast | Slow |
| Signature move | **Stomp**: a ground pound with a circular shockwave | **Charge**: dashes about 8 m forwards, ploughing through everything | **Tail swing**: spins once, sweeping a full circle |
| How it breaks things | **Area**: everything within the shockwave is knocked up and outwards | **Line**: breaks through a row of things and keeps going until it hits something big, then bounces back | **Launch**: knocks things a long way, so they crash into other things and start chain reactions |
| Best at | Toppling towers, big collapses | Walls, rows of houses, fences | Knocking things into targets, chain reactions |
| Signature colour | T. rex green `#3FA34D` | Triceratops purple `#7B5CC9` | Ankylosaurus teal `#1FA2A0` |

Shared behaviour:

- Walking into small props (fences, bins, benches, lamp posts) knocks them over without slowing down.
- Every dino plays a roar on the select screen and when a level is completed.
- Animations: idle, walk, run, signature move, celebrate and roar. The triceratops's charge uses its run.

---

## Controls

| Action | Input | Notes |
|---|---|---|
| Move | **Thumbstick**, bottom-left | A floating stick: it appears wherever his thumb lands in the bottom-left area. **Why:** small children don't hit a fixed stick accurately. |
| Signature move | **Smash button**, bottom-right | At least 96 pt. Uses the move in the direction the dino is facing. |
| Walk somewhere | **Tap the ground** | The dino walks there in a straight line. |
| Attack something | **Tap a building or prop** | The dino walks into range and uses its signature move. Tapping again repeats it. |
| Pause | Tap the pause button, top-right | One tap, no hold. Pausing by accident does no harm: resume is the biggest button in the pause menu. |
| Keyboard (for testing) | WASD or arrow keys, Space | |

Rules:

- **The thumbstick always wins.** Touching it cancels any walk or attack he started by tapping.
- **Straight lines, no pathfinding.** If a building is in the way of a tapped destination, the dino smashes through it with its signature move and carries on. **Why:** it fits the fantasy, everything really is in the way, and it means the game needs no pathfinding.
- **Tap targeting:** a raycast from the tap finds what he tapped. A building or prop means attack, and the ground means walk. The hit area is enlarged by 20% for small fingers.
- **The camera follows the dino automatically** from a fixed high, angled view, with no camera controls. **Why:** a toddler has enough to manage with moving and smashing, and a fixed angle keeps the town readable.

---

## Interface design

The interface gets as much care as the gameplay. He struggled a little with the interface in the last game, so this one is designed around how a small child actually uses a tablet, and tested with him before the polish stage (see milestone M1).

### What it should feel like

It should feel like a toy: chunky rounded shapes, thick outlines, bright palette colours, and buttons that look like moulded plastic buttons with depth and a shadow underneath. Everything bounces, squashes and makes a noise. Nothing looks like an app or a settings page, except the parent settings.

### Rules

| Rule | Spec | Why |
|---|---|---|
| **Big targets** | Main buttons at least 96 pt, other buttons at least 72 pt, at least 24 pt apart | Small fingers land imprecisely, and often more than one finger touches. Apple's 44 pt minimum is sized for adults. |
| **Few choices** | At most 3–4 options per screen, with one obvious main action that's bigger than the rest and gently pulses | Too many equal-looking choices is the most common way toddlers get stuck |
| **No reading** | Pictures and icons only. Every button **says its name aloud** when tapped ("T. rex!", "Castle Hill!") | Hearing it confirms what he chose, and teaches the icons |
| **Instant feedback** | Buttons squash and click the moment a finger touches. The action happens when the finger lifts, and still counts if the finger slid off slightly. | Toddlers need to know right away that the screen heard them. Acting on lift stops resting fingers triggering things, and the forgiving lift area stops "it didn't work" moments. |
| **Every tap gets an answer** | Locked or unavailable things play a gentle "bonk" and wobble, never nothing | Silence reads as "broken", and he'll keep tapping or give up |
| **Same place, same job** | Back is always top-left, go is always bottom-right, pause is always top-right | Familiar positions let him use screens he hasn't learnt yet |
| **Short paths** | At most 3 taps from the title screen to stomping. The game remembers his last dino and level. | Every extra screen is a chance to get lost |
| **Mistakes are harmless** | No text confirmations. Leaving a level keeps its objective progress, so going back in continues where he was. Swapping dino mid-level keeps progress too. | Accidental taps will happen, and they should cost nothing |
| **Help when he pauses** | On a menu, after 5 s without input, the main button pulses harder and a voice prompt plays. In a level, after 10 s without input, an animated hand shows the thumbstick or a tap. | Shows him what to do without needing him to ask |
| **Away from the edges** | Menu buttons sit at least 32 pt in from the screen edges | Children grip tablets by the edges, and a resting thumb shouldn't press anything |

### Screens

1. **Title:** two huge buttons, Story (a flag and a T. rex) and Sandbox (a toy box), plus a small parent cog in the corner.
2. **Dino select:** three big cards with the dinos moving and roaring. **One tap chooses and continues** after the roar (about 1 s). **Why:** a separate "confirm" step is confusing at this age, and swapping dino later is easy from the pause menu.
3. **Level select:** three big level cards along a winding path, like a board game. Locked levels show a padlock, and completed levels get a big stamp. Sandbox uses the same cards, all unlocked.
4. **Objective intro:** the two objective cards fly in, a voice explains each one, then they shrink and fly into the progress icons at the top of the screen. **Why:** the animation shows him where his progress lives.
5. **In-game display:** only the thumbstick area, the smash button, pause and the two objectives' progress icons. Nothing else on screen.
6. **Pause menu:** a huge resume button, plus swap dino, rebuild (sandbox only) and home. The parent cog sits small in a corner.
7. **Level complete:** the celebration, then keep stomping and next level.
8. **Parent settings:** normal adult layout with text. Volume, music, screen shake, reset progress.

### How it's built

- **The interface is an HTML and CSS layer over the 3D canvas**, built with React, rather than drawn inside WebGL. **Why:** it's crisp at any resolution, easy to lay out, quick to iterate, and CSS animations are cheap.
- **Buttons are built in code** (CSS and SVG), not generated images. **Why:** they need to scale sharply, show pressed and locked states, and squash and bounce. Generated images can't do that, and they'd vary from button to button. GPT Image supplies the illustrations *inside* buttons and cards (see "Textures and 2D art").
- **Springy animations** with a spring library (such as `motion`) for presses, card flights and celebrations.
- **Block the browser's own gestures:** `touch-action: none` on the game, `user-select: none`, `-webkit-touch-callout: none`, `overscroll-behavior: none`, and double-tap zoom turned off. **Why:** a stray pinch, double tap or long press otherwise zooms the page, selects text or opens a menu. To a child, that looks like the game broke.
- **Landscape only:** the web app manifest locks the orientation. If the tablet is held upright anyway, a picture of a tablet turning sideways appears.

---

## Story levels

### Level 1: Block Town

A small toy town with terraced houses, shops, a block of flats and three landmark towers. It teaches moving, smashing and exploring.

| Objective | Completion | Best dino |
|---|---|---|
| **Knock over the 3 tall towers** (the clock tower, the water tower and the tall flats, each marked with a star) | Each tower counts once less than 30% of its main parts are still standing | T. rex |
| **Find the 3 golden eggs** hidden in crates | 8 crates around town, 3 with eggs inside. A broken crate pops its egg out with a sparkle. Walking into an egg collects it, and it flies up to the progress bar. Eggs can't be broken. | Any |

### Level 2: Playground Park

A park with a bandstand, a glasshouse, an ice cream kiosk, a café, playground equipment, a giant domino run and a paddling pool. It teaches chain reactions and aiming.

| Objective | Completion | Best dino |
|---|---|---|
| **Set off the giant domino run** that winds round the park | Completes when the last domino falls, however that happens. Standing dominoes can be hit to keep a stalled run going. **Help:** if a moving domino stops while still leaning, it gets a small push. **Why:** spacing and physics can stall a run, and the payoff must always happen. The last domino rings a big bell and fires confetti. | Any |
| **Knock 3 beach balls into the paddling pool** | A ball entering the pool splashes, floats and counts. The pool is a big target. A ball that leaves the map reappears where it started. | Ankylosaurus |

### Level 3: Castle Hill

A toy castle on a hill, with crenellated walls, round turrets, an open gatehouse, a giant tower standing on three pillars in the courtyard, and a few houses outside the walls. It's the finale, with the biggest collapse in the game.

| Objective | Completion | Best dino |
|---|---|---|
| **Smash the castle walls** | 6 marked wall sections, each counting when broken | Triceratops |
| **Bring down the giant tower** | Break its 3 support pillars, each taking 1–2 hits. When the last one goes, the tower tips over and breaks apart on landing. It always falls whichever way you've hit it, never towards the dino, and ends with fireworks. | T. rex |

**The gate is open,** so he can reach the tower without breaking the walls. That keeps the objectives doable in any order.

---

## Art direction

### Toy-box town

The town is a bright toy playset made of chunky plastic and wooden pieces, seen from above at an angle. The energy comes from saturated colour on breakable things, motion and impact effects. The world around them stays calm, so the chaos is always readable.

### Palette

| Role | Colours |
|---|---|
| Breakable | Tomato `#E8483B` · Sunny `#F7C531` · Cobalt `#2F6FD6` · Tangerine `#F28C28` · Bubblegum `#EE6FA8` |
| World (can't be broken) | Ground `#EADBB8` · Grass `#A9C48E` · Sky `#BFE3F2` · Stone `#9AA0A6` |
| Dinos (used nowhere else) | T. rex green `#3FA34D` · Triceratops purple `#7B5CC9` · Ankylosaurus teal `#1FA2A0` |
| Effects | Dust `#FFF4DC` · Star gold `#FFD84D` |
| Building extras | Trim white `#FFFDF6` · Window blue `#3B4F7A` · Window shine `#BFD3F2` · Interior cream `#F4E6CF` · Door brown `#8A5A3B` |

All colours live in **one shared atlas**, alongside the pattern tiles and details (see "Textures and 2D art").

### Shading and light

- **Flat-shaded low-poly models with `MeshToonMaterial`**, using a three-band gradient map. Set the gradient texture's filtering to `NearestFilter` with mipmaps turned off. **Why:** the default filtering smooths between bands and turns the crisp toy-like steps back into a soft gradient.
- **Lights:** one warm sun light that casts shadows, plus a cool fill light from the sky.
- **Camera:** high and angled, looking down at about 50°, following the dino.

### Making hits feel big

| Effect | Spec | Why |
|---|---|---|
| Hit-stop | Freeze everything for 40–80 ms on big hits (longer for bigger hits) | Makes impacts feel heavy |
| Squash and stretch | On the dino as it attacks, and on pieces as they land | Feels like a cartoon, and readable at a glance |
| Dust puffs | Simple low-poly spheres that expand and fade, drawn together in one batch (instanced) | Shows where the hit landed |
| Confetti | Bits in the building's own colours | Makes breaking feel like a reward |
| Ground ring | An expanding ring decal under stomps and big landings | Shows the area of a move |
| Screen shake | Small, quick to fade, and limited in strength. Can be turned off in parent settings. | Adds weight without being uncomfortable |
| Objective markers | A bouncing star above each target, plus a pulsing white outline | He never has to read anything to know what to smash |

---

## Building design

### Goals

1. **Every building reads as a building.** It's recognisable from its silhouette alone, never just a stack of boxes.
2. **Variety that feels believable.** A street looks like a real street, with different buildings that still make sense together.
3. **Buildings break into recognisable pieces.** They come apart into windows, roof halves, chimneys and floors, not random cubes.
4. **Low poly**, so a whole level stays well within a tablet's budget.

### Why things read as buildings

These rules apply to every building type:

| Rule | What it means | Why it works |
|---|---|---|
| **Base, middle, top** | The ground floor differs from the floors above (shopfront, front door, steps, plinth). The top has a roof, cornice or parapet. | This three-part structure is how real façades are organised, so the eye reads "building" straight away. |
| **The roof makes the silhouette** | Pitched, hipped, flat with a parapet, cone, dome or spire, with an overhang of 10–15% | The roof is the most recognisable part from a high camera angle. |
| **Depth catches the light** | Windows and doors set 10–15 cm into the wall, overhanging roofs, ledges between floors, and a small bevel on every outside edge | With three-band toon shading, each small step in depth produces a crisp shadow line. That reads as detail for a handful of triangles, and the bevels stop anything looking like a raw cube. |
| **Consistent within, varied between** | One window style for each building, but different styles across a street | Real buildings are consistent with themselves. Matching windows is what makes a random mix believable. |
| **Toy proportions** | Thick walls, windows and doors about 1.3× life size, chunky roofs and chimneys | Fits the toy-box look, and the features stay readable from the high camera. |
| **A shine on every window** | Dark blue glass with a small light diagonal stripe | Two triangles that make a window instantly read as glass |

### Building types

| Type | Footprint | Storeys | Roof | Signature features | Levels | Material sound |
|---|---|---|---|---|---|---|
| Terraced house | Narrow rectangle, built in rows of 3–5 | 2 | Pitched, running along the row | Shared chimney stacks, front doors with steps, bay windows on some | Block Town | Plaster, tile |
| Cottage | Small rectangle or L-shape | 1–2 | Steep pitched | One big chimney, a round window in the gable, a little porch | Block Town, Castle Hill (outside the walls) | Plaster, tile |
| High-street shop | Rectangle | 2 | Flat with a stepped parapet, or pitched behind a false front | A big shop window, a striped awning, a hanging sign with a picture (loaf, ice cream cone, fish) and no words | Block Town | Plaster, wood (sign), glass |
| Block of flats | Rectangle or L-shape | 4–5 | Flat with a parapet, water tank on top | Balconies with railings, a grand front door, a cornice | Block Town (one of these is a star tower) | Plaster, glass |
| Clock tower | Square shaft | Tall | Pointed spire | Clock face (a disc with two hands), a belfry opening below the spire | Block Town (star tower) | Stone, tin (bell) |
| Water tower | Round tank on 4 legs | Tall | Cone cap | Legs with cross-bracing, a ladder | Block Town (star tower). Breaking the legs brings the tank down. | Tin |
| Bandstand | Octagon | 1 | Dome or cone on posts | Open sides, railings, a raised platform | Playground Park | Wood, tin |
| Glasshouse | Long rectangle | 1 | Curved or pitched glass | Thin frame, tinted glass panels, plant pots inside | Playground Park | Glass (chimes) |
| Kiosk and café | Round kiosk, rectangular café | 1 | Cone (kiosk), flat with an awning (café) | A giant cone on the kiosk roof, café tables outside | Playground Park | Plaster, wood |
| Castle pieces | Wall sections, round turrets, gatehouse, giant tower | Walls 1, turrets 3, tower about 6 | Crenellations, cone roofs on turrets | Arrow slits, flags, an arched open gate, the tower standing on 3 chunky pillars | Castle Hill | Stone |

### Street props

Props make the town feel lived in, and they're quick, satisfying things to knock over between buildings.

| Prop | Breaks into | Sound |
|---|---|---|
| Post box | Tips over in one piece | Tin |
| Phone box | Frame and glass panels | Tin, glass |
| Lamp post | Bends and falls | Tin |
| Bench | 2–3 planks | Wood |
| Bin | Tips over and the lid pops off | Tin |
| Fence and hedge | One section at a time | Wood, rustle |
| Rounded "lollipop" tree | Trunk and top | Wood, rustle |
| Parked toy car | Tumbles in one piece, wheels can pop off | Tin |
| Double-decker bus | Tumbles in one piece, rolls | Tin |
| Crate (Block Town) | 4–6 planks, plus an egg if it has one | Wood |
| Giant domino (Playground Park) | Falls in one piece | Wood |
| Beach ball (Playground Park) | Can't break, bounces | Rubber |

### Building from modules

Every building is put together from **modules**, the same way a real one is built:

| Module | Variants |
|---|---|
| Wall bay | Plain, window (several styles), door, shopfront, bay window, balcony |
| Corner | Plain, quoin stones (castle and clock tower) |
| Floor slab | One per storey. Shows inside when walls come away. |
| Band between floors | Ledge, cornice, parapet |
| Roof | Pitched halves, hipped pieces, flat cap, cone, dome, spire |
| Details | Chimney, awning, sign, railing, flag, clock face, water tank |

**Dolls'-house interiors.** Walls have real thickness, and their inside faces use interior cream. Every storey has a floor slab. When the front of a building falls away, he sees its floors like a dolls' house instead of an empty shell. It costs almost nothing and is charming in a toy world.

### Making the variety

- **Each building type is a generator function** in Blender Python, with parameters such as width in bays, depth, number of storeys, roof type, window style, details on or off, and colour scheme.
- **A seed number** picks the parameters, so `terraced_house(seed=12)` gives the same house every time.
- **Colour schemes are hand-picked, not random**: about 8 combinations of wall, trim, roof and door colours. **Why:** random colour choices produce clashing, messy streets. A set of chosen schemes gives variety that still looks good together.
- **The level layout** says which type, seed and position each building gets. No two neighbouring buildings share both type and scheme.

### How buildings break

**Structure.** Each module knows which modules hold it up. The generator already knows this from the storey and bay grid: a wall bay rests on the bay below it, and the roof rests on the top storey. These links are exported with the model.

**Damage:**

1. Each hit from a signature move detaches the modules inside its area and pushes them outwards. Detail pieces such as awnings, signs and chimneys come off on any hit.
2. **Collapse spreads upwards.** Any module whose supports have all gone also detaches, one storey at a time with about a 60 ms delay per storey. **Why:** taking out a bottom corner then brings down the column above it, which looks believable and is very satisfying. The short delay makes it crumble rather than vanish.
3. **Full collapse:** when less than 40% of the ground-floor modules remain, everything left comes down.

**How many hits it takes:**

| Building | Hits to bring down |
|---|---|
| Small buildings (cottages, kiosks) | 1 |
| Medium buildings (terraced rows, shops, bandstand) | 2 |
| Tall buildings (flats, clock tower, water tower) | 3 |

**Pieces never break further.** A detached module tumbles as one piece and doesn't split again. **Why:** it keeps the number of physics bodies predictable and the pieces recognisable.

### Triangle budgets

| Item | Budget (whole building, bevels included) |
|---|---|
| Module | ≤ 80 triangles |
| Small building | ≤ 400 |
| Medium building | ≤ 900 |
| Terraced row (3–5 houses) | ≤ 1,300 |
| Tall building or landmark | ≤ 1,800 |
| Prop | ≤ 150 |
| Dino | ≤ 2,500 |
| Whole level | ≤ 80,000 |

---

## Textures and 2D art

### The approach

Building surfaces stay **flat palette colour**. The shapes, depth and toon shading do the work. Textures are used only where a painted image clearly beats modelling, and they never break the single-batch rendering.

**Why not texture the buildings everywhere:**

- Painted textures fight the moulded-plastic toy look.
- From the high camera, fine detail either shimmers or blurs away to its average colour.
- Busy surfaces weaken the "bright means smashable" rule in an already busy scene.
- GPT Image textures rarely repeat without a visible seam, drift from the palette, and have shadows painted in.

### Where images are used

| Use | Source | Where it shows | Notes |
|---|---|---|---|
| Interface illustrations (title art, dino portraits, level cards, objective cards, progress icons) | GPT Image | The HTML interface layer | The biggest win. No cost to the 3D scene. |
| Small details: shop sign icons (loaf, fish, ice cream cone), clock face, flags, curtains seen through windows, flower boxes | GPT Image | The shared atlas | Small flat things where an image beats modelling |
| Dolls'-house wallpaper (stripes, flowers, dots) | GPT Image | The shared atlas, on the inside faces of walls | A surprise as walls fall away. Seen up close, so detail is visible. |
| Wood grain on crates and dominoes | GPT Image | The shared atlas | Subtle, and only on these big wooden props |
| Playmat ground (roads, zebra crossings, pavements, grass patches, park paths) | **Drawn by a script from the level layout** | The ground's own texture, one per level | **Why not GPT Image:** roads have to line up exactly with where the buildings are, and an image model can't match a layout precisely |

### The shared atlas

All building modules, props and details sample from **one 2048 × 2048 atlas**, so they all use one material and the whole town stays one `BatchedMesh` draw call.

| Area | Contents |
|---|---|
| Colour swatches | Every palette colour as a **32 × 32 px block** |
| Patterns | Awning stripes, café checks, roof-tile scallops, wood grain |
| Details | Sign icons, clock face, flags, curtains, flower boxes |
| Wallpaper | 4–6 interior patterns |

Rules:

- **Large swatch blocks, sampled at their centres.** Flat-coloured faces have UVs pointing at the centre of their swatch block. **Why:** filtering and mipmaps are set for a whole texture, not per area. The details need smooth filtering with mipmaps. Big swatch blocks sampled at the centre keep flat colours clean until the block shrinks to a couple of pixels, which is further away than the camera ever goes. (The toon gradient map is a separate small texture and keeps `NearestFilter`.)
- **8 px padding** around every tile, with the tile's edge colour repeated into the padding. **Why:** at lower mip levels, neighbouring tiles otherwise bleed into each other's edges.
- **Each image appears once per face.** A wallpaper or grain tile is mapped once across each wall bay or crate face. **Why:** a texture's repeat setting wraps the whole atlas, so a single tile inside an atlas can't repeat across a face. The modules are sized so one tile per face looks right.
- **Compressed as KTX2 using UASTC** (via `gltf-transform`, which needs KTX-Software installed). **Why KTX2:** PNG and WebP are unpacked to full size in graphics memory (about 22 MB for 2048 × 2048 with mipmaps), while KTX2 stays compressed at roughly a quarter of that. **Why UASTC rather than ETC1S:** ETC1S is smaller but shifts flat colours and smears small details. Exact palette colours matter here.

### Playmat ground

- A script reads the level layout and draws roads, pavements, crossings, paths and grass in flat palette colours, with slightly rounded corners and a faint stitched edge, like a real playmat.
- 2048 × 2048 per level, compressed as KTX2.
- **Anisotropic filtering** set to the device maximum (`renderer.capabilities.getMaxAnisotropy()`). **Why:** the ground is always seen at a steep angle, and without anisotropic filtering it goes blurry a short way from the dino.
- The ground has its own material, adding one draw call.

### Processing GPT Image output

Every generated image goes through a script before use. Claude Code writes it with Pillow, and it runs as part of `npm run assets`:

1. **Prompt for flat art:** "flat, evenly lit, front-on, no shadows, no highlights, bold simple shapes, toy-print style". Prompts are saved in `assets-src/textures/prompts.json`.
2. **Remove the background** for details, and make wallpaper and grain tiles repeat seamlessly.
3. **Snap colours to the palette** (nearest palette colour), so everything matches "bright means smashable". Sign icons and flags use the trim, window and dark colours, so they read as print rather than as breakable surfaces.
4. **Shrink to size**, then pack into the atlas with padding.
5. **Interface illustrations** are exported as WebP at 2× display size. **Why WebP is right here:** they're shown in HTML, not on the graphics card as textures, so a small download is what matters.

**Commit the original generated images**, not just the processed versions. **Why:** generation gives different results each time, so the originals are the source of truth. The processing steps are repeatable, so they can be re-run whenever the palette or atlas layout changes.

### Texture budget

| Item | Graphics memory (approximate) |
|---|---|
| Shared atlas (2048², UASTC, with mipmaps) | ~6 MB |
| Playmat ground for the current level | ~6 MB |
| Toon gradient map, effects | < 1 MB |
| **Total in the 3D scene** | **Under 16 MB** (hard limit 32 MB) |

**Why set a limit:** Safari on iPad closes tabs that use too much memory, and players see it as a crash.

---

## Audio design

### Principles

1. **Each break is built from three layers:** the **hit** (thump or crack), the **material** (see below) and the **debris** rattling as it lands, triggered by the physics.
2. **Never the exact same sound twice in a row.** Each sound has 4–6 versions, plus a random pitch shift of ±10% (`playbackRate` 0.9–1.1). **Why:** a clip repeating quickly sounds like a machine gun, which is what makes repeated game sounds grate.
3. **Physics triggers the debris sounds, with limits:**
   - Contact-force events from Rapier set the volume from how hard things hit.
   - Below a minimum force, there's no sound.
   - Each body has an 80 ms cooldown.
   - At most 8 debris sounds play at once, and a new one cuts off the oldest.
   - **Why:** a collapsing building produces hundreds of contacts a second, and without limits that becomes a distorted hiss.
4. **Chains are musical.** Each break within about 1 s of the last plays one step higher on a pentatonic scale, then the scale resets after a pause. **Why pentatonic:** no two of its notes clash, so long chains (the domino run, the ankylosaurus's launches) always sound good.
5. **Mixed for a small child:**
   - Everything goes through a final compressor (`DynamicsCompressorNode`), so nothing clips during the biggest collapse.
   - Music dips by about 6 dB for 300 ms on big hits, so the hits punch through.
   - No harsh high sounds, no sirens and nothing scary.
   - Parent settings include a master volume.

### Material sounds

| Material | Used for | Sound |
|---|---|---|
| Plaster | House and shop walls | A soft, chunky clack |
| Tile | Roofs | A light clatter |
| Wood | Doors, signs, crates, fences, dominoes, benches | A hollow clonk |
| Glass | Windows, glasshouse, phone box | Chimes and tinkles, never a sharp shatter |
| Tin | Post box, cars, bus, lamp posts, water tower, bell | A toy-tin clang |
| Stone | Castle, clock tower | A deep thunk |
| Rubber | Beach balls | Boing |
| Leaves | Hedges, trees | Rustle |

Each module and prop records its material in its export data, so the right sound plays automatically.

### Dino sound sets

| Dino | Sounds |
|---|---|
| T. rex | Big but cartoony roar, heavy footsteps, a booming stomp with deep bass, a happy roar to celebrate |
| Triceratops | Snorts, thundering run, horn crunch on impact, a "boing" bounce when it hits something big |
| Ankylosaurus | Grunts, a whoosh as the tail swings, a huge BONK, a falling whistle on launched objects |

Footsteps include a faint rattle from nearby props, which makes the dino feel heavy.

### Music

- Bouncy and percussive, around 120 BPM, in a toy marching band style (brass, xylophone, snare).
- One theme per story level, a looser loop for sandbox, and a short fanfare for completing a level.
- **Two layers per track:** a base groove, plus a percussion layer that fades up as destruction builds and back down when things calm.

### How it's built

- **Web Audio API:**
  - Decode each sound once when the game loads, then play it with a one-off `AudioBufferSourceNode`.
  - Group sounds into channels with their own volume (`GainNode`): dino, breaks, debris, interface, music. The channels feed the compressor, and the compressor feeds the speakers.
- **Start audio on the first tap:** the audio context starts suspended until the player interacts, so call `resume()` inside the title screen's tap handler.
- **Simple placement:** left–right panning by screen position, plus quieter sounds with distance. **Why not full 3D audio:** it costs more processing, and tablet speakers can barely tell the difference.
- **Sound sources:**
  - Kenney's Impact Sounds (CC0) as a starter and placeholder set.
  - ElevenLabs for custom roars and bonks, generated only when building the game.
  - Recordings of real toy blocks for the plaster and wood layers.
  - Generated sounds are saved as audio files in the repo, and the game never calls the API.

---

## Technical design

### Stack

| Part | Choice |
|---|---|
| Build | Vite + TypeScript |
| Rendering | React 19, `@react-three/fiber` v9, `@react-three/drei` |
| Physics | `@react-three/rapier` v2 (v2 is the version that works with React 19 and fiber v9) |
| Thumbstick | A small custom component (or `nipplejs`) |
| Hosting | Its own Netlify site |

### Rendering

- **Draw all building pieces with one `THREE.BatchedMesh`.**
  - Every module from every building goes into it.
  - Breaking a piece off hides its copy in the batch, and the piece reappears as a moving copy that follows its physics body.
  - **Why:** a batch can hold many different shapes but still be drawn in one go (one draw call). If each building drew its pieces separately, a level would make over a thousand draw calls, which is too many for a tablet. Every module shares the one atlas material, so they can all go in one batch.
- **Instancing** (many copies of one shape drawn in one go) for repeated props (lamp posts, benches, fences, crates) and for effects (dust, confetti).
- **One shadow-casting light** with a small shadow map. Debris doesn't cast shadows.
- **Limit pixel density with `dpr={[1, 2]}`.** **Why:** a Retina iPad at full density renders four times the pixels.
- **Per-frame updates through refs in `useFrame`, never `setState`.** **Why:** `setState` 60 times a second makes React re-check the component tree every frame.

### Physics

| Thing | Body type | Colliders |
|---|---|---|
| Ground and hills | Fixed | Mesh-shaped (static only) |
| Intact building | Fixed | A few rough boxes until its first hit, then one box per module |
| Detached module | Dynamic | A box, or a convex hull for roof pieces |
| Props | Dynamic, sleeping until touched | A box, capsule or ball |
| Dino | Kinematic (moved by code) | A capsule |

- **Rough colliders until the first hit.** **Why:** most buildings aren't being hit at any moment. A few boxes each keep the physics engine's checks light, and switching to per-module boxes only when hit gives precise breaking where it's needed.
- **Never use mesh-shaped colliders on moving bodies.** **Why:** collisions between two detailed meshes are expensive and unreliable, while boxes and hulls are cheap and stable.
- **The dino is kinematic.** **Why:** a dino driven by physics would get knocked about by debris and could tip over. A kinematic body pushes everything but can't be pushed.
- **Signature moves are shape queries.** Each move asks the physics world which bodies are inside its sphere (stomp), its box sweeping forwards (charge) or its ring (tail swing). It then gives each of them a push and passes the hits to the breaking system.
- **Fixed physics step of 1/60 s,** the Rapier default (don't set `timeStep="vary"`). **Why:** a varying step makes stacked pieces jitter and fall over on their own.
- **Limits on moving pieces:**
  - At most 150 moving bodies at once.
  - Settled debris sinks into the ground and disappears after 4 s.
  - If the limit is reached, the oldest debris sinks early.
  - **Why:** this keeps the frame rate steady during the castle tower collapse, the biggest moment in the game.

### Breaking system

- Builds the structure links (which module holds up which) from each building's export data.
- Handles hits: detaches modules, works out which modules have lost their supports, spreads the collapse with a delay, and checks for full collapse.
- Reports to the objectives system (towers knocked over, walls broken, pillars broken, crates opened).

---

## Asset pipeline

### Blender scripts as the source of truth

Claude Code writes Blender Python scripts and runs them in the background:

```bash
blender --background --factory-startup --python assets-src/build_level.py -- --level block-town
```

- `--background` runs without the interface, so it can run from a terminal or in a batch.
- `--factory-startup` ignores your own Blender preferences and add-ons, so the output is the same on any machine.
- Everything after `--` goes to the script, which reads it from `sys.argv`.

The **Blender MCP connector** is optional, for trying ideas in a live Blender window. Anything worth keeping gets turned into a generator script.

### Conventions (put these in CLAUDE.md)

- **Scale:** 1 unit = 1 metre.
- **Direction:** models face −Y in Blender. The glTF exporter's Y-up conversion turns that into +Z in three.js.
- **Origins** at the feet, or at the centre of the base.
- **Export with `export_apply=True`** (applies transforms and modifiers) **and `export_extras=True`** (includes custom properties). Custom properties end up in `userData` in three.js.
- **One shared atlas** (see "Textures and 2D art"). Every model is mapped onto it, and all models share one material. Flat-coloured faces point at the centre of their swatch block.
- **Flat shading, plus a small bevel** on outside edges.
- **Naming:** `MOD_<building>_<index>` for modules, `COL_` for collider shapes, `SPAWN_` for spawn points, `OBJ_` for objective targets.
- **Keep to the triangle budgets** in "Building design".
- **Previews:** every script ends by rendering previews with Workbench, and Claude **looks at them before saying the work is done**.

### Previews and checks

| Script | Previews |
|---|---|
| Building type | Contact sheet of 6 seeds, plus a **silhouette sheet** (solid black shapes) |
| Level | Top-down view and a high angled view |
| Dino | Turnaround views plus key poses from each animation |

**The silhouette test:** every building type must be identifiable from its black silhouette alone, and the 6 seeds must look noticeably different from each other. If not, the generator needs more variety.

### What gets exported

- **Each level becomes one GLB.** Each building is an empty with its module meshes as children. The export data carries:
  - **Building:** `id`, `type`, `seed`, `scheme`, `hitsToCollapse`, `objective?`
  - **Module:** `id`, `role`, `material`, `supports` (list of module ids), `collider` (`box` or `hull`)
- **Each dino becomes one GLB** with its puppet rig and named animations (`idle`, `walk`, `run`, `move`, `celebrate`, `roar`). Then run `gltfjsx --types` to generate typed components.
- **Optimise everything with `gltf-transform`:** remove unused data, merge duplicates and apply meshopt compression.

### Dinos: puppet rig

Each body part is a separate rigid low-poly piece attached to its own bone in a simple skeleton: head, jaw, neck, body, tail segments, legs, plus horns and frill or tail club. This needs no weight painting, and the chunky toy look suits it. Animations are keyframed in the same script.

### Repo layout

```
dino-stomp/
  CLAUDE.md
  assets-src/
    lib/           # shared helpers: scene reset, palette material, bevel, export, previews
    buildings/     # one generator per building type
    props/
    dinos/
    levels/        # level layouts: building type, seed and position, plus props, objectives, spawns
    textures/
      prompts.json # GPT Image prompts
      originals/   # generated images as they came out (committed)
      atlas.py     # snap to palette, pad, pack the atlas
      playmat.py   # draws each level's ground from its layout
    ui-art/        # interface illustration originals and prompts
    build_level.py
    palette.json   # palette colours and colour schemes
  assets-out/      # GLBs, atlas, ground textures, previews (previews kept out of the deployed build)
  public/
    models/
    textures/
    ui/
    audio/{dinos,breaks,debris,ui,music}/
  src/
    game/{dinos,controls,camera,objectives,modes}/
    world/{buildings,breaking,props,effects}/
    audio/
    ui/
```

`npm run assets` runs everything in order:

1. Process textures: snap colours to the palette, pack the atlas, draw the playmat grounds.
2. Run the Blender scripts.
3. Run `gltf-transform`, including KTX2 compression.
4. Run `gltfjsx`.
5. Export the interface art as WebP.
6. Copy everything into `public/`.

It never calls GPT Image. Generating new images is a separate, deliberate step (`npm run generate-art`), and its originals are committed.

### Data model

```ts
type DinoId = 'trex' | 'triceratops' | 'ankylosaurus';
type Material = 'plaster' | 'tile' | 'wood' | 'glass' | 'tin' | 'stone' | 'rubber' | 'leaves';

interface DinoStats {
  id: DinoId;
  speed: number;                 // metres per second
  move: 'stomp' | 'charge' | 'tailSwing';
  moveRadius: number;            // stomp and tail swing
  moveLength?: number;           // charge
  pushStrength: number;
  cooldownSeconds: number;
}

interface BuildingMeta {
  id: string;
  type: string;                  // e.g. "terraced_house"
  seed: number;
  scheme: string;
  hitsToCollapse: 1 | 2 | 3;
  objective?: string;            // objective id, if this is a target
}

interface ModuleMeta {
  id: string;
  buildingId: string;
  role: 'wall' | 'corner' | 'floor' | 'band' | 'roof' | 'detail' | 'pillar';
  material: Material;
  supports: string[];            // module ids holding this one up
  collider: 'box' | 'hull';
}

type ObjectiveType = 'topple' | 'collect' | 'chain' | 'deliver' | 'smashSet' | 'collapse';

interface Objective {
  id: string;
  type: ObjectiveType;
  icon: string;
  voiceClip: string;
  targets: string[];             // building, prop or module ids
  required: number;              // e.g. 3 towers, 6 wall sections
}

interface Level {
  id: 'block-town' | 'playground-park' | 'castle-hill';
  model: string;                 // GLB path
  music: { base: string; chaos: string };
  objectives: [Objective, Objective];
  dinoSpawn: [number, number, number];
}
```

---

## Getting set up

### Install

1. **Blender 5.1 or later.** Link it into a folder on your PATH, for example `ln -s /Applications/Blender.app/Contents/MacOS/Blender /opt/homebrew/bin/blender`. **Why a link:** shell aliases only exist in interactive sessions, so tools Claude Code runs may not see them. Blender has its own Python built in, so never `pip install bpy`.
2. **Node.js LTS.**
3. **Packages:**
   - `npm i three @react-three/fiber @react-three/drei @react-three/rapier motion`
   - `npm i -D @gltf-transform/cli gltfjsx`. **Why as dev dependencies:** they only run when you build assets, and installing them in the project pins their versions.
4. **KTX-Software** (from the Khronos Group's GitHub releases). `gltf-transform` needs it for KTX2 compression.
5. **Pillow** for the texture scripts: `pip install pillow`, in your normal Python, not Blender's.

### Optional connections

- **Blender MCP connector** (Blender Lab add-on), for trying ideas live. In Claude Code, register its binary with `claude mcp add --scope project blender -- "<path>"`.
- **Playwright MCP** (`claude mcp add playwright npx @playwright/mcp@latest`), so Claude Code can screenshot the running game.
- **ElevenLabs API key** in a `.env` file that git ignores, used only when building sounds.
- **OpenAI API key (GPT Image)** in the same `.env`, used only by `npm run generate-art`. **Why only there:** the game itself never calls an image API, so no key ever reaches the browser.

### Testing on the tablet

- `npm run dev -- --host` lets the tablet load the dev server over your Wi-Fi.
- Turn on Web Inspector in the iPad's Safari settings, then debug it from Safari on your Mac.

---

## Milestones

| # | Milestone | Done when |
|---|---|---|
| M0 | Tech spike | One terraced-house generator → GLB → R3F with `BatchedMesh` and Rapier. A placeholder capsule dino with the thumbstick and tap controls. A stomp detaches modules and the collapse spreads upwards. Frame rate checked on his tablet. |
| M1 | Interface prototype and test with him | Every screen built with placeholder art: title, dino select, level select, objective intro, in-game display, pause, level complete. The full tap feedback and voice labels work. **He uses it while you watch**, and you note every hesitation or wrong tap, then fix them before moving on. |
| M2 | Building kit and atlas | All 9 building types and all props, each passing its preview checks and silhouette test. Colour schemes chosen. Atlas built and the playmat script working. |
| M3 | Dinos | 3 puppet-rigged dinos with all animations and signature moves. |
| M4 | Block Town | Level layout, both objectives, objective cards, progress icons, markers and level completion. |
| M5 | Playground Park and Castle Hill | Both levels and their objectives, including the help pushes for the domino run and the guaranteed tower collapse. |
| M6 | Sandbox | Choosing a map, endless play, automatic and manual rebuild. |
| M7 | Audio | The full audio design: layers, limits, chain pitches, dino sets, music layers, compressor. |
| M8 | Art and polish | Final interface illustrations from GPT Image, detail images, parent settings, saving. A second test session with him, and tuning based on how it goes. |

---

## Acceptance checklist

### Buildings

- [ ] Every building type can be identified from its silhouette sheet.
- [ ] The 6 seeds of each type look noticeably different.
- [ ] No two neighbouring buildings share both type and colour scheme.
- [ ] Buildings break into recognisable modules (windows, roof halves, chimneys, floors), never random chunks.
- [ ] Taking out a bottom corner brings down the column above it, one storey at a time.
- [ ] A building with its front knocked off shows floors like a dolls' house.
- [ ] Everything is within its triangle budget.

### Gameplay

- [ ] Every objective can be completed with every dino.
- [ ] Objectives can be done in any order, and there's no timer.
- [ ] Tapping the ground walks there, and tapping a building attacks it.
- [ ] Touching the thumbstick always cancels a tapped walk or attack.
- [ ] A building between the dino and a tapped destination gets smashed through.
- [ ] The domino run always reaches the end once started, and the giant tower always falls once its pillars are gone.
- [ ] Sandbox never ends, and rebuild works both automatically and by button.

### Interface

- [ ] He can get from the title screen to stomping, and back home, without help.
- [ ] At most 3 taps from the title screen to stomping.
- [ ] Every tap gets feedback: a squash and a sound on touch, the spoken name on selection, a "bonk" and wobble on locked things.
- [ ] Every button meets its minimum size and spacing, and sits at least 32 pt from the screen edges.
- [ ] Pinching, double-tapping or long-pressing never zooms, selects text or opens a browser menu.
- [ ] Pause is one tap. Leaving a level or swapping dino keeps objective progress.
- [ ] The help prompts appear after 5 s idle on menus and 10 s idle in levels.
- [ ] Everything noted in the M1 test session has been addressed.

### Textures

- [ ] All building modules, props and details use the one shared atlas, and the town still draws in one batch.
- [ ] Flat colours stay clean at the furthest camera distance, with no bleeding between atlas tiles.
- [ ] Every generated image has been snapped to the palette, and none has shadows painted in.
- [ ] The playmat roads line up with the level layout.
- [ ] Graphics memory used by textures is under 16 MB in every level.

### Performance

- [ ] At least 50 fps on his tablet during the castle tower collapse.
- [ ] The town's buildings draw in one batch (one draw call for all modules).
- [ ] Moving bodies never go over 150.

### Audio

- [ ] No clipping during the biggest collapse.
- [ ] No sound plays exactly the same version twice in a row.
- [ ] Quick chains rise in pitch and reset after a pause.
- [ ] Audio starts after the first tap on iPad.

### Safety and comfort

- [ ] No people, fire, smoke or sharp shattering anywhere.
- [ ] Screen shake can be turned off, and master volume works.
- [ ] Nothing in the game needs reading.

---

## Decisions left open

1. **Target tablet:** this sets the frame rate and body limits.
2. **Sandbox maps:** all three open from the start (default), or unlocked through story mode.
3. **Sandbox auto-rebuild:** at 80% destroyed (default), or button only.
4. **Voice for objective prompts:** recorded by you, or text-to-speech.
5. **Where the music comes from:** generated, CC0 loops, or made for the game.
6. **Dino size compared to buildings:** default is the T. rex at about 1.5× a two-storey house.
7. **Lessons from the last game's interface:** write down exactly what he struggled with, and check the "Interface design" rules cover each point before M1.
8. **Parent settings:** open (default), or behind a simple gate so he can't turn the volume off by accident.

## Later

- **Secrets:** a hidden collectible in each level (for example a golden dino statue behind something breakable). Finding all three unlocks a **secret finale**: a giant wind-up toy robot that wanders the castle rebuilding towers, which he knocks over.
- **New settings:** beach, farm and forest, each with its own building types made with the same kit.
- **More dinos**, each with a new signature move.
