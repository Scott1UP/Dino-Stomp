import { createRoot } from 'react-dom/client';
import '@fontsource/fredoka/500.css';
import '@fontsource/fredoka/600.css';
import '@fontsource/fredoka/700.css';
import { App } from './App';
import './styles.css';

// Safari ignores user-scalable=no, so pinch and double-tap zoom are blocked here too.
document.addEventListener('gesturestart', (event) => event.preventDefault());
document.addEventListener('dblclick', (event) => event.preventDefault());
document.addEventListener('contextmenu', (event) => event.preventDefault());

createRoot(document.getElementById('root')!).render(<App />);
