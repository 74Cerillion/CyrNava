import { useEffect, useState } from 'react';
import { PAGE_ID } from '../drafts';

interface Configuration { managed: boolean; instance?: string; heartbeat_ms?: number }
let sequence = 0;

export function useLifecycle() {
  const [problem, setProblem] = useState<string | null>(null);
  useEffect(() => {
    let disposed = false;
    let configuration: Configuration | null = null;
    let timer: number | undefined;
    let busy = false;
    let hidden = false;
    const controller = new AbortController();
    async function heartbeat() {
      if (disposed || hidden || busy) return;
      busy = true;
      try {
        if (!configuration) {
          const response = await fetch('/api/lifecycle', { signal: AbortSignal.any([controller.signal, AbortSignal.timeout(3000)]) });
          if (!response.ok) throw new Error('Lifecycle check failed');
          const value = await response.json() as Configuration;
          if (typeof value.managed !== 'boolean' || (value.managed &&
              (typeof value.instance !== 'string' || !Number.isFinite(value.heartbeat_ms) || value.heartbeat_ms! <= 0))) throw new Error('Invalid lifecycle response');
          configuration = value;
        }
        if (configuration.managed) {
          const response = await fetch(`/api/lifecycle/sessions/${PAGE_ID}`, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ instance: configuration.instance, sequence: ++sequence }),
            signal: AbortSignal.any([controller.signal, AbortSignal.timeout(3000)]),
          });
          if (!response.ok) { configuration = null; throw new Error('Session unavailable'); }
        }
        if (!disposed) setProblem(null);
      } catch {
        configuration = null;
        if (!disposed && !controller.signal.aborted) setProblem('Connection to CyrNava was interrupted. Your local drafts remain available. If CyrNava has stopped, launch its desktop icon again; this tab will reconnect.');
      } finally {
        busy = false;
        if (!disposed && !hidden && configuration?.managed !== false) timer = window.setTimeout(() => void heartbeat(), configuration?.heartbeat_ms || 5000);
      }
    }
    function close() {
      hidden = true; window.clearTimeout(timer);
      if (configuration?.managed) {
        // A small close hint only. Never send note contents or rely on delivery.
        navigator.sendBeacon?.(`/api/lifecycle/sessions/${PAGE_ID}`, new Blob([
          JSON.stringify({ instance: configuration.instance, sequence: ++sequence, action: 'close' }),
        ], { type: 'application/json' }));
      }
    }
    function resume() { hidden = false; window.clearTimeout(timer); void heartbeat(); }
    function visible() { if (document.visibilityState === 'visible') resume(); }
    window.addEventListener('pagehide', close);
    window.addEventListener('pageshow', resume);
    window.addEventListener('online', resume);
    document.addEventListener('visibilitychange', visible);
    void heartbeat();
    return () => {
      disposed = true; controller.abort(); close();
      window.removeEventListener('pagehide', close); window.removeEventListener('pageshow', resume);
      window.removeEventListener('online', resume); document.removeEventListener('visibilitychange', visible);
    };
  }, []);
  return problem;
}
