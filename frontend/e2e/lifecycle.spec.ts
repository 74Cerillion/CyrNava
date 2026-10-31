import { test, expect } from '@playwright/test';
import type { BrowserContext, Page, TestInfo } from '@playwright/test';
import { execFileSync } from 'node:child_process';
import { cp, mkdtemp, mkdir, readFile, rm, symlink, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, resolve } from 'node:path';
import { createServer } from 'node:net';

const root = resolve('..');
const python = join(root, 'backend/.venv/bin/python');
const launcher = join(root, 'desktop/launcher.py');

async function installation() {
  const directory = await mkdtemp(join(tmpdir(), 'cyrnava-lifecycle-browser-'));
  const release = join(directory, 'release');
  const state = join(directory, 'state');
  await mkdir(join(release, 'backend'), { recursive: true }); await mkdir(join(release, 'frontend'));
  await mkdir(state, { mode: 0o700 });
  await symlink(join(root, 'backend/app'), join(release, 'backend/app'));
  await symlink(join(root, 'backend/.venv'), join(release, 'backend/.venv'));
  // Snapshot the build: a concurrent source rebuild must not alter this app.
  await cp(join(root, 'frontend/dist'), join(release, 'frontend/dist'), { recursive: true });
  const probe = createServer(); await new Promise<void>((done) => probe.listen(0, '127.0.0.1', done));
  const address = probe.address(); if (!address || typeof address === 'string') throw new Error('No test port');
  const port = address.port; await new Promise<void>((done) => probe.close(() => done()));
  const config = join(directory, 'config.json');
  await writeFile(config, JSON.stringify({ release, state_dir: state, data_home: join(directory, 'data'), port,
    // Graphical dispatch is stubbed. Playwright opens the real isolated browser.
    browser: '/bin/true', opener: '/bin/true', zenity: '/bin/true',
    lifecycle: { heartbeat: 0.1, expiration: 1.2, grace: 0.4, startup: 10 } }));
  const url = `http://127.0.0.1:${port}`;
  let launches = 0;
  function run(action: 'open' | 'stop') {
    execFileSync(python, [launcher, '--config', config, action], { timeout: 25000 });
    if (action === 'open') launches++;
  }
  async function stopped() {
    await expect.poll(async () => {
      try { await fetch(url + '/health', { signal: AbortSignal.timeout(500) }); return false; }
      catch { return true; }
    }, { timeout: 10000, message: 'Final session releases backend port' }).toBe(true);
    // The supervisor logs this only after wait() has reaped its own child.
    await expect.poll(async () => (await readFile(join(state, 'launcher.log'), 'utf8')).split('Supervisor reaped backend and exited').length - 1).toBe(launches);
    const check = createServer();
    await new Promise<void>((done, reject) => { check.once('error', reject); check.listen(port, '127.0.0.1', done); });
    await new Promise<void>((done) => check.close(() => done()));
  }
  async function open(page: Page) {
    const registered = page.waitForResponse((response) => response.url().includes('/api/lifecycle/sessions/') && response.ok(), { timeout: 10000 });
    await page.goto(url); await registered;
  }
  return { url, run, stopped, open, cleanup: async () => { run('stop'); await rm(directory, { recursive: true, force: true }); } };
}


// Synthetic-test diagnostics: revisions, status and relative timing only. Never
// copy request headers, session credentials, titles or document contents here.
function observeRevisions(context: BrowserContext, testInfo: TestInfo) {
  const events: object[] = [];
  const started = Date.now();
  const record = (value: object) => events.push({ ms: Date.now() - started, ...value });
  const request = (request: import('@playwright/test').Request) => {
    if (!new URL(request.url()).pathname.startsWith('/api/notes/')) return;
    const body = request.postData();
    record({ event: 'request', method: request.method(), revision: body ? JSON.parse(body).revision : undefined });
  };
  const response = async (response: import('@playwright/test').Response) => {
    if (!new URL(response.url()).pathname.startsWith('/api/notes/')) return;
    try {
      const body = await response.json();
      record({ event: 'response', method: response.request().method(), status: response.status(), revision: body.revision });
    } catch { /* A closing page may discard its response; checkpoints verify SQLite. */ }
  };
  context.on('request', request); context.on('response', response);
  return { record, finish: async () => {
    context.off('request', request); context.off('response', response);
    await mkdir(testInfo.outputDir, { recursive: true });
    const path = testInfo.outputPath('revision-timeline.json');
    await writeFile(path, JSON.stringify(events, null, 2));
    await testInfo.attach('revision-timeline', { path, contentType: 'application/json' });
  } };
}

const isNoteRead = (response: import('@playwright/test').Response) =>
  response.request().method() === 'GET' && /\/api\/notes\/[^/]+$/.test(new URL(response.url()).pathname) && response.ok();

test('managed tabs close, restart and recover immediately closed unconfirmed edits', async ({ context }, testInfo) => {
  const app = await installation();
  const timeline = observeRevisions(context, testInfo);
  try {
    app.run('open'); const first = await context.newPage(); await app.open(first);
    await first.getByRole('button', { name: 'New note', exact: true }).click();
    await first.getByRole('dialog').getByLabel('Note title').fill('Lifecycle evidence');
    await first.getByRole('button', { name: 'Create', exact: true }).click();
    const content = first.getByRole('textbox', { name: 'Note content' });
    await content.click(); await first.keyboard.type('Confirmed paragraph.');
    await expect(first.getByText('Saved', { exact: true })).toBeVisible();
    const second = await context.newPage(); await app.open(second);
    await expect(second.getByRole('textbox', { name: 'Note content' })).toContainText('Confirmed paragraph.');
    await first.close();
    // Outlive the short test expiration while the second tab keeps renewing.
    await expect.poll(async () => (await fetch(app.url + '/health')).ok).toBe(true);
    await second.getByRole('textbox', { name: 'Note title' }).fill('Second tab remains active');
    await expect(second.getByText('Saved', { exact: true })).toBeVisible();
    await second.close(); await app.stopped();

    // Install the write barrier BEFORE opening the next page. A route added
    // after editor readiness cannot intercept an already dispatched autosave.
    const blockSave = (route: import('@playwright/test').Route) => route.request().method() === 'PATCH' ? route.abort() : route.continue();
    await context.route('**/api/notes/*', blockSave);
    app.run('open'); const recovery = await context.newPage();
    const baselineRead = recovery.waitForResponse(isNoteRead);
    await app.open(recovery);
    const baseline = await (await baselineRead).json();
    timeline.record({ event: 'outage-baseline', canonical_revision: baseline.revision });
    await expect(recovery.getByRole('textbox', { name: 'Note content' })).toContainText('Confirmed paragraph.');
    // Context routing survives page.close and remains until restart verifies
    // that neither startup edits nor visibility-triggered flushes committed.
    await recovery.getByRole('textbox', { name: 'Note title' }).fill('Immediately closed draft');
    const paragraph = recovery.getByRole('textbox', { name: 'Note content' }).locator('p').first();
    await paragraph.evaluate((element) => {
      element.closest<HTMLElement>('[contenteditable="true"]')!.focus();
      const range = document.createRange(); range.selectNodeContents(element); range.collapse(false);
      const selection = window.getSelection()!; selection.removeAllRanges(); selection.addRange(range);
    });
    await expect.poll(() => paragraph.evaluate((element) => element.contains(window.getSelection()!.anchorNode))).toBe(true);
    await recovery.keyboard.press('Control+b');
    await recovery.keyboard.type(' Unconfirmed paragraph 🚀.'); await recovery.keyboard.press('Control+b');
    await expect(recovery.getByRole('textbox', { name: 'Note content' }).locator('strong')).toContainText('Unconfirmed paragraph 🚀.');
    const nativeDraft = await recovery.evaluate(() => {
      const name = Object.keys(localStorage).find((key) => key.startsWith('engage.recovery.v1:'))!;
      return JSON.parse(localStorage.getItem(name)!);
    });
    expect(nativeDraft.base_revision).toBe(baseline.revision);
    timeline.record({ event: 'retained-draft', base_revision: nativeDraft.base_revision });
    await expect(recovery.getByText('Unsaved Changes', { exact: true })).toBeVisible();
    // page.close skips beforeunload prompting; it cannot help this recovery test.
    await recovery.close(); await app.stopped();
    app.run('open'); const reopened = await context.newPage();
    const restartedRead = reopened.waitForResponse(isNoteRead);
    await app.open(reopened);
    const unchanged = await (await restartedRead).json();
    expect(unchanged).toEqual(baseline);
    timeline.record({ event: 'outage-source-unchanged', canonical_revision: unchanged.revision, base_revision: nativeDraft.base_revision });
    await context.unroute('**/api/notes/*', blockSave);
    await expect(reopened.getByRole('heading', { name: 'Recover unsaved edits' })).toBeVisible();
    const savedResponse = reopened.waitForResponse((response) => response.request().method() === 'PATCH' && response.ok());
    await reopened.getByRole('button', { name: 'Recover draft', exact: true }).click();
    const acknowledged = await (await savedResponse).json();
    expect(acknowledged.revision).toBe(nativeDraft.base_revision + 1);
    expect(acknowledged.document_json).toEqual(nativeDraft.document_json);
    timeline.record({ event: 'recovery-acknowledged', revision: acknowledged.revision });
    await expect(reopened.getByText('Saved', { exact: true })).toBeVisible();
    await reopened.reload();
    await expect(reopened.getByRole('textbox', { name: 'Note title' })).toHaveValue('Immediately closed draft');
    await expect(reopened.getByRole('textbox', { name: 'Note content' })).toContainText('Unconfirmed paragraph 🚀.');
    await expect(reopened.getByRole('textbox', { name: 'Note content' }).locator('strong')).toContainText('Unconfirmed paragraph 🚀.');
    const response = await fetch(app.url + '/api/notes/' + nativeDraft.note_id);
    expect((await response.json()).document_json).toEqual(nativeDraft.document_json);
    await expect(reopened.getByRole('heading', { name: 'Recover unsaved edits' })).toHaveCount(0);
    await reopened.close(); await app.stopped();
  } finally { try { await timeline.finish(); } finally { await app.cleanup(); } }
});


test('a committed write with a lost acknowledgement retains its draft and requires conflict review', async ({ context }, testInfo) => {
  const app = await installation();
  const timeline = observeRevisions(context, testInfo);
  let releaseResponse!: () => void;
  const responseGate = new Promise<void>((resolve) => { releaseResponse = resolve; });
  try {
    app.run('open'); const page = await context.newPage(); await app.open(page);
    await page.getByRole('button', { name: 'New note', exact: true }).click();
    await page.getByRole('dialog').getByLabel('Note title').fill('Acknowledgement gate');
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('textbox', { name: 'Note title' })).toHaveValue('Acknowledgement gate');
    let committed!: (revision: number) => void;
    const backendCommitted = new Promise<number>((resolve) => { committed = resolve; });
    let intercepted = false;
    await context.route('**/api/notes/*', async (route) => {
      if (route.request().method() !== 'PATCH') return route.continue();
      if (intercepted) return route.abort();
      intercepted = true;
      // Commit through the real API, but withhold only this response. No sleep,
      // timeout increase, request retry or application code hook is involved.
      const response = await route.fetch({ maxRetries: 0 });
      expect(response.ok()).toBe(true);
      const saved = await response.json();
      timeline.record({ event: 'backend-committed-acknowledgement-held', revision: saved.revision });
      committed(saved.revision);
      await responseGate;
      await route.fulfill({ response }).catch(() => { /* The old page is closed. */ });
    });
    await page.getByRole('textbox', { name: 'Note title' }).fill('Committed before close');
    const committedRevision = await backendCommitted;
    await page.getByRole('textbox', { name: 'Note title' }).fill('Unconfirmed newer title');
    const retained = await page.evaluate(() => {
      const key = Object.keys(localStorage).find((name) => name.startsWith('engage.recovery.v1:'))!;
      return JSON.parse(localStorage.getItem(key)!);
    });
    expect(retained.base_revision).toBe(committedRevision - 1);
    timeline.record({ event: 'retained-before-close', base_revision: retained.base_revision });
    await page.close(); releaseResponse(); await app.stopped();
    await context.unrouteAll({ behavior: 'wait' });
    app.run('open'); const reopened = await context.newPage(); await app.open(reopened);
    await expect(reopened.getByRole('heading', { name: 'Recover unsaved edits' })).toBeVisible();
    let writesAfterChoice = 0;
    const countWrite = (request: import('@playwright/test').Request) => {
      if (request.method() === 'PATCH' && /\/api\/notes\//.test(request.url())) writesAfterChoice++;
    };
    context.on('request', countWrite);
    await reopened.getByRole('button', { name: 'Recover draft', exact: true }).click();
    await expect(reopened.getByText('Save Error', { exact: true })).toBeVisible();
    await expect(reopened.getByRole('button', { name: 'Review conflict and recover' })).toBeVisible();
    const current = await (await fetch(app.url + '/api/notes/' + retained.note_id)).json();
    expect(current.revision).toBe(committedRevision);
    expect(current.title).toBe('Committed before close');
    const drafts = await reopened.evaluate(() => Object.keys(localStorage)
      .filter((name) => name.startsWith('engage.recovery.v1:')).map((name) => JSON.parse(localStorage.getItem(name)!)));
    expect(drafts).toContainEqual(retained);
    expect(writesAfterChoice).toBe(0);
    timeline.record({ event: 'stale-draft-protected', canonical_revision: current.revision, base_revision: retained.base_revision, writes_after_choice: writesAfterChoice });
    context.off('request', countWrite);
    await reopened.close(); await app.stopped();
  } finally { releaseResponse(); try { await timeline.finish(); } finally { await app.cleanup(); } }
});

test('killed isolated browser leaves no managed backend after lease expiry', async ({ playwright, browserName }) => {
  const app = await installation();
  let server: Awaited<ReturnType<typeof playwright.chromium.launchServer>> | undefined;
  try {
    server = await playwright[browserName].launchServer({ headless: true });
    app.run('open');
    const browser = await playwright[browserName].connect(server.wsEndpoint());
    const page = await browser.newPage(); await app.open(page);
    // Exact test-owned browser process, never the user's normal Firefox.
    server.process().kill('SIGKILL');
    await app.stopped();
  } finally { await server?.close().catch(() => {}); await app.cleanup(); }
});
