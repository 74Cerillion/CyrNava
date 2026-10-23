import { useEffect, useRef, useState } from 'react';
import { getNote } from '../notes';
import type { Note, NoteDraft } from '../notes';

interface Props {
  noteId: string;
  draft: NoteDraft;
  onClose: () => void;
  onReload: (note: Note) => void;
}

// Recovery reads never write. Reload requires the user to retain a recovery
// file containing BOTH versions; no force-save or silent merge is offered.
export function ConflictRecovery({ noteId, draft, onClose, onReload }: Props) {
  const dialog = useRef<HTMLDialogElement>(null);
  const lifetime = useRef<AbortController | null>(null);
  const [saved, setSaved] = useState<Note | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloaded, setDownloaded] = useState(false);
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const controller = new AbortController(); lifetime.current = controller;
    const previous = document.activeElement as HTMLElement | null;
    const modal = dialog.current!; modal.showModal();
    void getNote(noteId, controller.signal).then((note) => {
      if (!controller.signal.aborted) setSaved(note);
    }).catch(() => { if (!controller.signal.aborted) setError('Cannot read the saved version. Keep this draft open, restore the backend, then reopen recovery.'); });
    return () => { controller.abort(); modal.close(); if (previous?.isConnected) previous.focus(); };
  }, [noteId]);

  function download() {
    const bundle = { recovery_format: 1, note_id: noteId, local_draft: draft, saved_note: saved };
    const url = URL.createObjectURL(new Blob([JSON.stringify(bundle, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a'); link.href = url; link.download = `engage-conflict-${noteId}.json`;
    link.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    setDownloaded(true);
  }
  async function reload() {
    if (!saved || !confirmed || !downloaded || busy) return;
    setBusy(true); setError(null);
    try {
      const latest = await getNote(noteId, lifetime.current!.signal);
      if (!lifetime.current?.signal.aborted) onReload(latest);
    } catch { if (!lifetime.current?.signal.aborted) setError('Reopening failed. Your local draft is still open. Restore the backend and try again.'); }
    finally { if (!lifetime.current?.signal.aborted) setBusy(false); }
  }
  return <dialog ref={dialog} aria-labelledby="conflict-title"
    onCancel={(event) => { event.preventDefault(); if (!busy) onClose(); }}>
    <h2 id="conflict-title">Recover a revision conflict</h2>
    <p>Your local draft stays open. The saved note changed elsewhere. Review it and retain both versions before reopening.</p>
    {saved ? <>
      <p>Saved title: <strong>{saved.title}</strong>. Revision {saved.revision}.</p>
      <details><summary>Inspect saved document JSON</summary><pre className="recovery-document">{JSON.stringify(saved.document_json, null, 2)}</pre></details>
      <p>Local draft title: <strong>{draft.title}</strong></p>
      <button disabled={busy} onClick={download}>Download both versions</button>
      {downloaded && <label><input type="checkbox" checked={confirmed} disabled={busy}
        onChange={(event) => setConfirmed(event.target.checked)} /> I verified that the recovery file was saved. Reopening will replace this editor with the saved version.</label>}
    </> : !error && <p role="status">Reading the saved version...</p>}
    {error && <p role="alert">{error}</p>}
    <div className="dialog-actions">
      <button className="secondary" disabled={busy} onClick={onClose}>Keep editing this draft</button>
      <button disabled={!saved || !confirmed || !downloaded || busy} onClick={() => void reload()}>{busy ? 'Reopening...' : 'Reopen saved version'}</button>
    </div>
  </dialog>;
}
