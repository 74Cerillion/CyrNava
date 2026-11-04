// Actual Qt WebEngine tests using the project's existing Playwright installation.
// CDP is explicitly test-only. Never opens a personal browser/profile.
import { expect, chromium } from '../../frontend/node_modules/@playwright/test/index.mjs';
import { spawn, execFile } from 'node:child_process';
import { readFile, writeFile, readdir } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { performance } from 'node:perf_hooks';
import { createServer } from 'node:http';

const directory = dirname(fileURLToPath(import.meta.url));
const python = process.argv[2] || '/tmp/cyrnava-p1/venv/bin/python';
const results = { journeys: [], launches: [], note: 'synthetic only; unauthenticated test CDP; no production profiles', platform: process.env.QT_QPA_PLATFORM || 'wayland' };
let current;

async function until(callback, timeout = 20_000) {
  const end = Date.now() + timeout;
  let last;
  while (Date.now() < end) {
    try { const value = await callback(); if (value) return value; } catch (error) { last = error; }
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  throw last || new Error('Timed out');
}

async function launch(workspace) {
  const started = performance.now();
  const args = [join(directory, 'desktop.py'), '--test-cdp'];
  if (workspace) args.push('--workspace', workspace);
  const child = spawn(python, args, {
    cwd: directory, stdio: ['pipe', 'pipe', 'pipe'],
    env: { ...process.env, QT_QPA_PLATFORM: results.platform },
  });
  const state = { child, events: [], stderr: '', stdout: '' };
  current = state;
  let pending = '';
  child.stdout.on('data', chunk => {
    state.stdout += chunk;
    pending += chunk;
    while (pending.includes('\n')) {
      const end = pending.indexOf('\n'); const line = pending.slice(0, end); pending = pending.slice(end + 1);
      try { state.events.push(JSON.parse(line)); } catch { /* Qt diagnostics are separate. */ }
    }
  });
  child.stderr.on('data', chunk => { state.stderr += chunk; });
  child.on('error', error => { state.stderr += error.message; });
  await until(() => {
    if (child.exitCode !== null || child.signalCode) throw new Error(state.stderr);
    return state.events.find(event => event.event === 'frontend-loaded');
  });
  state.metrics = state.events.find(event => event.event === 'frontend-loaded');
  state.workspace = state.metrics.workspace;
  state.origin = state.metrics.origin;
  // Qt lacks Browser.setDownloadBehavior; noDefaults avoids that unrelated override.
  state.browser = await chromium.connectOverCDP(`http://127.0.0.1:${state.metrics.test_cdp}`, { noDefaults: true });
  state.page = state.browser.contexts()[0].pages().find(page => page.url().startsWith(state.origin));
  state.page.setDefaultTimeout(10_000);
  await expect(state.page.getByRole('combobox', { name: 'Appearance', exact: true })).toBeVisible();
  state.interactiveMs = Math.round((performance.now() - started) * 100) / 100;
  results.launches.push({ workspace: state.workspace, interactive_ms: state.interactiveMs, backend_ready_ms: state.metrics.backend_ready_ms, frontend_loaded_ms: state.metrics.frontend_loaded_ms });
  return state;
}

async function finished(state, graceful = true) {
  if (state.child.exitCode === null && !state.child.signalCode) {
    if (graceful) state.child.stdin.write('CLOSE\n');
    else state.child.kill('SIGTERM');
    await until(() => state.child.exitCode !== null || state.child.signalCode, 18_000);
  }
  await state.browser?.close().catch(() => {});
  await until(async () => {
    try { await fetch(state.origin + '/health', { signal: AbortSignal.timeout(300) }); return false; }
    catch { return true; }
  });
  const metrics = JSON.parse(await readFile(join(state.workspace, 'metrics.json'), 'utf8'));
  results.launches.at(-1).shutdown_ms = metrics.shutdown_ms;
  results.launches.at(-1).backend_exit_code = metrics.backend_exit_code;
  results.launches.at(-1).console_errors = metrics.console_errors;
  results.launches.at(-1).blocked_requests = metrics.blocked_requests;
  results.sandbox = metrics.sandbox_diagnostic;
  results.sandboxComplete = /Layer 1 Sandbox\s+(?!None)(?:Namespace|SUID)/i.test(metrics.sandbox_diagnostic || '')
    && /Seccomp-BPF sandbox\s+Yes/.test(metrics.sandbox_diagnostic || '');
  await writeFile(join(state.workspace, 'qt-stderr.txt'), state.stderr, { mode: 0o600 });
}

async function api(path, init) {
  const response = await fetch(current.origin + path, init);
  if (!response.ok) throw new Error(`API ${response.status}: ${path}`);
  return response.json();
}
async function saved(page) { await expect(page.getByText('Saved', { exact: true })).toBeVisible(); }
async function create(page, kind, title) {
  await page.getByRole('button', { name: `New ${kind}`, exact: true }).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByRole('textbox', { name: kind === 'note' ? 'Note title' : 'Name', exact: true }).fill(title);
  await dialog.getByRole('button', { name: 'Create', exact: true }).click();
  await expect(dialog).toBeHidden();
}
async function memoryTree(rootPid) {
  const processes = [];
  for (const name of await readdir('/proc')) {
    if (!/^\d+$/.test(name)) continue;
    try {
      const status = await readFile(`/proc/${name}/status`, 'utf8');
      processes.push({ pid: Number(name), ppid: Number(status.match(/^PPid:\s+(\d+)/m)[1]), status });
    } catch { /* Exited while sampled. */ }
  }
  const owned = new Set([rootPid]);
  for (let changed = true; changed;) {
    changed = false;
    for (const process of processes) if (owned.has(process.ppid) && !owned.has(process.pid)) { owned.add(process.pid); changed = true; }
  }
  const samples = [];
  for (const process of processes.filter(process => owned.has(process.pid))) {
    let pss = null;
    try { pss = Number((await readFile(`/proc/${process.pid}/smaps_rollup`, 'utf8')).match(/^Pss:\s+(\d+)/m)[1]); } catch { /* Report unavailable. */ }
    const command = (await readFile(`/proc/${process.pid}/cmdline`, 'utf8').catch(() => '')).replaceAll('\0', ' ');
    samples.push({ pid: process.pid, role: command.includes('--type=renderer') ? 'renderer' : command.includes('--worker') ? 'backend' : process.pid === rootPid ? 'desktop' : 'webengine-helper', rss_kib: Number(process.status.match(/^VmRSS:\s+(\d+)/m)?.[1] || 0), pss_kib: pss, seccomp: Number(process.status.match(/^Seccomp:\s+(\d+)/m)?.[1]), no_new_privs: Number(process.status.match(/^NoNewPrivs:\s+(\d+)/m)?.[1]) });
  }
  return { process_count: samples.length, rss_sum_kib: samples.reduce((n, p) => n + p.rss_kib, 0), pss_sum_kib: samples.every(p => p.pss_kib !== null) ? samples.reduce((n, p) => n + p.pss_kib, 0) : null, samples };
}

try {
  current = await launch();
  const workspace = current.workspace;
  let page = current.page;
  const duplicate = await new Promise(resolve => execFile(python, [join(directory, 'desktop.py'), '--workspace', workspace], { env: process.env }, (error, stdout, stderr) => resolve({ error, stdout, stderr })));
  expect(duplicate.error?.code).toBe(1);
  expect(duplicate.stderr).toContain('Resource temporarily unavailable');
  results.journeys.push('duplicate disposable-workspace launch refused before a second backend');
  let canaryRequests = 0;
  const canary = createServer((_request, response) => { ++canaryRequests; response.end('should not be reached'); });
  await new Promise(resolve => canary.listen(0, '127.0.0.1', resolve));
  try {
    const address = `http://127.0.0.1:${canary.address().port}/canary`;
    expect(await page.evaluate(url => fetch(url).then(() => true).catch(() => false), address)).toBe(false);
    expect(canaryRequests).toBe(0);
    results.journeys.push('different-origin fetch blocked before reaching an owned loopback canary');
  } finally { await new Promise(resolve => canary.close(resolve)); }
  await create(page, 'folder', 'P1 synthetic folder');
  await create(page, 'note', 'Qt native proof');
  const editor = () => page.getByRole('region', { name: 'Note editor' }).getByRole('textbox');
  await editor().click();
  await page.keyboard.type('# Native desktop heading'); await page.keyboard.press('Enter');
  await page.keyboard.type('A persistent paragraph with ');
  await page.keyboard.press('Control+b'); await page.keyboard.type('bold evidence'); await page.keyboard.press('Control+b');
  await page.keyboard.type(' and local content.'); await page.keyboard.press('Enter');
  await page.keyboard.type('```'); await page.keyboard.press('Space');
  await page.keyboard.type('print("local-only text")');
  await page.keyboard.press('ArrowDown'); await page.keyboard.press('Control+End');
  await page.keyboard.press('Enter'); await page.keyboard.press('Enter');
  await saved(page);
  await expect(editor().getByRole('heading', { name: 'Native desktop heading', exact: true })).toBeVisible();
  await expect(editor().locator('strong')).toContainText('bold evidence');
  await expect(editor().locator('[data-content-type="codeBlock"]')).toContainText('local-only text');
  results.journeys.push('native BlockNote heading, paragraph, bold and code editing');

  await editor().click(); await page.keyboard.press('Control+End'); await page.keyboard.press('Enter');
  current.child.stdin.write('PASTE_SCREENSHOT\n');
  await expect(editor().locator('img')).toHaveCount(1);
  await expect.poll(() => editor().locator('img').evaluateAll(images => images.every(image => image.complete && image.naturalWidth > 0))).toBe(true);
  await saved(page);
  results.journeys.push('native Qt clipboard screenshot paste, API upload and image decode');

  await editor().click(); await page.keyboard.press('Control+End'); await page.keyboard.press('ArrowDown'); await page.keyboard.press('Enter');
  await page.keyboard.type('/image');
  await page.locator('.bn-suggestion-menu').getByText('Image', { exact: true }).click();
  const chooser = page.waitForEvent('filechooser');
  await page.getByRole('button', { name: 'Upload image', exact: true }).click();
  await (await chooser).setFiles(join(workspace, 'synthetic-screenshot.png'));
  await expect(editor().locator('img')).toHaveCount(2);
  await saved(page);
  const tree = await api('/api/tree');
  const note = tree.notes.find(note => note.title === 'Qt native proof');
  const original = await api(`/api/notes/${note.id}`);
  results.journeys.push('image-selector upload and canonical native JSON persistence');

  await create(page, 'note', 'Navigation target');
  await page.getByRole('combobox', { name: 'Search all notes' }).fill('native');
  await page.getByRole('listbox').getByRole('option').first().click();
  await expect(page.getByRole('textbox', { name: 'Note title', exact: true })).toHaveValue('Qt native proof');
  await expect(editor().locator('img')).toHaveCount(2);
  await page.getByRole('combobox', { name: 'Appearance', exact: true }).selectOption('cyrnava');
  await page.evaluate(() => window.scrollTo(0, 0));
  current.child.stdin.write('CAPTURE\n');
  await until(() => current.events.find(event => event.event === 'captured'));
  await page.getByRole('button', { name: 'Hide navigation', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Show navigation', exact: true })).toBeVisible();
  results.memory = await memoryTree(current.child.pid);
  await finished(current);
  results.journeys.push('tree/search navigation and clean desktop-owned backend shutdown');

  current = await launch(workspace); page = current.page;
  await expect(page.getByRole('textbox', { name: 'Note title', exact: true })).toHaveValue('Qt native proof');
  await expect(page.getByRole('combobox', { name: 'Appearance', exact: true })).toHaveValue('cyrnava');
  await expect(page.getByRole('button', { name: 'Show navigation', exact: true })).toBeVisible();
  await expect(editor().locator('img')).toHaveCount(2);
  await expect(editor().getByRole('heading', { name: 'Native desktop heading', exact: true })).toBeVisible();
  expect((await api(`/api/notes/${note.id}`)).document_json).toEqual(original.document_json);
  await expect.poll(() => editor().locator('img').evaluateAll(images => images.every(image => image.complete && image.naturalWidth > 0))).toBe(true);
  results.journeys.push('full Qt/backend restart preserves SQLite JSON, images, preferred note and appearance/navigation preferences');

  const backendPid = current.metrics.backend_pid;
  const command = await readFile(`/proc/${backendPid}/cmdline`, 'utf8');
  if (!command.includes('--worker') || !command.includes(workspace)) throw new Error('Refusing to signal an unidentified backend');
  process.kill(backendPid, 'SIGTERM');
  await until(async () => { try { await fetch(current.origin + '/health'); return false; } catch { return true; } });
  await page.getByRole('textbox', { name: 'Note title', exact: true }).fill('Recovered Qt draft');
  await expect(page.getByText('Save Error', { exact: true })).toBeVisible();
  await expect.poll(() => page.evaluate(() => Object.keys(localStorage).some(key => key.startsWith('engage.recovery.v1:')))).toBe(true);
  current.child.stdin.write('CLOSE_KEEP_OPEN\n');
  const stay = await until(() => current.events.find(event => event.event === 'close-choice' && event.choice === 'Keep open'));
  expect(stay.default).toBe('Keep open');
  expect(current.child.exitCode).toBe(null);
  await expect(page.getByText('Save Error', { exact: true })).toBeVisible();
  current.child.stdin.write('CLOSE_RETAIN_DRAFT\n');
  await until(() => current.child.exitCode !== null || current.child.signalCode);
  await finished(current);
  results.journeys.push('failed-save close dialog defaults to Keep open and explicitly closes without deleting the disposable profile');
  current = await launch(workspace); page = current.page;
  await page.getByRole('button', { name: 'Recover draft', exact: true }).click();
  await saved(page);
  await expect(page.getByRole('textbox', { name: 'Note title', exact: true })).toHaveValue('Recovered Qt draft');
  expect((await api(`/api/notes/${note.id}`)).title).toBe('Recovered Qt draft');
  await page.reload(); await saved(page);
  results.journeys.push('backend outage and persistent Qt localStorage draft recovery after desktop restart');
  const navigationCanary = createServer((_request, response) => { ++canaryRequests; response.end('should not be reached'); });
  await new Promise(resolve => navigationCanary.listen(0, '127.0.0.1', resolve));
  try {
    const address = `http://127.0.0.1:${navigationCanary.address().port}/blocked-navigation`;
    await page.evaluate(url => { const link = document.createElement('a'); link.href = url; document.body.append(link); link.click(); link.remove(); }, address);
    expect(page.url()).toBe(current.origin + '/');
    expect(canaryRequests).toBe(0);
    results.journeys.push('native page rejects different-origin main-frame navigation');
  } finally { await new Promise(resolve => navigationCanary.close(resolve)); }
  await finished(current);
  results.compatibilityPassed = true;
} catch (error) {
  results.compatibilityPassed = false;
  results.error = error.stack;
  if (current?.page) await current.page.screenshot({ path: join(current.workspace, 'failure.png') }).catch(() => {});
  if (current) {
    await writeFile(join(current.workspace || '/tmp/cyrnava-p1', 'failure-stderr.txt'), current.stderr).catch(() => {});
    if (current.child.exitCode === null && !current.child.signalCode) {
      current.child.kill('SIGTERM');
      try { await until(() => current.child.exitCode !== null || current.child.signalCode, 3000); }
      catch { current.child.kill('SIGKILL'); }
    }
    await current.browser?.close().catch(() => {});
  }
} finally {
  await writeFile('/tmp/cyrnava-p1/verification.json', JSON.stringify(results, null, 2) + '\n', { mode: 0o600 });
  console.log(JSON.stringify(results, null, 2));
  process.exitCode = !results.compatibilityPassed ? 1 : results.sandboxComplete ? 0 : 2;
}
