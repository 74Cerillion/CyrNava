import { afterEach, beforeEach, expect, it, vi } from 'vitest';

beforeEach(() => { vi.resetModules(); vi.stubEnv('CYRNAVA_API_PORT', undefined); vi.stubEnv('ENGAGE_API_PORT', undefined); });
afterEach(() => vi.unstubAllEnvs());
it.each([
  [undefined, undefined, 8000], [undefined, '8010', 8010], ['8020', '8010', 8020],
])('resolves canonical and legacy API port configuration (%s, %s)', async (current, legacy, port) => {
  vi.stubEnv('CYRNAVA_API_PORT', current); vi.stubEnv('ENGAGE_API_PORT', legacy);
  const { default: config } = await import('../vite.config');
  expect(config.server?.proxy?.['/api']).toEqual({ target: `http://127.0.0.1:${port}` });
});
it('rejects an invalid canonical port instead of silently falling back to legacy configuration', async () => {
  vi.stubEnv('CYRNAVA_API_PORT', 'invalid'); vi.stubEnv('ENGAGE_API_PORT', '8010');
  await expect(import('../vite.config')).rejects.toThrow('CYRNAVA_API_PORT');
});
