import type { Graphics } from '../ui/store';

/**
 * What each graphics setting does. High is the full look; medium and low give
 * up the things that cost the most frames on an older tablet.
 */
export const GRAPHICS: Record<
  Graphics,
  { dpr: number; shadows: boolean; shadowMap: number; effects: number; maxMoving: number; detail: boolean }
> = {
  // Full resolution on a Retina screen, sharp shadows, all the confetti.
  high: { dpr: 2, shadows: true, shadowMap: 2048, effects: 1, maxMoving: 150, detail: true },
  // A little softer: fewer pixels, softer shadows, less debris left lying about.
  medium: { dpr: 1.5, shadows: true, shadowMap: 1024, effects: 0.7, maxMoving: 110, detail: true },
  // The steadiest: one pixel per point, no shadows or surface patterns, half the confetti.
  low: { dpr: 1, shadows: false, shadowMap: 512, effects: 0.5, maxMoving: 70, detail: false },
};
