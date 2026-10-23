# Ubuntu desktop launcher (P2-M01)

## Installation and paths

From the ENGAGE repository root, on Ubuntu 24.04:

```bash
sudo apt update
sudo apt install -y git curl ca-certificates python3.12 python3.12-venv xdg-utils xdg-user-dirs zenity
# Install Node 24.19.0 and npm 11.6.2 as described in the README.
nvm install
nvm use
npm install --global npm@11.6.2
python3.12 desktop/install.py
```

`nvm` applies only to the one-time source build. The installer checks Ubuntu/Linux, Python 3.12, the pinned Node/npm versions and desktop utilities before modifying the per-user installation. It copies backend source, installs pinned Python requirements into an application-owned venv, runs `npm ci` and builds the React frontend. It then starts a synthetic temporary profile to verify the local app before registering launchers. It does not read or copy the user's notes, screenshots, or database.

Program files and configuration: `$XDG_DATA_HOME/engage-application/`, default `~/.local/share/engage-application/`. User notes stay in the existing `$XDG_DATA_HOME/engage/`, default `~/.local/share/engage/`. Logs and runtime coordination state: `$XDG_STATE_HOME/engage-launcher/`, default `~/.local/state/engage-launcher/`. Directories are private to the user. A custom `XDG_DATA_HOME` must be present during installation; the launcher saves that path and supplies it at runtime. It refuses to change the saved path on reinstall. Preserve your environment if you have previously run ENGAGE with custom XDG settings.

The installer creates a menu item in `$XDG_DATA_HOME/applications/` and a copy in the XDG Desktop folder when one exists. GNOME may still ask the user to choose **Allow Launching** for the desktop file. No trust bit or OS protection is automatically changed. Each release stores its icon alongside its versioned program files, and the desktop entry references that absolute path. The provided SVG is explicitly temporary; provide approved PNG/SVG artwork with `--icon /absolute/path/logo.png` after approval.

## Start, reuse, stop

The menu item, desktop icon and **ENGAGE** action all execute the installed launcher with an absolute Python 3.12 path. It needs no shell profile, terminal, npm, nvm or Vite. The default URL is `http://127.0.0.1:8000`; `--port 18000` can set another port during installation. Browser launching uses `xdg-open`, which dispatches to the user's configured default browser.

The launcher uses a private `flock` to serialize repeated starts. A background worker holds a second lock for its lifetime. A recorded PID is accepted only when `/proc` start time and its generated worker identifier match; when stopping, Linux `pidfd` signals that same process identity. Readiness requires the recorded process plus a local `/api/desktop-ready` response matching its identifier and the actual compiled React root page. No HTTP proxy or redirects are used for this probe. The backend binds `127.0.0.1` and disables request access logs.

A healthy managed server is reused. A stale process record is ignored and the backend starts again. If another process owns the port, its identity is not trusted: the launcher shows an error and never stops that process. Stop the service from its own application, or choose a different port during installation. A running *unmanaged* ENGAGE development/release server does not carry the launcher's per-instance identifier and will not be adopted; stop it first to avoid two server processes sharing a data profile.

Use the desktop entry's **Stop ENGAGE** action (or app-menu Stop item). A graphical confirmation reminds you to wait for **Saved** and image uploads first. If confirmed, the launcher sends SIGTERM to the verified worker and lets Uvicorn shut down. This closes the server; it does not close your browser. **Open diagnostic logs** opens the state directory. Start errors show a Zenity dialog and log at `launcher.log`/`backend.log`; notes are not intentionally logged and HTTP access logging is disabled.

## Updates and removal

Wait for Saved, stop ENGAGE, update the source checkout, then run `python3.12 desktop/install.py` again. Reinstallation uses the same configured data/state paths, verifies the new release against an isolated profile and updates the existing two application-menu entries and one desktop icon. It preserves existing data. Earlier program release directories remain available for manual rollback. There is no automatic update or release cleanup policy yet.

To remove only the launcher, delete `org.engage.Workspace.desktop` and `org.engage.Stop.desktop` from the user's Applications folder, and `org.engage.Workspace.desktop` from Desktop (if installed). Remove `engage-application/` (including bundled icons) and `engage-launcher/` state if logs are no longer needed. Keep `engage/` to retain your database and assets. Make and verify a backup before intentionally deleting that profile.

## Troubleshooting

| Message or symptom | Safe action |
| --- | --- |
| Missing Python runtime/build | Run the one-time installer again from the current source checkout. |
| Port occupied by an unverified service | Do not kill it from ENGAGE. Stop the known development server in its own terminal or reinstall with a free local port. |
| Browser does not open | Check `launcher.log`; test the desktop's configured default browser/`xdg-open`. A failure is displayed after server readiness. |
| Startup times out/crashes | Read `launcher.log` and `backend.log` in the state directory; correct the reported dependency/profile error, then click again. Stale owned process state is recovered on the next attempt. |
| Data cannot be accessed | Check the saved `data_home` in `engage-application/config.json` and permissions for that profile. Do not point the installer at a new path until the original XDG value is confirmed; do not move the profile. |
| Desktop icon asks for trust | Review the installed desktop entry and choose **Allow Launching** in GNOME's file manager if desired. The application-menu item remains available. |
| Installer reports missing Node/npm | For installation only, initialize the required Node version in that terminal. Normal desktop launches do not read `.bashrc` or nvm. |

Desktop startup needs no network after dependencies/frontend assets have been installed. Install/update commands do download packages. A rebooted desktop session should still show the user-level application entry; reboot was not available for this automated review.
