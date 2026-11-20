import { useFrame } from '@react-three/fiber';
import { useMemo, useRef } from 'react';
import * as THREE from 'three';
import { game } from '../../game/state';

/**
 * Everything that makes a hit feel big: dust puffs, confetti in the
 * building's own colours, ground rings and bouncing stars. Each kind is one
 * instanced mesh, so a whole collapse's worth costs a few draw calls.
 *
 * Other systems call `fx.*`; this component only draws and ages what they asked for.
 */

const DUST = 48;
const CONFETTI = 280;
const RINGS = 5;

interface Puff {
  position: THREE.Vector3;
  velocity: THREE.Vector3;
  age: number;
  life: number;
  size: number;
}
interface Bit extends Puff {
  spin: THREE.Vector3;
  rotation: THREE.Euler;
  colour: THREE.Color;
}
interface Ring {
  position: THREE.Vector3;
  age: number;
  life: number;
  radius: number;
}

const dust: Puff[] = [];
const bits: Bit[] = [];
const rings: Ring[] = [];
const BRIGHT = ['#E8483B', '#F7C531', '#2F6FD6', '#F28C28', '#EE6FA8'];
let lastDustAt = 0;

export const fx = {
  /** A puff of dust where something broke. Throttled, so a collapse doesn't fog the screen. */
  dust(at: THREE.Vector3, size = 1.6, force = false) {
    const now = performance.now();
    if (!force && now - lastDustAt < 35 / game.effects) return;
    lastDustAt = now;
    if (dust.length >= DUST) dust.shift();
    dust.push({
      position: at.clone(),
      velocity: new THREE.Vector3((Math.random() - 0.5) * 2, 1.5 + Math.random() * 2, (Math.random() - 0.5) * 2),
      age: 0,
      life: 0.55 + Math.random() * 0.3,
      size: size * (0.7 + Math.random() * 0.6),
    });
  },

  /** Confetti: breaking things should feel like a reward. */
  confetti(at: THREE.Vector3, count: number, colour?: string, burst = 9) {
    count = Math.ceil(count * game.effects);
    for (let i = 0; i < count; i++) {
      if (bits.length >= CONFETTI) bits.shift();
      bits.push({
        position: at.clone(),
        velocity: new THREE.Vector3((Math.random() - 0.5) * burst, burst * (0.6 + Math.random() * 0.8), (Math.random() - 0.5) * burst),
        spin: new THREE.Vector3(Math.random() * 12, Math.random() * 12, Math.random() * 12),
        rotation: new THREE.Euler(Math.random() * 6, Math.random() * 6, 0),
        age: 0,
        life: 1.3 + Math.random() * 0.8,
        size: 0.8 + Math.random() * 0.6,
        colour: new THREE.Color(colour && Math.random() < 0.7 ? colour : BRIGHT[Math.floor(Math.random() * BRIGHT.length)]),
      });
    }
  },

  /** An expanding ring on the ground: it shows the area of a move. */
  ring(at: THREE.Vector3, radius: number) {
    if (rings.length >= RINGS) rings.shift();
    rings.push({ position: new THREE.Vector3(at.x, 0.12, at.z), age: 0, life: 0.45, radius });
  },

  /** Small, quick to fade, and limited in strength. Parents can turn it off. */
  shake(amount: number) {
    game.shake = Math.min(Math.max(game.shake, amount), 1);
  },

  fireworks(at: THREE.Vector3) {
    for (let i = 0; i < 5; i++) {
      window.setTimeout(() => {
        const where = at.clone().add(new THREE.Vector3((Math.random() - 0.5) * 40, 16 + Math.random() * 14, (Math.random() - 0.5) * 30));
        fx.confetti(where, 34, BRIGHT[i % BRIGHT.length], 16);
      }, i * 320);
    }
  },
};

const _matrix = new THREE.Matrix4();
const _quaternion = new THREE.Quaternion();
const _scale = new THREE.Vector3();
const _hidden = new THREE.Matrix4().makeScale(0, 0, 0);

export function Effects() {
  const dustMesh = useRef<THREE.InstancedMesh>(null);
  const bitMesh = useRef<THREE.InstancedMesh>(null);
  const ringMeshes = useRef<(THREE.Mesh | null)[]>([]);
  const ringMaterials = useMemo(
    () => Array.from({ length: RINGS }, () => new THREE.MeshBasicMaterial({ color: '#FFFDF6', transparent: true, depthWrite: false })),
    [],
  );

  useFrame((_, delta) => {
    const dt = Math.min(delta, 0.05);

    const puffs = dustMesh.current;
    if (puffs) {
      for (let i = dust.length - 1; i >= 0; i--) if ((dust[i].age += dt) >= dust[i].life) dust.splice(i, 1);
      for (let i = 0; i < DUST; i++) {
        const puff = dust[i];
        if (!puff) {
          puffs.setMatrixAt(i, _hidden);
          continue;
        }
        puff.position.addScaledVector(puff.velocity, dt);
        puff.velocity.multiplyScalar(1 - dt * 2.5);
        const t = puff.age / puff.life;
        // Grows fast, then shrinks away (a stand-in for fading, which instances can't do cheaply).
        const s = puff.size * (t < 0.3 ? t / 0.3 : 1 - (t - 0.3) / 0.7) * 1.4;
        puffs.setMatrixAt(i, _matrix.compose(puff.position, _quaternion.identity(), _scale.setScalar(Math.max(s, 0.001))));
      }
      puffs.instanceMatrix.needsUpdate = true;
    }

    const confetti = bitMesh.current;
    if (confetti) {
      for (let i = bits.length - 1; i >= 0; i--) if ((bits[i].age += dt) >= bits[i].life) bits.splice(i, 1);
      for (let i = 0; i < CONFETTI; i++) {
        const bit = bits[i];
        if (!bit) {
          confetti.setMatrixAt(i, _hidden);
          continue;
        }
        bit.velocity.y -= 16 * dt;
        bit.velocity.multiplyScalar(1 - dt * 1.2);
        bit.position.addScaledVector(bit.velocity, dt);
        if (bit.position.y < 0.15) {
          bit.position.y = 0.15;
          bit.velocity.set(0, 0, 0);
        } else {
          bit.rotation.x += bit.spin.x * dt;
          bit.rotation.y += bit.spin.y * dt;
        }
        const fade = Math.min(1, (bit.life - bit.age) / 0.3);
        confetti.setMatrixAt(i, _matrix.compose(bit.position, _quaternion.setFromEuler(bit.rotation), _scale.setScalar(bit.size * fade)));
        confetti.setColorAt(i, bit.colour);
      }
      confetti.instanceMatrix.needsUpdate = true;
      if (confetti.instanceColor) confetti.instanceColor.needsUpdate = true;
    }

    for (let i = rings.length - 1; i >= 0; i--) if ((rings[i].age += dt) >= rings[i].life) rings.splice(i, 1);
    for (let i = 0; i < RINGS; i++) {
      const mesh = ringMeshes.current[i];
      if (!mesh) continue;
      const ring = rings[i];
      mesh.visible = !!ring;
      if (!ring) continue;
      const t = ring.age / ring.life;
      const eased = 1 - (1 - t) ** 3;
      mesh.position.copy(ring.position);
      mesh.scale.setScalar(ring.radius * (0.25 + 0.75 * eased));
      ringMaterials[i].opacity = 0.75 * (1 - t);
    }
  });

  return (
    <>
      <instancedMesh ref={dustMesh} args={[undefined, undefined, DUST]} frustumCulled={false}>
        <icosahedronGeometry args={[1, 0]} />
        <meshToonMaterial color="#FFF4DC" />
      </instancedMesh>
      <instancedMesh ref={bitMesh} args={[undefined, undefined, CONFETTI]} frustumCulled={false}>
        <planeGeometry args={[0.7, 0.45]} />
        <meshBasicMaterial side={THREE.DoubleSide} />
      </instancedMesh>
      {ringMaterials.map((material, i) => (
        <mesh
          key={i}
          ref={(mesh) => {
            ringMeshes.current[i] = mesh;
          }}
          rotation={[-Math.PI / 2, 0, 0]}
          material={material}
          visible={false}
        >
          <ringGeometry args={[0.86, 1, 40]} />
        </mesh>
      ))}
    </>
  );
}
