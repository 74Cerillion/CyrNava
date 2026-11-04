import { useEffect, useImperativeHandle, useRef, useState } from 'react';
import type { Ref } from 'react';
import { schema } from './editorSchema';
import { BlockNoteView } from '@blocknote/mantine';
import { BlockNoteContext, FilePanel, FilePanelController, UploadTab, useCreateBlockNote } from '@blocknote/react';
import type { FilePanelProps } from '@blocknote/react';
import { uploadImage } from '../assets';
import type { NoteDocument } from '../notes';
import type { EditorAppearance } from '../appearanceContext';
import { cyrnavaEditorTheme } from '../cyrnavaTheme';
import '@blocknote/core/fonts/inter.css';
import '@blocknote/mantine/style.css';

function LocalImagePanel(props: FilePanelProps) {
  const [loading, setLoading] = useState(false);
  return <div aria-busy={loading}><FilePanel {...props} defaultOpenTab="Upload"
    tabs={[{ name: 'Upload', tabPanel: <UploadTab {...props} setLoading={setLoading} /> }]} /></div>;
}

function hasIncompleteImage(blocks: NoteDocument): boolean {
  return blocks.some((block) => (block.type === 'image' && (!block.props || typeof block.props !== 'object' || Array.isArray(block.props) || !block.props.url))
    || (Array.isArray(block.children) && hasIncompleteImage(block.children as NoteDocument)));
}
export interface UploadState { pending: boolean; incomplete: boolean }
export interface EditorHandle { flushUploads: () => Promise<boolean> }
interface Props {
  initialDocument: NoteDocument;
  onDocumentChange: (document: NoteDocument) => void;
  noteId: string;
  onUploadStateChange?: (state: UploadState) => void;
  editable?: boolean;
  theme?: EditorAppearance;
  ref?: Ref<EditorHandle>;
}

// Each note owns its editor, uploads and abort controller. Responses cannot reach
// another note's editor. Initial content is applied only on mount, never on save.
export function KnowledgeEditor({ initialDocument, onDocumentChange, noteId, editable = true, theme = 'light', ref, onUploadStateChange }: Props) {
  const [uploadCount, setUploadCount] = useState(0);
  const [incomplete, setIncomplete] = useState(() => hasIncompleteImage(initialDocument));
  useEffect(() => { onUploadStateChange?.({ pending: uploadCount > 0, incomplete }); }, [uploadCount, incomplete, onUploadStateChange]);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const pending = useRef(new Set<Promise<unknown>>());
  const controller = useRef<AbortController | null>(null);
  useEffect(() => {
    const lifetime = new AbortController(); controller.current = lifetime;
    return () => lifetime.abort();
  }, []);
  useEffect(() => {
    if (!uploadCount) return;
    const warn = (event: BeforeUnloadEvent) => { event.preventDefault(); event.returnValue = ''; };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [uploadCount]);


  const editor = useCreateBlockNote({
    schema,
    domAttributes: { editor: { 'aria-label': 'Note content' } },
    initialContent: initialDocument as unknown as typeof schema.PartialBlock[],
    uploadFile: (file) => {
      const lifetime = controller.current;
      if (!noteId || !lifetime || lifetime.signal.aborted) return Promise.reject(new Error('This note is no longer open.'));
      setUploadError(null);
      const task = uploadImage(noteId, file, lifetime.signal).catch((error: unknown) => {
        if (!lifetime.signal.aborted) setUploadError(error instanceof Error ? error.message : 'Image upload failed.');
        throw error;
      });
      pending.current.add(task); setUploadCount(pending.current.size);
      // Attach both handlers; avoid an unhandled rejected finally() promise.
      const finish = () => { pending.current.delete(task); if (!lifetime.signal.aborted) setUploadCount(pending.current.size); };
      void task.then(finish, finish);
      return task;
    },
    pasteHandler: ({ event, editor, defaultPasteHandler }) => {
      const files = Array.from(event.clipboardData?.files || []);
      if (!files.length) return defaultPasteHandler();
      // The installed default paste path fire-and-forgets rejected uploads.
      // Use its public uploadFile hook and editor operations, catching failures.
      const sequence = (async () => {
        let anchor = editor.getTextCursorPosition().block;
        for (const file of files) {
          if (controller.current?.signal.aborted) return;
          const [block] = editor.insertBlocks([{ type: 'image', props: { name: file.name } }], anchor, 'after');
          anchor = block;
          try {
            const url = await editor.uploadFile!(file, block.id);
            if (controller.current?.signal.aborted) return;
            if (editor.getBlock(block.id)) editor.updateBlock(block.id, { props: { url: url as string } });
          } catch { /* uploadFile displays a persistent error; keep the retry placeholder. */ }
        }
      })();
      // Include the complete multi-image sequence, not just each HTTP upload.
      // Closing freezes new input but must let an accepted paste finish.
      pending.current.add(sequence); setUploadCount(pending.current.size);
      const finishSequence = () => {
        pending.current.delete(sequence);
        if (!controller.current?.signal.aborted) setUploadCount(pending.current.size);
      };
      void sequence.then(finishSequence, finishSequence);
      return true;
    },
  });

  useImperativeHandle(ref, () => ({ flushUploads: async () => {
    let succeeded = true;
    do {
      const results = await Promise.allSettled([...pending.current]);
      succeeded = succeeded && results.every((result) => result.status === 'fulfilled');
      // BlockNote applies the returned URL after uploadFile resolves. Let its
      // change event reach React before the caller drains document autosave.
      await new Promise((resolve) => window.setTimeout(resolve, 0));
    } while (pending.current.size);
    return succeeded && !hasIncompleteImage(editor.document as unknown as NoteDocument);
  } }), [editor]);

  return (
    <section aria-label="Note editor" className="editor" onDropCapture={(event) => {
      if (event.dataTransfer.files.length) {
        event.preventDefault(); event.stopPropagation();
        setUploadError('Use Ctrl+V or the image selector to insert a local image.');
      }
    }} onErrorCapture={(event) => {
      if (event.target instanceof HTMLImageElement) setUploadError('A saved image is unavailable. Its reference is preserved; check local asset storage.');
    }}>
      <p className="hint editor-help">Use / for formatting and images. Paste a screenshot with Ctrl+V, or type /image to select a local PNG, JPEG or WebP.</p>
      {incomplete && uploadCount === 0 && <p role="alert">An image has not uploaded. Select an image or remove its empty block before closing.</p>}
      {uploadCount > 0 && <p role="status">Uploading image… Wait before closing.</p>}
      {uploadError && <div role="alert">{uploadError} <button onClick={() => setUploadError(null)}>Dismiss image error</button></div>}
      <BlockNoteContext.Provider value={{ colorSchemePreference: theme === 'cyrnava' ? 'dark' : theme }}>
      <BlockNoteView editor={editor} editable={editable} theme={theme === 'cyrnava' ? cyrnavaEditorTheme : theme} filePanel={false}
        onChange={() => {
          const document = structuredClone(editor.document) as unknown as NoteDocument;
          setIncomplete(hasIncompleteImage(document)); onDocumentChange(document);
        }}>
        <FilePanelController filePanel={LocalImagePanel} />
      </BlockNoteView>
      </BlockNoteContext.Provider>
    </section>
  );
}
