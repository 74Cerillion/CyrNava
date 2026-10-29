# F-09 M3 — global search interface engineering report

Implementation date: 2026-10-29. Scope: approved M3, building on reviewed M2.

## 1. Outcome

Implemented the navigation-pane search control, 300 ms debounce, ranked result
cards with title/path/preview, safe text highlighting, keyboard/mouse activation,
loading/empty/error/retry/clear states, cancellation and stale-response protection.
Opening a result uses the existing upload/autosave/recovery guard, loads canonical
native JSON, refreshes folder metadata and selects/reveals its tree location.
The current note's editor is retained if a save/read fails or if its own result
is selected. Successful saves/library changes refresh the active query.

M3 is a review candidate, **not F-09 release approval**. M4 benchmarks, final
validation/release and the optional matching-section jump were not implemented.
No dependencies, backend application code, schema, native document format,
storage paths, license or installed desktop copy were changed during M3. No
private profile was opened or migrated. No commit, push, tag or publication occurred.

The checkout already contained the reviewed, uncommitted M2 changes. They remain
present and are documented separately in [F09_M2_REPORT.md](F09_M2_REPORT.md).
The files below describe the additional M3 work, not that entire combined diff.

## 2. Files created or modified for M3

| File | Responsibility, dependencies and reason |
| --- | --- |
| `frontend/src/search.ts` (new) | Typed M2 response contract and `searchNotes` API client. Reuses `http.ts` timeout/error/cancellation; URL-encodes query, requests 20 results with no-store and validates unknown JSON before exposing it. Preserves backend ordering. No editor/database imports. |
| `frontend/src/search.test.ts` (new) | Existing Vitest API-client tests: encoding, no-store, composed abort signal, valid/empty responses, backend order, HTTP/network/JSON failures, malformed envelopes/rows and bounded page size. Synthetic values only. |
| `frontend/src/components/GlobalSearch.tsx` (new) | Owns transient query/request/result/keyboard state and safe React `<mark>` text rendering. Depends on `searchNotes` and the existing `Icon`; reports only a note ID to App. Contains no BlockNote or persistence code. |
| `frontend/src/components/GlobalSearch.test.tsx` (new) | Existing Testing Library/Vitest fake-timer tests for 300 ms debounce, loading/empty/error/retry, paths/counts, safe snippets, arrows/Enter/Escape, locks/composition, cancellation, repeated queries, out-of-order responses and committed-change refresh. |
| `frontend/src/App.tsx` | Mounts search near the top of the sidebar, supplies a refresh counter and adds `openSearchNote`. The existing `perform` guard remains the only route into a different note; fresh reads complete before selection changes. Same-note activation preserves the current editor. |
| `frontend/src/App.test.tsx` | Adds mocked search client and navigation cases against the real App/PersistentNote/autosave boundary: canonical load/ancestors, queued saves, 409/503, same-note identity, deleted result/tree failures, draft recovery and refresh/focus preservation. Existing tests retained. |
| `frontend/src/components/Icon.tsx` | Adds one local magnifying-glass SVG path to the existing icon map. No icon package or remote asset. |
| `frontend/src/styles.css` | Adds scoped search input/card/path/snippet/selection/highlight styling, using existing palette tokens so Light/Dark/System/CyrNava inherit the same colors. Bounded scrolling and wrapping preserve the two-pane/mobile layout. |
| `frontend/e2e/search.spec.ts` (new) | Two focused Playwright journeys with the real built UI, FastAPI and SQLite. Each owns an ephemeral loopback server, copied release snapshot and temporary synthetic profile. Blocks non-loopback browser requests, checks native formatting/navigation/queued saves/failure retention and active-query autosave refresh; captures synthetic desktop/mobile views. |
| `README.md` | Describes the available M3 controls/safeguards, links the report/guide and keeps M4 explicitly pending. |
| `docs/search.md` | Adds actual user behavior, keyboard/focus rules, refresh/error/privacy limitations to the existing M2 API/upgrade/rebuild guide. |
| `docs/architecture.md` | Adds the real search/client boundary and request/navigation execution flow. Existing persistence/editor responsibilities remain intact. |
| `CHANGELOG.md` | Records M3 separately from M2 and identifies pending benchmarks/release work. |
| `F09_M3_REPORT.md` (new) | This review explanation, test record, limitations and suggested commit. |

## 3. Execution flow

### Query → local results

1. `GlobalSearch` receives input through `changeQuery`. A meaningful trimmed
   query change invalidates the old request generation, aborts its controller,
   discards previous result/error state and resets keyboard selection immediately.
2. Its effect starts a **300 ms** timer. Another query change clears that timer;
   clearing/whitespace does not send an API request. When the timer expires, the
   status becomes **Searching...** and it calls `search.ts::searchNotes`.
3. The client uses `URLSearchParams` and the existing `http.request` to GET
   `/api/search?q=...&limit=20`, with cancellation and the shared 10-second timeout.
   M2 FastAPI/SQLite performs the search; no frontend document scan occurs.
4. The client checks the response envelope, count, result fields and finite score.
   The component accepts it only if its controller is not aborted and its request
   generation is still current. State also carries the query/refresh/retry key, so
   an old result cannot remain actionable during a new debounce or save refresh.
5. Result cards preserve API order and render title/current path/preview as React
   text. `Highlight` adds `<mark>` nodes for literal word-prefix text; it never
   inserts HTML. Totals above 20 ask the user to refine the query. Errors stay in
   the search panel, retain input and offer Retry without altering the editor.

Aborting alone is insufficient: a response may already be resolving, and the
shared HTTP helper represents aborts as `ApiError`. The generation/signal checks
reject those replies. Clearing old state is also necessary for the A → clear → A
case; an identical text key must not revive a previous result during debounce.

### Result → canonical note without losing a draft

1. Input arrows change `activeIndex` while keeping focus in the combobox through
   `aria-activedescendant`; Enter opens that option (or the first ready result).
   A pointer/native button activation emits the same `onOpen(note_id)` callback.
   Keys are scoped to the search region; no document/global editor shortcut exists.
2. `App.openSearchNote` respects loading/modal/lifecycle/operation locks. For the
   already-open note, it updates tree selection/expansion only. It does not fetch
   or remount the live editor: App's note snapshot can predate its latest autosave.
3. For another note it calls the existing `perform`. That locks editing and calls
   `PersistentNote.flush`, which first drains editor uploads, then serialized
   `useAutosave` requests. Local edit versions and SQLite revision numbers remain
   owned by the existing autosave hook; no new save/concurrency mechanism is added.
4. If typing B queued behind an in-flight save A, flush waits for A's acknowledgment
   and B's following save. A 409/503, upload failure or unresolved browser recovery
   prevents the transition, retaining the current draft and its editor.
5. Only after a successful flush does App call canonical `notes.getNote` and
   `refreshTree`. If either read fails, or the fresh tree no longer contains the
   result ID, the original note remains open with an error.
6. After both reads succeed, App calls `setNote`, `setSelected`, `reveal` using the
   fresh tree folder ID, and `remember`. Existing `PersistentNote`/`KnowledgeEditor`
   reconstruct the destination from native JSON. Existing tree focus behavior
   focuses the revealed selected row. The query remains for further use.

### Save/library change → fresh search

The existing `noteSaved` callback and committed create/rename/move/delete paths
already refresh library metadata. `refreshTree` now advances `searchRefresh`
before its read. `GlobalSearch` hides/invalidates the old results and reissues the
current query after the same debounce, even if the metadata read fails. It does
not remount the editor or move focus after ordinary autosave. Local typing alone
does not update the index/results; M2 indexes only successful saves.

## 4. Decisions, alternatives and accepted tradeoffs

| Decision | Reason and alternatives |
| --- | --- |
| One self-contained search component | Query lifecycle and list interaction have one owner, with a small note-ID callback. Putting all state in App would obscure navigation/save logic; Redux or another state package would add no value. The component depends on an application API contract, not editor internals. |
| Reuse the M2 API unchanged | FTS5 handles matching/ranking and returns at most 20 records. Browser-side scans would load private documents unnecessarily. No new endpoint, framework, package or dependency pin is required. |
| Debounce + abort + generation + state invalidation | Debounce reduces requests; abort releases obsolete work; generation rejects late replies; clearing state prevents a repeated query from restoring cached results. A single abort signal or query-string comparison would miss one of those races. Keys also include committed-change refresh and explicit retry. |
| Invalidate on existing library refresh | Keeps results in sync after successful saves, note mutations and folder path changes with one small counter. A separate event bus/cache/subscription is unnecessary. It may requery after navigation/manual refresh even if text did not change; requests remain debounced. Other tabs do not push notifications. |
| Keep the folder tree visible | The search region is added above existing controls; results have their own bounded scroll area. Replacing the tree while searching would complicate selection/keyboard/focus and hide context. Sidebar/page height can grow; narrow screens keep the existing stacked layout. |
| Combobox/listbox interaction | Label, live status, selected option, controlled list, descriptions and local arrow/Enter/Escape handling make the operation explicit. A fully modal search palette/global shortcut was unnecessary and could interfere with BlockNote. Clear/Retry preserve ordinary Enter/Space behavior; Escape also works there. |
| Existing `perform`/flush boundary | Navigation cannot bypass uploads, serialized saves, revision conflicts or recovery. Search only supplies an ID; no BlockNote changes or alternate document state. Same-note activation intentionally avoids a redundant fetch/remount. |
| Fetch canonical note and fresh tree before transition | Results are snapshots and other tabs may have moved/deleted notes. Existing metadata is refreshed rather than trusting the result path. An extra read is accepted; no combined backend endpoint is added. The two reads are not one atomic snapshot across tabs, so a later concurrent edit can still produce the existing revision conflict on save. |
| Safe approximate text highlighting | React strings/marks preserve safety even for HTML-looking note text. No sanitizer/HTML endpoint is needed. Browser highlighting does not reproduce every FTS diacritic/case/tokenization rule, so a genuine match can lack a visual mark. FTS remains authoritative. |
| Transient query, no persisted preference | Hiding navigation preserves the mounted query; reload clears it. No new localStorage key or query history contains search terms. GET URL logging considerations from M2 still apply. |

## 5. Tests and outcomes

Commands below run from `frontend/` using Node **24.19.0** and existing pinned
dependencies. Test profiles/release snapshots are under `/tmp`; browser requests
outside loopback are aborted and asserted absent. No private notes are fixtures.

| Check | Executed outcome |
| --- | --- |
| `npm test` | **263 passed**, 21 files. Includes 54 new client/component/App cases; existing 209 frontend tests retained. |
| `npm run lint` | **Passed**, zero warnings. |
| `npm run build` | **Passed**, TypeScript and Vite. Existing large-bundle advisory remains; no dependency or code-splitting work added. |
| `CYRNAVA_E2E_RELEASE=1 node node_modules/@playwright/test/cli.js test --output=/tmp/cyrnava-m3-chromium-reviewed` | **11 passed** with the final built UI/CSS: nine existing regression journeys plus two new search journeys. |
| `node node_modules/@playwright/test/cli.js test e2e/search.spec.ts --browser=firefox --output=/tmp/cyrnava-m3-firefox-reviewed` | **2 passed** with the final UI/CSS and native-document, failed-save, unchanged-query autosave refresh, desktop/mobile assertions. |
| `git diff --check` | **Passed**. |

Specific safeguards covered by automation:

- Literal API URL encoding/no-store, cancellation forwarding, bounded response
  validation and no silent acceptance of malformed backend/JSON responses.
- No query for blank input, exactly 300 ms debounce, loading/empty/error/retry,
  result totals/path/root labels, arrows/wrap/Enter and Escape from all controls.
- HTML-looking snippets remain text; selection/click cannot execute content.
- Old request resolves after the new one; clear followed by late error; repeated
  A → B → A / clear → A; refresh invalidates an older response; unmount aborts.
- Native document opening and fresh nested-tree expansion, in-flight A plus
  queued B before navigation, 409/503 retention, same-editor identity, stale/deleted
  result/tree-read failures and unresolved browser draft recovery.
- Active-query rerun after save without taking editor focus. Real-browser cases
  additionally exercise the actual FastAPI/FTS index, code-only prefix matching,
  persisted native heading/bold/code content, saved-note reload, failed save
  retention/retry and unchanged-query discovery after ordinary autosave.

Corrections made during implementation:

1. Read-only review identified repeated-query stale-state resurrection; explicit
   state clearing and A → clear → A / A → B → A tests fixed it before final checks.
2. Escape was extended from the input/results to Clear and Retry focus, without
   hijacking their Enter/Space activation. Regression tests passed.
3. The screenshot/theme extension initially used `getByLabel('Appearance')`, which
   timed out in both browsers after the core search assertions had succeeded.
   The fixture now uses the existing suite's exact combobox-role locator. Fresh
   corrected runs are recorded as passes only after execution; the initial full
   Chromium run had 10 passes/1 fixture timeout, not an all-green result.
4. Captures now wait for the post-navigation search refresh rather than recording
   the brief intentional debounce state. No test timeout was increased.
5. Visual inspection found that the branded theme's general button `inline-flex`
   rule overrode the new result card's block layout, squeezing title/path/preview
   into columns. A more specific, search-scoped rule now stacks those fields.
   The browser test asserts the computed block layout, and final branded desktop
   and 390 px mobile captures were visually inspected after the fix.

The backend pytest suite was not rerun for M3 because backend source did not
change. Its **301-pass M2 result is prior evidence**, not a new M3 execution claim.
The browser journeys do execute the real reviewed backend/search endpoint.
The full Firefox legacy suite was not rerun; M2 already identified its existing
unsupported clipboard-permission test. M3's new journeys require no such permission.

## 6. Limits, risks and deferred work

- M4's 100/1,000/10,000-note benchmarks, final release checklist and comprehensive
  acceptance remain unexecuted. No latency target, release readiness or general
  accessibility certification is claimed by M3.
- Search is of committed content, not unconfirmed drafts. Results update after
  successful local saves; another tab's edits need a query change or **Refresh
  library**. There is no polling/WebSocket infrastructure.
- First 20 results only; refine to narrow larger sets. No result pagination,
  advanced FTS syntax, arbitrary substring matching or matching-block scroll.
- Query and result state clear on reload. Notes remain canonical in SQLite;
  clearing search never deletes or changes one.
- If the fresh metadata read fails during opening, the current editor stays open
  even if the destination note read succeeded. This favors preserving context
  over a partial transition. Two HTTP reads cannot promise an atomic cross-tab
  snapshot; existing optimistic concurrency continues to protect later saves.
- A deleted result produces an ordinary error and retains the current note; no
  automatic destructive cleanup/recovery is attempted.
- Keyboard/ARIA are tested in Chromium/Firefox, but a human screen-reader and
  normal desktop-profile acceptance check remains outstanding.
- Styling uses existing tokens. Synthetic desktop/branded/mobile captures and
  a horizontal-overflow assertion exercise the new region; no unrelated UI
  redesign or visual framework was introduced.
- No known unresolved M3 correctness defect after the passing checks. Existing
  build advisory, M2 migration/backup constraints and pending project license
  decision remain unchanged.

## 7. Owner manual review

1. Use a synthetic/test profile with the reviewed M2 backend and rebuilt frontend;
   everyday schema-5 upgrade precautions remain in [docs/search.md](docs/search.md).
2. Search a title, heading, paragraph and code prefix from different folders.
   Confirm title/path/preview order, clear/no-match/retry and keyboard operation.
3. Edit a note and immediately open another search result. Wait for the guarded
   save, return and check the complete formatting/text. Simulate a backend outage:
   a failed save must keep the source draft; restore the backend and retry.
4. Check search after title/content changes, note deletion and folder rename/move.
   Query an already-open note while it has a draft; its editor must stay intact.
5. Check Light/Dark/System/CyrNava and the narrow layout in your normal browser.
   Verify tree ancestors, focus and Escape while also typing normally in BlockNote.

## 8. Suggested Git commit

`feat(search): add debounced global search and safe result navigation`

Summary: typed M2 client, isolated search control, stale-query protection, safe
autosave-aware opening, fresh ancestor selection, scoped theme styles, tests and
usage/architecture documentation. M3 depends on the reviewed M2 work already in
this checkout. Stage/review milestone boundaries as desired; nothing was committed.

**Stop at M3 for owner review. Do not begin M4 without explicit authorization.**
