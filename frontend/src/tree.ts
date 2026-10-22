import type { DirectoryData, Folder, NoteSummary } from './library';

export type TreeItem = { kind: 'folder'; value: Folder } | { kind: 'note'; value: NoteSummary };
export type TreeRow = { item: TreeItem; depth: number; parent: string | null; position: number; siblings: number };
export const itemKey = (item: TreeItem) => `${item.kind}:${item.value.id}`;
export const itemLabel = (item: TreeItem) => item.kind === 'folder' ? item.value.name : item.value.title;

export function visibleRows(data: DirectoryData, expanded: Set<string>, all = false): TreeRow[] {
  const children = new Map<string | null, TreeItem[]>();
  for (const value of data.folders) {
    const list = children.get(value.parent_id) || [];
    list.push({ kind: 'folder', value }); children.set(value.parent_id, list);
  }
  for (const value of data.notes) {
    const list = children.get(value.folder_id) || [];
    list.push({ kind: 'note', value }); children.set(value.folder_id, list);
  }
  const rows: TreeRow[] = [];
  const pending: TreeRow[] = [];
  const append = (parent: string | null, depth: number) => {
    const items = children.get(parent) || [];
    for (let index = items.length - 1; index >= 0; index--) {
      pending.push({ item: items[index], depth, parent, position: index + 1, siblings: items.length });
    }
  };
  append(null, 0);
  const seen = new Set<string>();
  while (pending.length) {
    const row = pending.pop()!;
    const key = itemKey(row.item);
    if (seen.has(key)) continue;
    seen.add(key); rows.push(row);
    if (row.item.kind === 'folder' && (all || expanded.has(row.item.value.id))) append(row.item.value.id, row.depth + 1);
  }
  return rows;
}

export function ancestorIds(data: DirectoryData, folderId: string | null): string[] {
  const parents = new Map(data.folders.map((f) => [f.id, f.parent_id]));
  const ids: string[] = [];
  const seen = new Set<string>();
  let current = folderId;
  while (current !== null && parents.has(current) && !seen.has(current)) {
    seen.add(current); ids.push(current); current = parents.get(current)!;
  }
  return ids;
}
