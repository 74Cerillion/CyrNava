# M5 verification record

## Final executed checks

Environment: Python 3.12 virtual environment, Node 24.19.0, npm 11.6.2, `@playwright/test` 1.64.1, Chromium/Chrome Headless Shell 156.0.8078.4 (Playwright build 1248). Tests run on Linux. Existing Python/runtime/frontend package versions were preserved.

From the repository root, the actual shell used the bundled Node path and local npm CLI because npm is not on this tool environment's default PATH:

```bash
export PATH=/home/cerillion/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin:$PATH
NPM_CLI=/home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/work/npm/package/bin/npm-cli.js

node "$NPM_CLI" --prefix frontend run lint
node "$NPM_CLI" --prefix frontend run build
node "$NPM_CLI" --prefix frontend test

cd backend
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pytest -q
.venv/bin/python -m pip check
cd ..

PLAYWRIGHT_BROWSERS_PATH=/tmp/engage-m5-playwright \
  node frontend/node_modules/playwright/cli.js test --config frontend/playwright.config.ts

git diff --check
```

Ordinary installed environments use `npm run lint`, `npm run build`, `npm test` and `npm run test:e2e` from `frontend/`. Browser setup was executed separately:

```bash
# From frontend, with the same bundled Node on PATH:
PLAYWRIGHT_BROWSERS_PATH=/tmp/engage-m5-playwright \
  node node_modules/playwright/cli.js install chromium
```

The package was installed exactly with `npm install --save-dev --save-exact @playwright/test@1.64.1`, using the existing isolated npm cache. Browser/package installation used authorized network access; application/test requests did not use external runtime services.

| Check | Final outcome |
| --- | --- |
| Backend pytest | **92 passed**; existing Starlette HTTPX deprecation warning |
| Frontend Vitest | **77 passed**, 10 files |
| Playwright | **2 passed**, 1 worker, 0 retries; final corrected run 14.3 seconds |
| Ruff | Passed; 14 Python files formatted |
| ESLint | Passed, zero warnings allowed |
| TypeScript/Vite build | Passed, includes e2e/config TypeScript; existing large-bundle warning |
| pip check | No broken requirements; nonfatal cache-permission warning |
| Git whitespace | Passed |

Existing M0–M4 suites were retained. M5 adds 20 backend tests and 5 frontend tests plus 2 browser journeys. Database/deletion/image runtime implementations were preserved except for the new backend-lifetime lock; there is no schema migration or new route.

## Failure-injection matrix

| Required scenario | Executed evidence |
| --- | --- |
| 1. Backend shutdown | First Playwright journey terminates its actual FastAPI child, edits the note and observes Save Error plus retained text. The Vite proxy logs connection refusal, an expected injected failure. |
| 2. Backend recovery | Same journey starts a new backend process, clicks Retry save, waits for Saved and reloads; retained text persists. |
| 3. Rapid editing / old response | Hook tests cover serial requests and newer drafts. Browser holds the response from a real committed PATCH A, types B while A remains in flight, verifies Unsaved Changes, releases A and confirms B reaches SQLite. |
| 4. Revision conflict | Existing API tests plus four real concurrent DB updates verify CAS. Second Playwright journey writes a newer title through the actual API, then edits the stale browser. 409 retains local content; actual download contains local and saved versions; explicit reopen reads current state and subsequent edits persist. |
| 5. Interrupted navigation | During the real outage, browser tries to switch to Companion; navigation fails visibly and the original note/draft remain open. Existing component/hook tests cover active saves and queued edits. |
| 6. Recursive deletion failure | Existing `test_recursive_delete_rolls_back_everything_if_a_statement_fails` is retained. New `test_recursive_delete_failure_preserves_asset_metadata_and_files` injects a late root-delete trigger failure after descendant deletion would have occurred; API returns 503 and all folders/notes/asset rows/file bytes remain intact. |
| 7. Backup restoration | Temporary-profile API test and complete real-browser CLI restoration drill below. Missing/corrupt DB/manifest/assets, mismatched hashes, symlink/traversal metadata, unsafe destinations, copy failures and overwrite attempts are rejected. |
| 8. Asset retrieval failure | Browser temporarily renames its test image, reloads and observes the missing-image alert without losing text; file is restored and image renders again. Existing M4 tests remain. |

Additional injection: an AFTER UPDATE note trigger aborts the transaction. HTTP returns generic 503 and the original title, document and revision remain unchanged. Four connections competing at one expected revision produce exactly one winner/revision increment.

## Mandatory restoration drill: executed

The first Playwright journey performs this entire sequence, without a personal profile:

1. Allocates a new OS temporary directory and two free loopback ports; launches its own FastAPI/Vite children. There is no test setting that points at an existing profile/server.
2. In real BlockNote creates `M5 Training / Nested / Evidence`, an H1, paragraph, bold text and a PNG image through the actual file selector/upload API. Adds a Companion note.
3. Waits for Saved, reloads, and verifies heading/formatting and image decoding.
4. Exercises actual backend outage/retry/navigation protection and held-response typing. Renames Nested to Verified folder. Opens folder deletion, verifies the two-note impact and cancels.
5. Temporarily hides/restores the image and verifies visible failure then successful decoding.
6. Records the complete tree and note API JSON and stored image bytes. Stops **both** server child processes and waits for their exits.
7. Invokes the actual CLI via the backend virtual environment:

```text
python -m app.backup backup
  --data-dir <temporary-root>/original-data/engage
  --destination <temporary-root>/backup

python -m app.backup restore
  --source <temporary-root>/backup
  --data-dir <temporary-root>/restored-data/engage
```

8. Starts fresh servers with `XDG_DATA_HOME=<temporary-root>/restored-data`. Reloads the browser, which reopens the same note ID.
9. Compares complete tree and note records exactly: folder relationships, IDs, native JSON, timestamps, revisions and image references. Compares stored image bytes exactly. Confirms real BlockNote H1, bold text and latest paragraphs. Confirms the image has natural width 600 and decodes successfully.
10. Verifies that the original profile database bytes remain unchanged. The separate API restoration test also modifies a restored note and verifies the original note remains unchanged.
11. Saves `restored-workspace.png` and `restoration-evidence.json` to the ignored test output directory. The evidence records zero external application requests; the browser aborts any attempted non-loopback HTTP request.
12. Stops all children in `finally` and removes the temporary fixture profiles. Retains only synthetic diagnostic evidence under ignored test results.

Review copies outside the repository:

- `../engage-m5-restored.png`
- `../engage-m5-restoration-evidence.json`

The evidence is generated test data, not user notes. The screenshot demonstrates restored native editor rendering; the JSON shows exact restored records and image byte count. `BACKUP_RESTORE.md` contains the owner procedure for real data.

## Intermediate failures and corrections

These were not counted as passing results:

- Ruff caught import order/long lines during initial CLI/test creation; corrected before passing final checks.
- An attempted guard against every ancestor `.git` directory rejected the controlled environment's `/tmp` Git wrapper, causing backup tests and a browser rerun to fail before copying. The guard was aligned with the existing application's known-checkout policy. Documentation explicitly requires keeping backups outside other repositories too. Source data and existing destinations were never overwritten.
- A browser rerun's restored-record comparisons passed, but its exact H1 assertion failed: caret-based rapid-edit automation had inserted paragraph A/B into the heading before backup. Inspection showed the restored JSON matched that source exactly. The test now clicks the intended last paragraph and uses keyboard input there. The corrected journey passed without retries.

No database rollback, conflict, upload, retry or restoration-rendering defect remains unresolved in the final executed paths.

## Remaining manual/platform checks and limits

Not executed or guaranteed:

- OS screenshot-tool capture and every platform's native clipboard behavior. M4 clipboard tests remain; M5 uses the real file selector for its image drill.
- Physical network disconnection. The main browser test blocks/records non-loopback HTTP and observed none; this is not a physical offline-machine test.
- Firefox/Safari, cross-platform locks, assistive technologies and a broad accessibility matrix.
- Sustained maximum-size image/resource pressure, hard power loss or abrupt tool termination during publication.
- Guaranteed beforeunload prompts or preservation of unsaved drafts after forced browser/process death. Existing warning logic is unit tested; browser policy may suppress dialogs.
- Recovery JSON automatic merge/import. The user retains both versions and manually compares/reapplies needed edits after deliberately reopening; no force-write is offered.

No relevant automated test was left unexecuted. Owner review and a normal local run remain appropriate. No personal profile, source Git history, existing development listener, commit, push or tag was changed by the tests.
