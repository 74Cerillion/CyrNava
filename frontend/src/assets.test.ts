import { afterEach, expect, it, vi } from 'vitest';
import { IMAGE_LIMIT, uploadImage } from './assets';

const owner = '5b2bc694-e529-4be4-8f67-dc5eae5ab8ff';
const id = '23d398da-6ac8-4e17-a6f0-1b8048714d2a';
const asset = { id, note_id: owner, url: `/api/assets/${id}`, mime_type: 'image/png', byte_size: 8 };
afterEach(() => vi.unstubAllGlobals());
it('posts raw image bytes to the local API and accepts a persistent owned URL', async () => {
  const file = new File(['bytes'], 'screenshot.png', { type: 'image/png' });
  const fetcher = vi.fn().mockResolvedValue({ ok: true, json: async () => asset });
  vi.stubGlobal('fetch', fetcher);
  expect(await uploadImage(owner, file, new AbortController().signal)).toBe(asset.url);
  expect(fetcher).toHaveBeenCalledWith(`/api/assets?note_id=${owner}`, expect.objectContaining({ method: 'POST', body: file, headers: { 'Content-Type': 'image/png' } }));
});
it.each(['image/svg+xml', 'application/pdf', 'text/plain'])('rejects unsupported %s without a request', async (type) => {
  const fetcher = vi.fn(); vi.stubGlobal('fetch', fetcher);
  await expect(uploadImage(owner, new File(['bad'], 'fake.png', { type }), new AbortController().signal)).rejects.toThrow('PNG, JPEG or WebP');
  expect(fetcher).not.toHaveBeenCalled();
});
it('rejects empty or oversized files before uploading', async () => {
  const fetcher = vi.fn(); vi.stubGlobal('fetch', fetcher);
  for (const bytes of ['', new Uint8Array(IMAGE_LIMIT + 1)]) {
    await expect(uploadImage(owner, new File([bytes], 'large.png', { type: 'image/png' }), new AbortController().signal)).rejects.toThrow('10 MiB');
  }
  expect(fetcher).not.toHaveBeenCalled();
});
it('reports server validation errors and backend connection failures', async () => {
  const file = new File(['bytes'], 'bad.png', { type: 'image/png' });
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 422, json: async () => ({ detail: 'Malformed image' }) }));
  await expect(uploadImage(owner, file, new AbortController().signal)).rejects.toThrow('Malformed image');
  vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('offline')));
  await expect(uploadImage(owner, file, new AbortController().signal)).rejects.toThrow('local backend');
});
it.each([{ ...asset, note_id: 'wrong' }, { ...asset, url: 'https://example.invalid/image.png' }, { ...asset, url: 'blob:temporary' }])('rejects an invalid upload response', async (response) => {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => response }));
  await expect(uploadImage(owner, new File(['bytes'], 'a.png', { type: 'image/png' }), new AbortController().signal)).rejects.toThrow('invalid image reference');
});
