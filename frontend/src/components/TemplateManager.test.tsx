import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import { TemplateManager } from './TemplateManager';
import { deleteTemplate, getTemplates, renameTemplate } from '../templates';

vi.mock('../templates', () => ({ getTemplates: vi.fn(), renameTemplate: vi.fn(), deleteTemplate: vi.fn() }));
const builtin = { id: 'builtin:general', name: 'General Notes', builtin: true, revision: 1 };
const custom = { id: 'custom', name: 'My custom', builtin: false, revision: 2 };
beforeEach(() => {
  vi.clearAllMocks(); vi.mocked(getTemplates).mockResolvedValue([builtin, custom]);
});
it('shows built-ins as protected and supports custom rename, cancel deletion and confirm deletion', async () => {
  vi.mocked(renameTemplate).mockResolvedValue({ ...custom, name: 'Renamed', revision: 3 });
  vi.mocked(deleteTemplate).mockResolvedValue(undefined);
  render(<TemplateManager onClose={vi.fn()} />);
  const select = await screen.findByLabelText('Available templates');
  fireEvent.change(select, { target: { value: builtin.id } });
  expect(screen.getByLabelText('Template name')).toBeDisabled();
  expect(screen.queryByRole('button', { name: 'Delete template' })).not.toBeInTheDocument();
  fireEvent.change(select, { target: { value: custom.id } });
  fireEvent.change(screen.getByLabelText('Template name'), { target: { value: 'Renamed' } });
  fireEvent.click(screen.getByRole('button', { name: 'Rename template' }));
  await screen.findByRole('option', { name: 'Renamed' });
  expect(renameTemplate).toHaveBeenCalledWith(custom, 'Renamed');
  fireEvent.click(screen.getByRole('button', { name: 'Delete template' }));
  fireEvent.click(screen.getByRole('button', { name: 'Keep template' }));
  expect(deleteTemplate).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button', { name: 'Delete template' }));
  fireEvent.click(screen.getByRole('button', { name: 'Delete template permanently' }));
  await waitFor(() => expect(screen.queryByRole('option', { name: 'Renamed' })).not.toBeInTheDocument());
  expect(deleteTemplate).toHaveBeenCalledWith({ ...custom, name: 'Renamed', revision: 3 });
});
it('keeps a failed rename visible and allows refreshing the library', async () => {
  vi.mocked(renameTemplate).mockRejectedValue(new Error('Changed elsewhere'));
  render(<TemplateManager onClose={vi.fn()} />);
  fireEvent.change(await screen.findByLabelText('Available templates'), { target: { value: custom.id } });
  fireEvent.click(screen.getByRole('button', { name: 'Rename template' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Changed elsewhere');
  fireEvent.click(screen.getByRole('button', { name: 'Refresh templates' }));
  await waitFor(() => expect(getTemplates).toHaveBeenCalledTimes(2));
});
