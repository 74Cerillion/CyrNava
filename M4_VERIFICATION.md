# M4 verification and owner acceptance

## Executed automated checks

Commands below run from the repository root unless a `cd` is shown. The test environment used the existing Python 3.12 virtual environment, bundled Node 24.19.0 and npm 11.6.2. npm was invoked through its local CLI path in the agent environment; the equivalent ordinary npm commands are shown here.

```bash
cd backend
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pip check
cd ../frontend
npm test
npm run lint
npm run build
cd ..
git diff --check
```

| Check | Actual outcome |
| --- | --- |
| pytest | 72 passed; 1 existing Starlette/HTTPX deprecation warning |
| Ruff check | Passed |
| Ruff format check | 10 files already formatted |
| pip check | No broken requirements; nonfatal existing cache-permission warning |
| Vitest | 72 passed across 9 files |
| ESLint, warnings treated as errors | Passed |
| TypeScript + Vite production build | Passed; existing large-bundle warning retained |
| Git whitespace check | Passed |

No tests use real application data. Backend fixtures inject temporary database paths. Images are generated in temporary test memory/directories. Frontend tests use existing Vitest/Testing Library; no additional test framework was introduced.

New backend cases cover PNG/JPEG/WebP uploads, metadata, IDs, retrieval/MIME/security headers, malformed/truncated/unsupported/mislabeled/animated files, byte/dimension/pixel limits, nonexistent owners/assets, UUID/path/symlink attacks, write/fsync/metadata failure, exclusive-create collision, reconnection and application restart, exact native document persistence, ownership and revision rejection, migration/repeated initialization, recursive/direct deletion and retry of failed cleanup. Existing folder/note/health tests still run.

New frontend coverage includes raw upload contract and errors, invalid response references, upload hook, clipboard insertion, image block positions/metadata, save/reload through the application boundary, missing-image feedback, abort on note replacement, pending uploads before autosave flush, navigation blocked by failed pending uploads, and optional drop rejection. Existing serial autosave, stale acknowledgement, conflict, note/folder navigation and editor-isolation tests still run.

Adapter tests mock the public BlockNote boundary. File-picker native behavior and browser clipboard input were additionally exercised against real installed BlockNote below.

## Executed browser and live-server checks

Environment: backend `127.0.0.1:8014`, Vite `127.0.0.1:5187`, `ENGAGE_API_PORT=8014`, XDG data under `/tmp/engage-m4-acceptance/data/`. A temporary copy of the existing test-generated M1 schema fixture was upgraded on startup. Controllers and snapshots are in the enclosing task's `work/`, outside Git. No default data directory or existing development listener was used.

1. Backend health returned `{"status":"ok"}` and the browser opened the fixture note.
2. Put a generated PNG image on the **browser's binary clipboard** via the automation clipboard API, focused real BlockNote, pressed Ctrl+V. The core image block appeared and loaded from a generated `/api/assets/{UUID}` URL. This exercised real clipboard input/upload/rendering, not a synthetic React paste test. It did not exercise an OS screenshot tool.
3. Used `/image` → Image → Upload image and the real file chooser for **JPEG, WebP and PNG**. All four images (including clipboard PNG) rendered at natural width 720 and used persistent local references.
4. Observed Saved. Retained native headings, bold text and paragraphs around images; added an H2 and further text.
5. Opened a new-note dialog immediately after editing, created a companion note, switched back, and verified all images/text. Navigation drained pending document edits.
6. Refreshed. All four images loaded, the title/content remained, and Saved was displayed.
7. Captured both complete note API records. Closed the browser. Sent the test controller `stop-both`, observed child-process exits, and independently confirmed **connection refused** on both ports. Restarted both services as new child processes. Both note records matched exactly, including document JSON, IDs, revisions and timestamps.
8. Each image GET after restart returned the correct MIME and bytes equal to its local stored file (PNG 8452 bytes each, JPEG 8782, WebP 24096). Opened a fresh browser tab; all four images decoded successfully with natural width 720.
9. Against the running HTTP server, submitted disguised text (422), SVG (422), PNG with JPEG MIME (422), and a body over 10 MiB (413). Both existing note records remained unchanged.
10. Through the running API, created a disposable note, uploaded and saved an image block, then deleted that note at its expected revision. GET became 404, its asset file was removed, and the two original notes and four unrelated images remained intact.
11. Temporarily renamed one test asset file. Refreshed the actual browser: a visible alert said “A saved image is unavailable. Its reference is preserved; check local asset storage.” The editor and surrounding text remained usable. Restored the file, refreshed, and confirmed all four images decoded again.
12. Saved the restored-note preview to `../engage-m4-preview.png`. Test-only server processes were shut down after verification; no changes were made to the user's existing ports 8000/5173.

The browser file-chooser automation intermittently took a long time, but each selected format was subsequently confirmed in the DOM and by successful image decoding. A returned intermediate state was not counted as completed upload.

### Failures encountered and corrected

- An old regression case rejected every image block. M4 intentionally changes that contract; the case now rejects unsupported video and new image-specific validation tests cover malformed references.
- The installed FilePanel API requires tab objects rather than tab-name strings. TypeScript caught this; the local-only tab now uses installed `UploadTab` and the documented object shape.
- The original adapter test mock lacked the newly used FilePanel exports. The mock was expanded, then the test and full suite passed.
- ESLint identified an imperative-handle dependency issue; the stable autosave flush function is captured explicitly.
- Ruff caught import order/long lines, which were corrected.
- The first test-server controller startup needed backend PYTHONPATH for fixture imports; it was corrected before launching the test servers.

### Not executed / not claimed passing

- OS screenshot capture using Ubuntu's screenshot tool (binary browser clipboard paste was executed).
- Physical network disconnection and the complete offline A–G sequence. Code, CSP and relative URLs remain local; that does not substitute for a disconnected-machine test.
- Computer reboot, forced power loss or file-system crash simulation.
- Every invalid/oversized file-selector GUI case. The running HTTP API and automated client/adapter error tests were exercised; repeat the GUI steps below during review.
- Broad Firefox/Safari/platform clipboard coverage, screen-reader testing, sustained large-image/concurrency pressure, or forensic-original preservation (not implemented).

**Do not declare the full owner acceptance sequence passed until these required human checks are complete.**

## Reproducible owner acceptance procedure (A–G)

First install the pinned dependencies using README setup. For a safe acceptance run, use a separate data directory rather than your real notes. From the repository root in terminal 1:

```bash
M4_REVIEW_DATA=$(mktemp -d /tmp/engage-m4-review.XXXXXX)
# Record this exact directory for the restart; do not generate a new one then.
printf '%s\n' "$M4_REVIEW_DATA"
cd backend
XDG_DATA_HOME="$M4_REVIEW_DATA" .venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8014
```

From the repository root in terminal 2:

```bash
cd frontend
ENGAGE_API_PORT=8014 npm run dev -- --port 5187
```

Open `http://127.0.0.1:5187`. If either test port is occupied, inspect its listener or use another pair consistently; do not kill unrelated processes. Do not delete real user notes to test lifecycle behavior.

### A. Initial setup

Create an initial test note and a companion note. Open the first, set a title, and confirm the page-load backend indicator is online. A direct `http://127.0.0.1:8014/health` GET should return `{"status":"ok"}`. Reopening this note establishes the “existing note” starting point.

### B. OS clipboard screenshot

Use Ubuntu's screenshot tool to capture a non-sensitive test window and **copy** the screenshot, rather than only saving a file. Click a paragraph in BlockNote and press Ctrl+V. Confirm an inline image appears. Wait for Uploading image… to disappear and Saved to appear. Confirm a generated file exists under the recorded XDG directory's `engage/assets/` and metadata in `engage/engage.sqlite3`. No capture should appear in the repository.

### C. File selection

For each PNG, JPEG and WebP fixture: type `/image` in an empty paragraph, choose Image and Upload image, then select a local static file. Confirm the image renders and autosave finishes. The image selector exposes Upload only, without external URL embedding. File drops are deliberately disabled.

### D. Persistence

Put an H1, several paragraphs, bold text and an H2 around the images. Wait for Saved. Navigate to the companion note and return; compare content and image positions. Refresh and compare again. Stop both terminal servers with Ctrl+C. Restart using the **same recorded XDG directory**, same ports and commands. Reopen the original note; verify formatting and images. Make a further edit and confirm it persists after reload. Do not replace the directory with a new mktemp result on restart.

### E. Invalid uploads and failures

Use the selector for a text file renamed `.png`, an unsupported SVG/GIF/PDF, and a file over 10 MiB. Expect understandable upload feedback, no successful permanent URL, and intact existing content. An empty failed placeholder may remain; reuse or remove it. For request-level limits/decoding, automated tests additionally cover mismatched MIME, truncated data, animation, excessive width and total pixels.

Stop only the backend and attempt another image upload: expect a visible failure and intact existing content. Restart it and select/paste again. A document save failure should remain visible as Save Error rather than Saved. The OS may report a beforeunload warning if you close during an unfinished upload/save; forced closing remains outside M4 recovery guarantees.

### F. Lifecycle

Create a **disposable test note** and upload an image. Wait for Saved. Record the asset URL/ID (browser inspector or database metadata). Delete that test note through ENGAGE's confirmation dialog. Its asset GET must return 404 and its generated file should be gone. Reopen your original test note and verify all unrelated images remain. Recursive folder deletion should behave equivalently; this also has automated coverage. If storage permissions temporarily prevent unlink, deletion remains committed and cleanup retries on startup.

### G. Offline

Disconnect external networking using your normal OS controls while keeping loopback available. Start/restart the already-installed servers with the same XDG directory. Open the image note; confirm all images load. Capture/copy another screenshot, paste it, wait for Saved, refresh, and verify. Check the browser network panel for application requests: assets, scripts, fonts and API traffic must stay on the local origin. Restore networking when finished. Installation itself requires packages to be available; normal application operation does not.

Stop at M4 and report any discrepancy before approval. Do not commit/push as part of this procedure.
