# P6 historical replay and production compatibility

1 November 2026. **LOCAL VERIFICATION ONLY. P6 CONDITIONAL.** No native command
in this document was executed during this remediation. Commands below are proposals
requiring separate owner authorization. The accepted application artifacts remain
unchanged; this is a host-side P6 verification-driver correction.

## Confirmed installed stack and boundary

R4's retained ImportError identifies a missing Qt private-ABI constructor for
`QtPrivate_6_11_2`. Static ELF inspection confirms PySide/shiboken 6.11.2 in
`/app`, runtime QtCore/Gui/Widgets 6.11.3, and application-local QtWebEngineCore
6.11.1. The bindings' RPATH selects runtime Core/Gui/Widgets. Runtime platform
plugins include Wayland and also depend on runtime Qt. The application does not
bundle QtCore. This is an incompatible installed dependency combination; imports
failed before Qt WebEngine or a GUI initialized. Normal launcher startup remains
unexecuted, rather than independently established as failing.

The static inventory (including NEEDED and RPATH for bindings, WebEngine and
runtime plugins) is `ci/evidence/p6/historical-runtime-remediation/static-stack.json`.
It was obtained with read-only `readelf`, without loading those libraries.
R4's exact module/error/private-output hashes remain in `r4-QtCore-ABI/diagnosis.json`.

## Historical policy and implementation

The new `--historical-runtime` option accepts only the full owner-approved commit:

`76fa01ac42ecf45d2c5020ef80de1c474c0c2ae86a51a79e8fec44c48f9dc473`

The toolchain lock must agree. Omitting the flag preserves strict drift refusal.
There is no packaged fallback, global mask, lock change or persistent runtime pin.
All operations use a newly created, marked, mode-0700 client under a fresh attempt
root outside the repository. Existing attempts are rejected, never resumed or
repaired. `real-pair-r2` is read-only input; publications use a new attempt store.

Runtime retrieval also journals the initially empty state, the retrieved current
commit, and the subsequent historical restoration in `client/runtime-setup.json`.
The driver records the runtime SHA immediately before and after installation,
update, rollback and reinstallation, including the preliminary B import/rollback
transactions. Each entry records monotonic observation times, original transaction
status, drift, ordinary-runtime compatibility, restoration status and trust
validation. A successful restoration **does not** change `ordinary_runtime_compatible`
from false to true. The install result's deferred runtime status is not a
compatibility PASS. Interrupted or failed transactions are read back and stop
without a repair attempt. Restoration failure stops; there is no retry/latest fallback.

Application installs, updates and rollbacks retain normal dependency resolution.
P6 uses its own exact-commit application update helper; accepted P5C client behavior
is unchanged. Only the explicitly requested runtime restoration transaction uses
`--no-deps --no-related`, preventing that operation from changing unrelated refs.
Each restoration is bounded to 300 seconds and targets exactly the approved SHA.
Before restoration, the isolated runtime origin must be `flathub`, its configured
URL must be `https://dl.flathub.org/repo/`, and both commit/summary GPG enforcement
must be enabled. This precheck validates configuration, not a local historical
object that a dependency update may have pruned. Flatpak restores/fetches exactly
the approved commit with signature enforcement intact. After restoration, OSTree
independently verifies that commit against the remote keyring (60-second bound),
and the live application runtime identity is checked again. An unavailable remote
historical commit, untrusted key, wrong origin, incorrect identity or failed
signature verification stops execution. A missing pre-restoration local cache
object is not treated as a signature failure. Flathub here supplies upstream runtimes; it is not application
hosting or a Flathub publication requirement.

Before the first GUI, the same isolated client installs A, restores/validates its
runtime, imports A's Qt modules, updates to exact B, restores/validates, imports B,
and rolls back to exact A with a final runtime check. Only then can GUI phases
begin. This reuses the newly populated isolated runtime object cache throughout
one run, avoiding separate downloads for each generation or GUI phase. Retained
failed clients are deliberately not cache donors: no unreviewed profile/deployment
or remote configuration is copied. Signed prepared A/B repositories are reused
without a rebuild or preparation repeat.

The sandbox probe imports QtCore, QtGui, QtWidgets, QtNetwork, QtWebChannel,
QtWebEngineCore and QtWebEngineWidgets, plus PySide6/shiboken6. It hashes actual
loaded modules and Qt providers from `/proc/self/maps`, reports only app/runtime
provider basenames and bounded version strings, and requires Core/Gui/Widgets and
WebEngine providers. Versions alone cannot pass. It creates no QApplication,
backend, renderer or window. Each probe has an absolute 60-second timeout and
10-second heartbeat. Raw success/failure child output stays in mode-0600 files
under a mode-0700 `private-subprocess/`; public records contain only validated
fields and hashes. No raw errors are committed or uploaded.

## Proposed owner commands — NOT AUTHORIZED TO EXECUTE YET

The first command is an **imports-only** diagnostic. It stops before every GUI.
Use it if the next authorization covers imports only:

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
backend/.venv/bin/python ci/release/real_update.py gui \
  --root "$HOME/.cache/p6/real-pair-r2" \
  --attempt-root "$HOME/.cache/p6/historical-import-attempt-r7" \
  --historical-runtime 76fa01ac42ecf45d2c5020ef80de1c474c0c2ae86a51a79e8fec44c48f9dc473 \
  --imports-only
```

Do not create the attempt directory first. Existing roots fail closed. Isolation
is built into `RuntimeClient`: `FLATPAK_USER_DIR`, HOME, XDG_DATA_HOME,
XDG_CONFIG_HOME, XDG_CACHE_HOME, GNUPGHOME, TMPDIR and the prelaunch runtime directory
are private subdirectories of this new attempt/client. All Flatpak commands use
`--user` plus this isolated environment, not the owner's ordinary installation.
The import check receives no forwarded desktop/session environment. No manual
`flatpak update` in the owner's terminal is part of this procedure.

Expected evidence in the fresh attempt:

- `operations.jsonl` and `progress.json`: flushed progress, operation and timeout.
- `runtime-transactions.json`: before/after SHA, drift and separate restoration.
- `imports-a.json` and `imports-b.json`: validated modules/providers/runtime identity.
- `imports-*-capture.json` or `imports-*-failure.json`: safe diagnostic hashes.
- `owner-result.json`: complete PASS only when both imports and rollback checks
  pass; `scope: IMPORTS ONLY; GUI NOT EXECUTED`; launch-attempt flag false.

Stop on any FAIL, missing evidence, wrong commit/origin, signature error, import
error or timeout. Preserve the attempt intact; raw diagnostic files remain private.
Do not alter an old attempt, repeat preparation, or run the GUI to obtain more
information about an import failure.

**Later GUI, only after separate authorization and review of the import results:**

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
backend/.venv/bin/python ci/release/real_update.py gui \
  --root "$HOME/.cache/p6/real-pair-r2" \
  --attempt-root "$HOME/.cache/p6/historical-gui-attempt-r8" \
  --historical-runtime 76fa01ac42ecf45d2c5020ef80de1c474c0c2ae86a51a79e8fec44c48f9dc473
```

This uses a separate fresh client to preserve the imports-only attempt. It repeats
the bounded A/B import gate in that client before launching anything, so an earlier
PASS cannot authorize a changed environment. A later owner may instead authorize
this single combined command initially: its built-in A/B gate precedes all GUI
execution and only one fresh runtime retrieval is needed. Neither proposed command
has current execution authorization. Runtime retrieval may download dependencies
once per fresh client (existing 1800-second bound); no shared installation is reused.

The GUI command requires a real Wayland session and forwards only the existing
reviewed desktop socket/session values for GUI phases. It does not disable renderer
sandboxing. After both import gates, follow the printed synthetic edit/restart,
update/rollback, backup/recovery and reinstall instructions. Import success cannot
be reported as GUI, renderer or lifecycle success. Even a complete historical GUI
PASS cannot close normal-runtime-update compatibility.

## Production recommendation — OPEN public-release blocker

The upstream [PySide BaseApp README](https://github.com/flathub/io.qt.PySide.BaseApp)
requires bindings to track KDE's Qt patch updates. Its inspected
[6.11 manifest](https://raw.githubusercontent.com/flathub/io.qt.PySide.BaseApp/branch/6.11/io.qt.PySide.BaseApp.yaml)
builds PySide 6.11.2 against the SDK and layers the WebEngine BaseApp. This explains
the split delivery model; it is not an upstream promise that a previously packaged
binding works after every independent runtime update. The observed undefined
private symbol is direct evidence that this artifact does not meet that requirement.

The smallest immediate repair would be an upstream-maintained, synchronized
BaseApp/KDE build, but rebuilding against 6.11.3 alone only matches one snapshot.
It does not establish safety at the next patch. No maintained compatibility
mechanism that makes the present immutable binding survive that update was verified
in this research. Do not select a new production lock merely to hide this boundary.

**Recommended production direction:** evaluate a coherent application-local Qt
closure maintained through upstream Qt for Python distribution, rather than
binding this immutable application to the runtime's independently changing private
Qt ABI. Qt's [package documentation](https://doc.qt.io/qtforpython-6/package_details.html)
describes matched Essentials/Addons/Shiboken packages containing their Qt libraries;
its [installation guidance](https://doc.qt.io/qtforpython-6/gettingstarted.html)
confirms those wheels include Qt binaries. This is an upstream packaging basis,
not evidence that unmodified wheels already meet CyrNava's Flatpak requirements.

The closure must include matching Core/Gui/Widgets, Network/WebChannel/Positioning,
WebEngine libraries, QtWebEngineProcess, resources/locales and required platform,
image, TLS and integration plugins. It must not accidentally fall back to runtime
Qt via RPATH or plugin paths. [Qt's plugin guidance](https://doc.qt.io/qt-6/deployment-plugins.html)
requires deployment-aware plugin selection. Existing
[WebEngine BaseApp sandbox integration](https://github.com/flathub/io.qt.qtwebengine.BaseApp)
must be preserved or replaced by an independently verified upstream-supported
Flatpak renderer arrangement; generic wheels alone do not prove that support.
Wayland/portal/renderer checks and native dependencies must be measured before
choosing a concrete build. This is a recommendation for an owner-approved packaging
assessment, not an implemented or proven production remedy.

Tradeoffs: application bytes/downloads increase because shared runtime Qt is
replaced by an app-local closure (no invented size estimate). Redistribution
licenses/notices and source/relinking obligations need a complete review, including
QtWebEngine/Chromium dependencies and plugins; current licensing clearance remains
open. CyrNava's maintainer becomes responsible for promptly rebuilding/releasing
bundled Qt/WebEngine security fixes, tracking upstream support and CVEs, and auditing
the full closure. A standard supported Flatpak runtime still supplies the OS ABI;
no custom runtime or permanent runtime-update disablement is proposed. A future
packaging change requires separate artifact approval; historical A/B remain fixed.

Required production release validation, after a separately approved packaging remedy:

1. Record exact supported runtime branch/architecture, minimum OS ABI and full Qt
   provider closure; reject mixed private-ABI providers in an audit.
2. Clean normal-dependency installation on a disposable client with the current
   supported runtime, signatures enabled, no historical restoration.
3. Bounded sandbox imports, actual **normal packaged launcher** startup, renderer
   sandbox verification, synthetic autosave/image/recovery and process cleanup.
4. Keep app bytes unchanged, independently update the supported runtime, repeat
   import/normal-launcher and lifecycle checks. Runtime drift is expected here;
   compatibility must be demonstrated rather than repinned.
5. Real application update and binary rollback across the supported schema boundary;
   do not infer SQLite downgrade support. Restart/data/assets/backup integrity pass.
6. Repeat on the supported machine/graphics/session matrix and test the declared
   compatibility limit. A future patch still requires ongoing monitoring; no finite
   test proves compatibility with arbitrary future binaries.

No production package source, manifest, lock, sandbox, signing policy or accepted
artifact changed in this remediation. Production compatibility remains **OPEN**.


Final local verification: **74 focused tests + 24 subtests PASS; 231 release/workflow
tests + 228 subtests PASS** in a disposable detached checkout with the exact P6
source overlay. Ruff check and formatting PASS. Twenty-four new tests were added.
The sole warning is the existing intentional duplicate-ZIP negative fixture.
No native runtime restoration, import or GUI was executed. No commit/push occurred.


## R6 retained failure and corrected ordering — 1 November 2026

R6 installation succeeded and correctly deferred its strict runtime check. Its
transaction records `PASS`, drift true and ordinary runtime compatibility false.
Historical authorization was correctly propagated. The failing operation was
`runtime-signature`, sequence 54 (exit 1), before restoration started. The requested
historical commit and detached metadata are absent from the retained local OSTree
object store, which has no parent object repository. The current runtime object
remains present. Original signature-check stderr was not retained, so its exact
libostree message is unavailable; the missing local input is independently observed.

The previous pre-restoration call tried to verify that missing historical object.
The correction separates origin/GPG policy checks from post-restoration cryptographic
verification. It restores the exact explicitly approved SHA, verifies the restored
SHA/origin/signature, then independently checks the application's live runtime
identity. Imports run only after those checks. Failure diagnostics now retain raw
signature child output privately and expose only safe categories and hashes.

`ci/evidence/p6/r6-restoration-order/isolated-reproduction.json` records a synthetic
execution of the archived R6 driver failing before restoration and the corrected
driver reaching import eligibility with ordinary compatibility still false.
The fixture uses the actual installation, replay and import-eligibility functions;
all native I/O is simulated. It is not a native PASS. Historical records/source
are preserved in that evidence directory and the retained attempts remain unchanged.

The commands above now propose **imports-only r7**, with GUI r8 separately gated
on review/authorization. R6 must not be reused or repaired. No new native execution
was performed or authorized by this local correction. Production compatibility
remains an OPEN public-release blocker.


R6 correction final clean-checkout verification: **85 focused tests + 24 subtests
PASS; 242 release/workflow tests + 228 subtests PASS**. Ruff and formatting PASS.
Eleven new R6 regressions were added. The single existing duplicate-ZIP warning
comes from a deliberate negative fixture. Exact source overlays, test commands,
results and preservation hashes are in `ci/evidence/p6/r6-restoration-order/`.
No new native verification was executed.


## R9 post-reinstall profile-open investigation — 2 November 2026

**P6 remains CONDITIONAL. R9 overall FAIL is preserved.** R9's initial B update
passed, followed by rollback, native backup/import and recovery PASS. The failing
`gui-updated` was the second `updated` invocation, after uninstall/reinstall B.
It had already verified the window, renderer sandbox, backend authentication,
private network/filesystem, single-instance lock, Dark preference and owned-backend
cleanup. It failed between `owned_backend_reaped` and `saved_owner_edit_checks`,
where the unchanged production `Profile(profile_root)` is constructed.

The active-workspace pointer is valid and selects an existing schema-5 imported
workspace. Read-only source inspection and integrity validation **on disposable
copies** establish that the original and active imported database bytes, logical
content fingerprints and image trees match. Each contains one synthetic note,
folder and asset; SQLite integrity/foreign-key and existing P3 validation pass.
The inactive schema-6 workspace is the deliberate future-schema refusal fixture.
All three generations retain the synthetic records and asset. The complete retained
profile remains 96 files / 8,660,684 bytes with unchanged aggregate tree hash.
No data loss, bad pointer or missing workspace was found.

**The exact missing object and originating syscall are undetermined.** The original
helper suppressed filename, errno and traceback, and set its stage only after
construction. Private stderr's only diagnostic is the known Chromium system D-Bus
warning, not a Python traceback. Present-day file existence cannot reconstruct a
transient missing entry. Removal of a Qt profile/cache entry during Profile's
strict recursive scan is a plausible hypothesis; a deterministic synthetic test
reproduces that error path, but does not prove historical causality. An application
filesystem defect versus verifier teardown timing cannot yet be distinguished.

Only the confirmed diagnostic gap is corrected. The host-streamed native helper
persists an allowlisted stage **before** each direct profile reopen and records
OSError errno, bounded path category and storage-function/source-line frames. It
never emits raw filename, traceback path, message, note content or environment.
It still calls the unchanged Profile and propagates failures; no retry, delay,
exception suppression or filesystem/security relaxation was added. The P6 parent
now labels `reinstall-b` separately and keeps `phase-reinstall-b.json` distinct
from the earlier `phase-updated.json`; active/completed phase context is retained.
Existing security, saved-content and integrity assertions remain mandatory.

Exact implementation changes:

- `packaging/flatpak/production/native_check.py`
- `ci/release/real_update.py`
- New `packaging/flatpak/production/test_profile_diagnostics.py`
- New `ci/release/test_native_phase_context.py`

The report, owner checklist, runbook, runtime-remediation status and current review
indexes are updated. Prior helper/driver/docs and original R9 success/failure
summaries are preserved in `ci/evidence/p6/r9-profile-investigation/` alongside
integrity, preservation, clean-source and test evidence. Raw child output and
synthetic image bytes remain outside the repository. Production storage/application
code, package/permissions/runtime locks, historical policy, accepted A/B archives
and signed preparation are unchanged. No preparation, GUI, native import or
runtime transaction was repeated; no commit/push/GitHub action occurred.

Clean-checkout results: **17 focused tests PASS; 109 storage/migration/packaging
tests PASS; 244 release/workflow tests + 228 subtests PASS.** The helper's 14
pre-existing E402/E501 lint findings are unchanged (no new findings); the other
changed Python files pass Ruff and all four changed Python files pass formatting.
Existing duplicate-ZIP and FastAPI/Starlette deprecation warnings are recorded.

Another separately authorized instrumented native observation is necessary to
complete post-reinstall saved-content verification and obtain exact operation
information if the error recurs. It must use a fresh attempt; preserve R9 and r2
preparation. No speculative application fix is proposed. A passing rerun alone
would not establish the historical transient's cause. Native execution is not
currently authorized by this local investigation.
