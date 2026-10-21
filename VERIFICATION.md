# M1 verification — 2026-10-21 (Asia/Seoul)

Runtime: Node 24.19.0, npm 11.6.2, Python 3.12.14, SQLite 3.53.1 in the supplied Linux environment. Existing bundled runtime paths were used. No dependency versions changed. Tests never open real application data.

## Automated checks

| Check | Result |
| --- | --- |
| Backend `python -m pytest -q` | 35 passed |
| Frontend `npm test` | 29 passed across 4 files |
| `npm run lint` | Passed with zero warnings |
| `npm run build` | TypeScript and Vite build passed |
| Backend `python -m ruff check .` | Passed |
| Backend `python -m ruff format --check .` | Passed |
| Backend `python -m pip check` | Passed |
| `git diff --check` | Passed |

Backend coverage: creation, UUID/metadata, retrieval, partial updates, revision increment, database/application reconnection, exact structured JSON/Unicode/style/child/link preservation, absent records, malformed UUIDs/bodies/blocks, size limits, strict revision/version values, stale-write rejection, real competing SQLite connections, SQL-parameter safety, foreign-key enforcement, schema-version initialization/rejection, and XDG path resolution/repository exclusion.

Frontend coverage: creation and ID-only localStorage, saved title/document loading, editor snapshot conversion, real shell save-state feedback, API failures, missing remembered notes, health failures, JSON request contracts, expected revision in PATCH, unsupported responses, 700 ms debounce, rapid edits, edits during an active request, acknowledgement of older snapshots without false Saved state, remaining debounce time, retained failed drafts, explicit retry, conflict blocking, title validation, beforeunload warning lifecycle, and ignoring responses after unmount. UI tests stub BlockNote rendering; the acceptance run below uses the real editor.

Non-blocking upstream warnings remain from M0: Starlette's HTTPX TestClient adapter is deprecated; Vite reports a large editor bundle. Neither warning was suppressed. No extra framework was installed to remove them.

## Required browser acceptance — completed

Used an isolated origin `127.0.0.1:5175`, backend `127.0.0.1:8002`, and `XDG_DATA_HOME=/tmp/engage-m1-controlled/data`. Thus the database was `/tmp/engage-m1-controlled/data/engage/engage.sqlite3`, outside Git and outside real application data.

| Step | Observed result |
| --- | --- |
| 1. Launch ENGAGE | Two panes; backend health online |
| 2. Create a note | Created through UI; title “M1 restart acceptance” |
| 3. Enter an H1 | “Persistence acceptance” rendered as an H1 |
| 4. Enter paragraphs | Paragraphs A and B entered |
| 5. Format additional text | “Bold evidence” bold; “italic details” italic |
| 6. Wait for Saved | Saved observed after real PATCH |
| 7. Refresh | Same ID reopened from localStorage |
| 8. Verify content | H1, paragraphs, bold and italic restored; DOM inspected |
| 9. Stop backend | Actual child exit confirmed; HTTP connection refused on 8002 |
| 10. Restart backend | New Uvicorn process; health responded |
| 11. Reload ENGAGE | Note loaded through GET again |
| 12. Verify saved content | Exact document JSON and revision compared before/after restart; rendered formatting restored |
| 13. Modify existing note | Added paragraph C after backend restart |
| 14. Verify persistence | Saved observed; later reopening retained paragraph C |

Additional checks completed:

- Stopped **both** backend and Vite; verified both ports refused connections. Closed the browser tab, restarted both applications, and opened a new tab on the same origin. The note, formatting, title and paragraph C reappeared without another creation request.
- Stopped the backend while the note was open, changed its title, and observed Save Error (Vite returned 502). The draft remained visible. Restarted the backend, used Retry save, observed Saved, refreshed, and confirmed the changed title persisted.
- Captured the final UI as `outputs/engage-m1-preview.png` in the enclosing task directory, outside the Git repository.

An initial run on ports 8001/5174 proved refresh persistence but was **not** counted as a restart test: cancelling tool sessions left their child servers listening. The restart acceptance was repeated with a test-only subprocess controller in the task's `work/` directory. It explicitly terminated/waited for each child, and independent requests confirmed refused connections before restarting. No shutdown endpoint or process controller was added to ENGAGE.

## Limits and operational notes

- A browser tab was closed and reopened; the entire host browser process/OS was not terminated. Full browser-process/OS crash, power loss, disk-full/permission failures, and prolonged lock contention were not tested. LocalStorage and SQLite provide the persistence boundary; waiting for Saved is required.
- Ubuntu package installation and a fresh dependency installation were not repeated for M1. Existing M0 environments and lockfiles were used; dependency validation passed.
- No packet-level external-network audit was performed. Code/configuration use only local HTTP/WebSocket targets and bundled assets, with a restrictive CSP; no external runtime service is configured.
- The primary/default application data directory was not written during testing. First-start schema creation and reconnect behavior were exercised using temporary paths, and both default XDG/fallback resolution branches have automated coverage.
- The preliminary test listeners on ports 8001/5174 outlived their tool sessions. The sandbox cannot signal those orphaned processes from a new process namespace. They are isolated from the application defaults; stop those specific temporary listeners from the host terminal with `fuser -k -TERM 8001/tcp 5174/tcp` if still present. The controlled acceptance servers are shut down separately after verification.

No commit, push, tag, remote publication, or M2 implementation was performed.
