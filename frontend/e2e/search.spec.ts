import { test, expect } from '@playwright/test';
import type { Page, Route } from '@playwright/test';
import { spawn, execFileSync } from 'node:child_process';
import type { ChildProcess } from 'node:child_process';
import { cp, mkdir, mkdtemp, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { dirname, join, resolve } from 'node:path';
import { createServer } from 'node:net';
import { fileURLToPath } from 'node:url';

const frontend = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const backend = resolve(frontend, '../backend');
const python = join(backend, '.venv/bin/python');

async function stop(child: ChildProcess | undefined) {
  if (!child?.pid || child.exitCode !== null || child.signalCode !== null) return;
  await new Promise<void>((done) => {
    child.once('exit', () => { clearTimeout(timer); done(); });
    const timer = setTimeout(() => child.kill('SIGKILL'), 5000);
    child.kill('SIGTERM');
  });
}
async function installation() {
  const directory = await mkdtemp(join(tmpdir(), 'cyrnava-search-browser-'));
  const release = join(directory, 'release');
  await mkdir(join(release, 'backend'), { recursive: true });
  await mkdir(join(release, 'frontend'));
  // Copies prevent __file__.resolve() from escaping this test's release snapshot.
  await cp(join(backend, 'app'), join(release, 'backend/app'), { recursive: true });
  await cp(join(frontend, 'dist'), join(release, 'frontend/dist'), { recursive: true });
  const probe = createServer();
  await new Promise<void>((done) => probe.listen(0, '127.0.0.1', done));
  const address = probe.address();
  if (!address || typeof address === 'string') throw new Error('Cannot allocate test port');
  const port = address.port;
  await new Promise<void>((done) => probe.close(() => done()));
  const url = `http://127.0.0.1:${port}`;
  const profile = join(directory, 'data', 'engage');
  const releaseBackend = join(release, 'backend');
  const environment = { ...process.env, XDG_DATA_HOME: join(directory, 'data') };
  let logs = ''; let child: ChildProcess | undefined;
  async function start() {
    child = spawn(python, ['-m', 'app', '--port', String(port)], {
      cwd: releaseBackend,
      env: environment,
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    child.stdout?.on('data', (chunk) => { logs += chunk.toString(); });
    child.stderr?.on('data', (chunk) => { logs += chunk.toString(); });
    child.on('error', (error) => { logs += error.message; });
    await expect.poll(async () => {
      if (child?.exitCode !== null || child?.signalCode !== null) throw new Error(`Test backend exited: ${logs}`);
      try { return (await fetch(`${url}/health`)).ok; } catch { return false; }
    }, { timeout: 15_000 }).toBe(true);
  }
  async function post(path: string, body: unknown) {
    const response = await fetch(url + path, {
      method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body),
    });
    expect(response.status).toBe(201); return response.json();
  }
  async function get(path: string) {
    const response = await fetch(url + path); expect(response.ok).toBe(true); return response.json();
  }
  async function stopBackend() { await stop(child); child = undefined; }
  function requireStopped() {
    if (child && child.exitCode === null && child.signalCode === null) throw new Error('Stop the synthetic backend before offline maintenance.');
  }
  function offlinePython(code: string) {
    requireStopped();
    return execFileSync(python, ['-c', code, profile], { cwd: releaseBackend, env: environment, encoding: 'utf8' });
  }
  function rebuild() {
    requireStopped();
    return execFileSync(python, ['-m', 'app.search_index', 'rebuild', '--data-dir', profile], { cwd: releaseBackend, env: environment, encoding: 'utf8' });
  }
  return { url, profile, start, stop: stopBackend, post, get, offlinePython, rebuild, logs: () => logs,
    cleanup: async () => { await stopBackend(); await rm(directory, { recursive: true, force: true }); } };
}
function paragraph(text: string) {
  return { type: 'paragraph', content: [{ type: 'text', text, styles: {} }], children: [] };
}
async function offlinePage(page: Page, preferred: string, external: string[]) {
  await page.addInitScript((id) => {
    if (!localStorage.getItem('engage.note-id.v1')) localStorage.setItem('engage.note-id.v1', id);
  }, preferred);
  await page.route('**/*', (route) => {
    if (new URL(route.request().url()).hostname !== '127.0.0.1') {
      external.push(route.request().url()); return route.abort();
    }
    return route.continue();
  });
}

function canonicalSnapshot(app: Awaited<ReturnType<typeof installation>>) {
  return JSON.parse(app.offlinePython(`
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

profile = Path(sys.argv[1])
database = profile / "engage.sqlite3"
connection = sqlite3.connect(f"{database.as_uri()}?mode=ro", uri=True)
tables = ("notes", "folders", "assets", "templates", "template_images")
def value(item):
    if isinstance(item, bytes):
        return {"blob_sha256": hashlib.sha256(item).hexdigest(), "length": len(item)}
    return item
canonical = {
    table: [[value(item) for item in row]
            for row in connection.execute("SELECT * FROM " + table + " ORDER BY 1,2")]
    for table in tables
}
print(json.dumps({
    "version": connection.execute("PRAGMA user_version").fetchone()[0],
    "canonical": canonical,
    "asset_hashes": {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted((profile / "assets").iterdir()) if path.is_file()
    },
}, ensure_ascii=False))
connection.close()
`));
}

test('global search opens native rich notes by code prefix, supports keyboard selection and reveals ancestors', async ({ page }, info) => {
  const app = await installation(); const external: string[] = []; const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  try {
    await app.start();
    const source = await app.post('/api/notes', { title: 'Starting scratchpad', document_json: [paragraph('A separate root note.')] });
    const engagement = await app.post('/api/folders', { name: 'Synthetic engagement' });
    const evidence = await app.post('/api/folders', { name: 'Evidence', parent_id: engagement.id });
    const target = await app.post('/api/notes', {
      title: 'Compass finding', folder_id: evidence.id,
      document_json: [
        { type: 'heading', props: { level: 1 }, content: [{ type: 'text', text: 'Local discovery evidence', styles: {} }], children: [] },
        { type: 'paragraph', content: [{ type: 'text', text: 'Preserved emphasis', styles: { bold: true } }], children: [] },
        { type: 'codeBlock', props: { language: 'text' }, content: [{ type: 'text', text: 'enumerate_services --local', styles: {} }], children: [] },
      ],
    });
    await app.post('/api/notes', { title: 'Compass triage', document_json: [paragraph('A second keyboard result.')] });
    const original = await app.get(`/api/notes/${target.id}`);
    await offlinePage(page, source.id, external); await page.goto(app.url);
    const title = page.getByRole('textbox', { name: 'Note title', exact: true });
    await expect(title).toHaveValue(source.title);
    await expect(page.getByRole('treeitem', { name: 'Folder Synthetic engagement', exact: true })).toHaveAttribute('aria-expanded', 'false');
    const search = page.getByRole('region', { name: 'Global note search' });
    const query = search.getByRole('combobox', { name: 'Search all notes', exact: true });
    const options = search.getByRole('option');
    await query.fill('compass'); await expect(options).toHaveCount(2);
    await query.press('ArrowDown'); await expect(options.nth(0)).toHaveAttribute('aria-selected', 'true');
    await query.press('ArrowDown'); await expect(options.nth(1)).toHaveAttribute('aria-selected', 'true');
    await query.press('ArrowUp'); await expect(options.nth(0)).toHaveAttribute('aria-selected', 'true');
    await query.press('Escape'); await expect(query).toHaveValue(''); await expect(options).toHaveCount(0);
    // This prefix occurs only in a native code block, not the title/heading/body.
    await query.fill('enumerat'); await expect(options).toHaveCount(1);
    await expect(search.getByRole('option', { name: 'Open note: Compass finding', exact: true })).toBeVisible();
    await expect(search).toContainText('Synthetic engagement'); await expect(search).toContainText('Evidence');
    await query.press('ArrowDown'); await query.press('Enter'); await expect(title).toHaveValue(target.title);
    const editor = page.getByRole('region', { name: 'Note editor' }).getByRole('textbox');
    await expect(editor.getByRole('heading', { name: 'Local discovery evidence', exact: true })).toBeVisible();
    await expect(editor.locator('strong')).toContainText('Preserved emphasis');
    await expect(editor.locator('[data-content-type="codeBlock"]')).toContainText('enumerate_services --local');
    await expect(page.getByRole('treeitem', { name: 'Folder Synthetic engagement', exact: true })).toHaveAttribute('aria-expanded', 'true');
    await expect(page.getByRole('treeitem', { name: 'Folder Evidence', exact: true })).toHaveAttribute('aria-expanded', 'true');
    await expect(page.getByRole('treeitem', { name: 'Note Compass finding', exact: true })).toHaveAttribute('aria-current', 'true');
    await expect(query).toHaveValue('enumerat'); expect(await app.get(`/api/notes/${target.id}`)).toEqual(original);
    // Opening refreshes metadata/search. Capture the final result card rather
    // than its intentional debounce state.
    await expect(options).toHaveCount(1);
    await page.screenshot({ path: info.outputPath('search-workspace.png'), fullPage: true });
    await page.getByRole('combobox', { name: 'Appearance', exact: true }).selectOption('cyrnava');
    await expect(options.first()).toHaveCSS('display', 'block');
    await page.screenshot({ path: info.outputPath('search-cyrnava.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    await page.screenshot({ path: info.outputPath('search-mobile.png'), fullPage: true });
    await search.getByRole('button', { name: 'Clear search', exact: true }).click();
    await expect(query).toHaveValue(''); await expect(options).toHaveCount(0);
    await page.reload(); await expect(title).toHaveValue(target.title);
    await expect(editor.locator('strong')).toContainText('Preserved emphasis');
    expect(external).toEqual([]); expect(errors).toEqual([]);
    expect(app.logs()).not.toContain('/api/search');
  } finally { await writeFile(info.outputPath('local-search-server.log'), app.logs()); await app.cleanup(); }
});

test('opening a search result waits for pending saves and a failed save keeps the draft open', async ({ page }, info) => {
  const app = await installation(); const external: string[] = []; const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message)); let release = () => {};
  try {
    await app.start();
    const source = await app.post('/api/notes', { title: 'Current field draft', document_json: [paragraph('Original paragraph.')] });
    const target = await app.post('/api/notes', { title: 'Pivot reference', document_json: [paragraph('Saved target content.')] });
    await offlinePage(page, source.id, external); await page.goto(app.url);
    const title = page.getByRole('textbox', { name: 'Note title', exact: true });
    const editor = page.getByRole('region', { name: 'Note editor' }).getByRole('textbox');
    await expect(title).toHaveValue(source.title);
    const search = page.getByRole('region', { name: 'Global note search' });
    const query = search.getByRole('combobox', { name: 'Search all notes', exact: true });
    const result = search.getByRole('option', { name: 'Open note: Pivot reference', exact: true });
    await query.fill('pivot'); await expect(result).toBeVisible();
    let reached!: () => void; const started = new Promise<void>((done) => { reached = done; });
    const gate = new Promise<void>((done) => { release = done; });
    const holdSave = async (route: Route) => {
      if (route.request().method() !== 'PATCH') return route.continue();
      reached(); const response = await route.fetch(); await gate; await route.fulfill({ response });
    };
    await page.route(`**/api/notes/${source.id}`, holdSave);
    let targetReads = 0;
    page.on('request', (request) => { if (request.method() === 'GET' && request.url() === `${app.url}/api/notes/${target.id}`) targetReads++; });
    await editor.click(); await page.keyboard.press('Control+End'); await page.keyboard.type(' Pending pivot paragraph saved before navigation.');
    await expect(page.getByText('Unsaved Changes', { exact: true })).toBeVisible();
    await result.click(); await started; await expect(page.getByText('Saving...', { exact: true })).toBeVisible();
    await expect(title).toHaveValue(source.title); expect(targetReads).toBe(0);
    release(); await expect(title).toHaveValue(target.title); await expect(editor).toContainText('Saved target content.');
    expect(targetReads).toBe(1);
    await expect(search.getByRole('option', { name: 'Open note: Current field draft', exact: true })).toBeVisible();
    const afterFlush = await app.get(`/api/notes/${source.id}`);
    expect(JSON.stringify(afterFlush.document_json)).toContain('Pending pivot paragraph saved before navigation.');
    await page.unroute(`**/api/notes/${source.id}`, holdSave);
    await page.getByRole('treeitem', { name: 'Note Current field draft', exact: true }).click();
    await expect(title).toHaveValue(source.title);
    const failedSave = (route: Route) => route.request().method() === 'PATCH'
      ? route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Synthetic local save failure' }) }) : route.continue();
    await page.route(`**/api/notes/${source.id}`, failedSave);
    await editor.click(); await page.keyboard.press('Control+End'); await page.keyboard.type(' Recoveryneedle remains in this draft.');
    await expect(page.getByText('Save Error', { exact: true })).toBeVisible(); await result.click();
    await expect(page.getByText(/Cannot leave this note until pending edits/)).toBeVisible();
    await expect(title).toHaveValue(source.title); await expect(editor).toContainText('Recoveryneedle remains in this draft.');
    expect(targetReads).toBe(1); expect(await app.get(`/api/notes/${source.id}`)).toEqual(afterFlush);
    await page.unroute(`**/api/notes/${source.id}`, failedSave);
    await page.getByRole('button', { name: 'Retry save', exact: true }).click(); await expect(page.getByText('Saved', { exact: true })).toBeVisible();
    await query.fill('recoveryn'); await expect(search.getByRole('option', { name: 'Open note: Current field draft', exact: true })).toBeVisible();
    await query.fill('pivot'); await expect(result).toBeVisible(); await result.click(); await expect(title).toHaveValue(target.title);
    expect(JSON.stringify((await app.get(`/api/notes/${source.id}`)).document_json)).toContain('Recoveryneedle remains in this draft.');
    // Keep the query unchanged while an ordinary autosave makes another note match.
    await query.fill('recoveryn');
    await expect(search.getByRole('option', { name: 'Open note: Current field draft', exact: true })).toBeVisible();
    await editor.click(); await page.keyboard.press('Control+End');
    await page.keyboard.type(' Recoveryneedle newly indexed in the target.');
    await expect(page.getByText('Saved', { exact: true })).toBeVisible();
    await expect(search.getByRole('option', { name: 'Open note: Pivot reference', exact: true })).toBeVisible();
    await expect(query).toHaveValue('recoveryn');
    expect(external).toEqual([]); expect(errors).toEqual([]);
    expect(app.logs()).not.toContain('/api/search');
  } finally { release(); await writeFile(info.outputPath('local-search-server.log'), app.logs()); await app.cleanup(); }
});

test('an unchanged search reflects UI renames, folder moves and deletion, and retries a failed query', async ({ page }, info) => {
  const app = await installation(); const external: string[] = []; const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  try {
    await app.start();
    const source = await app.post('/api/notes', { title: 'Unrelated scratchpad', document_json: [paragraph('Separate source.')] });
    const parent = await app.post('/api/folders', { name: 'Original parent' });
    const child = await app.post('/api/folders', { name: 'Original evidence', parent_id: parent.id });
    const destination = await app.post('/api/folders', { name: 'Relocated parent' });
    const target = await app.post('/api/notes', { title: 'M4refresh original', folder_id: child.id, document_json: [paragraph('Saved evidence, preserved during library changes.')] });
    await offlinePage(page, source.id, external); await page.goto(app.url);
    const title = page.getByRole('textbox', { name: 'Note title', exact: true });
    await expect(title).toHaveValue(source.title);
    const search = page.getByRole('region', { name: 'Global note search' });
    const query = search.getByRole('combobox', { name: 'Search all notes', exact: true });
    const sidebar = page.getByRole('complementary', { name: 'Workspace navigation' });
    const searchRoute = /\/api\/search\?/; let rejectSearch = true;
    const failOnce = (route: Route) => {
      if (!rejectSearch) return route.continue();
      rejectSearch = false;
      return route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ detail: 'Synthetic temporary search failure.' }) });
    };
    await page.route(searchRoute, failOnce); await query.fill('m4refresh');
    await expect(search.getByRole('alert')).toContainText('Synthetic temporary search failure.');
    await expect(query).toHaveValue('m4refresh'); await expect(title).toHaveValue(source.title);
    await search.getByRole('button', { name: 'Retry search', exact: true }).click();
    const original = search.getByRole('option', { name: 'Open note: M4refresh original', exact: true });
    await expect(original).toBeVisible(); await page.unroute(searchRoute, failOnce);
    await original.click(); await expect(title).toHaveValue(target.title);
    await title.fill('M4refresh renamed'); await expect(page.getByText('Saved', { exact: true })).toBeVisible();
    const renamed = search.getByRole('option', { name: 'Open note: M4refresh renamed', exact: true });
    await expect(renamed).toBeVisible(); await expect(original).toHaveCount(0); await expect(query).toHaveValue('m4refresh');
    const current = await app.get(`/api/notes/${target.id}`);
    const rejected = await fetch(`${app.url}/api/notes/${target.id}`, {
      method: 'PATCH', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ revision: current.revision - 1, title: 'Nevercommittedneedle' }),
    });
    expect(rejected.status).toBe(409);
    expect((await app.get('/api/search?q=Nevercommittedneedle&limit=20')).total).toBe(0);
    expect(await app.get(`/api/notes/${target.id}`)).toEqual(current);
    await page.getByRole('treeitem', { name: 'Folder Original evidence', exact: true }).click();
    await sidebar.getByRole('button', { name: 'Rename', exact: true }).click();
    let dialog = page.getByRole('dialog');
    await dialog.getByRole('textbox', { name: 'Name', exact: true }).fill('Renamed evidence');
    await dialog.getByRole('button', { name: 'Apply', exact: true }).click(); await expect(dialog).toBeHidden();
    await expect(renamed).toContainText('Original parent / Renamed evidence'); await expect(query).toHaveValue('m4refresh');
    await page.getByRole('treeitem', { name: 'Folder Renamed evidence', exact: true }).click();
    await sidebar.getByRole('button', { name: 'Move', exact: true }).click(); dialog = page.getByRole('dialog');
    await dialog.getByRole('combobox', { name: 'Destination folder', exact: true }).selectOption(destination.id);
    await dialog.getByRole('button', { name: 'Apply', exact: true }).click(); await expect(dialog).toBeHidden();
    await expect(renamed).toContainText('Relocated parent / Renamed evidence'); await expect(renamed).not.toContainText('Original parent');
    await expect(query).toHaveValue('m4refresh');
    expect((await app.get(`/api/notes/${target.id}`)).document_json).toEqual(current.document_json);
    await renamed.click();
    await expect(page.getByRole('treeitem', { name: 'Note M4refresh renamed', exact: true })).toHaveAttribute('aria-selected', 'true');
    await sidebar.getByRole('button', { name: 'Delete', exact: true }).click(); dialog = page.getByRole('dialog');
    await dialog.getByRole('button', { name: 'Delete permanently', exact: true }).click(); await expect(dialog).toBeHidden();
    await expect(search.getByText('No matching notes.', { exact: true })).toBeVisible(); await expect(search.getByRole('option')).toHaveCount(0);
    await expect(query).toHaveValue('m4refresh');
    expect((await app.get('/api/search?q=m4refresh&limit=20')).total).toBe(0);
    expect((await fetch(`${app.url}/api/notes/${target.id}`)).status).toBe(404);
    expect(external).toEqual([]); expect(errors).toEqual([]);
    expect(app.logs()).not.toContain('/api/search'); expect(app.logs()).not.toContain('m4refresh');
  } finally { await writeFile(info.outputPath('local-search-server.log'), app.logs()); await app.cleanup(); }
});

test('a schema4 profile migrates, opens rich search results and rebuilds offline without changing canonical data', async ({ page }, info) => {
  const app = await installation(); const external: string[] = []; const errors: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  try {
    await app.start();
    const parent = await app.post('/api/folders', { name: 'Legacy engagement' });
    const child = await app.post('/api/folders', { name: 'Legacy evidence', parent_id: parent.id });
    const source = await app.post('/api/notes', { title: 'Legacy rich evidence', folder_id: child.id, document_json: [paragraph('Initial source.')] });
    const png = execFileSync(python, ['-c', 'import sys; from PIL import Image; Image.new("RGB", (20, 12), "blue").save(sys.stdout.buffer, format="PNG")']);
    const uploaded = await fetch(`${app.url}/api/assets?note_id=${source.id}`, { method: 'POST', headers: { 'content-type': 'image/png' }, body: png });
    expect(uploaded.status).toBe(201); const asset = await uploaded.json();
    const document = [
      { type: 'heading', props: { level: 1 }, content: [{ type: 'text', text: 'Legacy discovery heading', styles: {} }], children: [] },
      { type: 'paragraph', content: [{ type: 'text', text: 'Migrated bold proof.', styles: { bold: true } }], children: [] },
      { type: 'codeBlock', props: { language: 'text' }, content: [{ type: 'text', text: 'legacyprobe --offline 127.0.0.1', styles: {} }], children: [] },
      { type: 'bulletListItem', content: [{ type: 'text', text: 'Nested parent', styles: {} }], children: [paragraph('Nested legacyprobe evidence.')] },
      { type: 'image', props: { url: asset.url, caption: 'Synthetic legacy evidence', previewWidth: 250 }, children: [] },
    ];
    const changed = await fetch(`${app.url}/api/notes/${source.id}`, { method: 'PATCH', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ revision: source.revision, document_json: document }) });
    expect(changed.status).toBe(200); const rich = await changed.json();
    const template = await app.post('/api/templates', { name: 'Synthetic migrated template', source_note_id: rich.id, source_revision: rich.revision });
    const copy = await app.post(`/api/templates/${template.id}/notes`, { revision: template.revision, title: 'Legacy independent copy', folder_id: parent.id });
    const root = await app.post('/api/notes', { title: 'Legacy root reference', document_json: [paragraph('legacyprobe root body.')] });
    const originalCopy = await app.get(`/api/notes/${copy.id}`); await app.stop();
    // Genuine schema-4 table layout, with deliberately indented raw JSON bytes.
    app.offlinePython(`
import json
import sqlite3
import sys
from pathlib import Path
with sqlite3.connect(Path(sys.argv[1]) / "engage.sqlite3") as connection:
    for name in ("note_search_insert", "note_search_update", "note_search_delete"):
        connection.execute("DROP TRIGGER IF EXISTS " + name)
    connection.execute("DROP TABLE note_search")
    connection.execute("DROP TABLE note_search_documents")
    for table in ("notes", "templates"):
        rows = connection.execute("SELECT id,document_json FROM " + table).fetchall()
        for identifier, raw in rows:
            connection.execute("UPDATE " + table + " SET document_json=? WHERE id=?",
                (json.dumps(json.loads(raw), ensure_ascii=False, indent=3), identifier))
    connection.execute("PRAGMA user_version=4")
`);
    const before = canonicalSnapshot(app); expect(before.version).toBe(4);
    expect(before.canonical.notes).toHaveLength(3); expect(before.canonical.templates).toHaveLength(1);
    expect(before.canonical.template_images).toHaveLength(1); expect(Object.keys(before.asset_hashes)).toHaveLength(2);
    await app.start(); await offlinePage(page, root.id, external); await page.goto(app.url);
    const title = page.getByRole('textbox', { name: 'Note title', exact: true });
    const search = page.getByRole('region', { name: 'Global note search' });
    const query = search.getByRole('combobox', { name: 'Search all notes', exact: true });
    const editor = page.getByRole('region', { name: 'Note editor' }).getByRole('textbox');
    await expect(title).toHaveValue(root.title); await query.fill('legacyprob'); await expect(search.getByRole('option')).toHaveCount(3);
    await search.getByRole('option', { name: 'Open note: Legacy rich evidence', exact: true }).click(); await expect(title).toHaveValue(rich.title);
    await expect(editor.getByRole('heading', { name: 'Legacy discovery heading', exact: true })).toBeVisible();
    await expect(editor.locator('strong')).toContainText('Migrated bold proof.');
    await expect(editor.locator('[data-content-type="codeBlock"]')).toContainText('legacyprobe --offline 127.0.0.1');
    await expect(editor).toContainText('Nested legacyprobe evidence.');
    const image = editor.locator('img[src^="/api/assets/"]').first(); await expect(image).toBeVisible();
    await expect.poll(() => image.evaluate((element) => { const image = element as HTMLImageElement; return image.complete && image.naturalWidth > 0; })).toBe(true);
    expect(await app.get(`/api/notes/${rich.id}`)).toEqual(rich); expect(await app.get(`/api/notes/${copy.id}`)).toEqual(originalCopy);
    await app.stop(); const migrated = canonicalSnapshot(app); expect(migrated.version).toBe(5);
    expect(migrated.canonical).toEqual(before.canonical); expect(migrated.asset_hashes).toEqual(before.asset_hashes);
    await app.start(); await page.reload(); await expect(title).toHaveValue(rich.title); await query.fill('legacyprob');
    await expect(search.getByRole('option')).toHaveCount(3); await app.stop(); expect(canonicalSnapshot(app)).toEqual(migrated);
    app.offlinePython(`
import sqlite3
import sys
from pathlib import Path
with sqlite3.connect(Path(sys.argv[1]) / "engage.sqlite3") as connection:
    connection.execute("INSERT INTO note_search(note_search) VALUES('delete-all')")
`);
    await app.start(); await page.reload(); await expect(title).toHaveValue(rich.title); await query.fill('legacyprob');
    await expect(search.getByText('No matching notes.', { exact: true })).toBeVisible(); await app.stop();
    expect(canonicalSnapshot(app)).toEqual(migrated); expect(app.rebuild()).toContain('rebuilt and verified');
    expect(canonicalSnapshot(app)).toEqual(migrated);
    await app.start(); await page.reload(); await expect(title).toHaveValue(rich.title); await query.fill('legacyprob');
    await expect(search.getByRole('option')).toHaveCount(3); await expect(editor.locator('strong')).toContainText('Migrated bold proof.');
    await expect(image).toBeVisible(); expect(await app.get(`/api/notes/${rich.id}`)).toEqual(rich);
    expect(await app.get(`/api/notes/${copy.id}`)).toEqual(originalCopy); await app.stop(); expect(canonicalSnapshot(app)).toEqual(migrated);
    expect(external).toEqual([]); expect(errors).toEqual([]);
    expect(app.logs()).not.toContain('/api/search'); expect(app.logs()).not.toContain('legacyprob');
  } finally { await writeFile(info.outputPath('local-search-server.log'), app.logs()); await app.cleanup(); }
});
