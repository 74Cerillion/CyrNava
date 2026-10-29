import { act, fireEvent, render, screen } from '@testing-library/react';
import { useComputedColorScheme } from '@mantine/core';
import { beforeEach, expect, it, vi } from 'vitest';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import { AppearanceControl, AppearanceProvider, APPEARANCE_KEY } from './appearance';
import { CYRNAVA_THEME_KEY } from './appearanceContext';

let systemDark = false;
let listeners: Set<(event: { matches: boolean }) => void>;
beforeEach(() => {
  systemDark = false; listeners = new Set();
  vi.stubGlobal('matchMedia', vi.fn(() => ({
    get matches() { return systemDark; },
    addEventListener: (_: string, listener: (event: { matches: boolean }) => void) => listeners.add(listener),
    removeEventListener: (_: string, listener: (event: { matches: boolean }) => void) => listeners.delete(listener),
  })));
});
function SystemChange(dark: boolean) {
  act(() => { systemDark = dark; for (const listener of listeners) listener({ matches: dark }); });
}
function Probe() {
  const resolved = useComputedColorScheme('light', { getInitialValueInEffect: false });
  return <><AppearanceControl /><output aria-label="Resolved appearance">{resolved}</output></>;
}
function mount() { return render(<AppearanceProvider><Probe /></AppearanceProvider>); }

it.each([null, 'invalid', 'system'])('defaults absent or invalid preference %s to System', (value) => {
  if (value !== null) localStorage.setItem(APPEARANCE_KEY, value);
  systemDark = true; mount();
  expect(screen.getByLabelText('Appearance')).toHaveValue('auto');
  expect(screen.getByLabelText('Resolved appearance')).toHaveTextContent('dark');
  expect(document.documentElement).toHaveAttribute('data-mantine-color-scheme', 'dark');
});

it('follows live system changes only while System is selected', () => {
  mount(); SystemChange(true);
  expect(screen.getByLabelText('Resolved appearance')).toHaveTextContent('dark');
  fireEvent.change(screen.getByLabelText('Appearance'), { target: { value: 'light' } });
  SystemChange(false); SystemChange(true);
  expect(screen.getByLabelText('Resolved appearance')).toHaveTextContent('light');
  expect(document.documentElement).toHaveAttribute('data-mantine-color-scheme', 'light');
  fireEvent.change(screen.getByLabelText('Appearance'), { target: { value: 'dark' } });
  SystemChange(false);
  expect(screen.getByLabelText('Resolved appearance')).toHaveTextContent('dark');
  fireEvent.change(screen.getByLabelText('Appearance'), { target: { value: 'auto' } });
  expect(screen.getByLabelText('Resolved appearance')).toHaveTextContent('light');
});

it('persists explicit preference and restores it on a fresh application mount', () => {
  const first = mount();
  fireEvent.change(screen.getByLabelText('Appearance'), { target: { value: 'dark' } });
  expect(localStorage.getItem(APPEARANCE_KEY)).toBe('dark');
  first.unmount(); mount();
  expect(screen.getByLabelText('Appearance')).toHaveValue('dark');
  expect(screen.getByLabelText('Resolved appearance')).toHaveTextContent('dark');
});

it('still switches appearance if localStorage is unavailable', () => {
  const read = vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('Storage denied'); });
  const write = vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('Storage denied'); });
  const warning = vi.spyOn(console, 'warn').mockImplementation(() => {});
  try {
    mount(); fireEvent.change(screen.getByLabelText('Appearance'), { target: { value: 'dark' } });
    expect(screen.getByLabelText('Resolved appearance')).toHaveTextContent('dark');
    fireEvent.change(screen.getByLabelText('Appearance'), { target: { value: 'cyrnava' } });
    expect(screen.getByLabelText('Appearance')).toHaveValue('cyrnava');
    expect(document.documentElement).toHaveAttribute('data-cyrnava-theme', 'true');
    expect(warning).toHaveBeenCalled();
  } finally { read.mockRestore(); write.mockRestore(); warning.mockRestore(); }
});

const bootstrap = readFileSync('public/assets/appearance-init.js', 'utf8');
it.each([
  ['light', true, 'light'], ['dark', false, 'dark'], ['auto', true, 'dark'],
  [null, false, 'light'], ['invalid', true, 'dark'],
])('initial startup script resolves %s with OS dark=%s before React', (stored, dark, resolved) => {
  const attribute = vi.fn();
  runInNewContext(bootstrap, {
    localStorage: { getItem: (key: string) => { expect([APPEARANCE_KEY, CYRNAVA_THEME_KEY]).toContain(key); return key === APPEARANCE_KEY ? stored : null; } },
    matchMedia: () => ({ matches: dark }), document: { documentElement: { setAttribute: attribute } },
  });
  expect(attribute).toHaveBeenCalledWith('data-mantine-color-scheme', resolved);
});
it('initial startup script tolerates blocked storage and absent matchMedia', () => {
  const attribute = vi.fn();
  runInNewContext(bootstrap, {
    localStorage: { getItem: () => { throw new Error('Storage denied'); } },
    document: { documentElement: { setAttribute: attribute } },
  });
  expect(attribute).toHaveBeenCalledWith('data-mantine-color-scheme', 'light');
});

it('adds CyrNava without replacing the previous preference, and restores it on remount', () => {
  localStorage.setItem(APPEARANCE_KEY, 'light');
  const first = mount();
  fireEvent.change(screen.getByLabelText('Appearance'), { target: { value: 'cyrnava' } });
  expect(screen.getByLabelText('Appearance')).toHaveValue('cyrnava');
  expect(screen.getByLabelText('Resolved appearance')).toHaveTextContent('dark');
  expect(localStorage.getItem(APPEARANCE_KEY)).toBe('light');
  expect(localStorage.getItem(CYRNAVA_THEME_KEY)).toBe('cyrnava');
  SystemChange(false);
  expect(document.documentElement).toHaveAttribute('data-cyrnava-theme', 'true');
  first.unmount(); mount();
  expect(screen.getByLabelText('Appearance')).toHaveValue('cyrnava');
  fireEvent.change(screen.getByLabelText('Appearance'), { target: { value: 'auto' } });
  expect(localStorage.getItem(CYRNAVA_THEME_KEY)).toBeNull();
  SystemChange(true);
  expect(screen.getByLabelText('Resolved appearance')).toHaveTextContent('dark');
  expect(document.documentElement).toHaveAttribute('data-cyrnava-theme', 'false');
});

it('applies the branded preference before React even when System is light', () => {
  const attribute = vi.fn();
  runInNewContext(bootstrap, {
    localStorage: { getItem: (key: string) => key === CYRNAVA_THEME_KEY ? 'cyrnava' : 'light' },
    matchMedia: () => ({ matches: false }), document: { documentElement: { setAttribute: attribute } },
  });
  expect(attribute).toHaveBeenCalledWith('data-cyrnava-theme', 'true');
  expect(attribute).toHaveBeenCalledWith('data-mantine-color-scheme', 'dark');
});

it('synchronizes the branded appearance across tabs', () => {
  mount();
  localStorage.setItem(CYRNAVA_THEME_KEY, 'cyrnava');
  act(() => window.dispatchEvent(new StorageEvent('storage', { key: CYRNAVA_THEME_KEY, newValue: 'cyrnava' })));
  expect(screen.getByLabelText('Appearance')).toHaveValue('cyrnava');
  expect(screen.getByLabelText('Resolved appearance')).toHaveTextContent('dark');
  localStorage.clear();
  act(() => window.dispatchEvent(new StorageEvent('storage', { key: null })));
  expect(screen.getByLabelText('Appearance')).toHaveValue('auto');
});
