import { BlockNoteSchema, defaultBlockSpecs } from '@blocknote/core';
import { BlockNoteView } from '@blocknote/mantine';
import { useCreateBlockNote } from '@blocknote/react';
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
  },
});

// BlockNote owns editor state here. The shell and backend never receive note content.
export function KnowledgeEditor() {
  const editor = useCreateBlockNote({
    schema,
    initialContent: [{ type: 'paragraph', content: 'Start a temporary note here.' }],
  });

  return (
    <section aria-label="Note editor" className="editor">
      <BlockNoteView editor={editor} theme="light" emojiPicker={false} />
    </section>
  );
}
