import { MantineProvider, localStorageColorSchemeManager, useMantineColorScheme } from '@mantine/core';
import type { MantineColorSchemeManager } from '@mantine/core';
import { useEffect, useLayoutEffect, useState } from 'react';
import type { ReactNode } from 'react';
import { AppearanceContext, CYRNAVA_THEME_KEY, useCyrnavaTheme } from './appearanceContext';
import { cyrnavaMantineTheme, cyrnavaVariables } from './cyrnavaTheme';

// Mantine calls System "auto". Retain the legacy key through the CyrNava rename.
// Keep the key/allowed values in sync with public/assets/appearance-init.js.
export const APPEARANCE_KEY = 'engage.appearance.v1';
const baseManager = localStorageColorSchemeManager({ key: APPEARANCE_KEY });
function storedCyrnava() {
  try { return localStorage.getItem(CYRNAVA_THEME_KEY) === 'cyrnava'; } catch { return false; }
}
let unsubscribeBrand = () => {};
// Mantine still owns light/dark/auto resolution. The skin resolves to dark while
// leaving the previous standard preference untouched in its existing key.
const manager: MantineColorSchemeManager = {
  ...baseManager,
  get: (fallback) => storedCyrnava() ? 'dark' : baseManager.get(fallback),
  set: (value) => { if (!storedCyrnava()) baseManager.set(value); },
  subscribe: (notify) => {
    baseManager.subscribe((value) => notify(storedCyrnava() ? 'dark' : value));
    const sync = (event: StorageEvent) => {
      if (event.key === CYRNAVA_THEME_KEY || event.key === null) notify(manager.get('auto'));
    };
    window.addEventListener('storage', sync);
    unsubscribeBrand = () => window.removeEventListener('storage', sync);
  },
  unsubscribe: () => { baseManager.unsubscribe(); unsubscribeBrand(); },
};

export function AppearanceProvider({ children }: { children: ReactNode }) {
  const [cyrnava, setActive] = useState(() => {
    return storedCyrnava();
  });
  function setCyrnava(value: boolean) {
    setActive(value);
    try {
      if (value) localStorage.setItem(CYRNAVA_THEME_KEY, 'cyrnava');
      else localStorage.removeItem(CYRNAVA_THEME_KEY);
    } catch { console.warn('Appearance preference could not be saved in this browser.'); }
  }
  useEffect(() => {
    const sync = (event: StorageEvent) => {
      if (event.key === CYRNAVA_THEME_KEY || event.key === null) setActive(event.key !== null && event.newValue === 'cyrnava');
    };
    window.addEventListener('storage', sync);
    return () => window.removeEventListener('storage', sync);
  }, []);
  useLayoutEffect(() => {
    document.documentElement.setAttribute('data-cyrnava-theme', String(cyrnava));
    return () => document.documentElement.removeAttribute('data-cyrnava-theme');
  }, [cyrnava]);
  return <AppearanceContext.Provider value={{ cyrnava, setCyrnava }}>
    <MantineProvider defaultColorScheme="auto" colorSchemeManager={manager}
      theme={cyrnava ? cyrnavaMantineTheme : undefined} cssVariablesResolver={cyrnava ? cyrnavaVariables : undefined} withCssVariables={cyrnava}>
      {children}
    </MantineProvider>
  </AppearanceContext.Provider>;
}

export function AppearanceControl() {
  const { colorScheme, setColorScheme } = useMantineColorScheme();
  const { cyrnava, setCyrnava } = useCyrnavaTheme();
  return <label className="appearance-control">
    Appearance
    <select value={cyrnava ? 'cyrnava' : colorScheme} onChange={(event) => {
      const value = event.target.value;
      if (value === 'cyrnava') { setCyrnava(true); setColorScheme('dark'); }
      else if (value === 'light' || value === 'dark' || value === 'auto') { setCyrnava(false); setColorScheme(value); }
    }}>
      <option value="light">Light</option>
      <option value="dark">Dark</option>
      <option value="auto">System</option>
      <option value="cyrnava">CyrNava</option>
    </select>
  </label>;
}
