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

async function installation(testInfo?: TestInfo) {
  const directory = await mkdtemp(join(tmpdir(), 'cyrnava-lifecycle-browser-'));
  const release = join(directory, 'release');
  const state = join(directory, 'state');
  const executable = join(directory, 'launcher-harness.py');
  await cp(join(root, 'ci/lifecycle_harness.py'), executable);
  await writeFile(join(directory, 'harness-source.json'), JSON.stringify({ launcher }));
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
    execFileSync(python, [executable, '--config', config, action], { timeout: 25000 });
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
  const database = join(directory, 'data/engage/engage.sqlite3');
  const journal = join(state, 'p5a-events.jsonl');
  function boundary(action: 'arm' | 'disarm' | 'inspect' | 'verify' | 'marker', expected?: unknown) {
    return JSON.parse(execFileSync(python, [executable, action, database, journal], {
      input: expected ? JSON.stringify(expected) : undefined, encoding: 'utf8', timeout: 10000,
    }));
  }
  async function close(page: Page) {
    await page.evaluate(() => { (window as Window & { __p5aCloseIntent?: boolean }).__p5aCloseIntent = true; });
    boundary('marker');
    await page.close();
  }
  return { url, run, stopped, open, close, boundary,
    events: async () => (await readFile(journal, 'utf8')).trim().split('\n').map((line) => JSON.parse(line)),
    cleanup: async () => {
      try { run('stop'); }
      finally {
        try {
          if (testInfo) {
            await mkdir(testInfo.outputDir, { recursive: true });
            const target = testInfo.outputPath('backend-persistence.jsonl');
            await cp(journal, target);
            await testInfo.attach('backend-persistence', { path: target, contentType: 'application/x-ndjson' });
          }
        } finally { await rm(directory, { recursive: true, force: true }); }
      }
    } };
}


// Only the disposable browser context receives this wrapper. Production assets
// and HTTP code have no instrumentation flag or endpoint.
async function installSaveCorrelation(context: BrowserContext) {
  await context.addInitScript(() => {
    const original = window.fetch.bind(window);
    let sequence = 0;
    window.fetch = (input, init) => {
      const raw = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
      if (init?.method !== 'PATCH' || !new URL(raw, location.href).pathname.startsWith('/api/notes/')) return original(input, init);
      const headers = new Headers(init.headers);
      headers.set('X-P5A-Operation', crypto.randomUUID());
      headers.set('X-P5A-Frontend', JSON.stringify({
        sequence: ++sequence, perf_ms: performance.now(), time_origin_ms: performance.timeOrigin,
        visibility: document.visibilityState,
        close_intent: (window as Window & { __p5aCloseIntent?: boolean }).__p5aCloseIntent === true,
        keepalive: init.keepalive === true, service_worker: !!navigator.serviceWorker?.controller,
      }));
      return original(input, { ...init, headers });
    };
  });
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

for (const browserRouting of [true, false]) {
test('managed tabs close, restart and recover immediately closed unconfirmed edits' + (browserRouting ? '' : ' without browser routing'), async ({ context }, testInfo) => {
  const app = await installation(testInfo);
  await installSaveCorrelation(context);
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
    await app.close(first);
    // Outlive the short test expiration while the second tab keeps renewing.
    await expect.poll(async () => (await fetch(app.url + '/health')).ok).toBe(true);
    await second.getByRole('textbox', { name: 'Note title' }).fill('Second tab remains active');
    await expect(second.getByText('Saved', { exact: true })).toBeVisible();
    await app.close(second); await app.stopped();

    const sqlBoundary = app.boundary('arm');
    // Install the write barrier BEFORE opening the next page. A route added
    // after editor readiness cannot intercept an already dispatched autosave.
    const blockSave = (route: import('@playwright/test').Route) => route.request().method() === 'PATCH' ? route.abort() : route.continue();
    if (browserRouting) await context.route('**/api/notes/*', blockSave);
    app.run('open'); const recovery = await context.newPage();
    const baselineRead = recovery.waitForResponse(isNoteRead);
    await app.open(recovery);
    const baseline = await (await baselineRead).json();
    timeline.record({ event: 'outage-baseline', canonical_revision: baseline.revision });
    // Independent HTTP client, outside Playwright routing: the SQL engine must
    // reject this valid update, and the canonical fingerprint must stay exact.
    const denied = await fetch(app.url + '/api/notes/' + baseline.id, {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ revision: baseline.revision, title: 'Synthetic fault-boundary probe' }),
    });
    expect(denied.status).toBe(503);
    app.boundary('verify', sqlBoundary);
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
    await app.close(recovery); await app.stopped();
    app.run('open'); const reopened = await context.newPage();
    const restartedRead = reopened.waitForResponse(isNoteRead);
    await app.open(reopened);
    const unchanged = await (await restartedRead).json();
    expect(unchanged).toEqual(baseline);
    app.boundary('verify', sqlBoundary);
    timeline.record({ event: 'outage-source-unchanged', canonical_revision: unchanged.revision, base_revision: nativeDraft.base_revision });
    app.boundary('disarm');
    if (browserRouting) await context.unroute('**/api/notes/*', blockSave);
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
    await app.close(reopened); await app.stopped();
  } finally { try { await timeline.finish(); } finally { await app.cleanup(); } }
});


}

test('a committed write with a lost acknowledgement retains its draft and requires conflict review', async ({ context }, testInfo) => {
  const app = await installation(testInfo);
  await installSaveCorrelation(context);
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
    await app.close(page); releaseResponse(); await app.stopped();
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
    await app.close(reopened); await app.stopped();
  } finally { releaseResponse(); try { await timeline.finish(); } finally { await app.cleanup(); } }
});

test('visibility flush is correlated through FastAPI and SQLite, and the SQL boundary rejects it', async ({ context }, testInfo) => {
  const app = await installation(testInfo);
  await installSaveCorrelation(context);
  const timeline = observeRevisions(context, testInfo);
  try {
    app.run('open'); const page = await context.newPage(); await app.open(page);
    await page.getByRole('button', { name: 'New note', exact: true }).click();
    await page.getByRole('dialog').getByLabel('Note title').fill('Visibility causality baseline');
    await page.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(page.getByRole('textbox', { name: 'Note title' })).toHaveValue('Visibility causality baseline');
    const baseline = app.boundary('arm');
    expect(context.serviceWorkers()).toHaveLength(0);
    expect(await page.evaluate(async () => navigator.serviceWorker ? (await navigator.serviceWorker.getRegistrations()).length : 0)).toBe(0);
    await page.getByRole('textbox', { name: 'Note title' }).fill('Synthetic visibility draft');
    // Controlled visibility event, not a claim that this reproduces the exact
    // historical teardown schedule. No browser request interception is used.
    const failed = page.waitForResponse((response) => response.request().method() === 'PATCH');
    await page.evaluate(() => {
      Object.defineProperty(document, 'visibilityState', { configurable: true, get: () => 'hidden' });
      document.dispatchEvent(new Event('visibilitychange'));
    });
    expect((await failed).status()).toBe(503);
    await expect(page.getByText('Save Error', { exact: true })).toBeVisible();
    app.boundary('verify', baseline);
    const events = await app.events();
    const request = [...events].reverse().find((event) => event.event === 'fastapi_request_enter' && event.method === 'PATCH');
    expect(request.frontend).toMatchObject({ visibility: 'hidden', close_intent: false, keepalive: false, service_worker: false });
    const correlated = events.filter((event) => event.operation === request.operation);
    expect(correlated.map((event) => event.event)).toEqual(expect.arrayContaining([
      'fastapi_request_enter', 'database_update_enter', 'sqlite_transaction_failed', 'database_update_failed', 'fastapi_response',
    ]));
    expect(correlated.some((event) => event.event === 'sqlite_commit_complete')).toBe(false);
    expect(await page.evaluate(() => Object.keys(localStorage).filter((key) => key.startsWith('engage.recovery.v1:')).length)).toBe(1);
    app.boundary('disarm');
    const succeeded = page.waitForResponse((response) => response.request().method() === 'PATCH' && response.ok());
    await page.getByRole('button', { name: 'Retry save', exact: true }).click();
    const saved = await (await succeeded).json();
    expect(saved.revision).toBe(baseline.notes[0].revision + 1);
    await expect(page.getByText('Saved', { exact: true })).toBeVisible();
    const committed = await app.events();
    const save = [...committed].reverse().find((event) => event.event === 'database_update_return');
    const chain = committed.filter((event) => event.operation === save.operation);
    const names = chain.map((event) => event.event);
    expect(names.indexOf('fastapi_request_enter')).toBeLessThan(names.indexOf('database_update_enter'));
    expect(names.indexOf('sqlite_commit_complete')).toBeLessThan(names.indexOf('database_update_return'));
    expect(names.indexOf('database_update_return')).toBeLessThan(names.indexOf('fastapi_response'));
    await page.evaluate(() => {
      Reflect.deleteProperty(document, 'visibilityState');
      document.dispatchEvent(new Event('visibilitychange'));
    });
    await app.close(page); await app.stopped();
  } finally { try { await timeline.finish(); } finally { await app.cleanup(); } }
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
