import react from '@vitejs/plugin-react';
import { defineConfig } from 'vitest/config';

const backendPort = Number(process.env.ENGAGE_API_PORT || '8000');
if (!Number.isInteger(backendPort) || backendPort < 1 || backendPort > 65535) {
  throw new Error('ENGAGE_API_PORT must be a local TCP port number');
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
  test: { include: ['src/**/*.test.{ts,tsx}'], environment: 'jsdom', setupFiles: ['./src/test-setup.ts'] },
});
