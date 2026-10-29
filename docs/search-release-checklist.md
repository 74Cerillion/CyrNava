# F-09 search candidate — M4 validation and owner gates

Engineering validation date: 2026-10-29. This records actual candidate evidence,
not permission to publish or install into the owner's everyday profile. M2/M3
changes remain in the checkout; no milestone has been committed automatically.

## Engineering evidence

- [x] SQLite FTS5 remains local; native version-1 JSON is canonical.
- [x] Index/schema migration is additive, transactional and protected from old
  cooperating writers; canonical fields/raw JSON survive unchanged.
- [x] Search/create/edit/rename/delete/template paths and revision conflicts are
  covered by the real backend tests; index failures roll back canonical writes.
- [x] Search result navigation drains uploads/queued saves and retains failed or
  unresolved drafts. Existing editor and folder navigation regressions pass.
- [x] Search query cancellation/repetition/out-of-order responses, keyboard,
  clear/retry/error states and untrusted text rendering are tested.
- [x] Built-UI tests cover unchanged-query refresh on title/folder changes and
  deletion, rejected-save exclusion and current ancestor selection.
- [x] Three-note legacy schema-4 profile with nested native content, copied custom
  template, image BLOB and two owned files passes migration/restart/rebuild with
  raw JSON, every canonical field and image hashes preserved.
- [x] Missing/stale/inverted index repair, failed rebuild rollback, live-profile
  refusal and bad/unsafe/old/corrupt input refusal are tested.
- [x] Offline browser request filtering asserts zero attempted non-loopback
  requests; release logs contain no search URLs/terms. Backend network calls are
  forbidden in the dedicated offline test.
- [x] 310 backend tests; 263 frontend tests; lint/format/types/build; `pip check`.
- [x] 13 Chromium release journeys; 12 applicable Firefox journeys. The existing
  Chromium clipboard-permission journey is explicitly excluded from Firefox,
  where that test harness permission is unsupported. No excluded test is a pass.
- [x] Synthetic 100/1,000/10,000-note benchmark, expected-hit checks, five warm-up
  rounds and 30 samples/query, with retained [method/raw metrics](search-benchmark.md).
- [x] Highest typical-query p95 observed: 1.51 / 4.51 / 26.50 ms. Broad stress p95:
  2.29 / 6.51 / 37.47 ms. These warm-cache backend measurements meet the stated
  typical-query targets on this development machine, not on every machine/corpus.
- [x] Synthetic desktop/mobile/branded search views reviewed; no unrelated redesign.
- [x] No new dependency, XL package, runtime external service, schema increment
  beyond reviewed M2 schema 5, or original-code license selection in M4.
- [x] Candidate text/runtime-artifact audit and `git diff --check` pass. No database,
  user notes, capture, credentials or benchmark profile is staged/unignored.
- [x] User guide, benchmark guide, engineering report and current release draft updated.

## Acceptance mapping

| Requirement | Executed evidence |
| --- | --- |
| T-SEARCH-01 title | `test_search.py` exact/weighted title cases and real-browser renamed result |
| T-SEARCH-02 paragraph | Native fixture/API search and unchanged-query ordinary autosave journey |
| T-SEARCH-03 headings | H1–H6/native fixtures, heading weighting and migrated rendered heading |
| T-SEARCH-04 code | Native code/flags/IP tests; code-only prefix browser result preserves code |
| T-SEARCH-05 nested text | Extraction/fixtures/nested list tests; rendered migrated nested evidence |
| T-SEARCH-06 folders | Root/nested path API tests and cross-folder result opening/current paths |
| T-SEARCH-07 rename | API old/new term checks and unchanged-query title autosave rename |
| T-SEARCH-08 successful edit | Transactional index tests and ordinary autosave creating another match |
| T-SEARCH-09 deletion | Note/recursive-delete/rollback tests and unchanged-query UI deletion |
| T-SEARCH-10 existing notes | Schema-1/2/3 regressions; raw schema-4 backfill and built-UI multi-note migration |
| T-SEARCH-11 invalid query | Length/term/control/limit, literal operators, SQL-like input and private errors |
| T-SEARCH-12 correct note | Built-UI native heading/bold/code/image opening and ancestor/tree selection |
| T-SEARCH-13 draft safety | Held PATCH response, queued edits, 409/503, same-note identity and recovery guards |
| T-SEARCH-14 offline | No non-loopback browser requests; backend socket prohibition; no query logs |
| T-SEARCH-15 rebuild | Derived corruption/missing/stale recovery, canonical snapshot checks and real CLI/UI restart |
| T-SEARCH-16 stale update | Competing revisions/409 and real rejected title never entering FTS |

## Remaining owner/release actions

- [ ] Owner reviews the complete F-09 candidate and its known limitations.
- [ ] Owner performs normal-browser/desktop acceptance on a synthetic profile,
  including preferred keyboard/screen-reader/clipboard workflow as applicable.
- [ ] Retain a verified pre-schema-5 backup and stop all backends before any
  everyday profile upgrade; install/update the desktop copy only after review.
- [ ] Owner commits/pushes approved source and repeats clean-checkout installation
  against that exact commit. Existing installed dependencies were used here; no
  fresh public clone/clean OS installation is claimed for this uncommitted feature.
- [ ] Existing project-wide publication gates remain resolved by the owner:
  original-code license decision, third-party attribution/source-availability
  review and explicit release/tag approval. See the historical [M6 checklist](release-checklist.md).

The earlier instruction to leave the license decision pending is preserved. No
new license choice is requested by this checklist. The directive's final commit
step remains unperformed under the owner's instruction not to commit automatically.

F-09 engineering validation passed. Public publication and the literal
"documented and committed" finish condition remain pending owner action. No new
feature or later phase is authorized by this checklist.
