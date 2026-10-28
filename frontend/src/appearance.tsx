import { MantineProvider, localStorageColorSchemeManager, useMantineColorScheme } from '@mantine/core';
import type { ReactNode } from 'react';

// Mantine calls System "auto". Retain the legacy key through the CyrNava rename.
// Keep the key/allowed values in sync with public/assets/appearance-init.js.
export const APPEARANCE_KEY = 'engage.appearance.v1';
const manager = localStorageColorSchemeManager({ key: APPEARANCE_KEY });

export function AppearanceProvider({ children }: { children: ReactNode }) {
  return <MantineProvider defaultColorScheme="auto" colorSchemeManager={manager} withCssVariables={false}>
    {children}
  </MantineProvider>;
}

export function AppearanceControl() {
  const { colorScheme, setColorScheme } = useMantineColorScheme();
  return <label className="appearance-control">
    Appearance
    <select value={colorScheme} onChange={(event) => {
      const value = event.target.value;
      if (value === 'light' || value === 'dark' || value === 'auto') setColorScheme(value);
    }}>
      <option value="light">Light</option>
      <option value="dark">Dark</option>
      <option value="auto">System</option>
    </select>
  </label>;
}
