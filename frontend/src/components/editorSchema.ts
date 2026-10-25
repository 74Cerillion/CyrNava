// The editor adapter owns the BlockNote schema. Contract tests inspect this exact instance.
import { BlockNoteSchema, defaultBlockSpecs } from '@blocknote/core';

export const schema = BlockNoteSchema.create({
  blockSpecs: {
    paragraph: defaultBlockSpecs.paragraph,
    heading: defaultBlockSpecs.heading,
    bulletListItem: defaultBlockSpecs.bulletListItem,
    numberedListItem: defaultBlockSpecs.numberedListItem,
    checkListItem: defaultBlockSpecs.checkListItem,
    quote: defaultBlockSpecs.quote,
    codeBlock: defaultBlockSpecs.codeBlock,
    image: defaultBlockSpecs.image,
  },
});
