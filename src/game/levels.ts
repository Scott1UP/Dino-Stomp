import type { DinoId } from '../types';

export type LevelId = 'block-town' | 'playground-park' | 'castle-hill' | 'farm' | 'forest' | 'hogwarts' | 'robot-castle';
export type Mode = 'story' | 'sandbox';

export interface ObjectiveDef {
  id: string;
  /**
   * What counts towards it. A building or prop carries this tag from the level
   * layout; `smash` counts any building knocked over, and `domino` counts each
   * domino run finished.
   */
  tag: string;
  /** A rendered picture of the target, shown in the progress display. */
  icon: string;
  required: number;
}

export interface LevelDef {
  id: LevelId;
  /** Shown on the level card and spoken aloud. */
  name: string;
  model: string;
  ground: string;
  card: string;
  /** Which music theme plays. */
  theme: number;
  /** The secret finale: it opens once every golden dino has been found. */
  secret?: boolean;
  objectives: [ObjectiveDef, ObjectiveDef];
}

/** Everything is about knocking things over: the big landmarks, and lots of everything else. */
export const LEVELS: LevelDef[] = [
  {
    id: 'block-town',
    name: 'Block Town',
    model: '/models/block-town.glb',
    ground: '/textures/block-town-ground.webp',
    card: '/ui/level-block-town.webp',
    theme: 0,
    objectives: [
      { id: 'towers', tag: 'tower', icon: '/ui/icon-tower.webp', required: 5 },
      { id: 'smash', tag: 'smash', icon: '/ui/icon-house.webp', required: 20 },
    ],
  },
  {
    id: 'playground-park',
    name: 'Playground Park',
    model: '/models/playground-park.glb',
    ground: '/textures/playground-park-ground.webp',
    card: '/ui/level-playground-park.webp',
    theme: 1,
    objectives: [
      { id: 'dominoes', tag: 'domino', icon: '/ui/icon-domino.webp', required: 4 },
      { id: 'rides', tag: 'ride', icon: '/ui/icon-ride.webp', required: 6 },
    ],
  },
  {
    id: 'farm',
    name: 'Sunny Farm',
    model: '/models/farm.glb',
    ground: '/textures/farm-ground.webp',
    card: '/ui/level-farm.webp',
    theme: 4,
    objectives: [
      { id: 'barns', tag: 'barn', icon: '/ui/icon-barn.webp', required: 8 },
      { id: 'giants', tag: 'giant', icon: '/ui/icon-giant.webp', required: 15 },
    ],
  },
  {
    id: 'forest',
    name: 'Pine Forest',
    model: '/models/forest.glb',
    ground: '/textures/forest-ground.webp',
    card: '/ui/level-forest.webp',
    theme: 5,
    objectives: [
      { id: 'lookouts', tag: 'lookout', icon: '/ui/icon-lookout.webp', required: 12 },
      { id: 'smash', tag: 'smash', icon: '/ui/icon-house.webp', required: 25 },
    ],
  },
  {
    id: 'castle-hill',
    name: 'Castle Hill',
    model: '/models/castle-hill.glb',
    ground: '/textures/castle-hill-ground.webp',
    card: '/ui/level-castle-hill.webp',
    theme: 2,
    objectives: [
      { id: 'walls', tag: 'wall', icon: '/ui/icon-wall.webp', required: 14 },
      { id: 'giantTower', tag: 'giantTower', icon: '/ui/icon-giantTower.webp', required: 1 },
    ],
  },
  {
    id: 'hogwarts',
    name: 'Hogwarts',
    model: '/models/hogwarts.glb',
    ground: '/textures/hogwarts-ground.webp',
    card: '/ui/level-hogwarts.webp',
    theme: 6,
    objectives: [
      { id: 'spires', tag: 'spire', icon: '/ui/icon-spire.webp', required: 8 },
      { id: 'smash', tag: 'smash', icon: '/ui/icon-house.webp', required: 25 },
    ],
  },
  {
    // Castle Hill again, with a giant wind-up robot wandering about rebuilding it.
    id: 'robot-castle',
    name: 'Robot Castle',
    model: '/models/castle-hill.glb',
    ground: '/textures/castle-hill-ground.webp',
    card: '/ui/level-robot-castle.webp',
    theme: 2,
    secret: true,
    objectives: [
      { id: 'robot', tag: 'robot', icon: '/ui/sticker-robot.webp', required: 5 },
      { id: 'smash', tag: 'smash', icon: '/ui/icon-house.webp', required: 30 },
    ],
  },
];

/** The levels with a golden dino hidden in them. */
export const SECRET_LEVELS = LEVELS.filter((level) => !level.secret).map((level) => level.id);

export const SANDBOX_THEME = 3;

export const levelDef = (id: LevelId) => LEVELS.find((level) => level.id === id)!;

export const DINOS: { id: DinoId; name: string; colour: string; dark: string }[] = [
  { id: 'trex', name: 'T. rex', colour: '#3FA34D', dark: '#2A7436' },
  { id: 'triceratops', name: 'Triceratops', colour: '#7B5CC9', dark: '#553C98' },
  { id: 'stegosaurus', name: 'Stegosaurus', colour: '#1FA2A0', dark: '#13716F' },
];

export const dinoDef = (id: DinoId) => DINOS.find((d) => d.id === id) ?? DINOS[0];
