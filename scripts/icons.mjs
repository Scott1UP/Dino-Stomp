// Makes the app's icons and its link-preview picture from art already in the project (after dino-safari's).
//
//   npm run icons
//
//   public/favicon.ico            16, 32 and 48 pixel browser tab icon
//   public/icon-192.png           home-screen icons (see public/manifest.webmanifest)
//   public/icon-512.png
//   public/icon-maskable-512.png  the same, filling the whole square so Android can cut its own shape
//   public/apple-touch-icon.png   home-screen icon for iPhones and iPads
//   public/og.jpg                 the picture shown when a link to the game is shared
//   android/app/src/main/res/mipmap-*/   launcher icons for the Android app
//
// The icon is the Dino Stomp logo, as large as it will go, on the yellow sunburst from the
// level-complete screen. At tab-icon size the logo would be a smudge, so the favicon is just
// the T. rex's head.
import { existsSync } from 'node:fs';
import { writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import sharp from 'sharp';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const pub = join(root, 'public');
const ui = (name) => join(pub, 'ui', `${name}.webp`);
const CLEAR = { r: 0, g: 0, b: 0, alpha: 0 };

const logo = await sharp(ui('logo')).trim().png().toBuffer();
// The T. rex's head, from its sticker.
const rex = await sharp(ui('sticker-trex')).png().toBuffer();
const rexSize = await sharp(rex).metadata();
const head = await sharp(rex)
  .extract({ left: Math.round(rexSize.width * 0.54), top: 0, width: Math.round(rexSize.width * 0.46), height: Math.round(rexSize.height * 0.5) })
  .trim()
  .png()
  .toBuffer();

/** The logo or the T. rex's head, fitted inside a square `side` pixels across. */
const mark = (which, side) => sharp(which === 'head' ? head : logo).resize({ width: side, height: side, fit: 'inside' }).png().toBuffer();

/** A square of yellow sunburst, warmer towards the edges. */
function tile(size) {
  const rays = Array.from({ length: 20 }, (_, i) => {
    const a = (i / 20) * Math.PI * 2;
    const b = ((i + 0.5) / 20) * Math.PI * 2;
    const c = size / 2;
    const r = size;
    return `<polygon points="${c},${c} ${c + r * Math.cos(a)},${c + r * Math.sin(a)} ${c + r * Math.cos(b)},${c + r * Math.sin(b)}" fill="#ffd965"/>`;
  }).join('');
  return sharp(
    Buffer.from(
      `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}">
        <defs><radialGradient id="v" cx="50%" cy="50%" r="72%">
          <stop offset="0.4" stop-color="#e88a00" stop-opacity="0"/><stop offset="1" stop-color="#e88a00" stop-opacity="0.45"/>
        </radialGradient></defs>
        <rect width="${size}" height="${size}" fill="#ffc533"/>${rays}
        <rect width="${size}" height="${size}" fill="url(#v)"/>
      </svg>`,
    ),
  )
    .png()
    .toBuffer();
}

/**
 * A square icon: the logo (or, for `which: 'head'`, the T. rex's head) on a tile of sunburst.
 * `corner` rounds the tile (as a fraction of its size); `fill` is how much of the tile's width the mark may take.
 */
async function icon(size, { corner = 0, fill = 0.9, which = 'logo' } = {}) {
  const top = await mark(which, Math.round(size * fill));
  const m = await sharp(top).metadata();
  const flat = await sharp(await tile(size))
    .composite([{ input: top, left: Math.round((size - m.width) / 2), top: Math.round((size - m.height) / 2) }])
    .png()
    .toBuffer();
  if (!corner) return flat;
  const mask = Buffer.from(
    `<svg xmlns="http://www.w3.org/2000/svg" width="${size}" height="${size}"><rect width="${size}" height="${size}" rx="${size * corner}" fill="#fff"/></svg>`,
  );
  return sharp(flat).composite([{ input: mask, blend: 'dest-in' }]).png().toBuffer();
}

/** An .ico file holding the given PNG pictures (each one square, and smaller than 256 pixels). */
function ico(pngs) {
  const header = Buffer.alloc(6 + 16 * pngs.length);
  header.writeUInt16LE(1, 2); // type: icon
  header.writeUInt16LE(pngs.length, 4);
  let offset = header.length;
  pngs.forEach(({ size, data }, n) => {
    const at = 6 + 16 * n;
    header.writeUInt8(size, at);
    header.writeUInt8(size, at + 1);
    header.writeUInt16LE(1, at + 4); // colour planes
    header.writeUInt16LE(32, at + 6); // bits per pixel
    header.writeUInt32LE(data.length, at + 8);
    header.writeUInt32LE(offset, at + 12);
    offset += data.length;
  });
  return Buffer.concat([header, ...pngs.map((p) => p.data)]);
}

async function write(name, data) {
  await writeFile(join(pub, name), data);
  console.log(`wrote public/${name}`);
}

// The tab icon is a rounded tile with the head nearly filling it, so it still reads at 16 pixels.
const tab = { corner: 0.22, fill: 0.94, which: 'head' };
await write('favicon.ico', ico(await Promise.all([16, 32, 48].map(async (size) => ({ size, data: await icon(size, tab) })))));
await write('icon-192.png', await icon(192, { corner: 0.22 }));
await write('icon-512.png', await icon(512, { corner: 0.22 }));
// Android may crop a maskable icon to a circle 80% of its width, so the logo stays inside that.
await write('icon-maskable-512.png', await icon(512, { fill: 0.68 }));
// iOS rounds the corners itself, and shows black wherever an icon is see-through.
await write('apple-touch-icon.png', await icon(180));

// The Android app's launcher icons, one set for each screen density, if the Android project is there.
// Newer Android builds the icon from two layers, a background and a foreground, each 108 units square,
// and cuts its own shape out of the middle 72: so the background is the sunburst and the foreground is
// the logo, kept well inside. The other two pictures are whole icons, for older launchers.
const res = join(root, 'android/app/src/main/res');
if (existsSync(res)) {
  const densities = { mdpi: 1, hdpi: 1.5, xhdpi: 2, xxhdpi: 3, xxxhdpi: 4 };
  for (const [density, scale] of Object.entries(densities)) {
    const size = 48 * scale;
    const full = 108 * scale;
    const top = await mark('logo', Math.round(full * 0.6));
    const m = await sharp(top).metadata();
    const y = Math.round((full - m.height) / 2);
    const x = Math.round((full - m.width) / 2);
    const files = {
      'ic_launcher.png': await icon(size, { corner: 0.22 }),
      'ic_launcher_round.png': await icon(size, { corner: 0.5, fill: 0.74 }),
      'ic_launcher_background.png': await tile(full),
      'ic_launcher_foreground.png': await sharp(top)
        .extend({ top: y, bottom: full - m.height - y, left: x, right: full - m.width - x, background: CLEAR })
        .png()
        .toBuffer(),
    };
    for (const [name, data] of Object.entries(files)) {
      await writeFile(join(res, `mipmap-${density}`, name), data);
      console.log(`wrote android/app/src/main/res/mipmap-${density}/${name}`);
    }
  }
}

// The link preview: three of the levels side by side, sliced on the slant, dimmed, with the logo over them.
const OG_W = 1200;
const OG_H = 630;
const strips = ['block-town', 'farm', 'hogwarts'];
const lean = 120;
const slice = async (id, i) => {
  const w = OG_W / strips.length;
  const x0 = i * w;
  const x1 = (i + 1) * w;
  const corners = `${x0 + (i ? lean / 2 : -lean)},0 ${x1 + lean / 2},0 ${x1 - lean / 2},${OG_H} ${x0 - (i ? lean / 2 : lean)},${OG_H}`;
  const cut = Buffer.from(`<svg xmlns="http://www.w3.org/2000/svg" width="${OG_W}" height="${OG_H}"><polygon points="${corners}" fill="#fff"/></svg>`);
  const picture = await sharp(ui(`level-${id}`)).resize(Math.round(w + lean * 2), OG_H, { fit: 'cover' }).png().toBuffer();
  const placed = await sharp({ create: { width: OG_W, height: OG_H, channels: 4, background: CLEAR } })
    .composite([{ input: picture, left: Math.max(0, Math.round(x0 - lean)), top: 0 }])
    .png()
    .toBuffer();
  return sharp(placed).composite([{ input: cut, blend: 'dest-in' }]).png().toBuffer();
};
const seams = Buffer.from(
  `<svg xmlns="http://www.w3.org/2000/svg" width="${OG_W}" height="${OG_H}">${[1, 2]
    .map((i) => `<line x1="${(i * OG_W) / 3 + lean / 2}" y1="0" x2="${(i * OG_W) / 3 - lean / 2}" y2="${OG_H}" stroke="#fff7e3" stroke-width="8"/>`)
    .join('')}</svg>`,
);
const backdrop = await sharp({ create: { width: OG_W, height: OG_H, channels: 3, background: '#bfe3f2' } })
  .composite([...(await Promise.all(strips.map((id, i) => slice(id, i)))).map((input) => ({ input })), { input: seams }])
  .png()
  .toBuffer();
const dim = Buffer.from(
  `<svg xmlns="http://www.w3.org/2000/svg" width="${OG_W}" height="${OG_H}">
    <defs><radialGradient id="d" cx="50%" cy="50%" r="65%">
      <stop offset="0" stop-color="#1c2a3a" stop-opacity="0.55"/><stop offset="1" stop-color="#1c2a3a" stop-opacity="0.2"/>
    </radialGradient></defs>
    <rect width="${OG_W}" height="${OG_H}" fill="url(#d)"/>
  </svg>`,
);
const title = await sharp(logo).resize(OG_W - 420, OG_H - 110, { fit: 'inside' }).png().toBuffer();
const t = await sharp(title).metadata();
await write(
  'og.jpg',
  await sharp(backdrop)
    .composite([{ input: dim }, { input: title, left: Math.round((OG_W - t.width) / 2), top: Math.round((OG_H - t.height) / 2) }])
    .jpeg({ quality: 86, mozjpeg: true })
    .toBuffer(),
);
