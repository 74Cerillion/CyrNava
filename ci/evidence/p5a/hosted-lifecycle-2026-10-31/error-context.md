# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: lifecycle.spec.ts >> managed tabs close, restart and recover immediately closed unconfirmed edits
- Location: e2e/lifecycle.spec.ts:87:1

# Error details

```
Error: expect(received).toEqual(expected) // deep equality

- Expected  -  3
+ Received  + 10

@@ -7,10 +7,17 @@
          Object {
            "styles": Object {},
            "text": "Confirmed paragraph.",
            "type": "text",
          },
+         Object {
+           "styles": Object {
+             "bold": true,
+           },
+           "text": " Unconfirmed paragraph 🚀.",
+           "type": "text",
+         },
        ],
        "id": "166fa299-59b7-46c1-b0ae-c48b5bc40a0c",
        "props": Object {
          "backgroundColor": "default",
          "textAlignment": "left",
@@ -20,9 +27,9 @@
      },
    ],
    "folder_id": null,
    "format_version": 1,
    "id": "9acbb5f9-de61-4909-8ee9-752b69d2f6dd",
-   "revision": 3,
-   "title": "Second tab remains active",
-   "updated_at": "2026-10-31T05:22:22.416674+00:00",
+   "revision": 4,
+   "title": "Immediately closed draft",
+   "updated_at": "2026-10-31T05:22:24.650597+00:00",
  }
```

# Page snapshot

```yaml
- generic [ref=e3]:
  - link "Skip to note" [ref=e4] [cursor=pointer]:
    - /url: "#note"
  - complementary "Workspace navigation" [ref=e5]:
    - generic [ref=e7]:
      - heading "CyrNava" [level=1] [ref=e8]
      - paragraph [ref=e9]: LOCAL WORKSPACE · v0.1.0
    - region "Global note search" [ref=e10]:
      - generic [ref=e11]: Search all notes
      - combobox "Search all notes" [disabled] [ref=e14]
      - paragraph [ref=e15]: Search saved notes. ↑ ↓ select; Enter opens; Esc clears.
    - button "Workspace root" [disabled] [ref=e16]
    - generic [ref=e19]:
      - button "New folder" [disabled] [ref=e20]
      - button "New note" [disabled] [ref=e23]
    - tree "Library" [ref=e26]:
      - treeitem "Note Immediately closed draft" [active] [level=1] [selected] [ref=e27] [cursor=pointer]:
        - generic [ref=e31]: Immediately closed draft
        - generic [aria-hidden] [ref=e32]: ●
    - generic [ref=e33]:
      - button "Rename" [disabled] [ref=e34]
      - button "Move" [disabled] [ref=e37]
      - button "Delete" [disabled] [ref=e40]
      - button "Refresh library" [disabled] [ref=e43]
    - status [ref=e46]: "Backend at page load: online"
    - paragraph [ref=e47]: Arrow keys navigate. Enter opens notes or toggles folders. F2 renames; Delete asks for confirmation.
    - paragraph [ref=e48]:
      - link "Third-party notices" [ref=e49] [cursor=pointer]:
        - /url: /third-party-notices.txt
  - main [ref=e50]:
    - generic [ref=e51]:
      - generic [ref=e52]:
        - text: Appearance
        - combobox "Appearance" [ref=e53]:
          - option "Light"
          - option "Dark"
          - option "System" [selected]
          - option "CyrNava"
      - button "Hide navigation" [expanded] [ref=e54] [cursor=pointer]
      - button "Manage templates" [disabled] [ref=e57]
      - button "Save as template" [disabled] [ref=e60]
    - alert [ref=e63]: Connection to CyrNava was interrupted. Your local drafts remain available. If CyrNava has stopped, launch its desktop icon again; this tab will reconnect.
    - region "Draft recovery" [ref=e64]:
      - heading "Recover unsaved edits" [level=2] [ref=e65]
      - paragraph [ref=e66]: SQLite still holds the saved note. These browser drafts may contain unconfirmed edits from this or another tab. Nothing is overwritten until you choose a draft and it saves with its original revision.
      - article [ref=e67]:
        - paragraph [ref=e68]:
          - strong [ref=e69]: Immediately closed draft
          - text: — base revision 3, 2026-10-31T05:22:24.616Z
        - group [ref=e70]:
          - generic "Inspect draft JSON" [ref=e71]
        - button "Recover draft" [disabled] [ref=e72]
        - button "Download draft" [ref=e73] [cursor=pointer]
      - button "Continue with saved note (retain drafts)" [disabled] [ref=e74]
```

# Test source

```ts
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
  55  | 
  56  | // Synthetic-test diagnostics: revisions, status and relative timing only. Never
  57  | // copy request headers, session credentials, titles or document contents here.
  58  | function observeRevisions(context: BrowserContext, testInfo: TestInfo) {
  59  |   const events: object[] = [];
  60  |   const started = Date.now();
  61  |   const record = (value: object) => events.push({ ms: Date.now() - started, ...value });
  62  |   const request = (request: import('@playwright/test').Request) => {
  63  |     if (!new URL(request.url()).pathname.startsWith('/api/notes/')) return;
  64  |     const body = request.postData();
  65  |     record({ event: 'request', method: request.method(), revision: body ? JSON.parse(body).revision : undefined });
  66  |   };
  67  |   const response = async (response: import('@playwright/test').Response) => {
  68  |     if (!new URL(response.url()).pathname.startsWith('/api/notes/')) return;
  69  |     try {
  70  |       const body = await response.json();
  71  |       record({ event: 'response', method: response.request().method(), status: response.status(), revision: body.revision });
  72  |     } catch { /* A closing page may discard its response; checkpoints verify SQLite. */ }
  73  |   };
  74  |   context.on('request', request); context.on('response', response);
  75  |   return { record, finish: async () => {
  76  |     context.off('request', request); context.off('response', response);
  77  |     await mkdir(testInfo.outputDir, { recursive: true });
  78  |     const path = testInfo.outputPath('revision-timeline.json');
  79  |     await writeFile(path, JSON.stringify(events, null, 2));
  80  |     await testInfo.attach('revision-timeline', { path, contentType: 'application/json' });
  81  |   } };
  82  | }
  83  | 
  84  | const isNoteRead = (response: import('@playwright/test').Response) =>
  85  |   response.request().method() === 'GET' && /\/api\/notes\/[^/]+$/.test(new URL(response.url()).pathname) && response.ok();
  86  | 
  87  | test('managed tabs close, restart and recover immediately closed unconfirmed edits', async ({ context }, testInfo) => {
  88  |   const app = await installation();
  89  |   const timeline = observeRevisions(context, testInfo);
  90  |   try {
  91  |     app.run('open'); const first = await context.newPage(); await app.open(first);
  92  |     await first.getByRole('button', { name: 'New note', exact: true }).click();
  93  |     await first.getByRole('dialog').getByLabel('Note title').fill('Lifecycle evidence');
  94  |     await first.getByRole('button', { name: 'Create', exact: true }).click();
  95  |     const content = first.getByRole('textbox', { name: 'Note content' });
  96  |     await content.click(); await first.keyboard.type('Confirmed paragraph.');
  97  |     await expect(first.getByText('Saved', { exact: true })).toBeVisible();
  98  |     const second = await context.newPage(); await app.open(second);
  99  |     await expect(second.getByRole('textbox', { name: 'Note content' })).toContainText('Confirmed paragraph.');
  100 |     await first.close();
  101 |     // Outlive the short test expiration while the second tab keeps renewing.
  102 |     await expect.poll(async () => (await fetch(app.url + '/health')).ok).toBe(true);
  103 |     await second.getByRole('textbox', { name: 'Note title' }).fill('Second tab remains active');
  104 |     await expect(second.getByText('Saved', { exact: true })).toBeVisible();
  105 |     await second.close(); await app.stopped();
  106 | 
  107 |     // Install the write barrier BEFORE opening the next page. A route added
  108 |     // after editor readiness cannot intercept an already dispatched autosave.
  109 |     const blockSave = (route: import('@playwright/test').Route) => route.request().method() === 'PATCH' ? route.abort() : route.continue();
  110 |     await context.route('**/api/notes/*', blockSave);
  111 |     app.run('open'); const recovery = await context.newPage();
  112 |     const baselineRead = recovery.waitForResponse(isNoteRead);
  113 |     await app.open(recovery);
  114 |     const baseline = await (await baselineRead).json();
  115 |     timeline.record({ event: 'outage-baseline', canonical_revision: baseline.revision });
  116 |     await expect(recovery.getByRole('textbox', { name: 'Note content' })).toContainText('Confirmed paragraph.');
  117 |     // Context routing survives page.close and remains until restart verifies
  118 |     // that neither startup edits nor visibility-triggered flushes committed.
  119 |     await recovery.getByRole('textbox', { name: 'Note title' }).fill('Immediately closed draft');
  120 |     const paragraph = recovery.getByRole('textbox', { name: 'Note content' }).locator('p').first();
  121 |     await paragraph.evaluate((element) => {
  122 |       element.closest<HTMLElement>('[contenteditable="true"]')!.focus();
  123 |       const range = document.createRange(); range.selectNodeContents(element); range.collapse(false);
  124 |       const selection = window.getSelection()!; selection.removeAllRanges(); selection.addRange(range);
  125 |     });
  126 |     await expect.poll(() => paragraph.evaluate((element) => element.contains(window.getSelection()!.anchorNode))).toBe(true);
  127 |     await recovery.keyboard.press('Control+b');
  128 |     await recovery.keyboard.type(' Unconfirmed paragraph 🚀.'); await recovery.keyboard.press('Control+b');
  129 |     await expect(recovery.getByRole('textbox', { name: 'Note content' }).locator('strong')).toContainText('Unconfirmed paragraph 🚀.');
  130 |     const nativeDraft = await recovery.evaluate(() => {
  131 |       const name = Object.keys(localStorage).find((key) => key.startsWith('engage.recovery.v1:'))!;
  132 |       return JSON.parse(localStorage.getItem(name)!);
  133 |     });
  134 |     expect(nativeDraft.base_revision).toBe(baseline.revision);
  135 |     timeline.record({ event: 'retained-draft', base_revision: nativeDraft.base_revision });
  136 |     await expect(recovery.getByText('Unsaved Changes', { exact: true })).toBeVisible();
  137 |     // page.close skips beforeunload prompting; it cannot help this recovery test.
  138 |     await recovery.close(); await app.stopped();
  139 |     app.run('open'); const reopened = await context.newPage();
  140 |     const restartedRead = reopened.waitForResponse(isNoteRead);
  141 |     await app.open(reopened);
  142 |     const unchanged = await (await restartedRead).json();
> 143 |     expect(unchanged).toEqual(baseline);
      |                       ^ Error: expect(received).toEqual(expected) // deep equality
  144 |     timeline.record({ event: 'outage-source-unchanged', canonical_revision: unchanged.revision, base_revision: nativeDraft.base_revision });
  145 |     await context.unroute('**/api/notes/*', blockSave);
  146 |     await expect(reopened.getByRole('heading', { name: 'Recover unsaved edits' })).toBeVisible();
  147 |     const savedResponse = reopened.waitForResponse((response) => response.request().method() === 'PATCH' && response.ok());
  148 |     await reopened.getByRole('button', { name: 'Recover draft', exact: true }).click();
  149 |     const acknowledged = await (await savedResponse).json();
  150 |     expect(acknowledged.revision).toBe(nativeDraft.base_revision + 1);
  151 |     expect(acknowledged.document_json).toEqual(nativeDraft.document_json);
  152 |     timeline.record({ event: 'recovery-acknowledged', revision: acknowledged.revision });
  153 |     await expect(reopened.getByText('Saved', { exact: true })).toBeVisible();
  154 |     await reopened.reload();
  155 |     await expect(reopened.getByRole('textbox', { name: 'Note title' })).toHaveValue('Immediately closed draft');
  156 |     await expect(reopened.getByRole('textbox', { name: 'Note content' })).toContainText('Unconfirmed paragraph 🚀.');
  157 |     await expect(reopened.getByRole('textbox', { name: 'Note content' }).locator('strong')).toContainText('Unconfirmed paragraph 🚀.');
  158 |     const response = await fetch(app.url + '/api/notes/' + nativeDraft.note_id);
  159 |     expect((await response.json()).document_json).toEqual(nativeDraft.document_json);
  160 |     await expect(reopened.getByRole('heading', { name: 'Recover unsaved edits' })).toHaveCount(0);
  161 |     await reopened.close(); await app.stopped();
  162 |   } finally { try { await timeline.finish(); } finally { await app.cleanup(); } }
  163 | });
  164 | 
  165 | 
  166 | test('a committed write with a lost acknowledgement retains its draft and requires conflict review', async ({ context }, testInfo) => {
  167 |   const app = await installation();
  168 |   const timeline = observeRevisions(context, testInfo);
  169 |   let releaseResponse!: () => void;
  170 |   const responseGate = new Promise<void>((resolve) => { releaseResponse = resolve; });
  171 |   try {
  172 |     app.run('open'); const page = await context.newPage(); await app.open(page);
  173 |     await page.getByRole('button', { name: 'New note', exact: true }).click();
  174 |     await page.getByRole('dialog').getByLabel('Note title').fill('Acknowledgement gate');
  175 |     await page.getByRole('button', { name: 'Create', exact: true }).click();
  176 |     await expect(page.getByRole('textbox', { name: 'Note title' })).toHaveValue('Acknowledgement gate');
  177 |     let committed!: (revision: number) => void;
  178 |     const backendCommitted = new Promise<number>((resolve) => { committed = resolve; });
  179 |     let intercepted = false;
  180 |     await context.route('**/api/notes/*', async (route) => {
  181 |       if (route.request().method() !== 'PATCH') return route.continue();
  182 |       if (intercepted) return route.abort();
  183 |       intercepted = true;
  184 |       // Commit through the real API, but withhold only this response. No sleep,
  185 |       // timeout increase, request retry or application code hook is involved.
  186 |       const response = await route.fetch({ maxRetries: 0 });
  187 |       expect(response.ok()).toBe(true);
  188 |       const saved = await response.json();
  189 |       timeline.record({ event: 'backend-committed-acknowledgement-held', revision: saved.revision });
  190 |       committed(saved.revision);
  191 |       await responseGate;
  192 |       await route.fulfill({ response }).catch(() => { /* The old page is closed. */ });
  193 |     });
  194 |     await page.getByRole('textbox', { name: 'Note title' }).fill('Committed before close');
  195 |     const committedRevision = await backendCommitted;
  196 |     await page.getByRole('textbox', { name: 'Note title' }).fill('Unconfirmed newer title');
  197 |     const retained = await page.evaluate(() => {
  198 |       const key = Object.keys(localStorage).find((name) => name.startsWith('engage.recovery.v1:'))!;
  199 |       return JSON.parse(localStorage.getItem(key)!);
  200 |     });
  201 |     expect(retained.base_revision).toBe(committedRevision - 1);
  202 |     timeline.record({ event: 'retained-before-close', base_revision: retained.base_revision });
  203 |     await page.close(); releaseResponse(); await app.stopped();
  204 |     await context.unrouteAll({ behavior: 'wait' });
  205 |     app.run('open'); const reopened = await context.newPage(); await app.open(reopened);
  206 |     await expect(reopened.getByRole('heading', { name: 'Recover unsaved edits' })).toBeVisible();
  207 |     let writesAfterChoice = 0;
  208 |     const countWrite = (request: import('@playwright/test').Request) => {
  209 |       if (request.method() === 'PATCH' && /\/api\/notes\//.test(request.url())) writesAfterChoice++;
  210 |     };
  211 |     context.on('request', countWrite);
  212 |     await reopened.getByRole('button', { name: 'Recover draft', exact: true }).click();
  213 |     await expect(reopened.getByText('Save Error', { exact: true })).toBeVisible();
  214 |     await expect(reopened.getByRole('button', { name: 'Review conflict and recover' })).toBeVisible();
  215 |     const current = await (await fetch(app.url + '/api/notes/' + retained.note_id)).json();
  216 |     expect(current.revision).toBe(committedRevision);
  217 |     expect(current.title).toBe('Committed before close');
  218 |     const drafts = await reopened.evaluate(() => Object.keys(localStorage)
  219 |       .filter((name) => name.startsWith('engage.recovery.v1:')).map((name) => JSON.parse(localStorage.getItem(name)!)));
  220 |     expect(drafts).toContainEqual(retained);
  221 |     expect(writesAfterChoice).toBe(0);
  222 |     timeline.record({ event: 'stale-draft-protected', canonical_revision: current.revision, base_revision: retained.base_revision, writes_after_choice: writesAfterChoice });
  223 |     context.off('request', countWrite);
  224 |     await reopened.close(); await app.stopped();
  225 |   } finally { releaseResponse(); try { await timeline.finish(); } finally { await app.cleanup(); } }
  226 | });
  227 | 
  228 | test('killed isolated browser leaves no managed backend after lease expiry', async ({ playwright, browserName }) => {
  229 |   const app = await installation();
  230 |   let server: Awaited<ReturnType<typeof playwright.chromium.launchServer>> | undefined;
  231 |   try {
  232 |     server = await playwright[browserName].launchServer({ headless: true });
  233 |     app.run('open');
  234 |     const browser = await playwright[browserName].connect(server.wsEndpoint());
  235 |     const page = await browser.newPage(); await app.open(page);
  236 |     // Exact test-owned browser process, never the user's normal Firefox.
  237 |     server.process().kill('SIGKILL');
  238 |     await app.stopped();
  239 |   } finally { await server?.close().catch(() => {}); await app.cleanup(); }
  240 | });
  241 | 
```