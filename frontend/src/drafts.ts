import type { Note, NoteDraft } from './notes';

const PREFIX = 'engage.recovery.v1:';
// A new ID per loaded page, including duplicated tabs; never shared sessionStorage.
export const PAGE_ID = crypto.randomUUID();
const deferredTokens = new Set<string>();
export interface RecoveryDraft extends NoteDraft {
  recovery_format: 1;
  note_id: string;
  writer: string;
  token: string;
  base_revision: number;
  format_version: number;
  edited_at: string;
}
const key = (draft: RecoveryDraft) => `${PREFIX}${draft.note_id}:${draft.writer}`;

export function storeDraft(note: Note, draft: NoteDraft, revision: number): RecoveryDraft {
  const record: RecoveryDraft = { title: draft.title, document_json: draft.document_json,
    recovery_format: 1, note_id: note.id,
    writer: PAGE_ID, token: crypto.randomUUID(), base_revision: revision,
    format_version: note.format_version, edited_at: new Date().toISOString() };
  // Synchronous, before debounce/network/unload. Failure is reported by the UI.
  localStorage.setItem(key(record), JSON.stringify(record));
  return record;
}

export function removeAcknowledgedDraft(record: RecoveryDraft) {
  const current = localStorage.getItem(key(record));
  // An older response must never remove a newer snapshot or another tab's draft.
  if (current && JSON.parse(current).token === record.token) localStorage.removeItem(key(record));
}

export function deferDraft(record: RecoveryDraft) {
  // Retain it on disk; avoid asking again after a same-page editor remount.
  deferredTokens.add(record.token);
}

export function findDrafts(noteId: string, includeAll = false): RecoveryDraft[] {
  const result: RecoveryDraft[] = [];
  for (let index = 0; index < localStorage.length; index++) {
    const name = localStorage.key(index)!;
    if (!name.startsWith(`${PREFIX}${noteId}:`)) continue;
    const value: unknown = JSON.parse(localStorage.getItem(name)!);
    if (!value || typeof value !== 'object') throw new Error('Invalid recovery record');
    const draft = value as RecoveryDraft;
    if (draft.recovery_format !== 1 || draft.note_id !== noteId || draft.format_version !== 1
        || typeof draft.title !== 'string' || !Array.isArray(draft.document_json)
        || !Number.isInteger(draft.base_revision) || draft.base_revision < 1
        || typeof draft.writer !== 'string' || typeof draft.token !== 'string') {
      throw new Error('Unsupported recovery record');
    }
    if (includeAll || (draft.writer !== PAGE_ID && !deferredTokens.has(draft.token))) result.push(draft);
  }
  return result.sort((a, b) => b.edited_at.localeCompare(a.edited_at));
}

export function downloadDraft(draft: RecoveryDraft) {
  const url = URL.createObjectURL(new Blob([JSON.stringify(draft, null, 2)], { type: 'application/json' }));
  const link = document.createElement('a'); link.href = url;
  link.download = `engage-draft-${draft.note_id}.json`; link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}
