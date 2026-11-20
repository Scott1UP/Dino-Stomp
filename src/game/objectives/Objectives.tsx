import { useFrame } from '@react-three/fiber';
import { useBeforePhysicsStep } from '@react-three/rapier';
import { useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';
import { audio } from '../../audio/engine';
import { speak, type Line } from '../../audio/ui';
import { actions, getState, useStore } from '../../ui/store';
import type { BuildingState, ModuleState, TownSystem } from '../../world/breaking/TownSystem';
import { fx } from '../../world/effects/Effects';
import { levelDef } from '../levels';
import { events, game } from '../state';

const AUTO_REBUILD_SHARE = 0.8;
const MAX_ARROWS = 3;
/** How far in from the edge of the screen the arrows sit, clear of the buttons. */
const ARROW_MARGIN = 96;

const _up = new THREE.Vector3();
const _q = new THREE.Quaternion();
const _v = new THREE.Vector3();

/** How upright a loose body is: 1 standing, 0 lying flat. */
function upright(module: ModuleState) {
  const r = module.body!.rotation();
  return _up.set(0, 1, 0).applyQuaternion(_q.set(r.x, r.y, r.z, r.w)).y;
}

interface Run {
  dominoes: ModuleState[];
  started: boolean;
  finished: boolean;
  stalled: number;
}

/**
 * The rules of each level: what counts towards its two objectives, the domino
 * runs' help pushes, the paddling pool, and sandbox rebuilds. It also draws the
 * bouncing stars that mark what to smash, so he never has to read anything.
 */
export function Objectives({ town, pool }: { town: TownSystem; pool: [number, number, number] | null }) {
  const story = useStore((s) => s.mode === 'story');
  const level = useStore((s) => s.level);
  const progress = useStore((s) => s.progress[s.level]);
  const [, refresh] = useState(0);
  const stars = useRef<THREE.Group>(null);
  const floated = useRef(0);
  const marks = useRef<{ key: string; x: number; y: number; z: number }[]>([]);
  const arrows = useRef<HTMLDivElement[]>([]);

  // Arrows at the edge of the screen point at the nearest things still to smash.
  useEffect(() => {
    const layer = document.createElement('div');
    layer.className = 'objective-arrows';
    for (let i = 0; i < MAX_ARROWS; i++) {
      const arrow = document.createElement('div');
      arrow.className = 'objective-arrow';
      arrow.style.display = 'none';
      arrow.innerHTML =
        '<svg viewBox="0 0 64 64"><path d="M10 14 L56 32 L10 50 L20 32 Z" fill="#ffc21f" stroke="#3b2414" stroke-width="5" stroke-linejoin="round"/></svg>';
      layer.appendChild(arrow);
      arrows.current.push(arrow);
    }
    document.body.appendChild(layer);
    return () => {
      layer.remove();
      arrows.current = [];
    };
  }, []);

  /** The domino runs: each is a chain that, once started, always reaches its end. */
  const runs = useMemo(() => {
    const byRun = new Map<number, Run>();
    for (const domino of town.dominoes) {
      const id = domino.building.meta.run ?? 0;
      if (!byRun.has(id)) byRun.set(id, { dominoes: [], started: false, finished: false, stalled: 0 });
      byRun.get(id)!.dominoes.push(domino);
    }
    return [...byRun.values()];
  }, [town]);

  useEffect(() => {
    const count = (tag: string) => {
      const index = levelDef(getState().level).objectives.findIndex((objective) => objective.tag === tag);
      if (index >= 0) actions.addProgress(index as 0 | 1);
    };
    town.events.onDown = (building: BuildingState) => {
      const top = _v.set(building.centre.x, building.box.max.y + 2, building.centre.z);
      if (building.kind === 'building' || building.kind === 'giantTower') {
        fx.confetti(top, 26, building.colour, 12);
        count('smash');
        actions.award('first-smash');
      }
      events.down.forEach((listener) => listener(building));
      // Stickers for the big moments.
      const type = building.meta.type;
      if (building.meta.objective === 'tower') actions.award('tower');
      if (building.kind === 'giantTower') actions.award('giant-tower');
      if (type === 'ferris_wheel') actions.award('big-wheel');
      if (type === 'giant_sunflower') actions.award('sunflower');
      if (type === 'treehouse') actions.award('treehouse');
      if (building.kind === 'mover') actions.award('catch');
      if (building.meta.objective) {
        count(building.meta.objective);
        // A landmark down gets a cheer.
        if (building.kind !== 'prop') speak(`cheer-${1 + Math.floor(Math.random() * 5)}` as Line);
      }
      refresh((n) => n + 1);
    };
    town.events.onTowerCrash = (building) => {
      fx.shake(1);
      game.hitStop(110);
      fx.fireworks(building.centre);
      for (let i = 0; i < 5; i++) audio.ui('firework', { delay: i * 0.32 });
    };
    town.events.onRebuilt = (building) => {
      if (building.kind === 'building') audio.ui('rebuild', { gain: 0.5 });
      refresh((n) => n + 1);
    };
    return () => {
      town.events.onDown = town.events.onTowerCrash = town.events.onRebuilt = undefined;
    };
  }, [town]);

  useBeforePhysicsStep((world) => {
    const dt = world.timestep;

    for (const run of runs) {
      if (run.finished) continue;
      const { dominoes } = run;
      let firstStanding = -1;
      let moving = false;
      for (let i = 0; i < dominoes.length; i++) {
        const domino = dominoes[i];
        if (!domino.body) continue;
        const tilt = upright(domino);
        const spin = domino.body.angvel();
        if (Math.hypot(spin.x, spin.y, spin.z) > 0.25) moving = true;
        if (tilt < 0.93 && !run.started) {
          run.started = true;
          refresh((n) => n + 1);
        }
        // The next one to push is the first still properly upright: a domino leaning on its
        // neighbour is not going anywhere, and pushing it again would not help.
        if (tilt > 0.85 && firstStanding < 0) firstStanding = i;
      }
      const last = dominoes[dominoes.length - 1];
      if (!last.body) continue;
      if (firstStanding < 0 || upright(last) < 0.5) {
        run.finished = true;
        // The last domino rings a big bell and fires confetti.
        const t = last.body.translation();
        audio.ui('bell');
        fx.confetti(_v.set(t.x, 8, t.z), 60, undefined, 16);
        actions.award('dominoes');
        const index = levelDef(getState().level).objectives.findIndex((objective) => objective.tag === 'domino');
        if (index >= 0) actions.addProgress(index as 0 | 1);
      } else if (run.started && !moving) {
        // Stalled: spacing and physics can stop a run, and the payoff must always happen.
        run.stalled += dt;
        if (run.stalled > 0.5) {
          run.stalled = 0;
          // Tip over the next upright domino, and any before it that are stuck leaning on a neighbour.
          for (let i = 0; i <= firstStanding; i++) {
            const domino = dominoes[i];
            if (!domino.body || upright(domino) < 0.35) continue;
            const ahead = dominoes[i + 1]?.rest.position ?? domino.rest.position;
            const behind = dominoes[i + 1] ? domino.rest.position : (dominoes[i - 1]?.rest.position ?? domino.rest.position);
            _v.set(ahead.x - behind.x, 0, ahead.z - behind.z);
            if (_v.lengthSq() < 1e-4) continue;
            _v.normalize();
            // Spin about the level axis across the run, so its top goes forwards.
            // (with its middle moving forwards to match, so it pivots on its base instead of spinning on the spot).
            const reach = domino.half.y * 2.6;
            domino.body.setLinvel({ x: _v.x * reach, y: 0, z: _v.z * reach }, true);
            domino.body.setAngvel({ x: _v.z * 2.6, y: 0, z: -_v.x * 2.6 }, true);
          }
        }
      } else {
        run.stalled = 0;
      }
    }

    // --- beach balls: they splash and float in the paddling pool, just for fun ---
    for (let i = town.balls.length - 1; i >= 0; i--) {
      const ball = town.balls[i];
      if (ball.state !== 'loose') continue;
      const t = ball.body!.translation();
      if (pool && Math.hypot(t.x - pool[0], t.z - pool[1]) < pool[2] - 0.5 && t.y < 3) {
        const angle = floated.current * 2.2;
        const spread = pool[2] * 0.45;
        town.float(ball, pool[0] + Math.cos(angle) * spread, pool[1] + Math.sin(angle) * spread);
        floated.current++;
        audio.ui('splash');
        fx.confetti(_v.set(t.x, 1.5, t.z), 18, '#8FD3E8', 8);
      } else if (Math.abs(t.x) > game.bounds + 6 || Math.abs(t.z) > game.bounds + 6 || t.y < -4) {
        town.reset(ball); // a ball that leaves the map reappears where it started
      }
    }

    // --- sandbox: once most of the town is down, it rebuilds itself ---
    if (getState().mode === 'sandbox' && !town.rebuilding && town.destroyedShare() >= AUTO_REBUILD_SHARE) {
      town.rebuild(game.dino.position);
      for (const run of runs) run.started = run.finished = false;
    }
  });

  useFrame(({ clock, camera, size }) => {
    // --- the arrows ---
    const playing = getState().screen === 'playing';
    const off: { distance: number; x: number; y: number }[] = [];
    if (playing) {
      for (const mark of marks.current) {
        // The robot walks about, so his arrow follows him live.
        const live = mark.key === 'robot' && game.robot ? game.robot : mark;
        _v.set(live.x, 4, live.z).project(camera);
        if (_v.z > 1) _v.multiplyScalar(-1); // behind the camera: point the other way
        if (Math.abs(_v.x) < 0.9 && Math.abs(_v.y) < 0.86) continue; // on screen already
        off.push({ distance: Math.hypot(live.x - game.dino.position.x, live.z - game.dino.position.z), x: _v.x, y: _v.y });
      }
      off.sort((a, b) => a.distance - b.distance);
    }
    arrows.current.forEach((arrow, i) => {
      const target = off[i];
      if (!target) {
        arrow.style.display = 'none';
        return;
      }
      // Slide the arrow out from the middle of the screen towards the target until it meets the edge.
      const px = (target.x * size.width) / 2;
      const py = (-target.y * size.height) / 2;
      const reach = Math.min((size.width / 2 - ARROW_MARGIN) / Math.abs(px || 1), (size.height / 2 - ARROW_MARGIN) / Math.abs(py || 1));
      const x = size.width / 2 + px * reach;
      const y = size.height / 2 + py * reach;
      arrow.style.display = 'block';
      arrow.style.transform = `translate(${x}px, ${y}px) rotate(${Math.atan2(py, px)}rad)`;
    });

    if (!stars.current) return;
    const time = clock.elapsedTime;
    for (const star of stars.current.children) {
      if (star.userData.robot && game.robot) star.position.set(game.robot.x, star.position.y, game.robot.z);
      star.position.y = (star.userData.height as number) + Math.abs(Math.sin(time * 2.6 + star.position.x)) * 1.8;
      star.rotation.y = time * 2;
    }
  });

  // The landmarks still standing get a bouncing star above them.
  const targets: { key: string; x: number; y: number; z: number }[] = [];
  if (story) {
    // Only what still counts: once an objective is complete, its targets drop out and the arrows
    // and stars point at the other one.
    const tags = new Set(
      levelDef(level)
        .objectives.filter((objective, index) => progress[index] < objective.required)
        .map((objective) => objective.tag),
    );
    for (const building of town.buildings) {
      const tag = building.meta.objective;
      if (building.down || !tag || !tags.has(tag) || building.kind === 'domino') continue;
      targets.push({ key: building.meta.id, x: building.centre.x, y: building.box.max.y + 3, z: building.centre.z });
    }
    if (tags.has('robot') && game.robot) targets.push({ key: 'robot', x: game.robot.x, y: 17, z: game.robot.z });
    runs.forEach((run, index) => {
      if (run.started || !tags.has('domino')) return;
      const first = run.dominoes[0].rest.position;
      targets.push({ key: `run${index}`, x: first.x, y: 11.5, z: first.z });
    });
  }

  // "Smash lots" has no particular target, so the arrows point at whatever buildings are still standing.
  const extra: typeof targets = [];
  if (story && targets.length === 0 && levelDef(level).objectives.some((o, i) => o.tag === 'smash' && progress[i] < o.required)) {
    for (const building of town.buildings) {
      if (building.kind !== 'building' || building.down) continue;
      extra.push({ key: building.meta.id, x: building.centre.x, y: 0, z: building.centre.z });
    }
  }
  marks.current = targets.length ? targets : extra;

  return (
    <group ref={stars}>
      {targets.map((target) => (
        <mesh key={target.key} position={[target.x, target.y, target.z]} userData={{ height: target.y, robot: target.key === 'robot' }} scale={[1.8, 2.4, 0.8]}>
          <octahedronGeometry args={[1, 0]} />
          <meshBasicMaterial color="#FFD84D" />
        </mesh>
      ))}
    </group>
  );
}
