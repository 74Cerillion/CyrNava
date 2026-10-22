import { useEffect, useRef, useState } from 'react';
import type { DirectoryData, DeletionImpact } from '../library';
import type { Note } from '../notes';
import { ancestorIds, itemLabel, visibleRows } from '../tree';
import type { TreeItem } from '../tree';

export interface DialogState {
  kind: 'new-folder' | 'new-note' | 'rename' | 'move' | 'delete';
  target?: TreeItem; parent: string | null; note?: Note; impact?: DeletionImpact;
}
interface Props {
  state: DialogState; data: DirectoryData; busy: boolean; error: string | null;
  onClose: () => void; onSubmit: (value: string) => void;
}
export function ManagementDialog({ state, data, busy, error, onClose, onSubmit }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const label = state.impact?.name || (state.target ? itemLabel(state.target) : '');
  const [value, setValue] = useState(state.kind === 'move' ? state.parent || '' : state.kind === 'rename' ? label : '');
  const title = state.kind === 'new-folder' ? 'New folder' : state.kind === 'new-note' ? 'New note'
    : `${state.kind === 'rename' ? 'Rename' : state.kind === 'move' ? 'Move' : 'Delete'} ${label}`;
  const names = new Map(data.folders.map((f) => [f.id, f.name]));
  useEffect(() => {
    const dialog = ref.current!;
    const previous = document.activeElement as HTMLElement | null;
    dialog.showModal();
    dialog.querySelector<HTMLElement>('input, select, button')?.focus();
    return () => { dialog.close(); if (previous?.isConnected) previous.focus(); };
  }, []);
  useEffect(() => { if (!busy) ref.current?.querySelector<HTMLElement>('input, select, button')?.focus(); }, [busy]);
  return <dialog ref={ref} aria-labelledby="management-title"
    onCancel={(event) => { event.preventDefault(); if (!busy) onClose(); }}
    onKeyDown={(event) => { if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); if (!busy) onClose(); } }}>
    <h2 id="management-title">{title}</h2>
    <form onSubmit={(event) => { event.preventDefault(); if (!busy) onSubmit(value); }}>
      {state.kind === 'delete' ? <>
        <p>This operation cannot be undone.</p>
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
        <label htmlFor="item-name">{state.kind === 'new-note' ? 'Note title' : 'Name'}</label>
        <input id="item-name" value={value} disabled={busy} required maxLength={200} onChange={(event) => setValue(event.target.value)} />
      </>}
      {error && <p role="alert">{error}</p>}
      <div className="dialog-actions">
        <button type="button" className="secondary" disabled={busy} onClick={onClose}>Cancel</button>
        <button type="submit" className={state.kind === 'delete' ? 'danger' : ''}
          disabled={busy || (!['move', 'delete'].includes(state.kind) && !value.trim())}>
          {busy ? 'Working...' : state.kind === 'delete' ? 'Delete permanently' : state.kind.startsWith('new-') ? 'Create' : 'Apply'}
        </button>
      </div>
    </form>
  </dialog>;
}
