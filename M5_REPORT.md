# ENGAGE M5 engineering report

## A. Implementation summary

M5 improves failure transparency and adds a verified recovery path for both conflicting drafts and complete local workspaces. The implementation is ready for architectural review; no M6 work, commit, push or tag was performed.

### Review findings and work packages

The working tree was clean at `cf8e4fe` (`m4 (feat) Add reliable image and screenshot support`). Inspection covered `App`, the tree/dialog components, `KnowledgeEditor`, `PersistentNote`, `useAutosave`, HTTP clients, FastAPI routes/models, `Database`, `AssetStore`, tests, dependency pins, ignore rules and setup documentation.

Already working and retained: native BlockNote JSON; dedicated editor adapter; debounced single-request autosave; acknowledgement of only the submitted snapshot; revision compare-and-swap; beforeunload warnings; save/upload draining before navigation; visible request errors; note/folder deletion confirmation with expected revision/descendant counts/fingerprint; transactional recursive deletion; image ownership/content/path validation and cleanup. No essential M4 persistence/upload prerequisite was missing. M4's unexecuted OS screenshot/physical-disconnection checks are not retroactively claimed passed.

Concrete gaps corrected:

1. API failures previously cleared on further typing, potentially hiding an outage and restarting requests without an explicit retry. They now remain visible while the newest draft accumulates. Local title-validation errors still clear on correction.
2. Repeated identical editor/title events could schedule redundant writes. Identical title values and serialized native documents now leave the edit version unchanged.
3. Conflict messages only advised copying text manually. A recovery dialog now reads the saved version, allows inspection, downloads **both** local and saved versions, requires the user to verify the file was retained, then explicitly reopens the current saved note. There is no forced stale write or automatic merge.
4. No complete tested backup/restore method existed. A Python standard-library CLI now validates and copies an offline profile, verifies hashes, refuses overwrites and restores into a new profile. A cooperative profile lock coordinates the backend with offline tools.
5. Browser checks were not reproducible as a repository test command. Two pinned Playwright journeys now launch isolated servers, inject failures, verify recovery and perform a real restoration/open drill.

Work proceeded in those packages with existing and new tests between changes. Schema version remains **3**, document format remains **1**, and **no HTTP endpoint was added or removed**. Existing image and deletion operations were not rewritten.

Final evidence: **92 backend tests passed, 77 frontend tests passed, 2 Playwright journeys passed**. Lint, formatting, TypeScript/Vite build, pip check and Git whitespace checks passed. Restoration rendered correctly in real Chromium; the original profile remained unchanged. Remaining manual/platform checks are listed in section E.

## B. File change report

Paths are relative to this repository. Source responsibilities remain separated; no new global state store or persistence framework was introduced.

| File | Responsibility, dependencies and reason |
| --- | --- |
| `.gitignore` | Adds backup/recovery directories, conflict downloads, profile lock, staging and browser-report guards. Runtime data/backup paths are also rejected inside this checkout. |
| `README.md` | Current M5 setup, retry/conflict behavior, backup overview, browser-test commands and report links. |
| `BACKUP_RESTORE.md` | Exact offline backup/restore procedure, directory mapping, validation, overwrite policy, privacy and failure limits. |
| `M5_REPORT.md` | This architecture/report/change inventory. |
| `M5_VERIFICATION.md` | Exact executed commands, results, failures/corrections, restoration evidence and remaining checks. |
| `backend/app/profile.py` | New small Linux `fcntl.flock` context manager. Backends hold shared locks; offline backup takes an exclusive lock. Uses only Python standard library. |
| `backend/app/main.py` | Holds the profile lock across the existing startup/lifespan/shutdown. Database initialization and asset cleanup remain inside that protected lifetime. No routing changes. |
| `backend/app/backup.py` | New offline CLI: safe paths, read-only profile validation, image validation, hashes, staging, exclusive destination creation, backup and restore. Depends on stdlib plus existing application models/database/image validation. |
| `backend/tests/test_backup.py` | Temporary complete-profile restoration, manifest/database/image corruption, missing components, overwrite refusal, active-backend lock, source preservation, symlink/sidecar/path/cycle and copy-failure tests. Uses existing pytest/TestClient/Pillow. |
| `backend/tests/test_reliability.py` | Real SQLite failed-write rollback, four competing expected-revision updates, and recursive deletion rollback including asset metadata/files. Uses existing pytest and stdlib threads; no database mocks. |
| `frontend/package.json` | Adds `test:e2e` and exact dev-only `@playwright/test` 1.64.1. Runtime versions unchanged. |
| `frontend/package-lock.json` | Pins Playwright test/Playwright/core 1.64.1, with npm resolver metadata updates. Existing package versions remain unchanged. |
| `frontend/playwright.config.ts` | Small Chromium configuration, one worker, zero retries, bounded timeout and failure screenshots. Uses the new test dependency. |
| `frontend/e2e/workspace.spec.ts` | Two actual-browser journeys. Owns temporary profiles, allocated loopback ports and child-process startup/stop/restart; exercises outage/retry, stale responses, image loading, deletion cancel, restoration and conflict-file recovery. Uses Playwright, Node stdlib and the existing Python environment. |
| `frontend/vite.config.ts` | Limits Vitest discovery to existing `src/**/*.test` files, keeping the Playwright suite separate. Development proxy/loopback defaults unchanged. |
| `frontend/tsconfig.json` | Includes Playwright configuration/test sources in existing TypeScript checks. |
| `frontend/src/hooks/useAutosave.ts` | Retains serial saver and revisions; deduplicates identical inputs, distinguishes local validation from API failures, retains API error until Retry, exposes native current draft to recovery UI. Depends on existing React and note client. |
| `frontend/src/hooks/useAutosave.test.tsx` | Adds explicit-retry-during-outage and duplicate-event behavior while retaining all existing stale response, rapid editing, conflict, flush, unload and abort tests. |
| `frontend/src/components/ConflictRecovery.tsx` | New native dialog: read saved note, inspect JSON, download both versions, require retained-file confirmation, fresh GET on explicit reopen. Uses existing React/note client and browser Blob/download APIs. No BlockNote knowledge or write endpoint. |
| `frontend/src/components/ConflictRecovery.test.tsx` | Inspect/cancel, disabled unsafe reopen, download/confirmation/fresh read and failed-read preservation tests. Uses existing Vitest/Testing Library. |
| `frontend/src/components/PersistentNote.tsx` | Drains pending uploads before conflict review, locks the editor/title during review, presents recovery button and passes current native draft. Existing navigation handle/save path retained. |
| `frontend/src/App.tsx` | Applies an explicitly recovered note by remounting the existing adapter with its current revision, clears obsolete transition error after confirmed save, updates M5 label. Existing navigation/deletion implementations retained. |
| `frontend/src/notes.ts` | Conflict message points to the recovery workflow. Existing 409/status/revision-response checks unchanged. |
| `frontend/src/styles.css` | Bounds and wraps the recovery document preview; no unrelated redesign. |

Review artifacts outside Git: `../engage-m5-restored.png` and `../engage-m5-restoration-evidence.json`. The latter contains only generated test data and records the restored tree/note, image byte count and absence of external application requests. Generated `frontend/test-results/` stays ignored.

## C. Execution flow walkthroughs

### Flow 1: successful autosave

User types → core BlockNote edits its native document → `KnowledgeEditor.tsx:BlockNoteView.onChange` emits a structured clone → `PersistentNote` calls `useAutosave.changeDocument` → identical serialized content is ignored; changed content increments the local edit version and updates `draft` → hook reports Unsaved Changes → after 700 ms debounce, one `updateNote` request begins → `notes.ts:updateNote`/`http.ts:request` PATCH expected revision + current title/document → `main.py:update_note`/Pydantic validates → `Database.update` uses `BEGIN IMMEDIATE`, validates image ownership and applies a single parameterized `UPDATE ... WHERE id=? AND revision=?` → revision increments and transaction commits → HTTP response is checked for correct ID/next revision → hook acknowledges only that local snapshot → Saved only if the latest edit version equals the acknowledged one.

### State representation

| Concept | Actual representation |
| --- | --- |
| Current editor state | BlockNote's live document; a native clone plus title in hook `draft` |
| Local change identity | `draft.version` and synchronous `versions.current.edited`; unrelated to database revision |
| Last confirmed local snapshot | `savedVersion` and `versions.current.saved` |
| Server concurrency token | `revision`, advanced only after a checked response |
| Pending changes | Current local edit version differs from saved version |
| In-flight request | `inFlight` ref, `busy`, and captured `savingVersion` |
| Failure | Error/failure refs, conflict flag, optional local-validation flag; current draft remains |

If A is saving and the user types B, B gets a newer local version. A's response can advance the server revision but only acknowledges A. The hook continues to show B as unsaved and sends B afterward with the new revision. There is never a second simultaneous PATCH from this saver. No response replaces the live document.

### Flow 2: failed autosave and backend recovery

Editing → same debounced PATCH → backend unavailable or storage/API failure → `http.ts`/`notes.ts` throws → `useAutosave.reportError` records failure, resolves navigation flush waiters false and displays Save Error → current title/document stay in React and BlockNote → further typing updates the draft but does not clear a network/server error or auto-retry → `App.perform` cannot switch away while the flush fails → backend returns → Retry save calls `clearTransientError` for a non-conflict failure → the same serial saver submits the latest retained draft at the last acknowledged revision → successful response → Saved and normal autosave resumes. `App.noteSaved` clears the obsolete transition error and refreshes summaries.

If the server committed but the response was lost, retrying the old revision safely yields 409. It does not silently overwrite a newer record. That ambiguity is resolved through the conflict path rather than an unsafe force-save.

The existing beforeunload warning is retained for dirty drafts and uploads. It is advisory and does not guarantee persistence or recovery after forced termination. There is no unload-time primary save request or persistent offline queue.

### Flow 3: revision conflict

Client submits expected revision 5 → `main.py:update_note` → `Database.update`'s atomic comparison affects zero rows if 6 is current → existing-note check distinguishes conflict from 404 → HTTP 409 with no mutation → `notes.ts` gives an actionable message → hook retains draft/error and blocks automatic retries even while typing.

User selects Review conflict and recover → `PersistentNote.beginRecovery` locks editing, drains outstanding M4 uploads, then opens `ConflictRecovery` → `getNote` reads the persisted snapshot → dialog shows saved title/revision and inspectable native JSON while retaining the local draft → Download both versions creates a local JSON file containing `local_draft`, complete `saved_note`, note ID and recovery format → user verifies the file exists and confirms → Reopen saved version performs a **fresh GET**; failure leaves the existing editor open → `App` sets that returned note and increments editor epoch → the adapter remounts with current document/revision. Later saves use the current revision normally. Cancel keeps the original draft; no write is made by the dialog.

This intentionally chooses retention + explicit reload over replacement or merging. A user can compare and manually reapply the retained draft after review. The recovery file is not a complete workspace backup: image bytes remain in the original workspace. Never delete it without retaining needed changes elsewhere.

### Flow 4: backup and restore

User waits for Saved/uploads and cleanly stops all backends → `python -m app.backup backup` resolves default XDG profile or explicit `--data-dir` → `safe_path` rejects checkout/symlink/nested destinations → `profile_lock(..., offline=True)` takes the exclusive lock → `validate_profile` reads schema-3 SQLite without initializing it, checks integrity/FKs/hierarchy/native notes/image ownership and validates every owned image → computes database/image SHA-256 values → `_publish` copies **unchanged bytes** to a private sibling staging directory → verifies the copied profile and manifest → reserves a previously nonexistent destination, takes its lock, moves validated entries and reports success.

Restore → `restore_backup`/`validate_backup` reject missing, corrupt, altered or unsafe data → no archive extraction or manifest paths are trusted as copy targets → `_publish` copies the validated DB/assets to staging, verifies them and refuses any existing destination → new profile preserves IDs, revisions, timestamps, relationships and image URLs → backend starts with `XDG_DATA_HOME` equal to the profile's **parent**, acquires its shared lock and follows existing initialization → `App` discovers notes → adapter loads native JSON → local asset GET resolves the copied file → rendered heading/bold text/image are checked. The Playwright drill compares tree/note records and image bytes exactly and checks that the original database is unchanged.

## D. Architectural decision review

| Decision | Problem, alternatives, rationale, tradeoff and dependency failure |
| --- | --- |
| Keep version-based save state | Existing local versions already distinguish new typing from old acknowledgements. A state-machine package/rewrite would add risk without correcting a deficiency. Retain refs/state and serialize requests. A failed request leaves the latest draft dirty; force quit still loses in-memory work. |
| Explicit retry for API failure | Clearing errors on each edit concealed outages. Keep API failures visible until Retry; only local validation resumes on correction. Simpler periodic retries were rejected because they can hide failure/repeat ambiguous requests. User must retry after backend restoration. |
| Deduplicate exact inputs | Identical editor/title events need no write. Compare current strings/serialized JSON before incrementing version. No semantic deep-diff library or whole-document patch protocol. Serialization costs CPU within existing document limits; key-order differences can still count as changes. |
| Retention + reload conflicts | Existing copy-before-reload advice was insufficiently concrete. Use a native dialog, both-version JSON download, user verification and fresh read. Force-save/automatic merge would risk data loss; a new note copy would require cross-note asset duplication. No automatic replacement is offered. Failed reads preserve the draft; the browser cannot prove a download was retained, so user verification is explicit. |
| Drain uploads and saves before transitions | Existing `App.perform` and `PersistentNote.flush` already work. Reuse them instead of per-note queues/caches. Block unsafe transitions on failure and retain current editor. Conflict review also drains uploads before freezing its snapshot. A failed backend deliberately reduces navigation availability to protect the draft. |
| Preserve deletion transactions | Existing revision/count/fingerprint checks and confirmations already satisfy M5. Do not rewrite them. Reuse SQLite rollback and post-commit M4 cleanup. Injected late deletion failure proves notes/folders/asset metadata/files remain intact. Cleanup failure after a committed delete still retries on startup as before. |
| Offline directory backup | SQLite plus files lack a shared transaction. Stopping the backend gives a simple stable dataset. Standard-library copy/checksums are preferable to archive libraries, live snapshots, daemons or cloud services. Sidecars are rejected, not guessed around. If validation/copy fails, command fails and source/existing destinations remain intact. |
| Shared/exclusive profile lock | Documentation alone cannot catch an accidentally running current backend. Lifetime shared locks permit existing local multiple-process use; exclusive offline lock blocks backup until stopped and blocks backend startup during it. `fcntl` is Linux-specific and advisory; older backends/external tools must still be stopped. No new lock table or distributed infrastructure. |
| Validate before publication | Copying files alone does not demonstrate recovery. Read-only integrity/FK/native-document/image checks, manifest hashes, staging and no-overwrite reservation catch common failures. Extra I/O/decoding is accepted for offline reliability. Hashes are not signatures, and full crash/power-loss atomic publication is deferred. |
| Current-format backup | Schema 3 and existing note/image validators define the exact current dataset. A generic migration framework is unnecessary. Older profiles should first be upgraded by the backend; future schema changes must update backup validation deliberately. Missing files or unsupported schema cause refusal, never silent omission. |
| Reproducible browser tests | Vitest covers component/hook behavior but cannot prove native editor, downloads, process outages or restored rendering. Add exact dev-only `@playwright/test` 1.64.1 and Chromium, retaining Vitest. [Published package](https://www.npmjs.com/package/@playwright/test?activeTab=versions). New maintenance is browser/test tooling only; no application runtime service or dependency is introduced. |

## E. Testing report

Final executed: **92 pytest, 77 Vitest, 2 Playwright passed**. Ruff check/format, ESLint, TypeScript including e2e sources, Vite build, pip check, and Git whitespace check passed. `M5_VERIFICATION.md` records exact commands, intermediate failures/corrections and failure-scenario mapping.

No real application profile was used. Backend tests inject temporary DB directories. Browser tests allocate temporary XDG profiles and loopback ports, launch their own servers, stop/restart their own backend, restore to a different profile and stop all children in `finally`. They cannot be pointed at an existing server/profile. Browser HTTP requests outside loopback are blocked and recorded; the main journey observed none.

Mandatory restoration evidence exists in both an API/SQLite test and real Chromium. The browser drill creates nested folders, a formatted note and local PNG, saves, stops both services, invokes the actual CLI backup/restore commands, launches the restored profile, compares records/bytes, and verifies rendered formatting and image decoding. A preview and JSON evidence are provided outside Git.

Unexecuted: physical internet disconnection, OS screenshot-tool capture, complete cross-browser/platform/assistive-technology coverage, sustained maximum-image/resource-pressure tests, hard power loss, forced browser termination and arbitrary external file/database tampering. No guarantee is claimed for browser unload warnings or unacknowledged drafts after process death. The required M5 browser journey and restoration checks were executed; they are not left as manual-only placeholders.

## F. Reliability assessment

| Dimension | Assessment and limits |
| --- | --- |
| Data integrity | Parameterized writes/FKs/CAS and single-request autosave retained; failed-write/concurrent-update/late-delete rollback tests passed. No stale response installs editor content. Files and SQLite still lack one shared transaction; M4 cleanup remains best effort. |
| Availability | Local backend outages are visible; latest edits remain while open, navigation blocks safely, and explicit Retry recovers. No daemon, offline write queue or live health monitor; page-load health remains a snapshot. |
| Recoverability | Complete offline backup/restore is validated and demonstrated, preserving relationships, native JSON and images. Conflict recovery retains both document versions before deliberate reload. Backups/recovery files are unencrypted and must be kept private. |
| Error transparency | Save/retrieval/folder/deletion/upload/missing-image behavior remains visible. API outages do not clear on typing. Backup/restore errors are nonzero and avoid stack traces/internal paths. Successful save clears obsolete navigation failure. |
| Transaction consistency | Expected revisions and recursive deletion remain atomic. Offline lock supplies the stable backup boundary. Sidecars, broken references and missing/corrupt files cause refusal. Power-loss publication durability is not guaranteed. |
| Failure isolation | Tests/profiles/processes are isolated; failed restore cannot overwrite an existing profile. Backup staging is distinct from source. Asset failures retain surrounding note content. Conflicts do not force writes. |

Residual security: runtime remains loopback-only, data/assets remain outside this checkout, existing image validation and CSP/proxy are unchanged, and no external runtime calls were added. Backups expose everything in the saved workspace to anyone who can read them; recovery JSON exposes note content too. File permissions are private but data is not encrypted. Hashes detect accidental corruption, not a maliciously rewritten manifest. Restore trusted local backups. The guard rejects ENGAGE checkout paths; users must also keep destinations outside other Git repositories.

## G. Technical debt

**Critical before acceptance:** No known unresolved implementation defect in the executed M5 paths. Owner review and normal-machine validation remain appropriate; the report does not claim universal platform reliability.

**Deferred, acceptable for Phase 1:** unsaved drafts remain in memory; conflicts require manual comparison/reapplication after downloading; there is no force-save or merge/import UI; the browser cannot verify retained download files; offline tools require every older/non-cooperating writer to be stopped; Linux advisory locking is platform-specific; profiles with journal sidecars require clean recovery first; current-format-only backups; staging/new destination can remain after abrupt process death; owned-but-unreferenced assets remain until note deletion; no disk quota or encrypted backups; repeated serialization and image validation add bounded work; page-load health is not live monitoring. Existing Starlette HTTPX deprecation, large frontend bundle and platform/browser coverage remain tracked.

**Future scope:** M6+ product work, persistent draft journals, coordinated live snapshots, crash-durable publication, authenticated/encrypted/scheduled backup, data-format migration tools, fine-grained asset garbage collection, more advanced conflict merging and broad browser/performance/accessibility campaigns. None is started here.

## H. Git summary

Recommended commit message:

```text
feat: add verified offline recovery and strengthen save failure handling
```

Commit only reviewed source, pinned test dependency/lockfile, tests and documentation. Never commit personal profiles, SQLite files, images, backups, conflict recovery downloads, staging directories, browser artifacts, dependency environments or caches. The new ignore rules are secondary protection; backup CLI refuses this checkout. The initial committed M4 state is preserved in Git history; no automatic commit, push, tag or publication has occurred. Stop at M5 for the owner's review.
