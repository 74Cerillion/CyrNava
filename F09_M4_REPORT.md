# F-09 M4 — validation and release handoff

Validation date: 2026-10-29. Scope: the approved F-09 M4 milestone, after M3 review.

## 1. Outcome and release status

**F-09 engineering validation passed.** The existing backend/frontend search
candidate meets the tested functional acceptance cases, preserves canonical data
through migration/rebuild, operates with remote requests blocked, and meets the
stated typical-query performance targets on this development machine's synthetic
workload. See the [acceptance/release checklist](docs/search-release-checklist.md)
and [benchmark method/raw metrics](docs/search-benchmark.md).

This is a **validated local candidate**, not a published release. The directive's
final "documented and committed" condition remains pending because the owner's
instruction forbids automatic commits/pushes. The existing original-code license
and attribution/publication gates also remain pending; the previous decision to
leave licensing undecided is preserved without another selection request.

No commit, push, tag, release, installed-desktop update or private-profile migration
was performed. M2/M3 were already uncommitted in this checkout and remain preserved.
M4 added diagnostic/test/documentation work, not another product feature. Production
search/editor/navigation code, schema 5, document format 1, package pins and storage
paths are unchanged from the reviewed candidate.

## 2. Every file created or modified in M4

Paths are repository-relative. Existing M2/M3 files are documented in their own
reports; this table covers only the additional M4 work.

| File | Responsibility, dependencies and reason |
| --- | --- |
| `backend/benchmarks/search.py` (new) | Standard-library, synthetic-only benchmark CLI. Reuses `Database`, native document validation, `index_note` and `verify_index`; generates deterministic valid documents in `/tmp`, checks expected hits and times the real backend search boundary. No existing-profile input option or new runtime dependency. |
| `backend/tests/test_search_benchmark.py` (new) | Nine pytest cases for nearest-rank statistics, deterministic corpus/query counts, seed variation, private temporary-profile cleanup, ignoring real XDG data, invalid arguments and JSON CLI output. No fragile latency thresholds in ordinary tests. |
| `frontend/e2e/search.spec.ts` | Adds safe stop/restart/offline CLI fixture helpers, canonical/raw-JSON/template-BLOB/asset snapshots and two broader real-browser journeys. Extends existing log checks. Uses existing Playwright, Node built-ins, FastAPI, SQLite and installed Pillow for synthetic pixels. All profiles/release copies are disposable and external to Git. |
| `docs/search-benchmark-results.json` (new) | Raw synthetic aggregate measurements: all query medians/p95/max/counts, corpus size/fingerprint, runtime, journal mode, page size and exact source fingerprint. Contains no profile/database or private note data. |
| `docs/search-benchmark.md` (new) | Reproduction commands, workload/method/timing boundary, per-query/scale results and limits. Separates backend timing from HTTP/render/debounce and rejects unsupported general performance claims. |
| `docs/search-release-checklist.md` (new) | Executed T-SEARCH-01–16 evidence, validation checklist and remaining owner/publication actions. Separates candidate correctness from licensing, commit and deployment approval. |
| `README.md` | Marks the candidate as M4-validated, links evidence and benchmark command, and retains pending owner release status. |
| `docs/search.md` | Updates current milestone status and links final validation/performance/release evidence. Existing API/upgrade/rebuild instructions remain applicable. |
| `docs/architecture.md` | Updates current validation status and links the synthetic benchmark; no architecture boundary was changed. |
| `docs/release-checklist.md` | Labels the old M6 evidence as historical and points to F-09's current checklist instead of presenting old test counts as current. |
| `docs/release-notes-v0.1.0.md` | Updates the unpublished draft with search, schema 5, current browser-draft limitations and evidence links; preserves owner/license approval gates. No version/tag/publication action. |
| `CHANGELOG.md` | Records M4 diagnostics/integration/validation separately from M2/M3. |
| `F09_M4_REPORT.md` (new) | This handoff, file/execution/decision/test/risk record and recommended commit. |

## 3. Execution flow and what M4 verifies

### Ordinary application operation — unchanged

`GlobalSearch.changeQuery` invalidates old state and aborts superseded work →
300 ms debounce → `search.ts::searchNotes` → shared `http.request` GET
`/api/search` → `main.search_notes` validates the envelope → `Database.search`
opens one read snapshot → `search.search_notes` binds literal prefix terms to
FTS5, counts/ranks/snippets and resolves current folder paths → validated response
→ current-generation check → safe React text/highlight result cards.

Click/Enter emits only a note ID → `App.openSearchNote` → existing `perform` →
`PersistentNote.flush` waits for uploads and queued autosaves → canonical `getNote`
and fresh `refreshTree` → verify the note still exists → install native JSON,
select/reveal its ancestors and remember the note ID. Failed saves/reads retain
the original editor. Same-note activation preserves its current editor. No snippet
is ever used as the saved document.

Typing → BlockNote adapter snapshot → existing serialized `useAutosave` PATCH →
FastAPI native validation → `Database.update` with expected revision → canonical
write plus `index_note`/projection/FTS trigger on the same transaction → commit →
acknowledge only that edit snapshot. A 409 never indexes the rejected title/body.
The successful-save/library callback refreshes an active query without changing it.

### Benchmark — separate development command

`python -m benchmarks.search` creates its own temporary directory → initializes
the current schema → validates/generates deterministic native documents → seeds
canonical rows and production index helper in one setup-only transaction → verifies
index integrity and expected query totals → five warm-up rounds → 30 timed rounds
per query, deterministically shuffled → serializes aggregate JSON → removes the
temporary database. It never resolves `default_database_path` or opens the user's
profile. The timer wraps `Database.search`, not fixture construction or the browser.

### Migration/rebuild drill — actual operator path

The new browser fixture creates three synthetic notes, nested folders, an owned
image and custom template/independent note image. After clean shutdown it removes
only search objects to model the genuine schema-4 table layout and deliberately
indents stored note/template JSON. It records every canonical field/raw JSON string,
template image BLOB hashes and owned image-file hashes.

Starting the actual release backend upgrades to schema 5 → the built UI searches
all three notes and renders heading/bold/code/nested/image content → shutdown and
canonical snapshot comparison → restart/reopen → deliberately clear only FTS's
derived inverted index → verify no matches while canonical data remains readable
→ stop → real `app.search_index rebuild` CLI → compare canonical snapshots again
→ restart and confirm search/formatting/images return. Whole SQLite file bytes
are not compared: adding/rebuilding an index necessarily changes the DB file.

## 4. Decisions and alternatives

| Decision | Why selected; alternatives and accepted tradeoff |
| --- | --- |
| Measure the actual backend boundary | A reused raw SQLite connection would understate per-request connection/snapshot/path costs. HTTP/browser timing would mix those with network, JSON and the intentional debounce. `Database.search` includes the real backend work while keeping the layers distinguishable. |
| Deterministic synthetic data only | Never benchmark private notes or accept a real-profile path. Standard-library temporary directories, UUIDs and seeded text are sufficient; a new dataset/service/dependency is unnecessary. The corpus is reproducible but intentionally not a promise about every operational document. |
| Fixture-only bulk seed | Setup validates native JSON and uses the production index helper/triggers, but bulk insertion makes repeated scale runs quick. It is excluded from measurements and does not claim to measure ordinary save throughput. No product write path, PRAGMA tuning, optimize command or ranking change was added. |
| Per-query p95, not one average | Exact/rare searches differ from all-match count/rank work. Fixed-frequency terms and separate broad stress cases expose those costs. Five warm-ups/30 samples offer useful bounded observations; no wall-clock assertions make the regular test suite flaky. |
| Broader integration tests rather than production rewrites | Inspection found no unresolved M2/M3 correctness issue. The useful remaining risk was proving chained UI/DB/operator flows: unchanged-query refresh, rejected saves and richer legacy recovery. Existing frameworks and fixture helpers cover those without new abstraction layers. |
| Preserve the reviewed UI | Branded/mobile result layouts and behavior were rerun and visually reviewed. No new defect justified a further product redesign; M3's scoped theme fix remains in place. |
| Explicit Firefox coverage boundary | Existing Chromium clipboard permissions are unsupported by Playwright Firefox. Excluding that one named legacy test, while running all 12 applicable journeys, preserves honest coverage without weakening a browser permission model or rewriting unrelated tests. The omitted journey passed in Chromium. |
| Candidate handoff rather than automatic commit/release | The owner explicitly retained Git/publication authority and left licensing pending. The full engineering evidence is concrete and reviewable; no inferred authorization overrides those choices. |

No new runtime/development dependency, BlockNote XL package, external search/AI
service, database migration framework or frontend state-management framework was added.

## 5. Executed validation

Current runtime: Python **3.12.15**, SQLite **3.46.1** with real FTS5, pinned Node
**24.19.0** and the existing lockfiles. This is a Linux development environment,
not a fresh Ubuntu installation. No unexecuted check is reported as passing.

| Command / check | Actual outcome |
| --- | --- |
| `.venv/bin/python -m pytest -q` in `backend/` | **310 passed**, one existing Starlette/httpx TestClient deprecation warning. Includes all prior search/migration/rebuild regressions and nine benchmark-harness cases. |
| `.venv/bin/python -m ruff check .` and `ruff format --check .` | **Passed**, 32 Python files formatted. |
| `.venv/bin/python -m pip check` | **No broken requirements**. Sandbox cache-directory warning was emitted; no installation/cache ownership change was needed. |
| `npm test` in `frontend/` | **263 passed**, 21 files. Existing autosave, editor, navigation, search, error/abort/repeated-query and safe rendering checks retained. |
| `npm run lint` and `tsc --noEmit` | **Passed**, including added browser fixture/helpers. |
| `npm run build` | **Passed**, TypeScript/Vite production bundle. Existing large-chunk advisory remains; no dependency or bundling workaround added. |
| `CYRNAVA_E2E_RELEASE=1 node node_modules/@playwright/test/cli.js test --output=/tmp/cyrnava-f09-m4-chromium-release` | **13 passed**: nine existing journeys and four search journeys against real built UI/FastAPI/SQLite. |
| Same release command with `--browser=firefox --grep-invert 'Phase 1 formatting, clipboard' --output=/tmp/cyrnava-f09-m4-firefox-release` | **12 applicable journeys passed**, including all four search journeys. Exactly one existing legacy clipboard-permission journey was excluded, not passed. |
| `.venv/bin/python -m benchmarks.search > /tmp/cyrnava-f09-search-benchmark.json` | **Completed**, all 100/1,000/10,000 datasets and expected-hit checks; five warm-ups and 30 samples for each of 15 queries/size. Raw aggregate metrics retained in docs. |
| Benchmark source fingerprint versus current implementation | **Matched**. Fingerprint includes database/search/document validation and benchmark source. |
| `git diff --check`, working candidate text/artifact/secret-pattern scan, staged-file review | **Passed** within the bounded scope below; no staged files or publication actions. |
| Branded desktop and 390 px mobile search captures from this run | **Visually reviewed**; stacked result title/path/preview, safe highlights and no page overflow retained. |

The two added M4 browser cases passed on their first execution. Initial benchmark
lint found an assigned lambda and a long string; both were corrected before the
first benchmark/test run. There were no product test failures or production fixes
required in M4. Existing advisories are recorded above instead of being suppressed.

### Functional evidence

[The checklist](docs/search-release-checklist.md) maps T-SEARCH-01–16 to the actual
backend/frontend/browser tests. Additional M4 evidence specifically demonstrates:

- Search 503/retry retains input and the current editor; title autosave updates
  the result under an unchanged query; folder rename/move changes its displayed
  path; deletion removes it without retyping.
- A real 409 rejected title never becomes searchable and the winning canonical
  note remains identical.
- Migration, ordinary restart, intentional inverted-index damage, offline rebuild
  and restart preserve three notes' every canonical field and indented JSON bytes,
  folder rows, custom-template definition/image BLOB and two independent image files.
- Real browser image decoding and native heading/bold/code/nested content work
  before and after those operations.
- Browser routes reject non-loopback destinations and assert **zero attempted
  remote requests**. Backend offline tests forbid outbound socket connections.
  Release logs contain neither search URLs nor the synthetic query terms.

## 6. Benchmark results

The reference corpus has 10/100/1,000 folders and about 10% root notes. Documents
range from **1,363 to 6,100 bytes**, mean **3,281.47 bytes** at 10,000 notes, with
valid native rich-text structures and varied term frequencies. At 10,000 notes,
the SQLite file is **86,286,336 bytes** and fixture validation/index seeding took
about **4.20 s**, excluded from query samples.

| Notes | Highest typical-query median | Highest typical-query p95 | Highest broad-stress p95 |
| ---: | ---: | ---: | ---: |
| 100 | 0.94 ms | 1.51 ms | 2.29 ms |
| 1,000 | 3.33 ms | 4.51 ms | 6.51 ms |
| 10,000 | 25.44 ms | 26.50 ms | 37.47 ms |

At 1,000 notes the highest typical-query p95 was below 100 ms; at 10,000 it was
below 250 ms. The largest typical case was `enum`, deliberately matching every
note. The 10,000-note one-character stress case matched every note and reached
37.47 ms p95. Per-query distributions/counts are retained, not hidden in a pooled
average. No performance optimization was necessary to meet the stated targets
on this workload.

These are **warm-filesystem-cache backend observations**, including a fresh
connection/count/ranking/snippets/folder paths per call. They exclude HTTP/JSON,
browser rendering and 300 ms debounce. Disk speed, cold caches, contention, deeper/
more numerous folders, concurrent writes and much larger documents can differ.
Neither universal latency nor near-1 MiB-document performance is claimed. The
default harness command is safe to repeat on the owner's machine without touching
their profile; no measurements against private notes were made.

## 7. Git hygiene and remaining release gates

The starting commit is `9109904` (`add CyrNava branding and theme`); reviewed
M2/M3 additions were already uncommitted. M4 preserves them. A bounded candidate
audit checks tracked and unignored files for runtime data/capture/key extensions
and high-signal private-key/token patterns, without printing matched contents.
No database, user notes, captures, credentials or generated benchmark profile is
tracked/unignored/staged; all application-data fixtures live outside Git.
The retained benchmark JSON contains aggregate synthetic metrics only. Generated
browser artifacts remain under `/tmp`/ignored results, not release assets.

This is not an exhaustive secret/history/security certification. It does not
substitute for owner review of the combined uncommitted diff or the post-commit
clean-checkout build. No fresh public clone/clean OS installation or everyday
profile/installed-launcher update was performed.

Remaining intentional limits:

- Prefix/AND search, 20-result UI cap, no arbitrary substring/fuzzy/advanced query
  language, no matching-section jump; highlighting approximates FTS normalization.
- Search indexes committed data. Another tab's changes require a query change or
  Refresh library. There is no background subscription/queue/cache layer.
- Cooperative Linux locks require external/noncooperating writers to be stopped.
  Rebuild repairs derived data with healthy canonical notes/assets/templates, not
  arbitrary physical SQLite corruption or lost source evidence.
- Search text/indexes/backups are private but unencrypted under the existing
  local-first model. GET terms can be recorded by clients/custom tools even though
  supported release/desktop servers suppress request logging.
- Full Firefox legacy clipboard journey, screen-reader/assistive-technology audit,
  fresh OS acceptance, power-loss/disk-full campaigns and complete cold-disk/concurrent
  performance characterization remain unverified. Applicable Firefox journeys and
  the complete Chromium suite passed; excluded/unexecuted checks are not passes.
- Existing original-code license and third-party publication decisions remain
  with the owner. No legal/public-release clearance is implied by passing tests.

No known F-09 correctness defect remains in the tested candidate. Literal final
commit/publication and owner-specific manual acceptance are still pending actions,
not silently completed milestones.

## 8. Owner verification and recommended commit

1. Review this report, the combined M2/M3/M4 changes and the acceptance checklist.
2. On a synthetic local profile, search titles/paragraphs/headings/code/nested text;
   use keyboard/clear/retry, edit and navigate immediately, then confirm the source
   saved. Check rename/move/delete refresh with the query unchanged.
3. Stop the test backend, rebuild its index using the documented CLI, restart and
   verify native formatting/images/search. Keep personal data out of this drill.
4. Reproduce the benchmark if desired; compare backend distributions separately
   from the visible debounce/render time.
5. Before an everyday upgrade, retain a verified pre-schema-5 backup and stop all
   backends. Install/update only after review. Older code refuses schema 5.
6. Owner stages/commits approved source, then verifies a clean checkout using the
   pinned environments before any authorized push/tag/release.

Suggested combined F-09 commit:

`feat(search): add validated local full-text search with safe navigation`

Commit summary: schema-5 FTS5 projection/backfill and offline rebuild; atomic
note/template synchronization with revision protection; debounced global UI and
safe canonical result opening; regression/migration/offline tests; reproducible
scale benchmarks and owner release documentation. If committing milestones
separately, M2/M3 messages remain in their reports; M4 can use
`test(search): validate migration, offline recovery and search performance`.

Nothing has been committed, pushed, tagged or published. **Stop here for review;
do not begin another feature or deployment without explicit authorization.**
