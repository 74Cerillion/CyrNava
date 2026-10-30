# P1B: disposable Flatpak feasibility run

This is a test application, **org.cyrnava.P1B**, branch **p1b**. It does not replace the installed CyrNava, register a production launcher, import notes or modify the production installer. Use synthetic data only. The host build, observed renderer sandbox/private networking and owner-run native acceptance checks have passed. P1B is complete for architectural review; [the assessment](REPORT.md) distinguishes automated, independently inspected and owner-confirmed evidence from untested supplemental behavior. Do not begin production integration without explicit approval.

## Build in your ordinary Ubuntu terminal

The host preflight has passed in the owner's recordings. Run this from the repository root in the same ordinary terminal, **outside the agent execution sandbox**:

```bash
cd "$HOME/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava"
/tmp/cyrnava-p1/venv/bin/python prototypes/p1b_flatpak/prepare.py --build
```

Keep the command's output. If it fails, stop at that error and return the final output. Do not change AppArmor/sysctls, add host-network permissions or disable renderer sandboxing to make it continue.

The command requires the P1 disposable Python environment, the existing `frontend/dist`, Flatpak, flatpak-builder, Bubblewrap and the user Flathub remote established in the preflight. It downloads the existing pinned backend requirements as Python 3.13/x86_64 wheels. Flatpak-builder installs missing KDE 6.11 runtime/BaseApp dependencies and installs only the new test ID. Setup downloads are expected; the running app has no host-network grant and starts no Vite server. Large SDK/BaseApp downloads are development dependencies, not the application's measured package size.

Every attempt creates a fresh private `/tmp/cyrnava-p1b/stage-*` snapshot. It copies only backend application source/requirements, built frontend assets and the desktop prototype. It refuses source symlinks and database files. No `.git`, browser profile, personal data or production installation directory is copied. The module installs the backend wheels offline with `--no-index --no-deps`; no Qt wheel is installed over the BaseApp. A build-time assertion requires the SDK's Python 3.13 and the 6.11 Qt/PySide/WebEngine family. Full backend requirements, including existing development packages, are deliberately retained for this limited experiment; runtime trimming is not attempted.

The script records source/wheel hashes, actual installed runtime/BaseApp commits, permissions, application commit and installed size in the printed `build-evidence.json`. These describe that local build; moving upstream runtime branches are not a production reproducibility lock. Without `--build`, the script only stages source and generates a manifest; it does not fetch or install anything.

## Launch and check security first

After a successful build:

```bash
flatpak run --user org.cyrnava.P1B//p1b
```

The title must say **CyrNava — P1B disposable Flatpak**. Keep the launching terminal open for JSON events/errors. The native **Save P1B evidence…** button saves a diagnostic JSON file through a native Save dialog. Export it to a test destination and inspect `sandbox_diagnostic`, `flatpak_info`, `process_evidence`, `network_interfaces`, `tcp_listeners`, and the recorded component versions. The JSON contains synthetic profile/process metadata, not note document content. No remote debugging or native JavaScript bridge is enabled.

Stop and return for review if backend startup/private loopback fails, Chromium reports inadequate sandboxing, the app requests broad host permissions, or helper startup fails. Preserve diagnostic output; there is no fallback to `--share=network` or insecure Chromium flags. A Flatpak wrapper alone does not prove effective renderer isolation.

While the test window is open, run in a second host terminal:

```bash
cd "$HOME/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava"
python3 prototypes/p1b_flatpak/inspect_host.py > /tmp/cyrnava-p1b/host-processes.json
flatpak info --user --show-permissions org.cyrnava.P1B//p1b
flatpak ps --columns=instance,application,pid,child-pid
```

`inspect_host.py` reads process metadata only for this test Flatpak: it selects desktop/WebEngine command lines, verifies their application identity through `.flatpak-info`, and records namespaces, seccomp and `NoNewPrivs`. It never signals processes or reads notes. Unreadable processes remain unavailable evidence, not a pass. Nested renderer instances may be invisible to the GUI's `/proc`, which is why host observations are collected separately. A positive seccomp field may include an outer filter and does not independently prove Chromium's complete sandbox.

Compare host, GUI, backend and renderer namespaces. The GUI/backend must communicate in private networking distinct from the host. In-app listener evidence must show the backend on `127.0.0.1`, with no debug listener. The actual renderer boundary must be justified using both Chromium's report and process evidence. Do not automatically treat a namespace difference, a keyword or an inherited seccomp filter as a full pass.

## Native tests after security/network review

The app uses a fixed synthetic workspace below `~/.var/app/org.cyrnava.P1B/data/p1b-profiles/workspace-p1b/`. The existing backend receives an explicit SQLite path there. Qt storage, images, preferences and recovery records stay in that test workspace. The stored loopback port is reused across launches to preserve localStorage origin identity. An occupied port causes an error; it is not silently changed. The app rejects a different Flatpak ID, broad host grants and host-network sharing.

| Test | Action and expected evidence |
| --- | --- |
| Rich text | Create a synthetic note; enter an H1, paragraphs, bold and a code block. Wait for Saved. |
| Clipboard screenshot | Use Ubuntu's screenshot tool to copy only a synthetic region. Focus the editor and press Ctrl+V. Wait for the image and Saved. This requires actual native input, not CDP injection. |
| Native chooser/upload | Type `/image`, choose Image, click Upload image and select a synthetic local PNG in the real native chooser. Verify rendering and Saved. |
| SQLite/restart | Close the window after Saved, launch the same test ID again and verify exact text/formatting and both images. |
| Preferences | Change Appearance and hide navigation; restart and verify both preferences. |
| Recovery | Click native **Stop test backend…**, confirm, edit the note title, and wait for Save Error. Close the window using **Close prototype**, then restart the same test ID. A recovery draft must be offered. |
| Portal download | Before recovering, click the existing **Download draft** button. Select a synthetic JSON destination in the native Save dialog. Inspect that file, then explicitly recover the draft, wait for Saved, restart and verify it persisted. |
| Owned termination | After normal closure, `flatpak ps` must no longer show the running test. Inspect the test workspace's `backend.log` for completed shutdown. Collect evidence after an outage separately from a healthy close. |

To confirm that native chooser actions actually use the portal, observe only the FileChooser interface in a host terminal while performing the synthetic Open/Save actions:

```bash
dbus-monitor --session "type='method_call',interface='org.freedesktop.portal.FileChooser'"
```

Expect corresponding OpenFile and SaveFile calls. Stop monitoring with Ctrl+C after the test; avoid unrelated file operations during capture. A dialog merely looking native is not portal proof. `QT_QPA_PLATFORMTHEME=xdgdesktopportal` requests the runtime's portal integration; successful calls and file results remain acceptance requirements.

For a repeat verification, retain the final build output, `build-evidence.json`, exported native evidence, `host-processes.json`, and observed native results. Do not send personal notes. The original P1B native results are now explicitly owner-confirmed in the assessment. An earlier agent-side instance listing was followed by a host inspector with no matching processes and an empty host `flatpak ps` result; end-state cleanup passed without force termination. Full-container cleanup latency was not measured. No P2–P6 work is authorized by this run.

## Local source checks

```bash
/tmp/cyrnava-p1/venv/bin/python -m pytest -q -p no:cacheprovider prototypes/p1_desktop/test_desktop.py prototypes/p1b_flatpak/test_prepare.py
/tmp/cyrnava-p1/venv/bin/python -m ruff check --no-cache prototypes/p1_desktop prototypes/p1b_flatpak
/tmp/cyrnava-p1/venv/bin/python -m ruff format --no-cache --check prototypes/p1_desktop prototypes/p1b_flatpak
```

No cleanup command deletes test profiles automatically. Keep the synthetic profile/evidence for review. Removing this test application later must name only `org.cyrnava.P1B`; do not use a global Flatpak uninstall or delete the existing CyrNava profile.
