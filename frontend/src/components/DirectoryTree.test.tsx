import { fireEvent, render, screen } from '@testing-library/react';
import { useState } from 'react';
import { expect, it, vi } from 'vitest';
import { DirectoryTree } from './DirectoryTree';
import type { DirectoryData } from '../library';

const data: DirectoryData = {
  folders: [
    { id: 'root', name: 'HTB Academy', parent_id: null, sort_order: 0, created_at: '', updated_at: '' },
    { id: 'child', name: 'B01', parent_id: 'root', sort_order: 0, created_at: '', updated_at: '' },
  ],
  notes: [
    { id: 'a', title: 'Nmap', folder_id: 'child', revision: 1, created_at: '', updated_at: '' },
    { id: 'b', title: 'Root note', folder_id: null, revision: 1, created_at: '', updated_at: '' },
  ],
};
function setup() {
  const select = vi.fn();
  const manage = vi.fn();
  function Harness() {
    const [expanded, setExpanded] = useState(new Set<string>());
    return <DirectoryTree data={data} expanded={expanded} selected={null} openedNote="a" busy={false}
      onSelect={select} onManage={manage} onToggle={(id) => setExpanded((current) => {
        const next = new Set(current); if (!next.delete(id)) next.add(id); return next;
      })} />;
  }
  render(<Harness />);
  return { select, manage };
}
const item = (name: string) => screen.getByRole('treeitem', { name });

it('renders hierarchy and expands/collapses with the mouse', () => {
  const { select } = setup();
  expect(screen.queryByRole('treeitem', { name: 'Folder B01' })).not.toBeInTheDocument();
  fireEvent.click(item('Folder HTB Academy'));
  expect(select).toHaveBeenCalledWith(expect.objectContaining({ kind: 'folder' }));
  fireEvent.click(screen.getByRole('button', { name: 'Expand HTB Academy' }));
  expect(item('Folder B01')).toHaveAttribute('aria-level', '2');
  fireEvent.click(screen.getByRole('button', { name: 'Expand B01' }));
  expect(item('Note Nmap')).toHaveAttribute('aria-level', '3');
  expect(item('Note Nmap')).toHaveAttribute('aria-current', 'true');
  fireEvent.click(item('Note Nmap'));
  expect(select).toHaveBeenLastCalledWith(expect.objectContaining({ kind: 'note' }));
  fireEvent.click(screen.getByRole('button', { name: 'Collapse HTB Academy' }));
  expect(screen.queryByRole('treeitem', { name: 'Note Nmap' })).not.toBeInTheDocument();
});

it('uses Up/Down/Left/Right to traverse only visible items with one tab stop', () => {
  setup();
  const root = item('Folder HTB Academy');
  root.focus();
  fireEvent.keyDown(root, { key: 'ArrowRight' });
  fireEvent.keyDown(root, { key: 'ArrowRight' });
  expect(item('Folder B01')).toHaveFocus();
  fireEvent.keyDown(item('Folder B01'), { key: 'ArrowRight' });
  fireEvent.keyDown(item('Folder B01'), { key: 'ArrowDown' });
  expect(item('Note Nmap')).toHaveFocus();
  fireEvent.keyDown(item('Note Nmap'), { key: 'ArrowLeft' });
  expect(item('Folder B01')).toHaveFocus();
  fireEvent.keyDown(item('Folder B01'), { key: 'ArrowLeft' });
  expect(item('Folder B01')).toHaveAttribute('aria-expanded', 'false');
  fireEvent.keyDown(item('Folder B01'), { key: 'ArrowLeft' });
  expect(root).toHaveFocus();
  fireEvent.keyDown(root, { key: 'ArrowDown' });
  fireEvent.keyDown(item('Folder B01'), { key: 'ArrowDown' });
  expect(item('Note Root note')).toHaveFocus();
  fireEvent.keyDown(item('Note Root note'), { key: 'ArrowUp' });
  expect(item('Folder B01')).toHaveFocus();
  expect(screen.getAllByRole('treeitem').filter((element) => element.tabIndex === 0)).toHaveLength(1);
});

it('Enter toggles folders or opens notes, F2 renames, and Delete requests confirmation', () => {
  const { select, manage } = setup();
  const root = item('Folder HTB Academy');
  fireEvent.keyDown(root, { key: 'Enter' });
  expect(root).toHaveAttribute('aria-expanded', 'true');
  const note = item('Note Root note');
  fireEvent.keyDown(note, { key: 'Enter' });
  expect(select).toHaveBeenLastCalledWith(expect.objectContaining({ kind: 'note' }));
  fireEvent.keyDown(note, { key: 'F2' });
  expect(manage).toHaveBeenLastCalledWith('rename', expect.objectContaining({ kind: 'note' }));
  fireEvent.keyDown(root, { key: 'Delete' });
  expect(manage).toHaveBeenLastCalledWith('delete', expect.objectContaining({ kind: 'folder' }));
});
