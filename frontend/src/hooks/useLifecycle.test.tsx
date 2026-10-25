import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { useLifecycle } from './useLifecycle';

const reply = (data: unknown, ok = true) => Promise.resolve(new Response(JSON.stringify(data), { status: ok ? 200 : 503 }));
async function tick(ms = 0) { await act(async () => { await vi.advanceTimersByTimeAsync(ms); }); }
beforeEach(() => {
  vi.useFakeTimers();
  vi.stubGlobal('fetch', vi.fn().mockImplementation((url: string) => reply(url === '/api/lifecycle'
    ? { managed: true, instance: 'test', heartbeat_ms: 5000 } : { registered: true })));
  Object.defineProperty(navigator, 'sendBeacon', { configurable: true, value: vi.fn(() => true) });
});
afterEach(() => vi.useRealTimers());
it('registers one page lease, renews and sends only a small close hint', async () => {
  const { unmount } = renderHook(useLifecycle); await tick();
  expect(fetch).toHaveBeenCalledTimes(2);
  const first = vi.mocked(fetch).mock.calls[1];
  await tick(5000); expect(fetch).toHaveBeenCalledTimes(3);
  expect(vi.mocked(fetch).mock.calls[2][0]).toBe(first[0]);
  expect(JSON.parse(first[1]!.body as string)).toMatchObject({ instance: 'test' });
  act(() => window.dispatchEvent(new Event('pagehide')));
  expect(navigator.sendBeacon).toHaveBeenCalledOnce();
  await tick(10000); expect(fetch).toHaveBeenCalledTimes(3);
  act(() => window.dispatchEvent(new Event('pageshow'))); await tick();
  expect(fetch).toHaveBeenCalledTimes(4);
  unmount();
});
it('does not keep polling or register with an independent development server', async () => {
  vi.mocked(fetch).mockImplementation(() => reply({ managed: false }));
  renderHook(useLifecycle); await tick(60000);
  expect(fetch).toHaveBeenCalledOnce();
});
it('reports a lost/draining instance and reconnects through fresh configuration', async () => {
  const { result } = renderHook(useLifecycle); await tick();
  vi.mocked(fetch).mockImplementation(() => reply({}, false));
  await tick(5000); expect(result.current).toContain('interrupted');
  vi.mocked(fetch).mockImplementation((url) => reply(url === '/api/lifecycle'
    ? { managed: true, instance: 'replacement', heartbeat_ms: 5000 } : {}));
  await tick(5000); expect(result.current).toBeNull();
  expect(JSON.parse(vi.mocked(fetch).mock.lastCall![1]!.body as string).instance).toBe('replacement');
});
