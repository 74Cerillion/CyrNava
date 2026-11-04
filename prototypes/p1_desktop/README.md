# P1: disposable PySide6 desktop experiment

This is a feasibility prototype on branch `prototype/p1-pyside6-feasibility`, based on `cbf7ccc`. It does not replace the installed Firefox launcher. **Use synthetic notes only.** The API is unauthenticated and this environment's Qt sandbox diagnostic reports incomplete namespace isolation. Read [the assessment](REPORT.md) before deciding on production adoption.

## Setup and launch on Ubuntu

Run from the repository root. Python 3.12 and the project's pinned Node/npm must already be available. Installation downloads dependencies; application operation uses the local backend and built assets.

```bash
# Frontend build tools are needed only to produce the existing release assets.
nvm use
cd frontend
npm ci
npm run build
cd ..

# A separate environment; never install Qt into the production backend environment.
python3.12 -m venv /tmp/cyrnava-p1/venv
/tmp/cyrnava-p1/venv/bin/python -m pip install -r prototypes/p1_desktop/requirements.txt

# Actual native window. No Vite or separately started backend is required.
QT_QPA_PLATFORM=wayland /tmp/cyrnava-p1/venv/bin/python prototypes/p1_desktop/desktop.py
```

Wayland was exercised here. X11 (`QT_QPA_PLATFORM=xcb`) is unverified. Missing host display/Qt libraries must be diagnosed on the target system; do not run as root or use `--no-sandbox` to get past a launch failure. The prototype rejects inherited WebEngine override/debugging variables.

Each normal launch creates a fresh private `/tmp/cyrnava-p1/workspace-*` directory and prints its exact path and random loopback origin as JSON to the terminal. That workspace contains only test data:

```text
workspace-*/
├── .p1-prototype.json             # marker and stable local port
├── .desktop.lock                 # prevents duplicate ownership of this workspace
├── data/engage/engage.sqlite3     # explicit temporary SQLite path
├── data/engage/assets/           # existing image storage
├── qt-data/                     # persistent Qt profile, including recovery storage
├── qt-cache/                    # profile cache path; HTTP cache is memory-only
├── config/ and cache/           # isolated XDG locations
├── backend.log
├── metrics.json                 # written at shutdown
└── sandbox.txt                  # actual chrome://sandbox output
```

To reopen, supply the **exact marked workspace path printed by your launch**, for example `--workspace /tmp/cyrnava-p1/workspace-abc123`. The example suffix is a placeholder, not an existing profile. Reopening preserves the port, SQLite, images and Qt localStorage. An occupied saved port is an error; silently choosing another port would hide origin-bound recovery records. Arbitrary personal paths and storage symlinks are refused. `/tmp` can be cleared on reboot: this is deliberately not durable personal storage.

## Close and recover

After **Saved** and completed uploads, use the window's close button. The desktop stops and reaps its own FastAPI child. If saving is unconfirmed or the backend has exited, the native dialog defaults to **Keep open** and offers **Close prototype**. Closing retains the workspace; it does not promise recovery of changes that never reached local recovery storage or unfinished image binaries. Reopen the same workspace and explicitly choose **Recover draft** when offered.

An earlier version of this prototype could get trapped in a “Keep the prototype open” warning after backend failure. That already-running process cannot load this correction. Dismiss its warning, then force quit only that disposable prototype in Ubuntu System Monitor. If shown as Python, inspect its command line for `prototypes/p1_desktop/desktop.py`; never stop every Python process or the installed CyrNava backend. Normal SIGTERM/Ctrl+C handling in the corrected prototype also exits without an interactive save dialog, retains existing recovery storage and cleans up its backend.

Keep the disposable workspace until verification is complete. No automatic deletion or production data import is provided. Test downloads are cancelled, including recovery exports; do not rely on the prototype's Download draft button.

## Reproduce checks

From the repository root, with the existing frontend development dependencies installed:

```bash
/tmp/cyrnava-p1/venv/bin/python -m pytest -q -p no:cacheprovider prototypes/p1_desktop/test_desktop.py
/tmp/cyrnava-p1/venv/bin/python -m ruff check prototypes/p1_desktop
/tmp/cyrnava-p1/venv/bin/python -m ruff format --check prototypes/p1_desktop
/tmp/cyrnava-p1/venv/bin/python -m pip check
node prototypes/p1_desktop/verify.mjs
/tmp/cyrnava-p1/venv/bin/python prototypes/p1_desktop/inspect_environment.py --firefox
```

`verify.mjs` launches real visible Qt windows, uses synthetic notes and the existing Playwright package, and closes its own processes. It opts into `--test-cdp`: an **unauthenticated loopback debugging port** plus a small fixed stdin test protocol. Do not use that option with sensitive content. Normal launches do not enable CDP. Native clipboard input is tested; the file chooser is intercepted by automation, so this does not verify a portal dialog.

Verification writes `/tmp/cyrnava-p1/verification.json`. Exit **0** means functional checks and the sandbox diagnostic passed; **1** means a functional failure; **2** means functional checks passed but the renderer sandbox acceptance gate did not. The recorded result is **2**, not an overall security pass.

The environment script reads installed package sizes and the existing wheel cache; it does not download or install tooling. Its optional Firefox check opens only a blank dedicated temporary profile, never your normal browser profile. The bubblewrap probe is a private-network capability probe, not Flatpak packaging. Both probes were blocked by this execution environment; see the report. No Flatpak manifest or install/update script is included.

The retained [evidence](evidence/verification.json) and [native screenshot](evidence/desktop.png) contain synthetic test content only. Databases, Qt profiles, notes and credentials are not copied into this repository.
