import { useImperativeHandle, useRef, useState } from 'react';
import type { Ref } from 'react';
import { useAutosave } from '../hooks/useAutosave';
import type { Note } from '../notes';
import type { EditorHandle } from './KnowledgeEditor';
import { ConflictRecovery } from './ConflictRecovery';
import { KnowledgeEditor } from './KnowledgeEditor';
import { deferDraft, downloadDraft, findDrafts } from '../drafts';
import type { RecoveryDraft } from '../drafts';

export interface NoteHandle { flush: () => Promise<boolean> }
interface Props { note: Note; locked?: boolean; onSaved?: (note: Note) => void; onRecovered?: (note: Note) => void; ref?: Ref<NoteHandle>; recovered?: RecoveryDraft }

export function PersistentNote({ ref, ...props }: Props) {
  const [recovery] = useState(() => {
    try { return { drafts: findDrafts(props.note.id), error: null }; }
    catch { return { drafts: [], error: 'Browser recovery storage could not be read. Stored records have been left intact.' }; }
  });
  const [choice, setChoice] = useState<RecoveryDraft | null | undefined>(undefined);
  const editor = useRef<NoteHandle>(null);
  const pending = recovery.drafts.length > 0 && choice === undefined;
  useImperativeHandle(ref, () => ({ flush: () => editor.current?.flush() || Promise.resolve(false) }), []);
  if (pending) return <section aria-label="Draft recovery">
    <h2>Recover unsaved edits</h2>
    <p>SQLite still holds the saved note. These browser drafts may contain unconfirmed edits from this or another tab. Nothing is overwritten until you choose a draft and it saves with its original revision.</p>
    {recovery.drafts.map((draft) => <article key={draft.token}>
      <p><strong>{draft.title}</strong> — base revision {draft.base_revision}, {draft.edited_at}</p>
      <details><summary>Inspect draft JSON</summary><pre className="recovery-document">{JSON.stringify(draft.document_json, null, 2)}</pre></details>
      <button disabled={props.locked} onClick={() => setChoice(draft)}>Recover draft</button>
      <button onClick={() => downloadDraft(draft)}>Download draft</button>
    </article>)}
    <button disabled={props.locked} onClick={() => { recovery.drafts.forEach(deferDraft); setChoice(null); }}>Continue with saved note (retain drafts)</button>
  </section>;
  return <>{recovery.error && <p role="alert">{recovery.error}</p>}
    <NoteEditor {...props} ref={editor} recovered={choice || undefined} onRecovered={(saved) => {
      if (choice) deferDraft(choice);
      props.onRecovered?.(saved);
    }} /></>;
}

function NoteEditor({ note, locked = false, onSaved, onRecovered, ref, recovered }: Props) {
  const save = useAutosave(note, onSaved, recovered);
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
        <p className="save-state" data-state={save.status} role="status" aria-live="polite" aria-atomic="true">{save.status}</p>
        {save.recoveryError && <p role="alert">{save.recoveryError}</p>}
        {save.error && <div role="alert">
          <p>{save.error.message}</p>
          {!save.error.conflict ? <button onClick={save.retry}>Retry save</button>
            : <button disabled={locked || preparingRecovery} onClick={() => void beginRecovery()}>Review conflict and recover</button>}
        </div>}
        <p className="hint">Your note stays on this computer. Wait for uploads and Saved before closing.</p>
      </header>
      {recovering && <ConflictRecovery noteId={note.id} draft={{ title: save.title, document_json: save.document }}
        onClose={() => setRecovering(false)} onReload={(saved) => { setRecovering(false); onRecovered?.(saved); }} />}
      <KnowledgeEditor ref={editor} noteId={note.id} initialDocument={recovered?.document_json || note.document_json} onDocumentChange={save.changeDocument} editable={!locked && !recovering && !preparingRecovery} />
    </>
  );
}
