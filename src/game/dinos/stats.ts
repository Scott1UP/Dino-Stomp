import type { DinoId, DinoStats } from '../../types';

/**
 * How each dino moves and smashes. These are the numbers to tune for feel:
 * speeds are in metres per second, on a map 200 m across.
 */
export const STATS: Record<DinoId, DinoStats> = {
  // Bite: a lunge that smashes a long path in whatever direction he is facing, and throws it all that way.
  trex: { id: 'trex', speed: 19.5, move: 'bite', moveRadius: 7, moveLength: 16, pushStrength: 17, cooldownSeconds: 0.7 },
  // Line: ploughs through a row of things until it meets something big, then bounces back.
  triceratops: { id: 'triceratops', speed: 22, move: 'charge', moveRadius: 3.7, moveLength: 10, pushStrength: 13, cooldownSeconds: 0.9 },
  // Launch: knocks things a long way, so they crash into other things.
  stegosaurus: { id: 'stegosaurus', speed: 17, move: 'tailSwing', moveRadius: 12.5, pushStrength: 24, cooldownSeconds: 0.9 },
};

/** The capsule that stands in for each dino in the physics world. */
export const BODIES: Record<DinoId, { radius: number; height: number }> = {
  trex: { radius: 2.1, height: 11 },
  triceratops: { radius: 2.4, height: 7.4 },
  stegosaurus: { radius: 2.4, height: 7.8 },
};

/** How long after a move starts its hit lands, to match the animation. */
export const WIND_UP: Record<DinoStats['move'], number> = { bite: 0.2, charge: 0.05, tailSwing: 0.3 };
export const CHARGE_SPEED = 30;
/** The charge strikes this many times a second as it dashes (the physics runs at 60). */
export const CHARGE_HITS_PER_SECOND = 10;

/** Holding the smash button winds the move up: this long for full power... */
export const CHARGE_SECONDS = 1;
/** ...which is this much stronger than a quick tap. */
export const CHARGE_BONUS = 0.2;
