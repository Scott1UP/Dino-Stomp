import { useFrame } from '@react-three/fiber';
import { useEffect, useRef } from 'react';
import { game } from '../game/state';

/**
 * The frame rate, for judging the graphics setting (the FPS switch in settings).
 * With `?debug` in the URL it also shows draw calls and moving bodies.
 */
export function DebugStats({ full }: { full: boolean }) {
  const element = useRef<HTMLDivElement | null>(null);
  const sample = useRef({ frames: 0, time: 0, worst: 0 });

  useEffect(() => {
    const div = document.createElement('div');
    div.className = 'debug-stats';
    document.body.appendChild(div);
    element.current = div;
    return () => div.remove();
  }, []);

  useFrame(({ gl }, delta) => {
    const s = sample.current;
    s.frames++;
    s.time += delta;
    s.worst = Math.max(s.worst, delta);
    if (s.time < 0.5 || !element.current) return;
    const fps = Math.round(s.frames / s.time);
    const low = Math.round(1 / s.worst);
    element.current.textContent = full
      ? `${fps} fps (low ${low}) · ${gl.info.render.calls} calls · ${game.town?.movingBodies ?? 0} moving`
      : `${fps} FPS`;
    s.frames = 0;
    s.time = 0;
    s.worst = 0;
  });

  return null;
}
