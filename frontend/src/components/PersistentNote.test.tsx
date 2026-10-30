import { act, render, screen } from '@testing-library/react';
import { createRef, useImperativeHandle } from 'react';
import type { Ref } from 'react';
import { beforeEach, expect, it, vi } from 'vitest';
import { PersistentNote } from './PersistentNote';
import type { NoteHandle } from './PersistentNote';
import type { Note } from '../notes';
import { downloadDraft } from '../drafts';

const { uploads, save, reportUpload, saveProblem } = vi.hoisted(() => ({ uploads: vi.fn(), save: vi.fn(), reportUpload: vi.fn(), saveProblem: { current: null as { message: string; conflict: boolean } | null } }));
vi.mock('../hooks/useAutosave', () => ({ useAutosave: () => ({ title: 'Note', status: 'Saved', error: saveProblem.current, document: note.document_json, getRevision: () => note.revision, flush: save, changeTitle: vi.fn(), changeDocument: vi.fn() }) }));
vi.mock('../drafts', async (original) => ({ ...await original<typeof import('../drafts')>(), downloadDraft: vi.fn() }));
vi.mock('./KnowledgeEditor', () => ({ KnowledgeEditor: ({ ref, onUploadStateChange }: { ref: Ref<{ flushUploads: typeof uploads }>; onUploadStateChange: (state: { pending: boolean; incomplete: boolean }) => void }) => {
  reportUpload.mockImplementation(onUploadStateChange);
  useImperativeHandle(ref, () => ({ flushUploads: uploads }), []);
  return <div>Editor adapter</div>;
} }));
const note: Note = { id: 'A', title: 'Note', folder_id: null, document_json: [{ type: 'paragraph', content: [] }], revision: 1, format_version: 1, created_at: '', updated_at: '' };
beforeEach(() => { vi.resetAllMocks(); saveProblem.current = null; save.mockResolvedValue(true); });
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

it('reports upload activity and incomplete images instead of Saved', () => {
  render(<PersistentNote note={note} />);
  expect(screen.getByText('Saved', { exact: true })).toBeVisible();
  act(() => reportUpload({ pending: true, incomplete: true }));
  expect(screen.queryByText('Saved', { exact: true })).not.toBeInTheDocument();
  expect(screen.getByText('Saving...', { exact: true })).toBeVisible();
  act(() => reportUpload({ pending: false, incomplete: true }));
  expect(screen.getByText('Save Error', { exact: true })).toBeVisible();
  act(() => reportUpload({ pending: false, incomplete: false }));
  expect(screen.getByText('Saved', { exact: true })).toBeVisible();
});

it('exports the current native draft after a failed save without requiring browser storage or the backend', async () => {
  const { fireEvent } = await import('@testing-library/react');
  saveProblem.current = { message: 'Offline', conflict: false };
  render(<PersistentNote note={note} />);
  fireEvent.click(screen.getByRole('button', { name: 'Download pending draft' }));
  expect(downloadDraft).toHaveBeenCalledWith(expect.objectContaining({
    note_id: note.id, base_revision: note.revision, title: 'Note', document_json: note.document_json,
  }));
});
