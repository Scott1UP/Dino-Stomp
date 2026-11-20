// Sound pipeline (after dino-safari's scripts/audio.mjs). Run through npm so the API key is loaded:
//
//   npm run audio -- sfx            generate every sound effect that is missing
//   npm run audio -- voice          generate every spoken line that is missing
//   npm run audio -- music          generate the music: ONE take per piece, and only the pieces that are missing
//   npm run audio -- redo <id...>   delete and regenerate named effects or lines (never music)
//
// Every file is one take. To replace a piece of music, delete its file in public/audio/music/ yourself and run `music` again. The game never calls the API:
// it plays the mp3s in public/audio/, listed in public/audio/manifest.json.

import { mkdir, writeFile, access, rm, readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const OUT = path.join(ROOT, 'public', 'audio');
const API = 'https://api.elevenlabs.io/v1';
const FORMAT = 'output_format=mp3_44100_128';

const TOY = 'A clean, close, dry recording with no music and no voices.';
const CUTE = 'Cartoon, friendly and funny, for a young child, not scary. No music.';

/** id: [what it sounds like, seconds]. Ids ending -1, -2 are versions of one sound: the game never plays the same one twice running. */
export const SFX = {
  // --- what things are made of, as they break (toy blocks, not real buildings)
  'plaster-1': [`A few chunky wooden toy building blocks knocked over onto a table: a soft clack and tumble. ${TOY}`, 0.8],
  'plaster-2': [`A small stack of plastic toy bricks toppling: two or three soft chunky clacks. ${TOY}`, 0.8],
  'tile-1': [`A handful of small plastic tiles clattering onto a wooden floor: a light, quick clatter. ${TOY}`, 0.7],
  'tile-2': [`Several dominoes scattering on a table: a light rattling clatter. ${TOY}`, 0.7],
  'wood-1': [`A hollow wooden toy block knocked with another: one warm, hollow clonk. ${TOY}`, 0.5],
  'wood-2': [`Two wooden skittles knocked over: hollow wooden clonks. ${TOY}`, 0.7],
  'glass-1': [`A gentle tinkle of small glass wind chimes: bright and pretty, not a smash. ${TOY}`, 0.9],
  'glass-2': [`A soft, sparkly chime of a toy glockenspiel run, three quick high notes. ${TOY}`, 0.8],
  'tin-1': [`A tin toy knocked over onto a floor: a short metallic toy clang and rattle. ${TOY}`, 0.7],
  'tin-2': [`An empty biscuit tin tapped and rolling briefly: a hollow tin clank. ${TOY}`, 0.8],
  'stone-1': [`A heavy wooden block dropped on a carpeted floor: one deep, soft thunk. ${TOY}`, 0.6],
  'stone-2': [`Two large pebbles knocked together and dropped: a deep, dull clunk. ${TOY}`, 0.6],
  'rubber-1': [`A rubber ball bouncing once: a springy cartoon boing. ${TOY}`, 0.6],
  'leaves-1': [`A quick rustle of a leafy bush being brushed past. ${TOY}`, 0.6],
  'debris-1': [`One small wooden block landing on a wooden floor: a single short tap. ${TOY}`, 0.5],
  'debris-2': [`One plastic toy brick landing on a table: a single light click-clack. ${TOY}`, 0.5],
  // --- the dinosaurs
  'roar-trex-1': [`A big Tyrannosaurus rex roar, deep and powerful but playful. ${CUTE}`, 1.6],
  'roar-triceratops-1': [`A Triceratops call: a loud, brassy, snorting bellow like a happy rhino. ${CUTE}`, 1.4],
  'roar-stegosaurus-1': [`A Stegosaurus call: a low, rumbly, friendly groan-roar. ${CUTE}`, 1.4],
  'crunch-1': [`A giant cartoon bite: a huge chomp and crunch through wooden toy blocks. ${CUTE}`, 0.9],
  'crunch-2': [`A big cartoon chomp followed by wooden blocks scattering. ${CUTE}`, 0.9],
  'stomp-1': [`One enormous, heavy dinosaur footstep landing: a deep booming thud. ${TOY}`, 0.9],
  'step-1': [`One heavy, soft, padded animal footstep on grass: a low thump. ${TOY}`, 0.5],
  'step-2': [`One heavy footstep on earth: a low, soft thud. ${TOY}`, 0.5],
  'whoosh-1': [`A big, fast cartoon whoosh, like a heavy tail swinging through the air. ${TOY}`, 0.6],
  'bonk-1': [`A huge, funny cartoon BONK: a hollow wooden mallet hit. ${CUTE}`, 0.7],
  'boing-1': [`A springy cartoon boing, like bouncing off a trampoline. ${CUTE}`, 0.8],
  'whistle-1': [`A cartoon slide whistle falling in pitch, like something flying off into the distance. ${CUTE}`, 1.0],
  // --- the levels and the interface
  'bell-1': [`One big, bright fairground strongman bell ringing: a clear, happy ding. ${TOY}`, 1.8],
  'splash-1': [`A beach ball landing in a paddling pool: a round, friendly splash. ${TOY}`, 1.0],
  'firework-1': [`One firework: a short whistle up and a soft, sparkly, crackling burst. Friendly, not loud. ${TOY}`, 1.6],
  'rebuild-1': [`A springy cartoon pop, like a toy popping back into shape. ${CUTE}`, 0.5],
  'click-1': [`A soft, chunky plastic toy button click. ${TOY}`, 0.5],
  'uibonk-1': [`A gentle, low, rubbery 'nope' bonk, like tapping a soft drum once. ${CUTE}`, 0.5],
  'pop-1': [`A bright bubble pop. ${TOY}`, 0.5],
  'sparkle-1': [`A short magical sparkle: a quick rising twinkle of tiny bells. ${TOY}`, 1.0],
  'fanfare-1': [`A short, triumphant toy brass fanfare with a snare drum flourish: ta-da! Played by a toy marching band. ${CUTE.replace(' No music.', '')}`, 3.0],
};

const BAND = 'Instrumental only, no vocals. Bright, playful and bouncy, for a young child\'s toy-town game. It should loop smoothly: steady tempo, no long intro, no big ending.';

/** id: [what it sounds like, seconds]. One piece per level, plus the sandbox. */
export const MUSIC = {
  'block-town': [`A cheerful toy marching band tune at 120 BPM: a bouncy tuba oom-pah, a catchy xylophone melody, snare drum and piccolo. ${BAND}`, 40],
  'playground-park': [`A jolly fairground tune at 120 BPM: a steam-organ calliope and glockenspiel melody over a bouncy tuba and a light snare, like a happy carousel. ${BAND}`, 40],
  'castle-hill': [`A playful, heroic toy-castle march at 116 BPM: toy trumpet fanfares, a recorder melody, timpani and a snare drum roll, grand but funny. ${BAND}`, 40],
  sandbox: [`A relaxed, happy play-time tune at 110 BPM: marimba, pizzicato strings, ukulele and soft toy percussion, gently bouncing along. ${BAND}`, 40],
  farm: [`A cheerful country hoedown tune at 120 BPM: a bouncy banjo, fiddle and harmonica melody over a tuba and woodblock, like a sunny toy farm. ${BAND}`, 40],
  forest: [`A light, adventurous woodland tune at 112 BPM: a playful flute and clarinet melody over pizzicato strings, a marimba and soft woodblock, like a toy camping trip. ${BAND}`, 40],
};

const exists = (p) => access(p).then(() => true, () => false);

async function eleven(endpoint, body) {
  const key = process.env.ELEVENLABS_API_KEY;
  if (!key) throw new Error('ELEVENLABS_API_KEY is not set (put it in .env.local)');
  const res = await fetch(`${API}/${endpoint}${endpoint.includes('?') ? '&' : '?'}${FORMAT}`, {
    method: 'POST',
    headers: { 'xi-api-key': key, 'content-type': 'application/json', accept: 'audio/mpeg' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`ElevenLabs ${res.status}: ${(await res.text()).slice(0, 300)}`);
  return Buffer.from(await res.arrayBuffer());
}

async function each(folder, entries, make) {
  await mkdir(path.join(OUT, folder), { recursive: true });
  let made = 0;
  let failed = 0;
  const queue = Object.entries(entries);
  await Promise.all(Array.from({ length: 3 }, async () => {
    for (let next = queue.shift(); next; next = queue.shift()) {
      const [id, entry] = next;
      const file = path.join(OUT, folder, `${id}.mp3`);
      if (await exists(file)) continue;
      try {
        await writeFile(file, await make(entry));
        made++;
        console.log(`[${folder}/${id}] written`);
      } catch (error) {
        failed++;
        console.error(`[${folder}/${id}] FAILED: ${error.message}`);
      }
    }
  }));
  console.log(`${folder}: ${made} made, ${failed} failed`);
}

const lines = async () => JSON.parse(await readFile(path.join(ROOT, 'src', 'audio', 'lines.json'), 'utf8'));

const sfx = (only = SFX) =>
  each('sfx', only, ([text, seconds]) => eleven('sound-generation', { text, duration_seconds: seconds, prompt_influence: 0.5 }));

async function voice(only) {
  const id = process.env.ELEVENLABS_VOICE_ID;
  const model = process.env.ELEVENLABS_MODEL_ID;
  if (!id) throw new Error('ELEVENLABS_VOICE_ID is not set (put it in .env.local)');
  return each('voice', only ?? (await lines()), (text) => eleven(`text-to-speech/${id}`, model ? { text, model_id: model } : { text }));
}

/** One take per piece, and never a piece that already exists. */
async function music() {
  await mkdir(path.join(OUT, 'music'), { recursive: true });
  const missing = [];
  for (const [id, entry] of Object.entries(MUSIC)) if (!(await exists(path.join(OUT, 'music', `${id}.mp3`)))) missing.push([id, entry]);
  if (!missing.length) {
    console.log('All the music already exists; not generating it again. Delete a file first if you really want a new one.');
    return;
  }
  console.log(`Generating ${missing.length} piece(s) of music, ${missing.reduce((sum, [, [, seconds]]) => sum + seconds, 0)} seconds in total, 1 take each...`);
  for (const [id, [prompt, seconds]] of missing) {
    try {
      await writeFile(path.join(OUT, 'music', `${id}.mp3`), await eleven('music', { prompt, music_length_ms: seconds * 1000, force_instrumental: true }));
      console.log(`[music/${id}] written`);
    } catch (error) {
      console.error(`[music/${id}] FAILED: ${error.message}`);
    }
  }
}

/** The game reads this to know which files exist. */
async function manifest() {
  const list = async (folder) => ((await exists(path.join(OUT, folder))) ? (await readdir(path.join(OUT, folder))).filter((f) => f.endsWith('.mp3')).map((f) => f.slice(0, -4)).sort() : []);
  await writeFile(path.join(OUT, 'manifest.json'), JSON.stringify({ sfx: await list('sfx'), voice: await list('voice'), music: await list('music') }, null, 2) + '\n');
}

const [cmd, ...ids] = process.argv.slice(2);
if (cmd === 'sfx') {
  await sfx();
} else if (cmd === 'voice') {
  await voice();
} else if (cmd === 'music') {
  await music();
} else if (cmd === 'redo') {
  const all = await lines();
  for (const id of ids) {
    if (SFX[id]) {
      await rm(path.join(OUT, 'sfx', `${id}.mp3`), { force: true });
      await sfx({ [id]: SFX[id] });
    } else if (all[id]) {
      await rm(path.join(OUT, 'voice', `${id}.mp3`), { force: true });
      await voice({ [id]: all[id] });
    } else {
      console.error(`unknown id: ${id}`);
    }
  }
} else {
  console.log('usage: npm run audio -- sfx | voice | music | redo <id...>');
}
await manifest();
