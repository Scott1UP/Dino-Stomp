# Dino Stomp

A toy-box destruction game for a young child. The full design is in `spec/dino-stomp-spec.md`: read the relevant section before changing anything it covers.

## Commands

- `npm run dev` — dev server (`npm run dev -- --host` to open it on the tablet). Add `?debug` to the URL for frame rate, draw calls and moving bodies.
- `npm run typecheck`
- `npm run assets` — builds all three levels headless: GLBs, the atlas, playmat grounds, previews, and the level cards and objective icons in `public/ui/`. One level: `blender --background --factory-startup --python assets-src/build_level.py -- --level block-town`.
- `npm run assets:dinos` — exports the three dino GLBs and their reference renders.
- Any generator runs on its own to render its preview sheets into `assets-out/previews/`, e.g. `blender --background --factory-startup --python assets-src/buildings/cottage.py`.

Blender is not on PATH. The scripts default to `/Applications/Blender.app/Contents/MacOS/Blender`; set `BLENDER` to override. Blender has its own Python: never `pip install bpy`.

## Asset conventions

- **Generator scripts in `assets-src/` are the source of truth.** The Blender MCP connector is for showing work in the live Blender window and trying ideas; anything worth keeping becomes a script. In the live window, build into a `DinoStomp_<level>` collection and never call `lib.scene.reset()` (it wipes the scene).
- **Scale:** 1 unit = 1 metre.
- **Direction:** models face −Y in Blender, which the glTF exporter turns into +Z in three.js.
- **Origins:** buildings at the centre of the base, modules at the centre of their bounding box.
- **Export** with `export_apply=True` and `export_extras=True`. Custom properties arrive as `userData` in three.js.
- **One shared atlas, one material.** Flat-coloured faces point their UVs at the centre of a swatch block. Colours and schemes live in `assets-src/palette.json`; append new colours at the end so existing swatches don't move. The atlas ships as `public/textures/atlas.png`, not inside the GLBs.
- **Flat shading.** Faces never share vertices.
- **Naming:** `BLD_<id>` for building empties, `MOD_<building>_<index>` for modules, `COL_` for collider shapes, `SPAWN_` for spawn points, `OBJ_` for objective targets.
- **Module data:** `id`, `buildingId`, `role`, `material`, `storey`, `supports` (comma-separated module ids), `collider` (`box` or `hull`).
- **Generators:** one file per type in `assets-src/buildings/` and `assets-src/props/`, each built on `lib.building.Building` and `lib.meshkit.Kit`. `terraced_house.py` is the exemplar. A `Building`'s `kind` tells the game how it behaves: `building`, `prop` (never blocks the dino, knocked over by walking into it), `crate`, `domino`, `ball`, `giantTower`.
- **Levels** are Python layouts in `assets-src/levels/` (X east, Y north; a building's front faces −Y at rot 0). The playmat ground is drawn from the same layout by `textures/playmat.py`, so roads always line up.
- **Triangle budgets** are in the spec under "Building design". Generators print their counts and flag anything over.
- **Previews:** every generator renders previews with Workbench. Look at them before saying the work is done.

## Dinos

- All three dinos (T. rex, triceratops, stegosaurus) come from the Quaternius CC0 pack in `Dinosaur-Animated-Pack-Quaternius-2018/` (head towards −Y, a shared 29-bone rig, six actions each). `assets-src/dinos/export_dinos.py` recolours them, scales them to game size and exports GLBs, plus renders to `art/refs/` that the sticker art is redrawn from. It opens downloaded .blend files, so it runs with `--disable-autoexec`.

## Generated art and sound

- Keys live in `.env.local` (git-ignored): `OPENAI_API_KEY`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `ELEVENLABS_MODEL_ID`. The game never calls either API; it plays and shows the files in `public/`.
- `npm run art` — the logo, dino stickers and smash icon (`scripts/art.mjs`). Stickers are redrawn from the dinos' own renders. Raw output is kept in `art/raw/`.
- `npm run audio -- sfx | voice | music` — sound effects, spoken lines and the music (`scripts/audio.mjs`); lines are listed in `src/audio/lines.json`. One take each, and music only for pieces that don't exist yet.

## Game structure

- `src/world/breaking/TownSystem.ts` — every module and prop: the batched mesh, physics bodies, how things come apart, the giant tower, rebuilding. It raises events (`onBreak`, `onImpact`, `onDown`…) that sound, effects and objectives listen to.
- `src/game/objectives/Objectives.tsx` — each level's rules: towers, eggs, the domino run's help pushes, the pool, sandbox auto-rebuild, and the marker stars.
- `src/game/dinos/` — `stats.ts` holds the speeds, move sizes, strengths and the charge (hold smash 1.5 s for +20%) to tune; `Dino.tsx` is the kinematic capsule, the three signature moves (bite, charge, tail swing) and the animated model.
- `src/audio/engine.ts` — layered breaks per material, chain pitches, debris limits, dino sets, and the looping music (one recorded piece per level, louder and brighter as he smashes). Every sound effect has a synthesised stand-in; recorded files listed in `public/audio/manifest.json` replace them as they load.
- `src/ui/` — the HTML interface over the canvas, in Dino Safari's look (ink outlines, cream panels, Fredoka, Lucide icons). `store.ts` holds the screens, progress and settings.
- `src/world/toon.ts` — the shared toon gradient and `addDetail`, which multiplies the detail patterns (roof tiles, bricks, planks) over the flat colours. Each face's second UV set and vertex colour, written by `lib/meshkit.py`, pick the pattern.

## Code conventions

- Per-frame updates go through refs in `useFrame` or the physics step, never `setState`.
- Shared mutable game and input state lives in `src/game/state.ts`.
- All building modules draw through the one `BatchedMesh` in `src/world/breaking/TownSystem.ts`. Keep the town at one draw call.
- Never use mesh-shaped colliders on moving bodies: boxes and convex hulls only.
- The physics step stays fixed at 1/60 s.
