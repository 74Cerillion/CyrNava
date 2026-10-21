import { useEffect, useState } from 'react';
import { PersistentNote } from './components/PersistentNote';
import { createEmptyDocument } from './components/editorDocument';
import { createNote, getNote } from './notes';
import type { Note } from './notes';

export const NOTE_ID_KEY = 'engage.note-id.v1';
type Health = 'checking' | 'online' | 'offline';

export default function App() {
  const [health, setHealth] = useState<Health>('checking');
  const [note, setNote] = useState<Note | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [initialTitle, setInitialTitle] = useState('My first note');
  const [loadError, setLoadError] = useState<string | null>(null);
  const [pointerError, setPointerError] = useState<string | null>(null);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const [rememberedNote, setRememberedNote] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 3000);
    let active = true;
    async function checkHealth() {
      try {
        const response = await fetch('/api/health', { signal: controller.signal });
        if (!response.ok) throw new Error('Health request failed');
        const data: unknown = await response.json();
        if (!data || typeof data !== 'object' || !('status' in data) || data.status !== 'ok') {
          throw new Error('Unexpected health response');
        }
        if (active) setHealth('online');
      } catch {
        if (active) setHealth('offline');
      } finally {
        window.clearTimeout(timeout);
      }
    }
    void checkHealth();
    return () => { active = false; window.clearTimeout(timeout); controller.abort(); };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const id = window.localStorage.getItem(NOTE_ID_KEY);
        if (!controller.signal.aborted) setRememberedNote(Boolean(id));
        if (id) {
          const saved = await getNote(id, controller.signal);
          if (!controller.signal.aborted) setNote(saved);
        }
      } catch (failure) {
        if (!controller.signal.aborted) setLoadError(failure instanceof Error ? failure.message : 'Cannot open note.');
      } finally {
        if (!controller.signal.aborted) setLoading(false);
      }
    }
    void load();
    return () => controller.abort();
  }, [loadAttempt]);

  async function createInitialNote() {
    setCreating(true);
    setLoadError(null);
    try {
      const saved = await createNote({ title: initialTitle, document_json: createEmptyDocument() });
      setNote(saved);
      try {
        window.localStorage.setItem(NOTE_ID_KEY, saved.id);
      } catch {
        setPointerError(`Note ${saved.id} was created, but browser storage failed. Keep this ID; automatic reopening is unavailable.`);
      }
    } catch (failure) {
      setLoadError(failure instanceof Error ? failure.message : 'Cannot create note.');
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="workspace">
      <aside className="sidebar" aria-label="Workspace navigation">
        <p className="eyebrow">LOCAL WORKSPACE · M1</p>
        <h1>ENGAGE</h1>
        <nav aria-label="Notes"><a href="#note" aria-current="page">My note</a></nav>
        <p className="status" role="status">Backend at page load: {health}</p>
        <p className="hint">One note, saved in a local SQLite database.</p>
      </aside>
      <main id="note">
        {loading ? <p role="status">Opening note...</p> : note ? <>
          {pointerError && <p role="alert">{pointerError}</p>}
          <PersistentNote key={note.id} note={note} />
        </> : <header>
          <h2>Your first note</h2>
          <p>Create a note to start saving rich text locally.</p>
          {loadError && <p role="alert">{loadError}</p>}
          {loadError && rememberedNote ?
            <button onClick={() => { setLoading(true); setLoadError(null); setLoadAttempt((n) => n + 1); }}>Retry opening note</button>
            : <form onSubmit={(event) => { event.preventDefault(); void createInitialNote(); }}>
              <label htmlFor="initial-title">Note title</label>
              <input id="initial-title" value={initialTitle} maxLength={200} required
                onChange={(event) => setInitialTitle(event.target.value)} />
              <button disabled={creating || !initialTitle.trim()}>{creating ? 'Creating...' : 'Create note'}</button>
            </form>}
        </header>}
      </main>
    </div>
  );
}
