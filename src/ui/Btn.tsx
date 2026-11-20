import { createContext, useContext, useRef, type CSSProperties, type ReactNode } from 'react';
import { sounds, speak, type Line } from '../audio/ui';

/** True once he has been idle on a menu: the main button pulses harder. */
export const NudgeContext = createContext(false);

/** A finger that slid off slightly before lifting still counts. */
const FORGIVING = 28; // px

interface Props {
  /** The line spoken aloud when it is chosen, so nothing depends on reading. */
  line?: Line;
  onPress: () => void;
  children: ReactNode;
  className?: string;
  /** The one obvious action on the screen: it pulses. */
  main?: boolean;
  /** Locked things answer with a bonk and a wobble, never with nothing. */
  locked?: boolean;
  label?: string;
  style?: CSSProperties;
}

/**
 * Every button in the game. It squashes and clicks the moment a finger touches
 * it, and acts when the finger lifts.
 */
export function Btn({ line, onPress, children, className = 'btn', main, locked, label, style }: Props) {
  const held = useRef(false);
  const nudge = useContext(NudgeContext);

  return (
    <button
      className={`${className} ${main ? (nudge ? 'pulse-hard' : 'pulse') : ''} ${locked ? 'locked' : ''}`}
      style={style}
      aria-label={label}
      onPointerDown={(event) => {
        event.currentTarget.setPointerCapture(event.pointerId);
        held.current = true;
        event.currentTarget.classList.add('down');
        sounds.click();
      }}
      onPointerUp={(event) => {
        const button = event.currentTarget;
        button.classList.remove('down');
        if (!held.current) return;
        held.current = false;
        const r = button.getBoundingClientRect();
        const inside =
          event.clientX >= r.left - FORGIVING &&
          event.clientX <= r.right + FORGIVING &&
          event.clientY >= r.top - FORGIVING &&
          event.clientY <= r.bottom + FORGIVING;
        if (!inside) return;
        if (locked) {
          sounds.bonk();
          speak('locked');
          button.classList.remove('wobble');
          void button.offsetWidth; // restart the animation
          button.classList.add('wobble');
          return;
        }
        if (line) speak(line);
        onPress();
      }}
      onPointerCancel={(event) => {
        held.current = false;
        event.currentTarget.classList.remove('down');
      }}
    >
      {children}
    </button>
  );
}
