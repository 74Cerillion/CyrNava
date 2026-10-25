import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { BlockNoteEditor } from '@blocknote/core';
import { getDefaultEmojiPickerItems, getDefaultSlashMenuItems } from '@blocknote/core/extensions';
import { expect, it } from 'vitest';
import { schema } from './editorSchema';

const contract = JSON.parse(readFileSync(resolve('../backend/app/document_format_v1.json'), 'utf8'));
const fixtures = JSON.parse(readFileSync(resolve('../backend/tests/fixtures/blocknote_v1.json'), 'utf8'));

it('keeps the backend compatibility contract aligned with the actual adapter schema', () => {
  const actual = JSON.parse(JSON.stringify({ blocks: schema.blockSchema, inline: schema.inlineContentSchema, styles: schema.styleSchema }));
  expect(actual).toEqual({ blocks: contract.blocks, inline: contract.inline, styles: contract.styles });
});

it('inventories all current slash actions without assuming the screenshot is exhaustive', () => {
  const editor = BlockNoteEditor.create({ schema });
  try { expect(getDefaultSlashMenuItems(editor).map((item) => item.key)).toEqual(fixtures.slash_menu_keys); }
  finally { editor._tiptapEditor.destroy(); }
});

for (const [name, document] of Object.entries(fixtures.cases)) {
  it('reconstructs the real editor fixture without loss: ' + name, () => {
    const editor = BlockNoteEditor.create({ schema, initialContent: document as typeof schema.PartialBlock[] });
    try { expect(editor.document).toEqual(document); }
    finally { editor._tiptapEditor.destroy(); }
  });
}

it('reconstructs mixed formatting, Unicode, links and nested toggle/list structures', () => {
  const editor = BlockNoteEditor.create({ schema, initialContent: fixtures.mixed });
  try {
    expect(editor.document).toEqual(fixtures.mixed);
    const image = editor.document.find((block) => block.type === 'image')!;
    editor.updateBlock(image.id, { props: { showPreview: false, previewWidth: 128, caption: 'Edited caption' } });
    const updated = editor.document;
    const reopened = BlockNoteEditor.create({ schema, initialContent: updated });
    try { expect(reopened.document).toEqual(updated); }
    finally { reopened._tiptapEditor.destroy(); }
  }
  finally { editor._tiptapEditor.destroy(); }
});


const expectedTypes: Record<string, string> = {
  paragraph: 'paragraph', quote: 'quote', numbered_list: 'numberedListItem', bullet_list: 'bulletListItem',
  check_list: 'checkListItem', code_block: 'codeBlock', image: 'image',
};
for (const key of fixtures.slash_menu_keys.filter((key: string) => key !== 'emoji') as string[]) {
  for (const existing of ['', 'Existing paragraph']) {
    it('executes and reconstructs slash action ' + key + (existing ? ' after text' : ' on empty block'), () => {
      const editor = BlockNoteEditor.create({ schema, initialContent: [{ id: 'current', type: 'paragraph', content: existing }] });
      try {
        editor.setTextCursorPosition('current');
        getDefaultSlashMenuItems(editor).find((item) => item.key === key)!.onItemClick();
        const document = editor.document;
        const block = document[existing ? 1 : 0];
        expect(block.type).toBe(key.includes('heading') ? 'heading' : expectedTypes[key]);
        if (block.type === 'heading') {
          expect(block.props.level).toBe(Number(key.match(/\d$/)?.[0] ?? 1));
          expect(block.props.isToggleable ?? false).toBe(key.startsWith('toggle'));
        }
        const reopened = BlockNoteEditor.create({ schema, initialContent: document });
        try { expect(reopened.document).toEqual(document); }
        finally { reopened._tiptapEditor.destroy(); }
      } finally { editor._tiptapEditor.destroy(); }
    });
  }
}

it('inserts an emoji using the bundled picker action and reconstructs it as Unicode text', async () => {
  const editor = BlockNoteEditor.create({ schema, initialContent: [{ id: 'emoji', type: 'paragraph', content: [] }] });
  try {
    editor.setTextCursorPosition('emoji');
    const choices = await getDefaultEmojiPickerItems(editor, 'rocket');
    expect(choices.length).toBeGreaterThan(0);
    choices[0].onItemClick();
    const document = editor.document;
    expect(JSON.stringify(document)).toContain(choices[0].id);
    const reopened = BlockNoteEditor.create({ schema, initialContent: document });
    try { expect(reopened.document).toEqual(document); }
    finally { reopened._tiptapEditor.destroy(); }
  } finally { editor._tiptapEditor.destroy(); }
});


for (const [kind, block] of Object.entries(schema.blockSchema)) {
  for (const [name, prop] of Object.entries(block.propSchema)) {
    for (const value of 'values' in prop ? prop.values! : []) {
      it('round-trips installed property ' + kind + '.' + name + '=' + value, () => {
        const editor = BlockNoteEditor.create({ schema, initialContent: [{ type: kind, props: { [name]: value } } as typeof schema.PartialBlock] });
        try {
          const document = editor.document;
          expect(document[0].props).toHaveProperty(name, value);
          const reopened = BlockNoteEditor.create({ schema, initialContent: document });
          try { expect(reopened.document).toEqual(document); }
          finally { reopened._tiptapEditor.destroy(); }
        } finally { editor._tiptapEditor.destroy(); }
      });
    }
  }
}

it('retains formatting commands applied to a nonempty block without replacing its identity', () => {
  const editor = BlockNoteEditor.create({ schema, initialContent: [{ id: 'format', type: 'paragraph', content: 'Formatted text' }, { id: 'end', type: 'paragraph', content: [] }] });
  try {
    editor.setSelection('format', 'end');
    editor.addStyles({ bold: true, italic: true, underline: true, strike: true, textColor: 'red', backgroundColor: 'yellow' });
    editor.createLink('https://example.invalid/command');
    editor.updateBlock('format', { type: 'heading', props: { level: 6, isToggleable: true, textAlignment: 'right' } });
    const document = editor.document;
    expect(document[0].id).toBe('format');
    expect(document[0].props).toMatchObject({ level: 6, isToggleable: true, textAlignment: 'right' });
    expect(JSON.stringify(document)).toContain('https://example.invalid/command');
    expect(JSON.stringify(document)).toContain('"bold":true');
    const reopened = BlockNoteEditor.create({ schema, initialContent: document });
    try { expect(reopened.document).toEqual(document); }
    finally { reopened._tiptapEditor.destroy(); }
  } finally { editor._tiptapEditor.destroy(); }
});
