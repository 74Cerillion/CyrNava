import { ApiError } from './http';

export const IMAGE_LIMIT = 10 * 1024 * 1024;
export const IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/webp'];
export interface UploadedAsset { id: string; note_id: string; url: string; mime_type: string; byte_size: number }

export async function uploadImage(noteId: string, file: File, signal: AbortSignal): Promise<string> {
  if (!IMAGE_TYPES.includes(file.type)) throw new Error('Choose a PNG, JPEG or WebP image.');
  if (!file.size || file.size > IMAGE_LIMIT) throw new Error('Images must be between 1 byte and 10 MiB.');
  let response: Response;
  try {
    response = await fetch(`/api/assets?note_id=${encodeURIComponent(noteId)}`, {
      method: 'POST', body: file, headers: { 'Content-Type': file.type },
      signal: AbortSignal.any([signal, AbortSignal.timeout(30_000)]),
    });
  } catch { throw new Error('Image upload failed. Check the local backend and select or paste the image again.'); }
  if (!response.ok) {
    let detail = `Image upload failed (HTTP ${response.status}).`;
    try { const body = await response.json(); if (typeof body.detail === 'string') detail = body.detail; } catch { /* Proxy may return text. */ }
    throw new ApiError(detail, response.status);
  }
  const asset = await response.json() as UploadedAsset;
  if (asset.note_id !== noteId || !/^\/api\/assets\/[0-9a-f-]{36}$/.test(asset.url) || asset.url !== `/api/assets/${asset.id}`) {
    throw new Error('The backend returned an invalid image reference.');
  }
  return asset.url;
}
