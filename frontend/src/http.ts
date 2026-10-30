import { beginMutation } from './pendingMutations';
export class ApiError extends Error {
  constructor(message: string, public readonly status: number) { super(message); }
}

export async function request<T>(path: string, init: RequestInit, signal?: AbortSignal): Promise<T> {
  const finish = !['GET', 'HEAD'].includes(init.method || 'GET') ? beginMutation() : undefined;
  try { const value = await performRequest<T>(path, init, signal); finish?.(true); return value; }
  catch (error) { finish?.(false); throw error; }
}

async function performRequest<T>(path: string, init: RequestInit, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(path, {
      ...init,
      headers: { 'Content-Type': 'application/json' },
      signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(10_000)]) : AbortSignal.timeout(10_000),
    });
  } catch {
    throw new ApiError('Cannot reach the local backend. Your draft is still here.', 0);
  }
  if (!response.ok) {
    let detail = '';
    try {
      const body = await response.json();
      if (typeof body.detail === 'string') detail = body.detail;
      else if (Array.isArray(body.detail)) {
        detail = body.detail.slice(0, 3).flatMap((issue: { loc?: unknown; msg?: unknown }) => {
          if (typeof issue.msg !== 'string' || !Array.isArray(issue.loc)) return [];
          const location = issue.loc.filter((part) => typeof part === 'string' || typeof part === 'number').join('.');
          return [location + ': ' + issue.msg];
        }).join('; ');
      }
    } catch { /* A proxy error may not be JSON. */ }
    throw new ApiError(detail || (response.status === 404 && init.method === 'POST'
      ? 'The API is unavailable. Restart the local backend with the M2 code.'
      : `The backend rejected the request (HTTP ${response.status}). Your edits are still here.`), response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
