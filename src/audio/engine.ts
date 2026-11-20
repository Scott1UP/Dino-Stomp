import type { DinoId, Material } from '../types';
import { getState } from '../ui/store';

/**
 * The game's sound, built on the Web Audio API.
 *
 * Every sound is synthesised when the game starts (there are no audio files
 * yet), decoded into buffers once, then played with one-off source nodes.
 * Sounds are grouped into channels that feed one compressor, so nothing clips
 * during the biggest collapse.
 */

type Channel = 'dino' | 'breaks' | 'debris' | 'ui' | 'voice' | 'music';

const VARIANTS = 5;
/** Breaks this close together climb a pentatonic scale, so long chains sound musical. */
const CHAIN_WINDOW = 1.0;
const PENTATONIC = [0, 2, 4, 7, 9, 12, 14, 16, 19, 21, 24];
const MAX_DEBRIS_VOICES = 8;
const MAX_BREAK_VOICES = 14;

let context: AudioContext | null = null;
let master: GainNode;
let compressor: DynamicsCompressorNode;
const channels = {} as Record<Channel, GainNode>;
const buffers = new Map<string, AudioBuffer[]>();
const lastVariant = new Map<string, number>();
const debrisVoices: AudioBufferSourceNode[] = [];
let breakVoices = 0;
let chargeHum: OscillatorNode | null = null;
let chainStep = 0;
let lastBreakAt = -10;
let chaos = 0;

// --- synthesis ---------------------------------------------------------------

type Voice = (t: number, noise: () => number) => number;

function render(seconds: number, voice: Voice): AudioBuffer {
  const rate = context!.sampleRate;
  const buffer = context!.createBuffer(1, Math.ceil(seconds * rate), rate);
  const data = buffer.getChannelData(0);
  const noise = () => Math.random() * 2 - 1;
  let peak = 0;
  for (let i = 0; i < data.length; i++) {
    const t = i / rate;
    // A few milliseconds of fade at each end stops clicks.
    const edge = Math.min(1, t / 0.003, (seconds - t) / 0.01);
    data[i] = voice(t, noise) * edge;
    peak = Math.max(peak, Math.abs(data[i]));
  }
  if (peak > 0) for (let i = 0; i < data.length; i++) data[i] *= 0.9 / peak;
  return buffer;
}

/** A one-pole low-pass, for turning white noise into softer thumps and rumbles. */
function lowpass(amount: number) {
  let state = 0;
  return (sample: number) => (state += (sample - state) * amount);
}

const sine = (frequency: number, t: number) => Math.sin(2 * Math.PI * frequency * t);
const decay = (t: number, rate: number) => Math.exp(-t * rate);
const vary = (base: number, spread: number) => base * (1 + (Math.random() * 2 - 1) * spread);

function variants(name: string, make: () => AudioBuffer) {
  buffers.set(name, Array.from({ length: VARIANTS }, make));
}

function synthesise() {
  // Each break is three layers: the hit, the material, and the debris landing.
  variants('hit', () => {
    const f = vary(70, 0.2);
    const lp = lowpass(0.08);
    return render(0.28, (t, n) => sine(f * (1 + decay(t, 30)), t) * decay(t, 14) + lp(n()) * decay(t, 30) * 0.8);
  });

  const material: Record<Material, () => AudioBuffer> = {
    // A soft, chunky clack.
    plaster: () => {
      const f = vary(190, 0.15);
      const lp = lowpass(0.18);
      return render(0.16, (t, n) => lp(n()) * decay(t, 45) + sine(f, t) * decay(t, 35) * 0.6);
    },
    // A light clatter: a few grains.
    tile: () => {
      const grains = [0, vary(0.035, 0.3), vary(0.075, 0.3)];
      const f = vary(1500, 0.2);
      return render(0.2, (t, n) =>
        grains.reduce((sum, at) => (t < at ? sum : sum + (n() * 0.5 + sine(f, t)) * decay(t - at, 90)), 0),
      );
    },
    // A hollow clonk.
    wood: () => {
      const f = vary(330, 0.18);
      return render(0.22, (t, n) => sine(f, t) * decay(t, 26) + sine(f * 2.4, t) * decay(t, 50) * 0.4 + n() * decay(t, 200) * 0.3);
    },
    // Chimes and tinkles, never a sharp shatter.
    glass: () => {
      const notes = [vary(1900, 0.1), vary(2550, 0.1), vary(3200, 0.1)];
      return render(0.6, (t) => notes.reduce((sum, f, i) => sum + sine(f, t) * decay(Math.max(t - i * 0.04, 0), 9) * (t >= i * 0.04 ? 1 : 0), 0));
    },
    // A toy-tin clang.
    tin: () => {
      const f = vary(520, 0.12);
      return render(0.4, (t, n) => (sine(f, t) + sine(f * 1.59, t) * 0.7 + sine(f * 2.33, t) * 0.5) * decay(t, 13) + n() * decay(t, 150) * 0.25);
    },
    // A deep thunk.
    stone: () => {
      const f = vary(95, 0.12);
      const lp = lowpass(0.06);
      return render(0.3, (t, n) => sine(f, t) * decay(t, 16) + lp(n()) * decay(t, 22) * 1.2);
    },
    rubber: () => {
      const f = vary(210, 0.1);
      return render(0.3, (t) => sine(f * (1 + t * 3), t) * decay(t, 10));
    },
    leaves: () => {
      const lp = lowpass(0.5);
      return render(0.3, (t, n) => (n() - lp(n())) * Math.sin(Math.min(t / 0.3, 1) * Math.PI) ** 2);
    },
  };
  for (const [name, make] of Object.entries(material)) variants(name, make);

  variants('debris', () => {
    const f = vary(260, 0.4);
    const lp = lowpass(0.25);
    return render(0.1, (t, n) => lp(n()) * decay(t, 70) + sine(f, t) * decay(t, 60) * 0.4);
  });

  // --- dino sets ---
  variants('step', () => {
    const lp = lowpass(0.05);
    return render(0.2, (t, n) => sine(vary(55, 0.1) * (1 + decay(t, 25)), t) * decay(t, 20) + lp(n()) * decay(t, 30));
  });
  variants('stomp', () => {
    const lp = lowpass(0.04);
    return render(0.7, (t, n) => sine(38 + 40 * decay(t, 12), t) * decay(t, 5) * 1.4 + lp(n()) * decay(t, 9));
  });
  variants('crunch', () => {
    const lp = lowpass(0.3);
    return render(0.3, (t, n) => lp(n()) * decay(t, 18) * (0.6 + 0.4 * sine(45, t)) + sine(vary(140, 0.1), t) * decay(t, 20) * 0.6);
  });
  variants('whoosh', () => {
    const lp = lowpass(0.2);
    return render(0.4, (t, n) => lp(n()) * Math.sin(Math.min(t / 0.4, 1) * Math.PI) ** 2);
  });
  variants('bonk', () => render(0.4, (t, n) => sine(vary(150, 0.08), t) * decay(t, 9) + sine(300, t) * decay(t, 25) * 0.4 + n() * decay(t, 250) * 0.3));
  variants('boing', () => render(0.5, (t) => sine(170 * (1 + 0.5 * Math.sin(t * 38) * decay(t, 6)), t) * decay(t, 6)));
  variants('whistle', () => render(0.7, (t) => sine(1500 * decay(t, 1.4), t) * Math.sin(Math.min(t / 0.7, 1) * Math.PI) * 0.6));

  const roar = (base: number) => () => {
    const lp = lowpass(0.12);
    const wobble = vary(27, 0.2);
    return render(0.95, (t, n) => {
      const pitch = base * (1.5 - t * 0.9);
      const growl = Math.sign(sine(pitch, t)) * 0.5 + sine(pitch * 0.5, t);
      return (growl * (0.7 + 0.3 * sine(wobble, t)) + lp(n()) * 0.5) * Math.sin(Math.min(t / 0.95, 1) * Math.PI) ** 0.6;
    });
  };
  variants('roar-trex', roar(105));
  variants('roar-triceratops', roar(150));
  variants('roar-stegosaurus', roar(125));

  // --- interface and level sounds ---
  variants('click', () => render(0.07, (t) => sine(vary(700, 0.05) * (1 + t * 5), t) * decay(t, 40)));
  variants('uibonk', () => render(0.2, (t) => sine(190 * decay(t, 4), t) * decay(t, 14)));
  variants('pop', () => render(0.14, (t) => sine(vary(520, 0.05) * (1 + t * 7), t) * decay(t, 18)));
  variants('sparkle', () => render(0.5, (t) => [1320, 1760, 2640].reduce((s, f, i) => s + (t > i * 0.07 ? sine(f, t) * decay(t - i * 0.07, 9) : 0), 0)));
  variants('bell', () => render(1.6, (t) => (sine(660, t) + sine(1325, t) * 0.6 + sine(1990, t) * 0.35) * decay(t, 2.6)));
  variants('splash', () => {
    const lp = lowpass(0.35);
    return render(0.6, (t, n) => lp(n()) * decay(t, 7) * (1 - decay(t, 80)) + sine(400 * decay(t, 6) + 120, t) * decay(t, 12) * 0.5);
  });
  variants('rebuild', () => render(0.3, (t) => sine(vary(300, 0.15) * (1 + 0.6 * Math.sin(t * 34) * decay(t, 8)) * (1 + t), t) * decay(t, 10)));
  variants('firework', () => {
    const lp = lowpass(0.3);
    return render(0.9, (t, n) => (t < 0.25 ? sine(600 + t * 3000, t) * 0.3 : (n() - lp(n())) * decay(t - 0.25, 5)));
  });
  variants('snare', () => {
    const lp = lowpass(0.5);
    return render(0.12, (t, n) => (n() - lp(n()) * 0.5) * decay(t, 32) + sine(190, t) * decay(t, 40) * 0.5);
  });
  variants('hat', () => {
    const lp = lowpass(0.6);
    return render(0.04, (t, n) => (n() - lp(n())) * decay(t, 90));
  });
}

// --- playing -------------------------------------------------------------------

function ensure() {
  if (!context) {
    context = new AudioContext();
    compressor = context.createDynamicsCompressor();
    compressor.threshold.value = -16;
    compressor.ratio.value = 6;
    compressor.attack.value = 0.004;
    compressor.release.value = 0.2;
    master = context.createGain();
    compressor.connect(master).connect(context.destination);
    const levels: Record<Channel, number> = { dino: 0.9, breaks: 0.7, debris: 0.45, ui: 0.6, voice: 1.1, music: 0.3 };
    for (const [name, level] of Object.entries(levels) as [Channel, number][]) {
      channels[name] = context.createGain();
      channels[name].gain.value = level;
      channels[name].connect(compressor);
    }
    synthesise();
    void loadRecordings(context);
  }
  // Browsers keep audio suspended until the first tap.
  if (context.state === 'suspended') void context.resume();
  master.gain.value = getState().settings.volume;
  return context;
}

const voices = new Map<string, AudioBuffer>();
let speaking: AudioBufferSourceNode | null = null;

/**
 * Recorded sounds and spoken lines (made once with `npm run audio`) replace the
 * synthesised stand-ins as they arrive. Anything missing keeps its stand-in.
 */
async function loadRecordings(ctx: AudioContext) {
  try {
    const manifest: { sfx: string[]; voice: string[]; music?: string[] } = await (await fetch('/audio/manifest.json')).json();
    const decode = async (url: string) => ctx.decodeAudioData(await (await fetch(url)).arrayBuffer());

    // "plaster-1", "plaster-2" are versions of "plaster".
    const groups = new Map<string, string[]>();
    for (const id of manifest.sfx) {
      const name = id.replace(/-\d+$/, '');
      groups.set(name, [...(groups.get(name) ?? []), id]);
    }
    for (const [name, ids] of groups) {
      void Promise.all(ids.map((id) => decode(`/audio/sfx/${id}.mp3`))).then((set) => buffers.set(name, set));
    }
    for (const id of manifest.voice) {
      void decode(`/audio/voice/${id}.mp3`).then((buffer) => voices.set(id, buffer));
    }
    for (const id of manifest.music ?? []) {
      void decode(`/audio/music/${id}.mp3`).then((buffer) => {
        tracks.set(id, buffer);
        if (trackWanted === id) playTrack(id);
      });
    }
  } catch {
    // No recordings: the synthesised sounds and the browser's voice carry on.
  }
}

interface PlayOptions {
  gain?: number;
  rate?: number;
  pan?: number;
  delay?: number;
}

function play(name: string, channel: Channel, options: PlayOptions = {}) {
  const ctx = ensure();
  const set = buffers.get(name);
  if (!set) return null;
  // Never the exact same version twice in a row.
  let index = Math.floor(Math.random() * set.length);
  if (index === lastVariant.get(name)) index = (index + 1) % set.length;
  lastVariant.set(name, index);

  const source = ctx.createBufferSource();
  source.buffer = set[index];
  source.playbackRate.value = (options.rate ?? 1) * (0.9 + Math.random() * 0.2);
  const gain = ctx.createGain();
  gain.gain.value = options.gain ?? 1;
  const panner = ctx.createStereoPanner();
  panner.pan.value = Math.max(-1, Math.min(1, options.pan ?? 0));
  source.connect(gain).connect(panner).connect(channels[channel]);
  source.start(ctx.currentTime + (options.delay ?? 0));
  return source;
}

/** Left-right placement and loudness from where a sound is, relative to the dino. */
function place(dx: number, distance: number): PlayOptions {
  return { pan: dx / 45, gain: 1 / (1 + (distance / 40) ** 2) };
}

/** Music dips for 300 ms so big hits punch through. */
function duck() {
  if (!context) return;
  const gain = channels.music.gain;
  const now = context.currentTime;
  gain.cancelScheduledValues(now);
  gain.setValueAtTime(gain.value, now);
  gain.linearRampToValueAtTime(0.15, now + 0.02);
  gain.linearRampToValueAtTime(0.3, now + 0.3);
}

export const audio = {
  /** Call from the first tap: the audio context starts suspended until then. */
  unlock: ensure,

  /** A module came off a building. */
  breakSound(material: Material, dx: number, distance: number, struck: boolean) {
    const ctx = ensure();
    chaos = Math.min(1, chaos + 0.05);
    if (breakVoices >= MAX_BREAK_VOICES) return;
    const now = ctx.currentTime;
    chainStep = now - lastBreakAt < CHAIN_WINDOW ? Math.min(chainStep + 1, PENTATONIC.length - 1) : 0;
    lastBreakAt = now;
    const at = place(dx, distance);
    const source = play(material, 'breaks', { ...at, rate: 2 ** (PENTATONIC[chainStep] / 12) });
    if (source) {
      breakVoices++;
      source.onended = () => breakVoices--;
    }
    if (struck) play('hit', 'breaks', { ...at, gain: (at.gain ?? 1) * 0.8 });
  },

  /** A tumbling piece landed. Limited to 8 at once, and a new one cuts off the oldest. */
  impact(material: Material, speed: number, dx: number, distance: number) {
    const at = place(dx, distance);
    const loud = Math.min(speed / 14, 1);
    if (loud < 0.2) return;
    while (debrisVoices.length >= MAX_DEBRIS_VOICES) debrisVoices.shift()!.stop();
    const source = play(Math.random() < 0.5 ? 'debris' : material, 'debris', { ...at, gain: (at.gain ?? 1) * loud });
    if (!source) return;
    debrisVoices.push(source);
    source.onended = () => {
      const index = debrisVoices.indexOf(source);
      if (index >= 0) debrisVoices.splice(index, 1);
    };
  },

  dino(sound: 'step' | 'stomp' | 'crunch' | 'whoosh' | 'bonk' | 'boing' | 'whistle', gain = 1) {
    play(sound, 'dino', { gain });
    if (sound === 'stomp' || sound === 'bonk' || sound === 'crunch') duck();
  },

  roar(dino: DinoId) {
    play(`roar-${dino}`, 'dino');
    duck();
  },

  /** A rising hum while the smash button is held, so winding up can be heard. */
  charge(on: boolean) {
    const ctx = ensure();
    chargeHum?.stop();
    chargeHum = null;
    if (!on) return;
    const oscillator = ctx.createOscillator();
    const gain = ctx.createGain();
    oscillator.type = 'triangle';
    const now = ctx.currentTime;
    oscillator.frequency.setValueAtTime(140, now);
    oscillator.frequency.exponentialRampToValueAtTime(560, now + 1);
    gain.gain.setValueAtTime(0.0001, now);
    gain.gain.exponentialRampToValueAtTime(0.18, now + 0.25);
    gain.gain.setValueAtTime(0.18, now + 1);
    gain.gain.exponentialRampToValueAtTime(0.06, now + 2.5);
    oscillator.connect(gain).connect(channels.ui);
    oscillator.start(now);
    oscillator.stop(now + 6);
    chargeHum = oscillator;
  },

  ui(sound: 'click' | 'uibonk' | 'pop' | 'sparkle' | 'bell' | 'splash' | 'rebuild' | 'firework', options?: PlayOptions) {
    play(sound, 'ui', options);
  },

  /** How long a recorded line lasts, in seconds (a guess if it has not loaded). */
  lineSeconds(id: string) {
    return voices.get(id)?.duration ?? 1;
  },

  /** Say a recorded line. Returns false if that line has not been recorded. */
  voice(id: string) {
    const ctx = ensure();
    const buffer = voices.get(id);
    if (!buffer) return false;
    speaking?.stop();
    const source = ctx.createBufferSource();
    source.buffer = buffer;
    source.connect(channels.voice);
    source.start();
    speaking = source;
    source.onended = () => {
      if (speaking === source) speaking = null;
    };
    return true;
  },

  fanfare() {
    const ctx = ensure();
    if (buffers.has('fanfare')) {
      play('fanfare', 'ui', { gain: 1.2 });
      return;
    }
    [0, 4, 7, 12, 7, 12, 16].forEach((semitone, i) => {
      note(ctx, channels.ui, 523.25 * 2 ** (semitone / 12), ctx.currentTime + i * 0.13, i === 6 ? 0.6 : 0.12, 'square', 0.22);
    });
  },

  music: { start: startMusic, stop: stopMusic },

  /** For checking: how many copies of a recorded track are audible right now. */
  get audibleTracks() {
    return trackVoices.filter((voice) => voice.gain.gain.value > 0.02).length;
  },
};

// --- music -------------------------------------------------------------------------

/**
 * A toy marching band at 120 BPM, played live by a small sequencer. Two layers:
 * a base groove (bass, oom-pah and a xylophone tune), and a percussion layer
 * that fades up as the destruction builds and back down when things calm.
 */

const STEP = 60 / 120 / 4; // a sixteenth note
const MAJOR = [0, 2, 4, 5, 7, 9, 11];

interface Theme {
  root: number; // Hz
  melody: (number | null)[]; // scale degrees, 32 steps (two bars), null is a rest
  bass: number[]; // scale degrees per beat, 8 beats
}

const THEMES: Theme[] = [
  // Block Town: a bright march.
  { root: 261.63, melody: [0, null, 2, null, 4, null, 4, 4, 5, null, 4, null, 2, null, null, null, 4, null, 5, null, 7, null, 7, 7, 9, null, 7, null, 4, null, null, null], bass: [0, 4, 0, 4, 3, 4, 0, 4] },
  // Playground Park: bouncier, with more hops.
  { root: 293.66, melody: [4, null, null, 4, 2, null, 0, null, 2, null, 4, null, 7, null, null, null, 5, null, null, 5, 4, null, 2, null, 0, null, 2, null, 0, null, null, null], bass: [0, 2, 4, 2, 3, 5, 4, 2] },
  // Castle Hill: grander, a fanfare shape.
  { root: 220.0, melody: [0, null, 0, 0, 4, null, null, null, 4, null, 4, 4, 7, null, null, null, 9, null, 7, null, 5, null, 4, null, 2, null, 4, null, 0, null, null, null], bass: [0, 0, 4, 4, 5, 5, 4, 4] },
  // Sandbox: a looser loop.
  { root: 246.94, melody: [0, null, 4, null, 2, null, 5, null, 4, null, null, null, 2, null, 0, null, 7, null, 4, null, 5, null, 2, null, 4, null, null, null, 0, null, null, null], bass: [0, 4, 3, 4, 0, 4, 5, 4] },
];

let musicTimer = 0;
let musicTheme: Theme | null = null;
let nextStepAt = 0;
let stepIndex = 0;
let percussion: GainNode | null = null;

function note(ctx: AudioContext, out: AudioNode, frequency: number, at: number, seconds: number, type: OscillatorType, level: number) {
  const oscillator = ctx.createOscillator();
  const gain = ctx.createGain();
  oscillator.type = type;
  oscillator.frequency.value = frequency;
  gain.gain.setValueAtTime(0.0001, at);
  gain.gain.exponentialRampToValueAtTime(level, at + 0.008);
  gain.gain.exponentialRampToValueAtTime(0.0001, at + seconds);
  oscillator.connect(gain).connect(out);
  oscillator.start(at);
  oscillator.stop(at + seconds + 0.02);
}

const degree = (root: number, d: number) => root * 2 ** ((MAJOR[((d % 7) + 7) % 7] + 12 * Math.floor(d / 7)) / 12);

function hitDrum(ctx: AudioContext, name: string, at: number, level: number) {
  const set = buffers.get(name)!;
  const source = ctx.createBufferSource();
  source.buffer = set[Math.floor(Math.random() * set.length)];
  const gain = ctx.createGain();
  gain.gain.value = level;
  source.connect(gain).connect(percussion!);
  source.start(at);
}

function schedule() {
  if (!context || !musicTheme) return;
  const ctx = context;
  const theme = musicTheme;
  const dt = 0.05;
  chaos = Math.max(0, chaos - dt * 0.22);
  // The percussion layer follows how much is being smashed right now.
  percussion!.gain.setTargetAtTime(getState().settings.music ? chaos : 0, ctx.currentTime, 0.4);
  const base = getState().settings.music ? 1 : 0;

  while (nextStepAt < ctx.currentTime + 0.15) {
    const step = stepIndex % 32;
    const at = nextStepAt;
    if (base) {
      const melody = theme.melody[step];
      if (melody !== null) {
        // The "xylophone": a quick bright pluck.
        note(ctx, channels.music, degree(theme.root * 2, melody), at, 0.22, 'triangle', 0.5);
        note(ctx, channels.music, degree(theme.root * 4, melody), at, 0.08, 'sine', 0.2);
      }
      if (step % 4 === 0) note(ctx, channels.music, degree(theme.root / 2, theme.bass[step / 4]), at, 0.3, 'triangle', 0.7);
      if (step % 4 === 2) {
        // The "pah" of the oom-pah: a soft brass stab.
        const d = theme.bass[(step - 2) / 4];
        note(ctx, channels.music, degree(theme.root, d + 2), at, 0.12, 'square', 0.12);
        note(ctx, channels.music, degree(theme.root, d + 4), at, 0.12, 'square', 0.12);
      }
    }
    if (step % 8 === 4) hitDrum(ctx, 'snare', at, 0.9);
    if (step % 2 === 0) hitDrum(ctx, 'hat', at, 0.35);
    if (step % 32 >= 28) hitDrum(ctx, 'snare', at, 0.5); // a little roll into the next bar
    nextStepAt += STEP;
    stepIndex++;
  }
}

/** The recorded pieces, one per level plus the sandbox, in theme order. */
const TRACKS = ['block-town', 'playground-park', 'castle-hill', 'sandbox', 'farm', 'forest', 'hogwarts'];
const CROSSFADE = 1.6;
const tracks = new Map<string, AudioBuffer>();
let trackWanted: string | null = null;
let trackPlaying: string | null = null;
let trackBus: GainNode | null = null;
let trackFilter: BiquadFilterNode | null = null;
const trackVoices: { source: AudioBufferSourceNode; gain: GainNode }[] = [];
let trackLoop = 0;
let trackTick = 0;

/**
 * Play a recorded piece on a loop, crossfading into itself so the join is
 * never heard. The destruction still shapes it: when things are calm it is
 * soft and a little muffled, and it opens up and gets louder as he smashes.
 */
function playTrack(name: string) {
  const ctx = ensure();
  const buffer = tracks.get(name);
  if (!buffer || trackPlaying === name) return;
  window.clearInterval(musicTimer); // the built-in sequencer steps aside
  musicTheme = null;
  if (!trackBus) {
    trackBus = ctx.createGain();
    trackFilter = ctx.createBiquadFilter();
    trackFilter.type = 'lowpass';
    trackFilter.frequency.value = 2400;
    trackBus.connect(trackFilter).connect(channels.music);
  }
  trackPlaying = name;

  const turn = () => {
    if (trackPlaying !== name) return;
    const now = ctx.currentTime;
    // The copy that is ending fades out as the next one fades in.
    for (const voice of trackVoices) silence(voice, CROSSFADE);
    const source = ctx.createBufferSource();
    source.buffer = buffer;
    const gain = ctx.createGain();
    gain.gain.setValueAtTime(0, now);
    gain.gain.linearRampToValueAtTime(1, now + CROSSFADE);
    source.connect(gain).connect(trackBus!);
    source.start(now);
    source.stop(now + buffer.duration);
    const voice = { source, gain };
    trackVoices.push(voice);
    source.onended = () => {
      const index = trackVoices.indexOf(voice);
      if (index >= 0) trackVoices.splice(index, 1);
    };
    trackLoop = window.setTimeout(turn, (buffer.duration - CROSSFADE) * 1000);
  };
  window.clearTimeout(trackLoop);
  turn();

  window.clearInterval(trackTick);
  trackTick = window.setInterval(() => {
    chaos = Math.max(0, chaos - 0.1 * 0.22);
    const on = getState().settings.music ? 1 : 0;
    trackBus!.gain.setTargetAtTime(on * (1.3 + chaos * 0.9), ctx.currentTime, 0.3);
    trackFilter!.frequency.setTargetAtTime(2400 + chaos * 15000, ctx.currentTime, 0.3);
  }, 100);
}

/**
 * Fade one playing copy of a track to silence and stop it. Anything still scheduled on its
 * volume (such as the fade-in of a copy that only just started) is cancelled first:
 * otherwise that fade-in carries on and brings the old song back under the new one.
 */
function silence(voice: { source: AudioBufferSourceNode; gain: GainNode }, seconds: number) {
  if (!context) return;
  const now = context.currentTime;
  const level = voice.gain.gain;
  level.cancelScheduledValues(now);
  level.setValueAtTime(level.value, now);
  level.linearRampToValueAtTime(0, now + seconds);
  try {
    voice.source.stop(now + seconds + 0.05);
  } catch {
    // already stopped
  }
}

function stopTrack() {
  window.clearTimeout(trackLoop);
  window.clearInterval(trackTick);
  for (const voice of trackVoices) silence(voice, 0.4);
  trackPlaying = null;
}

function startMusic(theme: number) {
  const ctx = ensure();
  trackWanted = TRACKS[theme % TRACKS.length];
  if (trackPlaying && trackPlaying !== trackWanted) stopTrack();
  if (tracks.has(trackWanted)) {
    playTrack(trackWanted);
    return;
  }
  // No recording (yet): the built-in sequencer plays instead.
  if (!percussion) {
    percussion = ctx.createGain();
    percussion.gain.value = 0;
    percussion.connect(channels.music);
  }
  // Levels without a recording of their own borrow one of the built-in tunes.
  const next = THEMES[theme === 4 ? 1 : theme === 5 ? 3 : theme === 6 ? 2 : theme % THEMES.length];
  if (musicTheme === next) return;
  musicTheme = next;
  stepIndex = 0;
  nextStepAt = ctx.currentTime + 0.1;
  window.clearInterval(musicTimer);
  musicTimer = window.setInterval(schedule, 50);
}

function stopMusic() {
  trackWanted = null;
  stopTrack();
  window.clearInterval(musicTimer);
  musicTheme = null;
}

// While developing, saving this file swaps in a fresh copy of it. Shut this copy's sound down
// first, or its music carries on underneath the new copy's (two songs at once).
if (import.meta.hot) {
  import.meta.hot.dispose(() => {
    window.clearInterval(musicTimer);
    window.clearInterval(trackTick);
    window.clearTimeout(trackLoop);
    void context?.close();
  });
}
