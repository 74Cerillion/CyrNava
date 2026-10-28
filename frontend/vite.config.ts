import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

// Retain the old variable for existing local terminal/task configurations.
const backendPort = Number(process.env.CYRNAVA_API_PORT ?? process.env.ENGAGE_API_PORT ?? '8000');
if (!Number.isInteger(backendPort) || backendPort < 1 || backendPort > 65535) {
  throw new Error('CYRNAVA_API_PORT must be a local TCP port number');
}
const target = `http://127.0.0.1:${backendPort}`;

export default defineConfig({
  plugins: [react()],
  server: {
    host: '127.0.0.1',
    port: 5173,
    strictPort: true,
    proxy: {
      '/api/health': { target, rewrite: () => '/health' },
      '/api': { target },
    },
  },
  // Transform the actual emoji JSON import as Vite does in the browser.
  test: { server: { deps: { inline: [/@blocknote\//, /@emoji-mart\/data/] } }, include: ['src/**/*.test.{ts,tsx}'], environment: 'jsdom', setupFiles: ['./src/test-setup.ts'] },
});
