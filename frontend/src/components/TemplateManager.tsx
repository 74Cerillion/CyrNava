import { useEffect, useRef, useState } from 'react';
import { deleteTemplate, getTemplates, renameTemplate } from '../templates';
import type { TemplateSummary } from '../templates';

export function TemplateManager({ onClose }: { onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [templates, setTemplates] = useState<TemplateSummary[]>([]);
  const [selected, setSelected] = useState('');
  const [name, setName] = useState('');
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [confirming, setConfirming] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const current = templates.find((item) => item.id === selected);
  useEffect(() => {
    const modal = dialog.current!; const previous = document.activeElement as HTMLElement | null;
    modal.showModal(); modal.querySelector<HTMLElement>('button')?.focus();
    return () => { modal.close(); if (previous?.isConnected) previous.focus(); };
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    void getTemplates(controller.signal).then((rows) => {
      if (!controller.signal.aborted) { setTemplates(rows); setError(null); }
    }).catch((problem: unknown) => {
      if (!controller.signal.aborted) setError(problem instanceof Error ? problem.message : 'Cannot read templates.');
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [attempt]);
  async function apply(action: 'rename' | 'delete') {
    if (!current || current.builtin || busy) return;
    setBusy(true); setError(null);
    try {
      if (action === 'rename') {
        const updated = await renameTemplate(current, name);
        setTemplates((rows) => rows.map((row) => row.id === updated.id ? updated : row));
        setName(updated.name);
      } else {
        await deleteTemplate(current);
        setTemplates((rows) => rows.filter((row) => row.id !== current.id));
        setSelected(''); setName(''); setConfirming(false);
      }
    } catch (problem) { setError(problem instanceof Error ? problem.message : 'Template change failed.'); }
    finally { setBusy(false); }
  }
  return <dialog ref={dialog} aria-labelledby="templates-title" onCancel={(event) => { event.preventDefault(); if (!busy) onClose(); }}>
    <h2 id="templates-title">Manage templates</h2>
    <p>Built-in templates are always available. Save an open note as a template to add a custom entry.</p>
    {loading ? <p role="status">Loading templates...</p> : <>
      <label htmlFor="managed-template">Available templates</label>
      <select id="managed-template" value={selected} disabled={busy} onChange={(event) => {
        const id = event.target.value; setSelected(id); setName(templates.find((item) => item.id === id)?.name || ''); setConfirming(false);
      }}>
        <option value="">Select a template</option>
        {templates.map((item) => <option key={item.id} value={item.id}>{item.name}{item.builtin ? ' (built-in)' : ''}</option>)}
      </select>
      {current && <>
        <label htmlFor="template-name">Template name</label>
        <input id="template-name" value={name} maxLength={200} disabled={busy || current.builtin} onChange={(event) => setName(event.target.value)} />
        {current.builtin ? <p>Built-in templates cannot be renamed or deleted.</p> : <>
          <button disabled={busy || !name.trim() || confirming} onClick={() => void apply('rename')}>Rename template</button>
          <button className="danger" disabled={busy} onClick={() => setConfirming(true)}>Delete template</button>
          {confirming && <div>
            <p>Delete this custom template and its copied images? Existing notes remain unchanged.</p>
            <button className="danger" disabled={busy} onClick={() => void apply('delete')}>Delete template permanently</button>
            <button className="secondary" disabled={busy} onClick={() => setConfirming(false)}>Keep template</button>
          </div>}
        </>}
      </>}
    </>}
    {error && <p role="alert">{error}</p>}
    <div className="dialog-actions">
      <button className="secondary" disabled={busy} onClick={() => { setLoading(true); setSelected(''); setConfirming(false); setAttempt((n) => n + 1); }}>Refresh templates</button>
      <button disabled={busy} onClick={onClose}>Close templates</button>
    </div>
  </dialog>;
}
