import { useEffect } from 'react';
import { getState } from '../../ui/store';
import { CHARGE_BONUS, CHARGE_SECONDS } from '../dinos/stats';
import { beginCharge, input, releaseCharge } from '../state';

const AXES: Record<string, [number, number]> = {
  KeyW: [0, 1],
  ArrowUp: [0, 1],
  KeyS: [0, -1],
  ArrowDown: [0, -1],
  KeyA: [-1, 0],
  ArrowLeft: [-1, 0],
  KeyD: [1, 0],
  ArrowRight: [1, 0],
};

/** WASD or arrow keys to move and Space to smash, for testing on a computer. */
export function useKeyboard() {
  useEffect(() => {
    const held = new Set<string>();

    const update = () => {
      let x = 0;
      let y = 0;
      for (const code of held) {
        x += AXES[code][0];
        y += AXES[code][1];
      }
      input.keys.x = Math.sign(x);
      input.keys.y = Math.sign(y);
    };

    const onDown = (event: KeyboardEvent) => {
      if (event.code === 'Space') {
        if (!event.repeat && getState().screen === 'playing') beginCharge();
        event.preventDefault();
      } else if (event.code in AXES) {
        held.add(event.code);
        update();
        event.preventDefault();
      }
    };
    const onUp = (event: KeyboardEvent) => {
      if (event.code === 'Space') releaseCharge(CHARGE_SECONDS, CHARGE_BONUS);
      if (held.delete(event.code)) update();
    };
    const onBlur = () => {
      held.clear();
      update();
    };

    window.addEventListener('keydown', onDown);
    window.addEventListener('keyup', onUp);
    window.addEventListener('blur', onBlur);
    return () => {
      window.removeEventListener('keydown', onDown);
      window.removeEventListener('keyup', onUp);
      window.removeEventListener('blur', onBlur);
    };
  }, []);
}
