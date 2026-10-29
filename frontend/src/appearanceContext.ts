import { createContext, useContext } from 'react';

// The branded skin is independent of Mantine's existing light/dark/auto preference.
export const CYRNAVA_THEME_KEY = 'cyrnava.theme.v1';
export const AppearanceContext = createContext<{ cyrnava: boolean; setCyrnava: (value: boolean) => void }>({ cyrnava: false, setCyrnava: () => undefined });
export function useCyrnavaTheme() { return useContext(AppearanceContext); }
export type EditorAppearance = 'light' | 'dark' | 'cyrnava';
