import { request } from './http';

export interface TemplateSummary { id: string; name: string; builtin: boolean; revision: number }

export async function getTemplates(signal?: AbortSignal): Promise<TemplateSummary[]> {
  const rows = await request<TemplateSummary[]>('/api/templates', { method: 'GET' }, signal);
  if (!Array.isArray(rows)) throw new Error('Cannot read the template library.');
  return rows;
}

export function captureTemplate(name: string, source_note_id: string, source_revision: number) {
  return request<TemplateSummary>('/api/templates', {
    method: 'POST', body: JSON.stringify({ name, source_note_id, source_revision }),
  });
}

export function renameTemplate(template: TemplateSummary, name: string) {
  return request<TemplateSummary>(`/api/templates/${encodeURIComponent(template.id)}`, {
    method: 'PATCH', body: JSON.stringify({ name, revision: template.revision }),
  });
}

export function deleteTemplate(template: TemplateSummary) {
  return request<void>(`/api/templates/${encodeURIComponent(template.id)}`, {
    method: 'DELETE', body: JSON.stringify({ revision: template.revision }),
  });
}
