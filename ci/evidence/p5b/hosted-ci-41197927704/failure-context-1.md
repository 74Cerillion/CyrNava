# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: workspace.spec.ts >> appearance follows system and explicit preferences without changing notes, templates or autosave
- Location: e2e/workspace.spec.ts:112:1

# Error details

```
Error: expect(received).toContain(expected) // indexOf

Expected substring: "Enter text"
Received string:    "none"

Call Log:
- Timeout 10000ms exceeded while waiting on the predicate
```

# Page snapshot

```yaml
- generic [ref=f2e3]:
  - link "Skip to note" [ref=f2e4] [cursor=pointer]:
    - /url: "#note"
  - complementary "Workspace navigation" [ref=f2e5]:
    - generic [ref=f2e7]:
      - heading "CyrNava" [level=1] [ref=f2e8]
      - paragraph [ref=f2e9]: LOCAL WORKSPACE · v0.1.0
    - region "Global note search" [ref=f2e10]:
      - generic [ref=f2e11]: Search all notes
      - combobox "Search all notes" [ref=f2e14]
      - paragraph [ref=f2e15]: Search saved notes. ↑ ↓ select; Enter opens; Esc clears.
    - button "Workspace root" [ref=f2e16] [cursor=pointer]
    - generic [ref=f2e19]:
      - button "New folder" [ref=f2e20] [cursor=pointer]
      - button "New note" [ref=f2e23] [cursor=pointer]
    - tree "Library" [ref=f2e26]:
      - treeitem "Note Appearance training" [level=1] [selected] [ref=f2e27] [cursor=pointer]:
        - generic [ref=f2e31]: Appearance training
        - generic [aria-hidden] [ref=f2e32]: ●
    - generic [ref=f2e33]:
      - button "Rename" [ref=f2e34] [cursor=pointer]
      - button "Move" [ref=f2e37] [cursor=pointer]
      - button "Delete" [ref=f2e40] [cursor=pointer]
      - button "Refresh library" [ref=f2e43] [cursor=pointer]
    - status [ref=f2e46]: "Backend at page load: online"
    - paragraph [ref=f2e47]: Arrow keys navigate. Enter opens notes or toggles folders. F2 renames; Delete asks for confirmation.
    - paragraph [ref=f2e48]:
      - link "Third-party notices" [ref=f2e49] [cursor=pointer]:
        - /url: /third-party-notices.txt
  - main [ref=f2e50]:
    - generic [ref=f2e51]:
      - generic [ref=f2e52]:
        - text: Appearance
        - combobox "Appearance" [ref=f2e53]:
          - option "Light" [selected]
          - option "Dark"
          - option "System"
          - option "CyrNava"
      - button "Hide navigation" [expanded] [ref=f2e54] [cursor=pointer]
      - button "Manage templates" [ref=f2e57] [cursor=pointer]
      - button "Save as template" [ref=f2e60] [cursor=pointer]
    - generic [ref=f2e63]:
      - generic [ref=f2e64]: Note title
      - generic [ref=f2e65]:
        - textbox "Note title" [ref=f2e66]: Appearance training
        - status [ref=f2e67]: Saved
      - paragraph [ref=f2e70]: Your note stays on this computer. Wait for uploads and Saved before closing.
    - region "Note editor" [ref=f2e71]:
      - paragraph [ref=f2e72]: Use / for formatting and images. Paste a screenshot with Ctrl+V, or type /image to select a local PNG, JPEG or WebP.
      - textbox "Note content" [active] [ref=f2e74]:
        - generic [ref=f2e75]:
          - heading "Target Information" [level=2] [ref=f2e79]
          - paragraph [ref=f2e83]
          - heading "Discovery Methodology" [level=2] [ref=f2e87]
          - paragraph [ref=f2e91]
          - heading "Open Ports" [level=2] [ref=f2e95]
          - paragraph [ref=f2e99]
          - heading "Identified Services" [level=2] [ref=f2e103]
          - paragraph [ref=f2e107]
          - heading "Service Versions" [level=2] [ref=f2e111]
          - paragraph [ref=f2e115]
          - heading "Commands Executed" [level=2] [ref=f2e119]
          - code [ref=f2e124]: printf "documentation only"
          - heading "Enumeration Results" [level=2] [ref=f2e128]
          - paragraph [ref=f2e132]
          - heading "Potential Attack Surface" [level=2] [ref=f2e136]
          - paragraph [ref=f2e140]
          - heading "Screenshots / Evidence" [level=2] [ref=f2e144]
          - paragraph [ref=f2e148]
          - heading "Next Steps" [level=2] [ref=f2e152]
          - paragraph [ref=f2e156]:
            - strong [ref=f2e157]: Theme-
          - paragraph [ref=f2e161]:
            - strong [ref=f2e162]: bold
          - paragraph [ref=f2e166]: Native document content.
          - paragraph [ref=f2e170]:
            - link "Local reference" [ref=f2e171]:
              - /url: https://example.invalid/reference
          - generic [ref=f2e174]:
            - text: •
            - paragraph [ref=f2e175]:
              - emphasis [ref=f2e176]: Preserved list item
          - paragraph [ref=f2e180]
```

# Test source

```ts
  128 |   async function themed(value: 'light' | 'dark') {
  129 |     await expect(page.locator('html')).toHaveAttribute('data-mantine-color-scheme', value);
  130 |     await expect(page.getByRole('region', { name: 'Note editor' }).locator('.bn-container')).toHaveAttribute('data-color-scheme', value);
  131 |     await expect(page.getByRole('region', { name: 'Note editor' }).locator('.bn-mantine').first()).toHaveAttribute('data-mantine-color-scheme', value);
  132 |   }
  133 |   async function atEnd() {
  134 |     await editor().evaluate((element) => {
  135 |       (element as HTMLElement).focus(); const range = document.createRange();
  136 |       range.selectNodeContents(element); range.collapse(false);
  137 |       const selection = window.getSelection()!; selection.removeAllRanges(); selection.addRange(range);
  138 |     });
  139 |   }
  140 |   try {
  141 |     await env.start(); await page.emulateMedia({ colorScheme: 'light' });
  142 |     await page.addInitScript(() => { if (!localStorage.getItem('engage.appearance.v1')) localStorage.setItem('engage.appearance.v1', 'dark'); });
  143 |     await page.goto(env.url, { waitUntil: 'commit' });
  144 |     await expect(page.locator('html')).toHaveAttribute('data-mantine-color-scheme', 'dark');
  145 |     // Release CSS is a render-blocking head link. Vite injects development CSS
  146 |     // through the module graph that this test deliberately stalls.
  147 |     if (releaseMode) await expect.poll(() => page.locator('html').evaluate((element) => getComputedStyle(element).backgroundColor)).toBe('rgb(24, 33, 47)');
  148 |     await expect(page.locator('#root')).toBeEmpty(); release(); await page.unroute(entrypoint);
  149 |     await expect(appearance()).toHaveValue('dark');
  150 |     await expect(page).toHaveTitle('CyrNava');
  151 |     await expect(page.getByRole('heading', { name: 'CyrNava', exact: true })).toBeVisible();
  152 |     await page.getByRole('button', { name: 'New note', exact: true }).click();
  153 |     const createDialog = page.getByRole('dialog');
  154 |     await createDialog.getByLabel('Note title', { exact: true }).fill('Appearance training');
  155 |     await createDialog.getByLabel('Starting content', { exact: true }).selectOption('builtin:enumeration');
  156 |     await createDialog.getByRole('button', { name: 'Create', exact: true }).click(); await saved(page);
  157 |     await atEnd(); await page.keyboard.press('Control+b'); await page.keyboard.type('Theme-safe bold');
  158 |     await page.keyboard.press('Control+b'); await page.keyboard.press('Enter'); await page.keyboard.type('Native document content.'); await saved(page);
  159 |     const owner = (await getJson(`${env.api}/api/tree`)).notes[0];
  160 |     const persisted = () => getJson(`${env.api}/api/notes/${owner.id}`);
  161 |     const seeded = await persisted();
  162 |     seeded.document_json.find((block: AssetBlock) => block.type === 'codeBlock').content = [{ type: 'text', text: 'printf "documentation only"', styles: {} }];
  163 |     seeded.document_json.push({ type: 'paragraph', content: [{ type: 'link', href: 'https://example.invalid/reference', content: [{ type: 'text', text: 'Local reference', styles: {} }] }], children: [] });
  164 |     seeded.document_json.push({ type: 'bulletListItem', content: [{ type: 'text', text: 'Preserved list item', styles: { italic: true } }], children: [] });
  165 |     seeded.document_json.push({ type: 'paragraph', content: [], children: [] });
  166 |     expect((await fetch(`${env.api}/api/notes/${owner.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ revision: seeded.revision, document_json: seeded.document_json }) })).status).toBe(200);
  167 |     await page.reload(); await saved(page);
  168 |     const before = await persisted(); const changes = writes.length;
  169 |     const instance = await editor().elementHandle();
  170 | 
  171 |     for (const mode of ['light', 'dark'] as const) {
  172 |       await appearance().selectOption(mode); await themed(mode);
  173 |       await page.emulateMedia({ colorScheme: mode === 'light' ? 'dark' : 'light' }); await themed(mode);
  174 |       expect(await instance!.evaluate((node) => node.isConnected)).toBe(true);
  175 |       await expect(editor().locator('strong')).toContainText('Theme-safe bold');
  176 |       await readable(page.locator('.editor-help')); await readable(page.locator('.save-state'));
  177 |       await readable(page.getByRole('textbox', { name: 'Note title', exact: true }));
  178 |       await readable(page.getByRole('treeitem', { name: 'Note Appearance training', exact: true }));
  179 |       await readable(editor().getByRole('link', { name: 'Local reference', exact: true }));
  180 |       await readable(editor().locator('[data-content-type="codeBlock"]'));
  181 |       await page.getByRole('button', { name: 'Hide navigation', exact: true }).click();
  182 |       await expect(appearance()).toBeVisible();
  183 |       await page.screenshot({ path: info.outputPath(`appearance-${mode}-collapsed.png`), fullPage: true });
  184 |       await page.getByRole('button', { name: 'Show navigation', exact: true }).click();
  185 |     }
  186 |     await appearance().selectOption('auto');
  187 |     await editor().focus();
  188 |     for (const colorScheme of ['dark', 'light'] as const) {
  189 |       await page.emulateMedia({ colorScheme }); await themed(colorScheme);
  190 |       await expect(editor()).toBeFocused();
  191 |     }
  192 |     expect(await persisted()).toEqual(before); expect(writes).toHaveLength(changes);
  193 |     await page.emulateMedia({ colorScheme: 'dark' }); await themed('dark');
  194 |     await page.getByRole('button', { name: 'Hide navigation', exact: true }).click();
  195 |     await page.reload(); await saved(page); await themed('dark');
  196 |     await expect(appearance()).toHaveValue('auto'); await expect(page.getByRole('complementary')).toBeHidden();
  197 |     await page.getByRole('button', { name: 'Show navigation', exact: true }).focus();
  198 |     await page.keyboard.press('Enter'); await expect(page.getByRole('complementary')).toBeVisible();
  199 |     await appearance().focus(); await page.keyboard.press('Tab'); await page.keyboard.press('Shift+Tab');
  200 |     await expect(appearance()).toBeFocused();
  201 |     expect(await appearance().evaluate((element) => getComputedStyle(element).outlineStyle)).toBe('solid');
  202 | 
  203 |     for (const mode of ['light', 'dark'] as const) {
  204 |       await appearance().selectOption(mode); await themed(mode);
  205 |       await editor().getByText('Theme-safe bold', { exact: true }).dblclick();
  206 |       const toolbar = page.locator('.bn-formatting-toolbar'); await expect(toolbar).toBeVisible();
  207 |       await readable(toolbar);
  208 |       await toolbar.getByRole('button', { name: 'Colors', exact: true }).click();
  209 |       await expect(page.getByText('Text', { exact: true }).last()).toBeVisible();
  210 |       await expect(page.locator('.bn-color-picker-dropdown')).toHaveCSS('opacity', '1');
  211 |       await readable(page.getByText('Text', { exact: true }).last());
  212 |       await readable(page.locator('.bn-color-picker-dropdown').getByRole('menuitem').first());
  213 |       await page.screenshot({ path: info.outputPath(`appearance-${mode}-formatting.png`), fullPage: true });
  214 |       await page.keyboard.press('Escape'); await atEnd();
  215 |       await page.keyboard.press('Enter'); await page.keyboard.type('/');
  216 |       const menu = page.locator('.bn-suggestion-menu'); await expect(menu).toBeVisible();
  217 |       await expect.poll(() => menu.evaluate((element) => {
  218 |         let node: Element | null = element;
  219 |         while (node) { if (getComputedStyle(node).opacity !== '1') return false; node = node.parentElement; }
  220 |         return true;
  221 |       })).toBe(true);
  222 |       await readable(menu); await readable(menu.locator('.bn-suggestion-menu-label').first());
  223 |       await readable(menu.locator('.bn-mt-suggestion-menu-item-subtitle').first());
  224 |       await expect(menu.locator('xpath=ancestor::*[@data-mantine-color-scheme][1]')).toHaveAttribute('data-mantine-color-scheme', mode);
  225 |       await page.screenshot({ path: info.outputPath(`appearance-${mode}-slash-menu.png`), fullPage: true });
  226 |       await page.keyboard.press('Escape'); await page.keyboard.press('Backspace'); await saved(page);
  227 |       const placeholder = editor().locator('[data-content-type="paragraph"]').last();
> 228 |       await expect.poll(() => placeholder.evaluate((element) => getComputedStyle(element, '::after').content)).toContain('Enter text');
      |                                                                                                                ^ Error: expect(received).toContain(expected) // indexOf
  229 |       await readable(placeholder, 4.5, '::after');
  230 |       await page.getByRole('button', { name: 'New note', exact: true }).click();
  231 |       const dialog = page.getByRole('dialog'); await readable(dialog); await readable(dialog.getByLabel('Starting content', { exact: true }));
  232 |       await expect(dialog.getByRole('option', { name: 'Enumeration Notes', exact: true })).toHaveCount(1);
  233 |       await page.screenshot({ path: info.outputPath(`appearance-${mode}-template-selection.png`), fullPage: true });
  234 |       await dialog.getByRole('button', { name: 'Cancel', exact: true }).click();
  235 |       await page.getByRole('button', { name: 'Manage templates', exact: true }).click();
  236 |       await page.getByRole('dialog').getByLabel('Available templates', { exact: true }).selectOption('builtin:enumeration');
  237 |       await page.screenshot({ path: info.outputPath(`appearance-${mode}-template-manager.png`), fullPage: true });
  238 |       await page.getByRole('dialog').getByRole('button', { name: 'Close templates', exact: true }).click();
  239 |     }
  240 |     await page.getByRole('button', { name: 'Save as template', exact: true }).click();
  241 |     await readable(page.getByRole('dialog'));
  242 |     await page.getByRole('dialog').getByLabel('Template name', { exact: true }).fill('Appearance-neutral template');
  243 |     await page.getByRole('dialog').getByRole('button', { name: 'Save template', exact: true }).click();
  244 |     await expect(page.getByRole('dialog')).toBeHidden();
  245 |     const template = (await getJson(`${env.api}/api/templates`)).find((row: { name: string }) => row.name === 'Appearance-neutral template');
  246 |     const canonical = (await persisted()).document_json;
  247 |     const withoutIds = (blocks: unknown) => JSON.parse(JSON.stringify(blocks, (key, value) => key === 'id' ? undefined : value));
  248 |     for (const mode of ['light', 'dark'] as const) {
  249 |       await appearance().selectOption(mode);
  250 |       const response = await fetch(`${env.api}/api/templates/${template.id}/notes`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ title: `Copy in ${mode}`, revision: 1 }) });
  251 |       expect(response.status).toBe(201); expect(withoutIds((await response.json()).document_json)).toEqual(withoutIds(canonical));
  252 |     }
  253 |     await env.stopBackend();
  254 |     await page.getByRole('textbox', { name: 'Note title', exact: true }).fill('Theme preserves pending edits');
  255 |     await expect(page.getByText('Save Error', { exact: true })).toBeVisible();
  256 |     for (const mode of ['light', 'dark'] as const) {
  257 |       await appearance().selectOption(mode); await themed(mode);
  258 |       await readable(page.locator('.save-state')); await readable(page.getByRole('alert').last());
  259 |       await page.screenshot({ path: info.outputPath(`appearance-${mode}-save-error.png`), fullPage: true });
  260 |     }
  261 |     await env.startBackend(); await page.getByRole('button', { name: 'Retry save', exact: true }).click(); await saved(page);
  262 |     expect((await persisted()).document_json).toEqual(canonical);
  263 |     await page.reload(); await saved(page); await themed('dark'); await expect(appearance()).toHaveValue('dark');
  264 |     await page.setViewportSize({ width: 390, height: 844 });
  265 |     await page.getByRole('button', { name: 'Hide navigation', exact: true }).click(); await expect(appearance()).toBeVisible();
  266 |     expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  267 |     await page.screenshot({ path: info.outputPath('appearance-dark-mobile.png'), fullPage: true });
  268 |     expect(external).toEqual([]); expect(errors).toEqual([]);
  269 |   } finally { release(); await env.shutdown(); await writeFile(info.outputPath('local-server.log'), env.logs()); await rm(env.directory, { recursive: true, force: true }); }
  270 | });
  271 | 
  272 | test('CyrNava reference appearance preserves the live editor, local images and saved content', async ({ page }, info) => {
  273 |   const env = await environment();
  274 |   const external: string[] = [];
  275 |   await page.route('**/*', (route) => {
  276 |     if (new URL(route.request().url()).hostname !== '127.0.0.1') { external.push(route.request().url()); return route.abort(); }
  277 |     return route.continue();
  278 |   });
  279 |   async function post(path: string, body: unknown) {
  280 |     const response = await fetch(env.api + path, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
  281 |     expect(response.status).toBe(201); return response.json();
  282 |   }
  283 |   try {
  284 |     await env.start(); await page.emulateMedia({ colorScheme: 'light' });
  285 |     await post('/api/folders', { name: 'Defensive Security' });
  286 |     const engagement = await post('/api/folders', { name: 'Engagements' });
  287 |     const folder = await post('/api/folders', { name: 'Brains', parent_id: engagement.id });
  288 |     await post('/api/folders', { name: "Fool’s Mate", parent_id: engagement.id });
  289 |     await post('/api/folders', { name: 'FlareVM' });
  290 |     await post('/api/folders', { name: 'Offensive Security' });
  291 |     const note = await post('/api/notes', { title: 'Brains', folder_id: folder.id, document_json: [
  292 |       { type: 'heading', props: { level: 1 }, content: [{ type: 'text', text: 'Discovery', styles: {} }] },
  293 |       { type: 'paragraph', content: [{ type: 'text', text: "A synthetic local lab note: discover which services are running on the host, document the observations, and keep the supporting screenshot alongside the written explanation.", styles: {} }] },
  294 |     ] });
  295 |     const png = join(env.directory, 'visual-fixture.png');
  296 |     execFileSync(python, ['-c', 'from PIL import Image,ImageDraw;import sys;im=Image.new("RGB",(600,340),"#f6f7f9");d=ImageDraw.Draw(im);d.rectangle((0,0,599,32),fill="#20324a");d.text((16,9),"Synthetic local evidence — example.test",fill="white");d.text((190,150),"Local service documentation",fill="#18212f",font_size=18);im.save(sys.argv[1])', png]);
  297 |     const uploaded = await fetch(`${env.api}/api/assets?note_id=${note.id}`, { method: 'POST', headers: { 'content-type': 'image/png' }, body: await readFile(png) });
  298 |     expect(uploaded.status).toBe(201); const asset = await uploaded.json();
  299 |     const content = [...note.document_json, { type: 'image', props: { url: asset.url, previewWidth: 600 }, children: [] }, { type: 'paragraph', content: [] }];
  300 |     const update = await fetch(`${env.api}/api/notes/${note.id}`, { method: 'PATCH', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ revision: note.revision, document_json: content }) });
  301 |     expect(update.ok).toBe(true);
  302 |     const before = await getJson(`${env.api}/api/notes/${note.id}`);
  303 |     await page.setViewportSize({ width: 1618, height: 889 });
  304 |     await page.goto(env.url); await saved(page);
  305 |     const editor = page.getByRole('textbox', { name: 'Note content', exact: true });
  306 |     const instance = await editor.elementHandle();
  307 |     const appearance = page.getByRole('combobox', { name: 'Appearance', exact: true });
  308 |     await appearance.selectOption('cyrnava');
  309 |     await expect(page.locator('html')).toHaveAttribute('data-cyrnava-theme', 'true');
  310 |     await expect(page.locator('.bn-container')).toHaveAttribute('data-color-scheme', 'dark');
  311 |     await expect.poll(() => editor.locator('img').evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth === 600)).toBe(true);
  312 |     await readable(editor.locator('p').first()); await readable(page.locator('.editor-help'));
  313 |     await readable(page.locator('.save-state')); await readable(page.locator('#note-title'));
  314 |     await readable(page.getByRole('treeitem', { name: 'Note Brains', exact: true }));
  315 |     for (const button of await page.getByRole('button').all()) {
  316 |       if (await button.isVisible() && await button.isEnabled()) await readable(button);
  317 |     }
  318 |     expect(await editor.locator('img').evaluate((image) => getComputedStyle(image).filter)).toBe('none');
  319 |     await page.screenshot({ path: info.outputPath('cyrnava-reference-viewport.png'), fullPage: false, animations: 'disabled' });
  320 |     await page.setViewportSize({ width: 1680, height: 936 });
  321 |     await page.screenshot({ path: info.outputPath('cyrnava-1680x936.png'), fullPage: false });
  322 |     for (const mode of ['light', 'dark', 'auto', 'cyrnava']) {
  323 |       await appearance.selectOption(mode);
  324 |       expect(await instance!.evaluate((node) => node.isConnected)).toBe(true);
  325 |     }
  326 |     expect(await getJson(`${env.api}/api/notes/${note.id}`)).toEqual(before);
  327 |     await page.reload(); await saved(page); await expect(appearance).toHaveValue('cyrnava');
  328 |     await expect(page.locator('.bn-container')).toHaveAttribute('data-color-scheme', 'dark');
```