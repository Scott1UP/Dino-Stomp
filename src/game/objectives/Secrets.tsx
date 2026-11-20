import { useGLTF } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import { useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';
import { clone as cloneSkinned } from 'three/examples/jsm/utils/SkeletonUtils.js';
import { audio } from '../../audio/engine';
import { speak } from '../../audio/ui';
import { actions, getState } from '../../ui/store';
import type { TownSystem } from '../../world/breaking/TownSystem';
import { fx } from '../../world/effects/Effects';
import { toonGradient } from '../../world/toon';
import { events, game } from '../state';

const COLLECT_DISTANCE = 5;
/** Every so often a few gold sparkles rise from the building hiding the golden dino: a hint, not a signpost. */
const HINT_SECONDS = 7;

/**
 * Each level hides one golden dino inside an ordinary building. Knock that
 * building down and the golden dino is revealed; walk into it to collect it.
 * Finding them all opens the Robot Castle.
 */
export function Secrets({ town }: { town: TownSystem }) {
  const hideout = useMemo(() => town.buildings.find((building) => building.meta.secret), [town]);
  const [revealed, setRevealed] = useState(false);
  const [collected, setCollected] = useState(false);
  const statue = useRef<THREE.Group>(null);
  const hintAt = useRef(HINT_SECONDS);

  const gltf = useGLTF('/models/dinos/trex.glb');
  const model = useMemo(() => {
    const scene = cloneSkinned(gltf.scene);
    const gold = new THREE.MeshToonMaterial({ color: '#FFD84D', emissive: '#8a5a00', emissiveIntensity: 0.35, gradientMap: toonGradient });
    scene.traverse((object) => {
      const mesh = object as THREE.Mesh;
      if (!mesh.isMesh) return;
      mesh.material = gold;
      mesh.castShadow = true;
      mesh.frustumCulled = false;
    });
    return scene;
  }, [gltf]);

  useEffect(() => {
    if (!hideout) return;
    const onDown = (building: typeof hideout) => {
      if (building !== hideout || revealed) return;
      setRevealed(true);
      audio.ui('sparkle');
      fx.confetti(new THREE.Vector3(hideout.centre.x, 6, hideout.centre.z), 30, '#FFD84D', 10);
    };
    events.down.add(onDown);
    return () => {
      events.down.delete(onDown);
    };
  }, [hideout, revealed]);

  useFrame(({ clock }, delta) => {
    if (!hideout || collected) return;
    if (!revealed) {
      hintAt.current -= delta;
      if (hintAt.current <= 0 && getState().screen === 'playing') {
        hintAt.current = HINT_SECONDS;
        fx.confetti(new THREE.Vector3(hideout.centre.x, hideout.box.max.y + 1, hideout.centre.z), 5, '#FFD84D', 3);
      }
      return;
    }
    const group = statue.current;
    if (!group) return;
    group.position.set(hideout.centre.x, 0.6 + Math.abs(Math.sin(clock.elapsedTime * 2.4)) * 0.8, hideout.centre.z);
    group.rotation.y = clock.elapsedTime * 1.4;
    const near = Math.hypot(game.dino.position.x - hideout.centre.x, game.dino.position.z - hideout.centre.z);
    if (near < COLLECT_DISTANCE + game.dino.radius && getState().screen === 'playing') {
      setCollected(true);
      audio.ui('sparkle');
      audio.fanfare();
      fx.confetti(new THREE.Vector3(hideout.centre.x, 4, hideout.centre.z), 70, '#FFD84D', 14);
      speak('secret-found');
      actions.findSecret(getState().level);
    }
  });

  if (!hideout || !revealed || collected) return null;
  return (
    <group ref={statue} scale={0.32}>
      <primitive object={model} />
    </group>
  );
}
