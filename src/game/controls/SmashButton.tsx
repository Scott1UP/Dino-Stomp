import { useEffect, useRef } from 'react';
import { audio } from '../../audio/engine';
import { CHARGE_BONUS, CHARGE_SECONDS } from '../dinos/stats';
import { beginCharge, chargeLevel, input, releaseCharge } from '../state';

/**
 * The signature move: the big red button, bottom-right. A tap fires it at
 * once; holding it winds the move up, and a ring fills round the button. After
 * a second it is fully charged, and hits harder.
 */
export function SmashButton() {
  const button = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    let frame = 0;
    let wasFull = false;
    const tick = () => {
      const level = chargeLevel(CHARGE_SECONDS);
      const element = button.current;
      if (element) {
        element.style.setProperty('--charge', String(level));
        element.classList.toggle('charging', input.charging);
        element.classList.toggle('full', level >= 1);
      }
      if (level >= 1 && !wasFull) audio.ui('sparkle');
      wasFull = level >= 1;
      frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, []);

  const release = () => {
    button.current?.classList.remove('down');
    audio.charge(false);
    releaseCharge(CHARGE_SECONDS, CHARGE_BONUS);
  };

  return (
    <button
      ref={button}
      className="orb orb-smash"
      aria-label="Smash"
      onPointerDown={(event) => {
        event.currentTarget.setPointerCapture(event.pointerId);
        event.currentTarget.classList.add('down');
        audio.charge(true);
        beginCharge();
      }}
      onPointerUp={release}
      onPointerCancel={release}
    >
      <img src="/ui/smash.webp" alt="" draggable={false} />
    </button>
  );
}
