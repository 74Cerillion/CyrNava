import { BlockNoteSchema, defaultBlockSpecs } from '@blocknote/core';
import { BlockNoteView } from '@blocknote/mantine';
import { useCreateBlockNote } from '@blocknote/react';
import type { NoteDocument } from '../notes';
import '@blocknote/core/fonts/inter.css';
import '@blocknote/mantine/style.css';

// Text-only blocks prevent embedded media from requesting remote resources.
const schema = BlockNoteSchema.create({
  blockSpecs: {
    paragraph: defaultBlockSpecs.paragraph,
    heading: defaultBlockSpecs.heading,
    bulletListItem: defaultBlockSpecs.bulletListItem,
    numberedListItem: defaultBlockSpecs.numberedListItem,
    checkListItem: defaultBlockSpecs.checkListItem,
    quote: defaultBlockSpecs.quote,
    codeBlock: defaultBlockSpecs.codeBlock,
  },
});

interface Props {
  initialDocument: NoteDocument;
  onDocumentChange: (document: NoteDocument) => void;
  editable?: boolean;
}

// Initial content is applied only on mount. Save responses never reset the editor.
// The caller mounts a new instance (keyed by note ID) when opening another note.
export function KnowledgeEditor({ initialDocument, onDocumentChange, editable = true }: Props) {
  const editor = useCreateBlockNote({
    schema,
    initialContent: initialDocument as unknown as typeof schema.PartialBlock[],
  });

  return (
    <section aria-label="Note editor" className="editor">
      <BlockNoteView
        editor={editor}
        editable={editable}
        theme="light"
        emojiPicker={false}
        onChange={() => onDocumentChange(structuredClone(editor.document) as unknown as NoteDocument)}
      />
    </section>
  );
}
