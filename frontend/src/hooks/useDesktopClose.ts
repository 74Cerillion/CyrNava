import { useEffect, useLayoutEffect, useRef, useState } from 'react';
import { mutationState, waitForMutations } from '../pendingMutations';

export interface CloseProtocol {
  request: (id: string) => void;
  state: (id: string) => 'waiting' | 'saved' | 'error' | 'unknown';
  cancel: (id: string) => void;
}
declare global { interface Window { __cyrnavaDesktop?: CloseProtocol } }

// Native-initiated, bounded save handshake. No OS capabilities or secrets cross
// this boundary; ordinary Firefox sessions never invoke it.
export function useDesktopClose(flush: (deadline: number) => Promise<boolean>) {
  const latest = useRef(flush);
  useLayoutEffect(() => { latest.current = flush; }, [flush]);
  const [closing, setClosing] = useState(false);
  useEffect(() => {
    let current: { id: string; status: 'waiting' | 'saved' | 'error' } | null = null;
    const protocol: CloseProtocol = {
      request(id) {
        if (current || !/^[a-f0-9]{32}$/.test(id)) return;
        const attempt = { id, status: 'waiting' as 'waiting' | 'saved' | 'error' };
        current = attempt; setClosing(true);
        const initialFailures = mutationState().failures;
        const deadline = Date.now() + 40_000;
        void (async () => {
          try {
            // Commit the editing lock before draining an already running action.
            await new Promise((resolve) => window.setTimeout(resolve, 0));
            await waitForMutations(deadline);
            const saved = await latest.current(deadline);
            await waitForMutations(deadline);
            if (current === attempt) attempt.status = saved && mutationState().failures === initialFailures ? 'saved' : 'error';
          } catch { if (current === attempt) attempt.status = 'error'; }
        })();
      },
      state(id) { return current?.id === id ? current.status : 'unknown'; },
      cancel(id) { if (current?.id === id) { current = null; setClosing(false); } },
    };
    window.__cyrnavaDesktop = protocol;
    return () => { current = null; if (window.__cyrnavaDesktop === protocol) delete window.__cyrnavaDesktop; };
  }, []);
  return closing;
}
