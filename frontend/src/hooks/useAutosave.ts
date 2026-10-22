import { useCallback, useEffect, useRef, useState } from 'react';
import { ApiError, updateNote } from '../notes';
import type { Note, NoteDocument } from '../notes';

export const AUTOSAVE_DELAY = 700;
export type SaveStatus = 'Unsaved Changes' | 'Saving...' | 'Saved' | 'Save Error';

export function useAutosave(note: Note, onSaved?: (note: Note) => void) {
  const [draft, setDraft] = useState({
    title: note.title, document_json: note.document_json, version: 0, editedAt: 0,
  });
  const [revision, setRevision] = useState(note.revision);
  const [savedVersion, setSavedVersion] = useState(0);
  const [savingVersion, setSavingVersion] = useState(-1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<{ message: string; conflict: boolean } | null>(null);
  const inFlight = useRef(false);
  const lifetime = useRef<AbortController | null>(null);

  const versions = useRef({ edited: 0, saved: 0 });
  const failure = useRef<{ message: string; conflict: boolean } | null>(null);
  const waiters = useRef<((saved: boolean) => void)[]>([]);
  const [flushRequested, setFlushRequested] = useState(false);

  const finishFlush = useCallback((saved: boolean) => {
    const pending = waiters.current.splice(0);
    for (const resolve of pending) resolve(saved);
  }, []);

  const reportError = useCallback((problem: { message: string; conflict: boolean }) => {
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
        reportError({ message: 'Use a title between 1 and 200 characters.', conflict: false });
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
        setSavedVersion(draft.version);
        versions.current.saved = draft.version;
        if (versions.current.edited === draft.version) {
          setFlushRequested(false);
          finishFlush(true);
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
  }, [draft, dirty, busy, error, note.id, revision, flushRequested, reportError, finishFlush, onSaved]);

  useEffect(() => {
    if (!dirty) return;
    const warn = (event: BeforeUnloadEvent) => {
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', warn);
    return () => window.removeEventListener('beforeunload', warn);
  }, [dirty]);

  function clearTransientError() {
    if (!failure.current?.conflict) { failure.current = null; setError(null); }
  }

  function changeTitle(title: string) {
    const version = ++versions.current.edited;
    setDraft((current) => ({ ...current, title, version, editedAt: Date.now() }));
    clearTransientError();
  }

  function changeDocument(document_json: NoteDocument) {
    const version = ++versions.current.edited;
    setDraft((current) => ({ ...current, document_json, version, editedAt: Date.now() }));
    clearTransientError();
  }

  const status: SaveStatus = error ? 'Save Error'
    : !dirty ? 'Saved'
      : busy && savingVersion === draft.version ? 'Saving...' : 'Unsaved Changes';

  return {
    title: draft.title, status, error, revision,
    changeTitle, changeDocument, flush,
    retry: clearTransientError,
  };
}
