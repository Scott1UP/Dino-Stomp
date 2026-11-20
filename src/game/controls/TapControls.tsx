import { useThree } from '@react-three/fiber';
import { useEffect } from 'react';
import * as THREE from 'three';
import { getState } from '../../ui/store';
import { game, input } from '../state';

const MAX_TAP_MOVE = 14; // px
const MAX_TAP_MS = 600;
/** Buildings are easier to tap than they look: the hit area is 20% bigger. */
const HIT_GROW = 0.2;

const ground = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);

/**
 * Tap the ground to walk there, tap a building to attack it. Taps that land on
 * the thumbstick area or the smash button never reach the canvas.
 */
export function TapControls() {
  const gl = useThree((state) => state.gl);
  const camera = useThree((state) => state.camera);

  useEffect(() => {
    const element = gl.domElement;
    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    const point = new THREE.Vector3();
    const downs = new Map<number, { x: number; y: number; at: number }>();

    const onDown = (event: PointerEvent) => {
      downs.set(event.pointerId, { x: event.clientX, y: event.clientY, at: performance.now() });
    };

    const onUp = (event: PointerEvent) => {
      const down = downs.get(event.pointerId);
      downs.delete(event.pointerId);
      if (!down || getState().screen !== 'playing') return;
      if (performance.now() - down.at > MAX_TAP_MS) return;
      if (Math.hypot(event.clientX - down.x, event.clientY - down.y) > MAX_TAP_MOVE) return;

      const rect = element.getBoundingClientRect();
      pointer.set(
        ((event.clientX - rect.left) / rect.width) * 2 - 1,
        -((event.clientY - rect.top) / rect.height) * 2 + 1,
      );
      raycaster.setFromCamera(pointer, camera);

      const town = game.town;
      let building = town?.pick(raycaster) ?? null;
      const onGround = raycaster.ray.intersectPlane(ground, point);
      if (!building && onGround) building = town?.buildingAt(point.x, point.z, HIT_GROW) ?? null;

      if (building) input.target = { kind: 'attack', building };
      else if (onGround) input.target = { kind: 'walk', x: point.x, z: point.z };
    };

    const onCancel = (event: PointerEvent) => downs.delete(event.pointerId);

    element.addEventListener('pointerdown', onDown);
    element.addEventListener('pointerup', onUp);
    element.addEventListener('pointercancel', onCancel);
    return () => {
      element.removeEventListener('pointerdown', onDown);
      element.removeEventListener('pointerup', onUp);
      element.removeEventListener('pointercancel', onCancel);
    };
  }, [gl, camera]);

  return null;
}
