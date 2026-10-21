import { beforeEach, expect, it, vi } from 'vitest';
import { ApiError, createNote, getNote, updateNote } from './notes';
import type { Note } from './notes';

const note: Note = {
  id: 'note-id', title: 'Title', document_json: [{ type: 'paragraph', content: [] }],
  folder_id: null, format_version: 1, revision: 1, created_at: 'now', updated_at: 'now',
};
beforeEach(() => vi.stubGlobal('fetch', vi.fn()));

it('sends native versioned JSON when creating a note', async () => {
  vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => note } as Response);
  expect(await createNote({ title: note.title, document_json: note.document_json })).toEqual(note);
  const [url, options] = vi.mocked(fetch).mock.calls[0];
  expect(url).toBe('/api/notes');
  expect(options?.method).toBe('POST');
  expect(JSON.parse(options?.body as string)).toEqual({
    title: note.title, document_json: note.document_json, format_version: 1,
  });
});

it('retrieves an existing note and sends expected revision on update', async () => {
  vi.mocked(fetch).mockResolvedValueOnce({ ok: true, json: async () => note } as Response)
    .mockResolvedValueOnce({ ok: true, json: async () => ({ ...note, revision: 2 }) } as Response);
  expect(await getNote(note.id)).toEqual(note);
  await updateNote(note.id, 1, { title: note.title, document_json: note.document_json });
  expect(JSON.parse(vi.mocked(fetch).mock.calls[1][1]?.body as string).revision).toBe(1);
});

it.each([404, 409, 422, 503])('reports HTTP %i without treating it as a saved note', async (status) => {
  vi.mocked(fetch).mockResolvedValue({ ok: false, status } as Response);
  await expect(getNote(note.id)).rejects.toMatchObject({ status });
});

it('reports connection failure', async () => {
  vi.mocked(fetch).mockRejectedValue(new TypeError('Failed to fetch'));
  await expect(getNote(note.id)).rejects.toBeInstanceOf(ApiError);
});

it('rejects an unsupported document format', async () => {
  vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => ({ ...note, format_version: 2 }) } as Response);
  await expect(getNote(note.id)).rejects.toThrow('Unsupported');
});

it('rejects a save response with an unexpected revision', async () => {
  vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => note } as Response);
  await expect(updateNote(note.id, 1, note)).rejects.toThrow('Unexpected save response');
});


it('explains an outdated backend when the create endpoint is missing', async () => {
  vi.mocked(fetch).mockResolvedValue({ ok: false, status: 404 } as Response);
  await expect(createNote(note)).rejects.toThrow('Restart the local backend');
});
