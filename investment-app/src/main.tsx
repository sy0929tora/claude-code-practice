import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { HashRouter } from 'react-router-dom';
import './index.css';
import App from './App.tsx';
import { db, ensureDefaultGoal, ensureDefaultSettings } from './db/db';
import { requestPersistentStorage } from './lib/persist';
import { initTheme } from './lib/theme';

async function bootstrap() {
  initTheme();
  await db.open();
  await ensureDefaultSettings();
  await ensureDefaultGoal();
  void requestPersistentStorage();
}

bootstrap().finally(() => {
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <HashRouter>
        <App />
      </HashRouter>
    </StrictMode>,
  );
});
