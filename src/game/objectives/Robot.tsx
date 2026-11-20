import { useFrame } from '@react-three/fiber';
import { useEffect, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { audio } from '../../audio/engine';
import { speak } from '../../audio/ui';
import { actions, getState } from '../../ui/store';
import type { BuildingState, TownSystem } from '../../world/breaking/TownSystem';
import { fx } from '../../world/effects/Effects';
import { toonGradient } from '../../world/toon';
import { levelDef } from '../levels';
import { events, game } from '../state';

const SPEED = 4.2;
const BUILD_SECONDS = 1.4;
const DOWN_SECONDS = 3.2;
const GETUP_SECONDS = 1.1;
/** How close a move has to land to knock him over (on top of the move's own reach). */
const HIT_REACH = 4;

type Mode = 'walk' | 'build' | 'falling' | 'down' | 'getup';

/**
 * The secret finale: a giant wind-up toy robot that wanders the castle,
 * putting back up whatever the dino knocks down. A good hit topples him; he
 * lies there for a moment, then winds himself up and carries on.
 */
export function Robot({ town }: { town: TownSystem }) {
  const root = useRef<THREE.Group>(null);
  const body = useRef<THREE.Group>(null);
  const key = useRef<THREE.Group>(null);
  const arms = useRef<(THREE.Mesh | null)[]>([]);
  const legs = useRef<(THREE.Mesh | null)[]>([]);
  const brain = useRef({
    mode: 'walk' as Mode,
    clock: 0,
    position: new THREE.Vector3(18, 0, -14),
    facing: 0,
    target: null as BuildingState | null,
    wander: new THREE.Vector3(-18, 0, -30),
    fallDirection: new THREE.Vector3(1, 0, 0),
    walkPhase: 0,
  });

  const materials = useMemo(() => {
    const toon = (color: string) => new THREE.MeshToonMaterial({ color, gradientMap: toonGradient });
    return { blue: toon('#2F6FD6'), cream: toon('#FFFDF6'), red: toon('#E8483B'), gold: toon('#F7C531'), dark: toon('#2B2D42'), grey: toon('#9AA0A6') };
  }, []);

  useEffect(() => {
    const onHit = (centre: THREE.Vector3, radius: number) => {
      const b = brain.current;
      if (b.mode === 'falling' || b.mode === 'down' || b.mode === 'getup') return;
      if (Math.hypot(centre.x - b.position.x, centre.z - b.position.z) > radius + HIT_REACH) return;
      b.mode = 'falling';
      b.clock = 0;
      b.fallDirection.set(b.position.x - game.dino.position.x, 0, b.position.z - game.dino.position.z).normalize();
      audio.dino('bonk');
      audio.dino('boing');
      fx.shake(0.8);
      game.hitStop(90);
      speak('robot-down');
      actions.award('robot');
      const index = levelDef(getState().level).objectives.findIndex((objective) => objective.tag === 'robot');
      if (index >= 0) actions.addProgress(index as 0 | 1);
    };
    events.hit.add(onHit);
    return () => {
      events.hit.delete(onHit);
      game.robot = null;
    };
  }, []);

  useFrame((_, delta) => {
    const b = brain.current;
    const dt = Math.min(delta, 0.05);
    if (getState().screen !== 'playing') return;
    b.clock += dt;
    game.robot = b.position;

    if (b.mode === 'walk') {
      // Head for the nearest building that has been knocked down, to put it back up.
      if (!b.target || !b.target.down) {
        b.target = null;
        let best = Infinity;
        for (const building of town.buildings) {
          if (!building.down || building.kind !== 'building') continue;
          const distance = building.centre.distanceTo(b.position);
          if (distance < best) {
            best = distance;
            b.target = building;
          }
        }
      }
      const goal = b.target ? b.target.centre : b.wander;
      const dx = goal.x - b.position.x;
      const dz = goal.z - b.position.z;
      const distance = Math.hypot(dx, dz);
      const reach = b.target ? Math.max(b.target.box.max.x - b.target.box.min.x, b.target.box.max.z - b.target.box.min.z) / 2 + 4 : 2;
      if (distance <= reach) {
        if (b.target) {
          b.mode = 'build';
          b.clock = 0;
        } else {
          b.wander.set((Math.random() - 0.5) * 60, 0, -14 + (Math.random() - 0.5) * 60);
        }
      } else {
        b.position.x += (dx / distance) * SPEED * dt;
        b.position.z += (dz / distance) * SPEED * dt;
        const want = Math.atan2(dx, dz);
        b.facing += Math.atan2(Math.sin(want - b.facing), Math.cos(want - b.facing)) * (1 - Math.exp(-dt * 4));
        b.walkPhase += dt * 6;
      }
    } else if (b.mode === 'build' && b.clock >= BUILD_SECONDS) {
      // Arms up, and pop! The building springs back up.
      if (b.target?.down) {
        town.rebuildOne(b.target);
        audio.ui('rebuild');
        fx.confetti(new THREE.Vector3(b.target.centre.x, b.target.box.max.y + 2, b.target.centre.z), 24, '#2F6FD6', 10);
      }
      b.target = null;
      b.mode = 'walk';
      b.clock = 0;
    } else if (b.mode === 'falling' && b.clock >= 0.5) {
      b.mode = 'down';
      b.clock = 0;
      fx.dust(b.position.clone().addScaledVector(b.fallDirection, 6), 4, true);
      fx.confetti(new THREE.Vector3(b.position.x, 4, b.position.z), 30, undefined, 12);
    } else if (b.mode === 'down' && b.clock >= DOWN_SECONDS) {
      b.mode = 'getup';
      b.clock = 0;
      audio.ui('rebuild');
    } else if (b.mode === 'getup' && b.clock >= GETUP_SECONDS) {
      b.mode = 'walk';
      b.clock = 0;
    }

    // --- pose the model ---
    const group = root.current;
    if (!group || !body.current) return;
    group.position.copy(b.position);
    group.rotation.y = b.facing;
    const tilt =
      b.mode === 'falling' ? Math.min(b.clock / 0.5, 1) ** 2 : b.mode === 'down' ? 1 : b.mode === 'getup' ? 1 - Math.min(b.clock / GETUP_SECONDS, 1) : 0;
    // Topple away from the dino: lean the body over about the axis across that direction.
    const away = Math.atan2(b.fallDirection.x, b.fallDirection.z) - b.facing;
    body.current.rotation.set(Math.cos(away) * tilt * (Math.PI / 2) * 0.95, 0, -Math.sin(away) * tilt * (Math.PI / 2) * 0.95);
    const walking = b.mode === 'walk' ? Math.sin(b.walkPhase) * 0.45 : 0;
    legs.current.forEach((leg, i) => leg && (leg.rotation.x = (i ? -1 : 1) * walking));
    const lift = b.mode === 'build' ? -2.6 : 0;
    arms.current.forEach((arm, i) => arm && (arm.rotation.x = lift + (i ? 1 : -1) * walking));
    if (key.current) key.current.rotation.z += dt * (b.mode === 'getup' ? 14 : b.mode === 'down' ? 0 : 3);
  });

  const box = (args: [number, number, number], position: [number, number, number], material: THREE.Material) => (
    <mesh position={position} material={material} castShadow>
      <boxGeometry args={args} />
    </mesh>
  );

  return (
    <group ref={root}>
      <group ref={body}>
        {/* legs */}
        {[-1.3, 1.3].map((x, i) => (
          <mesh
            key={x}
            ref={(mesh) => {
              legs.current[i] = mesh;
            }}
            position={[x, 3.4, 0]}
            material={materials.grey}
            castShadow
          >
            <boxGeometry args={[1.5, 3.4, 1.6]} />
          </mesh>
        ))}
        {box([2.2, 0.8, 3], [-1.3, 0.4, 0.4], materials.dark)}
        {box([2.2, 0.8, 3], [1.3, 0.4, 0.4], materials.dark)}
        {/* body */}
        {box([5.4, 5, 3.6], [0, 7.4, 0], materials.blue)}
        {box([3.2, 2.2, 0.3], [0, 7.6, 1.9], materials.cream)}
        {[-0.8, 0, 0.8].map((x, i) => (
          <mesh key={x} position={[x, 7.6, 2.1]} material={[materials.red, materials.gold, materials.red][i]}>
            <cylinderGeometry args={[0.32, 0.32, 0.25, 10]} />
          </mesh>
        ))}
        {/* arms */}
        {[-3.3, 3.3].map((x, i) => (
          <group key={x} position={[x, 9.3, 0]}>
            <mesh
              ref={(mesh) => {
                arms.current[i] = mesh;
              }}
              material={materials.red}
              castShadow
            >
              <boxGeometry args={[1.1, 4.6, 1.2]} />
            </mesh>
          </group>
        ))}
        {/* head */}
        {box([3.6, 2.8, 3], [0, 11.4, 0], materials.cream)}
        {[-0.8, 0.8].map((x) => (
          <mesh key={x} position={[x, 11.6, 1.55]} rotation={[Math.PI / 2, 0, 0]} material={materials.dark}>
            <cylinderGeometry args={[0.45, 0.45, 0.2, 12]} />
          </mesh>
        ))}
        {box([1.6, 0.3, 0.2], [0, 10.6, 1.55], materials.red)}
        {box([0.25, 1.4, 0.25], [0, 13.5, 0], materials.grey)}
        <mesh position={[0, 14.3, 0]} material={materials.gold} castShadow>
          <sphereGeometry args={[0.55, 12, 8]} />
        </mesh>
        {/* the wind-up key in his back */}
        <group ref={key} position={[0, 7.6, -2.4]}>
          {box([0.4, 0.4, 1.4], [0, 0, -0.5], materials.gold)}
          {box([2.6, 1.2, 0.3], [0, 0, -1.2], materials.gold)}
        </group>
      </group>
    </group>
  );
}
