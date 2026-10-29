import { ApiError, request } from './http';

export interface SearchResult {
  note_id: string;
  title: string;
  folder_path: string[];
  snippet: string;
  score: number;
}

export interface SearchResponse {
  query: string;
  total: number;
  results: SearchResult[];
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

function isSearchResult(value: unknown): value is SearchResult {
  return isRecord(value)
    && typeof value.note_id === 'string' && value.note_id.length > 0
    && typeof value.title === 'string'
    && Array.isArray(value.folder_path)
    && value.folder_path.every((name) => typeof name === 'string')
    && typeof value.snippet === 'string'
    && typeof value.score === 'number' && Number.isFinite(value.score);
}

function isSearchResponse(value: unknown): value is SearchResponse {
  return isRecord(value)
    && typeof value.query === 'string'
    && typeof value.total === 'number' && Number.isSafeInteger(value.total)
    && Array.isArray(value.results) && value.results.length <= 20
    && value.total >= value.results.length
    && value.results.every(isSearchResult);
}

export async function searchNotes(query: string, signal?: AbortSignal): Promise<SearchResponse> {
  const parameters = new URLSearchParams({ q: query, limit: '20' });
  let response: unknown;
  try {
    response = await request<unknown>(`/api/search?${parameters}`, { method: 'GET', cache: 'no-store' }, signal);
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError('The local backend returned an invalid search response.', 0);
  }
  if (!isSearchResponse(response)) {
    throw new ApiError('The local backend returned an invalid search response.', 0);
  }
  return response;
}
