import { beforeEach, expect, it, vi } from 'vitest';
import { captureTemplate, deleteTemplate, getTemplates, renameTemplate } from './templates';
import { createNoteFromTemplate } from './notes';

const custom = { id: 'custom', name: 'Custom', revision: 3, builtin: false };
const respond = (body: unknown, status = 200) => Promise.resolve(new Response(status === 204 ? null : JSON.stringify(body), { status }));
beforeEach(() => vi.stubGlobal('fetch', vi.fn().mockImplementation(() => respond(custom))));
it('captures using a source note identifier and confirmed revision without sending private document JSON', async () => {
  await captureTemplate('Custom', 'note', 7);
  expect(fetch).toHaveBeenCalledWith('/api/templates', expect.objectContaining({
    method: 'POST', body: JSON.stringify({ name: 'Custom', source_note_id: 'note', source_revision: 7 }),
  }));
});
it('lists templates and revision-checks custom rename and deletion', async () => {
  vi.mocked(fetch).mockImplementationOnce(() => respond([custom]));
  expect(await getTemplates()).toEqual([custom]);
  await renameTemplate(custom, 'Renamed');
  expect(JSON.parse(vi.mocked(fetch).mock.lastCall![1]!.body as string)).toEqual({ name: 'Renamed', revision: 3 });
  vi.mocked(fetch).mockImplementationOnce(() => respond(null, 204));
  await deleteTemplate(custom);
  expect(vi.mocked(fetch).mock.lastCall![1]!.method).toBe('DELETE');
});
it('creates an independent note through the validated note response boundary', async () => {
  vi.mocked(fetch).mockImplementationOnce(() => respond({ id: 'new-note', revision: 1, format_version: 1, document_json: [] }));
  const note = await createNoteFromTemplate('builtin:enumeration', 1, 'My note', null);
  expect(note.id).toBe('new-note');
  expect(fetch).toHaveBeenCalledWith('/api/templates/builtin%3Aenumeration/notes', expect.objectContaining({
    body: JSON.stringify({ title: 'My note', folder_id: null, revision: 1 }),
  }));
});
it('reports failed listing and stale template requests', async () => {
  vi.mocked(fetch).mockImplementationOnce(() => respond({}));
  await expect(getTemplates()).rejects.toThrow('Cannot read');
  vi.mocked(fetch).mockImplementationOnce(() => respond({ detail: 'Template changed' }, 409));
  await expect(renameTemplate(custom, 'Changed')).rejects.toThrow('Template changed');
});
