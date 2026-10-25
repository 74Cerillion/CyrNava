import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError, updateNote } from '../notes';
import type { Note, NoteDocument } from '../notes';
import { storeDraft, removeAcknowledgedDraft } from '../drafts';
import type { RecoveryDraft } from '../drafts';

export const AUTOSAVE_DELAY = 700;
export type SaveStatus = 'Unsaved Changes' | 'Saving...' | 'Saved' | 'Save Error';

export function useAutosave(note: Note, onSaved?: (note: Note) => void, recovered?: RecoveryDraft) {
  const initial = recovered || note;
  const initialError = recovered && recovered.base_revision !== note.revision
    ? { message: 'The recovered draft is based on an older revision. Review both versions before reopening.', conflict: true } : null;
  const [draft, setDraft] = useState({
    title: initial.title, document_json: initial.document_json, version: recovered ? 1 : 0, editedAt: 0,
  });
  const [revision, setRevision] = useState(recovered?.base_revision || note.revision);
  const acknowledgedRevision = useRef(recovered?.base_revision || note.revision);
  const [savedVersion, setSavedVersion] = useState(0);
  const [savingVersion, setSavingVersion] = useState(-1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<{ message: string; conflict: boolean; validation?: boolean } | null>(initialError);
  const [recoveryError, setRecoveryError] = useState<string | null>(null);
  const inFlight = useRef(false);
  const lifetime = useRef<AbortController | null>(null);

  const currentDraft = useRef({ title: initial.title, document_json: initial.document_json, json: JSON.stringify(initial.document_json) });
  const versions = useRef({ edited: recovered ? 1 : 0, saved: 0 });
  const localRecord = useRef<RecoveryDraft | null>(recovered || null);
  const sourceRecord = useRef(recovered);
  const failure = useRef<{ message: string; conflict: boolean; validation?: boolean } | null>(initialError);
  const waiters = useRef<((saved: boolean) => void)[]>([]);
  const [flushRequested, setFlushRequested] = useState(false);

  const finishFlush = useCallback((saved: boolean) => {
    const pending = waiters.current.splice(0);
    for (const resolve of pending) resolve(saved);
  }, []);

  const reportError = useCallback((problem: { message: string; conflict: boolean; validation?: boolean }) => {
    failure.current = problem;
    setError(problem);
    setFlushRequested(false);
    finishFlush(false);
  }, [finishFlush]);

  // Navigation asks the same serial saver to drain, bypassing only its debounce.
  const flush = useCallback((): Promise<boolean> => {
    if (failure.current) return Promise.resolve(false);
    if (versions.current.edited === versions.current.saved) return Promise.resolve(true);
    setFlushRequested(true);
    return new Promise((resolve) => waiters.current.push(resolve));
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    lifetime.current = controller;
    return () => { controller.abort(); finishFlush(false); };
  }, [finishFlush]);

  const dirty = draft.version !== savedVersion;

  useEffect(() => {
    if (!dirty || busy || error) return;
    // Time since the latest edit, not since the previous request completed.
    const remaining = flushRequested ? 0 : Math.max(0, draft.editedAt + AUTOSAVE_DELAY - Date.now());
    const timer = window.setTimeout(async () => {
      const controller = lifetime.current;
      if (!controller || controller.signal.aborted || inFlight.current) return;
      if (!draft.title.trim() || draft.title.trim().length > 200) {
        reportError({ message: 'Use a title between 1 and 200 characters.', conflict: false, validation: true });
        return;
      }
      inFlight.current = true;
      setBusy(true);
      setSavingVersion(draft.version);
      try {
        const saved = await updateNote(note.id, revision, {
          title: draft.title, document_json: draft.document_json,
        }, controller.signal);
        if (controller.signal.aborted) return;
        // Acknowledges ONLY this snapshot. Never replace the current draft with
        // the response: the user may have typed newer content while awaiting it.
        setRevision(saved.revision);
        acknowledgedRevision.current = saved.revision;
        setSavedVersion(draft.version);
        versions.current.saved = draft.version;
        if (versions.current.edited === draft.version) {
          try {
            if (localRecord.current) removeAcknowledgedDraft(localRecord.current);
            if (sourceRecord.current) removeAcknowledgedDraft(sourceRecord.current);
            localRecord.current = null; sourceRecord.current = undefined;
            setRecoveryError(null);
          } catch { setRecoveryError('Saved to SQLite, but browser recovery storage could not be cleared. A duplicate draft may be offered next time.'); }
          setFlushRequested(false);
          finishFlush(true);
        } else {
          try {
            localRecord.current = storeDraft(note, currentDraft.current, saved.revision);
            setRecoveryError(null);
          } catch { setRecoveryError('Browser draft recovery is unavailable. Keep this tab open until Saved; unconfirmed edits may be lost if you close it.'); }
        }
        onSaved?.(saved);
      } catch (failure) {
        if (controller.signal.aborted) return;
        reportError({
          message: failure instanceof Error ? failure.message : 'Saving failed. Your edits are still here.',
          conflict: failure instanceof ApiError && failure.status === 409,
        });
      } finally {
        inFlight.current = false;
        if (!controller.signal.aborted) setBusy(false);
      }
    }, remaining);
    return () => window.clearTimeout(timer);
  }, [draft, dirty, busy, error, note, revision, flushRequested, reportError, finishFlush, onSaved]);

  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [dirty]);

  useEffect(() => {
    const background = () => { if (document.visibilityState === 'hidden') void flush(); };
    document.addEventListener('visibilitychange', background);
    return () => document.removeEventListener('visibilitychange', background);
  }, [flush]);

  function retainDraft() {
    try {
      localRecord.current = storeDraft(note, currentDraft.current, acknowledgedRevision.current);
      setRecoveryError(null);
    } catch { setRecoveryError('Browser draft recovery is unavailable. Keep this tab open until Saved; unconfirmed edits may be lost if you close it.'); }
  }

  function clearTransientError() {
    if (!failure.current?.conflict) { failure.current = null; setError(null); }
  }

  function changeTitle(title: string) {
    if (currentDraft.current.title === title) return;
    currentDraft.current.title = title;
    retainDraft();
    const version = ++versions.current.edited;
    setDraft((current) => ({ ...current, title, version, editedAt: Date.now() }));
    if (failure.current?.validation) clearTransientError();
  }

  function changeDocument(document_json: NoteDocument) {
    const json = JSON.stringify(document_json);
    if (currentDraft.current.json === json) return;
    currentDraft.current.json = json;
    currentDraft.current.document_json = document_json;
    retainDraft();
    const version = ++versions.current.edited;
    setDraft((current) => ({ ...current, document_json, version, editedAt: Date.now() }));
    if (failure.current?.validation) clearTransientError();
  }

  const status: SaveStatus = error ? 'Save Error'
    : !dirty ? 'Saved'
      : busy && savingVersion === draft.version ? 'Saving...' : 'Unsaved Changes';

  return {
    title: draft.title, document: draft.document_json, status, error, recoveryError, revision,
    changeTitle, changeDocument, flush,
    retry: clearTransientError,
  };
}
