import { useEffect, useRef, useState } from 'react';
import type { KeyboardEvent } from 'react';
import type { DirectoryData } from '../library';
import { itemKey, itemLabel, visibleRows } from '../tree';
import type { TreeItem } from '../tree';
import { Icon } from './Icon';

export type ManagementAction = 'rename' | 'move' | 'delete';
interface Props {
  data: DirectoryData; expanded: Set<string>; selected: string | null; openedNote: string | null;
  busy: boolean; onToggle: (id: string) => void;
  onSelect: (item: TreeItem) => void;
  onManage: (action: ManagementAction, item: TreeItem) => void;
}

export function DirectoryTree({ data, expanded, selected, openedNote, busy, onToggle, onSelect, onManage }: Props) {
  const rows = visibleRows(data, expanded);
  const [focused, setFocused] = useState<string | null>(null);
  const elements = useRef(new Map<string, HTMLDivElement>());
  const effectiveFocus = rows.some((row) => itemKey(row.item) === focused)
    ? focused : rows.some((row) => itemKey(row.item) === selected) ? selected : rows[0] ? itemKey(rows[0].item) : null;

  const lastSelectionFocus = useRef<string | null>(null);
  const wasBusy = useRef(busy);
  useEffect(() => {
    const finished = wasBusy.current && !busy;
    wasBusy.current = busy;
    if (!selected) {
      lastSelectionFocus.current = null;
      if (finished && rows[0]) elements.current.get(itemKey(rows[0].item))?.focus();
      return;
    }
    if (busy || (lastSelectionFocus.current === selected && !finished)) return;
    const element = elements.current.get(selected);
    element?.focus();
    if (element && document.activeElement === element) lastSelectionFocus.current = selected;
  }, [selected, busy, rows]);

  function focus(key: string) { setFocused(key); elements.current.get(key)?.focus(); }
  function handleKey(event: KeyboardEvent<HTMLDivElement>) {
    if (busy || !(event.target instanceof HTMLElement)) return;
    const key = event.target.closest<HTMLElement>('[role="treeitem"]')?.dataset.key;
    const index = rows.findIndex((row) => itemKey(row.item) === key);
    if (index < 0) return;
    const row = rows[index];
    const folder = row.item.kind === 'folder';
    const handled = ['ArrowDown', 'ArrowUp', 'ArrowLeft', 'ArrowRight', 'Enter', 'F2', 'Delete', 'Home', 'End'];
    if (!handled.includes(event.key)) return;
    event.preventDefault(); event.stopPropagation();
    if (event.key === 'ArrowDown' && rows[index + 1]) focus(itemKey(rows[index + 1].item));
    if (event.key === 'ArrowUp' && rows[index - 1]) focus(itemKey(rows[index - 1].item));
    if (event.key === 'Home' && rows[0]) focus(itemKey(rows[0].item));
    if (event.key === 'End' && rows.length) focus(itemKey(rows[rows.length - 1].item));
    if (event.key === 'ArrowLeft') {
      if (folder && expanded.has(row.item.value.id)) onToggle(row.item.value.id);
      else if (row.parent) focus(`folder:${row.parent}`);
    }
    if (event.key === 'ArrowRight' && folder) {
      if (!expanded.has(row.item.value.id)) onToggle(row.item.value.id);
      else if (rows[index + 1]?.parent === row.item.value.id) focus(itemKey(rows[index + 1].item));
    }
    if (event.key === 'Enter') { onSelect(row.item); if (folder) onToggle(row.item.value.id); }
    if (event.key === 'F2') onManage('rename', row.item);
    if (event.key === 'Delete') onManage('delete', row.item);
  }

  return <div role="tree" aria-label="Library" aria-busy={busy} onKeyDown={handleKey} className="directory-tree">
    {rows.map((row) => {
      const key = itemKey(row.item);
      const isFolder = row.item.kind === 'folder';
      return <div key={key} role="treeitem" data-key={key}
        ref={(element) => { if (element) elements.current.set(key, element); else elements.current.delete(key); }}
        aria-level={row.depth + 1} aria-posinset={row.position} aria-setsize={row.siblings}
        aria-expanded={isFolder ? expanded.has(row.item.value.id) : undefined}
        aria-selected={selected === key} aria-label={`${isFolder ? 'Folder' : 'Note'} ${itemLabel(row.item)}`}
        aria-current={!isFolder && openedNote === row.item.value.id ? 'true' : undefined}
        data-open={!isFolder && openedNote === row.item.value.id}
        tabIndex={key === effectiveFocus ? 0 : -1} style={{ paddingLeft: 8 + row.depth * 18 }}
        onFocus={() => setFocused(key)} onClick={() => { if (!busy) { focus(key); onSelect(row.item); } }}>
        {isFolder ? <button type="button" tabIndex={-1} disabled={busy}
          aria-label={`${expanded.has(row.item.value.id) ? 'Collapse' : 'Expand'} ${itemLabel(row.item)}`}
          onClick={(event) => { event.stopPropagation(); focus(key); onToggle(row.item.value.id); }}>
          {expanded.has(row.item.value.id) ? '▾' : '▸'}</button> : <span aria-hidden="true" className="note-icon"><Icon name="note" /></span>}
        <span className="tree-label">{itemLabel(row.item)}</span>
        {!isFolder && openedNote === row.item.value.id && <span className="open-marker" aria-hidden="true">●</span>}
      </div>;
    })}
    {!rows.length && <p className="hint">Your library is empty. Create a folder or note.</p>}
  </div>;
}
