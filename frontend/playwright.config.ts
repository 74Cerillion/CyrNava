import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e', fullyParallel: false, workers: 1, retries: 0,
  timeout: 120_000, expect: { timeout: 10_000 }, reporter: 'list',
  use: { browserName: 'chromium', headless: true, viewport: { width: 1280, height: 1000 }, screenshot: 'only-on-failure', trace: 'retain-on-failure' },
});
