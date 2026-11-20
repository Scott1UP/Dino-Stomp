// Shrinks what the asset scripts build, before the game loads it. Run by `npm run assets` after Blender.
//
//   models     every GLB in public/models: identical meshes shared, vertices reordered,
//              then meshopt-compressed. Lossless (nothing is quantised), so the physics and
//              batching see exactly the same shapes; three.js decodes it as it loads.
//   textures   each level's playmat ground, PNG to WebP. Same pixels to the eye, a fraction
//              of the download. (KTX2 would also save graphics memory; it needs KTX-Software.)
//
// Files already compressed are skipped, so it is safe to run again.

import { readdir, stat, unlink } from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS, EXTMeshoptCompression } from '@gltf-transform/extensions';
import { dedup, prune, reorder } from '@gltf-transform/functions';
import { MeshoptDecoder, MeshoptEncoder } from 'meshoptimizer';
import sharp from 'sharp';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const MODELS = path.join(ROOT, 'public', 'models');
const TEXTURES = path.join(ROOT, 'public', 'textures');
const mb = (bytes) => `${(bytes / 1e6).toFixed(2)} MB`;

await MeshoptEncoder.ready;
await MeshoptDecoder.ready;
// The decoder too, so files that are already compressed can be read (and then skipped).
const io = new NodeIO()
  .registerExtensions(ALL_EXTENSIONS)
  .registerDependencies({ 'meshopt.encoder': MeshoptEncoder, 'meshopt.decoder': MeshoptDecoder });

async function models(folder) {
  for (const entry of await readdir(folder, { withFileTypes: true })) {
    const file = path.join(folder, entry.name);
    if (entry.isDirectory()) {
      await models(file);
      continue;
    }
    if (!entry.name.endsWith('.glb')) continue;
    const doc = await io.read(file);
    if (doc.getRoot().listExtensionsUsed().some((ext) => ext.extensionName === 'EXT_meshopt_compression')) continue;
    doc.setLogger({ debug() {}, info() {}, warn() {}, error: console.error });
    const before = (await stat(file)).size;
    // keepLeaves: the empty marker nodes (the dino's spawn point, the level's size and pool) carry data the game reads.
    await doc.transform(dedup(), prune({ keepLeaves: true, keepExtras: true }), reorder({ encoder: MeshoptEncoder }));
    doc.createExtension(EXTMeshoptCompression).setRequired(true).setEncoderOptions({ method: EXTMeshoptCompression.EncoderMethod.QUANTIZE });
    await io.write(file, doc);
    console.log(`[compress] ${path.relative(ROOT, file)}: ${mb(before)} -> ${mb((await stat(file)).size)}`);
  }
}

async function textures() {
  for (const name of await readdir(TEXTURES)) {
    if (!name.endsWith('-ground.png')) continue;
    const file = path.join(TEXTURES, name);
    const out = file.replace(/\.png$/, '.webp');
    const before = (await stat(file)).size;
    await sharp(file).webp({ quality: 90, effort: 6 }).toFile(out);
    await unlink(file);
    console.log(`[compress] ${path.relative(ROOT, out)}: ${mb(before)} -> ${mb((await stat(out)).size)}`);
  }
}

await models(MODELS);
await textures();
