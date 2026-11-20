import { Canvas, useThree } from '@react-three/fiber';
import { Physics } from '@react-three/rapier';
import { Suspense, useEffect, useState } from 'react';
import { audio } from './audio/engine';
import { DebugStats } from './debug/DebugStats';
import { FollowCamera } from './game/camera/FollowCamera';
import { Sun } from './game/camera/Sun';
import { TapControls } from './game/controls/TapControls';
import { useKeyboard } from './game/controls/useKeyboard';
import { GRAPHICS } from './game/graphics';
import { game } from './game/state';
import { SANDBOX_THEME, levelDef } from './game/levels';
import { Ui } from './ui/Ui';
import { useStore } from './ui/store';
import { Level } from './world/buildings/Level';

const debug = new URLSearchParams(window.location.search).has('debug');

/** Applies the graphics setting to the renderer while the game runs. */
function Quality() {
  const quality = GRAPHICS[useStore((s) => s.settings.graphics)];
  const setDpr = useThree((state) => state.setDpr);
  useEffect(() => {
    setDpr(Math.min(window.devicePixelRatio, quality.dpr));
    game.effects = quality.effects;
    if (game.town) game.town.maxMoving = quality.maxMoving;
  }, [quality, setDpr]);
  return null;
}

export function App() {
  useKeyboard();
  const screen = useStore((s) => s.screen);
  const session = useStore((s) => s.session);
  const level = useStore((s) => s.level);
  const mode = useStore((s) => s.mode);
  const playing = screen === 'playing';
  const fps = useStore((s) => s.settings.fps);
  const [frozen, setFrozen] = useState(false);

  // Hit-stop: everything holds still for a moment on a big hit.
  useEffect(() => {
    let timer = 0;
    game.hitStop = (ms) => {
      setFrozen(true);
      window.clearTimeout(timer);
      timer = window.setTimeout(() => setFrozen(false), ms);
    };
    return () => window.clearTimeout(timer);
  }, []);
  const inLevel = playing || screen === 'paused' || screen === 'complete';

  // Audio can only start after the first tap, and by the time he is in a level he has tapped.
  useEffect(() => {
    if (inLevel) audio.music.start(mode === 'sandbox' ? SANDBOX_THEME : levelDef(level).theme);
  }, [inLevel, level, mode]);

  return (
    <div className="game" onPointerDown={() => audio.unlock()}>
      {/* Pixel density is capped (2 on high): a Retina iPad at full density renders four times the pixels. */}
      <Canvas shadows dpr={Math.min(window.devicePixelRatio, 2)} camera={{ fov: 38, near: 2, far: 900 }}>
        <color attach="background" args={['#BFE3F2']} />
        <fog attach="fog" args={['#BFE3F2', 260, 620]} />

        {/* One warm sun that casts shadows, plus a cool fill from the sky. */}
        <hemisphereLight args={['#BFE3F2', '#EADBB8', 1.15]} />
        <Sun />

        <Suspense fallback={null}>
          {/* The step stays fixed at 1/60 s: a varying step makes stacked pieces jitter. */}
          <Physics gravity={[0, -24, 0]} paused={!playing || frozen}>
            <Level key={`${level}-${session}`} />
          </Physics>
        </Suspense>

        <FollowCamera />
        <TapControls />
        <Quality />
        {(debug || fps) && <DebugStats full={debug} />}
      </Canvas>

      <Ui />
    </div>
  );
}
