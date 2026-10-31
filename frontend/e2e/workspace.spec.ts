import { test, expect } from '@playwright/test';
import { editorSelection, paragraphCursor } from './editorSelection';
import type { Locator, Page } from '@playwright/test';
import { spawn, execFileSync } from 'node:child_process';
import type { ChildProcess } from 'node:child_process';
import { mkdtemp, mkdir, readFile, rename, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createServer } from 'node:net';

const frontend = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const backend = resolve(frontend, '../backend');
const python = join(backend, '.venv/bin/python');
const releaseMode = (process.env.CYRNAVA_E2E_RELEASE ?? process.env.ENGAGE_E2E_RELEASE) === '1';

async function freePort(): Promise<number> {
  const server = createServer();
  await new Promise<void>((done) => server.listen(0, '127.0.0.1', done));
  const address = server.address();
  if (!address || typeof address === 'string') throw new Error('Cannot allocate test port');
  const port = address.port;
  await new Promise<void>((done, reject) => server.close((error) => error ? reject(error) : done()));
  return port;
}
async function stop(child: ChildProcess | undefined) {
  if (!child || !child.pid || child.exitCode !== null || child.signalCode !== null) return;
  await new Promise<void>((done) => {
    child.once('exit', () => { clearTimeout(timer); done(); });
    const timer = setTimeout(() => child.kill('SIGKILL'), 5000);
    child.kill('SIGTERM');
  });
}
async function ready(url: string, child: ChildProcess) {
  await expect.poll(async () => {
    if (!child.pid || child.exitCode !== null || child.signalCode !== null) throw new Error('Test development server exited before startup');
    try { return (await fetch(url)).ok; } catch { return false; }
  }, { timeout: 15_000 }).toBe(true);
}
async function environment() {
  // No option to target an existing profile/server. Every test owns its children.
  const directory = await mkdtemp(join(tmpdir(), 'cyrnava-workspace-e2e-'));
  const backendPort = await freePort(); const frontendPort = releaseMode ? backendPort : await freePort();
  const api = `http://127.0.0.1:${backendPort}`; const url = `http://127.0.0.1:${frontendPort}`;
  let server: ChildProcess | undefined; let vite: ChildProcess | undefined;
  let data = join(directory, 'original-data'); let logs = '';
  function launch(command: string, args: string[], cwd: string) {
    const child = spawn(command, args, { cwd, env: { ...process.env, XDG_DATA_HOME: data, CYRNAVA_API_PORT: String(backendPort) }, stdio: ['ignore', 'pipe', 'pipe'] });
    child.stdout?.on('data', (chunk) => { logs += chunk.toString(); });
    child.stderr?.on('data', (chunk) => { logs += chunk.toString(); });
    child.on('error', (error) => { logs += error.message; });
    return child;
  }
  async function startBackend() {
    server = launch(python, releaseMode ? ['-m', 'app', '--port', String(backendPort)] : ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(backendPort)], backend);
    await ready(`${api}/health`, server);
  }
  async function start() {
    await startBackend();
    if (releaseMode) return;
    vite = launch(process.execPath, ['node_modules/vite/bin/vite.js', '--port', String(frontendPort)], frontend);
    await ready(url, vite);
  }
  async function shutdown() { await stop(server); await stop(vite); server = undefined; vite = undefined; }
  function cli(args: string[]) { return execFileSync(python, ['-m', 'app.backup', ...args], { cwd: backend, encoding: 'utf8' }); }
  return { directory, api, url, start, shutdown, startBackend, stopBackend: async () => { await stop(server); server = undefined; },
    profile: () => join(data, 'engage'), cli,
    restoreTo: (path: string) => { data = path; }, logs: () => logs };
}
async function saved(page: Page) { await expect(page.getByText('Saved', { exact: true })).toBeVisible(); }
async function create(page: Page, kind: 'folder' | 'note', name: string) {
  await page.getByRole('button', { name: `New ${kind}`, exact: true }).click();
  const dialog = page.getByRole('dialog');
  await dialog.getByRole('textbox', { name: kind === 'note' ? 'Note title' : 'Name', exact: true }).fill(name);
  await dialog.getByRole('button', { name: 'Create', exact: true }).click();
  await expect(dialog).toBeHidden();
  await expect(page.getByRole('button', { name: 'New folder', exact: true })).toBeEnabled();
}
async function getJson(url: string) {
  const response = await fetch(url);
  expect(response.ok).toBe(true); return response.json();
}

// The type mirrors the API only; editor internals remain inside the product adapter.
interface Summary { id: string; title: string }
interface AssetBlock { type: string; props?: { url?: string } }

async function readable(locator: Locator, minimum = 4.5, pseudo?: string) {
  // Measure actual computed foreground/background, including transparent ancestors.
  const ratio = await locator.evaluate((element, pseudo) => {
    const rgb = (value: string) => value.match(/[\d.]+/g)!.map(Number);
    const luminance = (values: number[]) => values.slice(0, 3).map((v) => {
      const s = v / 255; return s <= 0.04045 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
    }).reduce((sum, v, i) => sum + v * [0.2126, 0.7152, 0.0722][i], 0);
    let surface: Element | null = element;
    let background = [255, 255, 255];
    while (surface) {
      const value = rgb(getComputedStyle(surface).backgroundColor);
      if (value.length === 3 || value[3] === 1) { background = value; break; }
      surface = surface.parentElement;
    }
    const style = getComputedStyle(element, pseudo);
    const foreground = rgb(style.color);
    const alpha = (foreground[3] ?? 1) * Number(style.opacity);
    const effective = foreground.slice(0, 3).map((v, i) => v * alpha + background[i] * (1 - alpha));
    const levels = [luminance(effective), luminance(background)].sort((a, b) => a - b);
    return (levels[1] + 0.05) / (levels[0] + 0.05);
  }, pseudo);
  expect(ratio, `Text contrast for ${await locator.getAttribute('class')}`).toBeGreaterThanOrEqual(minimum);
}

test('appearance follows system and explicit preferences without changing notes, templates or autosave', async ({ page }, info) => {
  const env = await environment();
  const external: string[] = []; const errors: string[] = []; const writes: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  page.on('request', (request) => { if (request.method() === 'PATCH' && request.url().includes('/api/notes/')) writes.push(request.url()); });
  await page.route('**/*', (route) => {
    if (new URL(route.request().url()).hostname !== '127.0.0.1') { external.push(route.request().url()); return route.abort(); }
    return route.continue();
  });
  // Stall the React entrypoint to verify the blocking bootstrap independently.
  let release!: () => void;
  const gate = new Promise<void>((done) => { release = done; });
  const entrypoint = /\/(?:assets\/index-[^/]+\.js|src\/main\.tsx)(?:\?.*)?$/;
  await page.route(entrypoint, async (route) => { await gate; await route.continue(); });
  const editor = () => page.getByRole('region', { name: 'Note editor' }).getByRole('textbox');
  const appearance = () => page.getByRole('combobox', { name: 'Appearance', exact: true });
  async function themed(value: 'light' | 'dark') {
    await expect(page.locator('html')).toHaveAttribute('data-mantine-color-scheme', value);
    await expect(page.getByRole('region', { name: 'Note editor' }).locator('.bn-container')).toHaveAttribute('data-color-scheme', value);
    await expect(page.getByRole('region', { name: 'Note editor' }).locator('.bn-mantine').first()).toHaveAttribute('data-mantine-color-scheme', value);
  }
  async function atEnd() {
    await editor().evaluate((element) => {
      (element as HTMLElement).focus(); const range = document.createRange();
      range.selectNodeContents(element); range.collapse(false);
      const selection = window.getSelection()!; selection.removeAllRanges(); selection.addRange(range);
    });
  }
  try {
    await env.start(); await page.emulateMedia({ colorScheme: 'light' });
    await page.addInitScript(() => { if (!localStorage.getItem('engage.appearance.v1')) localStorage.setItem('engage.appearance.v1', 'dark'); });
    await page.goto(env.url, { waitUntil: 'commit' });
    await expect(page.locator('html')).toHaveAttribute('data-mantine-color-scheme', 'dark');
    // Release CSS is a render-blocking head link. Vite injects development CSS
    // through the module graph that this test deliberately stalls.
    if (releaseMode) await expect.poll(() => page.locator('html').evaluate((element) => getComputedStyle(element).backgroundColor)).toBe('rgb(24, 33, 47)');
    await expect(page.locator('#root')).toBeEmpty(); release(); await page.unroute(entrypoint);
    await expect(appearance()).toHaveValue('dark');
    await expect(page).toHaveTitle('CyrNava');
    await expect(page.getByRole('heading', { name: 'CyrNava', exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'New note', exact: true }).click();
    const createDialog = page.getByRole('dialog');
    await createDialog.getByLabel('Note title', { exact: true }).fill('Appearance training');
    await createDialog.getByLabel('Starting content', { exact: true }).selectOption('builtin:enumeration');
    await createDialog.getByRole('button', { name: 'Create', exact: true }).click(); await saved(page);
    await atEnd(); await page.keyboard.press('Control+b'); await page.keyboard.type('Theme-safe bold');
    await page.keyboard.press('Control+b'); await page.keyboard.press('Enter'); await page.keyboard.type('Native document content.'); await saved(page);
    const owner = (await getJson(`${env.api}/api/tree`)).notes[0];
    const persisted = () => getJson(`${env.api}/api/notes/${owner.id}`);
    const seeded = await persisted();
    seeded.document_json.find((block: AssetBlock) => block.type === 'codeBlock').content = [{ type: 'text', text: 'printf "documentation only"', styles: {} }];
    seeded.document_json.push({ type: 'paragraph', content: [{ type: 'link', href: 'https://example.invalid/reference', content: [{ type: 'text', text: 'Local reference', styles: {} }] }], children: [] });
    seeded.document_json.push({ type: 'bulletListItem', content: [{ type: 'text', text: 'Preserved list item', styles: { italic: true } }], children: [] });
    seeded.document_json.push({ type: 'paragraph', content: [], children: [] });
    expect((await fetch(`${env.api}/api/notes/${owner.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ revision: seeded.revision, document_json: seeded.document_json }) })).status).toBe(200);
    await page.reload(); await saved(page);
    const before = await persisted(); const changes = writes.length;
    const instance = await editor().elementHandle();

    for (const mode of ['light', 'dark'] as const) {
      await appearance().selectOption(mode); await themed(mode);
      await page.emulateMedia({ colorScheme: mode === 'light' ? 'dark' : 'light' }); await themed(mode);
      expect(await instance!.evaluate((node) => node.isConnected)).toBe(true);
      await expect(editor().locator('strong')).toContainText('Theme-safe bold');
      await readable(page.locator('.editor-help')); await readable(page.locator('.save-state'));
      await readable(page.getByRole('textbox', { name: 'Note title', exact: true }));
      await readable(page.getByRole('treeitem', { name: 'Note Appearance training', exact: true }));
      await readable(editor().getByRole('link', { name: 'Local reference', exact: true }));
      await readable(editor().locator('[data-content-type="codeBlock"]'));
      await page.getByRole('button', { name: 'Hide navigation', exact: true }).click();
      await expect(appearance()).toBeVisible();
      await page.screenshot({ path: info.outputPath(`appearance-${mode}-collapsed.png`), fullPage: true });
      await page.getByRole('button', { name: 'Show navigation', exact: true }).click();
    }
    await appearance().selectOption('auto');
    await editor().focus();
    for (const colorScheme of ['dark', 'light'] as const) {
      await page.emulateMedia({ colorScheme }); await themed(colorScheme);
      await expect(editor()).toBeFocused();
    }
    expect(await persisted()).toEqual(before); expect(writes).toHaveLength(changes);
    await page.emulateMedia({ colorScheme: 'dark' }); await themed('dark');
    await page.getByRole('button', { name: 'Hide navigation', exact: true }).click();
    await page.reload(); await saved(page); await themed('dark');
    await expect(appearance()).toHaveValue('auto'); await expect(page.getByRole('complementary')).toBeHidden();
    await page.getByRole('button', { name: 'Show navigation', exact: true }).focus();
    await page.keyboard.press('Enter'); await expect(page.getByRole('complementary')).toBeVisible();
    await appearance().focus(); await page.keyboard.press('Tab'); await page.keyboard.press('Shift+Tab');
    await expect(appearance()).toBeFocused();
    expect(await appearance().evaluate((element) => getComputedStyle(element).outlineStyle)).toBe('solid');

    for (const mode of ['light', 'dark'] as const) {
      await appearance().selectOption(mode); await themed(mode);
      await editor().getByText('Theme-safe bold', { exact: true }).dblclick();
      const toolbar = page.locator('.bn-formatting-toolbar'); await expect(toolbar).toBeVisible();
      await readable(toolbar);
      await toolbar.getByRole('button', { name: 'Colors', exact: true }).click();
      await expect(page.getByText('Text', { exact: true }).last()).toBeVisible();
      await expect(page.locator('.bn-color-picker-dropdown')).toHaveCSS('opacity', '1');
      await readable(page.getByText('Text', { exact: true }).last());
      await readable(page.locator('.bn-color-picker-dropdown').getByRole('menuitem').first());
      await page.screenshot({ path: info.outputPath(`appearance-${mode}-formatting.png`), fullPage: true });
      await page.keyboard.press('Escape'); await atEnd();
      await page.keyboard.press('Enter'); await page.keyboard.type('/');
      const menu = page.locator('.bn-suggestion-menu'); await expect(menu).toBeVisible();
      await expect.poll(() => menu.evaluate((element) => {
        let node: Element | null = element;
        while (node) { if (getComputedStyle(node).opacity !== '1') return false; node = node.parentElement; }
        return true;
      })).toBe(true);
      await readable(menu); await readable(menu.locator('.bn-suggestion-menu-label').first());
      await readable(menu.locator('.bn-mt-suggestion-menu-item-subtitle').first());
      await expect(menu.locator('xpath=ancestor::*[@data-mantine-color-scheme][1]')).toHaveAttribute('data-mantine-color-scheme', mode);
      await page.screenshot({ path: info.outputPath(`appearance-${mode}-slash-menu.png`), fullPage: true });
      await page.keyboard.press('Escape'); await page.keyboard.press('Backspace'); await saved(page);
      const placeholder = editor().locator('[data-content-type="paragraph"]').last();
      await expect.poll(() => placeholder.evaluate((element) => getComputedStyle(element, '::after').content)).toContain('Enter text');
      await readable(placeholder, 4.5, '::after');
      await page.getByRole('button', { name: 'New note', exact: true }).click();
      const dialog = page.getByRole('dialog'); await readable(dialog); await readable(dialog.getByLabel('Starting content', { exact: true }));
      await expect(dialog.getByRole('option', { name: 'Enumeration Notes', exact: true })).toHaveCount(1);
      await page.screenshot({ path: info.outputPath(`appearance-${mode}-template-selection.png`), fullPage: true });
      await dialog.getByRole('button', { name: 'Cancel', exact: true }).click();
      await page.getByRole('button', { name: 'Manage templates', exact: true }).click();
      await page.getByRole('dialog').getByLabel('Available templates', { exact: true }).selectOption('builtin:enumeration');
      await page.screenshot({ path: info.outputPath(`appearance-${mode}-template-manager.png`), fullPage: true });
      await page.getByRole('dialog').getByRole('button', { name: 'Close templates', exact: true }).click();
    }
    await page.getByRole('button', { name: 'Save as template', exact: true }).click();
    await readable(page.getByRole('dialog'));
    await page.getByRole('dialog').getByLabel('Template name', { exact: true }).fill('Appearance-neutral template');
    await page.getByRole('dialog').getByRole('button', { name: 'Save template', exact: true }).click();
    await expect(page.getByRole('dialog')).toBeHidden();
    const template = (await getJson(`${env.api}/api/templates`)).find((row: { name: string }) => row.name === 'Appearance-neutral template');
    const canonical = (await persisted()).document_json;
    const withoutIds = (blocks: unknown) => JSON.parse(JSON.stringify(blocks, (key, value) => key === 'id' ? undefined : value));
    for (const mode of ['light', 'dark'] as const) {
      await appearance().selectOption(mode);
      const response = await fetch(`${env.api}/api/templates/${template.id}/notes`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: `Copy in ${mode}`, revision: 1 }) });
      expect(response.status).toBe(201); expect(withoutIds((await response.json()).document_json)).toEqual(withoutIds(canonical));
    }
    await env.stopBackend();
    await page.getByRole('textbox', { name: 'Note title', exact: true }).fill('Theme preserves pending edits');
    await expect(page.getByText('Save Error', { exact: true })).toBeVisible();
    for (const mode of ['light', 'dark'] as const) {
      await appearance().selectOption(mode); await themed(mode);
      await readable(page.locator('.save-state')); await readable(page.getByRole('alert').last());
      await page.screenshot({ path: info.outputPath(`appearance-${mode}-save-error.png`), fullPage: true });
    }
    await env.startBackend(); await page.getByRole('button', { name: 'Retry save', exact: true }).click(); await saved(page);
    expect((await persisted()).document_json).toEqual(canonical);
    await page.reload(); await saved(page); await themed('dark'); await expect(appearance()).toHaveValue('dark');
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole('button', { name: 'Hide navigation', exact: true }).click(); await expect(appearance()).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await page.screenshot({ path: info.outputPath('appearance-dark-mobile.png'), fullPage: true });
    expect(external).toEqual([]); expect(errors).toEqual([]);
  } finally { release(); await env.shutdown(); await writeFile(info.outputPath('local-server.log'), env.logs()); await rm(env.directory, { recursive: true, force: true }); }
});

test('CyrNava reference appearance preserves the live editor, local images and saved content', async ({ page }, info) => {
  const env = await environment();
  const external: string[] = [];
  await page.route('**/*', (route) => {
    if (new URL(route.request().url()).hostname !== '127.0.0.1') { external.push(route.request().url()); return route.abort(); }
    return route.continue();
  });
  async function post(path: string, body: unknown) {
    const response = await fetch(env.api + path, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
    expect(response.status).toBe(201); return response.json();
  }
  try {
    await env.start(); await page.emulateMedia({ colorScheme: 'light' });
    await post('/api/folders', { name: 'Defensive Security' });
    const engagement = await post('/api/folders', { name: 'Engagements' });
    const folder = await post('/api/folders', { name: 'Brains', parent_id: engagement.id });
    await post('/api/folders', { name: "Fool’s Mate", parent_id: engagement.id });
    await post('/api/folders', { name: 'FlareVM' });
    await post('/api/folders', { name: 'Offensive Security' });
    const note = await post('/api/notes', { title: 'Brains', folder_id: folder.id, document_json: [
      { type: 'heading', props: { level: 1 }, content: [{ type: 'text', text: 'Discovery', styles: {} }] },
      { type: 'paragraph', content: [{ type: 'text', text: "A synthetic local lab note: discover which services are running on the host, document the observations, and keep the supporting screenshot alongside the written explanation.", styles: {} }] },
    ] });
    const png = join(env.directory, 'visual-fixture.png');
    execFileSync(python, ['-c', 'from PIL import Image,ImageDraw;import sys;im=Image.new("RGB",(600,340),"#f6f7f9");d=ImageDraw.Draw(im);d.rectangle((0,0,599,32),fill="#20324a");d.text((16,9),"Synthetic local evidence — example.test",fill="white");d.text((190,150),"Local service documentation",fill="#18212f",font_size=18);im.save(sys.argv[1])', png]);
    const uploaded = await fetch(`${env.api}/api/assets?note_id=${note.id}`, { method: 'POST', headers: { 'content-type': 'image/png' }, body: await readFile(png) });
    expect(uploaded.status).toBe(201); const asset = await uploaded.json();
    const content = [...note.document_json, { type: 'image', props: { url: asset.url, previewWidth: 600 }, children: [] }, { type: 'paragraph', content: [] }];
    const update = await fetch(`${env.api}/api/notes/${note.id}`, { method: 'PATCH', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ revision: note.revision, document_json: content }) });
    expect(update.ok).toBe(true);
    const before = await getJson(`${env.api}/api/notes/${note.id}`);
    await page.setViewportSize({ width: 1618, height: 889 });
    await page.goto(env.url); await saved(page);
    const editor = page.getByRole('textbox', { name: 'Note content', exact: true });
    const instance = await editor.elementHandle();
    const appearance = page.getByRole('combobox', { name: 'Appearance', exact: true });
    await appearance.selectOption('cyrnava');
    await expect(page.locator('html')).toHaveAttribute('data-cyrnava-theme', 'true');
    await expect(page.locator('.bn-container')).toHaveAttribute('data-color-scheme', 'dark');
    await expect.poll(() => editor.locator('img').evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth === 600)).toBe(true);
    await readable(editor.locator('p').first()); await readable(page.locator('.editor-help'));
    await readable(page.locator('.save-state')); await readable(page.locator('#note-title'));
    await readable(page.getByRole('treeitem', { name: 'Note Brains', exact: true }));
    for (const button of await page.getByRole('button').all()) {
      if (await button.isVisible() && await button.isEnabled()) await readable(button);
    }
    expect(await editor.locator('img').evaluate((image) => getComputedStyle(image).filter)).toBe('none');
    await page.screenshot({ path: info.outputPath('cyrnava-reference-viewport.png'), fullPage: false, animations: 'disabled' });
    await page.setViewportSize({ width: 1680, height: 936 });
    await page.screenshot({ path: info.outputPath('cyrnava-1680x936.png'), fullPage: false });
    for (const mode of ['light', 'dark', 'auto', 'cyrnava']) {
      await appearance.selectOption(mode);
      expect(await instance!.evaluate((node) => node.isConnected)).toBe(true);
    }
    expect(await getJson(`${env.api}/api/notes/${note.id}`)).toEqual(before);
    await page.reload(); await saved(page); await expect(appearance).toHaveValue('cyrnava');
    await expect(page.locator('.bn-container')).toHaveAttribute('data-color-scheme', 'dark');
    await page.getByRole('button', { name: 'Manage templates', exact: true }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.screenshot({ path: info.outputPath('cyrnava-dialog.png') });
    await page.keyboard.press('Escape');
    await editor.locator('[data-content-type="paragraph"]').last().evaluate((element) => {
      element.closest<HTMLElement>('[contenteditable="true"]')!.focus(); const range = document.createRange(); range.selectNodeContents(element); range.collapse(false);
      const selection = window.getSelection()!; selection.removeAllRanges(); selection.addRange(range);
    });
    await page.keyboard.type('/heading');
    const menu = page.locator('.bn-suggestion-menu');
    await expect(menu).toBeVisible();
    await expect(menu).toHaveCSS('background-color', 'rgb(16, 18, 27)');
    await readable(menu.getByText('Heading 1', { exact: true }));
    await page.screenshot({ path: info.outputPath('cyrnava-slash-menu.png'), animations: 'disabled' });
    await page.keyboard.press('Escape');
    await editor.locator('[data-content-type="paragraph"]').last().evaluate((element) => {
      const range = document.createRange(); range.selectNodeContents(element);
      const selection = window.getSelection()!; selection.removeAllRanges(); selection.addRange(range);
    });
    await page.keyboard.type('Persisted under the CyrNava theme.'); await saved(page);
    await env.stopBackend(); await env.startBackend(); await page.reload(); await saved(page);
    await expect(editor).toContainText('Persisted under the CyrNava theme.');
    await expect(editor.locator('img')).toBeVisible();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole('button', { name: 'Hide navigation', exact: true }).click();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(391);
    await expect(editor.getByRole('heading', { level: 1 })).toHaveCSS('font-size', '36px');
    await page.screenshot({ path: info.outputPath('cyrnava-mobile.png'), fullPage: true });
    expect(external).toEqual([]);
  } finally { await env.shutdown(); await writeFile(info.outputPath('local-server.log'), env.logs()); await rm(env.directory, { recursive: true, force: true }); }
});

test('navigation preference and reusable templates preserve independent rich notes and screenshots', async ({ page }, info) => {
  const env = await environment();
  const external: string[] = [];
  await page.route('**/*', (route) => {
    if (new URL(route.request().url()).hostname !== '127.0.0.1') { external.push(route.request().url()); return route.abort(); }
    return route.continue();
  });
  const editor = () => page.getByRole('region', { name: 'Note editor' }).getByRole('textbox');
  async function fromTemplate(title: string, template: string) {
    await page.getByRole('button', { name: 'New note', exact: true }).click();
    const dialog = page.getByRole('dialog');
    await dialog.getByRole('textbox', { name: 'Note title', exact: true }).fill(title);
    await dialog.getByLabel('Starting content', { exact: true }).selectOption(template);
    await dialog.getByRole('button', { name: 'Create', exact: true }).click();
    await expect(dialog).toBeHidden(); await saved(page);
  }
  async function atEnd() {
    // Establish a real DOM caret; subsequent edits use actual keyboard input.
    await editor().evaluate((element) => {
      (element as HTMLElement).focus();
      const range = document.createRange(); range.selectNodeContents(element); range.collapse(false);
      const selection = window.getSelection()!; selection.removeAllRanges(); selection.addRange(range);
    });
  }
  try {
    await env.start(); await page.goto(env.url); await create(page, 'note', 'Blank still works');
    await expect(editor().getByRole('heading')).toHaveCount(0);
    const instance = await editor().elementHandle();
    const expanded = (await page.getByRole('main').boundingBox())!.width;
    await editor().click(); await page.keyboard.type('Unsaved navigation draft');
    await page.getByRole('button', { name: 'Hide navigation', exact: true }).focus();
    await page.keyboard.press('Enter');
    await expect(page.getByRole('complementary')).toBeHidden();
    await expect(page.getByRole('button', { name: 'Show navigation', exact: true })).toHaveAttribute('aria-expanded', 'false');
    expect((await page.getByRole('main').boundingBox())!.width).toBeGreaterThan(expanded);
    expect(await instance!.evaluate((node) => node.isConnected)).toBe(true);
    await expect(editor()).toContainText('Unsaved navigation draft');
    await saved(page); await page.reload(); await saved(page);
    await expect(page.getByRole('complementary')).toBeHidden();
    await expect(editor()).toContainText('Unsaved navigation draft');
    await page.getByRole('button', { name: 'Show navigation', exact: true }).click();
    await create(page, 'folder', 'Template training');
    await fromTemplate('Enumeration source', 'builtin:enumeration');
    for (const section of ['Target Information', 'Commands Executed', 'Screenshots / Evidence', 'Next Steps']) {
      await expect(editor().getByRole('heading', { name: section, exact: true })).toBeVisible();
    }
    await atEnd(); await page.keyboard.type('Synthetic local technical documentation.');
    await page.keyboard.press('Enter'); await page.keyboard.press('Control+b');
    await page.keyboard.type('Bold evidence'); await page.keyboard.press('Control+b');
    await page.keyboard.press('Enter'); await page.keyboard.type('/image');
    await page.locator('.bn-suggestion-menu').getByText('Image', { exact: true }).click();
    const png = join(env.directory, 'template-screenshot.png');
    execFileSync(python, ['-c', "from PIL import Image; import sys; Image.new('RGB',(320,120),'#20324a').save(sys.argv[1])", png]);
    const chooser = page.waitForEvent('filechooser');
    await page.getByRole('button', { name: 'Upload image', exact: true }).click(); await (await chooser).setFiles(png);
    await expect.poll(() => editor().locator('img').evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth === 320)).toBe(true);
    await saved(page);
    const tree = await getJson(`${env.api}/api/tree`);
    const source = tree.notes.find((row: Summary) => row.title === 'Enumeration source');
    const before = await getJson(`${env.api}/api/notes/${source.id}`);
    expect(JSON.stringify(before.document_json)).toContain('"bold":true');
    await env.stopBackend(); await env.startBackend(); await page.reload(); await saved(page);
    await expect(editor().locator('strong')).toContainText('Bold evidence');
    await expect.poll(() => editor().locator('img').evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth === 320)).toBe(true);
    expect(await getJson(`${env.api}/api/notes/${source.id}`)).toEqual(before);
    await page.getByRole('button', { name: 'Save as template', exact: true }).click();
    await page.getByRole('dialog').getByLabel('Template name', { exact: true }).fill('Reusable enumeration');
    await page.getByRole('dialog').getByRole('button', { name: 'Save template', exact: true }).click();
    await expect(page.getByRole('dialog')).toBeHidden();
    const template = (await getJson(`${env.api}/api/templates`)).find((row: { name: string }) => row.name === 'Reusable enumeration');
    await fromTemplate('Independent copy', template.id);
    await expect(editor().locator('strong')).toContainText('Bold evidence');
    await expect.poll(() => editor().locator('img').evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth === 320)).toBe(true);
    const copied = (await getJson(`${env.api}/api/tree`)).notes.find((row: Summary) => row.title === 'Independent copy');
    const copy = await getJson(`${env.api}/api/notes/${copied.id}`);
    expect(copy.folder_id).toBe(before.folder_id);
    expect(copy.document_json[0].id).not.toBe(before.document_json[0].id);
    expect(copy.document_json.find((block: AssetBlock) => block.type === 'image').props.url)
      .not.toBe(before.document_json.find((block: AssetBlock) => block.type === 'image').props.url);
    await page.getByRole('textbox', { name: 'Note title', exact: true }).fill('Independently edited copy'); await saved(page);
    expect(await getJson(`${env.api}/api/notes/${source.id}`)).toEqual(before);
    await fromTemplate('Second independent copy', template.id);
    await expect(editor()).not.toContainText('Unsaved navigation draft');
    await expect(editor()).toContainText('Synthetic local technical documentation.');
    await page.getByRole('treeitem', { name: 'Note Enumeration source', exact: true }).click(); await saved(page);
    await page.getByRole('textbox', { name: 'Note title', exact: true }).fill('Independently edited source'); await saved(page);
    expect((await getJson(`${env.api}/api/notes/${copied.id}`)).title).toBe('Independently edited copy');
    await page.getByRole('button', { name: 'Manage templates', exact: true }).click();
    const manager = page.getByRole('dialog');
    await manager.getByLabel('Available templates', { exact: true }).selectOption('builtin:enumeration');
    await expect(manager.getByRole('button', { name: 'Delete template', exact: true })).toHaveCount(0);
    await manager.getByLabel('Available templates', { exact: true }).selectOption(template.id);
    await manager.getByLabel('Template name', { exact: true }).fill('Renamed enumeration');
    await manager.getByRole('button', { name: 'Rename template', exact: true }).click();
    await expect(manager.getByRole('option', { name: 'Renamed enumeration', exact: true })).toHaveCount(1);
    await manager.getByRole('button', { name: 'Delete template', exact: true }).click();
    await manager.getByRole('button', { name: 'Delete template permanently', exact: true }).click();
    await expect(manager.getByRole('option', { name: 'Renamed enumeration', exact: true })).toHaveCount(0);
    await manager.getByRole('button', { name: 'Close templates', exact: true }).click();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole('button', { name: 'Hide navigation', exact: true }).click();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
    await expect(editor()).toContainText('Bold evidence');
    await page.screenshot({ path: info.outputPath('templates-mobile-collapsed.png'), fullPage: true });
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.screenshot({ path: info.outputPath('templates-desktop-collapsed.png'), fullPage: true });
    await page.getByRole('button', { name: 'Show navigation', exact: true }).click();
    await page.screenshot({ path: info.outputPath('templates-desktop-expanded.png'), fullPage: true });
    expect(external).toEqual([]);
  } finally {
    await env.shutdown(); await writeFile(info.outputPath('local-server.log'), env.logs());
    await rm(env.directory, { recursive: true, force: true });
  }
});

test('real editing, outage recovery, safe navigation, image lifecycle and offline restoration drill', async ({ page }, info) => {
  const env = await environment();
  const external: string[] = [];
  await page.route('**/*', (route) => {
    const address = new URL(route.request().url());
    if (address.hostname !== '127.0.0.1') { external.push(address.origin); return route.abort(); }
    return route.continue();
  });
  try {
    await env.start(); await page.goto(env.url);
    await create(page, 'folder', 'M5 Training'); await create(page, 'folder', 'Nested');
    await create(page, 'note', 'Evidence');
    const editor = () => page.getByRole('region', { name: 'Note editor' }).getByRole('textbox');
    await editor().click(); await editor().pressSequentially('# '); await editor().pressSequentially('Recovery evidence');
    await editor().press('Enter'); await editor().pressSequentially('Formatted note before outage.');
    await editor().press('Enter'); await editor().press('Control+b'); await editor().pressSequentially('Bold evidence'); await editor().press('Control+b');
    await editor().press('Enter'); await editor().pressSequentially('/image'); await editor().press('Enter');
    const png = join(env.directory, 'screenshot.png');
    execFileSync(python, ['-c', "from PIL import Image,ImageDraw; import sys; im=Image.new('RGB',(600,140),'#20324a'); ImageDraw.Draw(im).text((25,45),'CyrNava - LOCAL RECOVERY TEST',fill='white',font_size=23); im.save(sys.argv[1])", png]);
    const chooser = page.waitForEvent('filechooser');
    await page.getByRole('button', { name: 'Upload image', exact: true }).click();
    await (await chooser).setFiles(png);
    await expect(page.getByRole('region', { name: 'Note editor' }).locator('img')).toHaveCount(1);
    await expect.poll(() => page.getByRole('region', { name: 'Note editor' }).locator('img').evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth > 0)).toBe(true);
    await saved(page); await page.reload(); await saved(page);
    await expect(editor()).toContainText('Bold evidence');
    await expect(editor().getByRole('heading', { name: 'Recovery evidence', exact: true })).toBeVisible();
    const tree = await getJson(`${env.api}/api/tree`);
    const owner = tree.notes.find((note: Summary) => note.title === 'Evidence');
    await create(page, 'note', 'Companion');
    await page.getByRole('treeitem', { name: 'Note Evidence', exact: true }).click();
    await expect(page.getByRole('textbox', { name: 'Note title', exact: true })).toHaveValue('Evidence');

    await env.stopBackend();
    await editor().locator('p').last().click(); await page.keyboard.press('End'); await page.keyboard.type(' Draft retained during backend outage.');
    await expect(page.getByText('Save Error', { exact: true })).toBeVisible();
    await expect(editor()).toContainText('Draft retained during backend outage.');
    await page.getByRole('treeitem', { name: 'Note Companion', exact: true }).click();
    await expect(page.getByRole('alert').filter({ hasText: 'Cannot leave this note' })).toBeVisible();
    await expect(page.getByRole('textbox', { name: 'Note title', exact: true })).toHaveValue('Evidence');
    await env.startBackend(); await page.getByRole('button', { name: 'Retry save', exact: true }).click();
    await saved(page); await page.reload(); await saved(page);
    await expect(editor()).toContainText('Draft retained during backend outage.');

    // Hold a confirmed old response while newer text is entered.
    let release!: () => void; const gate = new Promise<void>((resolve) => { release = resolve; });
    let received!: () => void; const firstResponse = new Promise<void>((resolve) => { received = resolve; });
    let first = true;
    await page.route('**/api/notes/*', async (route) => {
      if (first && route.request().method() === 'PATCH') {
        first = false; const response = await route.fetch(); received(); await gate; await route.fulfill({ response });
      } else await route.continue();
    });
    await editor().locator('p').last().click(); await page.keyboard.press('End'); await page.keyboard.type(' Paragraph A.'); await firstResponse;
    await page.keyboard.type(' Paragraph B.');
    await expect(page.getByText('Unsaved Changes', { exact: true })).toBeVisible(); release();
    await saved(page);
    expect(JSON.stringify((await getJson(`${env.api}/api/notes/${owner.id}`)).document_json)).toContain('Paragraph B.');
    await page.unroute('**/api/notes/*');

    await page.getByRole('treeitem', { name: 'Folder Nested', exact: true }).click();
    await page.getByRole('button', { name: 'Rename', exact: true }).click();
    await page.getByRole('dialog').getByRole('textbox', { name: 'Name', exact: true }).fill('Verified folder');
    await page.getByRole('dialog').getByRole('button', { name: 'Apply', exact: true }).click();
    await expect(page.getByRole('dialog')).toBeHidden();
    await page.getByRole('button', { name: 'Delete', exact: true }).click();
    await expect(page.getByRole('dialog')).toContainText('2 notes');
    await page.getByRole('dialog').getByRole('button', { name: 'Cancel', exact: true }).click();
    await expect(page.getByRole('treeitem', { name: 'Folder Verified folder', exact: true })).toBeVisible();

    const note = await getJson(`${env.api}/api/notes/${owner.id}`);
    const image = note.document_json.find((block: AssetBlock) => block.type === 'image');
    const assetId = image.props.url.split('/').pop();
    const assetPath = join(env.profile(), 'assets', assetId);
    await rename(assetPath, `${assetPath}.missing-test`); await page.reload();
    await expect(page.getByRole('alert')).toContainText('saved image is unavailable');
    await expect(editor()).toContainText('Paragraph B.');
    await rename(`${assetPath}.missing-test`, assetPath); await page.reload(); await saved(page);

    const beforeTree = await getJson(`${env.api}/api/tree`);
    const beforeNote = await getJson(`${env.api}/api/notes/${owner.id}`);
    const beforeBytes = await readFile(assetPath);
    await env.shutdown();
    const originalDb = await readFile(join(env.profile(), 'engage.sqlite3'));
    expect(env.cli(['backup', '--data-dir', env.profile(), '--destination', join(env.directory, 'backup')])).toContain('completed and validated');
    const restoredData = join(env.directory, 'restored-data'); await mkdir(restoredData);
    expect(env.cli(['restore', '--source', join(env.directory, 'backup'), '--data-dir', join(restoredData, 'engage')])).toContain('completed and validated');
    env.restoreTo(restoredData); await env.start(); await page.reload(); await saved(page);
    expect(await getJson(`${env.api}/api/tree`)).toEqual(beforeTree);
    expect(await getJson(`${env.api}/api/notes/${owner.id}`)).toEqual(beforeNote);
    expect(await readFile(join(env.profile(), 'assets', assetId))).toEqual(beforeBytes);
    await expect(editor().getByRole('heading', { name: 'Recovery evidence', exact: true })).toBeVisible();
    await expect(editor()).toContainText('Paragraph B.');
    await expect.poll(() => editor().locator('img').evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth === 600)).toBe(true);
    await page.screenshot({ path: info.outputPath('restored-workspace.png'), fullPage: true });
    expect(await readFile(join(env.directory, 'original-data/engage/engage.sqlite3'))).toEqual(originalDb);
    expect(external).toEqual([]);
    await writeFile(info.outputPath('restoration-evidence.json'), JSON.stringify({ restored_tree: beforeTree, restored_note: beforeNote, image_bytes: beforeBytes.length, external_requests: external }, null, 2));
  } finally {
    await env.shutdown();
    await writeFile(info.outputPath('local-server.log'), env.logs());
    await rm(env.directory, { recursive: true, force: true });
  }
});

test('revision conflict retains the draft and exports both versions before explicit reload', async ({ page }, info) => {
  const env = await environment();
  try {
    await env.start(); await page.goto(env.url); await create(page, 'note', 'Conflict note');
    const tree = await getJson(`${env.api}/api/tree`); const owner = tree.notes[0];
    const persisted = await getJson(`${env.api}/api/notes/${owner.id}`);
    const response = await fetch(`${env.api}/api/notes/${owner.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ revision: persisted.revision, title: 'Other saved version' }) });
    expect(response.status).toBe(200);
    await page.getByRole('textbox', { name: 'Note title', exact: true }).fill('My unsaved title');
    await expect(page.getByText('Save Error', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Review conflict and recover', exact: true }).click();
    const dialog = page.getByRole('dialog'); await expect(dialog).toContainText('Other saved version');
    await expect(dialog.getByRole('button', { name: 'Reopen saved version', exact: true })).toBeDisabled();
    const download = page.waitForEvent('download'); await dialog.getByRole('button', { name: 'Download both versions', exact: true }).click();
    const file = await download; const destination = info.outputPath('conflict-recovery.json'); await file.saveAs(destination);
    const bundle = JSON.parse(await readFile(destination, 'utf8'));
    expect(bundle.local_draft.title).toBe('My unsaved title'); expect(bundle.saved_note.title).toBe('Other saved version');
    await dialog.getByRole('checkbox').check(); await dialog.getByRole('button', { name: 'Reopen saved version', exact: true }).click();
    await expect(page.getByRole('textbox', { name: 'Note title', exact: true })).toHaveValue('Other saved version');
    await page.getByRole('textbox', { name: 'Note title', exact: true }).fill('Editing after recovery'); await saved(page);
    expect((await getJson(`${env.api}/api/notes/${owner.id}`)).title).toBe('Editing after recovery');
  } finally { await env.shutdown(); await writeFile(info.outputPath('local-server.log'), env.logs()); await rm(env.directory, { recursive: true, force: true }); }
});

test('Phase 1 formatting, clipboard, CRUD, keyboard access and sanitized documentation', async ({ page }, info) => {
  const env = await environment();
  const external: string[] = [];
  const selectionStates: unknown[] = [];
  const captureSelection = async (stage: string, extension: string) => { selectionStates.push({ stage, extension, ...await editorSelection(editor()) }); };
  await page.route('**/*', (route) => {
    if (new URL(route.request().url()).hostname !== '127.0.0.1') { external.push(route.request().url()); return route.abort(); }
    return route.continue();
  });
  const editor = () => page.getByRole('region', { name: 'Note editor' }).getByRole('textbox');
  try {
    await env.start(); await page.goto(env.url);
    await create(page, 'folder', 'Networking'); await create(page, 'folder', 'Protocols');
    await create(page, 'note', 'DNS reference');
    await editor().click();
    for (const [prefix, text] of [['# ', 'Network documentation'], ['## ', 'DNS resolution'], ['### ', 'Resolver behavior']]) {
      await page.keyboard.type(prefix); await page.keyboard.type(text); await page.keyboard.press('Enter');
    }
    await page.keyboard.type('A resolver translates a synthetic example.test name into a local documentation example.'); await page.keyboard.press('Enter');
    await page.keyboard.type('- '); await page.keyboard.type('Ask the configured resolver.'); await page.keyboard.press('Enter');
    await page.keyboard.type('Review the cached response.'); await page.keyboard.press('Enter'); await page.keyboard.press('Enter');
    await page.keyboard.press('Control+b'); await page.keyboard.type('Synthetic learning notes only.'); await page.keyboard.press('Control+b'); await page.keyboard.press('Enter');
    await page.keyboard.type('``` '); await page.keyboard.type('dig example.test'); await page.keyboard.press('Enter'); await page.keyboard.type('# Example syntax; CyrNava does not execute commands.');
    await saved(page);
    let tree = await getJson(`${env.api}/api/tree`);
    const owner = tree.notes.find((note: Summary) => note.title === 'DNS reference');
    const protocols = tree.folders.find((folder: { name: string }) => folder.name === 'Protocols');
    const networking = tree.folders.find((folder: { name: string }) => folder.name === 'Networking');
    const rich = await getJson(`${env.api}/api/notes/${owner.id}`);
    expect(rich.document_json.filter((b: { type: string }) => b.type === 'heading').map((b: { props: { level: number } }) => b.props.level)).toEqual([1, 2, 3]);
    expect(rich.document_json.some((b: { type: string }) => b.type === 'codeBlock')).toBe(true);
    expect(rich.document_json.some((b: { type: string }) => b.type === 'bulletListItem')).toBe(true);
    expect(JSON.stringify(rich.document_json)).toContain('"bold":true');
    await create(page, 'note', 'TCP overview');
    await editor().click(); await page.keyboard.type('TCP provides ordered, reliable byte streams between endpoints.'); await saved(page);
    await page.getByRole('treeitem', { name: 'Note DNS reference', exact: true }).click(); await saved(page);
    await expect(editor().getByRole('heading', { name: 'Network documentation', exact: true })).toBeVisible();
    await page.screenshot({ path: info.outputPath('01-workspace.png'), fullPage: true });
    await page.getByRole('complementary').screenshot({ path: info.outputPath('02-hierarchy.png') });
    await page.getByRole('main').screenshot({ path: info.outputPath('03-rich-text.png') });

    const png = join(env.directory, 'synthetic.png');
    execFileSync(python, ['-c', "from PIL import Image,ImageDraw; import sys; im=Image.new('RGB',(600,140),'#20324a'); ImageDraw.Draw(im).text((20,45),'SYNTHETIC DNS DIAGRAM - example.test',fill='white',font_size=23); [im.save(sys.argv[1]+ext,format=fmt) for ext,fmt in [('.png','PNG'),('.jpg','JPEG'),('.webp','WEBP')]]", png]);
    await page.context().grantPermissions(['clipboard-read', 'clipboard-write'], { origin: env.url });
    await page.evaluate(async (data) => {
      const bytes = Uint8Array.from(atob(data), (character) => character.charCodeAt(0));
      await navigator.clipboard.write([new ClipboardItem({ 'image/png': new Blob([bytes], { type: 'image/png' }) })]);
    }, (await readFile(`${png}.png`)).toString('base64'));
    await editor().getByText('Synthetic learning notes only.', { exact: true }).click(); await page.keyboard.press('End'); await page.keyboard.press('Control+v');
    await expect(editor().locator('img')).toHaveCount(1); await saved(page);
    // A DOM click/End can precede the editor's selectionchange transaction.
    // Establish each command's actual paragraph cursor, including after upload.
    for (const [index, extension] of ['jpg', 'webp'].entries()) {
      await captureSelection('before-paragraph-click', extension);
      const paragraph = editor().getByText('Synthetic learning notes only.', { exact: true });
      const blockId = await paragraph.evaluate((node) => node.closest('[data-id]')!.getAttribute('data-id')!);
      await paragraph.click();
      await captureSelection('after-click-before-synchronization', extension);
      await paragraphCursor(editor(), { blockId });
      await page.keyboard.press('End');
      await paragraphCursor(editor(), { blockId });
      await expect.poll(async () => { const state = await editorSelection(editor()); return state.model.parentOffset === state.model.contentSize; }).toBe(true);
      await page.keyboard.press('Enter');
      await paragraphCursor(editor(), { empty: true });
      await captureSelection('ready-for-image-command', extension);
      await page.keyboard.type('/image');
      await paragraphCursor(editor());
      const imageCommand = page.locator('.bn-suggestion-menu').getByRole('option').filter({ has: page.getByText('Image', { exact: true }) });
      await expect(imageCommand).toBeVisible();
      await expect(imageCommand).toHaveAttribute('aria-selected', 'true');
      await page.keyboard.press('Enter');
      const upload = page.getByRole('button', { name: 'Upload image', exact: true });
      await expect(upload).toBeVisible();
      const [chooser] = await Promise.all([page.waitForEvent('filechooser', { timeout: 10_000 }), upload.click({ timeout: 10_000 })]);
      await chooser.setFiles(`${png}.${extension}`);
      await expect(editor().locator('img')).toHaveCount(index + 2);
      await expect.poll(() => editor().locator('img').evaluateAll((images) => images.every((image) => (image as HTMLImageElement).complete && (image as HTMLImageElement).naturalWidth === 600))).toBe(true);
      await expect(upload).toBeHidden();
      await saved(page);
      await expect.poll(async () => {
        const note = await getJson(`${env.api}/api/notes/${owner.id}`);
        return note.document_json.filter((block: AssetBlock) => block.type === 'image' && block.props?.url).length;
      }).toBe(index + 2);
      await captureSelection('upload-rendered-and-persisted', extension);
    }
    await expect(editor().locator('img')).toHaveCount(3);
    const imageNote = await getJson(`${env.api}/api/notes/${owner.id}`);
    expect(imageNote.document_json.filter((b: { type: string }) => b.type === 'image')).toHaveLength(3);
    const originalBlocks = (blocks: { type: string; content?: unknown[] }[]) => blocks.filter((block) => block.type !== 'image' && !(block.type === 'paragraph' && !block.content?.length));
    expect(originalBlocks(imageNote.document_json)).toEqual(originalBlocks(rich.document_json));
    await env.stopBackend(); await env.startBackend(); await page.reload(); await saved(page);
    expect((await getJson(`${env.api}/api/notes/${owner.id}`)).document_json).toEqual(imageNote.document_json);
    await expect.poll(() => editor().locator('img').evaluateAll((images) => images.every((image) => (image as HTMLImageElement).complete && (image as HTMLImageElement).naturalWidth === 600))).toBe(true);
    await editor().locator('img').first().scrollIntoViewIfNeeded();
    await page.screenshot({ path: info.outputPath('04-images.png'), fullPage: true });

    // Move note to root and back; its native content is unchanged.
    for (const destination of ['', protocols.id]) {
      await page.getByRole('button', { name: 'Move', exact: true }).click();
      await page.getByRole('dialog').getByLabel('Destination folder').selectOption(destination);
      await page.getByRole('dialog').getByRole('button', { name: 'Apply', exact: true }).click();
      await expect(page.getByRole('dialog')).toBeHidden();
    }
    expect((await getJson(`${env.api}/api/notes/${owner.id}`)).document_json).toEqual(imageNote.document_json);
    // Folder movement is the same existing dialog, verified with descendants.
    await page.getByRole('treeitem', { name: 'Folder Protocols', exact: true }).click();
    for (const destination of ['', networking.id]) {
      await page.getByRole('button', { name: 'Move', exact: true }).click();
      await page.getByRole('dialog').getByLabel('Destination folder').selectOption(destination);
      await page.getByRole('dialog').getByRole('button', { name: 'Apply', exact: true }).click(); await expect(page.getByRole('dialog')).toBeHidden();
    }
    const folder = page.getByRole('treeitem', { name: 'Folder Protocols', exact: true });
    await folder.focus(); await page.keyboard.press('F2'); await expect(page.getByRole('dialog')).toBeVisible();
    await page.keyboard.press('Escape'); await expect(page.getByRole('dialog')).toBeHidden(); await expect(folder).toBeFocused();
    await page.keyboard.press('ArrowLeft'); await expect(folder).toHaveAttribute('aria-expanded', 'false');
    await page.keyboard.press('ArrowRight'); await page.keyboard.press('ArrowRight');
    const noteRow = page.getByRole('treeitem', { name: 'Note DNS reference', exact: true }); await expect(noteRow).toBeFocused();
    await page.keyboard.press('Enter'); await expect(page.getByRole('textbox', { name: 'Note title', exact: true })).toHaveValue('DNS reference');
    await noteRow.focus(); await page.keyboard.press('Delete'); await expect(page.getByRole('dialog')).toContainText('cannot be undone');
    await page.keyboard.press('Escape'); await expect(page.getByRole('dialog')).toBeHidden(); await expect(noteRow).toBeFocused();
    await editor().locator('p').first().click(); await page.keyboard.press('ArrowLeft'); await page.keyboard.press('ArrowRight');
    await expect(editor()).toBeFocused(); await expect(page.getByRole('dialog')).toBeHidden();
    for (const button of await page.getByRole('button').all()) if (await button.isVisible()) await expect(button).toHaveAccessibleName(/\S/);
    await page.keyboard.press('Tab'); // Native focus remains keyboard operable.
    await page.setViewportSize({ width: 390, height: 844 });
    await page.getByRole('textbox', { name: 'Note title', exact: true }).click();
    // Resizing retains the old hover target until the pointer moves. Measure
    // the mobile workspace after the closing hover menu has unmounted. A
    // visibility-hidden transition snapshot still contributes scroll width.
    await page.mouse.move(0, 0);
    await expect(page.locator('.bn-side-menu')).toHaveCount(0);
    const layout = await page.evaluate(() => ({ width: window.innerWidth, scroll: document.documentElement.scrollWidth, overflowing: Array.from(document.querySelectorAll('*')).filter((element) => element.getBoundingClientRect().right > window.innerWidth + 1).slice(0, 12).map((element) => ({ tag: element.tagName, class: element.className, right: element.getBoundingClientRect().right })) }));
    expect(layout.scroll, JSON.stringify(layout)).toBeLessThanOrEqual(layout.width + 1);
    await page.setViewportSize({ width: 1280, height: 1000 });

    await page.getByRole('button', { name: 'Workspace root', exact: true }).click();
    await create(page, 'folder', 'Disposable fixture'); await create(page, 'note', 'Disposable note');
    await page.getByRole('treeitem', { name: 'Folder Disposable fixture', exact: true }).click();
    await page.getByRole('button', { name: 'Delete', exact: true }).click();
    await expect(page.getByRole('dialog')).toContainText('1 note');
    await page.getByRole('button', { name: 'Delete permanently', exact: true }).click(); await expect(page.getByRole('dialog')).toBeHidden();
    tree = await getJson(`${env.api}/api/tree`); expect(tree.notes).toHaveLength(2); expect(tree.folders).toHaveLength(2);
    expect(external).toEqual([]);
  } finally {
    try { await writeFile(info.outputPath('image-selection-states.json'), JSON.stringify(selectionStates, null, 2)); }
    finally { await env.shutdown(); await writeFile(info.outputPath('local-server.log'), env.logs()); await rm(env.directory, { recursive: true, force: true }); }
  }
});


test('image command requires a synchronized paragraph after code-block focus', async ({ page }, info) => {
  const env = await environment();
  const editor = page.getByRole('region', { name: 'Note editor' }).getByRole('textbox');
  const states: unknown[] = [];
  try {
    await env.start(); await page.goto(env.url); await create(page, 'note', 'Synthetic image selection regression');
    await editor.click(); await page.keyboard.type('Image insertion anchor'); await page.keyboard.press('Enter');
    await page.keyboard.type('``` '); await page.keyboard.type('Synthetic code'); await page.keyboard.press('Enter');
    await expect.poll(async () => { const state = await editorSelection(editor); return state.synchronized && state.model.parent === 'codeBlock'; }).toBe(true);
    states.push({ stage: 'code-cursor', ...await editorSelection(editor) });
    await page.keyboard.type('/image');
    await expect(editor.locator('[data-content-type="codeBlock"]')).toContainText('/image');
    await expect(page.locator('.bn-suggestion-menu')).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Upload image', exact: true })).toHaveCount(0);
    states.push({ stage: 'literal-code-command', ...await editorSelection(editor) });

    const anchor = editor.getByText('Image insertion anchor', { exact: true });
    const blockId = await anchor.evaluate((node) => node.closest('[data-id]')!.getAttribute('data-id')!);
    await anchor.click();
    states.push({ stage: 'clicked-paragraph', ...await editorSelection(editor) });
    await paragraphCursor(editor, { blockId });
    await page.keyboard.press('End'); await paragraphCursor(editor, { blockId });
    await expect.poll(async () => { const state = await editorSelection(editor); return state.model.parentOffset === state.model.contentSize; }).toBe(true);
    await page.keyboard.press('Enter'); await paragraphCursor(editor, { empty: true });
    states.push({ stage: 'synchronized-empty-paragraph', ...await editorSelection(editor) });
    await page.keyboard.type('/image'); await paragraphCursor(editor);
    const imageCommand = page.locator('.bn-suggestion-menu').getByRole('option').filter({ has: page.getByText('Image', { exact: true }) });
    await expect(imageCommand).toBeVisible(); await expect(imageCommand).toHaveAttribute('aria-selected', 'true');
    await page.keyboard.press('Enter');
    const upload = page.getByRole('button', { name: 'Upload image', exact: true }); await expect(upload).toBeVisible();
    const png = join(env.directory, 'synthetic-selection.png');
    execFileSync(python, ['-c', "from PIL import Image; import sys; Image.new('RGB',(600,140),'#20324a').save(sys.argv[1])", png]);
    const [chooser] = await Promise.all([page.waitForEvent('filechooser'), upload.click()]);
    await chooser.setFiles(png);
    await expect.poll(() => editor.locator('img').evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth === 600)).toBe(true);
    await expect(upload).toBeHidden(); await saved(page);
    const tree = await getJson(`${env.api}/api/tree`);
    const note = await getJson(`${env.api}/api/notes/${tree.notes[0].id}`);
    expect(note.document_json.filter((block: AssetBlock) => block.type === 'image' && block.props?.url)).toHaveLength(1);
    expect(JSON.stringify(note.document_json.filter((block: AssetBlock) => block.type === 'codeBlock'))).toContain('/image');
    await expect(anchor).toHaveText('Image insertion anchor');
  } finally {
    try { await writeFile(info.outputPath('image-selection-states.json'), JSON.stringify(states, null, 2)); }
    finally { await env.shutdown(); await writeFile(info.outputPath('local-server.log'), env.logs()); await rm(env.directory, { recursive: true, force: true }); }
  }
});


test('all exposed editor actions persist; mixed content reconstructs after restart and rapid edits', async ({ page }) => {
  const env = await environment();
  const fixture = JSON.parse(await readFile(join(backend, 'tests/fixtures/blocknote_v1.json'), 'utf8'));
  const external: string[] = [];
  const rejected: number[] = [];
  let releaseHeld: (() => void) | undefined;
  await page.route('**/*', (route) => {
    if (new URL(route.request().url()).hostname !== '127.0.0.1') {
      external.push(route.request().url()); return route.abort();
    }
    return route.continue();
  });
  page.on('response', (response) => {
    if (response.request().method() === 'PATCH' && response.status() >= 400) rejected.push(response.status());
  });
  try {
    await env.start();
    const created = await fetch(env.api + '/api/notes', { method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ title: 'Compatibility', document_json: fixture.mixed }) });
    expect(created.status).toBe(201); const note = await created.json();
    const png = join(env.directory, 'compatibility.png');
    execFileSync(python, ['-c', 'from PIL import Image;import sys;Image.new("RGB",(32,20),"blue").save(sys.argv[1])', png]);
    const upload = await fetch(env.api + '/api/assets?note_id=' + note.id, { method: 'POST', headers: { 'content-type': 'image/png' }, body: await readFile(png) });
    expect(upload.status).toBe(201); const asset = await upload.json();
    fixture.mixed.find((block: AssetBlock) => block.type === 'image').props.url = asset.url;
    const initial = await fetch(env.api + '/api/notes/' + note.id, { method: 'PATCH', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ revision: 1, document_json: fixture.mixed }) });
    expect(initial.status).toBe(200);
    await page.goto(env.url); await saved(page);
    await page.getByRole('combobox', { name: 'Appearance', exact: true }).selectOption('cyrnava');
    const editor = page.getByRole('region', { name: 'Note editor' }).getByRole('textbox');
    for (let level = 1; level <= 6; level++) {
      await expect(editor.getByRole('heading', { name: 'Heading ' + level, exact: true })).toBeVisible();
    }
    for (const button of await editor.locator('.bn-toggle-button').all()) await button.click();
    await expect(editor.getByText('Nested toggle body 3', { exact: true })).toBeVisible();
    await expect(editor.getByText('Nested', { exact: true })).toBeVisible();
    await expect(editor.locator('[data-content-type="codeBlock"]')).toContainText('print("local 🚀")');
    await expect(editor.locator('strong')).toContainText('All styles');
    await expect(editor.locator('a[href="https://example.invalid/evidence"]')).toContainText('Reference');
    await expect.poll(() => editor.locator('img').evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth > 0)).toBe(true);
    const persisted = async () => (await getJson(env.api + '/api/notes/' + note.id)).document_json;
    expect(await persisted()).toEqual(fixture.mixed);

    // A block spans the editor width: clicking its center may miss its text
    // and leave the previous caret active. Use the browser's Selection API
    // solely for caret setup; all document edits still use real key events.
    async function newParagraph() {
      const anchor = editor.locator('[data-id="mixed-tail"] [data-content-type="paragraph"]');
      await anchor.scrollIntoViewIfNeeded();
      await anchor.evaluate((element) => {
        element.closest<HTMLElement>('[contenteditable="true"]')!.focus();
        const range = document.createRange();
        range.selectNodeContents(element); range.collapse(false);
        const selection = window.getSelection()!;
        selection.removeAllRanges(); selection.addRange(range);
      });
      const caret = () => page.evaluate(() => {
        const node = window.getSelection()?.anchorNode;
        const element = node instanceof Element ? node : node?.parentElement;
        const content = element?.closest('[data-content-type]');
        return { id: element?.closest('[data-id]')?.getAttribute('data-id'),
          type: content?.getAttribute('data-content-type'), text: content?.textContent };
      });
      await expect.poll(caret, { message: 'Caret is at the fixed paragraph' }).toMatchObject({ id: 'mixed-tail', type: 'paragraph', text: 'Final paragraph.' });
      await page.keyboard.press('Enter');
      await expect.poll(caret, { message: 'Enter creates an empty paragraph outside code' }).toMatchObject({ type: 'paragraph', text: '' });
      expect((await caret()).id).not.toBe('mixed-tail');
    }

    // Every current slash-menu command is activated through the real UI.
    for (const item of fixture.slash_menu as { key: string; title: string }[]) {
      await test.step('Slash command: ' + item.title, async () => {
        await newParagraph(); await page.keyboard.type('/' + item.title);
        await page.locator('.bn-suggestion-menu').getByText(item.title, { exact: true }).click({ timeout: 10_000 });
        if (item.key === 'image') {
          const chooser = page.waitForEvent('filechooser');
          await page.getByRole('button', { name: 'Upload image', exact: true }).click();
          await (await chooser).setFiles(png);
          await expect.poll(async () => (await persisted()).filter((b: AssetBlock) => b.type === 'image' && b.props?.url).length).toBe(2);
        } else if (item.key === 'emoji') {
          const emoji = page.locator('.bn-grid-suggestion-menu-item').first();
          await expect(emoji).toBeVisible(); const character = await emoji.innerText(); await emoji.click();
          await expect.poll(async () => JSON.stringify(await persisted()).includes(character.trim())).toBe(true);
        } else {
          const marker = 'Menu-' + item.key;
          await page.keyboard.type(marker);
          await expect.poll(async () => JSON.stringify(await persisted()).includes(marker)).toBe(true);
        }
        await saved(page);
      });
    }

    // Hold a successful old acknowledgement while newer formatting/text changes.
    let release!: () => void; const gate = new Promise<void>((done) => { release = done; releaseHeld = done; });
    let received = false; let first = true;
    await page.route('**/api/notes/*', async (route) => {
      if (first && route.request().method() === 'PATCH') {
        first = false; const response = await route.fetch(); received = true; await gate; await route.fulfill({ response });
      } else await route.continue();
    });
    await newParagraph();
    await page.keyboard.press('Control+Alt+4'); await page.keyboard.type('Rapid A');
    await expect.poll(() => received, { message: 'First rapid edit reaches the API' }).toBe(true);
    await page.keyboard.press('Control+Alt+6'); await page.keyboard.type(' + Rapid B 🚀');
    await expect(page.getByText('Unsaved Changes', { exact: true })).toBeVisible(); release();
    await expect.poll(async () => JSON.stringify(await persisted()).includes('Rapid A + Rapid B 🚀')).toBe(true);
    await saved(page); await page.unroute('**/api/notes/*');
    const final = await persisted();
    expect(final.find((block: { id: string }) => block.id === 'case-codeBlock')).toEqual(fixture.mixed.find((block: { id: string }) => block.id === 'case-codeBlock'));
    expect(final.find((block: { content?: unknown }) => (JSON.stringify(block.content) || '').includes('Rapid A')).props.level).toBe(6);
    await page.reload(); await saved(page); expect(await persisted()).toEqual(final);
    await expect(editor.getByRole('heading', { name: 'Rapid A + Rapid B 🚀', exact: true })).toBeVisible();
    await expect(editor.getByText('Nested toggle body 3', { exact: true })).toBeVisible();
    await env.stopBackend(); await env.startBackend(); await page.reload(); await saved(page);
    expect(await persisted()).toEqual(final);
    await expect(editor.locator('[data-id="case-codeBlock"] [data-content-type="codeBlock"]')).toContainText('print("local 🚀")');
    await expect(editor.getByRole('heading', { name: 'Rapid A + Rapid B 🚀', exact: true })).toBeVisible();
    expect(rejected).toEqual([]); expect(external).toEqual([]);
  } finally { releaseHeld?.(); await env.shutdown(); await rm(env.directory, { recursive: true, force: true }); }
});

test('desktop close protocol drains real autosave and retains an interrupted draft', async ({ page, context }) => {
  const env = await environment();
  try {
    await env.start(); await page.goto(env.url);
    await create(page, 'note', 'P2 close protocol');
    const content = page.getByRole('textbox', { name: 'Note content' });
    await content.click(); await page.keyboard.type('Paragraph saved by close handshake.');
    const request = 'a'.repeat(32);
    await page.evaluate((id) => window.__cyrnavaDesktop!.request(id), request);
    await expect.poll(() => page.evaluate((id) => window.__cyrnavaDesktop!.state(id), request)).toBe('saved');
    const tree = await getJson(env.api + '/api/tree');
    const note = await getJson(env.api + '/api/notes/' + tree.notes[0].id);
    expect(JSON.stringify(note.document_json)).toContain('Paragraph saved by close handshake.');
    await page.evaluate((id) => window.__cyrnavaDesktop!.cancel(id), request);
    await env.stopBackend();
    await page.getByRole('textbox', { name: 'Note title' }).fill('P2 unconfirmed recovery draft');
    const blocked = 'b'.repeat(32);
    await page.evaluate((id) => window.__cyrnavaDesktop!.request(id), blocked);
    await expect.poll(() => page.evaluate((id) => window.__cyrnavaDesktop!.state(id), blocked)).toBe('error');
    await page.evaluate((id) => window.__cyrnavaDesktop!.cancel(id), blocked);
    const exported = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download pending draft', exact: true }).click();
    const exportPath = await (await exported).path();
    expect(exportPath).not.toBeNull();
    expect(JSON.parse(await readFile(exportPath!, 'utf8')).title).toBe('P2 unconfirmed recovery draft');
    // Closing without an acknowledgement is explicitly the recovery path.
    // Context-level abort outlives the page and prevents a late close save.
    await context.route('**/api/notes/*', (route) => route.request().method() === 'PATCH' ? route.abort() : route.continue());
    await env.startBackend(); await page.reload();
    await expect(page.getByRole('heading', { name: 'Recover unsaved edits' })).toBeVisible();
    await context.unrouteAll({ behavior: 'wait' });
    await page.getByRole('button', { name: 'Recover draft', exact: true }).click();
    await saved(page); await page.reload();
    await expect(page.getByRole('textbox', { name: 'Note title' })).toHaveValue('P2 unconfirmed recovery draft');
  } finally { await env.shutdown(); await rm(env.directory, { recursive: true, force: true }); }
});

test('desktop close waits for an image upload and its subsequent document save', async ({ page, context }) => {
  const env = await environment();
  let release: (() => void) | undefined;
  try {
    await env.start(); await page.goto(env.url); await create(page, 'note', 'P2 pending image');
    const png = join(env.directory, 'synthetic-close.png');
    execFileSync(python, ['-c', 'from PIL import Image;import sys;Image.new("RGB",(8,8),"blue").save(sys.argv[1])', png]);
    let started = false;
    const held = new Promise<void>((done) => { release = done; });
    await page.route('**/api/assets?*', async (route) => { started = true; await held; await route.continue(); });
    await context.grantPermissions(['clipboard-read', 'clipboard-write'], { origin: env.url });
    await page.evaluate(async (data) => {
      const bytes = Uint8Array.from(atob(data), (value) => value.charCodeAt(0));
      await navigator.clipboard.write([new ClipboardItem({ 'image/png': new Blob([bytes], { type: 'image/png' }) })]);
    }, (await readFile(png)).toString('base64'));
    await page.getByRole('textbox', { name: 'Note content' }).click(); await page.keyboard.press('Control+v');
    await expect.poll(() => started).toBe(true);
    await expect(page.getByText('Saved', { exact: true })).toBeHidden();
    const id = 'c'.repeat(32);
    await page.evaluate((id) => window.__cyrnavaDesktop!.request(id), id);
    await expect.poll(() => page.evaluate((id) => window.__cyrnavaDesktop!.state(id), id)).toBe('waiting');
    // Closing must preserve the two-pane layout while the upload is held.
    await expect.poll(() => page.evaluate(() => {
      const sidebar = document.querySelector('.sidebar')!.getBoundingClientRect();
      const main = document.querySelector('main')!.getBoundingClientRect();
      return { sameRow: Math.abs(sidebar.y - main.y) < 1,
        adjacent: Math.abs(sidebar.right - main.x) < 1 };
    })).toEqual({ sameRow: true, adjacent: true });
    release!();
    await expect.poll(() => page.evaluate((id) => window.__cyrnavaDesktop!.state(id), id)).toBe('saved');
    const tree = await getJson(env.api + '/api/tree');
    const note = await getJson(env.api + '/api/notes/' + tree.notes[0].id);
    expect(note.document_json.find((block: AssetBlock) => block.type === 'image')?.props?.url).toMatch(/^\/api\/assets\/[0-9a-f-]{36}$/);
    await page.evaluate((id) => window.__cyrnavaDesktop!.cancel(id), id);
    await page.reload(); await expect(page.locator('.editor img')).toBeVisible();
    await expect.poll(() => page.locator('.editor img').evaluate((image) => (image as HTMLImageElement).naturalWidth)).toBeGreaterThan(0);
  } finally { release?.(); await env.shutdown(); await rm(env.directory, { recursive: true, force: true }); }
});

test('desktop close does not silently discard an unsubmitted management form', async ({ page }) => {
  const env = await environment();
  try {
    await env.start(); await page.goto(env.url);
    await page.getByRole('button', { name: 'New note', exact: true }).click();
    await page.getByRole('dialog').getByLabel('Note title').fill('Unsubmitted title');
    const id = 'd'.repeat(32);
    await page.evaluate((id) => window.__cyrnavaDesktop!.request(id), id);
    await expect.poll(() => page.evaluate((id) => window.__cyrnavaDesktop!.state(id), id)).toBe('error');
    await page.evaluate((id) => window.__cyrnavaDesktop!.cancel(id), id);
    await expect(page.getByRole('dialog').getByLabel('Note title')).toHaveValue('Unsubmitted title');
  } finally { await env.shutdown(); await rm(env.directory, { recursive: true, force: true }); }
});
