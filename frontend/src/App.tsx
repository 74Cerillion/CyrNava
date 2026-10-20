import { useEffect, useState } from 'react';
import { KnowledgeEditor } from './components/KnowledgeEditor';

type Health = 'checking' | 'online' | 'offline';

export default function App() {
  const [health, setHealth] = useState<Health>('checking');

  useEffect(() => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 3000);
    let active = true;

    async function checkHealth() {
      try {
        const response = await fetch('/api/health', { signal: controller.signal });
        if (!response.ok) throw new Error('Health request failed');
        const data: unknown = await response.json();
        if (!data || typeof data !== 'object' || !('status' in data) || data.status !== 'ok') {
          throw new Error('Unexpected health response');
        }
        if (active) setHealth('online');
      } catch {
        if (active) setHealth('offline');
      } finally {
        window.clearTimeout(timeout);
      }
    }

    void checkHealth();
    return () => {
      active = false;
      window.clearTimeout(timeout);
      controller.abort();
    };
  }, []);

  return (
    <div className="workspace">
      <aside className="sidebar" aria-label="Workspace navigation">
        <p className="eyebrow">LOCAL WORKSPACE · M0</p>
        <h1>Cybersecurity knowledge</h1>
        <nav aria-label="Notes"><a href="#scratchpad" aria-current="page">Scratchpad</a></nav>
        <p className="status" role="status">Backend: {health}</p>
        <p className="hint">One temporary note. Stored in memory only.</p>
      </aside>
      <main id="scratchpad">
        <header>
          <h2>Scratchpad</h2>
          <p>Changes disappear when you reload or close this page. Do not enter sensitive data.</p>
        </header>
        <KnowledgeEditor />
      </main>
    </div>
  );
}
