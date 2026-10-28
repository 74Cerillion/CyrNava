import '@testing-library/jest-dom/vitest';
import { cleanup } from '@testing-library/react';
import { afterEach, beforeEach, vi } from 'vitest';

// jsdom does not implement the browser's appearance/viewport media queries.
// Appearance-specific tests replace this with a controllable event source.
beforeEach(() => vi.stubGlobal('matchMedia', vi.fn((query: string) => ({
  matches: false, media: query, onchange: null,
  addEventListener() {}, removeEventListener() {}, addListener() {}, removeListener() {}, dispatchEvent() { return true; },
}))));

afterEach(() => {
  cleanup();
  window.localStorage.clear();
  document.documentElement.removeAttribute('data-mantine-color-scheme');
  vi.unstubAllGlobals();
});

// jsdom has no browser top-layer/focus implementation for native dialogs.
HTMLDialogElement.prototype.showModal = function () { this.setAttribute('open', ''); };
HTMLDialogElement.prototype.close = function () { this.removeAttribute('open'); };
