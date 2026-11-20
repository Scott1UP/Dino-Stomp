import * as THREE from 'three';
import type { BuildingState, TownSystem } from '../world/breaking/TownSystem';

/**
 * Shared per-frame game state. Plain mutable objects, read and written from
 * `useFrame` and the physics step, so nothing here ever triggers a React render.
 */
export const game = {
  town: null as TownSystem | null,
  dino: {
    position: new THREE.Vector3(),
    facing: 0,
    radius: 2,
  },
  /** Half the width of the playable area. The dino can't walk past it. */
  bounds: 96,
  /** How much confetti and dust to throw about, from the graphics setting (1 is all of it). */
  effects: 1,
  /** Screen shake, 0 to 1. It fades by itself. */
  shake: 0,
  /** Freeze the world for a few milliseconds on a big hit, so it feels heavy. Set by the app. */
  hitStop: (_ms: number) => {},
};

export type TapTarget =
  | { kind: 'walk'; x: number; z: number }
  | { kind: 'attack'; building: BuildingState };

export const input = {
  /** Thumbstick, -1..1 on each axis. `y` is up the screen. */
  stick: { x: 0, y: 0, active: false },
  /** Keyboard, for testing. */
  keys: { x: 0, y: 0 },
  /** The power of a smash waiting to happen (1 is a tap, up to 1.2 fully charged), or 0 for none. */
  smash: 0,
  /** True while the smash button or Space is held down, charging the move. */
  charging: false,
  chargeSince: 0,
  /** Where a tap sent the dino. The thumbstick always cancels this. */
  target: null as TapTarget | null,
};

/** Smash pressed: start winding the move up. */
export function beginCharge() {
  if (input.charging) return;
  input.charging = true;
  input.chargeSince = performance.now();
}

/** How charged the move is right now, 0 to 1. */
export function chargeLevel(seconds: number) {
  return input.charging ? Math.min((performance.now() - input.chargeSince) / (seconds * 1000), 1) : 0;
}

/** Smash let go: the move fires, stronger the longer it was held. */
export function releaseCharge(seconds: number, bonus: number) {
  if (!input.charging) return;
  input.smash = 1 + bonus * chargeLevel(seconds);
  input.charging = false;
}
