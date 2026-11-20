import { useFrame } from '@react-three/fiber';
import { useRef } from 'react';
import * as THREE from 'three';
import { getState } from '../../ui/store';
import { game } from '../state';

const PITCH = THREE.MathUtils.degToRad(50);
const DISTANCE = 70; // close enough that the smashing fills the screen
const OFFSET = new THREE.Vector3(0, Math.sin(PITCH) * DISTANCE, Math.cos(PITCH) * DISTANCE);

/** A fixed high, angled view that follows the dino. There are no camera controls. */
export function FollowCamera() {
  const focus = useRef<THREE.Vector3 | null>(null);

  useFrame(({ camera, clock }, delta) => {
    if (!focus.current) focus.current = game.dino.position.clone();
    // After a level loads the dino may be far from the last one's: jump there, don't glide.
    if (focus.current.distanceTo(game.dino.position) > 60) focus.current.copy(game.dino.position);
    focus.current.lerp(game.dino.position, 1 - Math.exp(-delta * 5));
    camera.position.copy(focus.current).add(OFFSET);
    camera.lookAt(focus.current);

    // Screen shake: small, quick to fade, and off if a parent turned it off.
    game.shake = Math.max(0, game.shake - delta * 2.8);
    if (game.shake > 0 && getState().settings.shake) {
      const amount = game.shake ** 2 * 1.3;
      const t = clock.elapsedTime * 55;
      camera.position.x += Math.sin(t) * amount;
      camera.position.y += Math.cos(t * 1.3) * amount;
    }
  });

  return null;
}
