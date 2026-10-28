import { useEffect, useImperativeHandle, useRef, useState } from 'react';
import type { Ref } from 'react';
import { schema } from './editorSchema';
import { BlockNoteView } from '@blocknote/mantine';
import { FilePanel, FilePanelController, UploadTab, useCreateBlockNote } from '@blocknote/react';
import type { FilePanelProps } from '@blocknote/react';
import { uploadImage } from '../assets';
import type { NoteDocument } from '../notes';
import '@blocknote/core/fonts/inter.css';
import '@blocknote/mantine/style.css';

function LocalImagePanel(props: FilePanelProps) {
  const [loading, setLoading] = useState(false);
  return <div aria-busy={loading}><FilePanel {...props} defaultOpenTab="Upload"
    tabs={[{ name: 'Upload', tabPanel: <UploadTab {...props} setLoading={setLoading} /> }]} /></div>;
}

export interface EditorHandle { flushUploads: () => Promise<boolean> }
interface Props {
  initialDocument: NoteDocument;
  onDocumentChange: (document: NoteDocument) => void;
  noteId: string;
  editable?: boolean;
  theme?: 'light' | 'dark';
  ref?: Ref<EditorHandle>;
}

// Each note owns its editor, uploads and abort controller. Responses cannot reach
// another note's editor. Initial content is applied only on mount, never on save.
export function KnowledgeEditor({ initialDocument, onDocumentChange, noteId, editable = true, theme = 'light', ref }: Props) {
  const [uploadCount, setUploadCount] = useState(0);
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
  useImperativeHandle(ref, () => ({ flushUploads: async () => {
    let succeeded = true;
    do {
      const results = await Promise.allSettled([...pending.current]);
      succeeded = succeeded && results.every((result) => result.status === 'fulfilled');
      // BlockNote applies the returned URL after uploadFile resolves. Let its
      // change event reach React before the caller drains document autosave.
      await new Promise((resolve) => window.setTimeout(resolve, 0));
    } while (pending.current.size);
    return succeeded;
  } }), []);

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
      void (async () => {
        let anchor = editor.getTextCursorPosition().block;
        for (const file of files) {
          if (!editor.isEditable || controller.current?.signal.aborted) return;
          const [block] = editor.insertBlocks([{ type: 'image', props: { name: file.name } }], anchor, 'after');
          anchor = block;
          try {
            const url = await editor.uploadFile!(file, block.id);
            if (controller.current?.signal.aborted) return;
            if (editor.getBlock(block.id)) editor.updateBlock(block.id, { props: { url: url as string } });
          } catch { /* uploadFile displays a persistent error; keep the retry placeholder. */ }
        }
      })();
      return true;
    },
  });

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
      {uploadCount > 0 && <p role="status">Uploading image… Wait before closing.</p>}
      {uploadError && <div role="alert">{uploadError} <button onClick={() => setUploadError(null)}>Dismiss image error</button></div>}
      <BlockNoteView editor={editor} editable={editable} theme={theme} filePanel={false}
        onChange={() => onDocumentChange(structuredClone(editor.document) as unknown as NoteDocument)}>
        <FilePanelController filePanel={LocalImagePanel} />
      </BlockNoteView>
    </section>
  );
}
