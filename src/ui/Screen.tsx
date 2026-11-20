import { useEffect, useState, type ReactNode } from 'react';
import { speak, type Line } from '../audio/ui';
import { NudgeContext } from './Btn';

/** Wait this long without a tap before the voice helps... */
const IDLE_MS = 8000;
/** ...and this long before it says it again. */
const REPEAT_MS = 13000;

/**
 * A menu screen. If he does nothing for 8 seconds, the main button pulses
 * harder and a voice says what to do, so he never has to ask.
 */
export function Screen({
  prompt,
  maxPrompts = Infinity,
  className = '',
  children,
}: {
  prompt?: Line;
  /** Say the prompt at most this many times while the screen is open. */
  maxPrompts?: number;
  className?: string;
  children: ReactNode;
}) {
  const [nudge, setNudge] = useState(false);

  useEffect(() => {
    let timer: number;
    let said = 0;
    const arm = (delay: number) => {
      window.clearTimeout(timer);
      timer = window.setTimeout(() => {
        setNudge(true);
        if (prompt && said < maxPrompts) {
          speak(prompt);
          said++;
        }
        arm(REPEAT_MS);
      }, delay);
    };
    const onInput = () => {
      setNudge(false);
      arm(IDLE_MS);
    };
    arm(IDLE_MS);
    window.addEventListener('pointerdown', onInput);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener('pointerdown', onInput);
    };
  }, [prompt, maxPrompts]);

  return (
    <NudgeContext.Provider value={nudge}>
      <div className={className}>{children}</div>
    </NudgeContext.Provider>
  );
}
