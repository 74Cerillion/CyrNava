# M6 engineering report — ENGAGE v0.1.0 candidate

## A. Release readiness summary

**NOT READY for public v0.1.0 publication.** Engineering verification of the local candidate passes, but the owner explicitly leaves original-code licensing pending. No LICENSE or permission grant has been added. Transitive attribution provenance also needs resolution/approval before bundle distribution. The final public M6 commit must receive a clean-clone check after owner commit/push; currently public HEAD is M5. These are explicit release gates, not hidden product failures.

The candidate is ready for architectural review and human acceptance. It preserves schema 3, native document format 1 and existing M0–M5 behavior. No personal data was used. No commit, push, tag, GitHub release or Phase 2 work was performed.

## B. Implementation summary

- Added `python -m app` to serve the built frontend and API on one loopback origin, with static-path boundaries, a same-origin CSP and actionable missing-build errors. No Vite runtime process or new dependency is required. `/api/health` aliases existing `/health` in release mode; `/`, `/assets/*` and `/third-party-notices.txt` exist only to serve that build.
- Displayed version 0.1.0, clarified save/upload guidance, named the editor, added a keyboard skip link, described deletion dialogs, improved checkbox sizing, status visibility, error wrapping and responsive controls. Fixed a demonstrated global-button-style leak into Mantine popup controls.
- Added four release-serving tests and one comprehensive real-browser Phase 1 journey; both existing browser journeys now also run against release mode.
- Replaced milestone-oriented onboarding with portable setup/usage; documented real flows, five retrospective ADRs, licenses/inventory, sanitized screenshots, changelog, release draft and checklist.

The [initial audit](docs/release-audit.md) distinguishes pre-existing functionality from M6 changes. Persistence, backup, editor schema and concurrency algorithms were not rewritten for style. No new application capability beyond minimal release serving was introduced.

## C. File change report

Every created/modified file is listed below. Paths are relative to the repository. Historical M0–M5 reports, data/asset/backup algorithms, requirements and existing unit suites are unchanged.

| File | Responsibility, dependencies and reason |
| --- | --- |
| `README.md` | Newcomer setup, run, usage/data/recovery/testing and limitations; depends on verified commands and linked docs; replaces milestone-only onboarding. |
| `CHANGELOG.md` | Candidate scope, compatibility/data preservation and limitations; depends on actual Phase 1 state; no invented release date. |
| `M6_REPORT.md` | This A–K engineering review; depends on executed evidence and full change inventory. |
| `M6_VERIFICATION.md` | Commands, environment, failures, outcomes and acceptance matrix; depends on real test/audit results; separates candidate/public-clone and manual gaps. |
| `backend/app/__init__.py` | Application version constant 0.1.0, consumed by FastAPI and version test. |
| `backend/app/__main__.py` | Argparse/Uvicorn/create_app release launcher; validates port, fixes loopback host and locates built frontend. |
| `backend/app/main.py` | Optional frontend_path/version integration; depends on release helper and existing FastAPI factory; default API behavior retained. |
| `backend/app/release.py` | FastAPI FileResponse/StaticFiles middleware; only built index/assets/notices and health alias; local request/CSP boundaries. |
| `backend/tests/test_release.py` | pytest/TestClient/subprocess tests for static/API isolation, headers, missing build, version agreement and bad port; temporary profiles only. |
| `frontend/package.json` | Version, pending-license marker and release browser command; existing npm/Playwright dependencies unchanged. |
| `frontend/package-lock.json` | Matching root metadata; exact dependency versions/integrity resolution preserved. |
| `frontend/e2e/workspace.spec.ts` | Existing Playwright/Node/Pillow harness; release mode and formatting/clipboard/CRUD/keyboard/responsive/screenshots journey; owns temporary profiles/processes. |
| `frontend/src/App.tsx` | React shell version, skip link/main target, clearer empty guidance and notices link; depends on existing App selection and package version. |
| `frontend/src/components/KnowledgeEditor.tsx` | Existing BlockNote adapter; adds accessible editor name and formatting/image instructions; persistence/event behavior unchanged. |
| `frontend/src/components/ManagementDialog.tsx` | Existing native dialog; connects deletion description through aria-describedby. |
| `frontend/src/components/PersistentNote.tsx` | Existing save/adapter boundary; text status pill/atomic announcement and upload/save guidance. |
| `frontend/src/styles.css` | Existing layout/control styles; scopes app buttons away from Mantine, contains editor overflow and improves focus/checkbox/status/dialog/narrow layout. |
| `frontend/public/third-party-notices.txt` | Actual runtime license texts/source pointers and local Inter OFL attribution; Vite copies it and UI links it; no original-code license grant. |
| `docs/release-audit.md` | Initial findings and disposition grounded in M5 source/history. |
| `docs/architecture.md` | Actual component/storage diagram and save/image/folder flows; depends on current modules/function names. |
| `docs/adr/README.md` | Decision index and retrospective-evidence qualification. |
| `docs/adr/ADR-001.md` | BlockNote adapter decision, current boundaries and replacement tradeoffs. |
| `docs/adr/ADR-002.md` | Native JSON canonical storage/versioning decision; tied to M1 persistence/schema. |
| `docs/adr/ADR-003.md` | Local FastAPI/SQLite/filesystem decision; tied to XDG/assets/offline recovery. |
| `docs/adr/ADR-004.md` | Incremental vertical-slice decision; source/history provenance and unavailable independent M3 history acknowledged. |
| `docs/adr/ADR-005.md` | Owner-specified React/TS/Vite/Python stack, isolation/pin tradeoffs. |
| `docs/dependencies-and-licenses.md` | Actual inventory interpretation, original-code license options/recommendation, obligations and unresolved provenance. |
| `docs/dependency-inventory.json` | Locked npm (including dev/optional) and pinned Python package versions/license labels; audit snapshot without upgrades. |
| `docs/python-third-party-notices.txt` | Available exact installed wheel license texts for pinned requirements; supports dependency review/redistribution. |
| `docs/screenshots/workspace.png` | Real full workspace capture, synthetic nested tree and formatted note; created by browser test. |
| `docs/screenshots/hierarchy.png` | Real cropped sidebar showing two folder levels and two notes. |
| `docs/screenshots/rich-text.png` | Real cropped main area showing H1/H2/H3, list/bold/code. |
| `docs/screenshots/images.png` | Real working note with persisted synthetic clipboard/upload images. |
| `docs/verification-source-sha256.txt` | Hashes of runtime/config/tests/notices used in clean candidate; supports source equivalence without committing. |
| `docs/release-notes-v0.1.0.md` | GitHub release description draft; depends on current supported features/limitations; publication explicitly gated. |
| `docs/release-checklist.md` | Verified checks and unresolved owner/license/final-public-commit gates; no unchecked item portrayed as complete. |

## D. Architecture review

The strongest boundary is the combination of a dedicated editor adapter, native validated JSON, serialized frontend saves and atomic database revision checks. It separates transient editing from durable transactions. App controls selection/navigation; PersistentNote/useAutosave control snapshots; clients own HTTP; FastAPI validates/routes; Database owns parameterized SQL and relationship/revision transactions. `KnowledgeEditor` is the only UI module needing detailed BlockNote API knowledge, although replacing it still requires a document migration.

A paragraph flows through `KnowledgeEditor`'s BlockNoteView change callback → `useAutosave.changeDocument` → 700ms debounce / serialized `flush` → `notes.updateNote` → `http.request` → FastAPI `update_note` → `Database.update` with expected revision → committed JSON/revision → checked response/local edit acknowledgement → Saved only when the latest local version is confirmed. New edits during A remain pending and save after A; responses never replace current typing. Reload follows App's `getTree`/`getNote`, FastAPI `get_note`, `Database.get`, and a remounted adapter initialized from saved native JSON. Three detailed walkthroughs and the dependency diagram are in [architecture](docs/architecture.md).

SQLite transactions own hierarchy and revision integrity. Asset files use generated IDs/ownership and normalized raster bytes; database/filesystem atomicity remains a managed boundary, not a false shared transaction. Error handling retains drafts and blocks transitions; 409 recovery deliberately exports both versions before explicit saved-state reload. Offline backup validates database/images/manifest and restores into a new profile under cooperative locks.

Maintainability is reasonable for this scope: no ORM, global state framework or migration framework was added. App/dialog code and the large editor bundle will need attention as future scope grows. Current limitations are documented rather than used to justify speculative refactoring. M6's optional static helper leaves the API factory/test seam intact and serves only intended build paths. The direct `/api/health` alias matches the dev proxy contract without an SPA catchall swallowing unknown API errors.

## E. Testing report

See [exact commands, failures and T-01–T-12](M6_VERIFICATION.md).

| Gate | Working candidate | Independent clean candidate |
| --- | --- | --- |
| Backend pytest | 96 passed | 96 passed |
| Frontend Vitest | 77 passed | 77 passed |
| Ruff lint / format | Passed, 17 files formatted | Passed |
| pip check | No broken requirements | No broken requirements |
| ESLint | Passed | Passed |
| TypeScript + Vite build | Passed | Passed |
| Chromium release journeys | 3 passed, 19.8s | 3 passed, 19.6s |
| Chromium development journeys | 3 passed, 24.5s | Not repeated; development baseline clone had 2 passed |

A genuine public M5 clone with fresh Python/npm environments also passed its 92 backend/77 frontend/two browser baseline tests and build. Independent M6 installs used empty environments/cache and no existing profile/build. The final published M6 commit does not exist yet; repeat its clean clone before tagging. This distinction satisfies feasible review-time verification without pretending uncommitted candidate files are already in GitHub.

Failures corrected: wrong pytest working directory; test caret inside code block; actual global CSS/Mantine popup overflow at 390px; Ruff formatting. Final affected and broad regressions passed. Offline journeys reject non-loopback browser requests and assert zero external attempts; fonts are bundled and backend paths were inspected. This is not a claim that the host NIC was physically disconnected. Remaining warnings: existing Starlette/HTTPX deprecation and Vite chunk size; no unnecessary upgrades were made.

Manual/unexecuted: fresh Ubuntu OS install, human screen-reader/contrast audit, actual screenshot-app clipboard interoperability, other browsers/OSes, crash/power-loss tests, independent legal/security review and owner acceptance. Four synthetic captures were visually inspected; they are working UI screenshots, not mockups.

## F. Dependency and licensing report

No library was added/upgraded. React/DOM 19.3.1, BlockNote core/react/mantine 0.56.0, Mantine 8.3.11, Vite 8.3.4, TypeScript 5.9.3, FastAPI 0.156.3, Pydantic 2.14.1, Uvicorn 0.54.0 and Pillow 13.0.0 remain pinned. Existing pytest/Vitest/Playwright continue their distinct roles. Exact lock/pin/license inventory and available notices are retained.

No XL package is declared/locked/installed. Core BlockNote is MPL-2.0, so notices and corresponding covered-source availability remain obligations independent of ENGAGE's own license. The frontend notice includes exact published source links and local Inter OFL attribution; dependency files were not modified. Runtime traversal found 75 npm packages; the lock includes 327 entries including optional/dev packages. Python has 24 pins. No obvious unused direct dependency or resolution conflict was found. npm reported zero known vulnerabilities during installation; this is not exhaustive vulnerability assurance.

MIT is recommended for original code; Apache-2.0 offers explicit patent terms at greater notice complexity; MPL adds covered-file reciprocity. **The owner selected neither: leave pending.** No LICENSE was added. `use-composed-ref` 1.4.0 declares MIT but omits copyright/license files in the inspected package/upstream; its notice discloses the gap and does not invent attribution. Resolve/approve provenance before bundle distribution. This report is not legal clearance. See [full review and primary-source links](docs/dependencies-and-licenses.md).

## G. Accessibility report

Improvements: named editable surface, skip link/main focus target, deletion description linkage, correctly sized checkboxes, textual save pills/atomic live status, clear upload instructions, visible focus outlines, wrapped errors/dialog actions and contained wide content. Existing tree semantics, scoped keyboard handlers and native modal behavior are preserved.

Executed: tree collapse/expand/first-child navigation, Enter opening, F2/Delete/Escape dialogs, focus return, editor key independence, accessible names on visible buttons, 390px overflow check and unit regressions. Screenshots distinguish selection background, open-note weight/dot and focused outline. Errors/status have readable text, not just colors.

Limitations: no full WCAG/contrast/screen-reader certification, exhaustive keyboard review of every upstream editor popup, touch/mobile app support or cross-browser accessibility audit. Targeted keyboard acceptance is demonstrated; comprehensive certification is not claimed.

## H. Security and privacy review

Audit covered `.gitignore`, every baseline tracked path, staged content (empty), intended candidate files, available history (five commits, 117 blobs), startup/config/tests/docs and demo screenshots. High-signal credential/private-key patterns found no matches; no tracked personal notes, databases, captures, backup archives, node_modules, venvs, build artifacts or sensitive environment files were found. Candidate Markdown relative links were checked. Historical user-specific tool paths are not credentials; historical reports were preserved. This is a bounded audit, not proof that no unknown secret pattern exists. No history was rewritten.

Data-path code and temporary-profile tests verify XDG isolation, in-checkout refusal and private new-file/directory permissions. Personal application contents were intentionally not read. Backend asset guards retain MIME/content/dimension/size validation, generated paths, ownership checks, symlink refusal and normalization. Documents are validated, never executed. Release static serving does not mount the source/data root, and unknown/traversal routes are tested. CSP permits local scripts/requests/fonts and the inline styles BlockNote needs; it is additional containment, not authentication.

Supported release and development commands bind loopback. No external runtime service was added. Localhost is not a defense against local malware or OS-account compromise; notes/backups/recovery downloads are unencrypted. Cooperative locking requires all writers to cooperate; unrelated older processes must be stopped. Browser APIs can vary by platform. No claim of public internet hosting readiness is made.

## I. Technical debt register

| Category | Item and implication |
| --- | --- |
| Release blocking | Owner license approval/accurate LICENSE and metadata remain explicitly pending. |
| Distribution blocking | Resolve/approve missing transitive copyright provenance and review MPL/other notices before shipping a bundle. |
| Release gate | Owner approval and clean clone of the exact published M6 commit before tagging; current evidence distinguishes public baseline and candidate export. |
| Accepted limitation | Unsaved drafts memory-only; wait for Saved/uploads. Forced shutdown can lose unconfirmed content. |
| Accepted limitation | Offline unencrypted backups, cooperative Linux locks, no live snapshotting; verify a restored profile. |
| Accepted limitation | Owned unused images remain until note deletion; normalization is unsuitable for forensic originals. |
| Accepted limitation | Manual refresh between tabs; conflict recovery is deliberate export/reopen, without merge. |
| Accepted limitation | Large editor bundle, existing TestClient deprecation, Python pins without hashes; defer focused maintenance rather than broad release upgrades. |
| Accepted limitation | Chromium/Linux and targeted accessibility verified; other platforms/full WCAG/human acceptance pending. |
| Future development | Engagement entities, search, tags, integrations, cloud/authentication, richer recovery/packaging are out of M6 scope. |

No remaining reproducible functional defect was found in the tested Phase 1 paths. That statement does not waive the unexecuted checks or release gates.

## J. Release recommendation

Authorize **review and local evaluation**, not public publication yet. The technical candidate passes its automated gates and has understandable setup/architecture/recovery documentation. Keep release approval blocked until the owner resolves licensing/distribution prerequisites, accepts documented limitations and verifies the exact final public commit. No Phase 2 work should begin under this authorization.

## K. Git and release instructions

Suggested commit message: **`Prepare ENGAGE v0.1.0 local release candidate`**.

These are owner instructions only; none were executed as publication actions. Review all changed/new files and licensing first:

```bash
git status --short
git diff --check
git diff --stat
git diff
# Inspect untracked docs, notices and screenshots as well; git diff omits them.
git ls-files --others --exclude-standard
```

After review and explicit license decisions, selectively stage approved files (avoid broad staging of unrelated files), review `git diff --cached --stat` and `git diff --cached`, repeat hygiene/tests, then create the approved commit. If licensing is still pending, keep this as a candidate rather than publishing v0.1.0.

After the owner pushes the approved release commit, obtain a fresh clone at that exact commit and execute the README install, lint/test/build and release browser gates; verify installation/persistence independently. Record the commit SHA and results. Only after those gates and owner publication approval:

```bash
# OWNER ONLY: run on the reviewed release commit; confirm no existing tag first.
git status --short
git rev-parse HEAD
git tag --list v0.1.0
git tag -a v0.1.0 -m "ENGAGE v0.1.0"
git show --stat v0.1.0
git push origin v0.1.0
```

Prepare a GitHub draft release targeting that tag, using `docs/release-notes-v0.1.0.md` after updating its pending-license wording to match the approved decision. Review source/notice obligations before attaching build artifacts. Verify the tag/commit, compatibility and limitations, then let the owner publish. Do not imply an unresolved license was selected or attach a personal database/demo profile. Stop at M6 review; do not begin Phase 2.
