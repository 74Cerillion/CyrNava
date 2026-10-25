# ENGAGE v0.1.0 — Application lifecycle engineering report

Date: 2026-10-26 (Asia/Seoul).

Source implementation is ready for review. Automated source checks and isolated browser verification are recorded below. The user's installed desktop snapshot has not been replaced by this implementation session; final installation and a graphical desktop smoke test remain operational acceptance steps. No commit, push, tag, database migration or personal-note modification was performed.

## A. Root cause and initial investigation

Closing a browser window previously removed the client, but no code associated client lifetime with the backend. `desktop/launcher.py::start` spawned a detached worker and returned. The worker ran Uvicorn indefinitely. Firefox may reuse an existing browser process, so waiting for a Firefox command's process to exit would not describe ENGAGE tab/window lifetime.

| Investigation | Existing behavior and retained boundary |
| --- | --- |
| FastAPI startup | Desktop worker calls `create_app(frontend_path=...)`, then Uvicorn on loopback. |
| Startup script | Existing Python launcher/installer and generated desktop entries; no new shell script is needed. |
| Independent entrypoints | `python -m app` serves a release; `uvicorn app.main:app` serves development. Both remain independent. |
| Frontend serving | Desktop FastAPI serves compiled Vite assets and API on one origin. |
| Vite development | Separate port 5173 proxies API to the development backend. No Vite is started for normal desktop use. |
| Firefox dispatch | Previously `xdg-open` selected the default browser. New installs record Firefox and request `--new-window`; old configurations keep their fallback until reinstalled. |
| Multiple tabs | Notes already use revision concurrency, but tabs had no lifecycle identities. Each loaded page now owns an independent random UUID. |
| SQLite connections | `Database.connect` opens a connection per operation, enables foreign keys, commits/rolls back, then closes it. No process-global database connection needs a new shutdown mechanism. |
| Autosave | Existing 700 ms debounce, serial PATCH queue, edit generations, revisions, flush/retry/conflict UI and dirty-page warning are retained. Previously pending edits were memory-only. |
| Process management | Reuse private locks, `/proc` start-time/nonce checks, readiness probes, pidfd manual stop, local logs and installer rollback. Add an owning supervisor rather than another framework. |

Firefox's command may be forwarded to an existing process; window identity is therefore tracked by leases, not process exit. No browser extension, dedicated normal-use profile, browser preference change or system service was introduced. See [Mozilla command-line documentation](https://firefox-source-docs.mozilla.org/browser/CommandLineParameters.html).

## B. Architecture and decisions

```text
Desktop icon → launcher open (short-lived dispatch, serialized by launcher.lock)
                  ↓ start/reuse + readiness + Firefox --new-window
              launcher supervise (background owner, supervisor.lock)
                  ├── retained Popen child → launcher worker → Uvicorn/FastAPI
                  └── secret-authenticated loopback lease inspection

Each browser page → useLifecycle → registration / heartbeats / close hint
                                       ↓
                            app.lifecycle.Sessions (memory only)
                                       ↓ drain claimed atomically
                         supervisor SIGTERM → wait → child reaped → exit

Editor edits → synchronous browser draft snapshot → ordinary revision-checked autosave
Reopen       → explicit draft choice → ordinary save or existing conflict review
```

The supervisor is another action in the existing launcher, not a daemon framework. The initial icon command may exit while the supervisor continues owning the backend. Normal close stops that supervisor after it reaps the worker. Startup/shutdown locks prevent duplicate workers and a relaunch racing previous cleanup. Zombie processes no longer count as live workers.

`create_app(..., sessions=None)` defaults to unmanaged operation. Only the desktop worker supplies `Sessions`, using an instance nonce and a separate 256-bit random supervisor secret. The secret is passed through the child environment, removed from that environment in the worker, and never sent to the browser or saved in configuration/state. This retains launcher authority without accepting public shutdown commands.

New HTTP surface:

| Route | Purpose |
| --- | --- |
| `GET /api/lifecycle` | Public same-origin configuration; unmanaged servers return `managed: false`. |
| `POST /api/lifecycle/sessions/{uuid}` | Managed-only registration/renewal/close. Requires exact loopback Origin/Host, compatible fetch-site header, current instance and validated sequence/action. No CORS permission is added. |
| `GET /api/lifecycle/supervisor` | Managed-only, secret header required. Prunes leases, reports phase, and atomically claims drain when its deadline is reached. There is no unrestricted shutdown endpoint. |

Keeping lease expiry and drain selection on the ASGI event loop avoids a poll-then-signal registration race. New leases cancel a pending grace period. Once drain is claimed, new leases and new mutating requests receive 503; the supervisor then terminates its child. Already accepted handlers may finish within the graceful timeout. Lifecycle configuration/readiness also refuse a draining instance.

| Default | Value / reason |
| --- | --- |
| Heartbeat | 5 seconds, as proposed. |
| Lease expiration | 20 seconds, tolerating several missed renewals. |
| Empty-session grace | 5 seconds, allowing refresh/reconnection. |
| Startup registration grace | 60 seconds from worker setup, allowing Firefox to start. Missing registration is reported after cleanup. |
| Readiness deadline | Existing 20 seconds, then up to 17 seconds for supervisor cleanup before any escalation (and a bounded final wait). |
| Supervisor poll | 250 ms; at most 1 second per private HTTP request. |
| Backend unresponsive | Cleanup after 25 seconds without a successful private probe. |
| Accepted-request grace | Uvicorn 8 seconds. Supervisor waits 10 seconds after SIGTERM, then kills only its retained child and waits up to 5 more seconds. |

Tests shorten lease timings in private temporary configuration files; normal installer configuration uses the defaults. Closed-session sequence tombstones prevent an older in-flight heartbeat from undoing a later close. Expired entries are pruned on activity and inspection; the registry is capped at 1,024 entries.

Draft recovery uses existing browser localStorage rather than adding IndexedDB, a queue framework, a new database table or dependencies. It is synchronous so each edit is copied before debounce/network/unload. The tradeoffs are browser quota, per-origin/profile storage, plaintext recovery copies and main-thread serialization cost. SQLite remains authoritative. Future changes can replace this small storage boundary without modifying BlockNote APIs or SQL.

No dependency or version changes. Python uses its standard library plus existing FastAPI/Pydantic/Uvicorn. Tests use existing pytest, Vitest, Testing Library and Playwright. Firefox test binaries were downloaded as development tooling only; application operation needs no internet.

## C. Complete execution flow

1. The installed desktop entry invokes `desktop/launcher.py::main` with `open`. Under `launcher.lock`, `start` verifies any existing PID/nonce/readiness/protocol. An occupied unverified port produces an error and no signal.
2. A new launch spawns `supervise`. It retains a `Popen` worker, holding `supervisor.lock`; the worker holds `backend.lock`, creates the opt-in application, publishes its identity and starts Uvicorn.
3. The existing lifespan acquires the profile lock, initializes SQLite if needed and performs the existing asset reconciliation. The application does not change schema or document format.
4. `ready` checks the owned worker, identity endpoint and actual frontend root. `open_browser` requests Firefox's new window. Its process lifetime is intentionally ignored. A dispatch error stops a newly created backend; an existing active instance is preserved.
5. React `App` mounts `useLifecycle`. It reads `/api/lifecycle`, then POSTs its page UUID, instance and increasing sequence. Managed pages renew at the configured interval, including ordinary background tabs. Page visibility returning, network returning and bfcache `pageshow` trigger renewal.
6. Typing reaches `KnowledgeEditor.onChange` and `useAutosave.changeDocument`. `retainDraft` calls `drafts.storeDraft` immediately with native JSON, title, note ID, writer ID, edit token and last acknowledged SQLite revision. The ordinary serial autosaver then debounces and PATCHes the note.
7. An acknowledgement removes recovery data only if its token still matches the stored snapshot and no newer local edit remains. If newer edits exist, their snapshot is retained with the newly acknowledged base revision. Other tabs' records are untouched.
8. On final page closure, `pagehide` attempts a small JSON beacon containing session identity/sequence/action only. No note data is sent by beacon. Failed or absent delivery is handled by heartbeat expiration. Hidden tabs do not count as closed merely because visibility changes.
9. `Sessions.inspect`, requested only by the supervisor, detects no leases, enters grace, then claims drain if no page returns. New writes/leases are refused. SIGTERM lets Uvicorn drain accepted requests; connection context managers complete/roll back and close, the lifespan releases the profile lock, and the worker exits. The supervisor waits/reaps and logs its exit. A forced timeout targets only its retained child.
10. Reopening from the icon starts a fresh managed instance. The UI reads SQLite as before. `PersistentNote` calls `findDrafts` for the note; it offers prior-page drafts before mounting an editor. Selecting a compatible draft submits it through ordinary revision-checked autosave. A newer saved revision instead opens the existing conflict workflow, requiring review/export before reopening the saved version. Choosing saved content retains the draft; it is deferred only for this loaded page and may be offered after a later reload.

If an acknowledgement was lost after a commit, recovery may encounter the newer database revision even when the content looks familiar. It refuses to overwrite automatically. This deliberate conservative behavior protects against ambiguous writes and other tabs.

## D. Files changed

Paths below are relative to this repository. Existing editor/schema/database files and all pinned dependency files are preserved.

| File | Responsibility / why changed |
| --- | --- |
| `.gitignore` | Exclude downloaded draft recovery JSON, alongside existing conflict recovery exports. |
| `README.md` | Explain Firefox installation, automatic closure and browser recovery storage; remove obsolete memory-only claims. |
| `desktop/launcher.py` | Owning supervisor, bounded drain/termination, lifecycle-aware readiness, Firefox dispatch, restart coordination and safe failure handling. Standard library; worker imports existing backend runtime. |
| `desktop/install.py` | Check/record Firefox executable. Existing release copying, private venv, smoke check, profile preservation and rollback remain. |
| `backend/app/lifecycle.py` (new) | In-memory lease model/timing, request validation, same-origin registration, authenticated inspection and drain gate. |
| `backend/app/main.py` | Optional lifecycle injection into the existing app factory. Development defaults remain unmanaged. |
| `backend/tests/test_lifecycle.py` (new) | Clock-controlled startup/expiry/grace/tombstone/capacity tests plus real FastAPI route/security/drain/development tests, with temporary SQLite. |
| `backend/tests/test_desktop.py` | Extend real subprocess tests for two leases, crash expiry, startup failure, duplicate reuse, Firefox dispatch, bounded forced termination and unrelated-child survival. Update new-launch opener failure expectation to safe cleanup. |
| `backend/tests/test_health.py` | Record the intentionally added lifecycle configuration route in the exact route-surface test. |
| `frontend/src/drafts.ts` (new) | Application-owned recovery JSON/storage/export boundary; per-page identities and token-guarded acknowledgement cleanup. Uses browser APIs and generic note JSON, not BlockNote internals. |
| `frontend/src/drafts.test.ts` (new) | Identity/revision/JSON integrity, other-tab isolation, stale acknowledgement and incompatible-record preservation. |
| `frontend/src/hooks/useLifecycle.ts` (new) | Page registration/renewal/close hints/reconnection, request timeout and visible connection failure. |
| `frontend/src/hooks/useLifecycle.test.tsx` (new) | Registration, renewals, pagehide/pageshow, unmanaged behavior and fresh-instance reconnection. |
| `frontend/src/hooks/useAutosave.ts` | Synchronous draft retention and guarded cleanup around the unchanged serial saver; conservative recovered-revision handling and best-effort background flush. |
| `frontend/src/hooks/useAutosave.test.tsx` | Verify newer snapshots retain correct revisions behind an old save, and storage failures remain visible with a close warning. Existing concurrency tests retained. |
| `frontend/src/components/PersistentNote.tsx` | Recovery choice before editor mount, original revision/conflict flow and storage warnings; flush still drains uploads first. |
| `frontend/src/components/DraftRecovery.test.tsx` (new) | Explicit recovery, no premature deletion, stale revision blocking and saved-note choice retaining data. |
| `frontend/src/App.tsx` | Mount session tracking, show connection loss, pause editing/management while disconnected, explain unresolved recovery on navigation. |
| `frontend/src/App.test.tsx` | Existing shell tests provide the explicit unmanaged lifecycle response. |
| `frontend/src/test-setup.ts` | Clear synthetic browser storage between tests to prevent recovery records crossing test boundaries. |
| `frontend/e2e/lifecycle.spec.ts` (new) | Real temporary managed installations: two browser pages, closure/port release/restart, native formatted draft recovery and exact JSON comparison, killed test-owned browser. Copies built assets to isolate each installation. Graphical dispatch/Zenity are stubbed, not the browser/editor/backend. |
| `docs/architecture.md` | Describe optional desktop supervision and recovery boundaries. |
| `docs/desktop-launcher.md` | Updated start/close/confirm/development/recovery instructions and limitations. |
| `LIFECYCLE_REPORT.md` (new) | This engineering and acceptance record. |

## E. Testing

Tests use fresh temporary databases, installation directories and isolated browser contexts. No tests target the personal ENGAGE profile. A network permission grant enabled loopback subprocess verification in this session; no test-only event-loop workaround was needed for the final runs.

| Command / execution | Result |
| --- | --- |
| Backend `.venv/bin/python -m pytest -q` | **190 passed**, one existing Starlette/httpx deprecation warning; 18.81 seconds. |
| Frontend `npm test` | **178 passed**, 15 files. |
| Frontend TypeScript `tsc --noEmit` | Passed. |
| `npm run lint` | Passed. |
| `npm run build` | Passed; existing large-chunk warning remains. |
| Backend `.venv/bin/python -m ruff check . ../desktop` and format check | Passed; 25 Python files already formatted. |
| Chromium targeted `npx playwright test e2e/lifecycle.spec.ts` | Both lifecycle journeys passed, including exact recovered native JSON and bold rendering. |
| Full Chromium release `npm run test:release` | **6 passed**, 52.6 seconds. After final supervisor startup-cleanup changes, both targeted lifecycle journeys also passed again (11.4 seconds). |
| Owner-run `npm run build && npx playwright install firefox && npx playwright test e2e/lifecycle.spec.ts --browser=firefox` from `frontend` | **2 passed**, 19.0 seconds, confirmed by terminal screenshot. Real isolated Firefox 157 test engine. Subsequent fixture hardening is noted below. |
| `git diff --check` | Passed during review; checked again before delivery. |

Acceptance mapping:

| Test | Evidence / limits |
| --- | --- |
| A Normal launch | Real supervisor/worker/readiness + isolated browser registration/editing pass. Actual Firefox command arguments unit-tested; desktop graphical dispatch is stubbed in automation. |
| B Normal closure | Actual final page closure leads to worker reaping and a successful bind to its released test port. |
| C Multiple tabs | Closing one page preserves editing in another; closing the last stops the backend. Independent lease/grace tests also pass. |
| D Browser crash | Kills only a separately launched test browser process; expiration stops the backend without a close beacon. |
| E Unsaved changes | Confirmed paragraph survives restart; immediately closed title/formatted paragraph recovers through browser storage and revision-checked save. Old revision recovery is blocked and storage failure reported. |
| F Startup failure | Missing runtime and deliberately invalid temporary SQLite startup fail cleanly; a browser that never registers is cleaned up and reported. |
| G Duplicate launch | Existing four-concurrent-launch test reuses one verified worker; failures do not stop an active reused instance. Unrelated port listener is preserved. |
| H Independent development | Factory reports unmanaged mode, has no session supervisor endpoints/watchdog; existing independent-server release journeys remain available. |
| I Restart | New instance after automatic stop loads confirmed content; recovery is acknowledged and not offered again after its save/reload. |
| J Interrupted shutdown | A deliberately SIGTERM-ignoring test child is killed and reaped within bounds; a separate test child remains alive. |

Failures encountered and corrected:

- Initial route-surface assertion needed the added configuration endpoint. A crash/restart test exposed a supervisor-lock cleanup race; a bounded wait fixed it. Review also found that the old five-second startup cleanup could kill a supervisor before it reaped the worker; cleanup now allows its bounded drain time, with signal handlers installed before child creation. A real readiness-timeout test verifies no owned process/listener remains.
- Root-invoked Ruff initially reordered unrelated test imports; those incidental edits were reverted. Checks run from the backend with its existing configuration.
- Page-scoped request interception vanished on close and allowed a background flush through, producing a correctly detected revision conflict. The outage test now uses context-scoped interception that outlives the closing page.
- A concurrent rebuild removed files from a shared test build directory. New lifecycle fixtures copy the build, matching installed-release isolation. Registration waits are bounded.
- Browser focus did not always establish the intended formatted input. The test now places/verifies its caret with the standard Selection API, verifies bold before close, and compares recovered JSON exactly.
- Firefox could not enter test bodies in this session's outer sandbox (namespace/profile launch errors). Its security settings were not weakened. The owner ran the real Firefox tests successfully in a regular terminal. Their first command was at repository root and stopped at missing `package.json`; changing to `frontend` resolved it.

Still unverified: launching the newly installed menu icon against the owner's normal Firefox process/profile, desktop session/reboot behavior, and an owner smoke test of personal notes. No GUI dispatch or personal-profile test is claimed as executed. Firefox's owner-run pass preceded final test-fixture/caret hardening and small recovery-cleanup refinements; final Chromium/unit coverage is recorded separately.

## F. Data integrity

SQLite document format, schema, SQL, foreign-key behavior and asset storage implementation are unchanged. The source changes do not open, migrate, delete or rewrite the personal database. Established synthetic persistence/image/backup tests remain in the regression suite. Prior private backups are not deleted or treated as a current backup of later edits.

Recovery records contain native JSON and the note/base revision, not HTML or executable content. They live in browser profile storage, never the repository. One record per page writer/note avoids cross-tab overwrite. Edit tokens guard deletion against stale acknowledgements. A newer server revision requires the existing conflict export/review workflow. A user choosing saved content does not erase an unacknowledged draft.

Visibility changes attempt ordinary flush but do not claim it will finish during closure. The dirty-page warning remains. Neither async `beforeunload` work nor beacon delivery is trusted for note persistence. The session beacon carries no document content. See [MDN beacon lifecycle guidance](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/sendBeacon).

Accepted transactions finish within the bounded grace when possible; interrupted SQLite transactions retain normal atomic rollback semantics. A forced stop can interrupt unconfirmed work, which is why recovery snapshots exist. No claim is made that lifecycle management fixes unrelated editor/API synchronization bugs or guarantees power-loss recovery.

## G. Ubuntu operation

After review, update the actual desktop installation from the repository root. Wait for Saved/uploads and use the existing Stop ENGAGE action first. Preserve any old tab with unsaved edits; this new source cannot journal edits retroactively in an older loaded build.

```bash
nvm use
python3.12 desktop/install.py
```

No sudo for the installer. Firefox and existing desktop prerequisites must be installed. Installation may download pinned packages; normal operation does not. Reinstallation keeps the data path/profile and retains older program releases for rollback. Launch **ENGAGE** from the desktop/menu, edit a synthetic note, wait for Saved and close its final tab. Allow approximately 5 seconds plus shutdown, or about 25 seconds plus shutdown when no close hint arrives.

Confirm default-port shutdown:

```bash
ss -ltnp 'sport = :8000'
tail -n 30 "$HOME/.local/state/engage-launcher/launcher.log"
```

Expect no listener and a reaped-backend log entry. Check identity if another application is listening; do not kill an unknown process. Reopen the icon and verify notes remain. Test two ENGAGE tabs with ordinary Firefox windows still open, closing the ENGAGE tabs one at a time. The backend should stop only after the final ENGAGE lease ends.

Independent backend development, from `backend`:

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Use `npm run dev` from `frontend` and open port 5173. These unmanaged servers stop with Ctrl+C and ignore tab lifetime. Do not run them simultaneously on the managed instance's port/profile.

After an abnormal close, launch ENGAGE and choose a draft for the correct note. Inspect/export it if uncertain; recovery retains the original revision and refuses silent overwrites. Browser storage must be the same profile/origin. If an existing open tab reports connection loss, relaunch the icon, let registration recover, then use Retry save or conflict recovery as needed. Full instructions are in [the desktop guide](docs/desktop-launcher.md).

## H. Remaining risks

- A background tab normally keeps heartbeating. A frozen tab, long OS stall or sustained network outage exceeding the lease/grace can expire; reconnecting after drain requires a new launch. No reliable heartbeat scheme can distinguish all frozen pages from crashed ones. [MDN documents background timer throttling](https://developer.mozilla.org/en-US/docs/Web/API/Window/setTimeout).
- Browser storage is per origin/profile, unencrypted and quota-limited. Clearing it, private-session closure, storage failure or power loss can remove recovery data. Failures are visible; wait for Saved. Large native documents incur synchronous serialization cost.
- The journal retains title/document JSON and already-uploaded image references. It does not copy in-flight image binary files; wait for uploads or reselect/repaste the original image after recovery. An unacknowledged image upload is not advertised as durable.
- Deferred/unconfirmed drafts are intentionally not expired or silently deleted, even when a note was deleted or an acknowledgement was lost. This may leave stale browser records and conservative conflict prompts. They are not a backup or a version-history system.
- Loopback/Origin checks do not authenticate other programs running as the same OS user. No new general authentication system is introduced. The private drain decision requires a separate random supervisor capability; force termination uses only the owned child.
- Killing the supervisor itself with SIGKILL can bypass its cleanup. Ordinary manual stop, browser crash, worker crash and handled supervisor termination are covered; a separate service manager is deliberately out of scope.
- Graphical desktop integration and the final installed snapshot require owner smoke verification. These are remaining acceptance checks, not reported passes. Raw in-flight-image journaling, power-loss guarantees, cross-browser/origin draft transfer and unrelated synchronization defects are outside this change's guarantees.

## I. Git commit

Recommended message:

```text
Manage desktop lifetime with tab leases and recoverable drafts
```

Changes extend the existing safe launcher, add opt-in session tracking and synchronous revision-aware draft recovery, and cover shutdown/restart/crash behavior with existing testing tools. No automatic commit, push, tag or publication was performed. No later product milestone was started.
