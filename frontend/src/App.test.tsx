import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App, { NOTE_ID_KEY } from './App';
import { ApiError, createNote, getNote, updateNote } from './notes';
import type { Note, NoteDocument } from './notes';

vi.mock('./notes', async (original) => ({
  ...await original<typeof import('./notes')>(), createNote: vi.fn(), getNote: vi.fn(), updateNote: vi.fn(),
}));
vi.mock('./components/KnowledgeEditor', () => ({
  KnowledgeEditor: ({ initialDocument, onDocumentChange }: {
    initialDocument: NoteDocument; onDocumentChange: (value: NoteDocument) => void;
  }) => <textarea aria-label="Note editor" defaultValue={JSON.stringify(initialDocument)}
    onChange={(event) => onDocumentChange(JSON.parse(event.target.value) as NoteDocument)} />,
}));
const note: Note = {
  id: 'saved-note', title: 'Persistent title', revision: 1, folder_id: null,
  document_json: [{ type: 'heading', props: { level: 1 }, content: [{ type: 'text', text: 'Saved heading', styles: { bold: true } }] }],
  format_version: 1, created_at: 'now', updated_at: 'now',
};
beforeEach(() => {
  window.localStorage.clear();
  vi.clearAllMocks();
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: 'ok' }) }));
  vi.mocked(getNote).mockResolvedValue(note);
  vi.mocked(createNote).mockResolvedValue(note);
});

describe('persistent workspace', () => {
  it('creates the initial note and remembers only its identifier', async () => {
    render(<App />);
    const title = await screen.findByLabelText('Note title');
    fireEvent.change(title, { target: { value: 'Initial title' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create note' }));
    expect(await screen.findByLabelText('Note editor')).toBeInTheDocument();
    expect(createNote).toHaveBeenCalledWith({ title: 'Initial title', document_json: [{ type: 'paragraph', content: [] }] });
    expect(window.localStorage.getItem(NOTE_ID_KEY)).toBe(note.id);
    expect(window.localStorage.length).toBe(1);
    expect(screen.getByRole('complementary')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
  });

  it('loads saved native content and title from the remembered identifier', async () => {
    window.localStorage.setItem(NOTE_ID_KEY, note.id);
    render(<App />);
    expect(await screen.findByLabelText('Note title')).toHaveValue(note.title);
    expect(screen.getByLabelText('Note editor')).toHaveValue(JSON.stringify(note.document_json));
    expect(getNote).toHaveBeenCalledWith(note.id, expect.any(AbortSignal));
    expect(screen.getByText('Saved')).toBeInTheDocument();
    expect(createNote).not.toHaveBeenCalled();
  });

  it('shows actual saving/saved feedback and retains editor edits', async () => {
    window.localStorage.setItem(NOTE_ID_KEY, note.id);
    let resolve!: (value: Note) => void;
    vi.mocked(updateNote).mockReturnValue(new Promise((yes) => { resolve = yes; }));
    render(<App />);
    const editor = await screen.findByLabelText('Note editor');
    const changed = [{ type: 'paragraph', content: [] }];
    fireEvent.change(editor, { target: { value: JSON.stringify(changed) } });
    expect(screen.getByText('Unsaved Changes')).toBeInTheDocument();
    expect(await screen.findByText('Saving...')).toBeInTheDocument();
    resolve({ ...note, revision: 2 });
    expect(await screen.findByText('Saved')).toBeInTheDocument();
    expect(editor).toHaveValue(JSON.stringify(changed));
  });

  it('reports a failed save without hiding the draft', async () => {
    window.localStorage.setItem(NOTE_ID_KEY, note.id);
    vi.mocked(updateNote).mockRejectedValue(new ApiError('Backend offline', 0));
    render(<App />);
    fireEvent.change(await screen.findByLabelText('Note title'), { target: { value: 'Unsaved title' } });
    expect(await screen.findByText('Save Error')).toBeInTheDocument();
    expect(screen.getByRole('alert')).toHaveTextContent('Backend offline');
    expect(screen.getByLabelText('Note title')).toHaveValue('Unsaved title');
    expect(screen.getByRole('button', { name: 'Retry save' })).toBeInTheDocument();
  });

  it('does not replace a missing/failed note with a newly created one', async () => {
    window.localStorage.setItem(NOTE_ID_KEY, note.id);
    vi.mocked(getNote).mockRejectedValue(new ApiError('Note not found', 404));
    render(<App />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Note not found');
    expect(screen.queryByRole('button', { name: 'Create note' })).not.toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Retry opening note' })).toBeInTheDocument();
    expect(createNote).not.toHaveBeenCalled();
  });

  it('reports create failure and allows another attempt', async () => {
    vi.mocked(createNote).mockRejectedValueOnce(new ApiError('Backend offline', 0));
    render(<App />);
    fireEvent.click(await screen.findByRole('button', { name: 'Create note' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Backend offline');
    await waitFor(() => expect(screen.getByRole('button', { name: 'Create note' })).toBeEnabled());
  });

  it.each([
    ['network failure', () => Promise.reject(new Error('offline'))],
    ['HTTP failure', () => Promise.resolve({ ok: false })],
    ['wrong response', () => Promise.resolve({ ok: true, json: async () => ({ status: 'wrong' }) })],
  ])('keeps the shell available on health %s', async (_name, response) => {
    vi.stubGlobal('fetch', vi.fn(response));
    render(<App />);
    expect(await screen.findByText('Backend at page load: offline')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
  });
});
