import { act, fireEvent, render, screen } from '@testing-library/react';
import { createRef } from 'react';
import { beforeEach, expect, it, vi } from 'vitest';
import { useCreateBlockNote } from '@blocknote/react';
import { uploadImage } from '../assets';
import { KnowledgeEditor } from './KnowledgeEditor';
import type { EditorHandle } from './KnowledgeEditor';
import type { NoteDocument } from '../notes';

const snapshot: NoteDocument = [{ type: 'heading', id: 'heading-1', props: { level: 1 },
  content: [{ type: 'text', text: 'Formatted', styles: { bold: true } }], children: [] }];
vi.mock('../assets', () => ({ uploadImage: vi.fn() }));
vi.mock('@blocknote/react', () => ({ useCreateBlockNote: vi.fn(), FilePanelController: () => null, FilePanel: () => null, UploadTab: () => null }));
vi.mock('@blocknote/mantine', () => ({
  BlockNoteView: ({ onChange }: { onChange: () => void }) => <><button onClick={onChange}>Editor change</button><img src="/api/assets/missing" alt="Saved evidence" /></>,
}));
// These mock only the editor's public boundary; real BlockNote is checked in browser.
let options: Parameters<typeof useCreateBlockNote>[0];
let current: NoteDocument;
const updateBlock = vi.fn();
const editor = { get document() { return current; }, isEditable: true,
  getTextCursorPosition: () => ({ block: { id: 'heading-1' } }),
  insertBlocks: vi.fn(() => [{ id: 'upload-block' }]), getBlock: () => ({ id: 'upload-block' }), updateBlock,
  uploadFile: (file: File) => options!.uploadFile!(file),
};
const initial: NoteDocument = [{ type: 'paragraph', content: [] }];
const file = new File(['image'], 'screen.png', { type: 'image/png' });
const url = '/api/assets/23d398da-6ac8-4e17-a6f0-1b8048714d2a';
beforeEach(() => {
  vi.resetAllMocks(); current = structuredClone(snapshot);
  vi.mocked(useCreateBlockNote).mockImplementation((config) => { options = config; return editor as unknown as ReturnType<typeof useCreateBlockNote>; });
  vi.mocked(uploadImage).mockResolvedValue(url);
});
function paste(files: File[]) {
  return options!.pasteHandler!({ event: { clipboardData: { files } } as unknown as ClipboardEvent,
    editor: editor as unknown as ReturnType<typeof useCreateBlockNote>, defaultPasteHandler: () => false });
}
it('hydrates native JSON and emits an independent document snapshot', () => {
  const onChange = vi.fn(); render(<KnowledgeEditor noteId="A" initialDocument={initial} onDocumentChange={onChange} />);
  expect(useCreateBlockNote).toHaveBeenCalledWith(expect.objectContaining({ initialContent: initial, uploadFile: expect.any(Function) }));
  fireEvent.click(screen.getByRole('button', { name: 'Editor change' }));
  expect(onChange).toHaveBeenCalledWith(snapshot);
  expect(onChange.mock.calls[0][0]).not.toBe(snapshot);
});
it('the file-picker upload hook returns a persistent URL owned by this note', async () => {
  render(<KnowledgeEditor noteId="A" initialDocument={initial} onDocumentChange={vi.fn()} />);
  let result: unknown;
  await act(async () => { result = await options!.uploadFile!(file); });
  expect(result).toBe(url);
  expect(uploadImage).toHaveBeenCalledWith('A', file, expect.any(AbortSignal));
});
it('clipboard insertion uses uploadFile and updates only its original placeholder', async () => {
  render(<KnowledgeEditor noteId="A" initialDocument={initial} onDocumentChange={vi.fn()} />);
  await act(async () => { expect(paste([file])).toBe(true); });
  expect(editor.insertBlocks).toHaveBeenCalledWith([{ type: 'image', props: { name: 'screen.png' } }], { id: 'heading-1' }, 'after');
  expect(updateBlock).toHaveBeenCalledWith('upload-block', { props: { url } });
});
it('loads and preserves image position, caption and formatting in emitted autosave JSON', () => {
  current = [snapshot[0], { type: 'image', props: { url, caption: 'Local evidence', previewWidth: 420 } }, { type: 'paragraph', content: [] }];
  const onChange = vi.fn(); render(<KnowledgeEditor noteId="A" initialDocument={current} onDocumentChange={onChange} />);
  expect(options!.initialContent).toEqual(current);
  fireEvent.click(screen.getByRole('button', { name: 'Editor change' }));
  expect(onChange).toHaveBeenCalledWith(current);
  expect(onChange.mock.calls[0][0][1].props.url).toBe(url);
});
it('failed clipboard upload reports feedback and never inserts a permanent URL', async () => {
  vi.mocked(uploadImage).mockRejectedValue(new Error('Malformed image'));
  render(<KnowledgeEditor noteId="A" initialDocument={initial} onDocumentChange={vi.fn()} />);
  await act(async () => { paste([file]); });
  expect(screen.getByRole('alert')).toHaveTextContent('Malformed image');
  expect(updateBlock).not.toHaveBeenCalled();
  expect(current).toEqual(snapshot);
});
it('navigation waits for the in-flight upload and editor URL application', async () => {
  let finish!: (value: string) => void;
  vi.mocked(uploadImage).mockReturnValue(new Promise((resolve) => { finish = resolve; }));
  const ref = createRef<EditorHandle>();
  render(<KnowledgeEditor ref={ref} noteId="A" initialDocument={initial} onDocumentChange={vi.fn()} />);
  act(() => { paste([file]); });
  expect(screen.getByRole('status')).toHaveTextContent('Uploading image');
  const done = vi.fn(); const flush = ref.current!.flushUploads().then(done);
  expect(done).not.toHaveBeenCalled();
  await act(async () => { finish(url); await flush; });
  expect(updateBlock).toHaveBeenCalledWith('upload-block', { props: { url } });
  expect(done).toHaveBeenCalledWith(true);
});
it('unmount aborts the old note upload and cannot insert its response into a new note', async () => {
  let finish!: (value: string) => void;
  vi.mocked(uploadImage).mockReturnValue(new Promise((resolve) => { finish = resolve; }));
  const first = render(<KnowledgeEditor noteId="A" initialDocument={initial} onDocumentChange={vi.fn()} />);
  act(() => { paste([file]); });
  const signal = vi.mocked(uploadImage).mock.calls[0][2];
  first.unmount();
  render(<KnowledgeEditor noteId="B" initialDocument={initial} onDocumentChange={vi.fn()} />);
  expect(signal.aborted).toBe(true);
  await act(async () => { finish(url); });
  expect(updateBlock).not.toHaveBeenCalled();
});
it('missing asset feedback preserves the document and does not crash the editor', () => {
  render(<KnowledgeEditor noteId="A" initialDocument={initial} onDocumentChange={vi.fn()} />);
  fireEvent.error(screen.getByAltText('Saved evidence'));
  expect(screen.getByRole('alert')).toHaveTextContent('saved image is unavailable');
  expect(screen.getByRole('button', { name: 'Editor change' })).toBeInTheDocument();
});

it('delegates ordinary text paste and disables the optional file-drop path', () => {
  render(<KnowledgeEditor noteId="A" initialDocument={initial} onDocumentChange={vi.fn()} />);
  expect(paste([])).toBe(false);
  fireEvent.drop(screen.getByRole('region', { name: 'Note editor' }), { dataTransfer: { files: [file] } });
  expect(screen.getByRole('alert')).toHaveTextContent('Ctrl+V or the image selector');
  expect(uploadImage).not.toHaveBeenCalled();
});
