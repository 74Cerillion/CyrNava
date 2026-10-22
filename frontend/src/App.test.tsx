import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App, { NOTE_ID_KEY } from './App';
import { ApiError, createNote, deleteNote, getNote, updateNote } from './notes';
import type { Note, NoteDocument } from './notes';
import { createFolder, deleteFolder, getDeletionImpact, getTree, updateFolder } from './library';
import type { DirectoryData, Folder } from './library';

vi.mock('./notes', async (original) => ({
  ...await original<typeof import('./notes')>(), createNote: vi.fn(), getNote: vi.fn(), updateNote: vi.fn(), deleteNote: vi.fn(),
}));
vi.mock('./library', () => ({ getTree: vi.fn(), createFolder: vi.fn(), updateFolder: vi.fn(), deleteFolder: vi.fn(), getDeletionImpact: vi.fn() }));
vi.mock('./components/KnowledgeEditor', () => ({
  KnowledgeEditor: ({ initialDocument, onDocumentChange, editable }: {
    initialDocument: NoteDocument; onDocumentChange: (value: NoteDocument) => void; editable: boolean;
  }) => <textarea aria-label="Note editor" disabled={!editable} defaultValue={JSON.stringify(initialDocument)}
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
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => ({ status: 'ok' }) }));
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
