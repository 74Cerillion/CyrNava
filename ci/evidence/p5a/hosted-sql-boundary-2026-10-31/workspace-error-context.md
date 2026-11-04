# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: workspace.spec.ts >> Phase 1 formatting, clipboard, CRUD, keyboard access and sanitized documentation
- Location: e2e/workspace.spec.ts:604:1

# Error details

```
TimeoutError: page.waitForEvent: Timeout 10000ms exceeded while waiting for event "filechooser"
=========================== logs ===========================
waiting for event "filechooser"
============================================================
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
      - combobox "Search all notes" [ref=e14]
      - paragraph [ref=e15]: Search saved notes. ↑ ↓ select; Enter opens; Esc clears.
    - button "Workspace root" [ref=e16] [cursor=pointer]
    - generic [ref=e19]:
      - button "New folder" [ref=e20] [cursor=pointer]
      - button "New note" [ref=e23] [cursor=pointer]
    - tree "Library" [ref=e26]:
      - treeitem "Folder Networking" [expanded] [level=1] [ref=e27] [cursor=pointer]:
        - button "Collapse Networking" [ref=e28]: ▾
        - generic [ref=e29]: Networking
      - treeitem "Folder Protocols" [expanded] [level=2] [ref=e30] [cursor=pointer]:
        - button "Collapse Protocols" [ref=e31]: ▾
        - generic [ref=e32]: Protocols
      - treeitem "Note DNS reference" [level=3] [selected] [ref=e33] [cursor=pointer]:
        - generic [ref=e37]: DNS reference
        - generic [aria-hidden] [ref=e38]: ●
      - treeitem "Note TCP overview" [level=3] [ref=e39] [cursor=pointer]:
        - generic [ref=e43]: TCP overview
    - generic [ref=e44]:
      - button "Rename" [ref=e45] [cursor=pointer]
      - button "Move" [ref=e48] [cursor=pointer]
      - button "Delete" [ref=e51] [cursor=pointer]
      - button "Refresh library" [ref=e54] [cursor=pointer]
    - status [ref=e57]: "Backend at page load: online"
    - paragraph [ref=e58]: Arrow keys navigate. Enter opens notes or toggles folders. F2 renames; Delete asks for confirmation.
    - paragraph [ref=e59]:
      - link "Third-party notices" [ref=e60] [cursor=pointer]:
        - /url: /third-party-notices.txt
  - main [ref=e61]:
    - generic [ref=e62]:
      - generic [ref=e63]:
        - text: Appearance
        - combobox "Appearance" [ref=e64]:
          - option "Light"
          - option "Dark"
          - option "System" [selected]
          - option "CyrNava"
      - button "Hide navigation" [expanded] [ref=e65] [cursor=pointer]
      - button "Manage templates" [ref=e68] [cursor=pointer]
      - button "Save as template" [ref=e71] [cursor=pointer]
    - generic [ref=e74]:
      - generic [ref=e75]: Note title
      - generic [ref=e76]:
        - textbox "Note title" [ref=e77]: DNS reference
        - status [ref=e78]: Saved
      - paragraph [ref=e81]: Your note stays on this computer. Wait for uploads and Saved before closing.
    - region "Note editor" [ref=e82]:
      - paragraph [ref=e83]: Use / for formatting and images. Paste a screenshot with Ctrl+V, or type /image to select a local PNG, JPEG or WebP.
      - textbox "Note content" [active] [ref=e85]:
        - generic [ref=e86]:
          - heading "Network documentation" [level=1] [ref=e90]
          - heading "DNS resolution" [level=2] [ref=e94]
          - heading "Resolver behavior" [level=3] [ref=e98]
          - paragraph [ref=e102]: A resolver translates a synthetic example.test name into a local documentation example.
          - generic [ref=e105]:
            - text: •
            - paragraph [ref=e106]: Ask the configured resolver.
          - generic [ref=e109]:
            - text: •
            - paragraph [ref=e110]: Review the cached response.
          - paragraph [ref=e114]:
            - strong [ref=e115]: Synthetic learning notes only.
          - img "synthetic.png.jpg" [ref=e121] [cursor=pointer]
          - img "image.png" [ref=e129] [cursor=pointer]
          - code [ref=e134]: "dig example.test # Example syntax; CyrNava does not execute commands. /image"
```

# Test source

```ts
  556 |     const beforeBytes = await readFile(assetPath);
  557 |     await env.shutdown();
  558 |     const originalDb = await readFile(join(env.profile(), 'engage.sqlite3'));
  559 |     expect(env.cli(['backup', '--data-dir', env.profile(), '--destination', join(env.directory, 'backup')])).toContain('completed and validated');
  560 |     const restoredData = join(env.directory, 'restored-data'); await mkdir(restoredData);
  561 |     expect(env.cli(['restore', '--source', join(env.directory, 'backup'), '--data-dir', join(restoredData, 'engage')])).toContain('completed and validated');
  562 |     env.restoreTo(restoredData); await env.start(); await page.reload(); await saved(page);
  563 |     expect(await getJson(`${env.api}/api/tree`)).toEqual(beforeTree);
  564 |     expect(await getJson(`${env.api}/api/notes/${owner.id}`)).toEqual(beforeNote);
  565 |     expect(await readFile(join(env.profile(), 'assets', assetId))).toEqual(beforeBytes);
  566 |     await expect(editor().getByRole('heading', { name: 'Recovery evidence', exact: true })).toBeVisible();
  567 |     await expect(editor()).toContainText('Paragraph B.');
  568 |     await expect.poll(() => editor().locator('img').evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth === 600)).toBe(true);
  569 |     await page.screenshot({ path: info.outputPath('restored-workspace.png'), fullPage: true });
  570 |     expect(await readFile(join(env.directory, 'original-data/engage/engage.sqlite3'))).toEqual(originalDb);
  571 |     expect(external).toEqual([]);
  572 |     await writeFile(info.outputPath('restoration-evidence.json'), JSON.stringify({ restored_tree: beforeTree, restored_note: beforeNote, image_bytes: beforeBytes.length, external_requests: external }, null, 2));
  573 |   } finally {
  574 |     await env.shutdown();
  575 |     await writeFile(info.outputPath('local-server.log'), env.logs());
  576 |     await rm(env.directory, { recursive: true, force: true });
  577 |   }
  578 | });
  579 | 
  580 | test('revision conflict retains the draft and exports both versions before explicit reload', async ({ page }, info) => {
  581 |   const env = await environment();
  582 |   try {
  583 |     await env.start(); await page.goto(env.url); await create(page, 'note', 'Conflict note');
  584 |     const tree = await getJson(`${env.api}/api/tree`); const owner = tree.notes[0];
  585 |     const persisted = await getJson(`${env.api}/api/notes/${owner.id}`);
  586 |     const response = await fetch(`${env.api}/api/notes/${owner.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ revision: persisted.revision, title: 'Other saved version' }) });
  587 |     expect(response.status).toBe(200);
  588 |     await page.getByRole('textbox', { name: 'Note title', exact: true }).fill('My unsaved title');
  589 |     await expect(page.getByText('Save Error', { exact: true })).toBeVisible();
  590 |     await page.getByRole('button', { name: 'Review conflict and recover', exact: true }).click();
  591 |     const dialog = page.getByRole('dialog'); await expect(dialog).toContainText('Other saved version');
  592 |     await expect(dialog.getByRole('button', { name: 'Reopen saved version', exact: true })).toBeDisabled();
  593 |     const download = page.waitForEvent('download'); await dialog.getByRole('button', { name: 'Download both versions', exact: true }).click();
  594 |     const file = await download; const destination = info.outputPath('conflict-recovery.json'); await file.saveAs(destination);
  595 |     const bundle = JSON.parse(await readFile(destination, 'utf8'));
  596 |     expect(bundle.local_draft.title).toBe('My unsaved title'); expect(bundle.saved_note.title).toBe('Other saved version');
  597 |     await dialog.getByRole('checkbox').check(); await dialog.getByRole('button', { name: 'Reopen saved version', exact: true }).click();
  598 |     await expect(page.getByRole('textbox', { name: 'Note title', exact: true })).toHaveValue('Other saved version');
  599 |     await page.getByRole('textbox', { name: 'Note title', exact: true }).fill('Editing after recovery'); await saved(page);
  600 |     expect((await getJson(`${env.api}/api/notes/${owner.id}`)).title).toBe('Editing after recovery');
  601 |   } finally { await env.shutdown(); await writeFile(info.outputPath('local-server.log'), env.logs()); await rm(env.directory, { recursive: true, force: true }); }
  602 | });
  603 | 
  604 | test('Phase 1 formatting, clipboard, CRUD, keyboard access and sanitized documentation', async ({ page }, info) => {
  605 |   const env = await environment();
  606 |   const external: string[] = [];
  607 |   await page.route('**/*', (route) => {
  608 |     if (new URL(route.request().url()).hostname !== '127.0.0.1') { external.push(route.request().url()); return route.abort(); }
  609 |     return route.continue();
  610 |   });
  611 |   const editor = () => page.getByRole('region', { name: 'Note editor' }).getByRole('textbox');
  612 |   try {
  613 |     await env.start(); await page.goto(env.url);
  614 |     await create(page, 'folder', 'Networking'); await create(page, 'folder', 'Protocols');
  615 |     await create(page, 'note', 'DNS reference');
  616 |     await editor().click();
  617 |     for (const [prefix, text] of [['# ', 'Network documentation'], ['## ', 'DNS resolution'], ['### ', 'Resolver behavior']]) {
  618 |       await page.keyboard.type(prefix); await page.keyboard.type(text); await page.keyboard.press('Enter');
  619 |     }
  620 |     await page.keyboard.type('A resolver translates a synthetic example.test name into a local documentation example.'); await page.keyboard.press('Enter');
  621 |     await page.keyboard.type('- '); await page.keyboard.type('Ask the configured resolver.'); await page.keyboard.press('Enter');
  622 |     await page.keyboard.type('Review the cached response.'); await page.keyboard.press('Enter'); await page.keyboard.press('Enter');
  623 |     await page.keyboard.press('Control+b'); await page.keyboard.type('Synthetic learning notes only.'); await page.keyboard.press('Control+b'); await page.keyboard.press('Enter');
  624 |     await page.keyboard.type('``` '); await page.keyboard.type('dig example.test'); await page.keyboard.press('Enter'); await page.keyboard.type('# Example syntax; CyrNava does not execute commands.');
  625 |     await saved(page);
  626 |     let tree = await getJson(`${env.api}/api/tree`);
  627 |     const owner = tree.notes.find((note: Summary) => note.title === 'DNS reference');
  628 |     const protocols = tree.folders.find((folder: { name: string }) => folder.name === 'Protocols');
  629 |     const networking = tree.folders.find((folder: { name: string }) => folder.name === 'Networking');
  630 |     const rich = await getJson(`${env.api}/api/notes/${owner.id}`);
  631 |     expect(rich.document_json.filter((b: { type: string }) => b.type === 'heading').map((b: { props: { level: number } }) => b.props.level)).toEqual([1, 2, 3]);
  632 |     expect(rich.document_json.some((b: { type: string }) => b.type === 'codeBlock')).toBe(true);
  633 |     expect(rich.document_json.some((b: { type: string }) => b.type === 'bulletListItem')).toBe(true);
  634 |     expect(JSON.stringify(rich.document_json)).toContain('"bold":true');
  635 |     await create(page, 'note', 'TCP overview');
  636 |     await editor().click(); await page.keyboard.type('TCP provides ordered, reliable byte streams between endpoints.'); await saved(page);
  637 |     await page.getByRole('treeitem', { name: 'Note DNS reference', exact: true }).click(); await saved(page);
  638 |     await expect(editor().getByRole('heading', { name: 'Network documentation', exact: true })).toBeVisible();
  639 |     await page.screenshot({ path: info.outputPath('01-workspace.png'), fullPage: true });
  640 |     await page.getByRole('complementary').screenshot({ path: info.outputPath('02-hierarchy.png') });
  641 |     await page.getByRole('main').screenshot({ path: info.outputPath('03-rich-text.png') });
  642 | 
  643 |     const png = join(env.directory, 'synthetic.png');
  644 |     execFileSync(python, ['-c', "from PIL import Image,ImageDraw; import sys; im=Image.new('RGB',(600,140),'#20324a'); ImageDraw.Draw(im).text((20,45),'SYNTHETIC DNS DIAGRAM - example.test',fill='white',font_size=23); [im.save(sys.argv[1]+ext,format=fmt) for ext,fmt in [('.png','PNG'),('.jpg','JPEG'),('.webp','WEBP')]]", png]);
  645 |     await page.context().grantPermissions(['clipboard-read', 'clipboard-write'], { origin: env.url });
  646 |     await page.evaluate(async (data) => {
  647 |       const bytes = Uint8Array.from(atob(data), (character) => character.charCodeAt(0));
  648 |       await navigator.clipboard.write([new ClipboardItem({ 'image/png': new Blob([bytes], { type: 'image/png' }) })]);
  649 |     }, (await readFile(`${png}.png`)).toString('base64'));
  650 |     await editor().getByText('Synthetic learning notes only.', { exact: true }).click(); await page.keyboard.press('End'); await page.keyboard.press('Control+v');
  651 |     await expect(editor().locator('img')).toHaveCount(1); await saved(page);
  652 |     // Reuse the empty trailing paragraph for the installed native image selector.
  653 |     for (const extension of ['jpg', 'webp']) {
  654 |       await editor().getByText('Synthetic learning notes only.', { exact: true }).click(); await page.keyboard.press('End'); await page.keyboard.press('Enter');
  655 |       await page.keyboard.type('/image'); await page.keyboard.press('Enter');
> 656 |       const [chooser] = await Promise.all([page.waitForEvent('filechooser', { timeout: 10_000 }), page.getByRole('button', { name: 'Upload image', exact: true }).click({ timeout: 10_000 })]);
      |                                                 ^ TimeoutError: page.waitForEvent: Timeout 10000ms exceeded while waiting for event "filechooser"
  657 |       await chooser.setFiles(`${png}.${extension}`); await page.keyboard.press('Escape'); await saved(page);
  658 |     }
  659 |     await expect(editor().locator('img')).toHaveCount(3);
  660 |     const imageNote = await getJson(`${env.api}/api/notes/${owner.id}`);
  661 |     expect(imageNote.document_json.filter((b: { type: string }) => b.type === 'image')).toHaveLength(3);
  662 |     await env.stopBackend(); await env.startBackend(); await page.reload(); await saved(page);
  663 |     expect((await getJson(`${env.api}/api/notes/${owner.id}`)).document_json).toEqual(imageNote.document_json);
  664 |     await expect.poll(() => editor().locator('img').evaluateAll((images) => images.every((image) => (image as HTMLImageElement).complete && (image as HTMLImageElement).naturalWidth === 600))).toBe(true);
  665 |     await editor().locator('img').first().scrollIntoViewIfNeeded();
  666 |     await page.screenshot({ path: info.outputPath('04-images.png'), fullPage: true });
  667 | 
  668 |     // Move note to root and back; its native content is unchanged.
  669 |     for (const destination of ['', protocols.id]) {
  670 |       await page.getByRole('button', { name: 'Move', exact: true }).click();
  671 |       await page.getByRole('dialog').getByLabel('Destination folder').selectOption(destination);
  672 |       await page.getByRole('dialog').getByRole('button', { name: 'Apply', exact: true }).click();
  673 |       await expect(page.getByRole('dialog')).toBeHidden();
  674 |     }
  675 |     expect((await getJson(`${env.api}/api/notes/${owner.id}`)).document_json).toEqual(imageNote.document_json);
  676 |     // Folder movement is the same existing dialog, verified with descendants.
  677 |     await page.getByRole('treeitem', { name: 'Folder Protocols', exact: true }).click();
  678 |     for (const destination of ['', networking.id]) {
  679 |       await page.getByRole('button', { name: 'Move', exact: true }).click();
  680 |       await page.getByRole('dialog').getByLabel('Destination folder').selectOption(destination);
  681 |       await page.getByRole('dialog').getByRole('button', { name: 'Apply', exact: true }).click(); await expect(page.getByRole('dialog')).toBeHidden();
  682 |     }
  683 |     const folder = page.getByRole('treeitem', { name: 'Folder Protocols', exact: true });
  684 |     await folder.focus(); await page.keyboard.press('F2'); await expect(page.getByRole('dialog')).toBeVisible();
  685 |     await page.keyboard.press('Escape'); await expect(page.getByRole('dialog')).toBeHidden(); await expect(folder).toBeFocused();
  686 |     await page.keyboard.press('ArrowLeft'); await expect(folder).toHaveAttribute('aria-expanded', 'false');
  687 |     await page.keyboard.press('ArrowRight'); await page.keyboard.press('ArrowRight');
  688 |     const noteRow = page.getByRole('treeitem', { name: 'Note DNS reference', exact: true }); await expect(noteRow).toBeFocused();
  689 |     await page.keyboard.press('Enter'); await expect(page.getByRole('textbox', { name: 'Note title', exact: true })).toHaveValue('DNS reference');
  690 |     await noteRow.focus(); await page.keyboard.press('Delete'); await expect(page.getByRole('dialog')).toContainText('cannot be undone');
  691 |     await page.keyboard.press('Escape'); await expect(page.getByRole('dialog')).toBeHidden(); await expect(noteRow).toBeFocused();
  692 |     await editor().locator('p').first().click(); await page.keyboard.press('ArrowLeft'); await page.keyboard.press('ArrowRight');
  693 |     await expect(editor()).toBeFocused(); await expect(page.getByRole('dialog')).toBeHidden();
  694 |     for (const button of await page.getByRole('button').all()) if (await button.isVisible()) await expect(button).toHaveAccessibleName(/\S/);
  695 |     await page.keyboard.press('Tab'); // Native focus remains keyboard operable.
  696 |     await page.setViewportSize({ width: 390, height: 844 });
  697 |     await page.getByRole('textbox', { name: 'Note title', exact: true }).click();
  698 |     const layout = await page.evaluate(() => ({ width: window.innerWidth, scroll: document.documentElement.scrollWidth, overflowing: Array.from(document.querySelectorAll('*')).filter((element) => element.getBoundingClientRect().right > window.innerWidth + 1).slice(0, 12).map((element) => ({ tag: element.tagName, class: element.className, right: element.getBoundingClientRect().right })) }));
  699 |     expect(layout.scroll, JSON.stringify(layout)).toBeLessThanOrEqual(layout.width + 1);
  700 |     await page.setViewportSize({ width: 1280, height: 1000 });
  701 | 
  702 |     await page.getByRole('button', { name: 'Workspace root', exact: true }).click();
  703 |     await create(page, 'folder', 'Disposable fixture'); await create(page, 'note', 'Disposable note');
  704 |     await page.getByRole('treeitem', { name: 'Folder Disposable fixture', exact: true }).click();
  705 |     await page.getByRole('button', { name: 'Delete', exact: true }).click();
  706 |     await expect(page.getByRole('dialog')).toContainText('1 note');
  707 |     await page.getByRole('button', { name: 'Delete permanently', exact: true }).click(); await expect(page.getByRole('dialog')).toBeHidden();
  708 |     tree = await getJson(`${env.api}/api/tree`); expect(tree.notes).toHaveLength(2); expect(tree.folders).toHaveLength(2);
  709 |     expect(external).toEqual([]);
  710 |   } finally { await env.shutdown(); await writeFile(info.outputPath('local-server.log'), env.logs()); await rm(env.directory, { recursive: true, force: true }); }
  711 | });
  712 | 
  713 | 
  714 | test('all exposed editor actions persist; mixed content reconstructs after restart and rapid edits', async ({ page }) => {
  715 |   const env = await environment();
  716 |   const fixture = JSON.parse(await readFile(join(backend, 'tests/fixtures/blocknote_v1.json'), 'utf8'));
  717 |   const external: string[] = [];
  718 |   const rejected: number[] = [];
  719 |   let releaseHeld: (() => void) | undefined;
  720 |   await page.route('**/*', (route) => {
  721 |     if (new URL(route.request().url()).hostname !== '127.0.0.1') {
  722 |       external.push(route.request().url()); return route.abort();
  723 |     }
  724 |     return route.continue();
  725 |   });
  726 |   page.on('response', (response) => {
  727 |     if (response.request().method() === 'PATCH' && response.status() >= 400) rejected.push(response.status());
  728 |   });
  729 |   try {
  730 |     await env.start();
  731 |     const created = await fetch(env.api + '/api/notes', { method: 'POST', headers: { 'content-type': 'application/json' },
  732 |       body: JSON.stringify({ title: 'Compatibility', document_json: fixture.mixed }) });
  733 |     expect(created.status).toBe(201); const note = await created.json();
  734 |     const png = join(env.directory, 'compatibility.png');
  735 |     execFileSync(python, ['-c', 'from PIL import Image;import sys;Image.new("RGB",(32,20),"blue").save(sys.argv[1])', png]);
  736 |     const upload = await fetch(env.api + '/api/assets?note_id=' + note.id, { method: 'POST', headers: { 'content-type': 'image/png' }, body: await readFile(png) });
  737 |     expect(upload.status).toBe(201); const asset = await upload.json();
  738 |     fixture.mixed.find((block: AssetBlock) => block.type === 'image').props.url = asset.url;
  739 |     const initial = await fetch(env.api + '/api/notes/' + note.id, { method: 'PATCH', headers: { 'content-type': 'application/json' },
  740 |       body: JSON.stringify({ revision: 1, document_json: fixture.mixed }) });
  741 |     expect(initial.status).toBe(200);
  742 |     await page.goto(env.url); await saved(page);
  743 |     await page.getByRole('combobox', { name: 'Appearance', exact: true }).selectOption('cyrnava');
  744 |     const editor = page.getByRole('region', { name: 'Note editor' }).getByRole('textbox');
  745 |     for (let level = 1; level <= 6; level++) {
  746 |       await expect(editor.getByRole('heading', { name: 'Heading ' + level, exact: true })).toBeVisible();
  747 |     }
  748 |     for (const button of await editor.locator('.bn-toggle-button').all()) await button.click();
  749 |     await expect(editor.getByText('Nested toggle body 3', { exact: true })).toBeVisible();
  750 |     await expect(editor.getByText('Nested', { exact: true })).toBeVisible();
  751 |     await expect(editor.locator('[data-content-type="codeBlock"]')).toContainText('print("local 🚀")');
  752 |     await expect(editor.locator('strong')).toContainText('All styles');
  753 |     await expect(editor.locator('a[href="https://example.invalid/evidence"]')).toContainText('Reference');
  754 |     await expect.poll(() => editor.locator('img').evaluate((image: HTMLImageElement) => image.complete && image.naturalWidth > 0)).toBe(true);
  755 |     const persisted = async () => (await getJson(env.api + '/api/notes/' + note.id)).document_json;
  756 |     expect(await persisted()).toEqual(fixture.mixed);
```