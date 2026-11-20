import type { Collider, RigidBody, World } from '@dimforge/rapier3d-compat';
import * as THREE from 'three';
import type { BuildingMeta, ModuleMeta } from '../../types';

type Rapier = typeof import('@dimforge/rapier3d-compat').default;

/** At most this many moving bodies at once. The oldest debris sinks early. */
const MAX_MOVING = 150;
/** Settled debris sinks into the ground after this long. */
const SETTLE_SECONDS = 4;
const SINK_SPEED = 0.5;
const SINK_SECONDS = 1.2;
/** Collapse spreads upwards one storey at a time. */
const STOREY_DELAY = 0.06;
/** Below this share of ground-floor walls, everything left comes down. */
const FULL_COLLAPSE_SHARE = 0.4;
/** A building counts as knocked over once less than this share of it is standing. */
const DOWN_SHARE = 0.3;
const POP_SECONDS = 0.4;
/** A building this far inside a move's reach (as a share of its radius) takes the full hit. */
const NEAR_HIT = 0.45;
/** Pieces at the very edge of a move are pushed this much less hard than those at its centre. */
const FAR_PUSH_LOSS = 0.55;
/**
 * Only the parts of a building that start this close to the ground stop the dino. Anything
 * higher (upper walls, floors, roofs left hanging when the walls under them go) is knocked loose
 * when he walks into it, and tumbles off him instead.
 */
const BLOCKS_BELOW = 2.5;
/** Buildings the dino can walk through or under while they are still standing. */
const OPEN_UNDERNEATH = new Set(['castle_gatehouse', 'gate_towers', 'viaduct']);
/** A sudden loss of speed this big (m/s in one step) is a piece landing. */
const IMPACT_DROP = 3;

export interface ModuleState {
  meta: ModuleMeta;
  building: BuildingState;
  instanceId: number;
  half: THREE.Vector3;
  hull: Float32Array | null;
  /** Where it stands when the building is whole. */
  rest: { position: THREE.Vector3; quaternion: THREE.Quaternion };
  position: THREE.Vector3;
  quaternion: THREE.Quaternion;
  box: THREE.Box3; // world bounds while standing
  /**
   * intact: standing as part of its building.  falling: a tumbling piece.
   * sinking / gone: settled debris on its way out.  loose: a domino or ball, always a physics body.
   * tipping: part of the giant tower as it falls in one piece.  floating: a ball in the pool.
   */
  state: 'intact' | 'falling' | 'sinking' | 'gone' | 'loose' | 'tipping' | 'floating';
  supportedBy: ModuleState[];
  holdsUp: ModuleState[];
  scheduled: boolean;
  collider: Collider | null;
  body: RigidBody | null;
  settled: number;
  sunk: number;
  speed: number;
  quietUntil: number;
  pop: number;
  hp: number;
  tipLocal: THREE.Matrix4 | null;
  floatAt: THREE.Vector3 | null;
  /** The module's own bounding box, before it is placed in the world. */
  shape: THREE.Box3;
  /** For a vehicle: where the module sits relative to the vehicle. */
  carried: THREE.Matrix4 | null;
}

export type BuildingKind = 'building' | 'prop' | 'crate' | 'domino' | 'ball' | 'block' | 'giantTower' | 'mover';

export interface BuildingState {
  meta: BuildingMeta & { kind: BuildingKind; order?: number; run?: number; secret?: number; route?: number[]; speed?: number; yaw?: number };
  kind: BuildingKind;
  modules: ModuleState[];
  box: THREE.Box3; // world bounds
  centre: THREE.Vector3;
  /** A palette colour for its confetti. */
  colour: string;
  remaining: number;
  hits: number;
  lastMove: number;
  down: boolean;
  rough: RigidBody | null; // a single box until the first hit
  fine: RigidBody | null; // one box per module after it
  roughShape: { position: THREE.Vector3; quaternion: THREE.Quaternion; centre: THREE.Vector3; half: THREE.Vector3 };
  tipping: { body: RigidBody; time: number } | null;
  /** For a vehicle that drives along a route: where it is on it. */
  drive: { route: THREE.Vector3[]; length: number; at: number; speed: number; yaw: number } | null;
}

export interface HitOptions {
  push: number;
  /** How much of the push goes upwards. A stomp tosses things up; a tail swing launches them flat. */
  lift?: number;
  /** One number per signature move, so a move that sweeps for several steps counts as one hit. */
  move?: number;
  /** Throw things this way (x, z) instead of straight out from the centre: a bite or a charge has a direction. */
  direction?: { x: number; z: number };
}

export interface TownEvents {
  /** A module came off. `struck` is true when a move knocked it off, false when it lost its support. */
  onBreak?(module: ModuleState, struck: boolean): void;
  /** A tumbling piece landed or hit something. */
  onImpact?(module: ModuleState, speed: number): void;
  /** A building, prop or crate has been knocked over. */
  onDown?(building: BuildingState): void;
  onTowerTip?(building: BuildingState): void;
  onTowerCrash?(building: BuildingState): void;
  onRebuilt?(building: BuildingState): void;
  /** A move struck here (whether or not it hit anything). */
  onHit?(centre: THREE.Vector3, radius: number, push: number): void;
  /** A settled piece starts to sink away. */
  onSink?(module: ModuleState): void;
}

const _matrix = new THREE.Matrix4();
const _body = new THREE.Matrix4();
const _one = new THREE.Vector3(1, 1, 1);
const _scale = new THREE.Vector3();
const _v = new THREE.Vector3();
const _w = new THREE.Vector3();
const _q = new THREE.Quaternion();

const isStreetProp = (kind: BuildingKind) => kind === 'prop' || kind === 'crate' || kind === 'mover';
const isLoose = (kind: BuildingKind) => kind === 'domino' || kind === 'ball' || kind === 'block';

/**
 * Owns every building module and prop: the one batched mesh that draws them,
 * their physics bodies, and the rules for how things come apart.
 */
export class TownSystem {
  readonly mesh: THREE.BatchedMesh;
  readonly buildings: BuildingState[] = [];
  readonly dominoes: ModuleState[] = [];
  readonly balls: ModuleState[] = [];
  events: TownEvents = {};
  /** At most this many tumbling pieces at once; the graphics setting lowers it. */
  maxMoving = MAX_MOVING;

  private readonly byInstance: ModuleState[] = [];
  private readonly falling: ModuleState[] = []; // oldest first
  private readonly sinking: ModuleState[] = [];
  private readonly loose: ModuleState[] = [];
  private readonly popping: ModuleState[] = [];
  private readonly floating: ModuleState[] = [];
  private queue: { module: ModuleState; at: number }[] = [];
  private rebuilds: { building: BuildingState; at: number }[] = [];
  private time = 0;
  private aim: { x: number; z: number } | null = null;
  private readonly dino = { position: new THREE.Vector3(), radius: 2, height: 8 };
  /** Which module each standing collider belongs to, so the dino's movement can tell them apart. */
  private readonly byCollider = new Map<number, ModuleState>();

  constructor(
    scene: THREE.Object3D,
    private readonly world: World,
    private readonly rapier: Rapier,
    material: THREE.Material,
    colours: Record<string, string>,
  ) {
    scene.updateMatrixWorld(true);

    const meshes: THREE.Mesh[] = [];
    scene.traverse((object) => {
      if ((object as THREE.Mesh).isMesh && object.name.startsWith('MOD_')) meshes.push(object as THREE.Mesh);
    });

    // Identical geometries are stored once in the batch.
    const geometries = [...new Set(meshes.map((m) => m.geometry))];
    const vertexCount = geometries.reduce((sum, g) => sum + g.attributes.position.count, 0);
    const indexCount = geometries.reduce((sum, g) => sum + (g.index?.count ?? 0), 0);

    this.mesh = new THREE.BatchedMesh(meshes.length, vertexCount, indexCount, material);
    this.mesh.castShadow = true;
    this.mesh.receiveShadow = true;
    this.mesh.sortObjects = false;
    this.mesh.frustumCulled = false;

    const geometryIds = new Map<THREE.BufferGeometry, number>();
    for (const geometry of geometries) geometryIds.set(geometry, this.mesh.addGeometry(geometry));

    const buildings = new Map<THREE.Object3D, BuildingState>();
    const byId = new Map<string, ModuleState>();

    for (const mesh of meshes) {
      const parent = mesh.parent!;
      let building = buildings.get(parent);
      if (!building) {
        const meta = parent.userData as BuildingState['meta'];
        const position = new THREE.Vector3();
        const quaternion = new THREE.Quaternion();
        parent.matrixWorld.decompose(position, quaternion, _scale);
        building = {
          meta,
          kind: meta.kind ?? 'building',
          modules: [],
          box: new THREE.Box3(),
          centre: new THREE.Vector3(),
          colour: colours[meta.scheme] ?? '',
          remaining: 0,
          hits: 0,
          lastMove: -1,
          down: false,
          rough: null,
          fine: null,
          roughShape: { position, quaternion, centre: new THREE.Vector3(), half: new THREE.Vector3() },
          tipping: null,
          drive: null,
        };
        buildings.set(parent, building);
        this.buildings.push(building);
      }

      const geometry = mesh.geometry;
      geometry.computeBoundingBox();
      const half = geometry.boundingBox!.getSize(new THREE.Vector3()).multiplyScalar(0.5);
      const position = new THREE.Vector3();
      const quaternion = new THREE.Quaternion();
      mesh.matrixWorld.decompose(position, quaternion, _scale);

      const extras = mesh.userData as Omit<ModuleMeta, 'supports'> & { supports: string };
      const meta: ModuleMeta = { ...extras, supports: extras.supports ? extras.supports.split(',') : [] };

      const instanceId = this.mesh.addInstance(geometryIds.get(geometry)!);
      this.mesh.setMatrixAt(instanceId, mesh.matrixWorld);

      const module: ModuleState = {
        meta,
        building,
        instanceId,
        half,
        hull: meta.collider === 'hull' ? new Float32Array(geometry.attributes.position.array) : null,
        rest: { position: position.clone(), quaternion: quaternion.clone() },
        position,
        quaternion,
        box: geometry.boundingBox!.clone().applyMatrix4(mesh.matrixWorld),
        state: 'intact',
        supportedBy: [],
        holdsUp: [],
        scheduled: false,
        collider: null,
        body: null,
        settled: 0,
        sunk: 0,
        speed: 0,
        quietUntil: 0,
        pop: POP_SECONDS,
        hp: 1,
        tipLocal: null,
        floatAt: null,
        shape: geometry.boundingBox!.clone(),
        carried: null,
      };
      building.modules.push(module);
      building.remaining++;
      building.box.union(module.box);
      byId.set(meta.id, module);
      this.byInstance[instanceId] = module;
    }

    // Structure links: which module holds up which.
    for (const module of byId.values()) {
      for (const id of module.meta.supports) {
        const support = byId.get(id);
        if (!support) continue;
        module.supportedBy.push(support);
        support.holdsUp.push(module);
      }
    }

    for (const [parent, building] of buildings) {
      building.box.getCenter(building.centre);
      const local = new THREE.Box3();
      for (const child of parent.children) {
        const geometry = (child as THREE.Mesh).geometry;
        if (!geometry?.boundingBox) continue;
        local.union(geometry.boundingBox.clone().applyMatrix4(child.matrix));
      }
      local.getCenter(building.roughShape.centre);
      local.getSize(building.roughShape.half).multiplyScalar(0.5);
      this.stand(building);
      if (building.kind === 'mover') this.startDriving(building);
    }

    this.dominoes.sort((a, b) => (a.building.meta.order ?? 0) - (b.building.meta.order ?? 0));
  }

  get movingBodies() {
    return this.falling.length;
  }

  /** Share of the town (not counting dominoes and balls) that has been knocked down. */
  destroyedShare() {
    let total = 0;
    let standing = 0;
    for (const building of this.buildings) {
      if (isLoose(building.kind)) continue;
      total += building.modules.length;
      standing += building.remaining;
    }
    return total ? 1 - standing / total : 0;
  }

  /** Where the dino is, so props can be knocked over by walking into them. */
  setDino(position: THREE.Vector3, radius: number, height: number) {
    this.dino.position.copy(position);
    this.dino.radius = radius;
    this.dino.height = height;
  }

  /**
   * Whether a collider should stop the dino. Only standing pieces at ground level do; the
   * giant tower is solid all the way up (it must be brought down by its base).
   */
  blocksDino(collider: Collider) {
    const module = this.byCollider.get(collider.handle);
    if (!module) return true; // the ground, or a building's single box before its first hit
    if (module.building.kind === 'giantTower') return true;
    return module.state === 'intact' && !module.scheduled && module.box.min.y < BLOCKS_BELOW;
  }

  /**
   * A signature move landed: everything within `radius` of `centre` is knocked
   * away. Returns true if it hit a building.
   */
  hit(centre: THREE.Vector3, radius: number, options: HitOptions): boolean {
    const { push, lift = 0.8, move = -1, direction } = options;
    this.aim = direction ?? null;
    this.events.onHit?.(centre, radius, push);
    let any = false;

    // Things that are already loose get knocked about too (before this hit adds more).
    for (const list of [this.falling, this.loose]) {
      for (const module of list) {
        const t = module.body!.translation();
        if (_v.set(t.x, t.y, t.z).distanceTo(centre) <= radius + module.half.y) {
          this.push(module.body!, centre, push * (module.state === 'loose' ? 0.45 : 0.7), lift);
        }
      }
    }

    for (const building of this.buildings) {
      if (building.remaining === 0 || isLoose(building.kind) || building.tipping) continue;
      if (building.box.distanceToPoint(centre) > radius) continue;
      any = true;
      const counted = move < 0 || building.lastMove !== move;
      building.lastMove = move;
      // Closer is stronger: a hit that only catches the edge of a building counts as half a hit towards
      // bringing it down, and (below) knocks its pieces away less hard.
      const nearness = 1 - building.box.distanceToPoint(centre) / radius;
      if (counted) building.hits += nearness > NEAR_HIT ? 1 : 0.5;

      if (building.kind === 'giantTower') {
        this.hitTower(building, centre, radius, push, lift, counted);
        continue;
      }

      this.refine(building);
      const bringDown = building.hits >= building.meta.hitsToCollapse;
      for (const module of building.modules) {
        if (module.state !== 'intact') continue;
        const distance = module.box.distanceToPoint(centre);
        // Chimneys, signs and the like come off on any nearby hit.
        const reach = module.meta.role === 'detail' ? radius * 2 : radius;
        if (distance <= reach) this.detach(module, centre, push * (1 - FAR_PUSH_LOSS * Math.min(distance / reach, 1)), lift);
        else if (bringDown) this.schedule(module, STOREY_DELAY * (module.meta.storey + 1));
      }
      this.checkFullCollapse(building);
    }

    this.aim = null;
    return any;
  }

  /** The standing building under a ray, if any. Street furniture is not a target. */
  pick(raycaster: THREE.Raycaster): BuildingState | null {
    for (const hit of raycaster.intersectObject(this.mesh, false)) {
      if (hit.batchId === undefined) continue;
      const module = this.byInstance[hit.batchId];
      if (module?.state === 'intact' && !isLoose(module.building.kind)) return module.building;
    }
    return null;
  }

  /** The standing building whose footprint, enlarged by `grow`, contains a ground point. */
  buildingAt(x: number, z: number, grow: number): BuildingState | null {
    for (const building of this.buildings) {
      if (building.remaining === 0 || isLoose(building.kind) || isStreetProp(building.kind)) continue;
      const { min, max } = building.box;
      const padX = ((max.x - min.x) * grow) / 2;
      const padZ = ((max.z - min.z) * grow) / 2;
      if (x >= min.x - padX && x <= max.x + padX && z >= min.z - padZ && z <= max.z + padZ) return building;
    }
    return null;
  }

  /** Put a beach ball afloat at a spot in the pool. */
  float(ball: ModuleState, x: number, z: number) {
    if (ball.state !== 'loose') return;
    this.remove(this.loose, ball);
    this.world.removeRigidBody(ball.body!);
    ball.body = null;
    ball.state = 'floating';
    ball.floatAt = new THREE.Vector3(x, ball.half.y * 0.55, z);
    this.floating.push(ball);
  }

  /** Put a ball or domino back where it started. */
  reset(module: ModuleState) {
    if (!module.body) return;
    const { position, quaternion } = module.rest;
    module.body.setTranslation(position, true);
    module.body.setRotation(quaternion, true);
    module.body.setLinvel({ x: 0, y: 0, z: 0 }, true);
    module.body.setAngvel({ x: 0, y: 0, z: 0 }, true);
  }

  /** Rebuild everything, one building at a time, spreading outwards from a point. */
  rebuild(origin: THREE.Vector3) {
    const order = [...this.buildings].sort((a, b) => a.centre.distanceTo(origin) - b.centre.distanceTo(origin));
    this.rebuilds = order.map((building, index) => ({ building, at: this.time + 0.2 + index * 0.07 }));
  }

  /** Put one building back up at once, with the springy pop (the wind-up robot does this). */
  rebuildOne(building: BuildingState) {
    this.rebuilds = this.rebuilds.filter((entry) => entry.building !== building);
    this.restore(building);
  }

  get rebuilding() {
    return this.rebuilds.length > 0;
  }

  /** Advance collapse timers and debris lifetimes by one physics step. */
  step(dt: number) {
    this.time += dt;

    for (let i = this.queue.length - 1; i >= 0; i--) {
      const entry = this.queue[i];
      if (entry.at > this.time) continue;
      this.queue.splice(i, 1);
      entry.module.scheduled = false;
      this.detach(entry.module);
      this.checkFullCollapse(entry.module.building);
    }

    for (const building of this.buildings) if (building.drive && building.remaining > 0) this.driveOn(building, dt);

    // Walking into street furniture knocks it over without slowing the dino down.
    const { position: dino, radius } = this.dino;
    for (const building of this.buildings) {
      if (!isStreetProp(building.kind) || building.remaining === 0) continue;
      const { min, max } = building.box;
      const dx = Math.max(min.x - dino.x, 0, dino.x - max.x);
      const dz = Math.max(min.z - dino.z, 0, dino.z - max.z);
      if (dx * dx + dz * dz > radius * radius) continue;
      for (const module of building.modules) this.detach(module, dino, 7, 0.9);
    }

    // Raised pieces of a broken building that he walks or charges into come loose and tumble off him,
    // carried along the way he is going, instead of stopping him dead.
    for (const building of this.buildings) {
      if (building.kind !== 'building' || !building.fine || building.remaining === 0) continue;
      const { min, max } = building.box;
      if (Math.max(min.x - dino.x, 0, dino.x - max.x) > radius || Math.max(min.z - dino.z, 0, dino.z - max.z) > radius) continue;
      for (const module of building.modules) {
        if (module.state !== 'intact') continue;
        const low = module.box.min.y < BLOCKS_BELOW && !module.scheduled;
        if (low || module.box.min.y > this.dino.height) continue;
        const b = module.box;
        const mx = Math.max(b.min.x - dino.x, 0, dino.x - b.max.x);
        const mz = Math.max(b.min.z - dino.z, 0, dino.z - b.max.z);
        if (mx * mx + mz * mz <= radius * radius) this.detach(module, dino, 4, 0.5);
      }
    }

    for (let i = this.falling.length - 1; i >= 0; i--) {
      const module = this.falling[i];
      const body = module.body!;
      const velocity = body.linvel();
      const speed = Math.hypot(velocity.x, velocity.y, velocity.z);
      if (module.speed - speed > IMPACT_DROP && this.time >= module.quietUntil) {
        module.quietUntil = this.time + 0.08;
        this.events.onImpact?.(module, module.speed - speed);
      }
      module.speed = speed;
      const still = body.isSleeping() || speed < 0.2;
      module.settled = still ? module.settled + dt : 0;
      if (module.settled >= SETTLE_SECONDS) this.sink(module);
    }

    for (let i = this.sinking.length - 1; i >= 0; i--) {
      const module = this.sinking[i];
      module.sunk += dt;
      module.position.y -= SINK_SPEED * dt;
      if (module.sunk >= SINK_SECONDS) {
        module.state = 'gone';
        this.mesh.setVisibleAt(module.instanceId, false);
        this.sinking.splice(i, 1);
      }
    }

    for (const building of this.buildings) {
      if (building.tipping) this.stepTower(building, dt);
    }

    for (let i = this.rebuilds.length - 1; i >= 0; i--) {
      const entry = this.rebuilds[i];
      if (entry.at > this.time) continue;
      // Never rebuild a house on top of him: wait until he has walked clear.
      const { min, max } = entry.building.box;
      const dx = Math.max(min.x - dino.x, 0, dino.x - max.x);
      const dz = Math.max(min.z - dino.z, 0, dino.z - max.z);
      if (Math.hypot(dx, dz) < radius + 1.5) {
        entry.at = this.time + 0.4;
        continue;
      }
      this.rebuilds.splice(i, 1);
      this.restore(entry.building);
    }
  }

  /** Copy moving pieces' transforms into the batch. Call once per frame. */
  sync(dt: number) {
    for (const list of [this.falling, this.loose]) {
      for (const module of list) {
        const t = module.body!.translation();
        const r = module.body!.rotation();
        _matrix.compose(_v.set(t.x, t.y, t.z), _q.set(r.x, r.y, r.z, r.w), _one);
        this.mesh.setMatrixAt(module.instanceId, _matrix);
      }
    }
    for (const module of this.sinking) {
      // It shrinks away as it settles into the ground, rather than visibly sliding through it.
      const left = Math.max(1 - module.sunk / SINK_SECONDS, 0.001);
      _matrix.compose(module.position, module.quaternion, _scale.setScalar(left * left));
      this.mesh.setMatrixAt(module.instanceId, _matrix);
    }
    for (const building of this.buildings) {
      if (!building.tipping) continue;
      const t = building.tipping.body.translation();
      const r = building.tipping.body.rotation();
      _body.compose(_v.set(t.x, t.y, t.z), _q.set(r.x, r.y, r.z, r.w), _one);
      for (const module of building.modules) {
        if (module.state !== 'tipping') continue;
        this.mesh.setMatrixAt(module.instanceId, _matrix.multiplyMatrices(_body, module.tipLocal!));
      }
    }
    for (const module of this.floating) {
      const at = module.floatAt!;
      _v.set(at.x, at.y + Math.sin(this.time * 2 + at.x) * 0.18, at.z);
      _matrix.compose(_v, _q.setFromAxisAngle(_w.set(0, 1, 0), this.time * 0.4 + at.z), _one);
      this.mesh.setMatrixAt(module.instanceId, _matrix);
    }
    // Rebuilt pieces pop back up with a springy overshoot.
    for (let i = this.popping.length - 1; i >= 0; i--) {
      const module = this.popping[i];
      module.pop = Math.min(module.pop + dt, POP_SECONDS);
      const t = module.pop / POP_SECONDS;
      const s = 1 + 2.4 * (t - 1) ** 3 + 1.4 * (t - 1) ** 2; // ease-out-back
      if (module.state === 'intact') {
        _matrix.compose(module.rest.position, module.rest.quaternion, _scale.setScalar(Math.max(s, 0.001)));
        this.mesh.setMatrixAt(module.instanceId, _matrix);
      }
      if (t >= 1) this.popping.splice(i, 1);
    }
  }

  dispose() {
    for (const building of this.buildings) {
      if (building.rough) this.world.removeRigidBody(building.rough);
      if (building.fine) this.world.removeRigidBody(building.fine);
      if (building.tipping) this.world.removeRigidBody(building.tipping.body);
    }
    for (const list of [this.falling, this.loose]) for (const module of list) this.world.removeRigidBody(module.body!);
    this.mesh.dispose();
  }

  // --- internals ----------------------------------------------------------

  private remove(list: ModuleState[], module: ModuleState) {
    const index = list.indexOf(module);
    if (index >= 0) list.splice(index, 1);
  }

  /** Give a whole building its starting physics: one rough box, or loose bodies for dominoes and balls. */
  private stand(building: BuildingState) {
    const { rapier, world } = this;
    if (isLoose(building.kind)) {
      for (const module of building.modules) {
        const { position, quaternion } = module.rest;
        const body = world.createRigidBody(
          rapier.RigidBodyDesc.dynamic()
            .setTranslation(position.x, position.y, position.z)
            .setRotation(quaternion)
            .setLinearDamping(building.kind === 'ball' ? 0.35 : 0.05)
            .setAngularDamping(building.kind === 'ball' ? 0.5 : 0.1)
            .setSleeping(true),
        );
        const { half } = module;
        const shape =
          building.kind === 'ball'
            ? rapier.ColliderDesc.ball(half.y).setDensity(0.12).setRestitution(0.75).setFriction(0.6)
            : building.kind === 'block'
              ? ((module.hull && rapier.ColliderDesc.convexHull(module.hull)) || rapier.ColliderDesc.cuboid(half.x, half.y, half.z))
                  .setDensity(0.35)
                  .setFriction(0.7)
                  .setRestitution(0.1)
              : rapier.ColliderDesc.cuboid(half.x, half.y, half.z).setDensity(0.9).setFriction(0.55).setRestitution(0.05);
        world.createCollider(shape, body);
        module.body = body;
        module.state = 'loose';
        this.loose.push(module);
        if (building.kind === 'ball') this.balls.push(module);
        else if (building.kind === 'domino') this.dominoes.push(module);
      }
      return;
    }
    if (isStreetProp(building.kind)) return; // never in the dino's way
    const { position, quaternion, centre, half } = building.roughShape;
    building.rough = world.createRigidBody(
      rapier.RigidBodyDesc.fixed().setTranslation(position.x, position.y, position.z).setRotation(quaternion),
    );
    world.createCollider(
      rapier.ColliderDesc.cuboid(half.x, half.y, half.z).setTranslation(centre.x, centre.y, centre.z),
      building.rough,
    );
    // The gatehouse is two towers with an open gate between them: one box would block the gate.
    // Arches and open gates: one box would fill the opening, so these get their own pieces from the start.
    if (OPEN_UNDERNEATH.has(building.meta.type)) this.refine(building);
    if (building.kind === 'giantTower') {
      // Each base block comes away with one hit.
      building.modules.forEach((module) => (module.hp = 1));
    }
  }

  /** Swap a building's single rough box for one box per standing module. */
  private refine(building: BuildingState) {
    if (!building.rough) return;
    this.world.removeRigidBody(building.rough);
    building.rough = null;
    building.fine = this.world.createRigidBody(this.rapier.RigidBodyDesc.fixed());

    for (const module of building.modules) {
      // Signs, flags and brackets never get in the dino's way.
      if (module.state !== 'intact' || module.meta.role === 'detail') continue;
      const { half } = module;
      const { position, quaternion } = module.rest;
      module.collider = this.world.createCollider(
        this.rapier.ColliderDesc.cuboid(half.x, half.y, half.z)
          .setTranslation(position.x, position.y, position.z)
          .setRotation(quaternion),
        building.fine,
      );
      this.byCollider.set(module.collider.handle, module);
    }
  }

  private schedule(module: ModuleState, delay: number) {
    if (module.scheduled || module.state !== 'intact') return;
    module.scheduled = true;
    this.queue.push({ module, at: this.time + delay });
  }

  private spawnBody(module: ModuleState) {
    const { rapier, world } = this;
    const { half, position, quaternion } = module;
    const body = world.createRigidBody(
      rapier.RigidBodyDesc.dynamic()
        .setTranslation(position.x, position.y, position.z)
        .setRotation(quaternion)
        .setLinearDamping(0.1)
        .setAngularDamping(0.4),
    );
    // Slightly undersized, so neighbours that touched while standing don't burst apart.
    const shape =
      (module.hull && rapier.ColliderDesc.convexHull(module.hull)) ||
      rapier.ColliderDesc.cuboid(
        Math.max(half.x * 0.92, 0.05),
        Math.max(half.y * 0.92, 0.05),
        Math.max(half.z * 0.92, 0.05),
      );
    world.createCollider(shape.setDensity(0.5).setFriction(0.8).setRestitution(0.15), body);
    module.body = body;
    module.state = 'falling';
    module.settled = 0;
    module.speed = 0;
    this.falling.push(module);
    while (this.falling.length > this.maxMoving) this.sink(this.falling[0]);
    return body;
  }

  /** Turn a standing module into a tumbling piece. It never breaks further. */
  private detach(module: ModuleState, from?: THREE.Vector3, push = 0, lift = 0.8) {
    if (module.state !== 'intact') return;
    const building = module.building;
    this.refine(building);

    if (module.collider) {
      this.byCollider.delete(module.collider.handle);
      this.world.removeCollider(module.collider, true);
      module.collider = null;
    }
    module.position.copy(module.rest.position);
    module.quaternion.copy(module.rest.quaternion);
    const body = this.spawnBody(module);
    building.remaining--;

    if (from) {
      this.push(body, from, push, lift);
    } else {
      // Unsupported pieces get a small nudge so stacks crumble instead of dropping flat.
      const mass = body.mass();
      body.applyTorqueImpulse(
        { x: (Math.random() - 0.5) * mass * 2, y: 0, z: (Math.random() - 0.5) * mass * 2 },
        true,
      );
    }
    this.events.onBreak?.(module, !!from);

    if (building.kind !== 'giantTower') {
      // Collapse spreads upwards: anything this was the last support for follows.
      for (const above of module.holdsUp) {
        if (above.supportedBy.every((support) => support.state !== 'intact')) this.schedule(above, STOREY_DELAY);
      }
    }
    this.checkDown(building);
  }

  private checkDown(building: BuildingState) {
    if (building.down) return;
    const share = building.remaining / building.modules.length;
    if (isStreetProp(building.kind) ? building.remaining > 0 : share >= DOWN_SHARE) return;
    building.down = true;
    this.events.onDown?.(building);
  }

  private push(body: RigidBody, from: THREE.Vector3, strength: number, lift: number) {
    const t = body.translation();
    _v.set(t.x - from.x, 0, t.z - from.z);
    if (_v.lengthSq() < 1e-4) _v.set(Math.random() - 0.5, 0, Math.random() - 0.5);
    _v.normalize();
    // A move with a direction throws things mostly that way, with a little spread.
    if (this.aim) _v.multiplyScalar(0.35).add(_w.set(this.aim.x, 0, this.aim.z)).normalize();
    const mass = body.mass();
    const kick = strength * mass * (0.75 + Math.random() * 0.5);
    body.applyImpulse({ x: _v.x * kick, y: kick * lift, z: _v.z * kick }, true);
    const spin = mass * strength * 0.25;
    body.applyTorqueImpulse(
      { x: (Math.random() - 0.5) * spin, y: (Math.random() - 0.5) * spin, z: (Math.random() - 0.5) * spin },
      true,
    );
  }

  private checkFullCollapse(building: BuildingState) {
    if (building.kind !== 'building') return;
    let total = 0;
    let standing = 0;
    for (const module of building.modules) {
      if (module.meta.storey !== 0 || (module.meta.role !== 'wall' && module.meta.role !== 'pillar')) continue;
      total++;
      if (module.state === 'intact' && !module.scheduled) standing++;
    }
    if (total === 0 || standing / total >= FULL_COLLAPSE_SHARE) return;
    for (const module of building.modules) this.schedule(module, STOREY_DELAY * (module.meta.storey + 1));
  }

  /** Settled debris sinks into the ground and disappears. */
  private sink(module: ModuleState) {
    this.remove(this.falling, module);
    const body = module.body!;
    const t = body.translation();
    const r = body.rotation();
    module.position.set(t.x, t.y, t.z);
    module.quaternion.set(r.x, r.y, r.z, r.w);
    this.world.removeRigidBody(body);
    module.body = null;
    module.state = 'sinking';
    module.sunk = 0;
    this.sinking.push(module);
    this.events.onSink?.(module);
  }

  // --- vehicles ----------------------------------------------------------------

  private startDriving(building: BuildingState) {
    const flat = building.meta.route ?? [];
    // The layout's (x, y) is the game's (x, -z).
    const route: THREE.Vector3[] = [];
    for (let i = 0; i + 1 < flat.length; i += 2) route.push(new THREE.Vector3(flat[i], 0, -flat[i + 1]));
    if (route.length < 2) return;
    let length = 0;
    for (let i = 0; i < route.length; i++) length += route[i].distanceTo(route[(i + 1) % route.length]);
    const inverse = new THREE.Matrix4().compose(building.roughShape.position, building.roughShape.quaternion, _one).invert();
    for (const module of building.modules) {
      module.carried = new THREE.Matrix4().multiplyMatrices(inverse, _matrix.compose(module.rest.position, module.rest.quaternion, _one));
    }
    building.drive = { route, length, at: 0, speed: building.meta.speed ?? 6, yaw: THREE.MathUtils.degToRad(building.meta.yaw ?? 0) };
  }

  /** Move a vehicle along its route, carrying its pieces, and bump aside any street furniture in its way. */
  private driveOn(building: BuildingState, dt: number) {
    const drive = building.drive!;
    drive.at = (drive.at + drive.speed * dt) % drive.length;
    let left = drive.at;
    const { route } = drive;
    let from = route[0];
    let to = route[1];
    for (let i = 0; i < route.length; i++) {
      from = route[i];
      to = route[(i + 1) % route.length];
      const leg = from.distanceTo(to);
      if (left <= leg || i === route.length - 1) {
        _v.copy(from).lerp(to, leg > 0 ? Math.min(left / leg, 1) : 0);
        break;
      }
      left -= leg;
    }
    const heading = Math.atan2(to.x - from.x, to.z - from.z) + drive.yaw;
    // Turn smoothly rather than snapping round the corners.
    const current = building.roughShape.quaternion;
    _q.setFromAxisAngle(_w.set(0, 1, 0), heading);
    current.slerp(_q, 1 - Math.exp(-dt * 5));
    building.roughShape.position.copy(_v);
    _body.compose(_v, current, _one);

    building.box.makeEmpty();
    for (const module of building.modules) {
      if (module.state !== 'intact') continue;
      _matrix.multiplyMatrices(_body, module.carried!);
      _matrix.decompose(module.rest.position, module.rest.quaternion, _scale);
      module.box.copy(module.shape).applyMatrix4(_matrix);
      building.box.union(module.box);
      this.mesh.setMatrixAt(module.instanceId, _matrix);
    }
    building.box.getCenter(building.centre);

    for (const other of this.buildings) {
      if (other === building || other.remaining === 0 || (other.kind !== 'prop' && other.kind !== 'crate')) continue;
      if (!other.box.intersectsBox(building.box)) continue;
      for (const module of other.modules) this.detach(module, building.centre, 4, 0.6);
    }
  }

  // --- the giant tower ------------------------------------------------------

  /** Only the pillars can be hit. When the last one goes, the whole tower tips over. */
  private hitTower(building: BuildingState, centre: THREE.Vector3, radius: number, push: number, lift: number, counted: boolean) {
    this.refine(building);
    let standing = 0;
    for (const module of building.modules) {
      if (module.meta.role !== 'pillar' || module.state !== 'intact') continue;
      if (counted && module.box.distanceToPoint(centre) <= radius) {
        module.hp--;
        if (module.hp <= 0) {
          // They are big and heavy, so they get a harder shove than ordinary pieces.
          this.detach(module, centre, push * 2, lift);
          continue;
        }
      }
      standing++;
    }
    if (standing === 0) this.tip(building, centre);
  }

  private tip(building: BuildingState, from: THREE.Vector3) {
    const { rapier, world } = this;
    if (building.fine) world.removeRigidBody(building.fine);
    building.fine = null;

    const origin = building.roughShape.position;
    const body = world.createRigidBody(
      rapier.RigidBodyDesc.dynamic().setTranslation(origin.x, origin.y, origin.z).setAngularDamping(0.2),
    );
    for (const module of building.modules) {
      if (module.state !== 'intact') continue;
      if (module.collider) this.byCollider.delete(module.collider.handle);
      module.collider = null;
      const { half } = module;
      const { position, quaternion } = module.rest;
      world.createCollider(
        rapier.ColliderDesc.cuboid(half.x, half.y, half.z)
          .setTranslation(position.x - origin.x, position.y - origin.y, position.z - origin.z)
          .setRotation(quaternion)
          .setDensity(0.5)
          .setFriction(0.9),
        body,
      );
      module.tipLocal = new THREE.Matrix4().compose(_v.copy(position).sub(origin), quaternion, _one);
      module.state = 'tipping';
    }
    // It always falls away from wherever the hit came from, never towards the dino.
    _v.set(origin.x - from.x, 0, origin.z - from.z);
    if (_v.lengthSq() < 1e-4) _v.set(0, 0, -1);
    _v.normalize();
    body.setAngvel({ x: _v.z * 0.9, y: 0, z: -_v.x * 0.9 }, true);
    body.setLinvel({ x: _v.x * 2.5, y: 0, z: _v.z * 2.5 }, true);
    building.tipping = { body, time: 0 };
    this.events.onTowerTip?.(building);
  }

  private stepTower(building: BuildingState, dt: number) {
    const tipping = building.tipping!;
    tipping.time += dt;
    const { body } = tipping;
    const r = body.rotation();
    const upright = _v.set(0, 1, 0).applyQuaternion(_q.set(r.x, r.y, r.z, r.w)).y;
    // Keep it going over: a tower that settles upright on its base would be no finale at all.
    if (upright > 0.5 && tipping.time > 0.3) {
      const spin = body.angvel();
      const length = Math.hypot(spin.x, spin.z) || 1;
      const mass = body.mass();
      body.applyTorqueImpulse(
        { x: (spin.x / length) * mass * 6 * dt * 60, y: 0, z: (spin.z / length) * mass * 6 * dt * 60 },
        true,
      );
    }
    if (upright > 0.42 && tipping.time < 6) return;

    // It has landed: break apart into its modules.
    const t = body.translation();
    const linear = body.linvel();
    const angular = body.angvel();
    _body.compose(_v.set(t.x, t.y, t.z), _q.set(r.x, r.y, r.z, r.w), _one);
    const pieces: ModuleState[] = [];
    for (const module of building.modules) {
      if (module.state !== 'tipping') continue;
      _matrix.multiplyMatrices(_body, module.tipLocal!).decompose(module.position, module.quaternion, _scale);
      pieces.push(module);
    }
    this.world.removeRigidBody(body);
    building.tipping = null;
    for (const module of pieces) {
      const piece = this.spawnBody(module);
      // Each piece keeps the speed it had as part of the falling tower.
      _v.copy(module.position).sub(_w.set(t.x, t.y, t.z));
      _w.set(angular.x, angular.y, angular.z).cross(_v);
      piece.setLinvel({ x: linear.x + _w.x, y: linear.y + _w.y, z: linear.z + _w.z }, true);
      piece.setAngvel(angular, true);
      building.remaining--;
      this.events.onBreak?.(module, false);
    }
    this.events.onTowerCrash?.(building);
    this.checkDown(building);
  }

  // --- rebuilding -------------------------------------------------------------

  private restore(building: BuildingState) {
    const { world } = this;
    if (building.rough) world.removeRigidBody(building.rough);
    if (building.fine) world.removeRigidBody(building.fine);
    if (building.tipping) world.removeRigidBody(building.tipping.body);
    building.rough = building.fine = null;
    building.tipping = null;

    const mine = new Set(building.modules);
    this.queue = this.queue.filter((entry) => !mine.has(entry.module));
    for (const module of building.modules) {
      if (module.collider) this.byCollider.delete(module.collider.handle);
      if (module.body) world.removeRigidBody(module.body);
      for (const list of [this.falling, this.sinking, this.loose, this.floating]) this.remove(list, module);
      this.remove(this.dominoes, module);
      this.remove(this.balls, module);
      module.body = null;
      module.collider = null;
      module.scheduled = false;
      module.state = 'intact';
      module.settled = module.sunk = 0;
      module.floatAt = null;
      module.position.copy(module.rest.position);
      module.quaternion.copy(module.rest.quaternion);
      this.mesh.setVisibleAt(module.instanceId, true);
      _matrix.compose(module.rest.position, module.rest.quaternion, _one);
      this.mesh.setMatrixAt(module.instanceId, _matrix);
      if (!isLoose(building.kind)) {
        module.pop = 0;
        this.popping.push(module);
      }
    }
    building.remaining = building.modules.length;
    building.hits = 0;
    building.lastMove = -1;
    building.down = false;
    this.stand(building);
    this.dominoes.sort((a, b) => (a.building.meta.order ?? 0) - (b.building.meta.order ?? 0));
    this.events.onRebuilt?.(building);
  }
}
