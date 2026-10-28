# FF-006 / FF-018 engineering report

Review candidate · 2026-10-28 · ENGAGE v0.1.0

## A. Implementation summary

Implemented only the approved navigation-collapse and note-template features. ENGAGE remains the application name; the directive's ASTRA heading was not treated as a rename request.

**FF-006:** Hide/Show navigation is always above the editor, supports keyboard activation, exposes `aria-controls`/`aria-expanded`, and persists its boolean preference in browser localStorage. The complete sidebar disappears from layout without unmounting the note or tree. Selection, native editor state, uploads and autosave keep their existing lifetimes. The editor gains the released width. No API operation is tied to toggling the preference.

**FF-018:** New note defaults to blank and optionally uses one of five built-ins or a custom template. All requested starter sections are present. Templates use the existing native BlockNote format; command sections have empty code blocks. Save as template drains pending uploads/saves, captures the exact acknowledged source revision and independently snapshots referenced images. Manage templates supports custom rename/delete, explicit deletion confirmation and protected built-ins. New notes have fresh note, block and image IDs. Source notes, templates and generated notes remain independent.

Custom data stays in the existing external SQLite profile. Schema 4 adds two tables; existing notes/folders/assets are not rewritten. Backups include and validate templates. No package, dependency version, editor contract, account, external runtime service or additional database was introduced.

Both features are implemented and tested, ready for human acceptance review. The installed everyday desktop application and real profile were not upgraded or changed. No commit, push, tag or publication was performed.

### Initial assessment and implementation order

Before editing, inspected the actual React/TypeScript/Vite frontend, BlockNote adapter, FastAPI/Pydantic routes, SQLite schema 3, image ownership and backup mechanisms. `App`/`DirectoryTree`/CSS controlled navigation; `ManagementDialog`/`App.submit` controlled creation; `PersistentNote`/`useAutosave` controlled save ordering. BlockNote APIs were already isolated in `KnowledgeEditor`. Existing tools were Vitest/Testing Library, Playwright, pytest and Ruff.

The main design constraint was note-owned images: retaining a source note's asset URL would make a template break when that note was deleted. The assessment proposed additive template tables with independent image snapshots rather than changing note ownership. This was communicated before implementation. FF-006 was implemented and its 23 App tests passed before FF-018 work began. Template tests and the combined browser workflow followed.

## B. Modified file tree

`+` means created; `~` means modified. Only files below changed.

```text
cyber-workspace/
├── ~ README.md
├── ~ BACKUP_RESTORE.md
├── + FEATURES_FF006_FF018_REPORT.md
├── docs/
│   └── ~ architecture.md
├── backend/
│   ├── app/
│   │   ├── ~ backup.py
│   │   ├── ~ database.py
│   │   ├── ~ main.py
│   │   ├── ~ models.py
│   │   └── + templates.py
│   └── tests/
│       ├── ~ test_assets.py
│       ├── ~ test_document_compatibility.py
│       ├── ~ test_health.py
│       ├── ~ test_library.py
│       ├── ~ test_notes.py
│       └── + test_templates.py
└── frontend/
    ├── e2e/
    │   └── ~ workspace.spec.ts
    └── src/
        ├── ~ App.tsx
        ├── ~ App.test.tsx
        ├── ~ notes.ts
        ├── ~ styles.css
        ├── + templates.ts
        ├── + templates.test.ts
        ├── components/
        │   ├── ~ ManagementDialog.tsx
        │   ├── ~ PersistentNote.tsx
        │   ├── + TemplateManager.tsx
        │   └── + TemplateManager.test.tsx
        └── hooks/
            └── ~ useAutosave.ts
```

### Responsibilities and dependencies

| File | Responsibility, dependencies and reason for change |
| --- | --- |
| `README.md` | User instructions for collapse, blank/template creation, capture, management, limits and upgrade. Links architecture/backup/report. |
| `BACKUP_RESTORE.md` | Explains supported schemas 3/4, template snapshot validation, restore checks and rollback via retained backup. Depends on the existing offline CLI. |
| `FEATURES_FF006_FF018_REPORT.md` | This assessment, changed-file inventory, concrete flows, test evidence and review limitations. |
| `docs/architecture.md` | Records actual UI/API/persistence boundaries and additive schema 4 design. |
| `backend/app/database.py` | Adds template tables atomically using existing SQLite connection/initialization logic; future schema guard becomes version 4. |
| `backend/app/templates.py` | Built-ins and custom capture/list/rename/delete/instantiate. Depends on existing Database transactions, document validation, AssetStore and raster validation, plus Python standard library. Owns snapshot independence and cleanup. |
| `backend/app/models.py` | Pydantic request/response models; reuses Title validation, strict revisions and UUID validation. Rejects unknown request fields. |
| `backend/app/main.py` | Wires TemplateStore during lifespan and exposes five template routes with explicit error responses. Depends on models/service; contains no template SQL. |
| `backend/app/backup.py` | Accepts schemas 3/4 and invokes template validation before copying/restore. Maps damaged snapshot images to an ordinary backup error. Existing manifest/copy/lock logic is reused. |
| `backend/tests/test_templates.py` | Isolated API/storage/migration/backup/image tests using existing pytest, TestClient, Pillow and temporary SQLite fixtures. |
| `backend/tests/test_assets.py` | Updates synthetic schema-2 migration fixture to exclude newer template tables; asserts current schema 4. |
| `backend/tests/test_document_compatibility.py` | Updates current-schema assertion to 4; document format remains version 1. |
| `backend/tests/test_health.py` | Updates the intentional API-surface assertion with the five template routes. |
| `backend/tests/test_library.py` | Updates migration target assertion to 4 while retaining original-source preservation checks. |
| `backend/tests/test_notes.py` | Updates current schema to 4 and unsupported-future-schema fixture to 5. |
| `frontend/src/App.tsx` | React state, navigation preference, toolbar and template workflow coordination. Reuses `perform` save/upload drain, existing selection and creation flow, HTTP clients and dialogs. |
| `frontend/src/styles.css` | Hidden sidebar/one-column layout, wrapping toolbar and template select spacing. Reuses existing responsive layout and button/dialog styling. |
| `frontend/src/templates.ts` | Application-owned template summary and HTTP capture/list/rename/delete calls using existing `http.request`, cancellation and errors. |
| `frontend/src/notes.ts` | Adds template instantiation through the existing validated Note-response client. |
| `frontend/src/components/ManagementDialog.tsx` | Optional template selection for New note, blank default, listing retry/failure feedback and capture naming. Depends on template summaries/client, not BlockNote internals. |
| `frontend/src/components/TemplateManager.tsx` | Small native modal for listing and custom rename/delete; focus restore, request errors, refresh and protected built-in display. Depends on React and template client. |
| `frontend/src/components/PersistentNote.tsx` | Exposes confirmed revision alongside flush through the small NoteHandle interface. Continues to own adapter/autosave integration and recovery. |
| `frontend/src/hooks/useAutosave.ts` | Exposes a stable getter for its already-existing acknowledged revision ref. The serialized autosave algorithm is unchanged. |
| `frontend/src/App.test.tsx` | Adds two collapse tests and three template orchestration/failure tests using existing mocked adapter/API and Testing Library. |
| `frontend/src/templates.test.ts` | Tests HTTP methods, payloads, revision values, URL encoding and API failures using existing Vitest mocks. |
| `frontend/src/components/TemplateManager.test.tsx` | Tests built-in protection, rename/delete/cancel, revision use and visible failure/refresh using existing Testing Library. |
| `frontend/e2e/workspace.spec.ts` | Adds one combined real-editor feature journey to the existing temporary-profile Playwright harness. Existing browser journeys remain intact. |

`DirectoryTree`, `KnowledgeEditor`, `AssetStore`, dependency manifests and lockfiles did not need changes.

## C. Architecture walkthrough

### Collapse navigation

1. The user activates **Hide navigation** in `App.tsx`, including by keyboard Enter.
2. Its handler updates `navigationCollapsed` and attempts `localStorage.setItem('engage.navigation-collapsed.v1', 'true')`. Storage failure is caught; the current page remains usable.
3. React applies `hidden` to `aside#workspace-navigation` and `data-navigation-collapsed="true"` to the workspace.
4. `styles.css` removes the sidebar from layout and changes the grid to one flexible column. The toolbar stays in main content, outside the hidden panel.
5. `PersistentNote` retains its key and the same mounted BlockNote adapter. There is no note request, flush or save triggered by this action. Any already-pending autosave proceeds on its own schedule.
6. On reload, the lazy state initializer reads the preference. Show navigation reverses the boolean/layout without changing selection.

### Create an Enumeration note

1. `App.newItem` uses `perform` to drain existing uploads/saves and opens `ManagementDialog` with the currently selected folder.
2. `ManagementDialog` calls `templates.getTemplates` to list summaries. Blank remains selected until the user chooses Enumeration Notes.
3. Form submission passes that summary to `App.submit`. It calls `notes.createNoteFromTemplate('builtin:enumeration', 1, title, folderId)`.
4. The existing HTTP client sends `POST /api/templates/builtin%3Aenumeration/notes` with title, destination and expected template revision.
5. FastAPI `instantiate_template` validates `InstantiateTemplate` and delegates to `TemplateStore.instantiate`.
6. The store starts `BEGIN IMMEDIATE`, loads `builtin_templates`, checks revision/destination, validates native JSON and assigns fresh note/block UUIDs. A custom template follows the same path, also loading snapshots and assigning new asset UUIDs/files/URLs.
7. Parameterized inserts create the ordinary note and any owned asset metadata. Files are durably written before the SQLite transaction commits. Failure rolls back SQL and cleans up generated files.
8. The API returns the new ordinary Note. The existing client checks its document/metadata. `App` remembers/selects it and refreshes library summaries.
9. `PersistentNote` passes saved `document_json` into `KnowledgeEditor`. The adapter initializes BlockNote with headings, paragraphs and code sections. Subsequent editing uses the existing 700 ms debounced, serialized `useAutosave` PATCH flow with note revision checks.

### Capture and reopen a custom template

Save as template calls `App.perform`, which waits for `NoteHandle.flush` to finish uploads and save current edits. `NoteHandle.getRevision` then returns the latest server-acknowledged revision, not a stale React prop. The naming dialog submits `templates.captureTemplate` with source ID/revision/name. FastAPI `capture_template` delegates to `TemplateStore.capture`, which locks the write transaction, rejects a changed/missing source, validates native document/image ownership and inserts an independent template plus referenced image bytes. Capturing itself does not modify the source note or its revision.

If another tab changes the source between flush and capture, HTTP 409 leaves the dialog/name intact. It does not silently capture a newer unseen version. Reopen/resolve the source before trying again.

After application restart, listing queries the same external SQLite database. Choosing the custom entry calls the same instantiation endpoint and produces a new independent ordinary note. Reloading that note uses the unchanged `App` → `notes.getNote` → FastAPI `get_note` → `Database.get` → `PersistentNote` → `KnowledgeEditor` path; image URLs resolve to that new note's own assets. The template and source are not needed to render it.

### API surface added

| Method and route | Purpose |
| --- | --- |
| `GET /api/templates` | Built-in/custom summaries; private document/image bytes are not included. |
| `POST /api/templates` | Capture a saved source revision as a custom template. |
| `PATCH /api/templates/{id}` | Rename custom template with expected revision. |
| `DELETE /api/templates/{id}` | Delete custom template with expected revision. |
| `POST /api/templates/{id}/notes` | Instantiate an independent ordinary note into the chosen folder. |

These are the minimum operations used by the UI. There is no additional document-download, image-serving or template-editing endpoint. Protected built-ins return 403, missing sources/templates 404, stale revisions 409, invalid input/relationships/images 422, and SQLite write failures use the existing 503 handling.

## D. Testing report

All application/browser tests used synthetic data and isolated temporary profiles outside Git. No automated test targeted real notes or the everyday backend. Existing dependency versions were used. Browser journeys abort and record unexpected non-loopback requests; none occurred in the new workflow.

| Executed verification | Outcome |
| --- | --- |
| FF-006 App tests before template implementation | 23 passed. |
| Focused backend templates/notes/assets/backup/health suite | 96 passed before the extra migration rollback test. |
| Focused frontend App/template client/manager/PersistentNote tests | 34 passed. |
| Full backend `python -m pytest -q` | **212 passed**, one existing Starlette/httpx deprecation warning. Includes 22 new template cases. |
| Full frontend `vitest run` | **189 passed across 17 files**, including 11 new feature tests. |
| TypeScript `tsc --noEmit` | Passed after correcting test query options. |
| ESLint, zero warnings permitted | Passed. |
| Ruff check and format check, backend + desktop | Passed; 27 files formatted. |
| Production Vite build | Passed; existing large-bundle warning remains. |
| Full Chromium release Playwright suite | **7 passed**, including both lifecycle tests and all existing workspace journeys. |
| New feature journey in Firefox | **1 passed**. |
| New feature journey using Vite development mode in Chromium | **1 passed**; loopback proxy and development entrypoint verified. |
| Desktop and 390-pixel screenshots | Visually inspected; controls wrap, no toolbar/content overlap or horizontal page overflow. |

The combined journey performs the directive's sequence: open → collapse → expand → create Enumeration note in a folder → enter technical text and bold formatting → insert synthetic screenshot through the upload UI → wait for Saved → stop/restart backend and reload → verify formatting/image/document → capture custom template → create two copies → edit source/copy independently. It also checks blank creation, unchanged source after capture/copy, fresh block/image IDs, custom rename/delete, built-in protection, keyboard activation, DOM/editor survival, preference reload, and responsive width.

Backend tests additionally exercise all five built-ins, nested native structure, restart/reconnection, malformed input, source/template conflicts, missing sources/templates, source/template/other-note deletion without broken images, rollback of partial image instantiation, missing source images, aggregate image cap, schema-3 migration idempotence/raw-row preservation, failed migration rollback, schema-3 backup compatibility, restored template images after source deletion, and damaged-snapshot backup refusal.

### Failures encountered and corrections

- New Testing Library tests initially used Playwright's `exact` option in role queries. Vitest ran them, but TypeScript correctly rejected the unsupported option. Removed it; string names already provide exact role-name matching. Type checking and lint then passed.
- Ruff requested formatting of the added migration-failure assertion. Applied its formatter; checks passed.
- During review, found that damaged template image validation needed the same concise `BackupError` mapping as ordinary images. Added the mapping and updated the corruption test; the final full backend suite passed.
- Visual review found that an old “Template saved” notice could remain after later management actions. `perform` now clears previous notices. All 26 App tests, type/lint checks and the final build were checked again after this small UI correction; the development-mode Chromium and release-mode Firefox feature journeys were also rerun.

No application/browser assertion failed in the new combined journey. No test was made green by disabling image ownership, stale-revision checks, validation, browser security or existing acceptance assertions.

### Testing limits

The workflow was browser-automated against real BlockNote/FastAPI/SQLite, not manually typed through the installed desktop launcher. Human acceptance with the owner's usual browser/profile remains pending. The full seven-journey release suite was run in Chromium; only the new feature journey was run in Firefox. Other browsers, assistive technologies and a fresh Ubuntu installation were not tested. Existing synthetic storage-failure tests do not simulate power loss or every filesystem/disk-full failure.

Reproduce with the existing environments, from `backend/`:

```bash
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check . ../desktop
.venv/bin/python -m ruff format --check . ../desktop
```

From `frontend/`:

```bash
npm run lint
npm test
npm run build
npm run test:release
ENGAGE_E2E_RELEASE=1 npx playwright test e2e/workspace.spec.ts --grep 'navigation preference' --browser=firefox
```

This session used the pinned Node binary directly and set `TMPDIR` to an approved task work directory because the tool sandbox disallows writing normal temporary paths. No sandbox weakening or browser download was needed. That environment adjustment is not required in an ordinary terminal.

## E. Design decisions

| Decision | Reason, simpler alternatives and accepted tradeoff |
| --- | --- |
| LocalStorage for collapse, CSS grid for layout | This is a browser preference, not note data. A database preference or resizable panel adds unnecessary state/API work. Preference is origin/profile-specific and excluded from backup. Storage failure only loses persistence of the preference. |
| Keep sidebar and editor mounted | Conditional unmounting was shorter but risks resetting tree/editor state. `hidden` removes navigation from layout/accessibility while preserving component lifetimes. |
| Blank-first existing creation dialog | Avoids changing routine blank-note behavior. A separate template gallery would create extra navigation and complexity. API/list failure still permits blank creation. |
| Built-ins in Python data | Deterministic, protected and no duplicate rows/seeding. Native JSON is assembled on demand. Changing built-ins later should advance their revision when semantics change. Existing generated notes stay unchanged. |
| Custom definitions in two additive SQLite tables | Reuses the established migration/transaction/backup boundary. A JSON file store would add a second persistence/backup mechanism; using ordinary notes as templates would blur ownership/navigation. No original table needs rebuilding. |
| Independent template image BLOBs | Reusing source URLs breaks deletion independence; retaining hidden source notes complicates the model. BLOB snapshots reuse the exact database backup path without adding a second asset tree or altering existing note ownership. Cost: larger SQLite/backup files and bounded image-copy/decode time. |
| Exact bytes for already-normalized snapshots | Reuses existing raster validation but discards its normalized return value during copies. Re-encoding JPEG again would unnecessarily change bytes/quality. Ordinary uploads still normalize first. |
| Fresh block/image IDs on instantiation | Separates all generated documents while preserving native structure/styles. Notes become ordinary independent documents, with no inheritance/update propagation. |
| Flush plus expected confirmed revision | A fresh GET after flush could capture another tab's unseen newer content. Exposing the acknowledged revision and checking it in the capture transaction makes that race an explicit 409. Note autosave ordering remains unchanged. |
| Revision checks for custom rename/delete/instantiate | A stale dialog cannot silently overwrite/delete a changed template or select an obsolete name/revision. Refresh/reopen is sufficient recovery for this scope. No automatic merge/version history. |
| 50 MiB aggregate snapshot cap | Bounds per-template reads and synchronous validation. Existing 10 MiB/image, pixel/decode and 1 MiB/native-document limits remain. Large evidence collections should stay ordinary notes; configurable caps/storage redesign are deferred. |
| Preserve backup format 1; accept schema 3/4 | Full SQLite copy already contains snapshots. Read-only validation extends to templates; old backups remain usable. No archive layout/manifest migration or downgrade framework was introduced. |

### Schema and upgrade behavior

`templates`: `id`, `name`, `document_json`, `format_version`, `revision`, `created_at`, `updated_at`.

`template_images`: `template_id` foreign key with delete cascade, `asset_id` snapshot key, `mime_type`, `data` BLOB; composite primary key. Snapshot keys are not foreign keys to source assets, intentionally allowing the source to be deleted.

The existing `Database.initialize` transaction creates both tables and advances `PRAGMA user_version` to 4 only if all DDL succeeds. Failed migration rolls back. Existing rows retain their raw field values, relationships, revisions and timestamps. Re-running initialization is idempotent. Data location remains absolute `$XDG_DATA_HOME/engage/`, otherwise `~/.local/share/engage/`; private file permissions and existing profile locks remain in use.

Before deploying to the everyday profile: stop ENGAGE, take and retain a validated schema-3 backup, then review/rebuild/reinstall using the existing desktop instructions. Starting the new backend performs the additive migration. Older code rejects schema 4; restore the retained schema-3 backup into a new profile if reverting. No in-place downgrade is supplied. The implementation did not perform these live-profile steps.

## F. Remaining risks and human review

No known defect blocks feature review based on the executed checks. Acceptance remains the owner's decision.

- Custom templates copy private note contents and images. They are unencrypted local data, also included in unencrypted backups. Built-ins contain only empty scaffolding. No note content is executed and no external runtime request is introduced.
- Template deletion removes the active definition/snapshots, not generated notes or earlier backups. SQLite file space reclamation and forensic erasure are not implemented; deleting a template is not a secure-erasure guarantee.
- Copies consume independent storage. Snapshot validation/instantiation holds a SQLite write transaction during image work; very large copies may briefly serialize other writes. The cap bounds per-template reads, not total database size or decoded-image memory beyond existing image limits.
- SQLite and ordinary note image files remain separate resources. Handled failures clean up; process crashes can leave generated orphan files for existing startup reconciliation. Power-loss durability and advanced recovery remain outside these features.
- A timed-out create/capture may have committed before its response was lost. As with existing note creation, retry can create a duplicate; inspect the library/manager first. Idempotency keys and duplicate prevention were not added.
- Custom templates support capture, rename and delete, not in-place content editing, export/import, ordering, inheritance or a preview editor. Capture a new template from an edited note when needed. Names may duplicate.
- Changes in another tab can invalidate a selected template/source revision. Errors stay visible; refresh templates or reopen/resolve the note before retrying. There is no automatic cross-tab template refresh.
- Preference persistence depends on browser storage and origin. It does not synchronize with another browser or return through a workspace backup.
- Full accessibility certification, other browsers, real-user desktop upgrade and real-profile restore remain unverified. Existing bundle-size and Starlette/httpx warnings were not addressed by unrelated dependency changes. Original-code licensing remains pending as previously requested.

## G. Git commit recommendations

No Git mutation was performed. The changes share App/CSS/test files, so splitting commits requires reviewing/staging the relevant hunks.

1. `feat(ui): preserve editor state while toggling workspace navigation`
   - Navigation preference, accessible persistent toggle, responsive grid and state-preservation tests.
2. `feat(templates): add native pentesting templates with independent image snapshots`
   - Built-ins/custom capture/management, schema 4, API/client/UI integration, image independence, backup compatibility, tests and documentation.

Review the diff, backup/migration tradeoff and owner acceptance workflow before committing or updating the installed app. Work stops at FF-006 and FF-018.
