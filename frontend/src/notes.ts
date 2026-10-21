// Application-owned JSON types: only the editor adapter knows BlockNote types.
export type JsonValue = null | boolean | number | string | JsonValue[] | { [key: string]: JsonValue };
export type NoteDocument = { [key: string]: JsonValue }[];
export interface NoteDraft {
  title: string;
  document_json: NoteDocument;
}
export interface Note extends NoteDraft {
  id: string;
  folder_id: null;
  format_version: number;
  revision: number;
  created_at: string;
  updated_at: string;
}

export class ApiError extends Error {
  constructor(message: string, public readonly status: number) {
    super(message);
  }
}

async function request(path: string, init: RequestInit, signal?: AbortSignal): Promise<Note> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      headers: { 'Content-Type': 'application/json' },
      signal: signal
        ? AbortSignal.any([signal, AbortSignal.timeout(10_000)])
        : AbortSignal.timeout(10_000),
    });
  } catch {
    throw new ApiError('Cannot reach the local backend. Check it is running, then retry.', 0);
  }
  if (!response.ok) {
    const message = response.status === 409
      ? 'This note changed elsewhere. Your edits are still here. Copy them before reloading.'
      : response.status === 404
        ? init.method === 'POST'
          ? 'The notes API is unavailable. Restart the local backend with the M1 code.'
          : 'Note not found. The browser remembers its ID, but this database does not contain it.'
        : `The backend rejected the request (HTTP ${response.status}). Your edits are still here.`;
    throw new ApiError(message, response.status);
  }
  const note: Note = await response.json();
  if (note.format_version !== 1 || !Array.isArray(note.document_json)
      || !Number.isInteger(note.revision) || note.revision < 1 || typeof note.id !== 'string') {
    throw new ApiError('Unsupported or invalid saved note format.', 0);
  }
  return note;
}

export function createNote(draft: NoteDraft): Promise<Note> {
  return request('/api/notes', {
    method: 'POST', body: JSON.stringify({ ...draft, format_version: 1 }),
  });
}

export function getNote(id: string, signal?: AbortSignal): Promise<Note> {
  return request(`/api/notes/${encodeURIComponent(id)}`, { method: 'GET' }, signal);
}

export async function updateNote(id: string, revision: number, draft: NoteDraft, signal?: AbortSignal): Promise<Note> {
  const note = await request(`/api/notes/${encodeURIComponent(id)}`, {
    method: 'PATCH', body: JSON.stringify({ ...draft, revision }),
  }, signal);
  if (note.id !== id || note.revision !== revision + 1) {
    throw new ApiError('Unexpected save response. Your edits are still here; reload carefully.', 0);
  }
  return note;
}
