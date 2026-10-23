import { test, expect } from '@playwright/test';
import type { Page } from '@playwright/test';
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
const releaseMode = process.env.ENGAGE_E2E_RELEASE === '1';

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
  const directory = await mkdtemp(join(tmpdir(), 'engage-m5-e2e-'));
  const backendPort = await freePort(); const frontendPort = releaseMode ? backendPort : await freePort();
  const api = `http://127.0.0.1:${backendPort}`; const url = `http://127.0.0.1:${frontendPort}`;
  let server: ChildProcess | undefined; let vite: ChildProcess | undefined;
  let data = join(directory, 'original-data'); let logs = '';
  function launch(command: string, args: string[], cwd: string) {
    const child = spawn(command, args, { cwd, env: { ...process.env, XDG_DATA_HOME: data, ENGAGE_API_PORT: String(backendPort) }, stdio: ['ignore', 'pipe', 'pipe'] });
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
    execFileSync(python, ['-c', "from PIL import Image,ImageDraw; import sys; im=Image.new('RGB',(600,140),'#20324a'); ImageDraw.Draw(im).text((25,45),'ENGAGE M5 - LOCAL RECOVERY TEST',fill='white',font_size=23); im.save(sys.argv[1])", png]);
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
    await page.keyboard.type('``` '); await page.keyboard.type('dig example.test'); await page.keyboard.press('Enter'); await page.keyboard.type('# Example syntax; ENGAGE does not execute commands.');
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
    // Reuse the empty trailing paragraph for the installed native image selector.
    for (const extension of ['jpg', 'webp']) {
      await editor().getByText('Synthetic learning notes only.', { exact: true }).click(); await page.keyboard.press('End'); await page.keyboard.press('Enter');
      await page.keyboard.type('/image'); await page.keyboard.press('Enter');
      const [chooser] = await Promise.all([page.waitForEvent('filechooser', { timeout: 10_000 }), page.getByRole('button', { name: 'Upload image', exact: true }).click({ timeout: 10_000 })]);
      await chooser.setFiles(`${png}.${extension}`); await page.keyboard.press('Escape'); await saved(page);
    }
    await expect(editor().locator('img')).toHaveCount(3);
    const imageNote = await getJson(`${env.api}/api/notes/${owner.id}`);
    expect(imageNote.document_json.filter((b: { type: string }) => b.type === 'image')).toHaveLength(3);
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
  } finally { await env.shutdown(); await writeFile(info.outputPath('local-server.log'), env.logs()); await rm(env.directory, { recursive: true, force: true }); }
});
