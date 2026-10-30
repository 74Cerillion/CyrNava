# Final four P2 native checks

**P2 STATUS: ACCEPTED — FINAL NATIVE PORTAL VERIFICATION PASSED**

Accepted 30 October 2026 (Asia/Seoul). Owner-executed run `run-64a7b56d5fc0`
was independently verified from both final JSON records. Corrected driver
`p2-portal-window-filter-3`, source SHA-256
`d4e5025c567074f7dc653b265e3429c2979e6bc5c70f0c9c6775fab251d8089b`,
matches current source. Supervisor and driver report complete PASS, child exit 0,
stage finished, and no remaining child. All eight checks passed, including the
real native Save chooser, granted-file JSON readback, offline recovery-draft
export, explicit recovery close, and owned-backend reaping. The driver record
sets `real_save_portal: true`; this was not a mocked export destination.

Original evidence:
`/home/cerillion/.var/app/org.cyrnava.CyrNava.Devel/data/p2-portal-verification/run-64a7b56d5fc0/`.
Repository copies: `desktop/native/evidence/p2-final-2026-10-30/`.
Prior failure/investigation sections below are retained as historical evidence;
their pending/conditional statuses are superseded by this acceptance record.
This passing run supports the instrumentation correction, without claiming a
native C++ stack established the exact earlier segmentation-fault mechanism.


Run on the owner's ordinary Ubuntu/Wayland desktop against the already installed
`org.cyrnava.CyrNava.Devel`, branch `p2`. Shell redirection streams test-only
helpers to the installed Flatpak Python. The helpers are not production launch
code. No permission changes are required.

The original candidate at preparation was
`262487450efb5271a96e84c53a6f9d1196be474a240de9d63a6e2f9556cd0f6c`.
The owner rebuilt the popup correction; the current verified installed candidate is
`d31bbde4a29a80e73806f8d5949c231d248f9cfdc17b6a2819f7d0724e95d7f7`.
The Codex session cannot exercise the real desktop namespace or host portals;
source checks are not native PASS results.

## Latest results: only the portal retest remains

The owner confirmed screenshot clipboard/restart PASS. Native held-upload/layout
and restart both PASS; their result JSON was independently read. The 30 October
rebuilt candidate displays actual notices text and blocks external links without
a blank popup. Notices/navigation is PASS. Keep those results.

**P2 remains conditionally accepted. Latest owner run: native startup crash.**
The recording and `run-f7703fae217f/supervisor-result.json` agree: the supervisor
recorded FAIL, child exit 139, and incomplete driver evidence. The fatal stderr
log explicitly reports `Segmentation fault`. The last checkpoint is `load` after
`event-loop-enter`, before any JS query, native typing or driver close request.
The Save portal was not reached. The supervisor's failure reporting worked; the
native crash remains an acceptance failure.

The previous helper's close observer was accidentally installed on QApplication.
That registration is application-wide, despite its receiver check. Revision
**`p2-portal-window-filter-3`** installs it only on the actual main window and uses
`aboutToQuit` for quit diagnostics. There is no global event filter or notify
override. This is a confirmed driver instrumentation defect and a plausible
startup-crash trigger; successful WebEngine/portal execution after this correction
is still required to establish causality and acceptance.

The host supervisor below streams the current helper to the same installed P2
candidate, preserves private stdout/stderr/fault diagnostics, and records final
PASS/FAIL even if the child crashes. No rebuild, Flatpak override, permission
expansion or production-profile access is needed. Unexpected dialogs remain
untouched. The four-minute driver deadline and 330-second supervisor watchdog
remain in force. Earlier failure records are preserved.

Close all P2 windows normally. **No rebuild is needed.** Run these blocks separately:

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
```

```bash
python3 packaging/flatpak/run_portal_verification.py
```

Do not type, click the status icon or close the helper's window. It creates the
offline draft and invokes **Download pending draft** automatically. The normal
Save icon is status feedback, not a manual-save control. This tests the existing
failed-save recovery JSON download, not a new general note-export feature.

During a successful run, only interact when the actual native **Save file dialog** appears: select Downloads
and a new filename, then click Save within four minutes. The old failing records
are preserved in their separate profiles. The supervisor first prints the run ID
and evidence directory, may print `P2 stage:` progress, and finally prints JSON,
`Evidence:` and `Diagnostics:` paths. Raw Chromium D-Bus/fault messages are saved
in `driver-stderr.log`; their absence from the terminal is not a security change.

Success requires the **supervisor** result to contain `"status": "PASS"`,
`"complete": true`, `"child_exit_code": 0`, and all required checks, including
`real_save_chooser_and_granted_json_readback: PASS`. The child must also have
completed its final evidence. Missing/partial evidence, a native crash, nonzero
exit or an unexpected dialog can never be promoted to success.

If an unexpected confirmation appears, the test stops and prints FAIL/evidence
immediately. Do not treat that confirmation as the Save portal. Record the
printed evidence path, then close the disposable window yourself using its
normal close/recovery choices. The driver will not dismiss an unexpected dialog.
The four-minute driver deadline bounds verification; the supervisor's maximum
wait is 330 seconds. A stopped failed test may leave its window open for owner
inspection and manual cleanup. `child_still_running: true` identifies this case.

Use no pipeline. In particular, `| echo $?` starts a reader that exits immediately,
which can cause BrokenPipe in the writer; its `$?` does not measure the new run.
If an additional shell exit status is desired, run `echo $?` as a separate command
immediately after the supervisor finishes. Exit 0 means supervisor PASS; 1 means
FAIL. The JSON separately records the Flatpak child exit code/signal where known.

The authoritative record is
`~/.var/app/org.cyrnava.CyrNava.Devel/data/p2-portal-verification/run-*/supervisor-result.json`.
The same run holds `outage-phase-3.json`, `driver-checkpoint.json`,
`driver-stdout.log` and `driver-stderr.log`. Startup failure may occur before all
child files exist; the supervisor still records that failure. No program can
print after its own SIGKILL/power loss, or guarantee a new file on an unavailable
filesystem; an initial incomplete FAIL checkpoint is written before child launch.

The original four-check instructions remain below for traceability.

Run every command block separately. Save and normally close any existing P2
window before starting. Use only synthetic notes in this development identity.
The original Firefox installation and its data are not used.

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
```

## 1. Real desktop screenshot clipboard

```bash
flatpak run --branch=p2 org.cyrnava.CyrNava.Devel
```

1. Create a note titled `P2 final native checks`.
2. Open an ordinary text editor containing only `Synthetic P2 screenshot`.
3. Use Ubuntu's screenshot UI to copy a crop of that text to the clipboard. Do
   not include personal information. Use its Copy action if needed.
4. Click an empty paragraph in CyrNava and press Ctrl+V. Do not use `/image` or a
   file chooser for this check: the system clipboard is the boundary being tested.
5. Confirm an image appears, upload finishes and **Saved** appears.
6. Close CyrNava normally, run the same launch command again and reopen the note.
   Confirm the screenshot is still visible.

PASS requires actual screenshot clipboard paste, Saved and a visible image after
application restart. A file selection/upload alone does not satisfy this check.

## 2. Notices and blocked external navigation

Use the same synthetic note and open P2 window.

1. Show navigation if hidden. Click **Third-party notices**. A separate native
   window must display the actual notice text. Close only that notice window.
2. Add a link in the note to
   `https://example.invalid/cyrnava-p2-native-check` using the editor's link UI
   (select synthetic text, Ctrl+K, enter the URL and confirm). Wait for Saved.
3. Use that link's **Open link** action, or its normal supported click action.
   CyrNava must keep the workspace, load no external page, and launch no external
   browser. If a blank/mislabelled popup appears, report that separately; it is
   not a successful notices window. The `.invalid` destination is deliberately
   non-routable and requires no internet connectivity.
4. Confirm the note is still editable. Close CyrNava normally.

Report both subresults. Existing URL policy tests do not replace this real Qt
navigation check. The owner must explicitly confirm no external browser opened;
the helper scripts do not inspect or control the owner's normal browser.

## 3. Real recovery-draft Save portal

```bash
python3 packaging/flatpak/run_portal_verification.py
```

This host supervisor opens a separate synthetic window. The helper stops only the backend child
it started, types an offline draft, chooses **Keep open** and requests its export.
It does not patch Qt's save dialog or fake a successful download.

Do not interact with the synthetic window until the real Save dialog appears.
When that dialog appears, within four minutes:

1. Select **Downloads** or **Documents** using the chooser's sidebar.
2. Name the file `cyrnava-p2-portal-test.json`; choose a new name if it exists.
3. Click **Save**. Do not cancel. The helper reads only that explicitly selected
   export and verifies its live draft title. The synthetic window then closes
   using the explicit recovery choice. The host prints the authoritative result
   after validating the child's final record and exit code.

PASS requires overall `"status": "PASS"` and
`"real_save_chooser_and_granted_json_readback": "PASS"`, plus the owner's
confirmation that the actual native Save dialog appeared without a missing-folder
error. On failure, preserve the terminal output. Cancellation is not a PASS.

Evidence stays in a new directory for each run:
`~/.var/app/org.cyrnava.CyrNava.Devel/data/p2-portal-verification/run-*/outage-phase-3.json`.
The chosen synthetic JSON file remains wherever the owner selected; it is not
deleted automatically. This profile is separate from phases 3/4's original
automated outage evidence.

## 4. Native close during a held upload and restart

The first command replaces the clipboard with a small generated cyan image;
copy anything you need elsewhere first. It does not read or preserve clipboard
contents. The real Ubuntu screenshot path was covered separately in check 1.

```bash
flatpak run --branch=p2 --command=python3 org.cyrnava.CyrNava.Devel - close < packaging/flatpak/verify_upload.py
```

Do not interact with its window. The helper uses a separate synthetic profile,
real Qt Ctrl+V and the installed editor/close protocol. It temporarily delays only
the asset fetch in that test renderer, requests native closure, checks for two
seconds that the window/backend stay open, Saved is absent and the panes remain
adjacent on the same row. It releases the real authenticated upload, allows the
normal close protocol to save, then checks SQLite and backend termination.
It does not imitate an upload response or change production timeouts.

If the close phase prints overall `"status": "PASS"`, run:

```bash
flatpak run --branch=p2 --command=python3 org.cyrnava.CyrNava.Devel - restart < packaging/flatpak/verify_upload.py
```

The restarted native window must render the persisted image(s), match the prior
saved SQLite document and close normally. Both commands must report PASS.
Unexpected dialogs, unfinished uploads, layout failures and timeouts fail this
test rather than being automatically accepted.

Evidence, synthetic document and a screenshot of the held close remain under:
`~/.var/app/org.cyrnava.CyrNava.Devel/data/p2-upload-verification/`:
`upload-close.json`, `upload-restart.json`, `held-close.png`.

## Result to return

```text
Screenshot clipboard and restart: PASS / FAIL (details)
Notices text: PASS / FAIL (details)
External link blocked, no external browser: PASS / FAIL (details)
Real Save portal and JSON verification: PASS / FAIL (details)
Held upload close/layout and restart: PASS / FAIL (details)
```

The two navigation subresults comprise one acceptance item. Known terminal
`XDG_DATA_DIRS` and unavailable system-bus messages do not themselves invalidate a
functional result; retain any new or different errors. No result is recorded as
PASS until it has actually been executed and confirmed. Stop at P2 for review.
