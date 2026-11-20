export type DinoId = 'trex' | 'triceratops' | 'stegosaurus';
export type Material = 'plaster' | 'tile' | 'wood' | 'glass' | 'tin' | 'stone' | 'rubber' | 'leaves';

export interface DinoStats {
  id: DinoId;
  speed: number; // metres per second
  move: 'bite' | 'charge' | 'tailSwing';
  moveRadius: number; // stomp and tail swing
  moveLength?: number; // charge
  pushStrength: number;
  cooldownSeconds: number;
}

export interface BuildingMeta {
  id: string;
  type: string; // e.g. "terraced_house"
  seed: number;
  scheme: string;
  hitsToCollapse: 1 | 2 | 3;
  objective?: string; // objective id, if this is a target
}

export interface ModuleMeta {
  id: string;
  buildingId: string;
  role: 'wall' | 'corner' | 'floor' | 'band' | 'roof' | 'detail' | 'pillar';
  material: Material;
  storey: number; // 0 is the ground floor
  supports: string[]; // module ids holding this one up
  collider: 'box' | 'hull';
}
