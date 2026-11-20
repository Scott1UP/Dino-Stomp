import type { Collider, KinematicCharacterController, RigidBody } from '@dimforge/rapier3d-compat';
import { useGLTF } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import { useBeforePhysicsStep, useRapier } from '@react-three/rapier';
import { Suspense, useEffect, useMemo, useRef, type RefObject } from 'react';
import * as THREE from 'three';
import { clone as cloneSkinned } from 'three/examples/jsm/utils/SkeletonUtils.js';
import { audio } from '../../audio/engine';
import type { DinoId } from '../../types';
import { actions, getState, useStore } from '../../ui/store';
import { fx } from '../../world/effects/Effects';
import { toonGradient } from '../../world/toon';
import { game, input } from '../state';
import { BODIES, CHARGE_HITS_PER_SECOND, CHARGE_SPEED, STATS, WIND_UP } from './stats';

type Anim = 'idle' | 'walk' | 'run' | 'move' | 'celebrate';

/** A tapped walk or attack gives up being polite after this long against a wall. */
const BLOCKED_SECONDS = 0.2;
const MOVE_SECONDS = 0.6;

const _desired = new THREE.Vector3();
const _point = new THREE.Vector3();
let moveCounter = 0;

interface Sim {
  time: number;
  readyAt: number;
  blocked: number;
  velocity: { x: number; z: number };
  nextStepAt: number;
  move: { id: number; startedAt: number; landed: boolean; x: number; z: number; travelled: number; struck: boolean; power: number; hitClock: number } | null;
  bounce: { until: number; x: number; z: number } | null;
}

/**
 * The dino: a kinematic capsule in the physics world (it pushes everything
 * and nothing pushes it back) wearing an animated model.
 */
export function Dino({ spawn }: { spawn: THREE.Vector3 }) {
  const { world, rapier } = useRapier();
  const id = useStore((s) => s.dino);
  const stats = STATS[id];
  const { radius, height } = BODIES[id];
  const centreY = height / 2 + 0.1;

  const group = useRef<THREE.Group>(null);
  const anim = useRef<Anim>('idle');
  const started = useRef(false);
  const physics = useRef<{ body: RigidBody; collider: Collider; controller: KinematicCharacterController } | null>(
    null,
  );
  const sim = useRef<Sim>({ time: 0, readyAt: 0, blocked: 0, velocity: { x: 0, z: 0 }, nextStepAt: 0, move: null, bounce: null });

  // Swapping dino mid-level keeps him where he is: only the capsule changes size.
  useEffect(() => {
    const at = started.current ? game.dino.position : spawn;
    started.current = true;
    const body = world.createRigidBody(rapier.RigidBodyDesc.kinematicPositionBased().setTranslation(at.x, centreY, at.z));
    const collider = world.createCollider(rapier.ColliderDesc.capsule(Math.max(height / 2 - radius, 0.1), radius), body);
    const controller = world.createCharacterController(0.05);
    controller.setSlideEnabled(true);
    physics.current = { body, collider, controller };
    game.dino.position.set(at.x, 0, at.z);
    game.dino.radius = radius;
    sim.current.move = null;
    return () => {
      world.removeCharacterController(controller);
      world.removeRigidBody(body);
      physics.current = null;
    };
  }, [world, rapier, spawn, radius, height, centreY]);

  useBeforePhysicsStep((stepWorld) => {
    const p = physics.current;
    const town = game.town;
    if (!p) return;
    const dt = stepWorld.timestep;
    const s = sim.current;
    s.time += dt;
    const position = p.body.translation();
    town?.setDino(_point.set(position.x, 0, position.z), radius + 0.8, height);

    const travel = (x: number, z: number) => {
      // Loose and falling pieces are left out, and so are raised pieces of a broken building:
      // only the ground floors of standing buildings stop him.
      p.controller.computeColliderMovement(
        p.collider,
        _desired.set(x, 0, z),
        rapier.QueryFilterFlags.EXCLUDE_DYNAMIC,
        undefined,
        (collider) => !town || town.blocksDino(collider),
      );
      const moved = p.controller.computedMovement();
      const limit = game.bounds;
      p.body.setNextKinematicTranslation({
        x: THREE.MathUtils.clamp(position.x + moved.x, -limit, limit),
        y: centreY,
        z: THREE.MathUtils.clamp(position.z + moved.z, -limit, limit),
      });
      return Math.hypot(moved.x, moved.z);
    };

    const smash = (power = 1) => {
      if (s.time < s.readyAt || s.move) return;
      s.readyAt = s.time + stats.cooldownSeconds;
      s.move = {
        id: ++moveCounter,
        startedAt: s.time,
        landed: false,
        x: Math.sin(game.dino.facing),
        z: Math.cos(game.dino.facing),
        travelled: 0,
        struck: false,
        power,
        hitClock: 1, // so the first step of the dash strikes at once
      };
      audio.dino('whoosh', power > 1.1 ? 1.4 : 1);
    };

    // --- a bounce back off something big ---
    if (s.bounce) {
      if (s.time >= s.bounce.until) s.bounce = null;
      else {
        travel(s.bounce.x * 12 * dt, s.bounce.z * 12 * dt);
        anim.current = 'idle';
        return;
      }
    }

    // --- the signature move in progress ---
    const move = s.move;
    if (move) {
      const since = s.time - move.startedAt;
      anim.current = stats.move === 'charge' ? 'run' : 'move';
      // A charged move reaches a little further, as well as hitting harder.
      const grow = 1 + (move.power - 1) / 2;

      if (stats.move === 'charge') {
        // Charge: dash forwards, ploughing through everything in a line.
        if (since >= WIND_UP.charge) {
          _point.set(position.x + move.x * (radius + 1.5), 2, position.z + move.z * (radius + 1.5));
          move.hitClock += dt;
          let hit = false;
          if (move.hitClock >= 1 / CHARGE_HITS_PER_SECOND - 1e-6) {
            move.hitClock = 0;
            hit = !!town?.hit(_point, stats.moveRadius * grow, { push: stats.pushStrength * move.power, lift: 0.55, move: move.id });
          }
          if (hit && !move.struck) {
            move.struck = true;
            if (move.power > 1.1) actions.award('power');
            audio.dino('crunch');
            fx.shake(0.35);
            game.hitStop(50);
          }
          const wanted = CHARGE_SPEED * dt;
          const moved = travel(move.x * wanted, move.z * wanted);
          move.travelled += moved;
          if (moved < wanted * 0.3 && since > 0.1) {
            // Something big: he bounces back.
            s.move = null;
            s.bounce = { until: s.time + 0.22, x: -move.x, z: -move.z };
            audio.dino('boing');
            fx.shake(0.4);
          } else if (move.travelled >= stats.moveLength! * grow) {
            s.move = null;
          }
        }
        return;
      }

      if (stats.move === 'bite' && !move.landed) {
        // The lunge: he throws himself forwards into the bite.
        travel(move.x * 24 * dt, move.z * 24 * dt);
      }
      if (!move.landed && since >= WIND_UP[stats.move]) {
        move.landed = true;
        let hit = false;
        if (stats.move === 'bite') {
          // Bite: a long path straight ahead, and everything in it is thrown that way.
          const direction = { x: move.x, z: move.z };
          for (const along of [0.25, 0.6, 1]) {
            const reach = radius + stats.moveLength! * grow * along - 2;
            _point.set(position.x + move.x * reach, 3, position.z + move.z * reach);
            const struck = town?.hit(_point, stats.moveRadius * grow * (0.8 + 0.2 * along), {
              push: stats.pushStrength * move.power,
              lift: 0.5,
              move: move.id,
              direction,
            });
            hit = struck || hit;
            fx.dust(_desired.set(_point.x, 1, _point.z), 2.6, true);
          }
          audio.dino('crunch');
          audio.dino('stomp', 0.7);
        } else {
          // Tail swing: a full circle that launches things flat and far.
          _point.set(position.x, 0, position.z);
          hit = !!town?.hit(_point, stats.moveRadius * grow, { push: stats.pushStrength * move.power, lift: 0.4, move: move.id });
          fx.ring(_point, stats.moveRadius * grow);
          if (hit) {
            audio.dino('bonk');
            audio.dino('whistle', 0.5);
          }
        }
        if (move.power > 1.1 && hit) actions.award('power');
        if (move.power > 1.1) {
          // A fully wound-up move: a bigger burst, so he can see it was worth the wait.
          fx.ring(_point.set(position.x, 0, position.z), stats.moveRadius * 1.6);
          fx.confetti(_desired.set(position.x, 4, position.z), 20, undefined, 12);
        }
        fx.shake((hit ? 0.7 : 0.3) * move.power);
        if (hit) game.hitStop(move.power > 1.1 ? 100 : 70);
      }
      if (since >= MOVE_SECONDS) s.move = null;
    }

    // --- where does he want to go? ---
    let x = input.stick.active ? input.stick.x : input.keys.x;
    let z = input.stick.active ? -input.stick.y : -input.keys.y;
    const steering = Math.hypot(x, z) > 0.1;
    let following = false;

    if (steering) {
      input.target = null; // the thumbstick always wins
    } else if (input.target) {
      const target = input.target;
      if (target.kind === 'attack') {
        if (target.building.remaining === 0 || target.building.tipping) {
          input.target = null;
        } else {
          target.building.box.clampPoint(_point.set(position.x, 0, position.z), _point);
          x = _point.x - position.x;
          z = _point.z - position.z;
          const reach = stats.move === 'charge' ? stats.moveLength! * 0.6 : stats.moveRadius * 0.55;
          if (Math.hypot(x, z) <= reach || s.blocked > BLOCKED_SECONDS) {
            game.dino.facing = Math.atan2(x, z);
            smash();
            input.target = null; // tapping again repeats it
          } else {
            following = true;
          }
        }
      } else {
        x = target.x - position.x;
        z = target.z - position.z;
        if (Math.hypot(x, z) < 1) input.target = null;
        else following = true;
      }
    }

    if (input.smash) {
      const power = input.smash;
      input.smash = 0;
      smash(power);
    }

    // --- move ---
    const length = Math.hypot(x, z);
    const going = (steering || following) && length > 1e-3;
    const top = stats.speed * (s.move ? 0.3 : 1) * (steering ? Math.min(length, 1) : 1);
    const targetX = going ? (x / length) * top : 0;
    const targetZ = going ? (z / length) * top : 0;
    // A little weight: he gets up to speed and slows down over a moment, not instantly.
    const ease = 1 - Math.exp(-dt * 9);
    s.velocity.x += (targetX - s.velocity.x) * ease;
    s.velocity.z += (targetZ - s.velocity.z) * ease;
    const speed = Math.hypot(s.velocity.x, s.velocity.z);

    if (going) {
      const want = Math.atan2(x, z);
      const turn = Math.atan2(Math.sin(want - game.dino.facing), Math.cos(want - game.dino.facing));
      game.dino.facing += turn * (1 - Math.exp(-dt * 12));
    }

    if (speed > 0.05) {
      const moved = travel(s.velocity.x * dt, s.velocity.z * dt);
      s.blocked = going && moved < speed * dt * 0.3 ? s.blocked + dt : 0;
      if (s.time >= s.nextStepAt) {
        s.nextStepAt = s.time + (speed > stats.speed * 0.6 ? 0.24 : 0.36);
        audio.dino('step', id === 'trex' ? 0.55 : 0.4);
      }
    } else {
      s.blocked = 0;
    }
    if (!s.move) anim.current = speed > stats.speed * 0.55 ? 'run' : speed > 0.6 ? 'walk' : 'idle';

    // Straight lines, no pathfinding: whatever is in the way of a tapped walk gets smashed.
    if (following && input.target?.kind === 'walk' && s.blocked > BLOCKED_SECONDS) smash();
  });

  useFrame(() => {
    const p = physics.current;
    if (!p || !group.current) return;
    const t = p.body.translation();
    game.dino.position.set(t.x, 0, t.z);
    group.current.position.set(t.x, 0, t.z);
    group.current.rotation.y = game.dino.facing;
    if (getState().screen === 'complete') anim.current = 'celebrate';

    // A quick squash as the move lands.
    const move = sim.current.move;
    const since = move?.landed ? sim.current.time - move.startedAt - WIND_UP[stats.move] : 1;
    const squash = since < 0.22 ? Math.sin((since / 0.22) * Math.PI) * 0.16 : 0;
    group.current.scale.set(1 + squash * 0.6, 1 - squash, 1 + squash * 0.6);
  });

  return (
    <group ref={group}>
      <Suspense fallback={null}>
        <DinoModel key={id} id={id} anim={anim} />
      </Suspense>
    </group>
  );
}

function DinoModel({ id, anim }: { id: DinoId; anim: RefObject<Anim> }) {
  const gltf = useGLTF(`/models/dinos/${id}.glb`);

  const { scene, mixer, actions } = useMemo(() => {
    const scene = cloneSkinned(gltf.scene);
    scene.traverse((object) => {
      const mesh = object as THREE.Mesh;
      if (!mesh.isMesh) return;
      const source = mesh.material as THREE.MeshStandardMaterial;
      mesh.material = new THREE.MeshToonMaterial({ color: source.color, gradientMap: toonGradient });
      mesh.castShadow = true;
      mesh.frustumCulled = false; // a skinned mesh's bounds don't follow its animation
    });
    const mixer = new THREE.AnimationMixer(scene);
    const actions = Object.fromEntries(gltf.animations.map((clip) => [clip.name, mixer.clipAction(clip)]));
    return { scene, mixer, actions };
  }, [gltf]);

  const playing = useRef<Anim | null>(null);

  useFrame((_, delta) => {
    const wanted = anim.current;
    if (wanted !== playing.current && actions[wanted]) {
      const next = actions[wanted];
      next.reset();
      // The signature move's animation is squeezed to fit the move.
      next.setEffectiveTimeScale(wanted === 'move' ? next.getClip().duration / MOVE_SECONDS : 1);
      next.fadeIn(0.14).play();
      if (playing.current) actions[playing.current]?.fadeOut(0.14);
      playing.current = wanted;
    }
    mixer.update(delta);
  });

  return <primitive object={scene} />;
}

for (const id of ['trex', 'triceratops', 'stegosaurus']) useGLTF.preload(`/models/dinos/${id}.glb`);
