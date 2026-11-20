import { useFrame } from '@react-three/fiber';
import { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { useStore } from '../../ui/store';
import { GRAPHICS } from '../graphics';
import { game } from '../state';

const OFFSET = new THREE.Vector3(55, 100, 45);
/** How far from the dino shadows are drawn. Tight, so they stay crisp. */
const REACH = 85;
/** The light moves in steps of one shadow-map texel, which stops shadow edges shimmering as he walks. */
const STEP = (REACH * 2) / 2048;

/** The one warm sun that casts shadows. It follows the dino, so the shadow map covers only what is on screen. */
export function Sun() {
  const light = useRef<THREE.DirectionalLight>(null);
  const quality = GRAPHICS[useStore((s) => s.settings.graphics)];

  // A new shadow map size only takes effect once the old map is thrown away.
  useEffect(() => {
    const sun = light.current;
    if (!sun) return;
    sun.shadow.mapSize.set(quality.shadowMap, quality.shadowMap);
    sun.shadow.map?.dispose();
    sun.shadow.map = null;
  }, [quality.shadowMap]);

  useFrame(() => {
    if (!light.current) return;
    const x = Math.round(game.dino.position.x / STEP) * STEP;
    const z = Math.round(game.dino.position.z / STEP) * STEP;
    light.current.position.set(x + OFFSET.x, OFFSET.y, z + OFFSET.z);
    light.current.target.position.set(x, 0, z);
    light.current.target.updateMatrixWorld();
  });

  return (
    <directionalLight
      ref={light}
      color="#FFF1D6"
      intensity={2.2}
      castShadow={quality.shadows}
      shadow-camera-left={-REACH}
      shadow-camera-right={REACH}
      shadow-camera-top={REACH}
      shadow-camera-bottom={-REACH}
      shadow-camera-near={1}
      shadow-camera-far={320}
      shadow-bias={-0.0006}
    />
  );
}
