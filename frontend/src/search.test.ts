import { beforeEach, expect, it, vi } from 'vitest';
import { ApiError } from './http';
import { searchNotes } from './search';
import type { SearchResponse } from './search';

const response: SearchResponse = {
  query: 'enum', total: 2, results: [
    { note_id: 'first', title: 'Enumeration', folder_path: ['Lab', 'Discovery'], snippet: 'Enumeration checklist', score: -0.2 },
    { note_id: 'second', title: 'Commands', folder_path: [], snippet: 'Enumeration commands', score: -0.1 },
  ],
};
beforeEach(() => vi.stubGlobal('fetch', vi.fn()));
function respond(body: unknown) {
  vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => body } as Response);
}
it('encodes the query, bounds results, disables caching and forwards cancellation', async () => {
  respond(response);
  const controller = new AbortController();
  await searchNotes('a & b/#? café', controller.signal);
  const [path, options] = vi.mocked(fetch).mock.calls[0];
  expect(path).toBe('/api/search?q=a+%26+b%2F%23%3F+caf%C3%A9&limit=20');
  expect(options).toMatchObject({ method: 'GET', cache: 'no-store' });
  const requestSignal = options?.signal as AbortSignal;
  expect(requestSignal.aborted).toBe(false);
  controller.abort(); expect(requestSignal.aborted).toBe(true);
});
it('returns results in backend order with plain snippet text unchanged', async () => {
  const body = { ...response, results: [
    { ...response.results[1], snippet: '<script>synthetic text</script>' }, response.results[0],
  ] };
  respond(body); expect(await searchNotes('enum')).toEqual(body);
});
it('accepts empty results and a total larger than the returned page', async () => {
  respond({ query: '', total: 0, results: [] });
  expect(await searchNotes('')).toEqual({ query: '', total: 0, results: [] });
  respond({ ...response, total: 100 }); expect((await searchNotes('enum')).total).toBe(100);
});
it.each([404, 422, 503])('preserves an HTTP %i failure', async (status) => {
  vi.mocked(fetch).mockResolvedValue({ ok: false, status, json: async () => ({ detail: 'Synthetic search failure.' }) } as Response);
  await expect(searchNotes('enum')).rejects.toMatchObject({ status, message: 'Synthetic search failure.' });
});
it('reports an unavailable backend', async () => {
  vi.mocked(fetch).mockRejectedValue(new TypeError('Network unavailable'));
  await expect(searchNotes('enum')).rejects.toBeInstanceOf(ApiError);
});
it('rejects invalid JSON as an ApiError', async () => {
  vi.mocked(fetch).mockResolvedValue({ ok: true, json: async () => { throw new SyntaxError('Invalid JSON'); } } as unknown as Response);
  await expect(searchNotes('enum')).rejects.toMatchObject({ status: 0, message: 'The local backend returned an invalid search response.' });
});
it.each([
  null, [], {}, { ...response, query: null }, { ...response, total: -1 },
  { ...response, total: 1.5 }, { ...response, total: Number.POSITIVE_INFINITY },
  { ...response, total: Number.MAX_SAFE_INTEGER + 1 }, { ...response, total: 1 },
  { ...response, results: {} },
  { ...response, total: 21, results: Array.from({ length: 21 }, () => response.results[0]) },
])('rejects malformed or unbounded envelope %#', async (body) => {
  respond(body); await expect(searchNotes('enum')).rejects.toBeInstanceOf(ApiError);
});
it.each([
  null, [], {}, { ...response.results[0], note_id: '' }, { ...response.results[0], note_id: 1 },
  { ...response.results[0], title: null }, { ...response.results[0], folder_path: 'Lab' },
  { ...response.results[0], folder_path: ['Lab', 1] }, { ...response.results[0], snippet: null },
  { ...response.results[0], score: '-0.2' }, { ...response.results[0], score: Number.NaN },
  { ...response.results[0], score: Number.NEGATIVE_INFINITY },
])('rejects malformed result fields %#', async (row) => {
  respond({ query: 'enum', total: 1, results: [row] });
  await expect(searchNotes('enum')).rejects.toBeInstanceOf(ApiError);
});
