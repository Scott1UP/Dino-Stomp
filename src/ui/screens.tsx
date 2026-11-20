import {
  ArrowLeft,
  ArrowRight,
  BookOpen,
  Blocks,
  Footprints,
  Gauge,
  Home,
  Lock,
  Music,
  Pause as PauseIcon,
  Play,
  Pointer,
  Repeat,
  Settings,
  Sparkles,
  Star,
  Vibrate,
  Volume2,
} from 'lucide-react';
import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react';
import { audio } from '../audio/engine';
import { sounds, speak, type Line } from '../audio/ui';
import { DINOS, LEVELS, dinoDef, levelDef } from '../game/levels';
import { STICKERS, stickerDef } from '../game/stickers';
import type { DinoId } from '../types';
import { Btn } from './Btn';
import { Screen } from './Screen';
import { actions, allSecrets, useStore, type Graphics } from './store';

const sticker = (id: DinoId) => `/ui/sticker-${id}.webp`;

/** The pause between the announcer finishing a dino's name and the dino roaring. */
const ROAR_GAP_MS = 250;

const GRAPHICS_ORDER: Graphics[] = ['high', 'medium', 'low'];
const GRAPHICS_NAME: Record<Graphics, string> = { high: 'High', medium: 'Medium', low: 'Low' };

/** Back is always top-left. */
function Back({ onPress }: { onPress: () => void }) {
  return (
    <Btn label="Back" onPress={onPress} className="btn btn-square corner-back">
      <ArrowLeft />
    </Btn>
  );
}

export function Title() {
  const stickers = useStore((s) => s.stickers);
  return (
    <Screen prompt="prompt-title" maxPrompts={3} className="screen title">
      <img className="logo" src="/ui/logo.webp" alt="Dino Stomp" draggable={false} />
      <div className="row">
        <Btn main className="btn btn-go btn-huge" onPress={() => actions.chooseMode('story')}>
          <Play className="solid" />
          Play
        </Btn>
        <Btn className="btn btn-alt btn-big" onPress={() => actions.chooseMode('sandbox')}>
          <Blocks />
          Sandbox
        </Btn>
      </div>
      <div className="row title-extras">
        <Btn line="stickers-open" className="btn btn-plain" onPress={actions.openStickers}>
          <BookOpen />
          Stickers
          <span className="count">
            {Object.keys(stickers).length}/{STICKERS.length}
          </span>
        </Btn>
        <Btn className="btn" onPress={actions.openParent}>
          <Settings />
          Settings
        </Btn>
      </div>
    </Screen>
  );
}

export function DinoSelect() {
  const last = useStore((s) => s.dino);
  const swapping = useStore((s) => s.swapping);
  const [selected, setSelected] = useState<DinoId | null>(null);
  const [going, setGoing] = useState(false);

  // As in Dino Kart: the first tap picks a dino (it roars and lights up, the others hold
  // still), and a second tap on it, or the Go button, carries on.
  const confirm = (id: DinoId) => {
    if (going) return;
    setGoing(true);
    window.setTimeout(() => actions.chooseDino(id), 350);
  };
  // The announcer says the dino's name first; it roars once the name has been said.
  const roar = useRef(0);
  useEffect(() => () => window.clearTimeout(roar.current), []);
  const tap = (id: DinoId) => {
    if (selected === id) return confirm(id);
    setSelected(id);
    window.clearTimeout(roar.current);
    roar.current = window.setTimeout(() => sounds.roar(id), audio.lineSeconds(id) * 1000 + ROAR_GAP_MS);
  };

  return (
    <Screen prompt={selected ? 'prompt-dino-go' : 'prompt-dino'} className="overlay">
      <div className="panel wide">
        <Back onPress={actions.back} />
        <h1 className="heading small">Pick a dino</h1>
        <div className="pick-row">
          {DINOS.map((dino, index) => (
            <Btn
              key={dino.id}
              line={selected === dino.id ? undefined : dino.id}
              main={!selected && dino.id === last}
              className={`pick ${selected === dino.id ? 'selected' : selected ? 'dim' : ''}`}
              style={{ '--face': dino.colour, '--edge': dino.dark, animationDelay: `${index * 70}ms` } as CSSProperties}
              onPress={() => tap(dino.id)}
            >
              <img src={sticker(dino.id)} alt="" draggable={false} />
              <span className="pick-name">{dino.name}</span>
            </Btn>
          ))}
        </div>
        {/* Go is always on the right, and looks switched off until a dino is picked. */}
        <Btn
          line={selected ? 'go-dino' : undefined}
          main={!!selected}
          locked={!selected}
          className={`btn btn-go btn-big pick-go ${selected ? '' : 'inactive'}`}
          onPress={() => selected && confirm(selected)}
        >
          {swapping ? 'Swap' : 'Go'}
          <ArrowRight />
        </Btn>
      </div>
    </Screen>
  );
}

export function LevelSelect() {
  const mode = useStore((s) => s.mode);
  const unlocked = useStore((s) => s.unlocked);
  const completed = useStore((s) => s.completed);
  const last = useStore((s) => s.level);
  const opened = useStore((s) => allSecrets(s.secrets));

  // The one to pulse: the first level he hasn't finished, or the last one he played in sandbox.
  const next =
    mode === 'sandbox' ? last : (LEVELS.find((l, i) => !l.secret && i < unlocked && !completed[l.id]) ?? LEVELS[Math.min(unlocked, LEVELS.length) - 1]).id;

  return (
    <Screen prompt="prompt-level" className="overlay">
      <div className="panel levels">
        <Back onPress={actions.back} />
        <h1 className="heading small">{mode === 'sandbox' ? 'Sandbox' : 'Where to?'}</h1>
        <div className="level-row">
          {LEVELS.map((level, index) => {
            if (level.secret && !opened) return null;
            const locked = !level.secret && mode === 'story' && index >= unlocked;
            return (
              <Btn
                key={level.id}
                line={level.id}
                locked={locked}
                main={level.id === next}
                className="level-card"
                style={{ backgroundImage: `url(${level.card})`, animationDelay: `${index * 70}ms` }}
                onPress={() => actions.chooseLevel(level.id)}
              >
                {locked && (
                  <span className="level-lock">
                    <Lock />
                  </span>
                )}
                {mode === 'story' && completed[level.id] && (
                  <span className="level-star">
                    <Star className="solid" />
                  </span>
                )}
                <span className="level-name">{level.name}</span>
              </Btn>
            );
          })}
        </div>
      </div>
    </Screen>
  );
}

/** One objective: a picture of what to smash, and how far along he is. */
function Goal({ index }: { index: 0 | 1 }) {
  const count = useStore((s) => s.progress[s.level][index]);
  const objective = levelDef(useStore((s) => s.level)).objectives[index];
  const done = count >= objective.required;
  const bump = useRef<HTMLDivElement>(null);

  // A little jump each time the count goes up.
  useEffect(() => {
    if (!count || !bump.current) return;
    bump.current.classList.remove('bump');
    void bump.current.offsetWidth;
    bump.current.classList.add('bump');
  }, [count]);

  return (
    <div ref={bump} className={`goal ${done ? 'done' : ''}`}>
      <img src={objective.icon} alt="" draggable={false} />
      {objective.required <= 6 ? (
        <span className="pips">
          {Array.from({ length: objective.required }, (_, i) => (
            <Star key={i} className={i < count ? 'solid on' : 'solid'} />
          ))}
        </span>
      ) : (
        <span className="meter">
          <i style={{ width: `${(count / objective.required) * 100}%` }} />
          <b>
            {count}/{objective.required}
          </b>
        </span>
      )}
    </div>
  );
}

/** In a level, only the controls, pause and the two progress displays are on screen. */
export function Hud({ playing }: { playing: boolean }) {
  const story = useStore((s) => s.mode === 'story');
  const level = useStore((s) => s.level);
  const session = useStore((s) => s.session);
  const foundSecret = useStore((s) => !!s.secrets[s.level]);
  const finished = useStore((s) => s.celebrated);

  // A voice says what to smash as the level begins; there is no intro to sit through.
  useEffect(() => {
    if (!story) return;
    const timer = window.setTimeout(() => speak(`goal-${level}` as Line), 700);
    return () => window.clearTimeout(timer);
  }, [story, level, session]);

  return (
    <>
      {story && (
        <div className="goals">
          <Goal index={0} />
          <Goal index={1} />
          {/* Once he has found this level's golden dino, it sits proudly next to the objectives. */}
          {foundSecret && (
            <div className="goal golden" aria-label="Golden dino found">
              <img src="/ui/sticker-secret.webp" alt="" draggable={false} />
            </div>
          )}
        </div>
      )}
      {playing && (
        <>
          <Btn label="Pause" onPress={actions.pause} className="orb orb-pause">
            <PauseIcon className="solid" />
          </Btn>
          {/* After "keep stomping", a way on to the next level whenever he is ready. */}
          {story && finished && (
            <Btn line="next" label="Next level" onPress={actions.nextLevel} className="btn btn-go hud-next">
              Next
              <ArrowRight />
            </Btn>
          )}
          <IdleHand />
        </>
      )}
    </>
  );
}

/** After 10 seconds without input in a level, a hand shows him the thumbstick. */
function IdleHand() {
  const [show, setShow] = useState(false);
  useEffect(() => {
    let timer: number;
    const arm = () => {
      setShow(false);
      window.clearTimeout(timer);
      timer = window.setTimeout(() => setShow(true), 10000);
    };
    arm();
    window.addEventListener('pointerdown', arm);
    window.addEventListener('keydown', arm);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener('pointerdown', arm);
      window.removeEventListener('keydown', arm);
    };
  }, []);
  return show ? (
    <div className="idle-hand">
      <span className="idle-ring" />
      <Pointer />
    </div>
  ) : null;
}

export function Pause() {
  const sandbox = useStore((s) => s.mode === 'sandbox');
  const finished = useStore((s) => s.mode === 'story' && s.celebrated);
  const dino = dinoDef(useStore((s) => s.dino));
  return (
    <Screen prompt="prompt-pause" className="overlay">
      <div className="panel menu">
        <h1 className="heading small">Paused</h1>
        {/* Resume is the biggest thing here, so pausing by accident costs nothing. */}
        <Btn line="go" main className="btn btn-go btn-tall" onPress={actions.resume}>
          <Play className="solid" />
          Go!
        </Btn>
        <Btn line="swap" className="btn btn-plain" onPress={actions.swapDino}>
          <Repeat />
          Swap dino
          <img className="btn-sticker" src={sticker(dino.id)} alt="" draggable={false} />
        </Btn>
        {sandbox && (
          <Btn line="rebuild" className="btn btn-alt" onPress={actions.rebuild}>
            <Blocks />
            Rebuild
          </Btn>
        )}
        {finished && (
          <Btn line="next" className="btn btn-go" onPress={actions.nextLevel}>
            Next level
            <ArrowRight />
          </Btn>
        )}
        <Btn line="stickers-open" className="btn btn-plain" onPress={actions.openStickers}>
          <BookOpen />
          Stickers
        </Btn>
        <Btn className="btn" onPress={actions.openParent}>
          <Settings />
          Settings
        </Btn>
        <Btn className="btn" onPress={actions.home}>
          <Home />
          Home
        </Btn>
      </div>
    </Screen>
  );
}

export function Complete() {
  const dino = dinoDef(useStore((s) => s.dino));
  const level = useStore((s) => s.level);
  const story = LEVELS.filter((l) => !l.secret);
  const last = story[story.length - 1].id === level || levelDef(level).secret;
  const played = useRef(false);

  useEffect(() => {
    if (played.current) return;
    played.current = true;
    sounds.fanfare();
    window.setTimeout(() => sounds.roar(dino.id), 900);
  }, [dino]);

  const bits = useMemo(
    () =>
      Array.from({ length: 56 }, (_, i) => ({
        left: `${(i * 37) % 100}%`,
        animationDelay: `${((i * 53) % 20) / 10}s`,
        animationDuration: `${2.2 + ((i * 29) % 14) / 10}s`,
        background: ['#f4543a', '#ffc21f', '#3bb4f6', '#6fd03c', '#ff7eb6'][i % 5],
      })),
    [],
  );

  return (
    <Screen prompt="prompt-complete" className="screen sunny complete">
      <div className="confetti" aria-hidden="true">
        {bits.map((style, i) => (
          <i key={i} style={style} />
        ))}
      </div>
      <h1 className="heading">You did it!</h1>
      <div className="stars">
        {[0, 1, 2].map((i) => (
          <Star key={i} className="solid" style={{ animationDelay: `${0.25 + i * 0.18}s` }} />
        ))}
      </div>
      <img className="hero" src={sticker(dino.id)} alt="" draggable={false} />
      <div className="row">
        <Btn line="stickers-open" label="Stickers" className="btn btn-alt btn-square complete-stickers" onPress={actions.openStickers}>
          <BookOpen />
        </Btn>
        <Btn line="go" className="btn btn-plain" onPress={actions.keepStomping}>
          <Footprints />
          Keep stomping
        </Btn>
        {/* Go is always on the right. */}
        <Btn line="next" main className="btn btn-go btn-huge" onPress={actions.nextLevel}>
          {last ? 'Play again' : 'Next'}
          <ArrowRight />
        </Btn>
      </div>
    </Screen>
  );
}

/** For the grown-up: an ordinary settings panel. */
export function Parent() {
  const settings = useStore((s) => s.settings);
  const [confirming, setConfirming] = useState(false);
  return (
    <div className="overlay">
      <div className="panel settings">
        <h1 className="heading small">Settings</h1>
        <label className="setting">
          <Volume2 />
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={settings.volume}
            aria-label="Volume"
            onChange={(event) => actions.setSetting('volume', Number(event.target.value))}
          />
        </label>
        <div className="row">
          <button className={`btn btn-plain ${settings.music ? '' : 'off'}`} onClick={() => actions.setSetting('music', !settings.music)}>
            <Music />
            Music {settings.music ? 'on' : 'off'}
          </button>
          <button className={`btn btn-plain ${settings.shake ? '' : 'off'}`} onClick={() => actions.setSetting('shake', !settings.shake)}>
            <Vibrate />
            Shake {settings.shake ? 'on' : 'off'}
          </button>
        </div>
        <div className="row">
          {/* Each press moves on to the next of high, medium and low. */}
          <button
            className="btn btn-plain"
            onClick={() => actions.setSetting('graphics', GRAPHICS_ORDER[(GRAPHICS_ORDER.indexOf(settings.graphics) + 1) % GRAPHICS_ORDER.length])}
          >
            <Sparkles />
            Graphics: {GRAPHICS_NAME[settings.graphics]}
          </button>
          <button className={`btn btn-plain ${settings.fps ? '' : 'off'}`} onClick={() => actions.setSetting('fps', !settings.fps)}>
            <Gauge />
            FPS {settings.fps ? 'on' : 'off'}
          </button>
        </div>
        <div className="row">
          {confirming ? (
            <>
              <button
                className="btn btn-red"
                onClick={() => {
                  actions.resetProgress();
                  setConfirming(false);
                }}
              >
                Yes, reset
              </button>
              <button className="btn" onClick={() => setConfirming(false)}>
                Cancel
              </button>
            </>
          ) : (
            <button className="btn" onClick={() => setConfirming(true)}>
              Reset progress
            </button>
          )}
          <button className="btn btn-go" onClick={actions.closeParent}>
            Done
          </button>
        </div>
      </div>
    </div>
  );
}

/** The sticker book: everything he has earned, and grey shapes of what is still to find. */
export function StickerBook() {
  const earned = useStore((s) => s.stickers);
  const [wiggle, setWiggle] = useState<string | null>(null);
  return (
    <Screen className="overlay">
      <div className="panel book">
        <Back onPress={actions.closeStickers} />
        <Btn label="Home" onPress={actions.home} className="btn btn-square corner-home">
          <Home />
        </Btn>
        <h1 className="heading small">My stickers</h1>
        <div className="sticker-grid">
          {STICKERS.map((sticker, index) => {
            const got = !!earned[sticker.id];
            return (
              <Btn
                key={sticker.id}
                line={(got ? `sticker-${sticker.id}` : `hint-${sticker.id}`) as Line}
                className={`sticker-slot ${got ? 'got' : 'missing'} ${sticker.round ? 'round' : ''} ${wiggle === sticker.id ? 'wiggle' : ''}`}
                style={{ animationDelay: `${index * 35}ms` }}
                onPress={() => {
                  setWiggle(null);
                  window.requestAnimationFrame(() => setWiggle(sticker.id));
                }}
              >
                <img src={sticker.art} alt="" draggable={false} />
              </Btn>
            );
          })}
        </div>
      </div>
    </Screen>
  );
}

/** A sticker just earned: it pops up big in the middle, then flies off to the book. */
export function StickerToast() {
  const id = useStore((s) => s.toast);
  useEffect(() => {
    if (!id) return;
    const timer = window.setTimeout(() => {
      sounds.pop();
      speak('new-sticker');
    }, 150);
    return () => window.clearTimeout(timer);
  }, [id]);
  const sticker = id ? stickerDef(id) : null;
  if (!sticker) return null;
  return (
    <div key={sticker.id} className="sticker-toast" aria-hidden="true">
      <span className={`sticker-toast-art ${sticker.round ? 'round' : ''}`}>
        <img src={sticker.art} alt="" draggable={false} />
      </span>
      <span className="sticker-toast-label">New sticker!</span>
    </div>
  );
}
