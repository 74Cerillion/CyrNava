# ENGAGE P2-M01 — Desktop launch engineering report

## A. Architectural assessment

Before P2-M01, ENGAGE already had the M6 single-origin release server: `backend/app/__main__.py` built the existing FastAPI app, served the compiled Vite output, and bound Uvicorn to `127.0.0.1`. Developers could run it after preparing Node/frontend build assets and the backend venv, then manually open a browser. No `.desktop` entry, install workflow, graphical process management, or launcher-level readiness/instance check existed. Separate Vite/FastAPI commands remain useful only in development.

## B. Selected solution

A per-user source installer prepares a pinned Python venv and compiled frontend once. A standard Ubuntu desktop entry invokes a small Python standard-library supervisor, which starts the existing one-server application in a detached session, confirms its process identity and its own readiness endpoint, then calls `xdg-open` with the loopback URL. Node/npm are not needed after installation for ordinary use. No Electron, new framework, service daemon or application dependency was added.

A user-level systemd service could own process lifetime, but introduces unit registration/user-manager assumptions and separate service lifecycle configuration. A shell launcher alone would still need robust locking, PID-reuse protection, readiness, diagnostics and UI errors. The supervisor keeps those checks in one auditable module and uses Linux `flock`/`pidfd` already available on target Ubuntu. It also supports stop/log actions from the desktop menu. These are targeted alternatives assessed for M01, not claims about earlier historical debates.

## C. Files created or modified

| File | Responsibility and reason |
| --- | --- |
| `desktop/install.py` | Python 3.12 one-time user installer. Checks host/build tools, builds a pinned venv/frontend, verifies startup using a temporary profile, and registers user desktop/menu/icon files. Uses existing pinned requirements and npm lockfile. Reinstalls preserve configured profile/state paths and retain prior application releases. |
| `desktop/launcher.py` | Standard-library entry/supervisor. Serializes clicks; preflights runtime/build, launches/reuses/restarts the backend, verifies PID/start time/nonce and application readiness, opens the default browser, shows Zenity failures and manages a confirmed safe stop. The venv imports the existing `app.main:create_app`; no framework replaces FastAPI. |
| `desktop/icons/engage.svg` | Clearly marked temporary icon matching the requested document placeholder. The installer also accepts owner-approved PNG/SVG without changing launcher code. |
| `desktop/icons/README.md` | Marks the icon as temporary and explains artwork replacement. |
| `backend/tests/test_desktop.py` | Seven pytest cases using fresh temporary profiles/ports, fake desktop utilities and the real app. Covers locking/reuse/crash/stale PID/port conflict/readiness/preflight, error UI/logs, profile+image persistence/backup, desktop command generation, permissions and failed-install rollback. |
| `README.md` | Adds Ubuntu one-time installation, default click workflow, Node/nvm distinction, data/log paths, update/removal, developer/server distinction and links to troubleshooting. Existing backend/frontend commands stay available. |
| `docs/desktop-launcher.md` | Install path, worker lifecycle, port behavior, trust prompt, logs, updates, removal and troubleshooting. |
| `P2_M01_REPORT.md` | This requested A–L implementation/test review. |

No backend route/schema, requirements file, frontend component, database, existing test, user profile, backup or M6 report was changed. The existing M6 license decision remains pending.

## D. Installation instructions

Prerequisites on target Ubuntu 24.04:

```bash
sudo apt update
sudo apt install -y git curl ca-certificates python3.12 python3.12-venv xdg-utils xdg-user-dirs zenity
```

Prepare Node 24.19.0/npm 11.6.2 once for the source build. If using nvm, initialize it in that installation terminal only:

```bash
nvm install
nvm use
npm install --global npm@11.6.2
python3.12 desktop/install.py
```

Run installer from repository root. Normal operation begins by clicking ENGAGE in the desktop/app menu. GNOME may require the user to choose **Allow Launching** for the desktop copy. The menu entry is available regardless. It uses the temporary placeholder until approved artwork is provided.

## E. Execution flow

1. GNOME reads `org.engage.Workspace.desktop` created by `install.py`. `Exec` invokes the absolute Python interpreter used to install the application and `$XDG_DATA_HOME/engage-application/launcher.py --config ... open`.
2. `launcher.main()` loads its private JSON config, creates/checks the 0700 state directory, opens a private launcher log and serializes concurrent starts with `locked()`.
3. `start()` checks the installed venv and built frontend. It reuses only a worker whose PID, `/proc` start time and nonce argument match and whose local `/api/desktop-ready` response and React root page pass. HTTP probing bypasses environment proxies and refuses redirects.
4. When no managed instance is live, it probes the configured loopback port without terminating its owner. It starts the installed Python venv running `launcher.py ... worker --nonce ...`; the worker takes a lifetime lock, imports existing `app.main.create_app`, adds an instance-specific readiness route and runs Uvicorn at `127.0.0.1`.
5. The launch caller waits up to 20 seconds, polling every 150ms. It opens `http://127.0.0.1:<configured port>` using configured `xdg-open` only after both process and application checks pass.
6. The existing FastAPI app serves the built React bundle, `/api` routes, SQLite profile and image files as in M6. There are no Vite or external-service calls at runtime.

`stop` asks the user to confirm after reminding them to wait for Saved/uploads, then uses `pidfd` to signal only the verified worker and allows graceful Uvicorn shutdown. `logs` opens the XDG state directory. A stale record is not trusted by itself.

## F. Process lifecycle

- First click: preflight → listener probe → detached owned worker → bounded application-ready check → default browser.
- Healthy managed instance: verifies instance nonce and app endpoints, then opens another browser tab/window without spawning another server.
- Concurrent/repeated click: one launcher holds `launcher.lock`; following launchers wait and reuse the now healthy instance.
- Crashed worker: PID/start-time/nonce fails; launcher records stale recovery and starts a new worker if port is free.
- Unmanaged or unrelated port listener: never adopted or terminated. A clear Zenity dialog points to logs and suggests stopping the listener in its own application or choosing another port.
- Startup failure: bounded wait, known-child termination if necessary, graphical error plus diagnostic file paths. It does not open an unusable page.
- Clean stop: desktop Stop action confirmation → PID identity recheck/pidfd SIGTERM → Uvicorn graceful shutdown. Browser remains open; no process is daemonized by systemd or auto-started at login.

## G. Data integrity

Program files/configuration are in `engage-application`; logs and locks are in `engage-launcher`; application data remains in the existing `$XDG_DATA_HOME/engage` or `~/.local/share/engage`. At install, custom XDG data path is captured and supplied to the child at runtime, then refused if it changes during reinstall. The installer does not copy or migrate profile data and tests startup with a separate throwaway data directory. It installs no second database. Reinstallation creates a new program release folder and updates one stable set of menu entries; the database/assets remain at their existing path. Tests saved/reloaded a synthetic native note and image, backed up the profile, and reinstalled against an existing synthetic note profile while verifying the database bytes and tree/document stayed intact.

A user who previously runs ENGAGE with nondefault XDG settings must launch the installer with the same `XDG_DATA_HOME`; the path is recorded in config so a graphical session need not read shell startup files. The launcher refuses a later data-path change rather than silently switching profiles.

## H. Security review

The server binds only to `127.0.0.1`; the frontend/API are same-origin; readiness bypasses proxies/redirects; the browser URL is loopback. No remote service, credential or note data is added. Desktop config and state directories use user-only permissions; launcher log rotation is bounded, backend log is truncated between runs if it exceeds 2 MiB, and Uvicorn request access logging is disabled. The installer never runs sudo. It does not set GNOME's trust metadata automatically; normal desktop trust prompts remain enabled.

Integrity uses serialized starts, a lifetime worker lock, exact PID/starttime/nonce validation and pidfd shutdown; port conflicts never cause a kill. Installation paths/data roots remain separate. A same-user process can still inspect or alter local data; localhost and private directory modes are not protection from that account's malware. Backend logs can grow during a long session below the launcher's between-session truncation; rotation during a continuously running server is deferred. Same-profile unmanaged development servers are not adopted; users should stop one before using the desktop launcher.

## I. Testing report

Commands executed from repository root or indicated directory:

```bash
cd backend
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check --config pyproject.toml .
.venv/bin/python -m ruff format --config pyproject.toml --check .
.venv/bin/python -m pip check
cd ../frontend
npm run lint
npm test
npm run build
npm run test:release
npm run test:e2e
```

P2-specific: `backend/.venv/bin/python -m pytest -q backend/tests/test_desktop.py` → **7 passed**; Ruff check on desktop and its tests passed. A clean isolated installation ran the actual installer using fresh program/Python paths, pinned package installs and build; GIO desktop-entry dispatch opened a stubbed `xdg-open` that fetched the local page; second clicks reused one PID; the desktop Stop action requested confirmed shutdown. A subsequent installer re-run against the same throwaway profile preserved the SQLite byte snapshot and note JSON, retained one application/menu entry and reopened the note after rebuild. After the final installer rerun, `desktop-file-validate` accepted the installed application-menu, Stop-menu and Desktop entries; GIO parsed the generated entry and resolved its absolute versioned icon path even with spaces. Earlier GIO launch checks dispatched through the entry, reused the healthy instance, called the fake `xdg-open` URL handler and ran the confirmed Stop action. The final icon-path change affected the file resource only; final runtime code passed the installer’s startup check. No real GNOME screen, browser window, native trust prompt, reboot or Ubuntu VM was available.

Final regressions: **103 backend tests**, **77 frontend tests**, Ruff check/format, ESLint, TypeScript/build, `pip check`, **three development and three release Chromium journeys** all passed. The seven P2 launcher tests are included in the 103 backend results. The isolated installer was rerun against an existing synthetic profile; the database SHA-256 remained unchanged, its note was reopened after rebuilding, and only one app/menu entry was present. Fresh install dependency setup and temporary-profile startup verification also passed.

Failure/correction history: initial tests exposed launcher rapid-click/process-state cleanup assumptions and test working-directory/quoting mistakes; changed port probing to permit safe TCP TIME_WAIT reuse, made termination use pidfd, and ran the backup check from `backend/`. A GIO harness initially checked readiness too early because `Gio.launch()` is asynchronous; corrected it to wait on actual health. These are test harness corrections; the final supported launch flow itself waits for readiness. A simulated missing-runtime and opener failure left logs/error messages. No existing user data was touched.

Acceptance status: installer/build, GIO launch, repeat-click, restart, simulated crash recovery, port conflict, synthetic persistence+image, offline checks, missing runtime, installer rerun, and Phase 1 regression suites are automated/verified. Existing real user-profile compatibility is preserved by using the same configured XDG path but was not tested by opening that user's profile. Human icon-click/data review, GNOME trust prompt, reboot, actual default-browser session, fresh Ubuntu VM and OS-level offline disconnect remain manual checks. Do not report those as passed.

## J. Documentation updates

The README now distinguishes one-time install, normal graphical use, local release server and developer Vite mode. It explains prerequisites, data/log paths, stopping, updating without data deletion, removal, licensing status and desktop troubleshooting. `docs/desktop-launcher.md` documents runtime behavior, lifecycle, port conflicts and trust prompts. M6 architecture and reports remain historical; this document records P2-M01.

## K. Technical debt

- The SVG is a temporary icon; replace only with the separately approved owner artwork.
- The native Ubuntu GNOME trust prompt and real GUI click/reboot are not exercised in this environment.
- No app launcher auto-login/systemd service or automatic updates. Server runs until Stop/session shutdown; no unrelated process is stopped.
- User may see a port conflict if a development/unmanaged ENGAGE server is already running. It is intentionally not adopted because its identity cannot be verified.
- Old program release directories are retained for rollback and need a documented/manual retention decision; no user data is stored in them.
- Backend log size is capped between runs, not continuously rotated.
- Linux-specific `/proc`, `flock`, and `pidfd` mean this launcher targets Ubuntu/Linux only.
- The project-level license remains pending from M6; no license was selected or changed by P2-M01.

These limits do not invalidate the tested local supervisor. Native desktop acceptance, final icon review and current desktop-entry validation remain outstanding before everyday rollout.

## L. Git summary

Recommended commit: **`Add one-click Ubuntu desktop launcher`**.

No commit, push, tag or release was created. Inspect `git status --short`, `git diff --check`, and review untracked desktop/docs/tests separately before selectively staging. Stop at P2-M01 pending owner review; do not start another milestone.
