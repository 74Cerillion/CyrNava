# ENGAGE v0.1.0 — BlockNote persistence compatibility repair

Status: source repair implemented; owner-run targeted Chromium test and release suite passed, supported by shared passing result and static-release artifacts. The owner-run unrestricted backend suite also passed all 170 tests. Installed-desktop acceptance remains pending; full acceptance is not yet claimed.

## A. Root cause analysis

In the original `backend/app/models.py::validate_document`, heading properties were checked against `(1, 2, 3)`. The actual installed BlockNote 0.56.0 heading specification defaults to levels 1–6 and optional `isToggleable`. The default slash menu also exposes H4–H6. `UpdateNote.document_json` ran that validator through Pydantic's `AfterValidator`, so valid H4–H6 documents raised a validation error before any SQL update; FastAPI returned HTTP 422. Serialization and SQLite were not responsible.

The eight original allowed block types match the adapter's actual configuration. The broader defect was maintaining a separate handwritten backend editor definition without checking it against the installed schema. Other property/style fields were insufficiently checked, while additional metadata was already capable of passing through storage.

Inventory came from the adapter schema and the installed `getDefaultSlashMenuItems` implementation, not the supplied feature list. There are eight block types, 17 slash commands and seven style types. Toggle-heading commands are heading properties, not separate block types. Tables, divider, toggle-list, video, audio and generic file blocks are excluded by the adapter.

An additional exposed-action defect was found: the slash menu offered Emoji while `BlockNoteView` disabled its picker. The picker is now enabled. Its already-installed emoji-mart implementation dynamically imports bundled local data; no new dependency or external runtime service is introduced.

## B. Architecture and execution flow

1. `components/editorSchema.ts` defines the same BlockNote schema formerly embedded in `KnowledgeEditor.tsx`. It remains inside the adapter boundary.
2. `KnowledgeEditor` applies the saved JSON as initial content once per mount. `BlockNoteView.onChange` sends a structured clone of `editor.document` as the application's generic `NoteDocument`.
3. `PersistentNote` passes the snapshot to `useAutosave.changeDocument`. The unchanged saver debounces 700 ms, assigns local edit generations, serializes requests and retains newer edits while an older request is pending.
4. `notes.updateNote` and `http.request` serialize title/document plus the expected database revision into a PATCH.
5. `main.update_note` receives `UpdateNote`; its Pydantic `AfterValidator` calls `documents.validate_document`. That function uses `document_format_v1.json` for known block content kinds, property scalar types/enums and styles, plus structural/security/resource checks.
6. `Database.update` performs the existing recursive image-ownership check and atomic expected-revision SQL update inside a transaction. Native JSON is stored as JSON text without lossy conversion.
7. The response contains unchanged JSON and the incremented revision. The client validates the acknowledgement; autosave acknowledges only that local snapshot. A response cannot replace a newer draft or mark it saved.
8. Reload reverses the flow: `App` discovers/selects the note, `getNote` retrieves native JSON, and a fresh `KnowledgeEditor` reconstructs it with the same schema.

No database operation or autosave production logic changed. Database schema remains 3 and document format remains 1. This corrects acceptance of an existing representation, so no migration is necessary.

The contract is a checked-in snapshot of the actual installed adapter schema, not a request-supplied schema. The frontend test detects drift. `npm run document:contract` regenerates it after a reviewed editor change. New blocks using existing inline/plain/none shapes and scalar properties generally need only a contract update; new content shapes or resource types still need explicit validation/rendering/security support. This avoids a Python branch for each heading/formatting option without accepting arbitrary unsupported documents.

Validation retains the 1 MiB UTF-8 document limit, 5,000 blocks, 32 block-nesting levels, unique supplied IDs and local image URL/ownership checks. It adds bounded metadata JSON, finite numbers, strict known-property/style types and safe link schemes. Additional metadata/properties are preserved by the API under those bounds. An unmodified editor cannot render arbitrary custom metadata; only native fields supported by its schema have an editor reconstruction guarantee.

Validation responses now omit Pydantic input/context fields, which could echo an entire rejected document. The HTTP client displays safe locations and reasons through the existing Save Error/Retry interface.

## C. Files changed

| File | Responsibility, dependencies and reason |
| --- | --- |
| `backend/app/models.py` | Existing Pydantic request envelopes retain `AfterValidator`; import the document validator rather than duplicating editor rules. |
| `backend/app/documents.py` | New stdlib validator interprets the contract and enforces JSON/structure/security/resource limits without transforming documents. |
| `backend/app/document_format_v1.json` | Generated snapshot of installed BlockNote 0.56.0 blocks, props, inline content and styles; packaged with the backend by the existing installer. |
| `backend/app/main.py` | Uses existing FastAPI validation exceptions to return useful 422 diagnostics without raw input/context. |
| `backend/tests/test_document_compatibility.py` | Real API create/update/get tests for native fixtures, every enum value, invalid input, metadata preservation, uploaded image, restart and backup/restore. Uses temporary SQLite profiles. |
| `backend/tests/fixtures/blocknote_v1.json` | Synthetic native JSON emitted by the actual editor: 19 individual documents, a mixed document and the actual 17-item slash inventory. Contains no user data. |
| `frontend/src/components/editorSchema.ts` | Moves the unchanged schema to a small adapter-owned module that runtime code, tests and the contract exporter share. Depends only on existing BlockNote core. |
| `frontend/src/components/KnowledgeEditor.tsx` | Imports that schema; enables the already-exposed emoji picker. Upload isolation, JSON snapshot and lifecycle handling remain intact. |
| `frontend/src/components/editorCompatibility.test.ts` | Uses real BlockNote: schema/contract equality, native reconstruction, every slash action in insert/update contexts, bundled emoji action, enums and formatting changes. |
| `frontend/src/components/editorRoundTrip.test.tsx` | Mounts the real React/Mantine/BlockNote adapter in JSDOM; verifies rendered formatting, nesting, toggles, checklist edits, image reference and remount. Layout APIs alone are stubbed. |
| `frontend/src/hooks/useAutosave.test.tsx` | Adds H4→H6/toggle/code edits while an older formatted save is in flight; verifies the latest document and revision sequencing. |
| `frontend/src/http.ts` | Displays structured validation locations/reasons while ignoring input fields. Uses the existing client/error type. |
| `frontend/src/notes.test.ts` | Verifies useful 422 reporting without displaying submitted content. |
| `frontend/e2e/workspace.spec.ts` | Adds a temporary-profile Chromium journey for mixed content, all slash actions, local upload, delayed acknowledgements and backend restart. Original journeys preserved. |
| `frontend/package.json` | Adds the offline `document:contract` development script only; versions/dependencies unchanged. |
| `frontend/scripts/export-document-contract.mjs` | Reads the actual adapter schema and installed package version and writes the reviewable backend contract. Uses Node stdlib. |
| `frontend/vite.config.ts` | Test-only dependency transforms load bundled emoji JSON consistently and avoid duplicate BlockNote module registration. Production server configuration unchanged. |
| `docs/architecture.md` | Corrects the validation responsibility description and links the explicit compatibility boundary. |
| `docs/document-format.md` | Documents native format, supported shapes, limits, extension policy, normalization and contract update procedure. |
| `BLOCKNOTE_COMPATIBILITY_REPORT.md` | This requested report and acceptance record. |

No dependency versions, requirements, lockfile, SQL schema, database code or production autosave code changed.

## D. Compatibility matrix

“API pass” means native JSON survived actual FastAPI POST/PATCH/GET exactly, including the relevant mixed/restart coverage. “Native” uses the real BlockNote editor, not the older mocked adapter tests. “DOM” uses the real React adapter in JSDOM, not Chromium layout or image decoding. The owner-run corrected Chromium journey and full release suite passed.

| Exposed capability | API persistence | Native editor / DOM coverage |
| --- | --- | --- |
| Paragraph | Pass | Native + DOM |
| Heading 1 | Pass | Native + DOM |
| Heading 2 | Pass | Native + DOM |
| Heading 3 | Pass | Native + DOM |
| Heading 4 | Pass | Native + DOM |
| Heading 5 | Pass | Native + DOM |
| Heading 6 | Pass | Native + DOM |
| Quote | Pass | Native + DOM |
| Numbered list, including nondefault start | Pass | Native; nested list DOM |
| Bulleted list | Pass | Native + nested DOM |
| Checklist checked/unchecked | Pass | Native + actual DOM edit/remount |
| Code block, language, multiline Unicode | Pass | Native + DOM; never executed |
| Toggle Heading 1 | Pass | Native + DOM |
| Toggle Heading 2 | Pass | Native + DOM |
| Toggle Heading 3 | Pass | Native + DOM interaction/remount |
| Image, name, caption, preview width/alignment | Pass, actual uploaded PNG and bytes after restart | Native + DOM URL/metadata; Chromium upload/decoding/restart passed |
| Emoji slash action / Unicode insertion | Pass as native text | Actual bundled picker action + native reconstruction; Unicode DOM |
| Bold | Pass | Native command + DOM |
| Italic | Pass | Native command + DOM |
| Underline | Pass | Native command + DOM |
| Strikethrough | Pass | Native command + DOM |
| Inline code | Pass | Native + DOM |
| Text color | Pass | Native field/command reconstruction |
| Background color | Pass | Native field/command reconstruction |
| Links | Pass; unsafe schemes rejected | Native command + DOM link |
| Left/center/right/justify alignment | Pass for every contract enum value | Native for every enum value |
| Nested lists/blocks/toggle children | Pass, including restart | Native + DOM |
| Stable IDs and supported block properties | Pass | Native reconstruction; formatting retains identity |
| Additional API metadata/unknown properties | Pass, bounded and unchanged | API-only extension storage; arbitrary custom rendering is not promised |

The schema also accepts toggle-heading properties at levels 4–6; those native cases were tested even though only three toggle-heading slash entries are exposed. Unsupported table/divider/toggle-list/video/audio/file types remain disabled.

Native normalization: partial initial blocks may receive default props/IDs. Image blocks have an undefined JavaScript content property that is absent in serialized JSON. All three existing user documents reconstruct to exactly equivalent serialized native JSON. Inline code is tested in a separate segment because BlockNote's code mark excludes combinations with the other marks. Toggle expanded/collapsed state is per-browser local view state; toggle identity and children are document data.

## E. Tests executed and outcomes

- Backend final owner-run full suite: **170 passed, one warning in 6.96 seconds**, confirmed by terminal screenshot. This includes all 67 new API/contract tests and the six desktop tests previously blocked in this session. The warning is the existing Starlette TestClient deprecation of its httpx integration; no dependency change was made for this compatibility repair. The earlier sandbox run had 164 passes and six local-socket setup errors; the unrestricted run resolves that test gap.
- Frontend final full suite: **166 passed** in 12 files, including real editor actions/reconstruction/DOM and existing error, retry, navigation and concurrency tests.
- ESLint, TypeScript, production Vite build, Ruff check/format and `git diff --check`: passed. The existing large-main-chunk warning remains. Emoji data is split into local lazy chunks.
- `npm run document:contract`: executed successfully and checked against the installed adapter schema.
- Existing-data drill: established restore to a disposable temporary profile; all three notes GET→edit→PATCH→GET→backend restart→GET passed. Native serialized editor reconstruction passed for all three. Verified backup and original database/asset hashes remained intact.
- Chromium attempt inside this session: did not enter the test body; the pinned browser executable was absent. The fallback sandbox also refuses localhost sockets despite a network permission grant.
- Owner's regular terminal: three existing development browser journeys passed. The new journey reached all menu actions, saved/reloaded and restarted successfully, then failed a positional assertion: a newly inserted code block appeared before the original, so `.first()` selected the wrong block. Corrected to the original stable block ID and an exact API JSON assertion. The first corrected rerun then timed out with `/Image` inside the newly inserted code block: the test used a document-end shortcut that did not reliably leave code content. Replaced moving/positional cursor placement with a fixed plain-paragraph anchor for every slash action and rapid-edit setup; added named slash-command steps, a bounded menu click and a bounded first-save acknowledgement assertion. The next owner run isolated the same Image step in 23 seconds: clicking the fixed paragraph container still left the code-block caret active. The helper now uses the standard browser Selection/Range API to place the caret at the anchor text end, verifies the selected block, then uses a real Enter key and verifies an empty paragraph before typing. All content changes and menu actions still use the actual editor UI. No production change for these browser-harness corrections. ESLint and discovery of all four browser tests pass after this correction; The owner subsequently confirmed a passing run. Shared `.last-run.json` records passed with no failures, and artifacts from all three original journeys show the built frontend served by FastAPI (release mode). Together with the chained command, this supports the corrected targeted development test and all four release journeys passing.

Normal commands, from the indicated directories:

~~~bash
# backend
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .

# frontend
npm run document:contract
npm test
npm run lint
npm run build
npx playwright install chromium
npm run test:e2e
npm run test:release
~~~

Execution environment note: granting the existing profile lock-file path triggered a command-runner filesystem-mount bug. Tests were run through the available fallback runtime. That sandbox drops asyncio cross-thread socket wakeups, so an uncommitted test-only `work/compat-test-runtime/sitecustomize.py` added periodic event-loop wakeups via `PYTHONPATH`; it is outside the repository and is never installed. This allowed in-process API tests, but did not grant TCP socket creation. Production code contains no workaround. Initial short timeouts were corrected after observing the slower fallback execution. Other test-harness corrections handled Node JSON loading, missing JSDOM layout APIs and the library's distinct-block selection API.

## F. Data safety

Active installation configuration identifies `$HOME/.local/share/engage/engage.sqlite3` and `$HOME/.local/share/engage/assets/`. There are three existing notes and 20 registered assets.

The owner stopped ENGAGE before backup. The established `app.backup.create_backup` copy/validation/manifest procedure created a private verified backup outside every Git repository at:

~~~text
/home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/work/private-backups/pre-blocknote-compatibility-20261025
~~~

The source's existing lock file was opened read-only with the same exclusive Linux flock because the sandbox blocked its ordinary read/write open. The backup's validation, copy, hash manifest and independent revalidation remained the established implementation. No production backup code changed. The backup is not encrypted and is retained privately outside the repository.

All 21 database/registered-asset SHA-256 values were compared with the manifest after implementation and are unchanged. Existing-note write/restart tests used only a disposable restored copy, which was removed after the test. No live note records, revisions, folder relationships, asset files or backups were overwritten. Schema 3 and document format 1 remain unchanged; there is no migration.

## G. Remaining risks and acceptance steps

The source fix is implemented, but full desktop acceptance is pending installation of this source into the desktop application's separate snapshot. The current installed release was not silently patched.

After tests pass, stop ENGAGE, run the existing installer from the source root:

~~~bash
nvm use
python3.12 desktop/install.py
~~~

Then launch the desktop icon. If the original failed draft remains in an old browser tab, use Retry save against the updated backend and wait for Saved before refreshing that tab. Refresh only after the draft is confirmed saved; this loads the updated frontend/picker too. Verify H4–H6, mixed formatting, reload and backend restart from the actual desktop application.

Unknown future types/shapes are deliberately rejected until reviewed; arbitrary custom metadata has API preservation, not an automatic rendering guarantee. No authentication, network exposure, new product features, schema migrations or external services were introduced. The browser-local toggle expansion state is library behavior rather than SQLite data. Existing warning/desktop sandbox limitations are recorded rather than hidden.

## H. Git commit

Recommended message: `Fix native BlockNote document persistence compatibility`.

No commit, push, tag or release was created. All changes are confined to this repair. Await owner review; no later milestone was started.
