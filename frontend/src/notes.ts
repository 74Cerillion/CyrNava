// Application-owned JSON types: only the editor adapter knows BlockNote types.
export type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };
export type NoteDocument = { [key: string]: JsonValue }[];
export interface NoteDraft {
  title: string;
  document_json: NoteDocument;
}
export interface Note extends NoteDraft {
  id: string;
  folder_id: string | null;
  format_version: number;
  revision: number;
  created_at: string;
  updated_at: string;
}

export { ApiError } from './http';
import { ApiError, request as httpRequest } from './http';

async function request(path: string, init: RequestInit, signal?: AbortSignal): Promise<Note> {
  const note = await httpRequest<Note>(path, init, signal);
  if (note.format_version !== 1 || !Array.isArray(note.document_json)
      || !Number.isInteger(note.revision) || note.revision < 1 || typeof note.id !== 'string') {
    throw new ApiError('Unsupported or invalid saved note format.', 0);
  }
  return note;
}

export function createNote(draft: NoteDraft & { folder_id?: string | null }): Promise<Note> {
  return request('/api/notes', {
    method: 'POST', body: JSON.stringify({ ...draft, format_version: 1 }),
  });
}

export function createNoteFromTemplate(templateId: string, revision: number, title: string, folder_id: string | null): Promise<Note> {
  return request(`/api/templates/${encodeURIComponent(templateId)}/notes`, {
    method: 'POST', body: JSON.stringify({ title, folder_id, revision }),
  });
}

export function getNote(id: string, signal?: AbortSignal): Promise<Note> {
  return request(`/api/notes/${encodeURIComponent(id)}`, { method: 'GET' }, signal);
}

export async function updateNote(id: string, revision: number, draft: Partial<NoteDraft> & { folder_id?: string | null }, signal?: AbortSignal): Promise<Note> {
  let note: Note;
  try {
    note = await request(`/api/notes/${encodeURIComponent(id)}`, {
      method: 'PATCH', body: JSON.stringify({ ...draft, revision }),
    }, signal);
  } catch (error) {
    if (error instanceof ApiError && error.status === 409) {
      throw new ApiError('This note changed elsewhere. Your edits remain here. Use Review conflict and recover to retain both versions before reopening.', 409);
    }
    throw error;
  }
  if (note.id !== id || note.revision !== revision + 1) {
    throw new ApiError('Unexpected save response. Your edits are still here; reload carefully.', 0);
  }
  return note;
}

export function deleteNote(id: string, revision: number): Promise<void> {
  return httpRequest(`/api/notes/${encodeURIComponent(id)}`, { method: 'DELETE', body: JSON.stringify({ revision }) });
}
