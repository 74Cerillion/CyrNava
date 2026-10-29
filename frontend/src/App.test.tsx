import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App, { NAVIGATION_KEY, NOTE_ID_KEY } from './App';
import { ApiError, createNote, createNoteFromTemplate, deleteNote, getNote, updateNote } from './notes';
import { captureTemplate, getTemplates } from './templates';
import type { Note, NoteDocument } from './notes';
import { createFolder, deleteFolder, getDeletionImpact, getTree, updateFolder } from './library';
import type { DirectoryData, Folder } from './library';
import { searchNotes } from './search';
import type { SearchResult } from './search';
import { storeDraft } from './drafts';

vi.mock('./notes', async (original) => ({
  ...await original<typeof import('./notes')>(), createNote: vi.fn(), createNoteFromTemplate: vi.fn(), getNote: vi.fn(), updateNote: vi.fn(), deleteNote: vi.fn(),
}));
vi.mock('./search', () => ({ searchNotes: vi.fn() }));
vi.mock('./templates', () => ({ getTemplates: vi.fn(), captureTemplate: vi.fn(), renameTemplate: vi.fn(), deleteTemplate: vi.fn() }));
vi.mock('./library', () => ({ getTree: vi.fn(), createFolder: vi.fn(), updateFolder: vi.fn(), deleteFolder: vi.fn(), getDeletionImpact: vi.fn() }));
vi.mock('./components/KnowledgeEditor', () => ({
  KnowledgeEditor: ({ initialDocument, onDocumentChange, editable, theme }: {
    initialDocument: NoteDocument; onDocumentChange: (value: NoteDocument) => void; editable: boolean; theme?: string;
  }) => <textarea aria-label="Note editor" data-theme={theme} disabled={!editable} defaultValue={JSON.stringify(initialDocument)}
    onChange={(event) => onDocumentChange(JSON.parse(event.target.value) as NoteDocument)} />,
}));
const original: Note = {
  id: 'saved-note', title: 'Persistent title', revision: 1, folder_id: null,
  document_json: [{ type: 'heading', props: { level: 1 }, content: [{ type: 'text', text: 'Saved heading', styles: { bold: true } }] }],
  format_version: 1, created_at: 'now', updated_at: 'now',
};
let tree: DirectoryData;
let records: Map<string, Note>;
let counter: number;
function seed(...notes: Note[]) { for (const note of notes) { records.set(note.id, structuredClone(note)); tree.notes.push(note); } }
function makeFolder(id: string, name: string, parent_id: string | null = null): Folder {
  return { id, name, parent_id, sort_order: 0, created_at: '', updated_at: '' };
}
beforeEach(() => {
  window.localStorage.clear(); vi.resetAllMocks();
  tree = { folders: [], notes: [] }; records = new Map(); counter = 0;
  vi.mocked(getTemplates).mockResolvedValue([]);
  vi.mocked(searchNotes).mockResolvedValue({ query: '', total: 0, results: [] });
  vi.stubGlobal('fetch', vi.fn().mockImplementation(async (path: string) => ({ ok: true, json: async () => path === '/api/lifecycle' ? { managed: false } : { status: 'ok' } })));
  vi.mocked(getTree).mockImplementation(async () => structuredClone(tree));
  vi.mocked(getNote).mockImplementation(async (id) => {
    if (!records.has(id)) throw new ApiError('Note not found', 404);
    return structuredClone(records.get(id)!);
  });
  vi.mocked(createNote).mockImplementation(async (draft) => {
    const note = { ...original, ...draft, id: `created-${++counter}`, folder_id: draft.folder_id || null };
    seed(note); return note;
  });
  vi.mocked(updateNote).mockImplementation(async (id, revision, draft) => {
    const updated = { ...records.get(id)!, ...draft, revision: revision + 1 };
    records.set(id, updated); tree.notes = tree.notes.map((note) => note.id === id ? updated : note);
    return structuredClone(updated);
  });
  vi.mocked(createFolder).mockImplementation(async (name, parent_id) => {
    const folder = makeFolder(`folder-${++counter}`, name, parent_id); tree.folders.push(folder); return folder;
  });
  vi.mocked(updateFolder).mockImplementation(async (id, changes) => {
    tree.folders = tree.folders.map((folder) => folder.id === id ? { ...folder, ...changes } : folder);
    return tree.folders.find((folder) => folder.id === id)!;
  });
  vi.mocked(deleteNote).mockImplementation(async (id) => { records.delete(id); tree.notes = tree.notes.filter((note) => note.id !== id); });
});
async function createThroughDialog(kind: 'note' | 'folder', name: string) {
  fireEvent.click(await screen.findByRole('button', { name: `New ${kind}` }));
  const dialog = await screen.findByRole('dialog');
  fireEvent.change(within(dialog).getByLabelText(kind === 'note' ? 'Note title' : 'Name'), { target: { value: name } });
  fireEvent.click(screen.getByRole('button', { name: 'Create' }));
  await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  await waitFor(() => expect(screen.getByRole('button', { name: 'New folder' })).toBeEnabled());
}
async function management(name: string) {
  fireEvent.click(screen.getByRole('button', { name }));
  return screen.findByRole('dialog');
}

async function searchResult(note: Note, query = 'matching') {
  const result: SearchResult = { note_id: note.id, title: note.title, folder_path: ['Remote'], snippet: 'Matching snippet', score: -1 };
  vi.mocked(searchNotes).mockResolvedValue({ query, total: 1, results: [result] });
  fireEvent.change(screen.getByRole('combobox', { name: 'Search all notes' }), { target: { value: query } });
  return screen.findByRole('option', { name: `Open note: ${note.title}` });
}

describe('F-09 search navigation', () => {
  it('opens the canonical note, refreshes stale folder metadata and reveals/selects its ancestors', async () => {
    seed(original); render(<App />); await screen.findByLabelText('Note editor');
    const destination = { ...original, id: 'new-note', title: 'Remote result', folder_id: 'child', document_json: [{ type: 'codeBlock', content: [{ type: 'text', text: 'native code', styles: {} }] }] };
    // Simulate another tab adding a note/folders after the initial library read.
    tree.folders.push(makeFolder('parent', 'Root'), makeFolder('child', 'Nested', 'parent')); seed(destination);
    const result = await searchResult(destination); fireEvent.click(result);
    await waitFor(() => expect(screen.getByLabelText('Note title')).toHaveValue(destination.title));
    expect(screen.getByLabelText('Note editor')).toHaveValue(JSON.stringify(destination.document_json));
    expect(screen.getByRole('treeitem', { name: 'Folder Root' })).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('treeitem', { name: 'Folder Nested' })).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByRole('treeitem', { name: 'Note Remote result' })).toHaveAttribute('aria-current', 'true');
    expect(screen.getByRole('treeitem', { name: 'Note Remote result' })).toHaveAttribute('aria-selected', 'true');
    expect(localStorage.getItem(NOTE_ID_KEY)).toBe(destination.id);
    expect(screen.getByRole('combobox', { name: 'Search all notes' })).toHaveValue('matching');
  });

  it('waits for both an in-flight snapshot and newer queued typing before opening a result', async () => {
    const destination = { ...original, id: 'destination', title: 'Destination' }; seed(original, destination);
    const pending: (() => void)[] = [];
    vi.mocked(updateNote).mockImplementation((id, revision, draft) => new Promise((resolve) => {
      pending.push(() => { const saved = { ...records.get(id)!, ...draft, revision: revision + 1 }; records.set(id, saved); resolve(saved); });
    }));
    render(<App />); const editor = await screen.findByLabelText('Note editor'); const result = await searchResult(destination);
    fireEvent.change(screen.getByLabelText('Note title'), { target: { value: 'Paragraph A' } });
    await screen.findByText('Saving...', { exact: true });
    fireEvent.change(screen.getByLabelText('Note title'), { target: { value: 'Paragraph A and B' } });
    fireEvent.click(result);
    expect(editor).toBeDisabled(); expect(getNote).toHaveBeenCalledTimes(1);
    await act(async () => pending[0]()); await waitFor(() => expect(updateNote).toHaveBeenCalledTimes(2));
    expect(getNote).toHaveBeenCalledTimes(1);
    expect(updateNote).toHaveBeenLastCalledWith(original.id, 2, expect.objectContaining({ title: 'Paragraph A and B' }), expect.any(AbortSignal));
    await act(async () => pending[1]());
    await waitFor(() => expect(screen.getByLabelText('Note title')).toHaveValue(destination.title));
    expect(records.get(original.id)?.title).toBe('Paragraph A and B'); expect(records.get(original.id)?.revision).toBe(3);
  });

  it.each([409, 503])('keeps the current editor/draft when its save fails with HTTP %s', async (status) => {
    const destination = { ...original, id: 'destination', title: 'Destination' }; seed(original, destination);
    vi.mocked(updateNote).mockRejectedValue(new ApiError('Synthetic save error', status));
    render(<App />); const editor = await screen.findByLabelText('Note editor'); const result = await searchResult(destination);
    fireEvent.change(screen.getByLabelText('Note title'), { target: { value: 'Keep this draft' } });
    fireEvent.click(result);
    await screen.findByText(/Cannot leave this note until pending edits/);
    expect(screen.getByLabelText('Note editor')).toBe(editor);
    expect(screen.getByLabelText('Note title')).toHaveValue('Keep this draft');
    expect(getNote).not.toHaveBeenCalledWith(destination.id, expect.anything());
    expect(localStorage.getItem(NOTE_ID_KEY)).toBe(original.id);
  });

  it('selects an already-open result without remounting or forcing a dirty save', async () => {
    seed(original); render(<App />); const editor = await screen.findByLabelText('Note editor'); const result = await searchResult(original);
    fireEvent.change(screen.getByLabelText('Note title'), { target: { value: 'Pending local title' } });
    fireEvent.click(result);
    expect(screen.getByLabelText('Note editor')).toBe(editor); expect(screen.getByLabelText('Note title')).toHaveValue('Pending local title');
    expect(updateNote).not.toHaveBeenCalled(); expect(getNote).toHaveBeenCalledTimes(1);
  });

  it('preserves the active editor if a result was deleted or the fresh tree cannot load', async () => {
    const destination = { ...original, id: 'deleted', title: 'Deleted result' }; seed(original, destination);
    render(<App />); const editor = await screen.findByLabelText('Note editor');
    fireEvent.click(await searchResult(destination));
    // The first ordinary opening succeeds; return to the source before failure cases.
    await waitFor(() => expect(screen.getByLabelText('Note title')).toHaveValue(destination.title));
    fireEvent.click(screen.getByRole('treeitem', { name: 'Note Persistent title' }));
    await waitFor(() => expect(screen.getByLabelText('Note title')).toHaveValue(original.title));
    const currentEditor = screen.getByLabelText('Note editor'); expect(currentEditor).not.toBe(editor);
    records.delete(destination.id); fireEvent.click(await screen.findByRole('option', { name: 'Open note: Deleted result' }));
    await screen.findByText('Note not found'); expect(screen.getByLabelText('Note editor')).toBe(currentEditor);
    records.set(destination.id, destination); vi.mocked(getTree).mockRejectedValueOnce(new Error('Cannot refresh library'));
    fireEvent.click(screen.getByRole('option', { name: 'Open note: Deleted result' }));
    await screen.findByText('Cannot refresh library'); expect(screen.getByLabelText('Note editor')).toBe(currentEditor);
    expect(screen.getByLabelText('Note title')).toHaveValue(original.title);
  });

  it('refreshes the active query after saving without moving focus from the editor', async () => {
    seed(original); render(<App />); await screen.findByLabelText('Note editor'); await searchResult(original);
    const reads = vi.mocked(searchNotes).mock.calls.length;
    const title = screen.getByLabelText('Note title'); title.focus();
    fireEvent.change(title, { target: { value: 'Indexed new title' } });
    expect(searchNotes).toHaveBeenCalledTimes(reads);
    await screen.findByText('Saved', { exact: true });
    await waitFor(() => expect(searchNotes).toHaveBeenCalledTimes(reads + 1));
    expect(title).toHaveFocus();
  });

  it('cannot bypass pending draft recovery by choosing a search result', async () => {
    const destination = { ...original, id: 'destination', title: 'Destination' }; seed(original, destination);
    const draft = storeDraft(original, { title: 'Unconfirmed draft', document_json: original.document_json }, 1);
    // Drafts from a prior page are eligible for the existing recovery UI.
    const name = localStorage.key(0)!; localStorage.setItem(name, JSON.stringify({ ...draft, writer: 'prior-page' }));
    render(<App />); const recovery = await screen.findByRole('region', { name: 'Draft recovery' });
    fireEvent.click(await searchResult(destination)); await screen.findByText(/Cannot leave this note until pending edits/);
    expect(screen.getByRole('region', { name: 'Draft recovery' })).toBe(recovery);
    expect(localStorage.getItem(name)).toContain('Unconfirmed draft');
    expect(getNote).not.toHaveBeenCalledWith(destination.id, expect.anything());
  });

  it('does not install a fetched note if it disappeared before the fresh tree response', async () => {
    const destination = { ...original, id: 'destination', title: 'Destination' }; seed(original, destination);
    render(<App />); const editor = await screen.findByLabelText('Note editor');
    const result = await searchResult(destination);
    vi.mocked(getTree).mockResolvedValueOnce({ folders: [], notes: [original] });
    fireEvent.click(result); await screen.findByText(/This note is no longer in the library/);
    expect(screen.getByLabelText('Note editor')).toBe(editor); expect(screen.getByLabelText('Note title')).toHaveValue(original.title);
  });
});

describe('M1 behavior preserved through the library', () => {
  it('creates a note and stores only its identifier in localStorage', async () => {
    render(<App />);
    await waitFor(() => expect(screen.queryByText('Opening library...')).not.toBeInTheDocument());
    await createThroughDialog('note', 'Initial title');
    expect(await screen.findByLabelText('Note editor')).toBeInTheDocument();
    expect(createNote).toHaveBeenCalledWith({ title: 'Initial title', document_json: [{ type: 'paragraph', content: [] }], folder_id: null });
    expect(window.localStorage.getItem(NOTE_ID_KEY)).toBe('created-1');
    expect(window.localStorage.length).toBe(1);
    expect(screen.getByRole('complementary')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
  });
  it('loads remembered content, title, and formatting from SQLite via the API', async () => {
    seed(original); window.localStorage.setItem(NOTE_ID_KEY, original.id);
    render(<App />);
    expect(await screen.findByLabelText('Note title')).toHaveValue(original.title);
    expect(screen.getByLabelText('Note editor')).toHaveValue(JSON.stringify(original.document_json));
    expect(getNote).toHaveBeenCalledWith(original.id, expect.any(AbortSignal));
    expect(screen.getByText('Saved')).toBeInTheDocument();
    expect(createNote).not.toHaveBeenCalled();
  });
  it('shows saving/saved feedback and retains editor edits', async () => {
    seed(original);
    let resolve!: (note: Note) => void;
    vi.mocked(updateNote).mockReturnValue(new Promise((yes) => { resolve = yes; }));
    render(<App />);
    const editor = await screen.findByLabelText('Note editor');
    const changed = [{ type: 'paragraph', content: [] }];
    fireEvent.change(editor, { target: { value: JSON.stringify(changed) } });
    expect(screen.getByText('Unsaved Changes')).toBeInTheDocument();
    expect(await screen.findByText('Saving...')).toBeInTheDocument();
    await act(async () => resolve({ ...original, revision: 2 }));
    expect(await screen.findByText('Saved')).toBeInTheDocument();
    expect(editor).toHaveValue(JSON.stringify(changed));
  });
  it('reports save failure without hiding the draft', async () => {
    seed(original); vi.mocked(updateNote).mockRejectedValue(new ApiError('Backend offline', 0));
    render(<App />);
    fireEvent.change(await screen.findByLabelText('Note title'), { target: { value: 'Unsaved title' } });
    expect(await screen.findByText('Save Error')).toBeInTheDocument();
    expect(screen.getByLabelText('Note title')).toHaveValue('Unsaved title');
    expect(screen.getByRole('button', { name: 'Retry save' })).toBeInTheDocument();
  });
  it('does not silently recreate a remembered note that fails to load', async () => {
    seed(original); window.localStorage.setItem(NOTE_ID_KEY, original.id);
    vi.mocked(getNote).mockRejectedValue(new ApiError('Note not found', 404));
    render(<App />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Note not found');
    expect(createNote).not.toHaveBeenCalled();
  });
  it('reports creation failure and retains the creation form', async () => {
    vi.mocked(createNote).mockRejectedValueOnce(new ApiError('Backend offline', 0));
    render(<App />);
    await waitFor(() => expect(screen.queryByText('Opening library...')).not.toBeInTheDocument());
    fireEvent.click(screen.getByRole('button', { name: 'New note' }));
    fireEvent.change(await screen.findByLabelText('Note title'), { target: { value: 'Keep title' } });
    fireEvent.click(screen.getByRole('button', { name: 'Create' }));
    expect(await screen.findByRole('alert')).toHaveTextContent('Backend offline');
    expect(screen.getByLabelText('Note title')).toHaveValue('Keep title');
  });
  it.each([
    ['network failure', () => Promise.reject(new Error('offline'))],
    ['HTTP failure', () => Promise.resolve({ ok: false })],
    ['wrong response', () => Promise.resolve({ ok: true, json: async () => ({ status: 'wrong' }) })],
  ])('keeps the shell available on health %s', async (_name, response) => {
    vi.stubGlobal('fetch', vi.fn(response)); render(<App />);
    expect(await screen.findByText('Backend at page load: offline')).toBeInTheDocument();
    expect(screen.getByRole('main')).toBeInTheDocument();
  });
});

it('discovers pre-M2 notes without a remembered identifier', async () => {
  seed(original); render(<App />);
  expect(await screen.findByLabelText('Note title')).toHaveValue(original.title);
  expect(screen.getByRole('treeitem', { name: 'Note Persistent title' })).toBeInTheDocument();
});

it('creates a root folder, subfolder, and note inside the selected folder', async () => {
  render(<App />);
  await waitFor(() => expect(screen.queryByText('Opening library...')).not.toBeInTheDocument());
  await createThroughDialog('folder', 'HTB Academy');
  await createThroughDialog('folder', 'B01');
  await createThroughDialog('note', 'Nmap');
  expect(createFolder).toHaveBeenNthCalledWith(1, 'HTB Academy', null);
  expect(createFolder).toHaveBeenNthCalledWith(2, 'B01', 'folder-1');
  expect(createNote).toHaveBeenCalledWith(expect.objectContaining({ title: 'Nmap', folder_id: 'folder-2' }));
  expect(screen.getByRole('treeitem', { name: 'Note Nmap' })).toHaveAttribute('aria-level', '3');
});

it('drains pending saves before switching and reopens the latest document', async () => {
  const b = { ...original, id: 'b', title: 'Second note' }; seed(original, b);
  let resolve!: (note: Note) => void;
  vi.mocked(updateNote).mockImplementationOnce((id, revision, draft) => new Promise((yes) => {
    resolve = (saved) => { records.set(id, { ...saved, ...draft, revision: revision + 1 }); yes(saved); };
  }));
  render(<App />);
  const changed = [{ type: 'paragraph', content: [{ type: 'text', text: 'Latest A', styles: {} }] }];
  fireEvent.change(await screen.findByLabelText('Note editor'), { target: { value: JSON.stringify(changed) } });
  fireEvent.click(screen.getByRole('treeitem', { name: 'Note Second note' }));
  await waitFor(() => expect(updateNote).toHaveBeenCalledTimes(1));
  expect(getNote).not.toHaveBeenCalledWith('b', expect.anything());
  expect(screen.getByLabelText('Note editor')).toBeDisabled();
  await act(async () => resolve({ ...original, document_json: changed, revision: 2 }));
  await waitFor(() => expect(screen.getByLabelText('Note title')).toHaveValue('Second note'));
  fireEvent.click(screen.getByRole('treeitem', { name: 'Note Persistent title' }));
  await waitFor(() => expect(screen.getByLabelText('Note title')).toHaveValue(original.title));
  expect(screen.getByLabelText('Note editor')).toHaveValue(JSON.stringify(changed));
});

it('blocks note switching on failed save and preserves the current draft', async () => {
  seed(original, { ...original, id: 'b', title: 'Second note' });
  vi.mocked(updateNote).mockRejectedValue(new ApiError('offline', 0));
  render(<App />);
  fireEvent.change(await screen.findByLabelText('Note title'), { target: { value: 'Keep my draft' } });
  fireEvent.click(screen.getByRole('treeitem', { name: 'Note Second note' }));
  expect(await screen.findByText('Save Error')).toBeInTheDocument();
  await waitFor(() => expect(screen.getByLabelText('Note title')).toBeEnabled());
  expect(screen.getByLabelText('Note title')).toHaveValue('Keep my draft');
  expect(getNote).not.toHaveBeenCalledWith('b', expect.anything());
});

it('renames and moves the active note without leaving autosave on an obsolete revision', async () => {
  seed(original); tree.folders.push(makeFolder('f', 'Destination'));
  render(<App />); await screen.findByLabelText('Note title');
  await management('Rename');
  fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Renamed' } });
  fireEvent.click(screen.getByRole('button', { name: 'Apply' }));
  await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  expect(screen.getByLabelText('Note title')).toHaveValue('Renamed');
  await management('Move');
  fireEvent.change(screen.getByLabelText('Destination folder'), { target: { value: 'f' } });
  fireEvent.click(screen.getByRole('button', { name: 'Apply' }));
  await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  expect(updateNote).toHaveBeenLastCalledWith(original.id, 2, { folder_id: 'f' });
  expect(screen.getByLabelText('Note editor')).toHaveValue(JSON.stringify(original.document_json));
  fireEvent.change(screen.getByLabelText('Note title'), { target: { value: 'After move' } });
  await waitFor(() => expect(updateNote).toHaveBeenLastCalledWith(original.id, 3,
    expect.objectContaining({ title: 'After move' }), expect.any(AbortSignal)));
});

it('handles invalid folder moves in the dialog and supports Escape cancellation', async () => {
  tree.folders.push(makeFolder('f', 'Parent'), makeFolder('child', 'Child', 'f'));
  vi.mocked(updateFolder).mockRejectedValueOnce(new ApiError('Cannot move into a descendant', 422));
  render(<App />); await waitFor(() => expect(screen.queryByText('Opening library...')).not.toBeInTheDocument());
  fireEvent.click(screen.getByRole('treeitem', { name: 'Folder Parent' }));
  await management('Move');
  fireEvent.change(screen.getByLabelText('Destination folder'), { target: { value: 'child' } });
  fireEvent.click(screen.getByRole('button', { name: 'Apply' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('descendant');
  expect(tree.folders[0].parent_id).toBeNull();
  fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape' });
  await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  await waitFor(() => expect(screen.getByRole('button', { name: 'New folder' })).toBeEnabled());
});

it('shows exact recursive counts, cancels without deleting, then confirms only the intended folder', async () => {
  tree.folders.push(makeFolder('f', 'Delete folder'), makeFolder('keep', 'Keep folder'));
  const impact = { folder_id: 'f', name: 'Delete folder', descendant_folders: 3, notes: 7, token: 'token' };
  vi.mocked(getDeletionImpact).mockResolvedValue(impact);
  vi.mocked(deleteFolder).mockImplementation(async () => { tree.folders = tree.folders.filter((f) => f.id !== 'f'); });
  render(<App />); await waitFor(() => expect(screen.queryByText('Opening library...')).not.toBeInTheDocument());
  fireEvent.click(screen.getByRole('treeitem', { name: 'Folder Delete folder' }));
  await management('Delete');
  expect(screen.getByText('3 subfolders')).toBeInTheDocument(); expect(screen.getByText('7 notes')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
  expect(deleteFolder).not.toHaveBeenCalled();
  expect(screen.getByRole('treeitem', { name: 'Folder Delete folder' })).toBeInTheDocument();
  await management('Delete');
  fireEvent.click(screen.getByRole('button', { name: 'Delete permanently' }));
  await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  expect(deleteFolder).toHaveBeenCalledWith(impact);
  expect(screen.queryByRole('treeitem', { name: 'Folder Delete folder' })).not.toBeInTheDocument();
  expect(screen.getByRole('treeitem', { name: 'Folder Keep folder' })).toBeInTheDocument();
});

it('requires confirmation before note deletion and clears the deleted active note', async () => {
  seed(original); render(<App />); await screen.findByLabelText('Note editor');
  await management('Delete'); expect(deleteNote).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Delete permanently' }));
  await waitFor(() => expect(screen.queryByLabelText('Note editor')).not.toBeInTheDocument());
  expect(deleteNote).toHaveBeenCalledWith(original.id, 1);
  expect(window.localStorage.getItem(NOTE_ID_KEY)).toBeNull();
});

it('does not intercept editing keyboard events from BlockNote', async () => {
  seed(original); render(<App />);
  const editor = await screen.findByLabelText('Note editor');
  for (const key of ['Delete', 'F2', 'ArrowDown', 'ArrowLeft', 'Enter']) {
    const event = new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true });
    editor.dispatchEvent(event); expect(event.defaultPrevented).toBe(false);
  }
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  expect(deleteNote).not.toHaveBeenCalled();
});

it('keeps a stale deletion confirmation open without silently refreshing its intent', async () => {
  tree.folders.push(makeFolder('f', 'Changed folder'));
  vi.mocked(getDeletionImpact).mockResolvedValue({ folder_id: 'f', name: 'Changed folder', descendant_folders: 1, notes: 2, token: 'old-token' });
  vi.mocked(deleteFolder).mockRejectedValue(new ApiError('Folder contents changed. Review the deletion counts again.', 409));
  render(<App />); await waitFor(() => expect(screen.queryByText('Opening library...')).not.toBeInTheDocument());
  fireEvent.click(screen.getByRole('treeitem', { name: 'Folder Changed folder' }));
  await management('Delete');
  fireEvent.click(screen.getByRole('button', { name: 'Delete permanently' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('contents changed');
  expect(screen.getByRole('dialog')).toBeInTheDocument();
  expect(getDeletionImpact).toHaveBeenCalledTimes(1);
  expect(tree.folders).toHaveLength(1);
});

it('does not steal editor focus when autosave refreshes the directory titles', async () => {
  seed(original); render(<App />);
  const title = await screen.findByLabelText('Note title');
  act(() => title.focus());
  fireEvent.change(title, { target: { value: 'Focused title' } });
  await screen.findByRole('treeitem', { name: 'Note Focused title' });
  expect(title).toHaveFocus();
  expect(screen.getByText('Saved')).toBeInTheDocument();
});

it('autosaves native image blocks in order and reloads them from the note API', async () => {
  const document: NoteDocument = [original.document_json[0],
    { type: 'image', props: { url: '/api/assets/23d398da-6ac8-4e17-a6f0-1b8048714d2a', caption: 'Evidence', previewWidth: 420 } },
    { type: 'paragraph', content: [{ type: 'text', text: 'After screenshot', styles: { bold: true } }] }];
  seed(original);
  const app = render(<App />);
  fireEvent.change(await screen.findByRole('textbox', { name: 'Note editor' }), { target: { value: JSON.stringify(document) } });
  await waitFor(() => expect(updateNote).toHaveBeenCalledWith(original.id, 1,
    { title: original.title, document_json: document }, expect.any(AbortSignal)), { timeout: 2000 });
  await waitFor(() => expect(screen.getByText('Saved', { exact: true })).toBeInTheDocument());
  app.unmount(); render(<App />);
  expect(await screen.findByRole('textbox', { name: 'Note editor' })).toHaveValue(JSON.stringify(document));
});

it('collapses navigation without remounting the editor, losing dirty content or making requests', async () => {
  seed(original); render(<App />);
  const editor = await screen.findByLabelText('Note editor');
  const title = screen.getByLabelText('Note title');
  fireEvent.change(title, { target: { value: 'Pending edit' } });
  const reads = vi.mocked(getNote).mock.calls.length;
  const trees = vi.mocked(getTree).mock.calls.length;
  const network = vi.mocked(fetch).mock.calls.length;
  fireEvent.click(screen.getByRole('button', { name: 'Hide navigation' }));
  expect(screen.getByRole('button', { name: 'Show navigation' })).toHaveAttribute('aria-expanded', 'false');
  expect(screen.queryByRole('complementary')).not.toBeInTheDocument();
  expect(screen.getByLabelText('Note editor')).toBe(editor);
  expect(title).toHaveValue('Pending edit');
  expect(getNote).toHaveBeenCalledTimes(reads); expect(getTree).toHaveBeenCalledTimes(trees);
  expect(fetch).toHaveBeenCalledTimes(network); expect(updateNote).not.toHaveBeenCalled();
  expect(localStorage.getItem(NAVIGATION_KEY)).toBe('true');
  fireEvent.click(screen.getByRole('button', { name: 'Show navigation' }));
  expect(screen.getByRole('treeitem', { name: 'Note Persistent title' })).toHaveAttribute('data-open', 'true');
  expect(screen.getByLabelText('Note editor')).toBe(editor);
  await screen.findByText('Saved', { exact: true });
  expect(updateNote).toHaveBeenCalledWith(original.id, 1, expect.objectContaining({ title: 'Pending edit' }), expect.any(AbortSignal));
});

it('switches appearance with navigation hidden while preserving dirty content and ordinary autosave', async () => {
  seed(original); render(<App />);
  const editor = await screen.findByLabelText('Note editor');
  fireEvent.click(screen.getByRole('button', { name: 'Hide navigation' }));
  fireEvent.change(screen.getByLabelText('Note title'), { target: { value: 'Unsaved before theme switch' } });
  const reads = vi.mocked(getNote).mock.calls.length;
  const trees = vi.mocked(getTree).mock.calls.length;
  fireEvent.change(screen.getByLabelText('Appearance'), { target: { value: 'dark' } });
  expect(screen.getByLabelText('Note editor')).toBe(editor);
  expect(editor).toHaveAttribute('data-theme', 'dark');
  expect(screen.getByLabelText('Note title')).toHaveValue('Unsaved before theme switch');
  expect(getNote).toHaveBeenCalledTimes(reads); expect(getTree).toHaveBeenCalledTimes(trees);
  expect(updateNote).not.toHaveBeenCalled();
  await screen.findByText('Saved', { exact: true });
  expect(updateNote).toHaveBeenCalledOnce();
  expect(records.get(original.id)?.document_json).toEqual(original.document_json);
});

it('restores the collapsed preference on reload and can immediately show navigation', async () => {
  seed(original); localStorage.setItem(NAVIGATION_KEY, 'true'); render(<App />);
  await screen.findByLabelText('Note editor');
  expect(screen.queryByRole('complementary')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: 'Show navigation' }));
  expect(screen.getByRole('complementary')).toBeInTheDocument();
  expect(localStorage.getItem(NAVIGATION_KEY)).toBe('false');
});

it('creates a template note in the selected folder through the note API client', async () => {
  const template = { id: 'builtin:enumeration', name: 'Enumeration Notes', builtin: true, revision: 1 };
  vi.mocked(getTemplates).mockResolvedValue([template]);
  tree.folders.push(makeFolder('folder', 'Templates destination'));
  vi.mocked(createNoteFromTemplate).mockImplementation(async (_id, _rev, title, folder_id) => {
    const created = { ...original, id: 'from-template', title, folder_id };
    seed(created); return created;
  });
  render(<App />);
  await waitFor(() => expect(screen.queryByText('Opening library...')).not.toBeInTheDocument());
  fireEvent.click(screen.getByRole('treeitem', { name: 'Folder Templates destination' }));
  fireEvent.click(screen.getByRole('button', { name: 'New note' }));
  await screen.findByRole('option', { name: 'Enumeration Notes' });
  fireEvent.change(screen.getByLabelText('Note title'), { target: { value: 'Enumeration example' } });
  fireEvent.change(screen.getByLabelText('Starting content'), { target: { value: template.id } });
  fireEvent.click(screen.getByRole('button', { name: 'Create' }));
  await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  expect(createNoteFromTemplate).toHaveBeenCalledWith(template.id, 1, 'Enumeration example', 'folder');
  expect(createNote).not.toHaveBeenCalled();
  expect(screen.getByLabelText('Note editor')).toHaveValue(JSON.stringify(original.document_json));
});

it('flushes dirty edits before capturing the exact acknowledged revision as a template', async () => {
  seed(original); vi.mocked(captureTemplate).mockResolvedValue({ id: 't', name: 'My template', builtin: false, revision: 1 });
  render(<App />);
  const editor = await screen.findByLabelText('Note editor');
  fireEvent.change(screen.getByLabelText('Note title'), { target: { value: 'Confirmed before capture' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save as template' }));
  const dialog = await screen.findByRole('dialog');
  expect(updateNote).toHaveBeenCalledOnce();
  fireEvent.change(within(dialog).getByLabelText('Template name'), { target: { value: 'My template' } });
  fireEvent.click(within(dialog).getByRole('button', { name: 'Save template' }));
  await waitFor(() => expect(screen.queryByRole('dialog')).not.toBeInTheDocument());
  expect(captureTemplate).toHaveBeenCalledWith('My template', original.id, 2);
  expect(screen.getByLabelText('Note editor')).toBe(editor);
  expect(screen.getByLabelText('Note title')).toHaveValue('Confirmed before capture');
});

it('retains the template name when capture fails and preserves blank creation if listing fails', async () => {
  seed(original); vi.mocked(captureTemplate).mockRejectedValue(new ApiError('Source revision changed', 409));
  render(<App />); await screen.findByLabelText('Note editor');
  fireEvent.click(screen.getByRole('button', { name: 'Save as template' }));
  fireEvent.change(await screen.findByLabelText('Template name'), { target: { value: 'Keep this name' } });
  fireEvent.click(screen.getByRole('button', { name: 'Save template' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Source revision changed');
  expect(screen.getByLabelText('Template name')).toHaveValue('Keep this name');
  fireEvent.click(screen.getByRole('button', { name: 'Cancel' }));
  vi.mocked(getTemplates).mockRejectedValue(new Error('offline'));
  await createThroughDialog('note', 'Still blank');
  expect(createNote).toHaveBeenCalledWith(expect.objectContaining({ document_json: [{ type: 'paragraph', content: [] }] }));
});
