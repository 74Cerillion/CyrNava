# P2 desktop review candidate

For the final P2 real Save portal check, use the host supervisor from the repository
root: `python3 packaging/flatpak/run_portal_verification.py`. It streams the current
test helper to the installed candidate and preserves final failure evidence even
if Qt/Python crashes. No rebuild or Flatpak permission override is required. See
`P2_NATIVE_CHECKS.md` for expected output and acceptance criteria. Earlier direct
stdin-only portal commands do not provide this independent crash reporting.

This is an unpublished, local review build. It does not replace the Firefox
installer, import its profile, configure an update remote, sign or publish a
release. P3 migration, rollback and distribution approval remain pending.

## Existing Ubuntu/Wayland test host

Prerequisites already used for P1B: Flatpak, flatpak-builder, working unprivileged
namespaces and the installed x86_64 KDE Platform/SDK 6.11, PySide BaseApp 6.11 which includes its matching WebEngine components. A separate installed WebEngine
BaseApp ref is not required. Do not change AppArmor or disable Chromium sandboxing if
preflight fails. The Codex session's nested namespace restrictions block the
actual Flatpak build/run; use your regular terminal.

Run each command separately from the repository root:

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
```

```bash
npm --prefix frontend run build
```

```bash
backend/.venv/bin/python packaging/flatpak/prepare.py --build
```

The build downloads pinned backend wheels into a new directory under
`$XDG_CACHE_HOME/cyrnava-builds/p2/` (normally
`~/.cache/cyrnava-builds/p2/`), records their hashes, source hashes and existing runtime commits
in `review-lock.json`, verifies wheel hashes, installs offline inside the SDK,
and installs only `org.cyrnava.CyrNava.Devel`, branch `p2`, for this user. It uses
production frontend assets, never Vite or an external browser. All pinned backend
requirements are retained for parity, including test packages; trimming those is
a later packaging decision. This staging lock is evidence, not a public release
or an independently trusted dependency attestation.

Build snapshots, Flatpak builder state and child-process temporary files stay on
that cache filesystem, rather than filling the host's small `/tmp` tmpfs. The build
requires at least 4 GiB of available space before starting. An account quota can
still impose a tighter limit than the filesystem free-space report. Rebuilds keep
separate review snapshots for traceability; generated build directories/caches can
be removed after verification, preserving evidence and any repository referenced
by the installed review candidate.


## Automated native verification

Run these in order. They open and normally close a real Qt window, using a
separate synthetic verification profile. No Chromium debugging port is enabled.
The two runs verify authenticated frontend/image loading, actual Qt typing,
normal close/save, backend reaping, persistent preferences, restart, Chromium's
sandbox report and renderer namespace/seccomp observations. They deliberately
fail if a native dialog interrupts the automated workflow.

```bash
flatpak run --branch=p2 --command=python3 org.cyrnava.CyrNava.Devel /app/share/cyrnava/verification/verify_native.py 1
```

```bash
flatpak run --branch=p2 --command=python3 org.cyrnava.CyrNava.Devel /app/share/cyrnava/verification/verify_native.py 2
```

Evidence is printed and stored under
`~/.var/app/org.cyrnava.CyrNava.Devel/data/p2-verification/verification-phase-1.json`
and `verification-phase-2.json`. Do not treat historical P1B results as P2 results.
If either command fails, retain its output and the private `backend.log`; do not
weaken permissions to make it pass. The test driver is outside the production
launch path and supplies no HTTP endpoint or OS bridge.

## Native outage and recovery drill

After phases 1 and 2, these test-only commands stop only their retained backend,
exercise Keep open, export the current offline JSON through Qt, explicitly close
with a recovery draft, then restart/recover/save it. They use a third independent
synthetic profile. The save destination is stubbed **inside that profile**; the
real portal chooser remains a manual check.

```bash
flatpak run --branch=p2 --command=python3 org.cyrnava.CyrNava.Devel /app/share/cyrnava/verification/verify_outage.py 3
```

```bash
flatpak run --branch=p2 --command=python3 org.cyrnava.CyrNava.Devel /app/share/cyrnava/verification/verify_outage.py 4
```

Evidence is under `~/.var/app/org.cyrnava.CyrNava.Devel/data/p2-outage-verification/`.
Neither command stops a normal Firefox or CyrNava installation.

## Manual production-shell checks

For the four outstanding final-candidate checks, use
[P2_NATIVE_CHECKS.md](P2_NATIVE_CHECKS.md). It provides the exact ordered commands,
real screenshot/notice/link steps, a real export-portal mode and a deterministic
native held-upload/layout/restart helper. The helpers stream into the installed
candidate without additional host permissions. The owner has rebuilt and verified
the popup correction; the checklist now tracks the sole remaining portal retest.
The latest driver-only correction needs no package rebuild.

```bash
flatpak run --branch=p2 org.cyrnava.CyrNava.Devel
```

Use only synthetic notes in this development identity. Its profile is independent
of the automated verification profile and the existing Firefox installation.

1. Create a note with headings, bold text, paragraphs and nested lists. Paste a
   synthetic screenshot. Use `/image` and the native chooser for another image.
   Confirm uploads finish and Saved appears. Check Third-party notices opens.
2. Type text and immediately close the native window without waiting for the
   debounce. Relaunch; confirm that text and images are present. Change appearance
   and navigation visibility, close and restart; confirm preferences remain.
3. During a deliberately slow upload, close the window. It must wait for all
   images and the subsequent note PATCH. Cancel an image selection: an empty image
   block must not claim Saved; select an image or delete that block.
4. Open a second instance while the first is running. It must explain that this
   profile is open and must not create a second backend. Quit the first normally.
5. For an outage, stop only the **test-owned** worker after identifying it inside
   this Flatpak instance. Do not reuse old PIDs or kill unrelated Python processes.
   Edit a note, close, choose Keep open, inspect/export the draft, then explicitly
   Close with recovery draft. Pending image bytes are not recoverable. Restart,
   choose Recover draft and verify a successful save. Never test this on personal
   data. Automated backend tests already exercise retained-child termination.
6. A note link to an external URL or `file:` must not navigate the renderer or
   open an external browser. Image/resource requests must remain local. Export a
   recovery draft and verify the portal-mediated save chooser writes valid JSON.
7. Inspect effective Flatpak permissions and host processes after closing. No
   `network`, `home`, `host`, session-bus or X11 broad grants should be present.
   P1B's inherited narrow KDE theme/D-Bus grants may still appear. Renderer
   sandbox evidence and private loopback must be reviewed alongside the test JSON.

```bash
flatpak info --user --show-permissions org.cyrnava.CyrNava.Devel
```

```bash
flatpak ps --columns=instance,application,pid,child-pid
```

## Source regression checks

From `backend/`, run your existing isolated environment's `python -m pytest -q`
and `python -m ruff check --no-cache . ../desktop/native ../packaging/flatpak`.
From `frontend/`, run `npm test`, `npm run lint`, `npm run build` and
`npm run test:release`. These tests use synthetic temporary profiles.

The optional `desktop/native/requirements.txt` pins the host Qt test environment
only. Flatpak must use its matching BaseApps, not pip WebEngine wheels. No user
needs Node, npm, a venv or development servers to run the built candidate.
