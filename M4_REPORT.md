# ENGAGE M4 engineering report

## A. Implementation summary

M4 adds local PNG/JPEG/WebP image persistence through clipboard paste and BlockNote's image file selector. SQLite owns metadata and note relationships; generated files live in the existing application data directory. Notes retain native BlockNote JSON and stable `/api/assets/{UUID}` references. There are exactly two new routes, no new frontend package, and one pinned backend dependency: Pillow 13.0.0.

The implementation and automated checks are complete. Real browser clipboard insertion, all three file-selector formats, navigation, refresh, and a confirmed frontend/backend restart worked. **Full owner acceptance remains pending:** OS screenshot-tool capture and a physically disconnected-network run were not performed. Invalid uploads and lifecycle deletion were exercised against the running API, rather than through every GUI step. See `M4_VERIFICATION.md` for the precise distinction and full reproduction procedure. No M5 work, commit, push or tag was performed.

### Reconnaissance and prerequisites

The working tree was clean at `673a3c8` (`feat(m3) Add filetree and nested structures`). Actual code used schema version 2, a dedicated `KnowledgeEditor`, 700 ms debounced serial autosave, local snapshot acknowledgements, revision compare-and-swap, guarded navigation with `flush()`, and beforeunload protection. These essential editing/save prerequisites were present; there was no need to implement missing M3 work. This is an audit of M4 prerequisites, not a claim about unspecified M3 features.

Installed BlockNote 0.56.0 source was examined: `BlockNoteEditorOptions.uploadFile`, `pasteHandler`, core `handleFileInsertion`, React `UploadTab` and `FilePanel`. The public upload hook returns a URL; the selector applies it to the original block. The default clipboard/drop implementation fire-and-forgets upload rejection. Consequently M4 catches clipboard failures in the public paste hook and disables optional file drops. The picker uses BlockNote's existing `UploadTab`; remote embedding is removed from that panel.

## B. File change report

Paths below are repository-relative. Existing files outside this inventory were preserved.

| File | Responsibility, dependencies, and reason for change |
| --- | --- |
| `.gitignore` | Adds the `assets/` directory guard. Secondary protection; runtime rejects storage within this checkout. |
| `README.md` | Current Ubuntu install/upgrade, image workflows, limits, lifecycle and local operation. Depends on the actual routes and environment settings. |
| `M4_REPORT.md` | This architecture, change inventory and tradeoff record. |
| `M4_VERIFICATION.md` | Executed checks and reproducible owner acceptance steps; distinguishes automated, browser and human-only evidence. |
| `backend/requirements.in` | Adds direct Pillow 13.0.0 pin for real image decoding. |
| `backend/requirements.txt` | Adds the same resolved Pillow pin; no transitive Python or existing package version changes. |
| `backend/app/assets.py` | New `validate_image` and `AssetStore`: Pillow validation, generated safe filenames, private writes, retrieval, metadata transaction, reconciliation. Uses existing `Database`, Python filesystem/UUID/logging modules. |
| `backend/app/database.py` | Additive version-3 assets table/index/FK and `_check_images` ownership validation in existing note transactions. Uses SQLite/JSON only; note/folder schema remains unchanged. |
| `backend/app/models.py` | Adds image block support and canonical local URL validation to existing native-document validator. Empty placeholders remain valid. Uses existing Pydantic/stdlib. |
| `backend/app/main.py` | Initializes the store/cleanup; raw upload and image GET routes; bounded streaming, two upload slots, thread-pool decode/write; cleanup after existing note/folder deletion. Uses existing FastAPI/Starlette plus `AssetStore`. |
| `backend/tests/test_assets.py` | New temporary-data image, validation, filesystem failure, ownership, migration, restart and cleanup tests. Uses existing pytest/TestClient and Pillow-generated fixtures. |
| `backend/tests/test_health.py` | Extends explicit route-surface expectation by exactly the asset POST/GET routes. |
| `backend/tests/test_library.py` | Existing M1 migration expectation now advances to current schema version 3; remaining hierarchy/deletion tests retained. |
| `backend/tests/test_notes.py` | Current/future schema expectations become 3/4. Replaces former blanket image rejection with unsupported video rejection; M4 now supports images. Other note/concurrency tests retained. |
| `frontend/src/assets.ts` | New typed `uploadImage` HTTP boundary: file prechecks, raw File body, local URL, timeout/abort, server errors, response ownership/reference validation. Uses browser fetch and existing `ApiError`. |
| `frontend/src/assets.test.ts` | Upload request/response, unsupported/oversize/empty files, backend failure and invalid URL/owner tests using existing Vitest. |
| `frontend/src/components/KnowledgeEditor.tsx` | Enables core image block, configures upload hook, local-only picker, caught clipboard insertion, upload status/error/missing-image feedback and lifetime abort. Exposes editor-neutral `flushUploads()`. Only this adapter understands BlockNote image operations. |
| `frontend/src/components/KnowledgeEditor.test.tsx` | Tests adapter hydration/snapshots, clipboard and picker-hook integration, image order, failure feedback, pending upload drain, abort across note replacement, missing image and optional drop rejection. Public editor boundary is mocked; actual browser tests complement it. |
| `frontend/src/components/PersistentNote.tsx` | Existing navigation handle now awaits adapter uploads before ordinary autosave flush. Passes note identity to adapter. Depends on existing autosave and adapter interface, without understanding image blocks. |
| `frontend/src/components/PersistentNote.test.tsx` | New orchestration tests: saves wait for upload completion; failed pending uploads block navigation. Uses existing Vitest/Testing Library. |
| `frontend/src/App.tsx` | Updates the visible milestone label to M4. Navigation implementation remains unchanged. |
| `frontend/src/App.test.tsx` | Adds full UI/autosave-client-boundary test retaining native image position/caption/width/formatting through save and reload. Uses existing editor mock and API mocks. |

The preview `../engage-m4-preview.png` is a review artifact outside the Git repository, not an uploaded application image. Temporary fixtures, controllers and acceptance snapshots are outside the repository in the enclosing task's `work/` and `/tmp/engage-m4-acceptance/`.

## C. Actual execution flows

### Flow 1: clipboard screenshot → durable note

1. The browser delivers a clipboard event to BlockNote. `KnowledgeEditor.tsx` configures `pasteHandler`; non-file text follows `defaultPasteHandler()` unchanged.
2. The file path inserts an empty core image block after the cursor's block using public `editor.insertBlocks`. It calls the configured `editor.uploadFile(file, block.id)` and catches rejection. Multiple pasted files retain their order.
3. `uploadFile` captures this editor's `noteId` and abort signal, records the pending promise, and calls `uploadImage` in `assets.ts`. Visible upload state and a beforeunload warning cover the operation.
4. `uploadImage` prechecks format/size and sends `POST /api/assets?note_id=<UUID>` with raw File bytes and the exact MIME header. It has a 30-second timeout and rejects nonlocal/wrong-owner response references.
5. `main.py:upload_asset` validates the UUID, permits two concurrent body/decode operations, reads at most 10 MiB with a 30-second body deadline, then calls `AssetStore.upload` in Starlette's existing thread pool.
6. `assets.py:validate_image` restricts decoders to PNG/JPEG/WebP, compares actual format to MIME, checks dimensions/pixels/frame count, verifies and fully decodes, and re-encodes pixels without original metadata/trailers. Stored bytes also have a 10 MiB limit.
7. `AssetStore.upload` begins an SQLite `BEGIN IMMEDIATE` transaction, checks the note exists, generates a UUID, exclusively creates a private generated file and fsyncs it, inserts metadata using parameters, then commits. The transaction serializes association against note deletion/cleanup. File/write/metadata failure rolls back and removes this operation's new file when possible.
8. The route returns `{id,note_id,mime_type,byte_size,url}`. Absolute paths and original filenames are absent. The adapter applies the returned URL with `editor.updateBlock` to that original block only. The picker reaches the same hook through installed `UploadTab` and applies its returned URL itself.
9. `BlockNoteView.onChange` emits a structured clone of native `editor.document`. `PersistentNote` passes that to unchanged `useAutosave.changeDocument`.
10. Existing `useAutosave` debounces then calls `notes.ts:updateNote`; `http.ts:request` sends PATCH with the expected note revision. `main.py:update_note` validates native JSON; `Database.update` verifies image ownership and atomically updates `WHERE id=? AND revision=?`, increments revision and commits.
11. The autosave response acknowledges only its submitted local snapshot. Newer typing stays dirty and is saved next. Older responses never reset the live document. The existing status becomes Saved only when that latest snapshot is acknowledged.

If the user immediately navigates, `App.perform` uses `PersistentNote`'s existing handle. It first awaits adapter `flushUploads()`, yields one event-loop turn for BlockNote's returned-URL update/change event, rechecks pending uploads, then drains `useAutosave.flush()`. Failed in-flight uploads or saves block that transition. Read-only transition state prevents starting more edits. Abrupt unmount aborts the old editor's request; even a late response cannot insert into a different editor instance.

### Flow 2: reload → image retrieval

`App` discovers the preferred note through `getTree`/`getNote` → `notes.ts`/`http.ts` GET → `main.py:get_note` → `Database.get` parses native JSON from SQLite → the newly mounted `KnowledgeEditor` supplies it as `initialContent` → core image nodes render their saved URLs → browser requests the same-origin `/api/assets/{UUID}` through the existing Vite proxy → `main.py:get_asset` → `AssetStore.retrieve` loads metadata, validates the generated basename/approved directory, refuses symlinks, reads bounded bytes, checks size and allowlisted MIME → a typed response with nosniff, sandbox CSP, no-store and inline disposition → the browser decodes the image in its original block position. No upload is repeated on reopen.

A missing metadata row/file produces 404. `KnowledgeEditor` captures the image's error event and displays an alert without removing its document reference or preventing surrounding text editing.

### Flow 3: invalid upload

File selection → BlockNote `UploadTab` → adapter `uploadFile` → `uploadImage` → POST → `upload_asset`/`validate_image` → 422 for malformed, unsupported or mismatched content (413 for an oversized request) → HTTP client throws the safe server message → adapter shows a persistent alert; `UploadTab` also shows its own failure indication. No permanent URL is returned or inserted, and existing document blocks remain intact. Clipboard failure is caught equivalently and may retain an empty retry placeholder. Client-side type/size failures stop before HTTP. Connection/timeout errors tell the user to check the local backend and select/paste again.

## D. Engineering decisions and tradeoffs

| Problem | Choice and simpler alternatives | Reason, accepted tradeoff and future limit |
| --- | --- | --- |
| Identification and paths | UUIDv4, filename equal to UUID, relative `disk_path`; rather than original filenames or user-provided paths. | Opaque stable URLs, exclusive creation and no traversal. File format is metadata, not an extension; inspecting files manually needs SQLite. No new content-hash deduplication. |
| Data location | `assets/` beside existing XDG SQLite database; not repo files or DB BLOBs. | Preserves existing local data policy and separates large bytes. Backups must eventually include both DB and directory; backup/export is outside M4. |
| Real validation | Pinned Pillow 13.0.0; rather than suffix/MIME checks or hand-written image parsers. | Existing dependencies cannot decode/verify these formats. Restricted decode plus full load and re-encode excludes active formats/metadata/trailers. Adds one native-decoder dependency that must receive security updates. [Pinned release](https://pypi.org/project/pillow/13.0.0/). No frontend dependency/version change. |
| Limits | 10 MiB incoming and encoded; 8192/side; 20M pixels; static frames; two upload slots; bounded body deadline. | Simple explicit memory/CPU bounds suitable for local screenshots. Larger or animated images must be reduced before insertion. Not a process-isolated image sandbox or a global disk quota. |
| Upload transport | Raw binary POST with note ID query and MIME header; not multipart. | A single file needs no multipart fields/parser. `Request.stream()` enforces the body cap before accumulating arbitrary data; avoids another dependency and multipart spooling. This is the explicit deviation from a conventional multipart implementation, allowed by “where appropriate.” |
| Filesystem/DB consistency | Write/fsync file before committing metadata within the ownership transaction; then return URL. | Metadata should never intentionally commit before a complete file exists. Unlike storing BLOBs, SQLite cannot roll back filesystem operations. Failed writes/metadata clean up immediately; process death can leave an unowned file, removed on startup. Full power-loss atomicity and directory fsync are deferred. |
| Upload before autosave | Associate immediately with the live note; keep owned assets even when absent from saved JSON. | Deleting “unreferenced” assets on every save could delete a second upload or a failed-save draft. Conservative retention protects those references. Abandoned/removed images consume space until note deletion; no background worker or arbitrary expiry window. |
| Deletion | `assets.note_id` FK CASCADE metadata, existing note/folder transaction; unowned-file reconciliation after deletion/startup under the same SQLite write lock used by uploads. | Avoids file deletion before a potentially rolled-back note deletion. Cleanup errors log and retry at startup rather than misreport a committed note deletion as failed. Temporary inaccessible storage may retain files longer. |
| Native references | Keep `format_version=1`, add core image JSON with canonical local URLs and ownership check. | Existing note storage/autosave remains authoritative and unchanged. Empty placeholders are valid. Copying image JSON across notes is rejected; users re-upload into the destination. Future shared assets need an explicit relationship model. |
| Editor isolation | Public `uploadFile`, core image block, upload-only `FilePanel`, public paste hook. | Navigation sees only `flushUploads`, never BlockNote internals. Existing default paste rejection handling required the small adapter override. Optional file drops are disabled instead of adding another insertion system. |
| Save ordering | Await uploads, allow URL application/change event, then existing serial autosave. | Reuses existing revision and stale-ack safeguards instead of a second note save path. Upload errors are separate from document save errors. Beforeunload is advisory; force quit can still lose unfinished work. |
| Normalized images | Re-encode the same raster format with metadata stripped. | Safer served bytes and no preserved metadata payloads. JPEG is recompressed and EXIF/orientation/profile metadata is removed; this is a note-image feature, not a forensic-original archive. |

Pending or abandoned uploads can be identified without another table or endpoint using a read-only query (this includes legitimate pending saves, so it is **not** an instruction to delete them):

```sql
SELECT a.id, a.note_id
FROM assets AS a JOIN notes AS n ON n.id = a.note_id
WHERE NOT EXISTS (
  SELECT 1 FROM json_tree(n.document_json) AS j
  WHERE j.key = 'url' AND j.value = '/api/assets/' || a.id
);
```

In M4, deleting the owning note manages all of its assets, including these abandoned uploads. Fine-grained removal is deliberately deferred.

## E. Test report

Final executed results: **72 backend tests passed; 72 frontend tests passed across 9 files; Ruff, ESLint, TypeScript/Vite build and pip dependency checks passed.** `git diff --check` is recorded in verification. Backend data is temporary; no test uses the default user-data path.

Coverage includes all three decoders, metadata/unique IDs, retrieval/MIME/headers, invalid/mislabeled/truncated/animated/oversize/excess-dimension inputs, nonexistent IDs/notes, traversal and symlink rejection, write/fsync/metadata failures, exclusive-create collisions, reconnect/restart, additive migration preserving records, deletion/recursive deletion, deferred cleanup retry, native JSON/ownership/revision regression, upload client/hook/clipboard paths, ordered snapshots, pending-upload flush, failure/unmount isolation, missing image feedback, autosave/reload, and existing note/folder/editor/health/concurrency behavior.

Real browser and running-server checks verified four inline images (clipboard PNG plus selector JPEG/WebP/PNG), natural image widths, Saved status, headings/bold/paragraphs, navigation, refresh, actual server stop/restart and exact record preservation. Missing-file feedback was observed and the temporary file restored. Running API checks rejected invalid images without modifying notes; deleted a temporary saved image note and its file while unrelated assets remained.

Initial failures and corrections: old image-rejection test updated to unsupported video; upload-only FilePanel configured using the installed object-shaped tabs API rather than strings; adapter mock exports updated; imperative-flush dependency fixed for ESLint; Ruff imports/line lengths corrected. These failures were followed by passing checks. An initial acceptance runner import needed the backend PYTHONPATH before startup; no application change was needed.

Known warnings remain: Starlette's existing HTTPX TestClient deprecation, Vite's existing large bundle warning, and a pip cache permission warning (pip check still reports no broken requirements). No package upgrades or warning suppression were introduced for these.

Not executed: OS screenshot-tool capture itself, physical internet disconnection, computer reboot/power-loss tests, comprehensive browser/platform clipboard matrix, manual invalid/oversize file-selector UI cases, and sustained resource-exhaustion testing. Some frontend tests mock BlockNote's public boundary; they do not establish native GUI behavior by themselves. See the verification record before declaring full M4 acceptance.

## F. Security assessment

Only allowlisted static raster decoders are opened; actual content must match declared MIME. Extensions are unused, SVG/HTML/PDF/video/GIF are rejected. Files are fully decoded and normalized, with explicit encoded and decoded limits. The server restricts simultaneous uploads and body time/size. Retrieval requires a UUID plus existing metadata, identical generated basename, approved resolved directory, no symlink and expected bounded byte count. Original filenames/absolute paths never appear in API responses. SQL values are parameterized; foreign keys are enabled on every connection.

Image responses use allowlisted MIME, `X-Content-Type-Options: nosniff`, `Content-Security-Policy: default-src 'none'; sandbox`, `Cache-Control: no-store`, and inline disposition. The frontend keeps its existing same-origin CSP and proxy. Remote embedding is absent; documents reject remote/data/blob image sources as canonical URLs. Existing local links are not executed as note content. Loopback defaults and no-CORS policy are unchanged. New files/directories use 0600/0700; assets are outside Git plus ignored defensively.

Residual risks: a decoder vulnerability still requires patching; local data is unencrypted and readable by the same OS user; users who can modify the database/files directly are outside this boundary; no authentication or hostile remote-service hardening is added. Large valid images still use bounded but material CPU/memory. File contents are verified at upload, not cryptographically revalidated on every GET. OS/file permissions and disk integrity remain relevant. Do not expose this development backend to a network.

## G. Technical debt and acceptance boundaries

No known implementation defect blocks the tested M4 paths. Owner acceptance is still open for the human-only/unexecuted cases above; this report does not declare those passed.

Accepted M4 limits: owned but unreferenced images persist until note deletion; cleanup is best effort with startup retry; uploaded JPEGs are recompressed and originals are not archived; image blocks cannot be shared across notes; optional file drops are disabled; image GET buffers up to 10 MiB and does not implement ranges/cache optimization; cleanup scans the asset directory under a write lock; upload retries require selecting/pasting again. A failed paste can leave an empty placeholder. A missing file produces an alert, not automatic restoration.

Deferred reliability work: per-asset garbage collection that understands drafts, crash/power-loss durability improvements, backup/export coordination, resumable uploads, persistent unsaved drafts, storage quotas and broader accessibility/performance/browser testing. These are future decisions, not authorization to start M5/M6.

## H. Git summary

Recommended commit:

```text
feat: persist local note images with validated uploads and safe lifecycle handling
```

Commit source, dependency pins, tests and these documents after owner review. Do not commit `.venv`, `node_modules`, `dist`, caches, SQLite files, runtime `assets/`, uploaded notes/screenshots or acceptance data. The preview is outside this repository. No commit, push, tag or publication has been performed. Stop at M4 for architectural review.
