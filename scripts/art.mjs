// Interface art (after dino-safari's scripts/art.mjs). Run through npm so the API key is loaded:
//
//   npm run art                 generate everything that is missing, then pack
//   npm run art -- gen <id...>  regenerate named images, then pack
//   npm run art -- pack         convert art/raw/*.png into public/ui/*.webp
//
// Raw model output is kept in art/raw/ (git-ignored) so packing can be re-run for free.
// The dino stickers are redrawn from the game's own renders of the models, so they match what he plays as.

import { mkdir, readFile, writeFile, access } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const RAW = path.join(ROOT, 'art', 'raw');
const OUT = path.join(ROOT, 'public', 'ui');

const MODEL = process.env.ART_MODEL ?? 'gpt-image-2.6-sunburst';
const QUALITY = process.env.ART_QUALITY ?? 'high';
const SQUARE = '1024x1024';
const WIDE = '1536x1024';

const ORIGINAL =
  "An original design for a young child's toy-town dinosaur game. It does not resemble any character or artwork " +
  'from an existing game, film or cartoon. Friendly, suitable for a young child.';
const TOY =
  'Style: a chunky, glossy, moulded-plastic toy, like a bright collectable figure, with simple faceted low-poly shapes, ' +
  'thick dark-brown ink outlines, flat saturated colours with one soft highlight and one soft shade, no gradients, no realism.';
/** Asked of every picture: art that runs off the canvas comes out with a flat, cut-off edge. */
const MARGIN =
  'The whole picture fits well inside the image with a wide empty margin on all four sides: nothing touches or is cut off by any edge of the image.';
const CUTOUT =
  'Centred with empty space all round, on a fully transparent background, with a thick, even, white die-cut ' +
  'sticker border all the way around the outline. No text, no letters, no background, no ground, no shadow, nothing else in the picture.';

const dino = (id, what) => ({
  size: SQUARE, transparent: true, tall: 640, from: path.join(OUT, `dino-${id}.webp`), out: `sticker-${id}`,
  prompt:
    `Redraw this toy dinosaur as a sticker: ${what} Keep its exact colours, shape and pose, seen from the same angle, ` +
    `and give it a friendly face with a bright eye. ${TOY} ${ORIGINAL} ${CUTOUT} ${MARGIN}`,
});

export const ART = {
  logo: {
    size: WIDE, transparent: true, tall: 560, out: 'logo',
    prompt:
      'A game logo that reads exactly "DINO STOMP" in two stacked lines, DINO above STOMP, in huge, chunky, rounded, ' +
      'bouncy toy-block capital letters, each letter a different bright colour (tomato red, sunny yellow, cobalt blue, ' +
      'orange, pink), with thick dark-brown ink outlines and a thick white sticker border round the whole logo. One big ' +
      'green dinosaur footprint stamped behind the letters. On one side, a little cartoon toy-town house is being knocked ' +
      'over and coming apart: its red roof flying off, a wall tipping, a chimney and a window tumbling through the air ' +
      'with a puff of dust and a few stars. No interlocking plastic bricks, no studded bricks, no construction-toy pieces. ' +
      'The text reads exactly DINO STOMP and nothing else. Flat, front-on, centred, on a fully transparent background, ' +
      `no other words, no background, no shadow. ${MARGIN} ${ORIGINAL}`,
  },
  'sticker-trex': dino('trex', 'a green Tyrannosaurus rex with a cream belly, mouth open in a happy roar showing white teeth.'),
  'sticker-triceratops': dino('triceratops', 'a purple Triceratops with a cream belly and three white horns.'),
  'sticker-stegosaurus': dino('stegosaurus', 'a teal Stegosaurus with golden-yellow plates along its back and tail spikes.'),
  // --- the sticker book ---
  ...Object.fromEntries(
    [
      ['first-smash', 'a cheerful little toy house tumbling apart: its roof popping off, a wall tipping and a window flying, with a puff of dust and stars. No studded or interlocking plastic bricks'],
      ['tower', 'a tall toy clock tower toppling over sideways with a big swoosh line and stars'],
      ['dominoes', 'a curving row of giant colourful dominoes falling one after another'],
      ['big-wheel', 'a bright fairground big wheel tipping over with its little gondolas flying off'],
      ['sunflower', 'a giant smiling sunflower bending over with petals flying'],
      ['treehouse', 'a wooden treehouse in a leafy tree, its planks tumbling down'],
      ['giant-tower', 'a tall grey toy castle tower with a pink cone roof crashing down, with fireworks'],
      ['catch', 'a little red toy car bouncing up into the air, flipped over, with a big BOING burst'],
      ['power', 'a huge glowing yellow starburst with lightning-bolt sparkles, like a super-powered smash'],
      ['secret', 'a shiny golden toy dinosaur statue on a little pedestal, sparkling'],
      ['robot', 'a friendly blue wind-up toy robot with a golden key in its back, toppled over on its back, dizzy, with stars'],
    ].map(([id, what]) => [
      `sticker-${id}`,
      { size: SQUARE, transparent: true, tall: 360, out: `sticker-${id}`, prompt: `A round collectable reward sticker for a young child: ${what}. ${TOY} ${ORIGINAL} ${CUTOUT} ${MARGIN}` },
    ]),
  ),
  'level-robot-castle': {
    size: SQUARE, tall: 720, out: 'level-robot-castle',
    prompt:
      'A bright picture for a level card in a toy-town dinosaur game: a toy castle of grey blocks with pink and red cone-roofed ' +
      'turrets on a green hill, and a giant friendly blue wind-up toy robot with a big golden key in its back striding through ' +
      'the courtyard, seen from a high three-quarter angle like a toy playset. Sunny sky, soft colours. ' +
      `${TOY} ${ORIGINAL} No text, no letters, no border.`,
  },
  smash: {
    size: SQUARE, transparent: true, tall: 256, out: 'smash',
    prompt:
      `A comic-book impact burst: a big, jagged white-and-yellow starburst with three small toy building blocks flying out of it. ${TOY} ${CUTOUT}`,
  },
};

const exists = (p) => access(p).then(() => true, () => false);

async function openai(endpoint, body) {
  const key = process.env.OPENAI_API_KEY;
  if (!key) throw new Error('OPENAI_API_KEY is not set (put it in .env.local)');
  const isForm = body instanceof FormData;
  const res = await fetch(`https://api.openai.com/v1/${endpoint}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${key}`, ...(isForm ? {} : { 'Content-Type': 'application/json' }) },
    body: isForm ? body : JSON.stringify(body),
  });
  const json = await res.json();
  if (!res.ok) throw new Error(`OpenAI ${res.status}: ${json.error?.message ?? JSON.stringify(json)}`);
  return Buffer.from(json.data[0].b64_json, 'base64');
}

async function generate(id, spec) {
  const background = spec.transparent ? 'transparent' : 'opaque';
  let png;
  if (spec.from) {
    // Redraw from one of the game's own renders.
    const form = new FormData();
    form.set('model', MODEL);
    form.set('prompt', spec.prompt);
    form.set('size', spec.size);
    form.set('quality', QUALITY);
    form.set('background', background);
    form.set('output_format', 'png');
    const reference = await sharp(spec.from).png().toBuffer();
    form.append('image[]', new Blob([reference], { type: 'image/png' }), 'reference.png');
    png = await openai('images/edits', form);
  } else {
    png = await openai('images/generations', { model: MODEL, prompt: spec.prompt, size: spec.size, quality: QUALITY, background, output_format: 'png' });
  }
  await writeFile(path.join(RAW, `${id}.png`), png);
  console.log(`[${id}] generated`);
  return png;
}

/** True if the drawing touches an edge of its canvas, which means part of it has been cut off. */
async function clipped(png) {
  const { data, info } = await sharp(png).ensureAlpha().raw().toBuffer({ resolveWithObject: true });
  const solid = (x, y) => data[(y * info.width + x) * 4 + 3] > 40;
  for (let x = 0; x < info.width; x++) if (solid(x, 0) || solid(x, info.height - 1)) return true;
  for (let y = 0; y < info.height; y++) if (solid(0, y) || solid(info.width - 1, y)) return true;
  return false;
}

/** Generate, and if the result runs off the canvas, try again (up to three goes in all). */
async function generateWhole(id, spec) {
  for (let attempt = 1; attempt <= 3; attempt++) {
    const png = await generate(id, spec);
    if (!spec.transparent || !(await clipped(png))) return;
    console.warn(`[${id}] attempt ${attempt} runs off the edge of the canvas${attempt < 3 ? '; trying again' : ': STILL CLIPPED, check it by eye'}`);
  }
}

async function pack() {
  await mkdir(OUT, { recursive: true });
  for (const [id, spec] of Object.entries(ART)) {
    const raw = path.join(RAW, `${id}.png`);
    if (!(await exists(raw))) continue;
    // Trim the empty margin, then size it for the screen.
    await sharp(raw).trim().resize({ height: spec.tall, withoutEnlargement: true }).webp({ quality: 90 }).toFile(path.join(OUT, `${spec.out}.webp`));
    console.log(`[${id}] packed -> public/ui/${spec.out}.webp`);
  }
}

const [cmd, ...ids] = process.argv.slice(2);
await mkdir(RAW, { recursive: true });
if (cmd !== 'pack') {
  const wanted = cmd === 'gen' ? ids : Object.keys(ART);
  const results = await Promise.allSettled(
    wanted.map(async (id) => {
      if (!ART[id]) throw new Error(`unknown id: ${id}`);
      if (cmd !== 'gen' && (await exists(path.join(RAW, `${id}.png`)))) return;
      await generateWhole(id, ART[id]);
    }),
  );
  results.forEach((r, i) => r.status === 'rejected' && console.error(`[${wanted[i]}] FAILED: ${r.reason.message}`));
}
await pack();
