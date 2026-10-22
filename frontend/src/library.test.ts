import { beforeEach, expect, it, vi } from 'vitest';
import { createFolder, deleteFolder, getDeletionImpact, getTree, updateFolder } from './library';
import { deleteNote } from './notes';

beforeEach(() => vi.stubGlobal('fetch', vi.fn()));
const ok = (body: unknown) => ({ ok: true, status: 200, json: async () => body } as Response);

it('retrieves the flat tree without requesting every document', async () => {
  const tree = { folders: [], notes: [] };
  vi.mocked(fetch).mockResolvedValue(ok(tree));
  expect(await getTree()).toEqual(tree);
  expect(fetch).toHaveBeenCalledTimes(1);
  expect(fetch).toHaveBeenCalledWith('/api/tree', expect.objectContaining({ method: 'GET' }));
});

it('creates and reparents folders including an explicit null root destination', async () => {
  vi.mocked(fetch).mockResolvedValue(ok({ id: 'f' }));
  await createFolder('B01', 'parent');
  expect(JSON.parse(vi.mocked(fetch).mock.calls[0][1]?.body as string)).toEqual({ name: 'B01', parent_id: 'parent' });
  await updateFolder('f', { parent_id: null });
  expect(JSON.parse(vi.mocked(fetch).mock.calls[1][1]?.body as string)).toEqual({ parent_id: null });
});

it('requests fresh deletion impact and sends explicit intent, counts, and token', async () => {
  const impact = { folder_id: 'f', name: 'B01', descendant_folders: 3, notes: 7, token: 'confirmed-token' };
  vi.mocked(fetch).mockResolvedValueOnce(ok(impact)).mockResolvedValueOnce({ ok: true, status: 204 } as Response);
  expect(await getDeletionImpact('f')).toEqual(impact);
  expect(vi.mocked(fetch).mock.calls[0][0]).toBe('/api/folders/f/deletion-impact');
  await deleteFolder(impact);
  expect(vi.mocked(fetch).mock.calls[1][1]?.method).toBe('DELETE');
  expect(JSON.parse(vi.mocked(fetch).mock.calls[1][1]?.body as string)).toEqual({
    recursive: true, expected_descendant_folders: 3, expected_notes: 7, impact_token: 'confirmed-token',
  });
});

it('sends the confirmed revision when deleting a note', async () => {
  vi.mocked(fetch).mockResolvedValue({ ok: true, status: 204 } as Response);
  await deleteNote('n', 4);
  expect(fetch).toHaveBeenCalledWith('/api/notes/n', expect.objectContaining({ method: 'DELETE', body: '{"revision":4}' }));
});

it('surfaces the backend domain error on an invalid move', async () => {
  vi.mocked(fetch).mockResolvedValue({ ok: false, status: 422, json: async () => ({ detail: 'A folder cannot move into itself or a descendant' }) } as Response);
  await expect(updateFolder('a', { parent_id: 'b' })).rejects.toThrow('descendant');
});
