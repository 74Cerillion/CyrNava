import { act, render } from '@testing-library/react';
import { createRef, useImperativeHandle } from 'react';
import type { Ref } from 'react';
import { beforeEach, expect, it, vi } from 'vitest';
import { PersistentNote } from './PersistentNote';
import type { NoteHandle } from './PersistentNote';
import type { Note } from '../notes';

const { uploads, save } = vi.hoisted(() => ({ uploads: vi.fn(), save: vi.fn() }));
vi.mock('../hooks/useAutosave', () => ({ useAutosave: () => ({ title: 'Note', status: 'Saved', error: null, flush: save, changeTitle: vi.fn(), changeDocument: vi.fn() }) }));
vi.mock('./KnowledgeEditor', () => ({ KnowledgeEditor: ({ ref }: { ref: Ref<{ flushUploads: typeof uploads }> }) => {
  useImperativeHandle(ref, () => ({ flushUploads: uploads }), []);
  return <div>Editor adapter</div>;
} }));
const note: Note = { id: 'A', title: 'Note', folder_id: null, document_json: [{ type: 'paragraph', content: [] }], revision: 1, format_version: 1, created_at: '', updated_at: '' };
beforeEach(() => { vi.resetAllMocks(); save.mockResolvedValue(true); });
it('drains uploads before requesting the ordinary autosave flush', async () => {
  let finish!: (value: boolean) => void;
  uploads.mockReturnValue(new Promise((resolve) => { finish = resolve; }));
  const ref = createRef<NoteHandle>(); render(<PersistentNote ref={ref} note={note} />);
  const result = ref.current!.flush();
  expect(uploads).toHaveBeenCalledOnce(); expect(save).not.toHaveBeenCalled();
  await act(async () => { finish(true); expect(await result).toBe(true); });
  expect(save).toHaveBeenCalledOnce();
});
it('does not allow navigation when a pending upload fails', async () => {
  uploads.mockResolvedValue(false);
  const ref = createRef<NoteHandle>(); render(<PersistentNote ref={ref} note={note} />);
  await act(async () => { expect(await ref.current!.flush()).toBe(false); });
  expect(save).not.toHaveBeenCalled();
});
