import { useImperativeHandle } from 'react';
import type { Ref } from 'react';
import { useAutosave } from '../hooks/useAutosave';
import type { Note } from '../notes';
import { KnowledgeEditor } from './KnowledgeEditor';

export interface NoteHandle { flush: () => Promise<boolean> }
interface Props { note: Note; locked?: boolean; onSaved?: (note: Note) => void; ref?: Ref<NoteHandle> }

export function PersistentNote({ note, locked = false, onSaved, ref }: Props) {
  const save = useAutosave(note, onSaved);
  useImperativeHandle(ref, () => ({ flush: save.flush }), [save.flush]);
  return (
    <>
      <header>
        <label htmlFor="note-title">Note title</label>
        <input id="note-title" value={save.title} maxLength={200} disabled={locked}
          onChange={(event) => save.changeTitle(event.target.value)} />
        <p role="status" aria-live="polite">{save.status}</p>
        {save.error && <div role="alert">
          <p>{save.error.message}</p>
          {!save.error.conflict && <button onClick={save.retry}>Retry save</button>}
        </div>}
        <p className="hint">Your note stays on this computer. Wait for Saved before closing.</p>
      </header>
      <KnowledgeEditor initialDocument={note.document_json} onDocumentChange={save.changeDocument} editable={!locked} />
    </>
  );
}
