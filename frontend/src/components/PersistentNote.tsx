import { useAutosave } from '../hooks/useAutosave';
import type { Note } from '../notes';
import { KnowledgeEditor } from './KnowledgeEditor';

export function PersistentNote({ note }: { note: Note }) {
  const save = useAutosave(note);
  return (
    <>
      <header>
        <label htmlFor="note-title">Note title</label>
        <input id="note-title" value={save.title} maxLength={200}
          onChange={(event) => save.changeTitle(event.target.value)} />
        <p role="status" aria-live="polite">{save.status}</p>
        {save.error && <div role="alert">
          <p>{save.error.message}</p>
          {!save.error.conflict && <button onClick={save.retry}>Retry save</button>}
        </div>}
        <p className="hint">Your note stays on this computer. Wait for Saved before closing.</p>
      </header>
      <KnowledgeEditor initialDocument={note.document_json} onDocumentChange={save.changeDocument} />
    </>
  );
}
