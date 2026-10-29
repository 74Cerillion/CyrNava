import { version } from '../package.json';
import { useCallback, useEffect, useRef, useState } from 'react';
import { PersistentNote } from './components/PersistentNote';
import type { NoteHandle } from './components/PersistentNote';
import { createEmptyDocument } from './components/editorDocument';
import { DirectoryTree } from './components/DirectoryTree';
import type { ManagementAction } from './components/DirectoryTree';
import { ManagementDialog } from './components/ManagementDialog';
import type { DialogState } from './components/ManagementDialog';
import { createNote, createNoteFromTemplate, deleteNote, getNote, updateNote } from './notes';
import type { Note } from './notes';
import { createFolder, deleteFolder, getDeletionImpact, getTree, updateFolder } from './library';
import type { DirectoryData } from './library';
import { ancestorIds, itemKey } from './tree';
import type { TreeItem } from './tree';
import { useLifecycle } from './hooks/useLifecycle';
import { captureTemplate } from './templates';
import type { TemplateSummary } from './templates';
import { TemplateManager } from './components/TemplateManager';
import { useComputedColorScheme } from '@mantine/core';
import { AppearanceControl, AppearanceProvider } from './appearance';
import { useCyrnavaTheme } from './appearanceContext';
import { Icon } from './components/Icon';

// Compatibility identifiers preserve existing preferred notes, drafts and settings.
export const NOTE_ID_KEY = 'engage.note-id.v1';
export const NAVIGATION_KEY = 'engage.navigation-collapsed.v1';
const emptyLibrary: DirectoryData = { folders: [], notes: [] };
type Health = 'checking' | 'online' | 'offline';

export default function App() {
  return <AppearanceProvider><Workspace /></AppearanceProvider>;
}

function Workspace() {
  const theme = useComputedColorScheme('light', { getInitialValueInEffect: false });
  const { cyrnava } = useCyrnavaTheme();
  const [navigationCollapsed, setNavigationCollapsed] = useState(() => {
    try { return localStorage.getItem(NAVIGATION_KEY) === 'true'; } catch { return false; }
  });
  const lifecycleProblem = useLifecycle();
  const [health, setHealth] = useState<Health>('checking');
  const [data, setData] = useState<DirectoryData>(emptyLibrary);
  const [note, setNote] = useState<Note | null>(null);
  const [editorEpoch, setEditorEpoch] = useState(0);
  const [selected, setSelected] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(new Set<string>());
  const [loading, setLoading] = useState(true);
  const [working, setWorking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dialog, setDialog] = useState<DialogState | null>(null);
  const [templateManager, setTemplateManager] = useState(false);
  const [templateNotice, setTemplateNotice] = useState<string | null>(null);
  const [loadAttempt, setLoadAttempt] = useState(0);
  const editor = useRef<NoteHandle>(null);
  const operation = useRef(false);
  const treeRequest = useRef(0);
  const lifetime = useRef<AbortController | null>(null);

  const reveal = useCallback((tree: DirectoryData, folder: string | null) => {
    setExpanded((current) => new Set([...current, ...ancestorIds(tree, folder)]));
  }, []);
  const remember = useCallback((id: string | null) => {
    try { if (id) window.localStorage.setItem(NOTE_ID_KEY, id); else window.localStorage.removeItem(NOTE_ID_KEY); }
    catch { /* The tree remains authoritative and permits reopening every note. */ }
  }, []);

  const refreshTree = useCallback(async () => {
    const generation = ++treeRequest.current;
    const tree = await getTree(lifetime.current?.signal);
    if (!lifetime.current?.signal.aborted && generation === treeRequest.current) setData(tree);
    return tree;
  }, []);
  const noteSaved = useCallback(() => {
    setError(null);
    void refreshTree().catch((failure) => {
      if (!lifetime.current?.signal.aborted) setError(`Note saved, but the library refresh failed: ${failure instanceof Error ? failure.message : 'unknown error'}`);
    });
  }, [refreshTree]);

  useEffect(() => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 3000);
    let active = true;
    async function checkHealth() {
      try {
        const response = await fetch('/api/health', { signal: controller.signal });
        if (!response.ok) throw new Error('Health request failed');
        const body: unknown = await response.json();
        if (!body || typeof body !== 'object' || !('status' in body) || body.status !== 'ok') throw new Error('Unexpected health response');
        if (active) setHealth('online');
      } catch { if (active) setHealth('offline'); }
      finally { window.clearTimeout(timeout); }
    }
    void checkHealth();
    return () => { active = false; controller.abort(); window.clearTimeout(timeout); };
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    lifetime.current = controller;
    async function load() {
      try {
        const tree = await getTree(controller.signal);
        if (controller.signal.aborted) return;
        setData(tree);
        let remembered: string | null = null;
        try { remembered = window.localStorage.getItem(NOTE_ID_KEY); } catch { /* Discovery does not require browser storage. */ }
        const summary = tree.notes.find((item) => item.id === remembered) || tree.notes[0];
        if (summary) {
          const saved = await getNote(summary.id, controller.signal);
          if (controller.signal.aborted) return;
          setNote(saved); setSelected(`note:${saved.id}`); reveal(tree, saved.folder_id); remember(saved.id);
        }
      } catch (failure) {
        if (!controller.signal.aborted) setError(failure instanceof Error ? failure.message : 'Cannot open library.');
      } finally { if (!controller.signal.aborted) setLoading(false); }
    }
    void load();
    return () => controller.abort();
  }, [loadAttempt, reveal, remember]);

  async function perform(action: () => Promise<void>) {
    if (operation.current) return;
    operation.current = true; setWorking(true); setError(null); setTemplateNotice(null);
    try {
      if (editor.current && !await editor.current.flush()) throw new Error('Cannot leave this note until pending edits and draft recovery are resolved. Your draft remains available; resolve the save error or recovery choice first.');
      await action();
    } catch (failure) {
      if (!lifetime.current?.signal.aborted) setError(failure instanceof Error ? failure.message : 'Operation failed.');
    } finally { operation.current = false; if (!lifetime.current?.signal.aborted) setWorking(false); }
  }

  function selectItem(item: TreeItem) {
    if (working || dialog || templateManager) return;
    if (item.kind === 'folder') { setSelected(itemKey(item)); return; }
    if (note?.id === item.value.id) { setSelected(itemKey(item)); return; }
    void perform(async () => {
      const saved = await getNote(item.value.id, lifetime.current?.signal);
      if (lifetime.current?.signal.aborted) return;
      setNote(saved); setSelected(itemKey(item)); reveal(data, saved.folder_id); remember(saved.id);
    });
  }

  const selectedFolder = data.folders.find((item) => `folder:${item.id}` === selected);
  const selectedNote = data.notes.find((item) => `note:${item.id}` === selected);
  const selectedItem: TreeItem | undefined = selectedFolder ? { kind: 'folder', value: selectedFolder }
    : selectedNote ? { kind: 'note', value: selectedNote } : undefined;
  const parent = selectedItem?.kind === 'folder' ? selectedItem.value.id : selectedItem?.value.folder_id || null;

  function newItem(kind: 'new-folder' | 'new-note') {
    void perform(async () => { setDialog({ kind, parent }); });
  }
  function manage(kind: ManagementAction, target: TreeItem) {
    if (working || dialog || templateManager) return;
    setSelected(itemKey(target));
    void perform(async () => {
      const fresh = target.kind === 'note' ? await getNote(target.value.id) : undefined;
      const impact = kind === 'delete' && target.kind === 'folder' ? await getDeletionImpact(target.value.id) : undefined;
      setDialog({ kind, target: fresh ? { kind: 'note', value: fresh } : target,
        parent: fresh ? fresh.folder_id : target.kind === 'folder' ? target.value.parent_id : target.value.folder_id,
        note: fresh, impact });
    });
  }
  // A committed mutation must not look retryable just because the next read fails.
  async function refreshAfterChange() {
    setDialog(null);
    try { return await refreshTree(); }
    catch (failure) { throw new Error(`The change completed, but the library refresh failed. Use Refresh library. ${failure instanceof Error ? failure.message : ''}`, { cause: failure }); }
  }
  function submit(value: string, template?: TemplateSummary) {
    if (!dialog) return;
    const state = dialog;
    void perform(async () => {
      if (state.kind === 'new-folder') {
        const created = await createFolder(value, state.parent);
        setSelected(`folder:${created.id}`);
        const tree = await refreshAfterChange(); reveal(tree, created.id);
      } else if (state.kind === 'new-note') {
        const created = template ? await createNoteFromTemplate(template.id, template.revision, value, state.parent)
          : await createNote({ title: value, document_json: createEmptyDocument(), folder_id: state.parent });
        setNote(created); remember(created.id); setSelected(`note:${created.id}`);
        const tree = await refreshAfterChange(); reveal(tree, created.folder_id);
      } else if (state.kind === 'save-template') {
        await captureTemplate(value, state.note!.id, state.note!.revision);
        setDialog(null); setTemplateNotice('Template saved. It is available in New note and Manage templates.');
      } else if (state.target) {
        if (state.target.kind === 'folder') {
          if (state.kind === 'delete') await deleteFolder(state.impact!);
          else await updateFolder(state.target.value.id, state.kind === 'rename' ? { name: value } : { parent_id: value || null });
        } else {
          if (state.kind === 'delete') await deleteNote(state.note!.id, state.note!.revision);
          else {
            const updated = await updateNote(state.note!.id, state.note!.revision,
              state.kind === 'rename' ? { title: value } : { folder_id: value || null });
            if (note?.id === updated.id) { setNote(updated); setEditorEpoch((n) => n + 1); }
          }
        }
        if (state.kind === 'delete') {
          setSelected(null);
          const deletedActive = note && (state.target.kind === 'note' ? note.id === state.target.value.id
            : ancestorIds(data, note.folder_id).includes(state.target.value.id));
          if (deletedActive) { setNote(null); remember(null); }
        }
        const tree = await refreshAfterChange();
        if (note && !tree.notes.some((item) => item.id === note.id)) { setNote(null); remember(null); }
        if (state.kind === 'delete') setSelected(null);
        else if (state.target.kind === 'folder') reveal(tree, state.target.value.id);
        else reveal(tree, tree.notes.find((item) => item.id === state.target!.value.id)?.folder_id || null);
      }
      setDialog(null);
    });
  }

  const blocked = working || dialog !== null || templateManager || loading || lifecycleProblem !== null;
  return <div className="workspace" data-navigation-collapsed={navigationCollapsed}>
    <a className="skip-link" href="#note">Skip to note</a>
    <aside id="workspace-navigation" className="sidebar" aria-label="Workspace navigation" hidden={navigationCollapsed}>
      <div className="brand"><img src="/assets/branding/cyrnava-256.png" alt="" width="128" height="128" />
        <div><h1>CyrNava</h1><p className="eyebrow">LOCAL WORKSPACE · v{version}</p></div></div>
      <button className="secondary root-button" disabled={blocked} onClick={() => setSelected(null)}><Icon name="home" />Workspace root</button>
      <div className="library-actions create-actions">
        <button disabled={blocked} onClick={() => newItem('new-folder')}><Icon name="folder" />New folder</button>
        <button className="secondary new-note-button" disabled={blocked} onClick={() => newItem('new-note')}><Icon name="note" />New note</button>
      </div>
      <DirectoryTree data={data} expanded={expanded} selected={selected} openedNote={note?.id || null}
        busy={blocked} onSelect={selectItem} onManage={manage}
        onToggle={(id) => setExpanded((current) => { const next = new Set(current); if (!next.delete(id)) next.add(id); return next; })} />
      <div className="library-actions">
        {(['rename', 'move', 'delete'] as const).map((action) => <button key={action} className="secondary"
          disabled={blocked || !selectedItem} onClick={() => selectedItem && manage(action, selectedItem)}>
          <Icon name={action} />{action[0].toUpperCase() + action.slice(1)}
        </button>)}
        <button className="secondary refresh-button" disabled={blocked} onClick={() => void perform(async () => { await refreshTree(); })}><Icon name="refresh" />Refresh library</button>
      </div>
      <p className="status" role="status" data-health={health}>Backend at page load: {health}</p>
      <p className="hint">Arrow keys navigate. Enter opens notes or toggles folders. F2 renames; Delete asks for confirmation.</p>
      <p className="hint"><a href="/third-party-notices.txt" target="_blank" rel="noopener noreferrer">Third-party notices</a></p>
    </aside>
    <main id="note" tabIndex={-1}>
      <div className="workspace-toolbar">
        <AppearanceControl />
        <button className="secondary" aria-controls="workspace-navigation" aria-expanded={!navigationCollapsed}
          onClick={() => {
            const next = !navigationCollapsed; setNavigationCollapsed(next);
            try { localStorage.setItem(NAVIGATION_KEY, String(next)); } catch { /* Preference remains usable for this page. */ }
          }}><Icon name={navigationCollapsed ? 'show' : 'hide'} />{navigationCollapsed ? 'Show navigation' : 'Hide navigation'}</button>
        <button className="secondary" disabled={blocked} onClick={() => void perform(async () => { setTemplateManager(true); })}><Icon name="templates" />Manage templates</button>
        <button className="secondary" disabled={blocked || !note} onClick={() => note && void perform(async () => {
          const revision = editor.current!.getRevision();
          setDialog({ kind: 'save-template', parent: null, note: { ...note, revision } });
        })}><Icon name="save" />Save as template</button>
      </div>
      {templateNotice && <p role="status">{templateNotice}</p>}
      {lifecycleProblem && <p role="alert">{lifecycleProblem}</p>}
      {working && <p role="status">Saving pending changes or updating the library...</p>}
      {error && !dialog && <div role="alert"><p>{error}</p>
        {!note && <button onClick={() => { setLoading(true); setError(null); setLoadAttempt((n) => n + 1); }}>Retry opening library</button>}
      </div>}
      {loading ? <p role="status">Opening library...</p> : note ?
        <PersistentNote key={`${note.id}:${editorEpoch}`} note={note} ref={editor} theme={cyrnava ? 'cyrnava' : theme} locked={working || dialog !== null || templateManager || lifecycleProblem !== null} onSaved={noteSaved} onRecovered={(saved) => { setNote(saved); setEditorEpoch((n) => n + 1); setError(null); noteSaved(); }} />
        : <header><h2>Select or create a note</h2><p>Choose a note in the library, or use New folder and New note to start.</p></header>}
    </main>
    {dialog && <ManagementDialog state={dialog} data={data} busy={working} error={error}
      onClose={() => { if (!working) { setDialog(null); setError(null); } }} onSubmit={submit} />}
    {templateManager && <TemplateManager onClose={() => setTemplateManager(false)} />}
  </div>;
}
