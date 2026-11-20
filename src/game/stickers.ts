/**
 * The sticker book. Each sticker is earned once, and kept.
 *
 * Level stickers are the level's own picture in a round frame; the others are
 * generated art (`npm run art`). Every sticker has a spoken name, and a spoken
 * hint for when he taps one he hasn't got yet.
 */

export interface StickerDef {
  id: string;
  art: string;
  /** A level's sticker is round, framing the level's picture. */
  round?: boolean;
}

export const STICKERS: StickerDef[] = [
  { id: 'level-block-town', art: '/ui/level-block-town.webp', round: true },
  { id: 'level-playground-park', art: '/ui/level-playground-park.webp', round: true },
  { id: 'level-farm', art: '/ui/level-farm.webp', round: true },
  { id: 'level-forest', art: '/ui/level-forest.webp', round: true },
  { id: 'level-castle-hill', art: '/ui/level-castle-hill.webp', round: true },
  { id: 'level-hogwarts', art: '/ui/level-hogwarts.webp', round: true },
  { id: 'level-robot-castle', art: '/ui/level-robot-castle.webp', round: true },
  { id: 'first-smash', art: '/ui/sticker-first-smash.webp' },
  { id: 'tower', art: '/ui/sticker-tower.webp' },
  { id: 'dominoes', art: '/ui/sticker-dominoes.webp' },
  { id: 'big-wheel', art: '/ui/sticker-big-wheel.webp' },
  { id: 'sunflower', art: '/ui/sticker-sunflower.webp' },
  { id: 'treehouse', art: '/ui/sticker-treehouse.webp' },
  { id: 'giant-tower', art: '/ui/sticker-giant-tower.webp' },
  { id: 'catch', art: '/ui/sticker-catch.webp' },
  { id: 'power', art: '/ui/sticker-power.webp' },
  { id: 'secret', art: '/ui/sticker-secret.webp' },
  { id: 'robot', art: '/ui/sticker-robot.webp' },
];

export const stickerDef = (id: string) => STICKERS.find((sticker) => sticker.id === id);
