# CyrNava P4 — Production Flatpak packaging

Date: 30 October 2026 (Asia/Seoul).

## A. Executive summary

**P4 STATUS: CONDITIONAL — OWNER HOST VERIFICATION REQUIRED**

Production packaging, explicit identity selection, desktop metadata, approved
artwork, dependency locking and package auditing are implemented. The production
filesystem assembled successfully. Static validation and available regressions
pass. **Build A is now a finished local `.flatpak` artifact:** owner-host export and
bundle creation passed after the timestamp correction. Its SHA-256, size and
OSTree ref were independently verified. The validator remained enabled. There
is a verified synthetic production installation with passing edit, restart, update and rollback checks. Overall native P4 acceptance remains conditional. P5/P6, publication, signing, commits and pushes have not begun.

The final resumable build is:
`outputs/CyrNava/.p4-cache/cyrnava-builds/p4/local-A-6m4ne70o`
(relative to the enclosing task directory). See `build-inputs.json`,
`package-inventory.json` and `result.json` in that directory. The final result is
PASS. Previous export failures are retained under `evidence/p4/`; final Build A
records are under `evidence/p4/build-A-final-2026-10-30/`. Build B also passed and was independently verified; real native installation/update/rollback passed in run-83587bd18651. Backup/import continuation and final launcher checks remain outstanding.

## B. Baseline and P3 reconciliation

- Branch: `desktop/p2-production-integration`, unchanged.
- Starting commit: `eb65fc152181f77b3fa131f79aa417a03d84a1ac` (`P3 Complete`).
- Initial working tree: clean. No unrelated changes found; no tags listed.
- Previous commit: `808e906dbe977edd4a20ec23f134ad565c54a675`.
- App 0.1.0; SQLite schema 5. Neither was increased in P4.

P3 final evidence was independently reconciled before implementation: run
`run-a2e0fcaea12a`, all five phases complete PASS, helper SHA-256
`2695e2495ea5f056475bce86483b5ea76cd1bcc074b1c79cb672cec4852dc56b` matches
source. All copied evidence hashes match the acceptance manifest. Real portal
delivery/readback, native import/schema upgrade, saved title/new screenshot after
restart, source preservation, restore/rollback and backend cleanup passed.
P2 final evidence for corrected `p2-portal-window-filter-3` remains accepted.

P3's earlier failed edit and pending continuation describe a superseded attempt.
P3_REPORT.md now explicitly labels those follow-ups historical and adds this P4
prerequisite reconciliation. The raw failure records were preserved. P3's earlier
statement that P4 was unauthorized describes its checkpoint, before this grant.

Baseline: 67 focused backend/native/migration/verification tests and 273 frontend
tests passed. Subsequent final regressions are listed in section I.

## C. Production identity and storage

Permanent ID: **io.github._74Cerillion.CyrNava**. Flatpak branch: **stable**.
Development remains **org.cyrnava.CyrNava.Devel**, branch **p2**.

`desktop/native/build_identity.py` is the explicit checked-in development
configuration. Production installs the separately reviewed module from
`packaging/flatpak/production/build_identity.py`. This is a build-time file choice,
not string replacement or an environment-driven profile switch. Runtime checks
still require matching FLATPAK_ID, `.flatpak-info`, `/app/share/cyrnava` and the
matching WebEngine helper. Production window title is CyrNava; application desktop
ID/window icon use the permanent ID. Development's title and runtime ID remain.

Production private root:
`~/.var/app/io.github._74Cerillion.CyrNava/`

Normal desktop storage:
`data/cyrnava/{workspace,workspaces,active-workspace.json,web-profile*,web-cache*,desktop.json}`

P3 generations, recovery drafts, preferences, migration journals and backups keep
their established semantics. Test code redirects only a validated production
configuration into `data/p4-verification/run-<id>/desktop`, never the actual normal
profile. Neither build installs/copies data from the development or Firefox roots.
The host procedure refuses an existing production installation/data root for its
fresh-install scenario rather than experimenting on it.

## D. Build architecture and controlled inputs

Runtime: `org.kde.Platform/x86_64/6.11`; SDK: `org.kde.Sdk/x86_64/6.11`;
BaseApp: `io.qt.PySide.BaseApp/x86_64/6.11`; target Python 3.13 and Qt/PySide 6.11
(the installed pinned BaseApp is 6.11.2). Exact commits are checked before/after
assembly against `production/toolchain.lock.json`; mismatches fail without silent
runtime updates. Graphics/runtime extensions remain host-supplied dependencies.

Build command: `backend/.venv/bin/python packaging/flatpak/production/build.py`.
A compatible Python/pip can replace the developer venv. Node 24/npm 11.6.2 are
build tools only. npm ci uses the checked-in lock, ignores install scripts, then
TypeScript/Vite build the production frontend. No Vite/Node server is packaged.

Production Python lock contains 15 required runtime distributions, exact versions
and CPython 3.13/Linux wheel SHA-256 hashes. FastAPI's required opentelemetry-api is
included; no exporter, telemetry configuration or network permission is added.
pytest, Ruff, HTTPX, Pygments, pluggy and iniconfig are excluded. Offline pip
cross-installs binary wheels as data, with no sdist setup code, target execution,
bytecode compilation or runtime dependency downloads. Target interpreter comes
from the declared runtime; Qt/PySide/WebEngine come from the pinned BaseApp.

Flatpak build-init copies BaseApp, the explicit installer adds the allowlisted
application, and standard build-finish/export/bundle construct the unsigned local
artifact. Exported icons are validated with sandboxing enabled. The fixed
production JSON manifest also describes staged inputs for flatpak-builder; that
alternate route is NOT TESTED here. The canonical custom data-assembly route
reuses Flatpak primitives without invoking target application code during build.

Input records include Git baseline, actual source hashes, frontend lock/package
hashes, wheel hashes, tool versions and pinned core refs. P4 is uncommitted; the
Git SHA alone does not identify these changes. Fixed export timestamp is
`2026-10-29T23:00:00Z` (epoch 1793314800), and local build IDs distinguish A/B artifacts. These controls support
repeatable pinned inputs. **Byte-for-byte reproducibility and clean-checkout
replay have not been demonstrated.** No such claim is made.

## E. Package-content audit

Final staged inventory: **5,320 entries, 980,983,648 logical bytes** (about 981 MB,
936 MiB). Every regular payload file has size/SHA-256; every symlink has its target
recorded. Full inventory is in `evidence/p4/package-inventory.json` and the staged
build. Payload files/directories are normalized to portable readable/executable
modes; application data permissions remain private and unchanged.

Application source is an explicit runtime-module allowlist. Frontend output is
limited to expected HTML/JS/CSS/fonts/icons and approved branding. Tests, fixtures,
evidence, recordings, databases, notes, Git metadata, caches, venvs and local env
files are not copied. Source symlinks are rejected. Final audit rejects prohibited
paths, database/log/key/env/capture extensions, and escaping links. It does not
rely on .gitignore. Explicit boundaries plus inventory are not a claim of a general
secret-scanner proof against malicious source substitutions.

BaseApp's developer entry points, build helpers, headers, CMake/pkgconfig files,
debug directory and dependency test/agent directories are removed; required
WebEngine helper, libraries, plugins, resources, dictionaries, translations and
upstream license material remain. An initial audit caught `.agents` shipped in
the FastAPI wheel; it was excluded before the final audited payload.
Third-party license/notices are included. No owner data was read for packaging.
Finish refuses payload changes relative to the recorded audit.

## F. Sandbox and runtime security

Assembled effective `[Context]`, session-bus and system-bus policies match the
installed accepted development package exactly:

- Wayland socket and DRI only; network unshared.
- Home/host filesystems denied. Inherited `xdg-config/kdeglobals:ro` is retained
  solely for Qt desktop appearance; no additional host access.
- Existing Qt desktop bus talks: com.canonical.AppMenu.Registrar,
  org.kde.kconfig.notify, org.kde.KGlobalSettings. No system-bus permission.
- Matching `/app/bin/QtWebEngineProcess`, dictionaries and Qt portal theme.

No Chromium sandbox override, remote debugging, privileged JS bridge, public
listener or tool execution was added. Backend credential/death pipes, loopback
bind, authenticated session, Host/Origin checks, readiness polling, close/recovery
protocol and reaping remain the accepted implementations. Regression tests pass.

**Installed production effective permissions, renderer sandbox and network
isolation PASS in the first owner host run**, independently inspected below.
Full functional/update/rollback acceptance remains pending. The host verifier records
actual installed permissions, rejects added capabilities, compares network
namespaces, checks an inaccessible host canary, tests API rejections and duplicate
profile locking, and collects Chromium diagnostic plus renderer namespace/seccomp
evidence. The staging comparison is not substituted for real installed evidence.

## G. Desktop integration and metadata

Name/title: CyrNava. Launcher: `cyrnava`, runs bundled Python native module from
`/app/share/cyrnava`; no source-checkout access or external server is needed.
Qt desktop filename/Wayland identity and window icon use the build identity.
The original owner logo and its checked-in 16–512 px derivatives are installed in
hicolor; no invented SVG artwork or external brand asset was introduced.

Desktop-file validation passes. AppStream validation passes with two informational
notices (no content rating or developer entry). No privacy/support site, commercial
license or public release history was invented. Existing GitHub URL is the
homepage. Owner approved CC0-1.0 **only for new metadata**; project code remains
LicenseRef-proprietary pending the original license decision. No code/logo rights
were changed. Public redistribution clearance remains outside this local sprint.
Actual desktop launcher/icon, welcome, dialogs and clipboard still need host checks.

## H. Installation, update, rollback and uninstall

See `packaging/flatpak/production/README.md` and `P4_NATIVE_CHECKS.md`.
Current state: Build A export and bundle creation PASS on the owner host; no
production installation has been verified. Build B export/bundle also PASS. Install/reinstallation, real
launch, update, binary rollback and uninstall remain **NOT TESTED**.

The owner supervisor verifies distinct artifact hashes/commits, installs A,
exercises an isolated synthetic workspace, restarts, updates to B, rolls back to A,
checks native backup export/import and supported recovery, tests future-schema
refusal on a copied generation, uninstalls without --delete-data, verifies
synthetic data unchanged, and reinstalls B. Development's installed commit must
stay unchanged. New schema refusal is automated locally with DB hash preservation.

Binary rollback does not roll back schema. P3 compatible verified snapshots and
workspace selection are the recovery path; no speculative reverse migration.
Metadata-only local-A/local-B are test build IDs at app 0.1.0, not invented public
versions. A future reviewed SemVer source shared by frontend/backend/metadata/tags
is recommended, but release automation/signing/distribution belong to P5.

## I. Verification

Machine-readable results and raw failure logs: `evidence/p4/validation.json`.

| Check | Result |
|---|---|
| P3 final recorded evidence/hash reconciliation | PASS |
| Baseline focused backend/native/migration | 67 PASS |
| Final comprehensive backend + retained P2/P3 + initial P4 tests | 501 PASS, 2 existing warnings |
| Final packaging/host-supervisor contracts | 21 PASS (includes later permission/tamper/resume coverage) |
| Post-hardening focused native/packaging | 52 PASS before the last mocked supervisor cases |
| Frontend unit suite | 273 PASS, 22 files |
| Release browser suite | 16 PASS, 1.8 min |
| Actual offscreen Qt migration workflow | PASS; chooser selections mocked |
| Actual Qt portal/event-delivery/edit-prerequisite probe | PASS; DBus replies simulated |
| Production desktop and AppStream validation | PASS; informational notices only |
| Package audit/effective assembled permission comparison | PASS |
| Ruff, Python compile checks, git diff --check | PASS |
| Final Flatpak export / bundle A | PASS on owner host; independently hash/ref verified |
| Production native install/launch/portals/update/uninstall | NOT TESTED |

Comprehensive command (the backend working directory matters for CLI subprocesses):

```bash
cd backend
.venv/bin/python -m pytest -q tests ../packaging/flatpak/test_verify_outage.py ../packaging/flatpak/test_run_portal_verification.py ../packaging/flatpak/test_run_migration_verification.py ../packaging/flatpak/production/test_packaging.py
```

Focused P4 tests: `backend/.venv/bin/python -m pytest -q packaging/flatpak/production/test_packaging.py`.
Frontend: `npm --prefix frontend test`; browser: `npm --prefix frontend run test:release`.
The temporary Qt bootstrap reuses already installed matched Flatpak libraries for
offscreen widgets; it installs no dependencies and does not verify WebEngine.
Native host-driver execution is NOT TESTED; mocked supervisor tests establish
failure/evidence gating, not actual portals or renderer behavior.

Historical failures are retained: denied external-cache creation, .woff staging
allowlist omission, upstream wheel agent tooling caught by audit, a public APP_ID
export removed by lint and restored after collection failure, eight CLI-context
failures from running backend tests at the wrong cwd, and namespace-blocked final
exports. The documented cwd rerun passed all 501. No failed run was relabeled PASS.
Discarded generated build duplicates were removed only after saving result/input
records; the final assembled build is retained. No application data was cleaned.

## J. Performance and size

| Measurement | Observed state |
|---|---|
| Staged logical payload | 980,983,648 bytes, 5,320 entries |
| Flatpak bundle A size | 209,183,720 bytes (~209 MB / 199.5 MiB) |
| Actual installed production footprint | NOT TESTED |
| First-run/warm startup, backend readiness/shutdown | NOT TESTED |
| Idle RSS | NOT TESTED |

The staged payload is larger than P2's reported ~738 MB installed ref because the
custom assembly retains BaseApp locales (~296 MiB) in the main payload; P2's
flatpak-builder split them into a separate optional Locale extension. Production
also removes test tools/headers, so this is not evidence of runtime memory growth.
Core Qt/WebEngine components were not removed for size. The uncompressed staged
logical total and Flatpak's installed-ref metric are different measures. The host
helper records frontend/backend timings and sampled RSS; these are not a true
cold-OS-cache or settled idle-memory benchmark. No performance improvement claimed.
Builds require 5 GiB free and a volume outside RAM-backed /tmp where practical.

## K. Risks, limits and deferred work

- Genuine blocker: session namespace policy prevents sandboxed icon validation and
  production execution. Finish on the normal Ubuntu host; do not disable security.
- x86_64/Wayland-only configuration; other architectures and X11 are not claimed.
- Pinned runtime commits must be supplied by a trusted runtime source; different
  versions fail clearly and need a reviewed lock update, not silent substitution.
- No byte reproducibility or clean-checkout replay proof yet.
- Host scripts are prepared/tested at contract boundaries; real native workflows
  may reveal defects and must be diagnosed before another run is requested.
- Production code license/previous attribution provenance remain pending for
  future public distribution. Only AppStream metadata CC0 was approved in P4.
- User-data migration, public release, signing/remote setup, automatic updates,
  Flathub submission and P5/P6 are outside scope and have not been performed.

## L. Recommendation and owner checklist

**P4 STATUS: CONDITIONAL — OWNER HOST VERIFICATION REQUIRED**

- [x] Reconcile P3 acceptance from recorded results, preserve history.
- [x] Explicit approved production identity, separate development configuration.
- [x] Pinned inputs, assembled payload, metadata, content and permission audits.
- [x] Available automated verification and owner host procedure.
- [x] Complete protected export and produce local artifact A.
- [x] Produce local artifact B for update/rollback tests.
- [x] Record synthetic production install/launch/security/persistence/update/rollback results.
- [ ] Record native backup/import, safe uninstall/reinstall and development isolation.
- [ ] Owner verifies real desktop launcher/icon/first-run/shortcuts/formatting.
- [ ] Owner reviews final evidence and accepts P4. P5 stays unauthorized.

Do not perform real-data migration. Stop after P4.

## Host export correction — 30 October 2026

The owner's final-export attempt passed metadata validation, then failed because
`flatpak build-export --timestamp` requires an ISO 8601 date. The script incorrectly
supplied numeric Unix seconds. It now passes `2026-10-29T23:00:00Z`, representing
the same instant. This is a build-driver defect, unrelated to the application
payload or renderer sandbox. The protected production export remains pending.

The focused packaging suite passes all 22 tests. The new regression invokes real
Flatpak export on an icon-free synthetic fixture and independently checks the
OSTree commit date. This exercises the actual parser without disabling any
sandbox; it does not count as a successful production/icon export. No application
rebuild is required. Prior host FAIL and regression evidence are preserved under
`evidence/p4/timestamp-correction-2026-10-30/`. Repeat the same --finish command
from the regular Ubuntu terminal. P4 remains CONDITIONAL.

## Build A final export — 30 October 2026

Owner-host export/bundle creation completed with PASS. Independent local reads
verified size **209,183,720 bytes**, SHA-256
`856cc0ccd82bca263320e2d692a5b3d316543ae320cd76d9cd42bf42e54a3170`,
and OSTree ref
`e0529b136effc347a5f7a32b52d95ddd5fead5230410e752ce8eb8f9a4c35e19`.
This supersedes earlier build-A export blockers while preserving their raw
records. Build B and real production native checks are still pending; P4 remains
CONDITIONAL. No installation or user-data migration was inferred from build PASS.

## Build B final export — 30 October 2026

Build B PASS was independently verified at
`/home/cerillion/.cache/cyrnava-builds/p4/local-B-f26wev2b`. Bundle size
**209,186,816 bytes**, SHA-256
`96f17ff6a7e46763c846a223d27029f96071b421e167f27263672b6f45e25d8e`,
OSTree commit
`b49969699b4e52df078193713a1aca9a1e8def70f608ba46d700e48d0be5d5c5`.
A/B commits are distinct. Both local build artifacts now exist; production
installation, update, rollback and native acceptance remain NOT TESTED.

## First production host test: run-83587bd18651

Fresh production installation/effective permissions PASS. Actual production
private network/filesystem, single-instance lock, API authentication/Origin,
window title, Chromium Flatpak sandbox/renderer namespace/seccomp and owned
backend reap checks PASS. Overall EDIT failed because required saved edits were
incomplete. The owner confirmed manual closure. Read-only synthetic profile
inspection finds one folder and one saved screenshot asset, but no exact
`P4 owner edit` title. These partial results are not full P4 acceptance.

Observed backend readiness 840.0 ms, frontend load 2372.0 ms and backend shutdown
163.9 ms are single startup samples, not controlled cold/warm or idle benchmarks.
Renderer diagnostic and process RSS/namespace data remain in the original record.

The host-only driver now presents edit instructions inside the window, reports
individual missing title/image/folder/preference checks, serializes preference
state explicitly through JSON.stringify, and does not erase the last valid sample
when WebEngine cancels callbacks during normal teardown. A guarded --resume option
validates the known A/B artifacts, original fresh-install PASS and installed A,
refuses normal production profiles, archives old phase records and preserves
existing synthetic notes instead of creating duplicate seed data. No production
payload/security behavior was changed, so no rebuild is required. All 27 focused
tests pass, including fresh/resumed supervisor success/failure contracts and saved
state/preference regressions. Evidence is in `evidence/p4/owner-run-83587bd18651/`.
Native continuation remains pending.

## Resumed host results — 30 October 2026

The latest recorded EDIT, RESTART, UPDATED and ROLLBACK phases are complete PASS,
including exact title, screenshot asset, folder, persisted Dark preference,
API authentication/Origin rejection, private networking/filesystem isolation,
single-instance lock, effective renderer sandbox and owned backend cleanup.
The same preference digest is recorded across all four phases.

| Phase | Backend ready ms | Frontend loaded ms | Shutdown ms |
| --- | ---: | ---: | ---: |
| Edit | 1028.0 | 2004.0 | 164.1 |
| Restart | 976.9 | 1758.4 | 214.0 |
| Update B | 1081.1 | 1925.2 | 214.1 |
| Rollback A | 788.3 | 1520.1 | 214.0 |

These are individual observations, not controlled performance benchmarks.
Recorded helper SHA-256:
`02b85571ac7da81dc168df54e4efc7ca2ca0172e2c538d3f6e5aeae7b628c005`.

MAINTENANCE remains FAIL: the owner confirmed closing the manager without
importing. Read-only inspection of this synthetic profile finds no active pointer
or imported generation. The failure is consistent with an incomplete required
interaction; no production defect is established. The two supplied recordings
show editing and screenshot interaction, not a completed native backup/import.
Recovery and uninstall/reinstall have NOT TESTED status for this run.

Original JSON and supervisor output are copied unchanged under
`evidence/p4/owner-run-83587bd18651/resumed-2026-10-30-maintenance-incomplete/`.
Earlier failures remain preserved. The corrected host-only diagnostics report
whether a new workspace was activated, records match and owner edits remain.
`--resume ... --continue-maintenance` validates complete prior records and matching
preferences, build identity, installed A and synthetic-only storage before
skipping the already passing phases. Previous JSON is archived before resuming.
The checkpoint's original helper hash is retained alongside the new helper hash.
Production behavior, permissions and package contents are unchanged; no rebuild
is required. All 36 focused packaging/driver tests pass, including rejection of
partial/failed/mismatched checkpoints and failure when no import occurs.
P4 remains CONDITIONAL pending native backup/import, recovery, uninstall/reinstall,
real desktop launcher checks and owner review. P5/P6 have not begun.

## Backup filename/filter correction — 30 October 2026

The owner supplied `/home/cerillion/test`, an extensionless ZIP-format CyrNava
backup. Independent unpack/validation into disposable temporary storage passed:
schema 5, one note, two folders and two assets. SHA-256 before/after was unchanged.
The recording shows the import chooser filtering for CyrNava backups and hiding
that extensionless file. Latest native evidence still reports
`import_activated_new_workspace: FAIL`; reported success after manual extraction
is not counted as successful direct archive import.

This establishes a production chooser usability defect: save accepted a name
without `.cyrnava`, while import offered only the `.cyrnava` filter. The bounded
correction suggests `cyrnava-backup.cyrnava` before saving, and offers ZIP plus
All files on import. Returned portal paths are never renamed or suffixed by the
application; ungranted sibling paths are never accessed. Archive validation,
resource limits, staging and confirmation remain unchanged. An archive must be
imported directly; manual extraction is unnecessary.

Installed A/B artifacts predate this source correction. Their compatible owner
workaround is to type the full name `test.cyrnava` when saving, then select that
same archive for import. Native validation of the chooser correction itself
remains outstanding until a corrected candidate is built/tested. P4 remains
CONDITIONAL. Evidence: `evidence/p4/backup-extension-2026-10-30/`.

Filename/portal-contract, migration integrity (including extensionless/ZIP archives),
and P4 packaging regressions: **76 PASS** in 0.82 s. Ruff, compileall and diff
checks passed. The initial restricted-network run stalled in the local API test;
it was interrupted and rerun successfully with local socket access. No native
portal PASS is inferred from automated chooser mocks.
