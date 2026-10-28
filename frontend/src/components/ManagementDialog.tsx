import { useEffect, useRef, useState } from 'react';
import type { DirectoryData, DeletionImpact } from '../library';
import type { Note } from '../notes';
import { ancestorIds, itemLabel, visibleRows } from '../tree';
import type { TreeItem } from '../tree';
import { getTemplates } from '../templates';
import type { TemplateSummary } from '../templates';

export interface DialogState {
  kind: 'new-folder' | 'new-note' | 'rename' | 'move' | 'delete' | 'save-template';
  target?: TreeItem; parent: string | null; note?: Note; impact?: DeletionImpact;
}
interface Props {
  state: DialogState; data: DirectoryData; busy: boolean; error: string | null;
  onClose: () => void; onSubmit: (value: string, template?: TemplateSummary) => void;
}
export function ManagementDialog({ state, data, busy, error, onClose, onSubmit }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const label = state.impact?.name || (state.target ? itemLabel(state.target) : '');
  const [value, setValue] = useState(state.kind === 'move' ? state.parent || '' : state.kind === 'rename' ? label : '');
  const [templates, setTemplates] = useState<TemplateSummary[]>([]);
  const [templateId, setTemplateId] = useState('');
  const [templateError, setTemplateError] = useState<string | null>(null);
  const [templateAttempt, setTemplateAttempt] = useState(0);
  const selectedTemplate = templates.find((item) => item.id === templateId);
  const title = state.kind === 'new-folder' ? 'New folder' : state.kind === 'new-note' ? 'New note'
    : state.kind === 'save-template' ? 'Save as template'
    : `${state.kind === 'rename' ? 'Rename' : state.kind === 'move' ? 'Move' : 'Delete'} ${label}`;
  const names = new Map(data.folders.map((f) => [f.id, f.name]));
  useEffect(() => {
    if (state.kind !== 'new-note') return;
    const controller = new AbortController();
    void getTemplates(controller.signal).then((rows) => {
      if (!controller.signal.aborted) { setTemplates(rows); setTemplateError(null); }
    }).catch(() => { if (!controller.signal.aborted) setTemplateError('Templates are unavailable. You can still create a blank note.'); });
    return () => controller.abort();
  }, [state.kind, templateAttempt]);
  useEffect(() => {
    const dialog = ref.current!;
    const previous = document.activeElement as HTMLElement | null;
    dialog.showModal();
    dialog.querySelector<HTMLElement>('input, select, button')?.focus();
    return () => { dialog.close(); if (previous?.isConnected) previous.focus(); };
  }, []);
  useEffect(() => { if (!busy) ref.current?.querySelector<HTMLElement>('input, select, button')?.focus(); }, [busy]);
  return <dialog ref={ref} aria-labelledby="management-title" aria-describedby={state.kind === 'delete' ? 'deletion-description' : undefined}
    onCancel={(event) => { event.preventDefault(); if (!busy) onClose(); }}
    onKeyDown={(event) => { if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); if (!busy) onClose(); } }}>
    <h2 id="management-title">{title}</h2>
    <form onSubmit={(event) => { event.preventDefault(); if (!busy && (!templateId || selectedTemplate)) onSubmit(value, selectedTemplate); }}>
      {state.kind === 'delete' ? <>
        <p id="deletion-description">This operation cannot be undone.</p>
        {state.impact ? <p>This will permanently delete this folder, <strong>{state.impact.descendant_folders} {state.impact.descendant_folders === 1 ? 'subfolder' : 'subfolders'}</strong>, and <strong>{state.impact.notes} {state.impact.notes === 1 ? 'note' : 'notes'}</strong>.</p>
          : <p>This will permanently delete this note.</p>}
      </> : state.kind === 'move' ? <>
        <label htmlFor="destination">Destination folder</label>
        <select id="destination" value={value} disabled={busy} onChange={(event) => setValue(event.target.value)}>
          <option value="">Workspace root</option>
          {visibleRows(data, new Set(), true).filter((row) => row.item.kind === 'folder').map(({ item }) =>
            <option key={item.value.id} value={item.value.id}>
              {ancestorIds(data, item.value.id).reverse().map((id) => names.get(id)).join(' / ')}
            </option>)}
        </select>
      </> : <>
        <label htmlFor="item-name">{state.kind === 'new-note' ? 'Note title' : state.kind === 'save-template' ? 'Template name' : 'Name'}</label>
        <input id="item-name" value={value} disabled={busy} required maxLength={200} onChange={(event) => setValue(event.target.value)} />
      </>}
      {state.kind === 'new-note' && <div className="template-choice">
        <label htmlFor="note-template">Starting content</label>
        <select id="note-template" value={templateId} disabled={busy} onChange={(event) => setTemplateId(event.target.value)}>
          <option value="">Blank note</option>
          <optgroup label="Built-in templates">{templates.filter((item) => item.builtin).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</optgroup>
          <optgroup label="Custom templates">{templates.filter((item) => !item.builtin).map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</optgroup>
        </select>
        {templateError && <p role="alert">{templateError}</p>}
        <button type="button" className="secondary" disabled={busy} onClick={() => setTemplateAttempt((n) => n + 1)}>Reload templates</button>
      </div>}
      {state.kind === 'save-template' && <p>This captures the saved note and copies its images into an independent reusable template. The original note stays unchanged.</p>}
      {error && <p role="alert">{error}</p>}
      <div className="dialog-actions">
        <button type="button" className="secondary" disabled={busy} onClick={onClose}>Cancel</button>
        <button type="submit" className={state.kind === 'delete' ? 'danger' : ''}
          disabled={busy || (!['move', 'delete'].includes(state.kind) && !value.trim()) || (!!templateId && !selectedTemplate)}>
          {busy ? 'Working...' : state.kind === 'delete' ? 'Delete permanently' : state.kind === 'save-template' ? 'Save template' : state.kind.startsWith('new-') ? 'Create' : 'Apply'}
        </button>
      </div>
    </form>
  </dialog>;
}
