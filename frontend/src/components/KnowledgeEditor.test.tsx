import { fireEvent, render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { useCreateBlockNote } from '@blocknote/react';
import { KnowledgeEditor } from './KnowledgeEditor';
import type { NoteDocument } from '../notes';

const { snapshot } = vi.hoisted(() => ({ snapshot: [{
  type: 'heading', id: 'heading-1', props: { level: 1 },
  content: [{ type: 'text', text: 'Formatted', styles: { bold: true } }], children: [],
}] }));
vi.mock('@blocknote/react', () => ({ useCreateBlockNote: vi.fn(() => ({ document: snapshot })) }));
vi.mock('@blocknote/mantine', () => ({
  BlockNoteView: ({ onChange }: { onChange: () => void }) => <button onClick={onChange}>Editor change</button>,
}));

it('hydrates the editor with native JSON and emits an independent document snapshot', () => {
  const initial: NoteDocument = [{ type: 'paragraph', content: [] }];
  const onChange = vi.fn();
  render(<KnowledgeEditor initialDocument={initial} onDocumentChange={onChange} />);
  expect(useCreateBlockNote).toHaveBeenCalledWith(expect.objectContaining({ initialContent: initial }));
  fireEvent.click(screen.getByRole('button', { name: 'Editor change' }));
  expect(onChange).toHaveBeenCalledWith(snapshot);
  expect(onChange.mock.calls[0][0]).not.toBe(snapshot);
  expect(onChange.mock.calls[0][0][0].content[0].styles).toEqual({ bold: true });
});
