import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { useDesktopClose } from './useDesktopClose';
import { beginMutation } from '../pendingMutations';
const id = 'a'.repeat(32), next = 'b'.repeat(32);
beforeEach(() => vi.useFakeTimers());
afterEach(() => vi.useRealTimers());
const tick = async () => { await act(async () => { await vi.advanceTimersByTimeAsync(25); }); };
it('freezes editing, waits for pending mutations and real save acknowledgement', async () => {
  let resolve!: (value: boolean) => void;
  const flush = vi.fn(() => new Promise<boolean>((yes) => { resolve = yes; }));
  const finish = beginMutation();
  const { result } = renderHook(() => useDesktopClose(flush));
  act(() => window.__cyrnavaDesktop!.request(id)); expect(result.current).toBe(true);
  await tick(); expect(flush).not.toHaveBeenCalled(); finish(true); await tick();
  expect(window.__cyrnavaDesktop!.state(id)).toBe('waiting');
  await act(async () => resolve(true)); expect(window.__cyrnavaDesktop!.state(id)).toBe('saved');
});
it('refuses failed uploads/autosave, supports Keep open and retry', async () => {
  const flush = vi.fn().mockResolvedValueOnce(false).mockResolvedValueOnce(true);
  const { result } = renderHook(() => useDesktopClose(flush));
  act(() => window.__cyrnavaDesktop!.request(id)); await tick();
  expect(window.__cyrnavaDesktop!.state(id)).toBe('error');
  act(() => window.__cyrnavaDesktop!.cancel(id)); expect(result.current).toBe(false);
  act(() => window.__cyrnavaDesktop!.request(next)); await tick();
  expect(window.__cyrnavaDesktop!.state(next)).toBe('saved');
});
it('rejects a mutation failure during closure even if note flush succeeds', async () => {
  const finish = beginMutation(); renderHook(() => useDesktopClose(async () => true));
  act(() => window.__cyrnavaDesktop!.request(id)); await tick(); finish(false); await tick();
  expect(window.__cyrnavaDesktop!.state(id)).toBe('error');
});
it('ignores late acknowledgements after cancellation and duplicate requests', async () => {
  let resolve!: (value: boolean) => void;
  renderHook(() => useDesktopClose(() => new Promise<boolean>((yes) => { resolve = yes; })));
  act(() => window.__cyrnavaDesktop!.request(id)); await tick();
  act(() => window.__cyrnavaDesktop!.request(next));
  expect(window.__cyrnavaDesktop!.state(next)).toBe('unknown');
  act(() => window.__cyrnavaDesktop!.cancel(id)); await act(async () => resolve(true));
  expect(window.__cyrnavaDesktop!.state(id)).toBe('unknown');
});
it('reports thrown save failures and removes the protocol on unmount', async () => {
  const { unmount } = renderHook(() => useDesktopClose(async () => { throw new Error('offline'); }));
  act(() => window.__cyrnavaDesktop!.request(id)); await tick();
  expect(window.__cyrnavaDesktop!.state(id)).toBe('error');
  unmount(); expect(window.__cyrnavaDesktop).toBeUndefined();
});
it('times out pending mutations without deadlocking', async () => {
  const finish = beginMutation(); renderHook(() => useDesktopClose(async () => true));
  act(() => window.__cyrnavaDesktop!.request(id));
  await act(async () => { await vi.advanceTimersByTimeAsync(40_100); });
  expect(window.__cyrnavaDesktop!.state(id)).toBe('error'); finish(true);
});
