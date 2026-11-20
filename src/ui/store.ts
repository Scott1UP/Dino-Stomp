import { useSyncExternalStore } from 'react';
import { DINOS, LEVELS, SECRET_LEVELS, levelDef, type LevelId, type Mode } from '../game/levels';
import { game, input } from '../game/state';
import type { DinoId } from '../types';

export type Screen =
  | 'title'
  | 'dinoSelect'
  | 'levelSelect'
  | 'playing'
  | 'paused'
  | 'complete'
  | 'parent'
  | 'stickers';

export type Graphics = 'high' | 'medium' | 'low';

interface Settings {
  volume: number;
  music: boolean;
  shake: boolean;
  /** Lower settings trade looks for a steadier frame rate on older tablets. */
  graphics: Graphics;
  /** A small frames-per-second counter in the corner, for judging the graphics setting. */
  fps: boolean;
}

interface State {
  screen: Screen;
  mode: Mode;
  dino: DinoId;
  level: LevelId;
  /** How many story levels are open, in order. */
  unlocked: number;
  completed: Record<LevelId, boolean>;
  /** Objective progress per level. Leaving a level keeps it. */
  progress: Record<LevelId, [number, number]>;
  /** Bumped to load a level afresh. */
  session: number;
  sessionKey: string | null;
  celebrated: boolean;
  swapping: boolean;
  parentReturn: Screen;
  stickersReturn: Screen;
  settings: Settings;
  /** Stickers he has earned, by id. */
  stickers: Record<string, boolean>;
  /** Golden dinos found, by level. */
  secrets: Partial<Record<LevelId, boolean>>;
  /** Whether he has picked up the golden dino on this visit to the level (for the badge). */
  foundHere: boolean;
  /** The sticker just earned, shown big for a moment. */
  toast: string | null;
}

const SAVE_KEY = 'dino-stomp-save';
const emptyProgress = () =>
  Object.fromEntries(LEVELS.map((l) => [l.id, [0, 0]])) as Record<LevelId, [number, number]>;
const noneCompleted = () => Object.fromEntries(LEVELS.map((l) => [l.id, false])) as Record<LevelId, boolean>;

function load(): Partial<State> {
  try {
    return JSON.parse(localStorage.getItem(SAVE_KEY) ?? '{}');
  } catch {
    return {};
  }
}

const saved = load();

let state: State = {
  screen: 'title',
  mode: 'story',
  dino: DINOS.some((d) => d.id === saved.dino) ? saved.dino! : 'trex',
  level: saved.level ?? 'block-town',
  unlocked: saved.unlocked ?? 1,
  completed: { ...noneCompleted(), ...saved.completed },
  progress: emptyProgress(),
  session: 0,
  sessionKey: null,
  celebrated: false,
  swapping: false,
  parentReturn: 'title',
  stickersReturn: 'title',
  settings: { volume: 0.8, music: true, shake: true, graphics: 'high', fps: false, ...saved.settings },
  stickers: saved.stickers ?? {},
  secrets: saved.secrets ?? {},
  foundHere: false,
  toast: null,
};

const listeners = new Set<() => void>();

function set(patch: Partial<State>) {
  const leavingPlay = state.screen === 'playing' && patch.screen && patch.screen !== 'playing';
  const enteringPlay = state.screen !== 'playing' && patch.screen === 'playing';
  state = { ...state, ...patch };
  if (leavingPlay || enteringPlay) {
    // Nothing he pressed on a menu should carry into the level, or the other way round.
    input.smash = 0;
    input.charging = false;
    input.target = null;
    input.stick.active = false;
    input.stick.x = 0;
    input.stick.y = 0;
  }
  try {
    const { dino, level, unlocked, completed, settings, stickers, secrets } = state;
    localStorage.setItem(SAVE_KEY, JSON.stringify({ dino, level, unlocked, completed, settings, stickers, secrets }));
  } catch {
    // Private browsing: the game still works, it just won't remember.
  }
  listeners.forEach((listener) => listener());
}

export const getState = () => state;

export function useStore<T>(selector: (s: State) => T): T {
  return useSyncExternalStore(
    (listener) => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    () => selector(state),
  );
}

const done = (level: LevelId) =>
  levelDef(level).objectives.every((objective, i) => state.progress[level][i] >= objective.required);

export const actions = {
  chooseMode(mode: Mode) {
    set({ mode, swapping: false, screen: 'dinoSelect' });
  },

  chooseDino(dino: DinoId) {
    // Swapping mid-level goes straight back to the level, progress untouched.
    if (state.swapping) set({ dino, swapping: false, screen: 'playing' });
    else set({ dino, screen: 'levelSelect' });
  },

  chooseLevel(level: LevelId) {
    const key = `${state.mode}:${level}`;
    // Going back into the level he just left continues it. A finished level starts over.
    const fresh = key !== state.sessionKey || (state.mode === 'story' && done(level));
    const patch: Partial<State> = { level, sessionKey: key };
    if (fresh) {
      patch.session = state.session + 1;
      patch.progress = { ...state.progress, [level]: [0, 0] };
      patch.celebrated = false;
      patch.foundHere = false;
    }
    // Straight into the level: the progress display at the top shows what to smash.
    set({ ...patch, screen: 'playing' });
  },

  addProgress(index: 0 | 1) {
    if (state.mode !== 'story') return;
    const current = state.progress[state.level];
    if (current[index] >= levelDef(state.level).objectives[index].required) return;
    const next: [number, number] = [current[0], current[1]];
    next[index]++;
    set({ progress: { ...state.progress, [state.level]: next } });

    if (!state.celebrated && done(state.level)) {
      const level = state.level;
      const index = LEVELS.findIndex((l) => l.id === level);
      set({
        celebrated: true,
        completed: { ...state.completed, [level]: true },
        unlocked: Math.max(state.unlocked, Math.min(index + 2, LEVELS.length)),
      });
      actions.award(`level-${level}`);
      // A moment to watch the last thing fall before the party starts.
      setTimeout(() => {
        if (state.level === level && state.screen === 'playing') set({ screen: 'complete' });
      }, 2600);
    }
  },

  pause() {
    if (state.screen === 'playing') set({ screen: 'paused' });
  },
  resume() {
    set({ screen: 'playing' });
  },
  home() {
    set({ screen: 'title' });
  },
  back() {
    if (state.screen === 'dinoSelect') set(state.swapping ? { swapping: false, screen: 'paused' } : { screen: 'title' });
    else if (state.screen === 'levelSelect') set({ screen: 'dinoSelect' });
  },
  swapDino() {
    set({ swapping: true, screen: 'dinoSelect' });
  },
  /** Sandbox: everything pops back up, spreading outwards from the dino. */
  rebuild() {
    game.town?.rebuild(game.dino.position);
    set({ screen: 'playing' });
  },
  keepStomping() {
    set({ screen: 'playing' });
  },
  nextLevel() {
    // On through the story; the secret Robot Castle is never "next", it is chosen from the map.
    const index = LEVELS.findIndex((l) => l.id === state.level);
    const next = LEVELS.slice(index + 1).find((l) => !l.secret);
    if (next && !levelDef(state.level).secret) actions.chooseLevel(next.id);
    else set({ screen: 'levelSelect' });
  },

  /** Earn a sticker. The first time, it is shown big and announced. */
  award(id: string) {
    if (state.stickers[id]) return;
    set({ stickers: { ...state.stickers, [id]: true }, toast: id });
    window.setTimeout(() => {
      if (state.toast === id) set({ toast: null });
    }, 3200);
  },
  findSecret(level: LevelId) {
    set({ secrets: { ...state.secrets, [level]: true }, foundHere: true });
    actions.award('secret');
  },
  openStickers() {
    set({ stickersReturn: state.screen, screen: 'stickers' });
  },
  closeStickers() {
    set({ screen: state.stickersReturn });
  },

  openParent() {
    set({ parentReturn: state.screen, screen: 'parent' });
  },
  closeParent() {
    set({ screen: state.parentReturn });
  },
  setSetting<K extends keyof Settings>(key: K, value: Settings[K]) {
    set({ settings: { ...state.settings, [key]: value } });
  },
  resetProgress() {
    set({
      unlocked: 1,
      completed: noneCompleted(),
      progress: emptyProgress(),
      sessionKey: null,
      celebrated: false,
      stickers: {},
      secrets: {},
    });
  },
};

/** True once every golden dino has been found: the robot castle opens. */
export const allSecrets = (secrets: Partial<Record<LevelId, boolean>>) => SECRET_LEVELS.every((id) => secrets[id]);
