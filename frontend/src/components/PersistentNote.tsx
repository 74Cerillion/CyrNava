import { useImperativeHandle, useRef, useState } from 'react';
import type { Ref } from 'react';
import { useAutosave } from '../hooks/useAutosave';
import type { Note } from '../notes';
import type { EditorHandle } from './KnowledgeEditor';
import { ConflictRecovery } from './ConflictRecovery';
import { KnowledgeEditor } from './KnowledgeEditor';

export interface NoteHandle { flush: () => Promise<boolean> }
interface Props { note: Note; locked?: boolean; onSaved?: (note: Note) => void; onRecovered?: (note: Note) => void; ref?: Ref<NoteHandle> }

export function PersistentNote({ note, locked = false, onSaved, onRecovered, ref }: Props) {
  const save = useAutosave(note, onSaved);
  const [recovering, setRecovering] = useState(false);
  const [preparingRecovery, setPreparingRecovery] = useState(false);
  async function beginRecovery() {
    setPreparingRecovery(true);
    try { await editor.current?.flushUploads(); setRecovering(true); }
    finally { setPreparingRecovery(false); }
  }
  const editor = useRef<EditorHandle>(null);
  const flushSave = save.flush;
  useImperativeHandle(ref, () => ({ flush: async () => {
    if (editor.current && !await editor.current.flushUploads()) return false;
    return flushSave();
  } }), [flushSave]);
  return (
    <>
      <header>
        <label htmlFor="note-title">Note title</label>
        <input id="note-title" value={save.title} maxLength={200} disabled={locked || recovering || preparingRecovery}
          onChange={(event) => save.changeTitle(event.target.value)} />
        <p role="status" aria-live="polite">{save.status}</p>
        {save.error && <div role="alert">
          <p>{save.error.message}</p>
          {!save.error.conflict ? <button onClick={save.retry}>Retry save</button>
            : <button disabled={locked || preparingRecovery} onClick={() => void beginRecovery()}>Review conflict and recover</button>}
        </div>}
        <p className="hint">Your note stays on this computer. Wait for Saved before closing.</p>
      </header>
      {recovering && <ConflictRecovery noteId={note.id} draft={{ title: save.title, document_json: save.document }}
        onClose={() => setRecovering(false)} onReload={(saved) => { setRecovering(false); onRecovered?.(saved); }} />}
      <KnowledgeEditor ref={editor} noteId={note.id} initialDocument={note.document_json} onDocumentChange={save.changeDocument} editable={!locked && !recovering && !preparingRecovery} />
    </>
  );
}
