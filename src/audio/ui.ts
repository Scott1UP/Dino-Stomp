import type { DinoId } from '../types';
import { getState } from '../ui/store';
import { audio } from './engine';
import lines from './lines.json';

export type Line = keyof typeof lines;

/** Interface sounds. */
export const sounds = {
  /** The moment a finger touches a button. */
  click: () => audio.ui('click'),
  /** Locked or unavailable: a gentle answer, never silence. */
  bonk: () => audio.ui('uibonk'),
  pop: () => audio.ui('pop'),
  fanfare: () => audio.fanfare(),
  roar: (dino: DinoId) => audio.roar(dino),
};

/**
 * Say a line aloud: a button's name, a prompt, a cheer. The recorded clip
 * plays if there is one; otherwise the browser's own voice reads it.
 */
export function speak(line: Line) {
  if (audio.voice(line)) return;
  if (!('speechSynthesis' in window)) return;
  speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(lines[line]);
  utterance.volume = getState().settings.volume;
  utterance.rate = 0.95;
  utterance.pitch = 1.25;
  speechSynthesis.speak(utterance);
}
