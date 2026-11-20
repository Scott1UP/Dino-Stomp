import { useRef } from 'react';
import { input } from '../state';

const REACH = 60; // px the knob travels for full speed

/**
 * The movement thumbstick. It stays fixed in the bottom-left corner: only a
 * touch on it (or just round it) moves the dino, so taps anywhere else on the
 * left of the screen still reach the town, to walk or attack.
 */
export function Thumbstick() {
  const knob = useRef<HTMLDivElement>(null);
  const touch = useRef<{ id: number; x: number; y: number } | null>(null);

  const release = () => {
    touch.current = null;
    input.stick.active = false;
    input.stick.x = 0;
    input.stick.y = 0;
    if (knob.current) knob.current.style.transform = '';
  };

  const steer = (clientX: number, clientY: number) => {
    const t = touch.current;
    if (!t) return;
    let dx = clientX - t.x;
    let dy = clientY - t.y;
    const length = Math.hypot(dx, dy);
    if (length > REACH) {
      dx = (dx / length) * REACH;
      dy = (dy / length) * REACH;
    }
    input.stick.x = dx / REACH;
    input.stick.y = -dy / REACH;
    if (knob.current) knob.current.style.transform = `translate(${dx}px, ${dy}px)`;
  };

  return (
    <div
      className="stick-zone"
      onPointerDown={(event) => {
        if (touch.current) return;
        event.currentTarget.setPointerCapture(event.pointerId);
        // Steer from the middle of the stick, so a thumb landing off-centre already pushes that way.
        const rect = event.currentTarget.getBoundingClientRect();
        touch.current = { id: event.pointerId, x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 };
        input.stick.active = true;
        steer(event.clientX, event.clientY);
      }}
      onPointerMove={(event) => touch.current?.id === event.pointerId && steer(event.clientX, event.clientY)}
      onPointerUp={(event) => touch.current?.id === event.pointerId && release()}
      onPointerCancel={(event) => touch.current?.id === event.pointerId && release()}
    >
      <div className="stick-base">
        <div ref={knob} className="stick-knob" />
      </div>
    </div>
  );
}
