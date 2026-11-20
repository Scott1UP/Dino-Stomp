import { RotateCw } from 'lucide-react';
import { SmashButton } from '../game/controls/SmashButton';
import { Thumbstick } from '../game/controls/Thumbstick';
import { Complete, DinoSelect, Hud, LevelSelect, Parent, Pause, Title } from './screens';
import { useStore } from './store';
import './ui.css';

/** The whole interface: an HTML layer over the 3D canvas, in the same chunky look as Dino Safari. */
export function Ui() {
  const screen = useStore((s) => s.screen);
  const inLevel = screen === 'playing' || screen === 'paused' || screen === 'complete';

  return (
    <div className="ui">
      {inLevel && <Hud playing={screen === 'playing'} />}
      {screen === 'playing' && (
        <>
          <Thumbstick />
          <SmashButton />
        </>
      )}

      {screen === 'title' && <Title />}
      {screen === 'dinoSelect' && <DinoSelect />}
      {screen === 'levelSelect' && <LevelSelect />}
      {screen === 'paused' && <Pause />}
      {screen === 'complete' && <Complete />}
      {screen === 'parent' && <Parent />}

      {/* Landscape only. Held upright, it asks for a turn. */}
      <div className="rotate-me">
        <RotateCw />
        <p>Turn sideways to play</p>
      </div>
    </div>
  );
}
