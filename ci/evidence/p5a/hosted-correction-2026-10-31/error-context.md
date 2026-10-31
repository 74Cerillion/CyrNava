# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: lifecycle.spec.ts >> managed tabs close, restart and recover immediately closed unconfirmed edits
- Location: e2e/lifecycle.spec.ts:55:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('Saved', { exact: true })
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByText('Saved', { exact: true }) with timeout 10000ms
  - waiting for getByText('Saved', { exact: true })

```

```yaml
- link "Skip to note":
  - /url: "#note"
- complementary "Workspace navigation":
  - heading "CyrNava" [level=1]
  - paragraph: LOCAL WORKSPACE · v0.1.0
  - region "Global note search":
    - text: Search all notes
    - combobox "Search all notes"
    - paragraph: Search saved notes. ↑ ↓ select; Enter opens; Esc clears.
  - button "Workspace root"
  - button "New folder"
  - button "New note"
  - tree "Library":
    - treeitem "Note Immediately closed draft" [level=1] [selected]: Immediately closed draft
  - button "Rename"
  - button "Move"
  - button "Delete"
  - button "Refresh library"
  - status: "Backend at page load: online"
  - paragraph: Arrow keys navigate. Enter opens notes or toggles folders. F2 renames; Delete asks for confirmation.
  - paragraph:
    - link "Third-party notices":
      - /url: /third-party-notices.txt
- main:
  - text: Appearance
  - combobox "Appearance":
    - option "Light"
    - option "Dark"
    - option "System" [selected]
    - option "CyrNava"
  - button "Hide navigation" [expanded]
  - button "Manage templates"
  - button "Save as template"
  - text: Note title
  - textbox "Note title": Immediately closed draft
  - status: Save Error
  - alert:
    - paragraph: The recovered draft is based on an older revision. Review both versions before reopening.
    - button "Review conflict and recover"
  - paragraph: Your note stays on this computer. Wait for uploads and Saved before closing.
  - region "Note editor":
    - paragraph: Use / for formatting and images. Paste a screenshot with Ctrl+V, or type /image to select a local PNG, JPEG or WebP.
    - textbox "Note content":
      - paragraph:
        - text: Confirmed paragraph.
        - strong: Unconfirmed paragraph 🚀.
```

# Test source

```ts
  3   | import { execFileSync } from 'node:child_process';
  4   | import { cp, mkdtemp, mkdir, readFile, rm, symlink, writeFile } from 'node:fs/promises';
  5   | import { tmpdir } from 'node:os';
  6   | import { join, resolve } from 'node:path';
  7   | import { createServer } from 'node:net';
  8   | 
  9   | const root = resolve('..');
  10  | const python = join(root, 'backend/.venv/bin/python');
  11  | const launcher = join(root, 'desktop/launcher.py');
  12  | 
  13  | async function installation() {
  14  |   const directory = await mkdtemp(join(tmpdir(), 'cyrnava-lifecycle-browser-'));
  15  |   const release = join(directory, 'release');
  16  |   const state = join(directory, 'state');
  17  |   await mkdir(join(release, 'backend'), { recursive: true }); await mkdir(join(release, 'frontend'));
  18  |   await mkdir(state, { mode: 0o700 });
  19  |   await symlink(join(root, 'backend/app'), join(release, 'backend/app'));
  20  |   await symlink(join(root, 'backend/.venv'), join(release, 'backend/.venv'));
  21  |   // Snapshot the build: a concurrent source rebuild must not alter this app.
  22  |   await cp(join(root, 'frontend/dist'), join(release, 'frontend/dist'), { recursive: true });
  23  |   const probe = createServer(); await new Promise<void>((done) => probe.listen(0, '127.0.0.1', done));
  24  |   const address = probe.address(); if (!address || typeof address === 'string') throw new Error('No test port');
  25  |   const port = address.port; await new Promise<void>((done) => probe.close(() => done()));
  26  |   const config = join(directory, 'config.json');
  27  |   await writeFile(config, JSON.stringify({ release, state_dir: state, data_home: join(directory, 'data'), port,
  28  |     // Graphical dispatch is stubbed. Playwright opens the real isolated browser.
  29  |     browser: '/bin/true', opener: '/bin/true', zenity: '/bin/true',
  30  |     lifecycle: { heartbeat: 0.1, expiration: 1.2, grace: 0.4, startup: 10 } }));
  31  |   const url = `http://127.0.0.1:${port}`;
  32  |   let launches = 0;
  33  |   function run(action: 'open' | 'stop') {
  34  |     execFileSync(python, [launcher, '--config', config, action], { timeout: 25000 });
  35  |     if (action === 'open') launches++;
  36  |   }
  37  |   async function stopped() {
  38  |     await expect.poll(async () => {
  39  |       try { await fetch(url + '/health', { signal: AbortSignal.timeout(500) }); return false; }
  40  |       catch { return true; }
  41  |     }, { timeout: 10000, message: 'Final session releases backend port' }).toBe(true);
  42  |     // The supervisor logs this only after wait() has reaped its own child.
  43  |     await expect.poll(async () => (await readFile(join(state, 'launcher.log'), 'utf8')).split('Supervisor reaped backend and exited').length - 1).toBe(launches);
  44  |     const check = createServer();
  45  |     await new Promise<void>((done, reject) => { check.once('error', reject); check.listen(port, '127.0.0.1', done); });
  46  |     await new Promise<void>((done) => check.close(() => done()));
  47  |   }
  48  |   async function open(page: Page) {
  49  |     const registered = page.waitForResponse((response) => response.url().includes('/api/lifecycle/sessions/') && response.ok(), { timeout: 10000 });
  50  |     await page.goto(url); await registered;
  51  |   }
  52  |   return { url, run, stopped, open, cleanup: async () => { run('stop'); await rm(directory, { recursive: true, force: true }); } };
  53  | }
  54  | 
  55  | test('managed tabs close, restart and recover immediately closed unconfirmed edits', async ({ context }) => {
  56  |   const app = await installation();
  57  |   try {
  58  |     app.run('open'); const first = await context.newPage(); await app.open(first);
  59  |     await first.getByRole('button', { name: 'New note', exact: true }).click();
  60  |     await first.getByRole('dialog').getByLabel('Note title').fill('Lifecycle evidence');
  61  |     await first.getByRole('button', { name: 'Create', exact: true }).click();
  62  |     const content = first.getByRole('textbox', { name: 'Note content' });
  63  |     await content.click(); await first.keyboard.type('Confirmed paragraph.');
  64  |     await expect(first.getByText('Saved', { exact: true })).toBeVisible();
  65  |     const second = await context.newPage(); await app.open(second);
  66  |     await expect(second.getByRole('textbox', { name: 'Note content' })).toContainText('Confirmed paragraph.');
  67  |     await first.close();
  68  |     // Outlive the short test expiration while the second tab keeps renewing.
  69  |     await expect.poll(async () => (await fetch(app.url + '/health')).ok).toBe(true);
  70  |     await second.getByRole('textbox', { name: 'Note title' }).fill('Second tab remains active');
  71  |     await expect(second.getByText('Saved', { exact: true })).toBeVisible();
  72  |     await second.close(); await app.stopped();
  73  | 
  74  |     app.run('open'); const recovery = await context.newPage(); await app.open(recovery);
  75  |     await expect(recovery.getByRole('textbox', { name: 'Note content' })).toContainText('Confirmed paragraph.');
  76  |     // Hold no network save: this edit must survive solely via the sync snapshot.
  77  |     // Context routing outlives the closing page. Page-scoped routes disappear
  78  |     // at close and may let its visibility-triggered flush reach the backend.
  79  |     const blockSave = (route: import('@playwright/test').Route) => route.request().method() === 'PATCH' ? route.abort() : route.continue();
  80  |     await context.route('**/api/notes/*', blockSave);
  81  |     await recovery.getByRole('textbox', { name: 'Note title' }).fill('Immediately closed draft');
  82  |     const paragraph = recovery.getByRole('textbox', { name: 'Note content' }).locator('p').first();
  83  |     await paragraph.evaluate((element) => {
  84  |       element.closest<HTMLElement>('[contenteditable="true"]')!.focus();
  85  |       const range = document.createRange(); range.selectNodeContents(element); range.collapse(false);
  86  |       const selection = window.getSelection()!; selection.removeAllRanges(); selection.addRange(range);
  87  |     });
  88  |     await expect.poll(() => paragraph.evaluate((element) => element.contains(window.getSelection()!.anchorNode))).toBe(true);
  89  |     await recovery.keyboard.press('Control+b');
  90  |     await recovery.keyboard.type(' Unconfirmed paragraph 🚀.'); await recovery.keyboard.press('Control+b');
  91  |     await expect(recovery.getByRole('textbox', { name: 'Note content' }).locator('strong')).toContainText('Unconfirmed paragraph 🚀.');
  92  |     const nativeDraft = await recovery.evaluate(() => {
  93  |       const name = Object.keys(localStorage).find((key) => key.startsWith('engage.recovery.v1:'))!;
  94  |       return JSON.parse(localStorage.getItem(name)!);
  95  |     });
  96  |     await expect(recovery.getByText('Unsaved Changes', { exact: true })).toBeVisible();
  97  |     // page.close skips beforeunload prompting; it cannot help this recovery test.
  98  |     await recovery.close(); await app.stopped();
  99  |     await context.unroute('**/api/notes/*', blockSave);
  100 |     app.run('open'); const reopened = await context.newPage(); await app.open(reopened);
  101 |     await expect(reopened.getByRole('heading', { name: 'Recover unsaved edits' })).toBeVisible();
  102 |     await reopened.getByRole('button', { name: 'Recover draft', exact: true }).click();
> 103 |     await expect(reopened.getByText('Saved', { exact: true })).toBeVisible();
      |                                                                ^ Error: expect(locator).toBeVisible() failed
  104 |     await reopened.reload();
  105 |     await expect(reopened.getByRole('textbox', { name: 'Note title' })).toHaveValue('Immediately closed draft');
  106 |     await expect(reopened.getByRole('textbox', { name: 'Note content' })).toContainText('Unconfirmed paragraph 🚀.');
  107 |     await expect(reopened.getByRole('textbox', { name: 'Note content' }).locator('strong')).toContainText('Unconfirmed paragraph 🚀.');
  108 |     const response = await fetch(app.url + '/api/notes/' + nativeDraft.note_id);
  109 |     expect((await response.json()).document_json).toEqual(nativeDraft.document_json);
  110 |     await expect(reopened.getByRole('heading', { name: 'Recover unsaved edits' })).toHaveCount(0);
  111 |     await reopened.close(); await app.stopped();
  112 |   } finally { await app.cleanup(); }
  113 | });
  114 | 
  115 | test('killed isolated browser leaves no managed backend after lease expiry', async ({ playwright, browserName }) => {
  116 |   const app = await installation();
  117 |   let server: Awaited<ReturnType<typeof playwright.chromium.launchServer>> | undefined;
  118 |   try {
  119 |     server = await playwright[browserName].launchServer({ headless: true });
  120 |     app.run('open');
  121 |     const browser = await playwright[browserName].connect(server.wsEndpoint());
  122 |     const page = await browser.newPage(); await app.open(page);
  123 |     // Exact test-owned browser process, never the user's normal Firefox.
  124 |     server.process().kill('SIGKILL');
  125 |     await app.stopped();
  126 |   } finally { await server?.close().catch(() => {}); await app.cleanup(); }
  127 | });
  128 | 
```