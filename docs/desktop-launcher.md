# Ubuntu desktop launcher (P2-M01)

## Installation and paths

From the CyrNava repository root, on Ubuntu 24.04:

```bash
sudo apt update
sudo apt install -y git curl ca-certificates python3.12 python3.12-venv xdg-utils xdg-user-dirs zenity firefox
# Install Node 24.19.0 and npm 11.6.2 as described in the README.
nvm install
nvm use
npm install --global npm@11.6.2
python3.12 desktop/install.py
```

`nvm` applies only to the one-time source build. The installer checks Ubuntu/Linux, Python 3.12, the pinned Node/npm versions and desktop utilities before modifying the per-user installation. It copies backend source, installs pinned Python requirements into an application-owned venv, runs `npm ci` and builds the React frontend. It then starts a synthetic temporary profile to verify the local app before registering launchers. It does not read or copy the user's notes, screenshots, or database.

Program files and configuration: `$XDG_DATA_HOME/engage-application/`, default `~/.local/share/engage-application/`. User notes stay in the existing `$XDG_DATA_HOME/engage/`, default `~/.local/share/engage/`. Logs and runtime coordination state: `$XDG_STATE_HOME/engage-launcher/`, default `~/.local/state/engage-launcher/`. Directories are private to the user. A custom `XDG_DATA_HOME` must be present during installation; the launcher saves that path and supplies it at runtime. It refuses to change the saved path on reinstall. Preserve your environment if you have previously run CyrNava with custom XDG settings.

The installer creates a menu item in `$XDG_DATA_HOME/applications/` and a copy in the XDG Desktop folder when one exists. GNOME may still ask the user to choose **Allow Launching** for the desktop file. No trust bit or OS protection is automatically changed. Each release stores its icon alongside its versioned program files, and the desktop entry references that absolute path. The default icon is the original CyrNava logo downsampled to 512 pixels. Known shipped placeholder bytes are upgraded automatically; configured custom icons remain selected. An explicit `--icon /absolute/path/logo.png` overrides that choice. PNG and SVG are supported.

To pin the logo launcher, open Ubuntu's application menu, search **CyrNava**, right-click its entry and select **Add to Favorites / Pin to Dash** (wording varies with the desktop). Pin the CyrNava entry rather than the Firefox window. The application still opens in Firefox; its running window/dock grouping belongs to Firefox. No browser profile, window-class override or desktop framework has been added. Real GNOME pinning/trust requires manual verification on the owner's desktop.

## Start, reuse, stop

The menu item, desktop icon and **CyrNava** action all execute the installed launcher with an absolute Python 3.12 path. It needs no shell profile, terminal, npm, nvm or Vite. The default URL is `http://127.0.0.1:8000`; `--port 18000` can set another port during installation. New installations record Firefox's executable and open `firefox --new-window URL`. No dedicated profile, extension, preference change or reliance on Firefox process lifetime is needed. Existing configurations retain their previous `xdg-open` fallback until reinstalled.

The launcher uses a private `flock` to serialize repeated starts. Its detached supervisor retains the backend's `Popen` handle, monitors session leases, and reaps that child on exit. Supervisor and worker each hold lifetime locks. A recorded PID is accepted only when `/proc` start time and its generated worker identifier match; manual stopping uses Linux `pidfd` to signal that identity. Readiness requires the recorded process plus a local `/api/desktop-ready` response matching its identifier and lifecycle protocol, and the compiled React root page. No HTTP proxy or redirects are used for probes. The backend binds `127.0.0.1` and disables request access logs.

A healthy managed server is reused. A stale process record is ignored and the backend starts again. If another process owns the port, its identity is not trusted: the launcher shows an error and never stops that process. Stop the service from its own application, or choose a different port during installation. A running *unmanaged* CyrNava development/release server does not carry the launcher's per-instance identifier and will not be adopted; stop it first to avoid two server processes sharing a data profile.

For normal closure, wait for **Saved** and uploads, then close all CyrNava tabs/windows. Other Firefox windows may stay open. Each CyrNava page has an unpredictable identifier and sends a heartbeat every 5 seconds. A best-effort `pagehide` close beacon accelerates closure, but leases expire after 20 seconds without heartbeats. Once no leases remain, a 5-second grace allows refresh/reconnection before shutdown is claimed. A new lease cancels that grace. After drain is claimed, new writes/leases return 503 and cannot revive the stopping process. The supervisor sends SIGTERM, allows Uvicorn up to 8 seconds for accepted requests, and waits up to 10 seconds before killing only its retained child; reaping is bounded by a further 5 seconds.

Usually closure takes about 5 seconds plus shutdown. Without a delivered close beacon, allow about 25 seconds plus shutdown after the last heartbeat. Startup has a separate 60-second registration grace; a browser that never registers causes cleanup and an error. A backend that stops answering the private supervisor probe is stopped after 25 seconds without contact. Suspended/frozen tabs cannot guarantee heartbeats; see recovery below.

The existing **Stop CyrNava** action remains a manual fallback. Its confirmation reminds you to wait for Saved/uploads; it signals only a verified worker. It does not close Firefox. **Open diagnostic logs** opens the state directory. Errors show a Zenity dialog and log at `launcher.log`/`backend.log`; note content is not logged by lifecycle management.

## Confirm shutdown and recover

With the default port, run:

```bash
ss -ltnp 'sport = :8000'
tail -n 30 "$HOME/.local/state/engage-launcher/launcher.log"
```

No listener means the port is free. Logs show `Session lifecycle: grace`, `draining`, then `Supervisor reaped backend and exited`. A listener could belong to another application: inspect it, never kill an unidentified PID. Substitute your saved port and XDG state path if customized.

Pending title/native document edits are synchronously stored in the browser's localStorage on each change, before debounce or a network request. These are recovery copies, separate from authoritative SQLite data. Records include note ID, page writer ID, base revision and an edit token. Reopening a note with a previous-page draft offers **Recover draft**, **Download draft**, or **Continue with saved note (retain drafts)**. Recovery uses the original revision; a changed SQLite revision opens the existing conflict workflow rather than overwriting it. Choosing the saved note retains the record and defers the prompt only for the current loaded page. Draft records are removed only after a successful save acknowledgement, guarded against newer edits and other tabs.

If the backend disappears, use the desktop icon to start it again. The existing page retries registration; unsaved content remains in memory/browser storage, and a failed autosave still needs **Retry save**. A revision conflict still requires review/export. Do not refresh a tab containing older unprotected edits until Saved; this source update cannot retroactively protect a page loaded from the old build.

Recovery storage is per browser profile and exact origin (including port), unencrypted, and outside Git. Private browsing, clearing site data, quotas, disabled storage, OS/storage failure, or changing browser/port can make drafts unavailable. Storage failures show a warning; keep the tab open until Saved. Already uploaded image references are retained, but an in-flight original image file is not journaled: wait for uploads or reselect the original file after recovery. A local draft is not a backup.

## Independent development

From the repository's `backend` directory:

```bash
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

From `frontend`, run `npm run dev` and open `http://127.0.0.1:5173`. Direct `python -m app` release serving also remains unmanaged. These paths return `managed: false` from `/api/lifecycle`; there is no watchdog, and closing the browser does not stop them. Stop with Ctrl+C. Do not run them on the managed application's port/profile simultaneously.

## Updates and removal

Wait for Saved, stop CyrNava, update the source checkout, then run `python3.12 desktop/install.py` again. Reinstallation uses the same configured data/state paths, verifies the new release against an isolated profile and updates the existing two application-menu entries and one desktop icon. It preserves existing data. Earlier program release directories remain available for manual rollback. There is no automatic update or release cleanup policy yet.

To remove only the launcher, delete `org.engage.Workspace.desktop` and `org.engage.Stop.desktop` from the user's Applications folder, and `org.engage.Workspace.desktop` from Desktop (if installed). Remove `engage-application/` (including bundled icons) and `engage-launcher/` state if logs are no longer needed. Keep `engage/` to retain your database and assets. Make and verify a backup before intentionally deleting that profile.

## Troubleshooting

| Message or symptom | Safe action |
| --- | --- |
| Missing Python runtime/build | Run the one-time installer again from the current source checkout. |
| Port occupied by an unverified service | Do not kill it from CyrNava. Stop the known development server in its own terminal or reinstall with a free local port. |
| Browser does not open/register | Check `launcher.log`; verify Firefox starts normally. Immediate dispatch failure stops a newly started backend; missing registration stops it after the startup grace. Reused active instances are preserved if an additional browser dispatch fails. |
| Startup times out/crashes | Read `launcher.log` and `backend.log` in the state directory; correct the reported dependency/profile error, then click again. Stale owned process state is recovered on the next attempt. |
| Data cannot be accessed | Check the saved `data_home` in `engage-application/config.json` and permissions for that profile. Do not point the installer at a new path until the original XDG value is confirmed; do not move the profile. |
| Desktop icon asks for trust | Review the installed desktop entry and choose **Allow Launching** in GNOME's file manager if desired. The application-menu item remains available. |
| Installer reports missing Node/npm | For installation only, initialize the required Node version in that terminal. Normal desktop launches do not read `.bashrc` or nvm. |

Desktop startup needs no network after dependencies/frontend assets have been installed. Install/update commands do download packages. A rebooted desktop session should still show the user-level application entry; reboot was not available for this automated review.

The [lifecycle engineering report](../LIFECYCLE_REPORT.md) records tests and remaining platform verification. Firefox may route a new-window command to an existing process; see [Mozilla's command-line documentation](https://firefox-source-docs.mozilla.org/browser/CommandLineParameters.html). Closure events are unreliable; see [MDN's beacon guidance](https://developer.mozilla.org/en-US/docs/Web/API/Navigator/sendBeacon). Heartbeat expiry and synchronous draft recovery address those separate concerns.
