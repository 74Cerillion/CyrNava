import type { NoteDocument } from '../notes';

// Creation uses the same native JSON format as the adapter's editor snapshots.
export function createEmptyDocument(): NoteDocument {
  return [{ type: 'paragraph', content: [] }];
}
