import { request } from './http';
import type { Note } from './notes';

export interface Folder {
  id: string; parent_id: string | null; name: string; sort_order: number;
  created_at: string; updated_at: string;
}
export type NoteSummary = Omit<Note, 'document_json' | 'format_version'>;
export interface DirectoryData { folders: Folder[]; notes: NoteSummary[] }
export interface DeletionImpact {
  folder_id: string; name: string; descendant_folders: number; notes: number; token: string;
}
export function getTree(signal?: AbortSignal): Promise<DirectoryData> {
  return request('/api/tree', { method: 'GET' }, signal);
}
export function createFolder(name: string, parent_id: string | null): Promise<Folder> {
  return request('/api/folders', { method: 'POST', body: JSON.stringify({ name, parent_id }) });
}
export function updateFolder(id: string, changes: { name?: string; parent_id?: string | null }): Promise<Folder> {
  return request(`/api/folders/${encodeURIComponent(id)}`, { method: 'PATCH', body: JSON.stringify(changes) });
}
export function getDeletionImpact(id: string): Promise<DeletionImpact> {
  return request(`/api/folders/${encodeURIComponent(id)}/deletion-impact`, { method: 'GET' });
}
export function deleteFolder(impact: DeletionImpact): Promise<void> {
  return request(`/api/folders/${encodeURIComponent(impact.folder_id)}`, { method: 'DELETE', body: JSON.stringify({
    recursive: true, expected_descendant_folders: impact.descendant_folders,
    expected_notes: impact.notes, impact_token: impact.token,
  }) });
}
