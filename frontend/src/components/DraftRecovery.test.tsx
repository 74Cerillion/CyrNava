import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { PersistentNote } from './PersistentNote';
import { updateNote } from '../notes';
import type { Note } from '../notes';
import { findDrafts, storeDraft } from '../drafts';

vi.mock('../notes', async (original) => ({ ...await original<typeof import('../notes')>(), updateNote: vi.fn() }));
vi.mock('./KnowledgeEditor', () => ({ KnowledgeEditor: () => <div>Editor</div> }));
const note: Note = { id: 'recovery', title: 'Saved', revision: 2, folder_id: null,
  document_json: [{ type: 'paragraph', content: [] }], format_version: 1, created_at: '', updated_at: '' };
beforeEach(() => {
  localStorage.clear(); vi.clearAllMocks();
  const record = storeDraft(note, { ...note, title: 'Unconfirmed' }, 2);
  localStorage.clear(); localStorage.setItem('engage.recovery.v1:recovery:closed-tab',
    JSON.stringify({ ...record, writer: 'closed-tab' }));
});
it('offers recovery and clears only after acknowledged revision-checked persistence', async () => {
  let finish!: (note: Note) => void;
  vi.mocked(updateNote).mockReturnValue(new Promise((resolve) => { finish = resolve; }));
  render(<PersistentNote note={note} />);
  expect(screen.getByRole('heading', { name: 'Recover unsaved edits' })).toBeInTheDocument();
  expect(updateNote).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Recover draft' }));
  await waitFor(() => expect(updateNote).toHaveBeenCalledWith(note.id, 2,
    expect.objectContaining({ title: 'Unconfirmed' }), expect.any(AbortSignal)));
  expect(findDrafts(note.id)).toHaveLength(1);
  finish({ ...note, title: 'Unconfirmed', revision: 3 });
  await screen.findByText('Saved', { exact: true });
  expect(findDrafts(note.id)).toEqual([]);
});
it('blocks automatic writes when the saved note has a newer revision', async () => {
  render(<PersistentNote note={{ ...note, revision: 3 }} />);
  fireEvent.click(screen.getByRole('button', { name: 'Recover draft' }));
  expect(await screen.findByText('Save Error')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Review conflict and recover' })).toBeInTheDocument();
  expect(updateNote).not.toHaveBeenCalled(); expect(findDrafts(note.id)).toHaveLength(1);
});
it('opening the saved note preserves the unconfirmed record', () => {
  render(<PersistentNote note={note} />);
  fireEvent.click(screen.getByRole('button', { name: /Continue with saved note/ }));
  expect(screen.getByDisplayValue('Saved')).toBeInTheDocument();
  expect(findDrafts(note.id, true)).toHaveLength(1); expect(updateNote).not.toHaveBeenCalled();
});
