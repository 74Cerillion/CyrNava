import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, updateNote } from '../notes';
import type { Note, NoteDocument } from '../notes';
import { AUTOSAVE_DELAY, useAutosave } from './useAutosave';

vi.mock('../notes', async (original) => ({ ...await original<typeof import('../notes')>(), updateNote: vi.fn() }));
const note: Note = {
  id: 'note-1', title: 'Saved title', document_json: [{ type: 'paragraph', content: [] }],
  revision: 1, format_version: 1, folder_id: null, created_at: 'now', updated_at: 'now',
};
const document = (text: string): NoteDocument => [{ type: 'paragraph', content: [{ type: 'text', text, styles: {} }] }];
function deferred() {
  let resolve!: (note: Note) => void;
  let reject!: (error: Error) => void;
  const promise = new Promise<Note>((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
async function tick(milliseconds = AUTOSAVE_DELAY) {
  await act(async () => { await vi.advanceTimersByTimeAsync(milliseconds); });
}

beforeEach(() => { vi.useFakeTimers(); vi.mocked(updateNote).mockReset(); });
afterEach(() => { vi.useRealTimers(); });

describe('serial debounced autosave', () => {
  it('starts saved, debounces changes, and reports saving then saved', async () => {
    const pending = deferred();
    vi.mocked(updateNote).mockReturnValue(pending.promise);
    const { result } = renderHook(() => useAutosave(note));
    expect(result.current.status).toBe('Saved');
    act(() => result.current.changeDocument(document('A')));
    expect(result.current.status).toBe('Unsaved Changes');
    await tick(AUTOSAVE_DELAY - 1);
    expect(updateNote).not.toHaveBeenCalled();
    await tick(1);
    expect(result.current.status).toBe('Saving...');
    await act(async () => pending.resolve({ ...note, revision: 2 }));
    expect(result.current.status).toBe('Saved');
    expect(result.current.revision).toBe(2);
  });

  it('keeps rapid edits and sends only the latest debounced snapshot', async () => {
    vi.mocked(updateNote).mockResolvedValue({ ...note, revision: 2 });
    const { result } = renderHook(() => useAutosave(note));
    act(() => result.current.changeDocument(document('A')));
    await tick(400);
    act(() => result.current.changeDocument(document('AB')));
    await tick(400);
    act(() => result.current.changeTitle('Latest title'));
    await tick();
    expect(updateNote).toHaveBeenCalledTimes(1);
    expect(updateNote).toHaveBeenCalledWith(note.id, 1, {
      title: 'Latest title', document_json: document('AB'),
    }, expect.any(AbortSignal));
    expect(result.current.status).toBe('Saved');
  });

  it('never lets an older acknowledgement mark newer typing saved or overlap requests', async () => {
    const first = deferred();
    const second = deferred();
    vi.mocked(updateNote).mockReturnValueOnce(first.promise).mockReturnValueOnce(second.promise);
    const { result } = renderHook(() => useAutosave(note));
    act(() => result.current.changeDocument(document('A')));
    await tick();
    act(() => result.current.changeDocument(document('AB')));
    await tick();
    expect(updateNote).toHaveBeenCalledTimes(1);
    expect(result.current.status).toBe('Unsaved Changes');
    await act(async () => first.resolve({ ...note, revision: 2 }));
    // Acknowledged A, but AB is still dirty. A response cannot claim AB is saved.
    expect(result.current.status).not.toBe('Saved');
    await tick(0);
    expect(updateNote).toHaveBeenCalledTimes(2);
    expect(updateNote).toHaveBeenLastCalledWith(note.id, 2, {
      title: note.title, document_json: document('AB'),
    }, expect.any(AbortSignal));
    expect(result.current.status).toBe('Saving...');
    await act(async () => second.resolve({ ...note, revision: 3 }));
    expect(result.current.status).toBe('Saved');
  });

  it('reports failures and retries the latest draft with its original expected revision', async () => {
    vi.mocked(updateNote).mockRejectedValueOnce(new ApiError('Backend offline', 0))
      .mockResolvedValueOnce({ ...note, revision: 2 });
    const { result } = renderHook(() => useAutosave(note));
    act(() => result.current.changeTitle('Keep me'));
    await tick();
    expect(result.current.status).toBe('Save Error');
    expect(result.current.title).toBe('Keep me');
    await tick(10_000);
    expect(updateNote).toHaveBeenCalledTimes(1);
    act(() => result.current.retry());
    await tick(0);
    expect(updateNote).toHaveBeenLastCalledWith(note.id, 1, {
      title: 'Keep me', document_json: note.document_json,
    }, expect.any(AbortSignal));
    expect(result.current.status).toBe('Saved');
  });

  it('blocks automatic retries after revision conflict even when typing continues', async () => {
    vi.mocked(updateNote).mockRejectedValue(new ApiError('Conflict', 409));
    const { result } = renderHook(() => useAutosave(note));
    act(() => result.current.changeTitle('Local draft'));
    await tick();
    act(() => result.current.changeTitle('Still my local draft'));
    act(() => result.current.retry());
    await tick(5000);
    expect(updateNote).toHaveBeenCalledTimes(1);
    expect(result.current.status).toBe('Save Error');
    expect(result.current.error?.conflict).toBe(true);
    expect(result.current.title).toBe('Still my local draft');
  });

  it('validates title locally, retains changes, and recovers after correction', async () => {
    vi.mocked(updateNote).mockResolvedValue({ ...note, revision: 2 });
    const { result } = renderHook(() => useAutosave(note));
    act(() => result.current.changeTitle('   '));
    await tick();
    expect(result.current.status).toBe('Save Error');
    expect(updateNote).not.toHaveBeenCalled();
    act(() => result.current.changeTitle('Corrected'));
    await tick();
    expect(result.current.status).toBe('Saved');
  });

  it('warns before leaving with pending edits and removes the warning once saved', async () => {
    vi.mocked(updateNote).mockResolvedValue({ ...note, revision: 2 });
    const { result } = renderHook(() => useAutosave(note));
    act(() => result.current.changeTitle('Dirty'));
    const dirty = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(dirty);
    expect(dirty.defaultPrevented).toBe(true);
    await tick();
    const saved = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(saved);
    expect(saved.defaultPrevented).toBe(false);
  });

  it('aborts on unmount and ignores late responses', async () => {
    const pending = deferred();
    vi.mocked(updateNote).mockReturnValue(pending.promise);
    const { result, unmount } = renderHook(() => useAutosave(note));
    act(() => result.current.changeTitle('A'));
    await tick();
    const signal = vi.mocked(updateNote).mock.calls[0][3];
    unmount();
    expect(signal?.aborted).toBe(true);
    await act(async () => pending.resolve({ ...note, revision: 2 }));
    expect(result.current.status).toBe('Saving...');
  });
});

it('honors the remaining debounce delay after an earlier save completes', async () => {
  const first = deferred();
  vi.mocked(updateNote).mockReturnValueOnce(first.promise)
    .mockResolvedValueOnce({ ...note, revision: 3 });
  const { result } = renderHook(() => useAutosave(note));
  act(() => result.current.changeDocument(document('A')));
  await tick();
  act(() => result.current.changeDocument(document('AB')));
  await tick(200);
  await act(async () => first.resolve({ ...note, revision: 2 }));
  await tick(499);
  expect(updateNote).toHaveBeenCalledTimes(1);
  expect(result.current.status).toBe('Unsaved Changes');
  await tick(1);
  expect(updateNote).toHaveBeenCalledTimes(2);
  expect(result.current.status).toBe('Saved');
});
