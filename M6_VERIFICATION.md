# M6 verification — v0.1.0 candidate

Verification date: 2026-10-23. All acceptance activity used synthetic temporary profiles. No personal database was opened, edited or backed up. Browser journeys are automated Playwright/Chromium checks, not a claim of human acceptance or full accessibility certification.

## Environments and commands

Linux execution environment: Python 3.12.14, Node 24.19.0, npm 11.6.2, Playwright 1.64.1 with its Chromium revision 1248. Ubuntu 24.04 commands are documented but a freshly installed Ubuntu VM, alternate OSes, alternate browsers and hardware clipboard applications were not available. Existing installed system libraries and the shared Playwright browser binary were used; project packages and profiles were isolated.

### Public baseline clone

Executed a real `git clone --depth 1 https://github.com/74Cerillion/PEngage_Pentest-Engagement-Manager-.git /tmp/engage-m6-baseline`. Public HEAD was `5fa4dabd22849dd2db0941897ab5733d73ed53fd` (M5). Created a fresh `backend/.venv` using Python 3.12, installed `pip install --no-cache-dir -r backend/requirements.txt`, then `npm ci` with an empty dedicated cache. No source file, existing venv, node_modules or database was copied from the working directory.

Baseline results: 92 backend tests; 77 frontend tests; production build; two existing Playwright development journeys; `pip check`: all passed. npm installed 304 dependencies, audited 305 packages and reported zero known vulnerabilities.

### Clean M6 candidate

The owner prohibits committing/publishing automatically, so public HEAD cannot yet contain M6. Exported all intended tracked and nonignored candidate source/document files into `/tmp/engage-m6-candidate`, without `.git`, environments, dist or user data. This is a self-contained source candidate, **not a clone of a published M6 commit**. No hidden source/configuration is imported from the original checkout. Source hashes are recorded in [verification manifest](docs/verification-source-sha256.txt). Final reports/checklist were written after execution; they are not runtime inputs.

Executed, using the bundled Python 3.12 interpreter to create the fresh environment:

```bash
python3.12 -m venv /tmp/engage-m6-candidate/backend/.venv
cd /tmp/engage-m6-candidate/backend
.venv/bin/python -m pip install --no-cache-dir -r requirements.txt
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pip check
cd ../frontend
npm ci --cache /tmp/engage-m6-candidate-npm-cache
npm run lint
npm test
npm run build
PLAYWRIGHT_BROWSERS_PATH=/tmp/engage-m5-playwright npm run test:release
```

Here `python3.12` denotes the available 3.12.14 interpreter; the sandbox used its absolute bundled path. `npm` denotes the npm 11.6.2 CLI invoked with Node 24.19.0; its absolute tool location was used because npm was not on the initial shell PATH. These are tool locations, not application configuration. Browser binaries were installed previously, not downloaded during runtime tests.

Candidate results: fresh Python install and npm ci passed; **96 backend tests**, **77 frontend tests**, Ruff lint/format (17 Python files), ESLint, TypeScript/build, pip check, **three release-mode Chromium journeys** passed. All runtime source/test/lockfiles match the working candidate; no release build was copied from the original.

### Working checkout regression

From `backend/`: `.venv/bin/python -m pytest -q`, Ruff check/format check, pip check. From `frontend/`: `npm run lint`, `npm test`, `npm run build`, `npm run test:release`, `npm run test:e2e`, with the same Node/npm/browser selections above.

Results: **96 backend**, **77 frontend**, **3 release browser**, **3 development browser** tests passed. Release browser tests launch `python -m app` only; development journeys launch Uvicorn plus Vite. The release CLI fixes the bind address to `127.0.0.1`; tests use free ephemeral ports and stop their own children.

## Phase 1 acceptance matrix

| ID | Result | Executed evidence |
| --- | --- | --- |
| T-01 Create | PASS, automated | New root/child folders and notes; browser backend restart/reload checks hierarchy and full native document; backend adjacency/reconnection tests. |
| T-02 Rich content | PASS, automated | Browser creates H1/H2/H3, paragraphs, bullet lists, bold, plain code; compares JSON after restart and renders headings. Backend JSON integrity tests. |
| T-03 Screenshots | PASS, automated | Real browser ClipboardItem PNG + Ctrl+V; native selector JPEG/WebP; three images decoded after backend restart. Actual OS screenshot-app interoperability remains a manual check. |
| T-04 Keyboard | PASS, targeted | Browser tree arrows/Enter/F2/Delete/Escape, collapse/expand and focus return; editor arrows retain editing focus; visible buttons have accessible names. Unit tree/adapter tests supplement this. |
| T-05 CRUD | PASS, automated | GUI creates/edits/renames/moves notes/folders, moves to root/back preserving JSON, cancels deletion, confirms disposable subtree deletion with exact counts; backend rollback/cycle/deep-tree/conflict tests. |
| T-06 Offline | PASS, bounded | Browser blocks every non-loopback HTTP request during full local workflows, asserts no external requests; built fonts/images load locally. Backend runtime inspected for external services. This was a network-filtered browser test, not physical NIC disconnection or a firewall audit. |
| T-07 Save race | PASS, automated | Browser delays an acknowledged PATCH response, types B after A, verifies B remains current and persists; serialized autosave, stale-response and navigation-drain unit tests. |
| T-08 API interruption | PASS, automated | Browser stops its backend, types, observes Save Error and retained draft, rejects switching, restarts, retries, reloads persisted content. Separate 409 recovery exports both versions before explicit reopen. |
| T-09 Image safety | PASS, automated | Backend malformed/unsupported/mismatched/oversized/animated/traversal/symlink/ownership cases; adapter upload failures and unavailable-image alert; no note content execution. |
| T-10 Backup | PASS, automated | Offline backup then restore into fresh profile, restart GUI, compare entire tree/note JSON/image bytes and decode image; original profile DB unchanged. Integrity/tampering/locking/refusal tests supplement. |
| T-11 Fresh clone | PASS for public M5 baseline and clean M6 candidate; final publication check pending | Real public clone installs/runs existing baseline. Independent M6 source export fresh installs/builds/runs persistence/restart journeys. After owner commit/push, repeat against the exact public release commit before tagging. |
| T-12 Git hygiene | PASS, bounded audit | All 63 baseline tracked paths, empty index, five available commits/117 blobs scanned; candidate source/docs scanned; four PNGs visually reviewed as synthetic. No high-signal secrets or tracked runtime data found. No comprehensive forensic guarantee. |

The three journeys are named in `frontend/e2e/workspace.spec.ts`: “real editing, outage recovery, safe navigation, image lifecycle and offline restoration drill”; “revision conflict retains the draft and exports both versions before explicit reload”; “Phase 1 formatting, clipboard, CRUD, keyboard access and sanitized documentation”. Browser-generated files remain under ignored `frontend/test-results/`; only four reviewed synthetic screenshots were copied to docs.

## Failures and corrective actions

- An initial backend invocation from the repository root failed to import `app`; reran from the documented `backend/` directory. No path hack or application change was required.
- Initial new browser image-selector automation typed `/image` inside a code block and timed out. Corrected the test to place its caret in a paragraph and bounded file-chooser waits; reruns pass.
- The 390px browser check exposed a 405px page width: the application's generic button margins affected Mantine popup controls. Scoped generic button styling away from Mantine controls, allowed dialog actions to wrap and contained oversized editor content. Targeted and full browser reruns pass. This was a product CSS defect, not merely a changed assertion.
- Ruff reformatted the new conditional notices route. Final format/lint checks pass.

Remaining nonfatal output: Vite warns about >500kB chunks (largest JS 1.18MB, ~358kB gzip); existing Starlette TestClient warns about HTTPX deprecation; npm advertises a newer major version; pip disables an unwritable default cache. No broad dependency upgrade or misleading warning suppression was introduced.

## Remaining owner/manual gates

No unexecuted check is marked passed. Owner license selection remains pending by explicit instruction. Resolve attribution provenance before binary/bundle distribution. A final public M6 commit clone cannot be verified before the owner commits/publishes it. Human review, real desktop clipboard applications, screen readers, full contrast/WCAG audit, other browsers/OSes, clean Ubuntu VM, physical network disconnection, crash/power-loss durability and independent legal/security review were not performed. No commit, push, tag or release was created.
