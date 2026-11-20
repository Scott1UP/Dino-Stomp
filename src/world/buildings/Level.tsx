import { useGLTF, useTexture } from '@react-three/drei';
import { useFrame, useThree } from '@react-three/fiber';
import { CuboidCollider, useBeforePhysicsStep, useRapier } from '@react-three/rapier';
import { useEffect, useMemo, useRef, useState } from 'react';
import * as THREE from 'three';
import palette from '../../../assets-src/palette.json';
import { audio } from '../../audio/engine';
import { Dino } from '../../game/dinos/Dino';
import { levelDef } from '../../game/levels';
import { Objectives } from '../../game/objectives/Objectives';
import { game } from '../../game/state';
import { getState, useStore } from '../../ui/store';
import { GRAPHICS } from '../../game/graphics';
import { TownSystem } from '../breaking/TownSystem';
import { Effects, fx } from '../effects/Effects';
import { addDetail, groundWeave, toonGradient } from '../toon';

const ATLAS = '/textures/atlas.png';
const DETAIL = '/textures/detail.png';

/** Each colour scheme's wall colour, for confetti in the building's own colours. */
const SCHEME_COLOURS = Object.fromEntries(
  Object.entries(palette.schemes).map(([name, scheme]) => [name, (palette.colours as Record<string, string>)[scheme.wall]]),
);

const _v = new THREE.Vector3();

/** One level: its town, its ground, the dino, and the rules. */
export function Level() {
  const level = levelDef(useStore((s) => s.level));
  const gltf = useGLTF(level.model);
  const atlas = useTexture(ATLAS);
  const groundMap = useTexture(level.ground);
  const detail = useTexture(DETAIL);
  const showDetail = GRAPHICS[useStore((s) => s.settings.graphics)].detail;
  const { world, rapier } = useRapier();
  const maxAnisotropy = useThree((state) => state.gl.capabilities.getMaxAnisotropy());
  const [town, setTown] = useState<TownSystem | null>(null);

  /** The one material every building module and prop shares, so the town stays one draw call. */
  const material = useMemo(() => {
    atlas.flipY = false; // glTF UV convention
    atlas.colorSpace = THREE.SRGBColorSpace;
    atlas.needsUpdate = true;
    // Roof tiles, brick courses and planks are multiplied over the flat colours.
    const plain = new THREE.MeshToonMaterial({ map: atlas, gradientMap: toonGradient });
    return showDetail ? addDetail(plain, detail, true) : plain;
  }, [atlas, detail, showDetail]);

  useMemo(() => {
    groundMap.colorSpace = THREE.SRGBColorSpace;
    // The ground is always seen at a steep angle; without this it blurs a short way from the dino.
    groundMap.anisotropy = maxAnisotropy;
    groundMap.needsUpdate = true;
  }, [groundMap, maxAnisotropy]);

  const info = useMemo(() => {
    gltf.scene.updateMatrixWorld(true);
    const marker = gltf.scene.getObjectByName('SPAWN_dino');
    const data = (gltf.scene.getObjectByName('LEVEL')?.userData ?? {}) as { size?: number; pool?: number[] };
    const size = data.size ?? 200;
    return {
      spawn: marker ? marker.getWorldPosition(new THREE.Vector3()) : new THREE.Vector3(),
      size,
      // The layout's (x, y) is the game's (x, -z).
      pool: data.pool ? ([data.pool[0], -data.pool[1], data.pool[2]] as [number, number, number]) : null,
    };
  }, [gltf]);

  const materialRef = useRef(material);

  const groundMaterial = useMemo(() => {
    const weave = groundWeave();
    weave.repeat.set(info.size / 5, info.size / 5);
    const plain = new THREE.MeshToonMaterial({ map: groundMap, gradientMap: toonGradient });
    return showDetail ? addDetail(plain, weave, false) : plain;
  }, [groundMap, info.size, showDetail]);

  useEffect(() => {
    const system = new TownSystem(gltf.scene, world, rapier, materialRef.current, SCHEME_COLOURS);
    system.events.onBreak = (module, struck) => {
      const dx = module.rest.position.x - game.dino.position.x;
      const distance = module.rest.position.distanceTo(game.dino.position);
      audio.breakSound(module.meta.material, dx, distance, struck);
      fx.dust(module.rest.position, struck ? 2 : 1.3);
      if (struck) fx.confetti(_v.copy(module.rest.position), 2, module.building.colour);
    };
    system.events.onImpact = (module, speed) => {
      const t = module.body?.translation();
      if (!t) return;
      audio.impact(module.meta.material, speed, t.x - game.dino.position.x, Math.hypot(t.x - game.dino.position.x, t.z - game.dino.position.z));
      if (speed > 9) fx.dust(_v.set(t.x, 0.5, t.z), 1.4);
    };
    system.maxMoving = GRAPHICS[getState().settings.graphics].maxMoving;
    game.town = system;
    game.bounds = info.size / 2 - 5;
    setTown(system);
    return () => {
      game.town = null;
      system.dispose();
    };
  }, [gltf, world, rapier, info]);

  // A change of graphics setting swaps the material without rebuilding the town.
  useEffect(() => {
    materialRef.current = material;
    if (town) town.mesh.material = material;
  }, [material, town]);

  const half = info.size / 2;

  useBeforePhysicsStep((stepWorld) => game.town?.step(stepWorld.timestep));
  useFrame((_, delta) => game.town?.sync(delta));

  // Soft green hills ring the playmat: they mark the edge of the world and can't be broken.
  // One instanced mesh, so the whole ring is a single draw call.
  const hills = useMemo(() => {
    const count = 28;
    const mesh = new THREE.InstancedMesh(
      new THREE.IcosahedronGeometry(1, 1),
      new THREE.MeshToonMaterial({ color: '#A9C48E', gradientMap: toonGradient }),
      count,
    );
    const matrix = new THREE.Matrix4();
    const position = new THREE.Vector3();
    const scale = new THREE.Vector3();
    const upright = new THREE.Quaternion();
    for (let i = 0; i < count; i++) {
      const angle = (i / count) * Math.PI * 2;
      const reach = (half + 26 + ((i * 37) % 17)) * 1.25;
      const width = 26 + ((i * 53) % 22);
      position.set(Math.cos(angle) * reach, -4, Math.sin(angle) * reach);
      scale.set(width, 12 + ((i * 29) % 16), width);
      mesh.setMatrixAt(i, matrix.compose(position, upright, scale));
    }
    mesh.frustumCulled = false;
    return mesh;
  }, [half]);

  return (
    <>
      {town && <primitive object={town.mesh} />}
      {town && <Objectives town={town} pool={info.pool} />}
      <Dino spawn={info.spawn} />
      <Effects />

      {/* The world around the town is soft-coloured and can't be broken. */}
      <CuboidCollider args={[half + 60, 0.5, half + 60]} position={[0, -0.5, 0]} />
      <mesh rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
        <planeGeometry args={[info.size, info.size]} />
        <primitive object={groundMaterial} attach="material" />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.06, 0]}>
        <planeGeometry args={[900, 900]} />
        <meshToonMaterial color="#A9C48E" gradientMap={toonGradient} />
      </mesh>
      <primitive object={hills} />
    </>
  );
}

// Only the level being played is loaded: each model is several megabytes.
