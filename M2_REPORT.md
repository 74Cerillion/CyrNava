# ENGAGE M2 engineering report

## A. Implementation summary

M2 implements a hierarchical library with root/nested folders, root/folder notes, expand/collapse, mouse and keyboard navigation, and GUI creation, renaming, movement and confirmed permanent deletion. All relationships persist in SQLite. M1's document JSON, revision-protected saves, title editing, error feedback, localhost operation and two-pane layout remain.

The required manual A–U acceptance sequence was executed successfully on an isolated copied M1 database. All 49 backend tests and 52 frontend tests pass, including retained M0/M1 coverage. Detailed commands, observations, failures/corrections and limits are in `M2_VERIFICATION.md`.

Necessary, documented changes to M1:

- SQLite schema version 2 replaces the M1 notes definition because `CHECK(folder_id IS NULL)` cannot simply be removed. Every original note column is copied by name inside a transaction; original IDs, revisions, timestamps and raw JSON text survive unchanged.
- The BlockNote adapter and validator now accept the existing core `codeBlock`. M1 excluded it, while M2's mandatory acceptance requires it. No remote highlighter, new library, code execution, or document-format conversion was added. This is additive within native document format version 1.
- Autosave gains a small awaitable drain operation, reused before navigation/management. Its debounce, serial requests, local acknowledgement numbers and server revision checks remain.
- A read-only `GET /api/folders/{id}/deletion-impact` endpoint supplies authoritative counts and a subtree token. Counts alone cannot detect same-count replacement of confirmed contents. It is the only endpoint added beyond the requested operations and retained M1 routes.

No known product defect blocks the executed M2 acceptance. Testing limits and deliberate M2 limitations are listed below. No M3 features, dependency updates, commits, tags, pushes, or publication were performed.

## B. File change report

Complete repository inventory, relative to its root:

| File | Responsibility / important dependencies | Why changed |
| --- | --- | --- |
| `backend/app/database.py` | Schema migration, transaction/connection lifetime, note/folder operations, hierarchy reads, cycle/deletion rules; stdlib SQLite, JSON, hashlib, UUID/time | Add persistent relationships and atomic domain operations at the existing persistence boundary |
| `backend/app/models.py` | Folder/tree/impact/delete contracts, nullable folder references, strict intent/counts, code-block support; existing Pydantic | Validate M2 requests while retaining M1 document and revision rules |
| `backend/app/main.py` | Tree/folder/note-delete routes and domain-error mapping; FastAPI, models, Database | Expose requested operations and fresh deletion impact without introducing a service framework |
| `backend/tests/test_library.py` (new) | Temporary-DB hierarchy, moves, deletion, FK, migration, deep traversal and code-block tests; pytest, TestClient, Database, stdlib threads/SQLite/shutil | Verify M2 integrity guarantees and copied-M1 preservation, including destructive failure cases |
| `backend/tests/test_health.py` | Health/route-surface regression checks; existing temporary client fixture | Extend the expected route surface while preserving health/docs restrictions |
| `backend/tests/test_notes.py` | Existing M1 persistence/validation/concurrency tests | Expect schema version 2 and reject future schema 3; retain original note assertions |
| `frontend/src/http.ts` (new) | Shared fetch timeout, HTTP/domain error handling, 204 responses, ApiError; browser Fetch/AbortSignal | Reuse M1 transport behavior across notes and library operations rather than duplicate it |
| `frontend/src/notes.ts` | Note client/types, nullable folder IDs, partial patches, revision-aware deletion; shared HTTP function | Preserve note APIs while allowing metadata-only moves and confirmed deletion; re-export ApiError for existing callers |
| `frontend/src/library.ts` (new) | Folder/tree/summary/impact types and API functions; shared HTTP function, note metadata type | Keep directory transport out of UI/editor code and encode explicit deletion intent in one place |
| `frontend/src/library.test.ts` (new) | Tree/folder/move/impact/delete HTTP contract checks; Vitest fetch stubs | Verify root/null handling, expected revision, counts, recursive intent and token are actually sent |
| `frontend/src/tree.ts` (new) | Iterative visible-row/ancestor calculations and item identity/labels; application library types | Share hierarchy calculations without recursive React rendering or editor knowledge |
| `frontend/src/tree.test.ts` (new) | Deep-chain traversal; Vitest | Demonstrate 2,000 folder levels without recursive call-stack dependence |
| `frontend/src/components/DirectoryTree.tsx` (new) | Accessible tree, roving focus, selected/open markers, scoped keyboard handling; React, pure tree helpers | Implement graphical and keyboard hierarchy navigation with no global keyboard listeners |
| `frontend/src/components/DirectoryTree.test.tsx` (new) | Expand/collapse, levels/current item, visible traversal, Enter/F2/Delete; existing Testing Library/Vitest | Check observable tree behavior and accessibility attributes |
| `frontend/src/components/ManagementDialog.tsx` (new) | Native create/rename/move/delete dialogs, destination paths, explicit counts, Cancel/Escape/focus; React, HTML dialog, tree helpers | Support complete management with existing browser controls and no UI framework |
| `frontend/src/App.tsx` | Library discovery/refresh, selection, management orchestration, transition gate and preferred ID; React, API clients, tree/dialog/editor components | Replace single-note discovery with the authoritative tree and coordinate safe note lifecycles |
| `frontend/src/App.test.tsx` | Retained M1 behaviors plus folder placement, navigation drain/error blocking, rename/move/delete/error/focus/keyboard-isolation integration tests; existing testing tools | Verify complete user interactions rather than only API/helper implementation details |
| `frontend/src/hooks/useAutosave.ts` | Existing serial debounce plus flush waiters/synchronous edit acknowledgements and saved callback; React, note client | Await the latest snapshot before unmounting a note; block transitions on save failure |
| `frontend/src/hooks/useAutosave.test.tsx` | Existing tests plus drain/queued edit/failure/same-event navigation cases | Protect both M1 save ordering and the new note-transition boundary |
| `frontend/src/components/PersistentNote.tsx` | Title/editor/save-state composition, small imperative flush handle, temporary lock; React `useImperativeHandle`, autosave, adapter | Let the shell await persistence without knowing BlockNote internals; briefly freeze editing during transitions/dialogs |
| `frontend/src/components/KnowledgeEditor.tsx` | Core code-block spec and editable flag; existing BlockNote core/React/Mantine and JSON contract | Meet acceptance's code-block requirement and support safe temporary read-only state; no directory dependencies introduced |
| `frontend/src/styles.css` | Small tree/dialog/actions/focus styles and sidebar width | Keep the existing design readable while distinguishing indentation, selection, focus and the open note |
| `frontend/src/test-setup.ts` | Minimal native-dialog method stubs in jsdom; existing testing setup | Permit DOM tests without claiming jsdom implements the browser's modal top layer |
| `README.md` | M2 setup/upgrade, GUI/keyboard, data, API, save and test guide | Explain actual behavior, migration, API additions, and local startup without obsolete single-note instructions |
| `M2_VERIFICATION.md` (new) | Executed results, exact commands, A–U observations and reproducible procedure | Supply reviewable evidence, including true shutdown/restart and two-tab stale-deletion rejection |
| `M2_REPORT.md` (new) | This A–H engineering report | Explain boundaries, execution paths, decisions and risks for architectural review |

Dependency manifests/lockfiles, `.gitignore`, XDG path policy, Vite loopback configuration, and historical M1 report/verification are unchanged. Acceptance control scripts, copied databases, snapshots and screenshots live outside this repository in the enclosing task's `work/`, `outputs/` and `/tmp/`; they are not product features or user-note source files.

## C. Execution flow walkthroughs

### Flow 1 — create a folder

1. **UI:** `App.newItem('new-folder')` receives the toolbar click. It chooses the selected folder as parent, a selected note's folder as sibling destination, or null for root.
2. **Save boundary:** `App.perform` serializes management operations and awaits `editor.current.flush()`. `PersistentNote` exposes this handle using `useImperativeHandle`; the method belongs to the existing `useAutosave` hook. A failed drain stops here and keeps the draft mounted.
3. **Dialog:** `ManagementDialog` opens a native modal, accepts a trimmed-valid name, and submits to `App.submit`.
4. **HTTP:** `library.ts:createFolder(name,parent_id)` uses `http.ts:request` to POST `/api/folders`.
5. **Route/validation:** `main.py:create_folder` receives `models.py:CreateFolder`, which validates name and optional UUID. It delegates to `Database.create_folder`.
6. **Domain/SQLite:** In a `BEGIN IMMEDIATE` transaction, `_check_parent` rejects nonexistent parents, then a parameterized INSERT stores UUID, nullable parent, name, sort order 0 and UTC timestamps. Returning from the connection context commits before HTTP success.
7. **Response/GUI:** The 201 response identifies the committed folder. `App.refreshAfterChange` closes the dialog and calls `refreshTree` → `library.getTree` → `Database.tree`. React installs the authoritative adjacency lists, reveals ancestors, selects the new folder, and `DirectoryTree` renders `visibleRows`.

If the mutation succeeded but the subsequent tree read fails, the UI says the change completed and offers Refresh library. It does not leave the creation form looking as though resubmitting the mutation is necessary.

### Flow 2 — move a note

1. `DirectoryTree`/toolbar calls `App.manage('move',target)`. `perform` drains the active editor first, then `notes.getNote(target.id)` captures fresh target metadata/revision for the dialog.
2. `ManagementDialog` offers all folder paths plus Workspace root. `App.submit` maps an empty root option to explicit `folder_id:null` and calls `notes.updateNote(id,expectedRevision,{folder_id})`.
3. `main.py:update_note` validates `UpdateNote`. Its field set distinguishes an omitted relationship from explicit null. The UUID is serialized into a database string.
4. `Database.update` begins a write transaction, checks the destination, and performs the existing conditional update. `CASE WHEN` changes the folder only when supplied; `COALESCE` is retained for optional title/document. The WHERE clause still requires the expected revision. Success increments revision/updated_at; IDs, title, created_at and document JSON remain unchanged for a pure move. A stale revision returns 409.
5. The client verifies the returned ID/next revision. If the moved note is active, App installs the returned note and increments `editorEpoch` to remount the drained editor with the current revision. This prevents the next autosave from using its pre-move revision. An inactive note move does not reset the active editor.
6. `refreshAfterChange` reads the updated directory and reveals the destination ancestors. Tree membership changes without moving or converting the canonical document.

### Flow 3 — open a note

1. A click or Enter in `DirectoryTree.handleKey` calls `App.selectItem`. Arrow focus movement alone does not load documents.
2. `App.perform` requests `useAutosave.flush`. The same serial saver bypasses the remaining debounce, waits for any active request, and then sends the latest queued snapshot with the newly acknowledged database revision. A synchronous edit counter also catches edits made immediately before the navigation event, before React has rendered them.
3. Flush resolves true only when its latest local edit has been acknowledged. While waiting, the editor/title are read-only and further library operations are gated. An error resolves false, leaves the note/draft mounted, and prevents the GET/unmount transition.
4. `notes.getNote` sends GET `/api/notes/{id}` through `http.request`; `main.py:get_note` calls `Database.get`, whose `_note` decodes JSON and returns metadata.
5. App mounts `PersistentNote` keyed by note ID/editor epoch. `KnowledgeEditor` initializes once with native JSON. Save responses still never overwrite live editor content/caret.
6. App records the ID as a preference, reveals its folder ancestors, and updates selection/current-note semantics. The tree, not localStorage, determines which notes exist; boot discovers a pre-M2 note even with no remembered ID.

A successful autosave invokes App's `noteSaved` callback to refresh summaries so edited titles/revisions/order are current. Request generations reject old tree responses. The focus guard permits explicit selection/operation focus restoration without routine refreshes stealing focus from BlockNote/title inputs.

### Flow 4 — delete a nested folder

1. Delete/F2-equivalent management is scoped to the tree or toolbar. `App.manage('delete',folder)` drains the active draft before determining impact.
2. `library.getDeletionImpact` GETs `/api/folders/{id}/deletion-impact`. `main.py:deletion_impact` calls `Database.deletion_impact` in one read transaction.
3. `Database._impact` builds parent→children adjacency, iteratively visits the target subtree, and selects associated note summaries. It returns descendant-folder count (excluding the target itself), note count, name, and a SHA-256 fingerprint over sorted folder metadata and note membership/revisions/metadata. It does not read every document body.
4. `ManagementDialog` displays permanent-deletion wording and those exact counts. Cancel/Escape invokes no DELETE. The modal starts destructive flows on Cancel and blocks background editing/management while confirmation is open.
5. Confirmation calls `library.deleteFolder(impact)`, sending `recursive:true`, expected counts, and `impact_token` in the DELETE body. `models.DeleteFolder` requires strict counts/token and validates intent.
6. `Database.delete_folder` takes `BEGIN IMMEDIATE`, recomputes impact under the write lock, compares both counts and token, and rejects stale intent with 409 before deleting anything. A nonempty subtree additionally requires explicit recursive intent. Same-count membership replacement or a changed note revision is caught by the token, not just counts.
7. All affected notes are deleted with bound IDs, then folders in reverse traversal order (children before parents). RESTRICT foreign keys remain enabled throughout. This avoids both orphaning and deep cascading-trigger limits. Any failure rolls the entire transaction back; the injected-failure test proves earlier deletes are restored.
8. After commit, the route returns 204. App clears an affected active editor/preference, refreshes the authoritative tree, and restores usable focus. Other notes remain untouched. A 409 keeps the old confirmation visible with an error; cancel and reopen to explicitly review fresh counts.

## D. Architectural decisions

| Problem / selected approach | Alternatives, rationale, tradeoffs and later effect |
| --- | --- |
| **Hierarchy representation:** nullable parent adjacency columns with actual foreign keys | Materialized paths or closure tables add migration/maintenance rules not needed for M2. Stable IDs make moves a single relationship update. SQLite FKs reject invalid references; cycle checks remain a domain rule. Future queries may optimize traversal without changing IDs or editor documents. |
| **Migration:** transactional notes-table replacement only where required | ALTER cannot remove M1's CHECK; resetting the database would destroy data. Named-column copying, FK checking, schema version advancement and rollback preserve M1 fields exactly. No migration framework/new package was justified. Future schema changes can add another explicit version branch. |
| **Tree response:** flat folder/note-summary lists | Nested JSON is convenient at shallow depth but introduces serializer/call-stack limits. Parent IDs carry all hierarchy information while excluding document bodies. The client constructs visible rows iteratively. The whole summary library is read at once; pagination/virtualization are deferred. |
| **Traversal/deletion:** iterative adjacency walk and explicit child-first deletes | Recursive React/Python calls and ON DELETE CASCADE risk stack/SQLite trigger-depth limits. A single transaction still makes multiple bound DELETE statements atomic. The implementation scans summary metadata and uses O(N) memory; very large-library optimization is deferred. |
| **Cycle prevention:** walk prospective parent ancestors under the same serialized write transaction | Checking outside a transaction could allow competing A→B/B→A moves to both pass. BEGIN IMMEDIATE serializes validation plus update. This holds a write lock briefly; a real two-connection test confirms one competing cycle move is rejected. |
| **Ordering:** folder sort_order/name/ID, note title/ID, folders first | No drag/drop ordering subsystem is required. IDs provide deterministic ties; duplicate names are permitted. SQLite NOCASE is ASCII-oriented, not locale-aware natural sorting. Later ordering needs can use the existing folder field. |
| **Frontend state:** React state for tree/selection/expansion and small pure helpers | Redux or a tree framework would add dependencies and obscure the lifecycle. Roving tab focus and flat rows give explicit keyboard behavior. Expansion is ephemeral and automatically reveals the preferred note on reload; it is not separately persisted. |
| **Autosave transitions:** await the existing saver rather than keep many drafts mounted | A per-note draft cache/outbox would require eviction/recovery semantics. The small flush handle retains M1 serial/revision guarantees. Editing is briefly locked during transitions, and a failed save blocks navigation. Advanced recovery remains M3/M5. |
| **Active metadata changes:** remount only after successful drain | Reusing an old hook revision after a move/rename causes spurious conflicts; copying responses into a live dirty editor can overwrite edits. A safe remount uses the latest response/revision. Caret position may reset during explicit management, an accepted tradeoff; ordinary autosaves never reset it. |
| **Recursive deletion:** fresh impact read plus counts AND fingerprint precondition | Tree-derived counts can be stale; counts alone miss replacing one confirmed item with another. One additional read endpoint supplies authoritative identity/revision context. The transaction rechecks it and requires recursive intent. No global library revision, soft-delete table, trash or backup framework is introduced. |
| **Note deletion:** expected revision in DELETE body | Confirmation alone would allow deleting text another tab saved afterward. Reusing M1's revision concept produces 409 on a changed note. The local app uses JSON DELETE bodies directly through its existing Vite proxy. |
| **Dialogs:** native HTML dialog and select controls | A new UI framework is unnecessary. Native modal semantics block background interaction and keep keyboard behavior local. jsdom needs small method stubs, so actual top-layer/focus behavior is separately checked in the browser. |
| **Code blocks:** existing core spec, no highlighter provider | M2 acceptance requires code blocks. The pinned core implementation renders plain source when no highlighter is configured; no executable preview or remote language data was added. Existing format-1 documents remain compatible. |
| **HTTP extraction:** one generic transport plus note/library functions | M1's note-only response handler could not represent tree/folder/204 results. Duplicating transport would drift timeout/error behavior. This is a shared function, not a service framework, and introduces no dependency. |

Folder updates do not have a separate revision field because the requested folder model omits one. Valid concurrent folder metadata changes use last-write-wins behavior, while cycle checks and deletion preconditions remain transactional. Note updates/moves/deletes retain revision protection.

## E. Testing report

Exact commands, directories and all observed A–U outcomes are recorded in `M2_VERIFICATION.md`. Final suites: **49 backend tests, 52 frontend tests**, all passed; lint/type/build/format/dependency/whitespace checks passed. No destructive test accessed the real data path.

Key integrity evidence:

- Migrated a copy of an M1-style database; all note fields and raw JSON text survived. The source stayed schema 1; target became schema 2; repeat initialization left it intact. A deliberately invalid copy rolled back both schema creation and data changes.
- Traversed/deleted a 1,202-folder chain with FK enforcement; frontend helpers traversed 2,000 levels.
- Real competing folder moves could not create a cycle. Existing real competing note writes still produced one winner and one revision conflict.
- A triggered failure late in recursive deletion restored all earlier-deleted notes/folders.
- The real browser created headings/paragraph/code content, switched with pending saves, renamed/moved items, used keyboard navigation, canceled deletion, rejected a second-tab count change, and deleted only the freshly confirmed subtree.
- Both test servers were explicitly terminated; independent requests returned connection refused before restart. Tree and all three full surviving notes matched the pre-restart snapshot. The original pre-M2 note's full row remained byte-for-byte unchanged at revision 7 and was opened through the GUI after restart.

Corrections during implementation: wrong initial npm working directory (no tests executed there); Ruff long-string formatting; test-only `exact` options not supported by Testing Library's TypeScript signature; ESLint's required caught-error cause; initial disabled-dialog focus; post-management tree focus; and distinguishing a committed mutation from a failed subsequent refresh. The final checks were run after corrections. No unexecuted test is counted as passing.

Coverage gaps: fresh Ubuntu/dependency installation, mobile/touch, assistive-technology testing, browser/OS process termination and power loss, disk-full/permission faults, sustained contention and huge-library performance. jsdom does not test the native modal top layer; the browser run does. No new permanent browser test framework was installed; the existing browser automation surface performed the A–U run and the procedure is reproducible from the verification document.

## F. Technical debt and risks

**Acceptable M2 limitations**

- Tree/impact operations load all summary metadata. Moves/impact walks use O(N) memory; full-path dropdown labels can become large/quadratic across a deep chain. No huge-library benchmark, pagination, virtualized tree, or search was added.
- Duplicate names are legal, and identical full paths can be visually ambiguous in a move dropdown; IDs still identify the actual destination. There is no locale-aware/natural sorting or manual ordering.
- Expansion state is in memory. The preferred note ID is origin/profile-specific, but losing it no longer hides saved notes because the tree is authoritative.
- Save errors/conflicts block note transitions. Drafts remain in memory and require copying before reload on conflict. Forced termination can bypass beforeunload warnings. Recovery/outboxes belong to later milestones.
- Tree changes from other tabs are read on refresh, save, or management operations; there is no live synchronization. A disappeared/changed item may return 404/409 and require a refresh. Folder metadata updates are last-write-wins, not revision-protected.
- A response lost after a committed create can still lead to uncertainty/duplicates if the user explicitly retries; idempotency keys are deferred. A **known successful** mutation followed by failed refresh is clearly reported as committed, avoiding that unnecessary retry case.
- Native dialogs and ARIA tree attributes were checked in the browser, but screen-reader interoperability and touch/very narrow layouts were not tested. Deep indentation can require horizontal scrolling.
- Databases remain local/unencrypted with the existing permissions and localhost assumptions. Same-user processes can read files/use APIs; this is not an authenticated network deployment. Intent tokens are stale-operation preconditions, not authentication credentials.
- Default SQLite write locking uses the existing five-second timeout. Very long operations can cause other writes to fail with a visible 503; no background job system was added.
- Existing large editor bundle and upstream HTTPX TestClient deprecation remain. A future dependency update can address these separately.

**Immediate defects / approval blockers:** no known remaining defect blocks the executed M2 acceptance. The cases above are explicit limitations, not claims of untested reliability. Foreign-key integrity, stale deletion rejection, atomic rollback, saved-document preservation, and unsafe-note-transition prevention are tested requirements, not deferred work.

No screenshot-storage feature, search/tagging, engagements, scanners, AI, cloud, auth, multi-user system, trash or advanced backup/recovery was implemented. The preview image is test evidence outside the repository, not an application attachment feature.

## G. Dependency report

No new packages or version changes. All manifests/lockfiles are unchanged from reviewed M1.

- SQLite/UUID/hashlib and traversal containers are Python standard library facilities.
- Folder/intent validation uses the already pinned Pydantic and FastAPI.
- Tree, flush, and dialogs use existing React plus native browser APIs.
- Code blocks use the already installed BlockNote core/React/Mantine packages; no XL package or highlighter service.
- Tests use existing pytest/TestClient and Vitest/Testing Library/jsdom; no redundant test framework.

## H. Git summary

Recommended commit message:

```text
feat: add hierarchical library CRUD with safe note navigation and deletion
```

Commit the listed source/tests and README/M2 report/verification after review. Do not commit user databases/notes, dependency environments, build output, temporary server controllers, copied databases, or intermediate/exported note snapshots. Those test artifacts are outside the repository; existing ignore rules remain unchanged.

Working changes are based on the reviewed M1 commit `bc1441a` (Persist Notes, init SQLite DB). No commit, tag, push, remote change or publication was made. Stop at M2 and await technical-lead review before M3.
