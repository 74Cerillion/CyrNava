# ENGAGE M1 engineering report

## A. Implementation Summary

M1 implements the first persistent titled rich-text note. The browser creates/reopens a note through FastAPI, the backend stores native versioned BlockNote JSON in SQLite outside Git, and a 700 ms debounced autosave shows Unsaved Changes, Saving..., Saved, or Save Error. SQLite uses an atomic revision check to reject stale writes with HTTP 409.

The required 14-step acceptance sequence passed using the real editor and real server process termination/restart. An additional close/reopen of the browser tab with both development servers restarted passed. Whole-host-browser termination was not exercised. Automated checks passed: 35 backend and 29 frontend tests, lint, type/build, format and dependency checks. Detailed evidence and limits are in `VERIFICATION.md`.

M0's two-pane layout, localhost defaults, editor schema, health endpoint and dependency pins are retained. Temporary-note messaging is replaced. There are no new runtime endpoints beyond the three requested notes endpoints; `/health` is retained. No M2 feature was started. Changes are uncommitted for review.

## B. File Changes

Paths below are relative to this repository. This is the complete repository change inventory; unchanged frontend manifest, lockfiles, `.gitignore`, entry point, and test setup are intentionally absent.

| File | Responsibility and dependencies | Reason for change |
| --- | --- | --- |
| `backend/app/database.py` (new) | XDG resolution, schema initialization, connection/transaction lifetime, create/get/update; Python stdlib `sqlite3`, `json`, `pathlib`, UUID and UTC time | Give persistence one explicit home without adding an ORM |
| `backend/app/models.py` (new) | Request/response schemas and version-1 document validation; existing Pydantic, stdlib JSON | Validate API inputs without converting or flattening native documents |
| `backend/app/main.py` (modified) | `create_app`, lifespan, health, notes routes and error mapping; FastAPI, models, Database | Initialize at startup, inject test DBs, and expose requested operations |
| `backend/requirements.in` (modified) | Explicit direct Pydantic 2.14.1 pin, already installed and frozen in requirements.txt | Declare the dependency now imported directly by note validation; no new package/version or lockfile change |
| `backend/tests/conftest.py` (new) | Temporary DB/client fixtures and structured synthetic document; pytest, TestClient | Prevent any test from modifying real user data |
| `backend/tests/test_health.py` (modified) | Health and exact route/method surface checks; temporary client fixture | Preserve health coverage while permitting the three M1 operations |
| `backend/tests/test_notes.py` (new) | Persistence, validation, metadata, revision/real-connection race, schema and XDG tests; pytest, TestClient, Database, stdlib executor | Verify the durability and integrity contract beyond individual functions |
| `frontend/src/notes.ts` (new) | Application JSON/note types, HTTP create/get/update functions, timeout/errors; browser fetch/AbortSignal | Keep HTTP and backend contracts outside the editor/UI |
| `frontend/src/notes.test.ts` (new) | Request body/revision contracts, HTTP/network/format failures; Vitest fetch stubs | Verify the client cannot treat a failed or unexpected response as a valid save |
| `frontend/src/hooks/useAutosave.ts` (new) | Draft state, debounce, serial writes, local edit acknowledgements, errors/retry, unload guard; React and notes client | Make asynchronous save ordering explicit and testable |
| `frontend/src/hooks/useAutosave.test.tsx` (new) | Deferred promises, fake timers, retry/conflict/unmount and rapid-edit cases; existing Testing Library/Vitest | Exercise the cases most likely to lose changes or falsely show Saved |
| `frontend/src/components/KnowledgeEditor.tsx` (modified) | Hydrates BlockNote once and emits detached native JSON snapshots; existing core/React/Mantine, application document type | Retain the dedicated adapter boundary and preserve formatting |
| `frontend/src/components/KnowledgeEditor.test.tsx` (new) | Adapter hydration and detached snapshot contract; real core schema, mocked editor hook/view | Check the adapter without asking jsdom to emulate a complete rich editor |
| `frontend/src/components/editorDocument.ts` (new) | Empty native-document factory; application document type | Keep initial BlockNote document details out of navigation and the HTTP client |
| `frontend/src/components/PersistentNote.tsx` (new) | Title/editor/save feedback composition; autosave hook, adapter, Note type | Give each loaded note its own editing lifecycle |
| `frontend/src/App.tsx` (modified) | Shell, initial creation, remembered-ID loading, health/error states; notes client, persistent note component, empty-document factory, localStorage | Reopen one note while preserving the M0 layout |
| `frontend/src/App.test.tsx` (modified) | Creation, ID-only storage, hydration, visible saves/errors, missing note and health behavior; existing testing tools | Replace disposable-scratchpad expectations with persistent-note behavior |
| `frontend/src/styles.css` (modified) | Small input/button/error styles; no dependency | Support title editing, creation and retry within the existing layout |
| `frontend/index.html` (modified) | ENGAGE title and CSP loopback WebSocket port allowance; browser/Vite | Name the app and permit isolated localhost acceptance ports while keeping remote runtime targets blocked |
| `frontend/vite.config.ts` (modified) | Preserve `/api/notes`, special-case old health rewrite, optional validated loopback backend port; existing Vite/react plugin | Route the exact requested API paths; permit isolated checks without changing defaults |
| `README.md` (modified) | Setup/run/data location/API/concurrency/limitations guide; no runtime dependencies | Replace M0 instructions that described notes as disposable and explain backend restart/port conflicts |
| `VERIFICATION.md` (modified) | Executed checks, 14-step browser acceptance, failures and limits | Record actual M1 evidence rather than carrying forward M0 results |
| `M1_REPORT.md` (new) | This architecture and review report | Supply the requested A–G engineering record |

The acceptance runner, intermediate JSON snapshots, and synthetic databases are outside this Git repository under the enclosing task's `work/` and `/tmp/`. The final screenshot is also outside Git in the task's `outputs/`. No real notes were used or added to source control.

## C. Execution Flow

### Typing a paragraph through to durable storage

1. The user edits the real BlockNote view in `KnowledgeEditor.tsx`. Its `onChange` callback obtains `editor.document`, clones it with `structuredClone`, and emits application-owned `NoteDocument` JSON through `onDocumentChange`. The clone prevents later editor mutations from changing a request's snapshot.
2. `PersistentNote` passes this event to `useAutosave.changeDocument`. A functional React state update replaces the draft document, increments its local `version`, and records the edit time. The current save state becomes Unsaved Changes.
3. The effect in `useAutosave.ts` waits until 700 ms after the most recent edit. Each new edit clears/replaces the pending timer. If a write is already running, the new draft remains pending; it is not dropped.
4. The timer calls `updateNote(note.id, revision, snapshot, signal)` in `notes.ts`. The request contains title, native `document_json`, and the expected database `revision`. UI state becomes Saving... for that snapshot. Requests have a 10-second timeout.
5. Vite forwards `PATCH /api/notes/{id}` unchanged to localhost FastAPI. `main.py:update_note` validates the UUID and `models.py:UpdateNote` validates the expected revision, title/document shape, version contract and update fields. There is no service class because the application logic is still this small.
6. The route calls `Database.update`. A fresh SQLite connection enables foreign keys. One parameterized SQL statement performs `UPDATE ... SET revision = revision + 1 ... WHERE id = ? AND revision = ?`. A zero-row result becomes either NoteNotFound or RevisionConflict. There is no separate read/compare/write window that another request could slip through.
7. A successful update reads the row while still in the transaction. Leaving `Database.connect` commits before the route returns. On failure, it rolls back; the connection always closes. The stored `document_json` is serialized native JSON text in SQLite, not HTML or Markdown.
8. FastAPI returns the updated note/metadata. The HTTP client checks the expected ID and next revision. The hook updates the database revision and acknowledges only the local edit version that was submitted. It never installs the response document into the live editor.
9. Saved appears only when the latest local edit version equals the acknowledged version. If newer typing occurred during the request, the draft remains Unsaved Changes and the latest snapshot is saved next using the newly acknowledged database revision.

### Reopening the note

`App`'s `load` function reads only `engage.note-id.v1` from localStorage and calls `notes.ts:getNote`. Vite forwards GET to `main.py:get_note`, which calls `Database.get`. SQLite returns the row; `_note` decodes `document_json` without translating the document. FastAPI returns it and the client checks the supported format.

`App` mounts `PersistentNote` keyed by the returned note ID. The autosave hook starts from that saved title/document/revision; `KnowledgeEditor` initializes BlockNote with `initialDocument`. The editor renders native headings/styles/children, and the status begins at Saved. No save response remounts or resets the editor. A missing remembered note shows an error rather than silently replacing it.

## D. Architectural Decisions

| Decision | Why; simpler alternatives; accepted tradeoffs; effect on later work |
| --- | --- |
| Python stdlib SQLite, one connection per operation | Three operations do not justify an ORM, pool, or async database dependency. Synchronous FastAPI routes run blocking work in its worker thread pool. Connections are not shared across threads. The cost of opening a local connection is accepted for M1; repository methods can change internally later. |
| XDG storage outside Git | Saved notes outlive code changes/clones and cannot accidentally be staged through this repository. Relative XDG values are ignored; in-repository paths are rejected. A JSON file would be simpler but would not meet SQLite or atomic revision requirements. Newly created files/directories are private to the user. |
| One notes table, nullable reserved folder column | Implements the requested model without a premature folders table. `folder_id` is constrained to NULL until M2. Foreign-key enforcement is enabled on every connection now; there is no actual folder foreign key pointing to a nonexistent table. M2 must migrate the table to add the real relationship. |
| `PRAGMA user_version = 1` | Schema initialization uses an explicit transaction and version check. Existing version 1 is unchanged; a newer schema fails startup instead of being overwritten. A future migration can add a sequential version branch. No migration dependency/framework is needed yet. |
| Native JSON plus document format version | Rich formatting remains authoritative without lossy Markdown/HTML conversion. Schema version controls database layout; format version separately controls document interpretation. Replacing/upgrading the editor will require an explicit document-format decision rather than navigation knowing editor internals. |
| Supported-block envelope validation | Uses existing Pydantic and mirrors the existing six-block M0 schema. Preserves properties/styles/children rather than reconstructing documents. Limits bound normal stored-document size/complexity. It is intentionally not an exhaustive reimplementation of every BlockNote property; adding block types requires updating the adapter and version contract together. |
| Serial debounced autosave plus two counters | Serial requests avoid the in-tab race at its source. A local edit version prevents a delayed acknowledgement from falsely claiming new typing was saved. The database revision protects against other tabs/processes. Allowing overlapping writes would require more response/revision coordination with no M1 benefit. |
| Full snapshots instead of deltas | Easy to understand, validate, retry and test. More JSON is sent on each save, bounded by the 1 MiB limit. Delta protocols and background infrastructure are deferred. |
| ID-only localStorage | Reopens one note without adding a list endpoint/navigation system. The actual document always reloads from SQLite. The tradeoff is origin/profile dependence and a lost pointer if browser storage is cleared; listing/recovery belongs to later milestones. |
| Explicit retry and conflict stop | Transient failure retains the draft and offers retry. A lost response after a committed write may produce a later 409; this is safer than retrying with an assumed new revision and overwriting another write. Conflicts retain local edits but require manual copying/reload; no merge/force-write UI was added. |
| Initial content applied once | Save responses never overwrite active editing state or move the caret. The adapter exposes JSON in/out; surrounding navigation and API code import no BlockNote implementation types. |
| Optional numeric loopback proxy port | Allows isolated acceptance on a separate origin/database while default ports remain unchanged. Validation prevents this option from becoming an arbitrary remote target. CSP WebSocket allowance remains restricted to 127.0.0.1. |

### The A/B concurrency scenario

Suppose SQLite is at revision 7. Paragraph A produces local edit 1 and starts a PATCH expecting revision 7. The user then types B: the document is now A+B at local edit 2. M1 queues that full snapshot and keeps only one request active.

When A's response arrives with database revision 8, it acknowledges local edit 1. The live draft remains A+B and cannot show Saved because local edit 2 is still pending. The hook then sends A+B expecting revision 8. Only its successful response (revision 9) permits Saved.

If another tab wins a write in between, the next expected-revision condition fails with 409. SQLite changes zero rows. The losing tab keeps its local draft and shows Save Error. Serial requests solve ordering within this editor; the SQL revision condition solves stale writes across editors.

## E. Testing Results

35 backend tests and 29 frontend tests pass. ESLint, TypeScript/Vite build, Ruff lint/format, `pip check`, and `git diff --check` pass. No new packages or version changes were introduced. Pydantic, already installed/frozen as FastAPI’s dependency, is now explicitly declared in requirements.in because M1 imports it directly. See `VERIFICATION.md` for coverage and each observed acceptance step.

The browser run created an H1, paragraphs, bold/italic text, saved, refreshed, stopped/restarted the backend, reloaded, modified the same note, and verified persistence. It also confirmed recovery after an actual backend outage and reopened the note after both servers and its browser tab were closed/restarted.

Failures/corrections during work: an initial npm invocation used the repository root instead of `frontend` and exited without executing checks; corrected directory, then all checks executed successfully. Initial Ruff long-line findings were formatted. Review found an unhashable malformed block `type` could escape validation; added a string guard and passing regression cases. Boolean format versions were made strict integers. Initial tool-session cancellation did not terminate child servers; that run was excluded from restart evidence and replaced with confirmed process exits plus refused-connection checks. There were no failing assertions in the final suites.

The M0 Starlette/HTTPX deprecation and Vite editor chunk-size warnings remain visible. Full browser-process/OS shutdown, power-loss durability, disk-full/permission failures, browser-storage-denied behavior in a real browser, and prolonged database-lock exhaustion are untested. No unexecuted check is counted as passing.

## F. Risks and Technical Debt

Acceptable M1 limitations:

- Unsaved drafts are memory-only. The browser receives a beforeunload warning while dirty, but forced close/crash can bypass it. Wait for Saved. No durable client-side outbox or background retry was introduced.
- A cleared/changed browser origin/profile loses its note pointer. SQLite data remains, but M1 has no list/recovery UI. A storage-write failure after creation reports the note ID; an ambiguous failed POST can leave an unreferenced row. Idempotent creation/discovery is deferred.
- A 409 requires copying local changes before reload. There is no merge, live synchronization, or conflict recovery workflow. A successful save can become stale if a second tab writes later; the next edit will detect that conflict.
- Backend health is sampled at page load. Actual save errors are reported separately; continuous monitoring is not implemented.
- Files are local and permission-restricted, not encrypted. Local processes running as the same user can access them. There is no authentication, backup, or protection against a compromised local account in M1.
- Incoming documents are JSON and are never evaluated or rendered as arbitrary HTML by application code. SQLite uses parameters. The editor uses its normal schema renderer and existing CSP. This remains a localhost development application, not a hardened network deployment.
- Size/nesting limits may need adjustment for larger notes. Every save sends the full document. The editor bundle is still large.
- Actual folder referential integrity requires an M2 schema migration; merely having a nullable column does not create that relationship.
- Preliminary test listeners on ports 8001/5174 survived tool cancellation and cannot be signalled from a new sandbox namespace. Host-terminal cleanup is documented in `VERIFICATION.md`. The controlled acceptance servers use 8002/5175 and are explicitly shut down.

No known product defect blocks the tested M1 acceptance. Environmental and untested cases above are explicit limits, not passing test claims. No advanced recovery, folders, search, attachments, cloud/AI, auth, or engagement tooling was implemented.

## G. Git Changes

Recommended commit message:

```text
feat: persist the first ENGAGE note with revision-safe autosave
```

Summary: introduce XDG SQLite storage and a versioned notes API; connect the isolated editor through a small HTTP client and serial debounced autosave; retain ID-only reopening and visible failure/conflict states; add isolated persistence/concurrency tests and the real restart acceptance record.

No commit, push, tag, release or publication was performed. Stop after M1 and review these persistence, asynchronous-save, and optimistic-concurrency boundaries before authorizing further work.
