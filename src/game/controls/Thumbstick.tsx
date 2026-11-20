import { useRef } from 'react';
import { input } from '../state';

const REACH = 60; // px the knob travels for full speed

/**
 * The movement thumbstick. It always sits in the bottom-left corner so he can
 * see where to put his thumb. If his thumb lands somewhere else in that area,
 * the stick jumps there to meet it (small children don't hit a fixed stick
 * accurately), and slides back home when he lets go.
 */
export function Thumbstick() {
  const zone = useRef<HTMLDivElement>(null);
  const base = useRef<HTMLDivElement>(null);
  const knob = useRef<HTMLDivElement>(null);
  const touch = useRef<{ id: number; x: number; y: number } | null>(null);

  const release = () => {
    touch.current = null;
    input.stick.active = false;
    input.stick.x = 0;
    input.stick.y = 0;
    if (base.current && knob.current) {
      base.current.classList.remove('held');
      base.current.style.transform = '';
      knob.current.style.transform = '';
    }
  };

  return (
    <div
      ref={zone}
      className="stick-zone"
      onPointerDown={(event) => {
        if (touch.current) return;
        event.currentTarget.setPointerCapture(event.pointerId);
        const rect = event.currentTarget.getBoundingClientRect();
        touch.current = { id: event.pointerId, x: event.clientX, y: event.clientY };
        input.stick.active = true;
        if (base.current && knob.current) {
          // Move from its home spot to wherever the thumb landed.
          const home = base.current.offsetParent ? { x: base.current.offsetLeft, y: base.current.offsetTop } : { x: 0, y: 0 };
          const half = base.current.offsetWidth / 2;
          base.current.classList.add('held');
          base.current.style.transform = `translate(${event.clientX - rect.left - home.x - half}px, ${event.clientY - rect.top - home.y - half}px)`;
          knob.current.style.transform = 'translate(0px, 0px)';
        }
      }}
      onPointerMove={(event) => {
        const t = touch.current;
        if (!t || t.id !== event.pointerId) return;
        let dx = event.clientX - t.x;
        let dy = event.clientY - t.y;
        const length = Math.hypot(dx, dy);
        if (length > REACH) {
          dx = (dx / length) * REACH;
          dy = (dy / length) * REACH;
        }
        input.stick.x = dx / REACH;
        input.stick.y = -dy / REACH;
        if (knob.current) knob.current.style.transform = `translate(${dx}px, ${dy}px)`;
      }}
      onPointerUp={(event) => touch.current?.id === event.pointerId && release()}
      onPointerCancel={(event) => touch.current?.id === event.pointerId && release()}
    >
      <div ref={base} className="stick-base">
        <div ref={knob} className="stick-knob" />
      </div>
    </div>
  );
}
