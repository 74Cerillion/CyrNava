# CyrNava P5A — Continuous integration assessment

Date: 31 October 2026, Asia/Seoul.

**P5A STATUS: CONDITIONAL — LOCAL CORRECTION PASSED; HOSTED VERIFICATION PENDING**

## A. Executive summary

The backend CI preparation defect is corrected locally. Its job independently installs
locked frontend dependencies and builds real production assets before running the
unchanged full backend/security/lifecycle/migration/packaging test selection. It
uses the same pinned Node setup as the frontend job, without cross-job artifacts.
Permissions, failure propagation, package audit and upload gates are unchanged.

A disposable clone of `329020b5286ce0d5474e04a781ed61a6079f8edc` began with a
clean tracked baseline and no `frontend/dist`, `node_modules` or backend venv.
Only the four corrected source files were overlaid, explicitly uncommitted. Fresh
isolated dependencies were installed. Backend: **550 passed, 31 subtests passed**,
two existing warnings; frontend: **273 unit and 16 browser tests passed**. All
three previously failing tests passed. Four new CI contract tests bring the
standalone contract suite from 19 to 23 methods. This is local verification,
not a new GitHub-hosted PASS.

The first and only hosted [run 41157614256](https://github.com/74Cerillion/CyrNava/actions/runs/41157614256)
remains FAIL. Its original records and pre-correction reports are preserved.
No new commit, push, manual trigger, release, signing or P5B/P5C work occurred.
The correction is ready for owner review and authorization of one additional
commit/push. A successful hosted build, actual bundle audit, upload and checksum
verification are still required before P5A acceptance.

Correction evidence: `evidence/p5a/frontend-prerequisite-correction-2026-10-31/`.
See its `validation.json`, `setup.json`, JUnit, logs, patch and `manifest.json`.

## B. Repository baseline

- Repository: `74Cerillion/CyrNava` (public).
- Branch: `desktop/p2-production-integration`, unchanged.
- Starting HEAD: `8418339cf3c9ff7ae26f792ed8697b7c16d7450a`, “Complete P4”.
- Upstream: `origin/desktop/p2-production-integration`; initial worktree clean.
- No tags or existing workflows at baseline; read-only GitHub inspection found
  zero workflows. This does not establish whether Actions is enabled in settings.
- App version 0.1.0, schema 5, runtime lock and production/development IDs unchanged.
- P4 acceptance record: `desktop/native/evidence/p4/closeout-2026-10-30/owner-acceptance.json`.
  P4 was closed by owner acceptance with explicit native evidence limitations.
  P2/P3/P4 records are preserved. CI does not retroactively close those gaps.

Baseline backend/P2/P3/P4 tests: 527 PASS, two existing warnings, 32.78 seconds.
Frontend ESLint and 273 unit tests PASS. Ruff under the committed backend config
found 16 import-order issues in test files; only imports were reordered. No test
was removed, marked optional or excluded. Host-inherited Ruff settings are not
used as an undocumented CI dependency.

## C. CI architecture

`.github/workflows/ci.yml` has five jobs on Ubuntu 24.04 x86_64:

1. `validate`: parse/security policy, negative contracts, pinned actionlint.
2. `backend`: requires validate; its own locked npm install and production build,
   then backend/security/lifecycle/migration/packaging tests.
3. `frontend`: requires validate; ESLint, unit tests, TypeScript/build, Chromium.
4. `flatpak`: requires both test jobs; provision locked runtimes, P4 build, audit,
   then upload the validated unsigned bundle and checksum/provenance.
5. `required`: always runs after all four and accepts only all-success results.

Triggers: integration/main pushes, PRs targeting main, manual dispatch. No path
filters, tag/deployment/release triggers, matrices or privileged PR context.
Same-ref concurrency cancels obsolete runs. Timeouts: 10/15/20/45/2 minutes.
The stable required check name is `CI required`; no branch-protection setting was
changed. All jobs default to `contents: read` and ephemeral hosted runners.

## D. Backend verification

Canonical command: `backend/.venv/bin/python ci/verify.py backend`.
CI adds `--require-clean-frontend`: it fails with final evidence if generated assets
already exist at entry, without deleting them. The normal local command allows a
warm checkout but still runs `npm ci` and the real production build before pytest.
Node 24.19.0 and npm 11.6.2 are required. Ruff runs under the committed backend
configuration. The original full test selection is unchanged.

Clean-clone result: **550 PASS**, **31 subtests PASS**, two existing warnings;
pytest 30.65 s, wrapper 41.472 s. Dependency installation/build added 10.142 s
(6.663 s npm ci + 3.479 s build), a reasonable local cost without shared artifacts.
Separate fresh Python dependency installation and `pip check` passed. Backend
requirements retain their existing pins; production wheel hashes remain enforced
separately. Synthetic tests used isolated XDG paths, pip/npm caches and profiles.

New regression coverage requires Node and the strict clean-assets command in the
workflow, checks installation/build ordering before the preserved suite, rejects
warm input without deleting it, and proves build failure stops downstream tests
and writes FAIL evidence. The real disposable-clone run demonstrates success
starting without production assets; mocks alone are not claimed as that proof.

## E. Frontend verification

Canonical command: `backend/.venv/bin/python ci/verify.py frontend`.
Requires backend venv, Node 24.19.0, npm 11.6.2, `npm ci --ignore-scripts`, and the
lockfile's Chromium installation through Playwright. No separate dev service is
required for the production-mode integration tests.

ESLint, 273 unit tests, TypeScript/Vite and all 16 browser integration tests pass.
The corrected clean-clone wrapper took 122.877 s: lint 2.697 s, unit tests
14.156 s, TypeScript/build 3.394 s and Chromium 102.630 s. Browser installation
took a separate 56.678 s; that is not backend build overhead. Results and logs
are in the correction evidence directory; earlier local records remain historical. Existing Vite large-chunk and BlockNote jsdom viewport
warnings are retained. No frontend application behavior was changed.

Coverage boundaries: component/unit != real Chromium != Qt WebEngine != native
host portals. CI does not claim effective renderer sandbox/native chooser tests
from ordinary Playwright or synthetic structural fixtures.

## F. Production Flatpak build

`ci/flatpak.py` reuses `packaging/flatpak/production/build.py`, with one optional
`--output-directory NEW_PATH` argument to select a new CI build directory safely.
The default local P4 build path/behavior remains. No parallel CI-only packager.
The payload auditor now closes file handles explicitly during hashing, fixing a
ResourceWarning observed when running its tests under unittest.

Unchanged runtime: KDE Platform/Sdk 6.11, PySide BaseApp 6.11, CPython 3.13 runtime,
Qt/WebEngine, app 0.1.0/schema 5. The workflow installs GPG-verified upstream refs,
selects exact P4 lock commits, verifies them and fails if any are missing. Read-only
HTTP probes found all three locked commit objects available. This availability
probe is not equivalent to installing/verifying them on a hosted runner.

No new source-built P5A Flatpak PASS/size exists: hosted build was skipped after backend failure. P4
A/B were about 209 MB compressed and 981 MB logical payload; these are historical
reference values, not a newly produced CI artifact. The Codex environment cannot
perform the required build validator namespaces. No security workaround is added.

## G. Workflow and artifact security

- Read-only repository permissions; checkout never persists credentials.
- Official checkout/setup-python/setup-node/upload-artifact actions pinned to
  immutable SHAs in `ci/tools.json`; action metadata fetched and pins verified.
- No production secrets, signing keys, write token, privileged PR build or deploy.
- No GitHub expression interpolation inside run shell scripts. Step values pass
  through quoted environment variables where necessary.
- Locked actionlint download SHA-256 verified before extracting only its executable.
- PyYAML parser wheel pinned/hash locked for CPython 3.12/Linux x86_64.
- P4's source allowlists, production wheel hashes and validators remain active.
- Exported `.flatpak` is imported into an isolated OSTree repo and checked out;
  the actual payload, identity, permissions, required files and inventory are
  checked against build records. Source SHA, package size/hash/ref must match.
- No application code is executed during package audit. Filename/path/content
  inventory checks are not a general proof that arbitrary source cannot hide a
  secret; review and least-privilege contexts remain necessary.

See [GitHub secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use)
and [Flatpak command reference](https://docs.flatpak.org/en/latest/flatpak-command-reference.html).
P4 renderer sandbox, API authentication/Host/Origin/private-loopback behavior is
preserved and its existing tests continue to run. No application permissions changed.

## H. Artifacts and provenance

Validated artifact: `CyrNava-linux-x86_64-<source-sha>-<attempt>`, seven-day retention,
compression level zero. Contains unsigned `.flatpak`, `SHA256SUMS`, source/build
inputs, inventory, result and provenance (source SHA, app version/ID, runtime,
runner image, run ID/attempt, export/build timestamps, size and checksum).
Missing files or upload errors fail the job. Audit failure prevents package upload.
Separate diagnostics contain only selected JSON, JUnit and synthetic screenshots;
no environment dumps, unvalidated bundles, full build directories or home profiles.

Artifacts in this public repository may be downloaded by authenticated readers;
they are neither private storage nor a public application release/update channel.
No signing or GitHub Releases capability is implemented.

## I. Performance and caching

Independent backend/frontend jobs run in parallel after validation. Flatpak only
runs after both pass. Timed step JSON and hosted runner job timings provide the
future workflow measurements. Hosted workflow took 233 s; the first frontend npm cache lookup was a MISS and a cache was saved. Warm hosted restore benefit remains unmeasured.

Local npm download cache: cold 8.578 s, warm 2.963 s, roughly 67 MB. Enabled only
that cache; keys account for package lock, package/npm configuration and Node
version, plus the official action's OS/architecture scoping. PR caches remain ref
scoped; dependency integrity is rechecked by npm ci. No node_modules, completed
artifact, entire Qt environment or signing material is cached. Full Flatpak/Python
cache overhead is unmeasured and those caches are not enabled speculatively.

Real prior-bundle import/audit/rejection took 40.415 s. This is an audit observation,
not a production build or native startup benchmark. Python/runner OS patch and apt
packages may evolve; recorded inputs do not establish byte reproducibility.

## J. Actual GitHub-hosted verification

- Run: [41157614256](https://github.com/74Cerillion/CyrNava/actions/runs/41157614256), attempt 1, push event.
- Source SHA: `329020b5286ce0d5474e04a781ed61a6079f8edc`.
- Started 31 October 2026 **10:55:30 KST**, completed **10:59:23 KST** (233 s).
- Runner: Ubuntu 24.04.5 x86_64, image `ubuntu-24.04` version `20261025.353.1`,
  runner `2.338.2`; backend CPython `3.12.15`.
- Logged token permissions: Contents read, Metadata read.

| Job | Result | Job duration |
| --- | --- | ---: |
| Workflow validation | PASS; 19 contract tests plus actionlint | 8 s |
| Backend and security | FAIL; 543 passed, 3 failed, 28 subtests passed | 59 s |
| Frontend and browser | PASS; lint, 273 units, TypeScript/Vite, 16 browsers | 215 s |
| Production Flatpak and bundle audit | SKIPPED after required backend failure | 0 s |
| CI required | FAIL, correctly rejecting the failed/skipped dependencies | 2 s |

Backend lint passed. Pytest failed in 35.39 s:

1. `test_real_backend_restart_revokes_token_preserves_content` — owned backend
   exits during startup because production frontend assets are absent.
2. `test_parent_death_pipe_stops_worker_and_lock_survives_gui_release` — same startup prerequisite.
3. `test_stage_and_install_exclude_owner_data_and_development_tools` — explicit
   `ValueError: Production frontend build missing`.

At the failed source revision, the backend job installed Python dependencies but did not build the frontend.
The independent frontend job's generated files are on a different runner and
cannot satisfy that prerequisite. An isolated code copy without `frontend/dist`
reproduced `Frontend build missing` and confirmed the owned process was reaped.
This is a confirmed CI preparation defect; no production architecture change is
needed to fix it. Earlier local PASS did not demonstrate a clean-checkout run.

Hosted frontend step timings: lint 4.453 s, units 15.831 s, TypeScript/build 5.335 s,
Chromium 127.796 s (153.415 s for the test wrapper, excluding setup/upload).

Both diagnostic uploads succeeded and their downloaded ZIP digests were independently
verified. These are **diagnostics, not production Flatpak checksums**:

| Artifact | ID | Bytes | SHA-256 |
| --- | ---: | ---: | --- |
| Backend diagnostics | 13026131792 | 12,225 | `30adeec94e96176f536790a7ddfc654f6d5002fb9bdd428eb9e1c2f90407f283` |
| Frontend diagnostics | 13025193988 | 4,871,567 | `8dacb24c2e2288fa991e3667a691b25c50d9f67da16f99665b7a79512b1d09ba` |

Production Flatpak artifact/checksum: **NOT PRODUCED**. Runtime provisioning,
production build, exported-payload audit and production upload were not executed.
No hosted PASS or successful package build is inferred from diagnostic uploads.

## K. Fail-closed verification

- A real isolated subprocess intentionally exited 17. Orchestrator returned 1,
  wrote final FAIL evidence, and did not execute the later marker/upload step.
- The exact final gate shell was run with success/failure/skipped/cancelled/empty
  results for every dependency. Only all-success exited zero.
- Policy mutations rejected write permissions, mutable actions, path filters,
  credential persistence, broad continue-on-error and ungated package upload.
- Payload fixtures rejected wrong production identity, missing helper, host network
  access, a prohibited synthetic database and corrupt package checksum.
- Real P4 artifact A was imported and checked out through Flatpak/OSTree. Payload
  identity/security, inventory and packaged metadata matched, then the auditor
  correctly rejected it with `Build source commit mismatch`. No upload directory
  was created. This was an expected negative test, not a new CI build success.
- Initial local import hit /var/tmp write restrictions; a scoped temporary-directory
  permission grant allowed the test. No application/system security was disabled.

Negative results remain in `evidence/p5a/`. No broken test is committed to the
integration branch, and no release or external workflow was created to simulate failure.
The actual hosted backend failure blocked the production build, and the final required job exited 1. This confirms failure propagation; it does not constitute successful build validation.

## L. Remaining risks and limitations

Hosted runtime provisioning/build/icon sandbox validators and production artifact upload remain unexecuted because the first backend job failed. The explicit frontend-assets prerequisite now passes local clean-clone verification; a corrected hosted run has not been authorized or executed. If hosted AppArmor/namespace
policies block validation, stop and diagnose; do not disable sandboxing or change
kernel security settings as an unreviewed workaround. Upstream pinned historical
commits may eventually be pruned; fail closed and review lock changes explicitly.

P4's final native evidence gaps (launcher/manual checks, corrected chooser in a
rebuilt native artifact, full final supervisor recovery/uninstall record) remain
recorded, not reclassified. Public redistribution licensing and future release
signing/hosting remain outside P5A. No dependency vulnerability scan is claimed:
existing security regressions and actual packaging audits run without adding
redundant scanners. Source review remains necessary for untrusted PR changes.

## M. Recommendation and owner checklist

**P5A STATUS: CONDITIONAL — LOCAL CORRECTION PASSED; HOSTED VERIFICATION PENDING**

- [x] Preserve branch, application behavior and all existing test suites.
- [x] Confirm missing-assets root cause and preserve the first hosted FAIL.
- [x] Independently build production assets in the backend job.
- [x] Verify from a disposable clone without preexisting assets or dependencies.
- [x] Pass 550 backend tests, 31 subtests, 273 units and 16 browser tests.
- [x] Pass 23 CI contract methods, Ruff, actionlint, compile and diff checks.
- [ ] Obtain authorization for one additional P5A-only commit and push.
- [ ] Obtain corrected hosted PASS including production build/audit/upload.
- [ ] Independently verify produced package checksum/provenance; owner accepts P5A.

## N. Exact correction files and review boundary

Implementation: `.github/workflows/ci.yml`, `ci/verify.py`, `ci/validate.py`,
`ci/test_ci.py`. Documentation: `ci/README.md`, `ci/P5A_REPORT.md`,
`ci/P5A_OWNER_CHECKS.md`. Current structured assessment:
`ci/evidence/p5a/validation.json`. Supporting historical hosted records are under
`ci/evidence/p5a/hosted-attempt-2026-10-31/`; new clean-clone results and regression
records are under `ci/evidence/p5a/frontend-prerequisite-correction-2026-10-31/`.
The latter's manifest enumerates each evidence file and checksum. Existing
backend, frontend, desktop and packaging application sources are unchanged.

Available automated suites passed before requesting another hosted execution.
Local ShellCheck is not installed; actionlint syntax/expression validation passed
with ShellCheck integration disabled locally. No new Flatpak/native build is
claimed in this restricted environment. Existing Vite/BlockNote warnings and the
two backend warnings remain documented.

HEAD remains `329020b5286ce0d5474e04a781ed61a6079f8edc`. All correction/reporting
changes are local, uncommitted and unpushed. The first approved push remains the
only push. The original failed hosted run is not rewritten as passing. Following
owner approval, one additional commit/push should trigger validation, parallel
backend/frontend checks, then the production build/audit/upload only if both pass.
Any prerequisite, test or audit failure must fail the final required gate.

Stop at this authorization checkpoint. No release, signing, main merge, public
repository deployment, P5B or P5C is included.

An exploratory lint expansion to unchanged desktop/packaging sources found 98
existing style violations outside the established CI lint scope. They were not
changed or represented as passing; canonical CI Ruff passed. See correction
evidence `exploratory-lint.json`.
