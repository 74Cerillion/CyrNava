import { beforeEach, expect, it } from 'vitest';
import { findDrafts, PAGE_ID, removeAcknowledgedDraft, storeDraft } from './drafts';
import type { Note } from './notes';

const note: Note = { id: 'one', revision: 3, format_version: 1, folder_id: null,
  title: 'Saved', document_json: [{ type: 'paragraph', content: [] }], created_at: '', updated_at: '' };
beforeEach(() => localStorage.clear());
it('records native JSON, note identity and revision synchronously', () => {
  const draft = storeDraft(note, { title: 'Draft', document_json: note.document_json }, 3);
  expect(findDrafts(note.id, true)).toEqual([draft]);
  expect(draft).toMatchObject({ note_id: 'one', base_revision: 3, writer: PAGE_ID });
  expect(findDrafts('another', true)).toEqual([]);
});
it('an old acknowledgement cannot clear a newer draft', () => {
  const old = storeDraft(note, { ...note, title: 'Old' }, 3);
  const latest = storeDraft(note, { ...note, title: 'Latest' }, 3);
  removeAcknowledgedDraft(old);
  expect(findDrafts(note.id, true)).toEqual([latest]);
  removeAcknowledgedDraft(latest); expect(findDrafts(note.id, true)).toEqual([]);
});
it('keeps drafts from separate tabs independent', () => {
  const record = storeDraft(note, note, 3);
  const other = { ...record, writer: 'other-tab', token: 'other-token', title: 'Other' };
  localStorage.setItem('engage.recovery.v1:one:other-tab', JSON.stringify(other));
  removeAcknowledgedDraft(record);
  expect(findDrafts(note.id)).toEqual([other]);
});
it('rejects an incompatible recovery record without deleting it', () => {
  localStorage.setItem('engage.recovery.v1:one:old', '{"recovery_format":99}');
  expect(() => findDrafts(note.id)).toThrow(); expect(localStorage.length).toBe(1);
});
