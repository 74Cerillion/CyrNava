# F-09 M2 — backend search engineering report

Implementation date: 2026-10-29. Scope: the approved backend milestone only.

## 1. Outcome and scope

Implemented SQLite FTS5 search across saved notes, bounded BlockNote plaintext
extraction, transactional index synchronization, `GET /api/search`, schema-5
backfill, an offline rebuild command, and backend regression tests. No frontend
source, dependency versions, document format, storage paths or license changed.

The full F-09 feature is **not complete**. M3 search controls/result navigation
and M4 benchmarks/release acceptance remain pending. No commit, push, publication
or installation into the owner's everyday desktop release was performed. The
owner's private profile was not opened or migrated; tests used synthetic data in
temporary profiles outside Git.

## 2. Every created or modified file

Paths below are repository-relative. Dependencies describe logical relationships,
not additional installed packages.

| File | Responsibility, dependencies and reason |
| --- | --- |
| `backend/app/search.py` (new) | Uses standard-library JSON, regex and SQLite. Owns bounded native text extraction, derived schema/triggers, index upsert/verification/rebuild, literal-prefix query preparation, ranking, snippets and current folder paths. Keeps search details out of canonical note/API code. |
| `backend/app/search_index.py` (new) | Offline CLI uses `search`, `Database.connect`, existing backup path/canonical validation and exclusive profile locks. Repairs only derived objects; refuses live/missing/unsafe/legacy profiles. Adds no HTTP maintenance endpoint. |
| `backend/app/database.py` | Existing SQLite lifecycle/CRUD. Adds version-5 migration, profile-lock protection, calls to `index_note` inside create/update transactions, and snapshot-based `search`. Canonical revision checks remain in their existing atomic UPDATE. |
| `backend/app/templates.py` | Existing native-template store. Imports `index_note` and calls it before committing instantiated notes/assets. Template capture/catalog content remains separate from note search. |
| `backend/app/main.py` | FastAPI routing, existing Pydantic validation and domain error mapping. Adds one GET route with bounded query/limit, response model, private 422/503 errors and no-store headers. Initialization precedes the serving shared lock so migration can acquire exclusivity. Validation errors gain no-store without echoing input. |
| `backend/app/models.py` | Existing Pydantic envelopes. Adds `SearchResult` and `SearchResponse`; document validators and note fields are unchanged. |
| `backend/app/profile.py` | Existing Linux `fcntl` lock. Yields its descriptor and adds `require_exclusive` for migrations; retains the lock until migration commit. Refusal messages now describe offline maintenance, including rebuild. |
| `backend/app/backup.py` | Existing offline validation/copy/restore. Accepts schema 5 while retaining 3/4; validates template content for versions >=4. Copies/checksums the complete DB, including FTS, without read-only FTS writes or implicit migration. |
| `backend/app/__main__.py` | Supported loopback release entrypoint. Disables Uvicorn access logging so GET search terms are not written as request URLs. Desktop serving already disabled it. |
| `backend/tests/search_helpers.py` (new) | Test-only removal of derived schema to construct genuine old-version fixtures, plus snapshots of every canonical table. Uses synthetic test connections only. |
| `backend/tests/test_search.py` (new) | Existing pytest/TestClient and real SQLite FTS5. Tests extraction/native fixtures, API contract, relevance, metadata paths, validation/privacy, synchronization, failures, competing saves and operation with outbound connection calls blocked. |
| `backend/tests/test_search_index.py` (new) | Existing pytest/TestClient/subprocess tools. Tests migration/backfill, byte-preserved JSON, idempotency, unavailable FTS5, rollback, exclusive locks, CLI refusal/rebuild, corruption limits and schema-4/5 backup/restore. |
| `backend/tests/test_assets.py` | Historical schema-2 fixture now also removes later search objects. Asserts current version 5 while preserving canonical note fields. |
| `backend/tests/test_document_compatibility.py` | Native mixed/image restart/backup regression now expects schema 5; formatting/JSON assertions remain intact. |
| `backend/tests/test_health.py` | Existing explicit route inventory includes the single new search GET endpoint. |
| `backend/tests/test_library.py` | Existing schema-1 migration test expects current version 5; historical-source and byte-preservation assertions remain unchanged. |
| `backend/tests/test_notes.py` | Existing restart/current-schema checks expect 5; future-schema refusal fixture advances to 6. |
| `backend/tests/test_templates.py` | Historical schema-3 fixtures remove later search objects and expect migration to 5; old backup remains version 3. Existing template/image assertions retained. |
| `docs/search.md` (new) | Complete API contract, token/ranking limitations, transaction flow, pre-upgrade backup, offline rebuild and isolated manual HTTP procedure. |
| `README.md` | Marks search as backend-only, links the guide/report, explains schema 5 and adds `--no-access-log` to development startup. |
| `BACKUP_RESTORE.md` | Documents schema-3/4/5 compatibility, retained backup rollback, derived-index validation limits and no-access-log startup. |
| `docs/architecture.md` | Updates current schema/backend boundaries and actual note-save flow; distinguishes implemented API from pending search UI. |
| `docs/desktop-launcher.md` | Adds `--no-access-log` to the existing direct-development command. Launcher behavior itself is unchanged. |
| `CHANGELOG.md` | Records the unreleased backend-only change and pending M3/M4 scope. |
| `F09_M2_REPORT.md` (new) | This review record, decisions, test evidence, limits and suggested commit. |

## 3. Actual execution flow

### Typing and saving a paragraph

1. `frontend/src/components/KnowledgeEditor.tsx` receives BlockNote's
   `BlockNoteView.onChange` and sends a structured clone of `editor.document`
   through `onDocumentChange`. The adapter stays isolated and unchanged.
2. `PersistentNote.tsx` passes that event to `hooks/useAutosave.ts::changeDocument`.
   The existing hook records a local edit version and waits 700 ms after the last
   edit, serializing requests. Local edit version and persisted revision are
   intentionally separate counters.
3. The hook calls `frontend/src/notes.ts::updateNote`, which sends PATCH
   `/api/notes/{id}` with title/native JSON and the expected revision through the
   existing `http.ts` client.
4. `backend/app/main.py::update_note` receives `models.UpdateNote` validation,
   separates the revision from changed fields and calls `Database.update`.
5. `database.py::Database.update` begins an immediate transaction, checks image
   ownership and executes `UPDATE notes ... WHERE id=? AND revision=?`.
   A stale revision updates no rows and returns 409 without indexing stale text.
6. On success, it reads the new canonical row and calls
   `search.py::index_note(connection, row)` **on the same connection**.
   `extract_text` reads its native JSON; the projection upsert stores title,
   headings, body and the new revision. `note_search_update` updates FTS tokens.
7. Leaving `Database.connect` commits all changes together. Extraction/SQL/index
   failure instead rolls back the note, revision, projection and FTS together;
   the existing generic database error handler returns 503 for SQLite failures.
8. FastAPI returns the saved canonical note. `notes.updateNote` checks identity
   and revision progression. `useAutosave` acknowledges only the submitted local
   snapshot. Newer typing remains dirty and is sent next; it is never overwritten
   by an earlier response. **Saved now implies the search index committed too.**

Creating a blank note uses `Database.create` with the same indexing helper.
`TemplateStore.instantiate` has its own existing transaction, so it calls that
helper explicitly after creating the final canonical note/image rows. Deletion
uses the note-to-projection cascading FK and projection-to-FTS delete trigger.

### Searching the paragraph

An HTTP client calls `/api/search?q=enum`. `main.search_notes` validates the
envelope; `Database.search` begins one read snapshot. `search.search_notes` calls
`prepare_query` to produce the literal FTS expression `"enum"*`, binds it to
MATCH, counts results, selects BM25-ranked rows and builds breadcrumbs from
current folder metadata. The response contains bounded plain text, not a document
or HTML. M3 will supply the UI client; there is no frontend search call yet.

### Reloading the saved note

Existing `App.tsx` selection/load calls `notes.ts::getNote`, then
`main.get_note` → `Database.get`. SQLite's canonical native JSON is decoded and
returned, including the saved revision/metadata. `PersistentNote` passes it as
`KnowledgeEditor.initialDocument`; BlockNote reconstructs the formatted content.
The search projection is never used to reconstruct or save the document.

## 4. Decisions and tradeoffs

| Decision | Why selected; simpler alternatives; accepted cost/future effect |
| --- | --- |
| FTS5 plus ordinary projection | SQLite is already the persistence dependency and FTS5 supplies tokenization/prefixes/BM25. A `LIKE` scan of every JSON document would be shorter but would search metadata, parse poorly and scale badly. An external-content index avoids a second stored FTS content copy; projection integer IDs bridge UUID note IDs to FTS rowids. There are two derived logical tables, no service/job framework. |
| Explicit application helper plus projection triggers | JSON-to-text belongs in Python; the three small triggers only synchronize ordinary text with FTS. Directly maintaining both tables in every CRUD branch would duplicate synchronization SQL. This arrangement requires future note-write paths to call `index_note` inside their transaction. Template instantiation was identified and covered now. |
| Same transaction, synchronous indexing | A successful save cannot leave an old index, and stale writes cannot publish uncommitted text. Async/background indexing would reduce save work but introduce an eventual-consistency queue and failure handling. Accepted cost: extracting up to the document limit adds synchronous save latency; benchmark before optimizing. |
| Literal AND prefixes | Safe ordinary input is useful without teaching the FTS query language. Parameter binding alone does not prevent malformed MATCH expressions. Tokenization plus quoted tokens separates those concerns. No OR/NOT/phrase/fuzzy/substring syntax; technical punctuation splits words and emoji are not indexed search terms. |
| Exact title + weighted BM25 | Implements the approved relevance preference with a small ORDER BY and built-in ranker. A rigid four-bucket/custom scoring engine is unnecessary. Exact title is guaranteed first; other title/heading/body preferences remain weighted BM25, not rigid ordering across arbitrary documents. Raw scores are not user-facing percentages. |
| Current folder paths in one snapshot | Folder rename/move should immediately affect results. Storing paths in each index row would require descendant reindexing. Accepted cost: one folder metadata read per nonempty search, not loading every note document. Root paths are arrays `[]`; names containing slashes remain distinct. |
| Additive schema 5 and exclusive upgrade | Established `user_version` migration, individual DDL calls and backfill share a transaction. Canonical tables are not rebuilt. Exclusive profile locking through commit prevents an old backend from continuing to save without indexing. A shared-only migration would be unsafe; a new migration framework is unnecessary. Current-version backends still share a profile. Locks are cooperative/Linux-specific. |
| Explicit offline rebuild | Reuse trusted-profile validation and exclusive locking, replace derived objects in a transaction, then verify revisions/FKs/FTS. Automatic destructive repair at startup would hide corruption and make recovery harder to understand. Schema-5 missing objects refuse startup with a repair hint. Semantic staleness caused by external writes requires explicit rebuild; it is not scanned on every startup/query. |
| Plain snippets and disabled request logging | Snippets remain untrusted text for safe M3 React rendering. No HTML escaping/highlighting protocol is introduced now. GET is consistent with the approved endpoint, but query strings can be recorded by custom clients/tools; supported release/desktop logging avoids them and the docs cover direct Uvicorn. |
| Existing dependencies only | Standard Python `sqlite3` includes the engine interface; FTS5 availability is checked by real virtual-table creation. Current runtime is SQLite 3.46.1 with FTS5. A missing-module runtime fails clearly and rolls migration back. No Python/npm package pin, license or framework change is needed. |

## 5. Verification

All application-data tests use temporary SQLite profiles. No real notes appear
in fixtures, output, commits or screenshots. Existing browser fixtures block
non-loopback requests; a new backend test blocks outbound socket connection
functions while exercising create/reopen/search through ASGI.

Final results are recorded below after execution; no unexecuted test is a pass.

### Commands and outcomes

| Check | Outcome |
| --- | --- |
| `.venv/bin/python -m pytest -q` from `backend/` | **301 passed**, one existing Starlette/httpx test-client deprecation warning. Includes 73 new search/migration/rebuild cases. |
| `.venv/bin/python -m ruff check app tests` and `ruff format --check app tests` from `backend/` | **Passed**. |
| `npm run build` from `frontend/` with pinned Node 24.19.0 | **Passed**, TypeScript and Vite build. Existing large-chunk advisory remains; no dependency/UI change. |
| `npm run test:release` from `frontend/` | **9 Chromium journeys passed**. Existing editor/rapid-save, template/image, conflict, backup/restore, appearance/navigation and lifecycle regressions. |
| `CYRNAVA_E2E_RELEASE=1 node node_modules/@playwright/test/cli.js test --browser=firefox` from `frontend/` | **8 passed, 1 failed**. The existing Phase-1 clipboard journey stops at `browserContext.grantPermissions: Unknown permission: clipboard-read` (`workspace.spec.ts:645`), before clipboard/remainder assertions. This test harness permission is unsupported by Playwright Firefox; the same whole journey passed in Chromium. No full Firefox-suite pass is claimed. |
| Isolated real Uvicorn HTTP smoke on an ephemeral loopback port | **Passed**: create/search, update/remove old terms, stale revision returns 409 without indexing it, process restart preserves native JSON/results, offline CLI rebuild, restart/search again. Temporary profile removed. |
| `git diff --check` | **Passed**. |

### Backend coverage and corrections

- T-SEARCH-01–11, 14–16: title/body/headings/code/nested text, cross-folder paths,
  renames, successful edits, deletion, existing-note migration, malformed/literal
  queries, no outbound calls, rebuild preservation and stale-save exclusion.
- Real installed-editor fixtures cover every supported native block; additional
  cases cover split styled words, links, H1–H6, nested lists/toggles, checklists,
  code flags/IPs, Unicode/diacritics, image captions/names and ignored metadata.
- Ranking/limits/ties, no-store/error privacy, bounded snippets and unchanged
  canonical rows during search are checked.
- Injected indexing failures after the projection write roll back create, update
  and template instantiation. A recursive folder-delete failure restores note and
  search data. Four competing same-revision updates have exactly one indexed winner.
- Migration tests preserve deliberately indented JSON bytes and all canonical
  fields; duplicate startup, DDL collision, unavailable FTS5 and an old serving
  shared lock are covered. Existing schema-1/2/3 migration tests still pass.
- CLI subprocess tests repair missing, stale and inconsistent inverted indexes,
  preserve every canonical table, reject unsafe/missing paths/live profiles/old
  schemas, refuse invalid canonical/physical data and roll back a failed rebuild.
  Backup/restore supports 3/4/5; old backup bytes remain unchanged after upgrade.
- The existing route-surface test initially rejected the additional route, and
  historical migration expectations still referred to version 4. These were
  updated explicitly, not removed or weakened. Historical fixtures now genuinely
  omit newer search objects. Formatting/lint issues were corrected before the
  final checks. Inspection also corrected a lock-descriptor variable collision
  before exercising migrations.
- The extra full Firefox run exposed the existing Chromium-specific clipboard
  permission request above. No unrelated browser-test/product change was made.
  Firefox's clipboard portion and later assertions in that journey remain
  unverified here; its other eight journeys, including mixed content, rapid edits,
  restart, images/templates and lifecycle, passed with this backend.

### Not claimed

T-SEARCH-12/13 (clicking search results and preserving unsaved edits during that
new transition) require M3 and have not been implemented or executed. Existing
navigation/autosave regression passes do not substitute for those future tests.
No 100/1,000/10,000-note benchmark, physical power-loss/disk-full campaign, fresh
Ubuntu installation, private-profile migration, normal-profile desktop dispatch,
or installed-release update was performed. These results are not whole-feature
release approval.

## 6. Risks and intentionally deferred work

- Search shows **committed** content. A draft still typing/uploading is not indexed
  until save succeeds. Frontend debouncing, stale response handling, cancellation,
  selected-result navigation and editor flush guards are M3 work.
- Backfill/rebuild are synchronous and startup time depends on saved data size.
  FTS count, folder metadata reads and result ranking have not been benchmarked at
  target scale; no latency target is claimed. M4 should measure before tuning.
- Missing search schema is detected on startup; arbitrary semantic staleness from
  external SQL edits is not automatically detected or repaired. Supported app
  writes stay atomic. Run offline rebuild if inconsistency is suspected.
- Rebuild requires a healthy canonical profile, including images/templates. It
  cannot promise to repair physical SQLite damage. Retain verified backups and
  never treat an index rebuild as restoration of missing source data.
- Note text also exists in derived index data and retained SQLite pages/backups.
  Everything remains local/private and unencrypted under the existing model;
  logical deletion is not secure erasure. No new network/execution path is added.
- Locks cover cooperating Linux processes only. Stop external tools/older
  noncooperating writers. Schema 5 has no downgrade; keep a pre-upgrade backup.
- Image captions/names are searchable, not image pixels/OCR. Template catalogs,
  formatting metadata and URL targets are intentionally not note-search text.
- No known backend M2 correctness defect remains after the passing checks.
  Pending frontend/benchmark/release work and unchanged dependency warnings must
  not be represented as completed F-09 functionality.

## 7. Owner review / manual verification

1. Review `search.py`, especially the derived-vs-canonical boundary and quoted FTS
   terms; compare `Database.update` and `TemplateStore.instantiate` commit points.
2. Follow the isolated manual API procedure in [docs/search.md](docs/search.md).
   Check `enum`, a title, heading and code term; restart and verify unchanged JSON.
3. On synthetic data, rename/edit/delete and repeat search. Stale PATCH revision
   should return 409 with the winning content still searchable.
4. Stop that test backend, rebuild the temporary profile, restart, repeat search
   and verify formatting. Running rebuild during serving must refuse.
5. Before any everyday upgrade, retain a verified pre-schema-5 backup and stop
   every backend. Review this milestone before installing it into daily use.

## 8. Suggested Git change

`feat(search): add transactional FTS5 backend search and offline index rebuild`

Commit summary: add schema-5 derived indexing/backfill, native text extraction,
bounded search API, atomic note/template synchronization and revision protection,
offline rebuild/backup compatibility, tests and operating documentation.

No commit, push, tag or publication has been made. **Stop at M2 for review.**
