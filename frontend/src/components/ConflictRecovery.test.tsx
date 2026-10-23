import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { getNote } from '../notes';
import type { Note } from '../notes';
import { ConflictRecovery } from './ConflictRecovery';

vi.mock('../notes', () => ({ getNote: vi.fn() }));
const saved: Note = { id: 'A', title: 'Remote title', document_json: [{ type: 'paragraph', content: [] }], revision: 3, folder_id: null, format_version: 1, created_at: '', updated_at: '' };
const draft = { title: 'Local title', document_json: [{ type: 'paragraph', content: [] }] };
beforeEach(() => { vi.resetAllMocks(); vi.mocked(getNote).mockResolvedValue(saved); });
it('inspects the persisted version without writing and Cancel retains the local editor', async () => {
  const close = vi.fn(); const reload = vi.fn();
  render(<ConflictRecovery noteId="A" draft={draft} onClose={close} onReload={reload} />);
  expect(await screen.findByText('Remote title')).toBeInTheDocument();
  expect(screen.getByText('Local title')).toBeInTheDocument();
  expect(screen.getByRole('button', { name: 'Reopen saved version' })).toBeDisabled();
  fireEvent.click(screen.getByRole('button', { name: 'Keep editing this draft' }));
  expect(close).toHaveBeenCalledOnce(); expect(reload).not.toHaveBeenCalled();
});
it('requires retained recovery data and confirmation before a fresh GET replaces the editor', async () => {
  let bundle: Blob | undefined;
  const create = vi.spyOn(URL, 'createObjectURL').mockImplementation((blob) => { bundle = blob as Blob; return 'blob:recovery'; });
  vi.spyOn(URL, 'revokeObjectURL').mockImplementation(() => {});
  const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {});
  const reload = vi.fn();
  render(<ConflictRecovery noteId="A" draft={draft} onClose={vi.fn()} onReload={reload} />);
  await screen.findByText('Remote title');
  fireEvent.click(screen.getByRole('button', { name: 'Download both versions' }));
  expect(create).toHaveBeenCalledOnce(); expect(click).toHaveBeenCalledOnce();
  expect(bundle?.type).toBe('application/json');
  expect(screen.getByRole('button', { name: 'Reopen saved version' })).toBeDisabled();
  fireEvent.click(screen.getByRole('checkbox'));
  vi.mocked(getNote).mockResolvedValue({ ...saved, revision: 4 });
  fireEvent.click(screen.getByRole('button', { name: 'Reopen saved version' }));
  await waitFor(() => expect(reload).toHaveBeenCalledWith({ ...saved, revision: 4 }));
  expect(getNote).toHaveBeenCalledTimes(2);
  create.mockRestore(); click.mockRestore();
});
it('failed recovery reads preserve the draft and offer an actionable error', async () => {
  vi.mocked(getNote).mockRejectedValue(new Error('offline'));
  const reload = vi.fn();
  await act(async () => { render(<ConflictRecovery noteId="A" draft={draft} onClose={vi.fn()} onReload={reload} />); });
  expect(screen.getByRole('alert')).toHaveTextContent('Keep this draft open');
  expect(reload).not.toHaveBeenCalled();
});
