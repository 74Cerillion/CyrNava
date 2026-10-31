# CyrNava P5A — Continuous integration assessment

Date: 31 October 2026, Asia/Seoul.

**P5A STATUS: FAIL — GITHUB-HOSTED BACKEND VERIFICATION FAILED**

## A. Executive summary

Implemented and pushed the reviewed verification-only workflow as commit
`329020b5286ce0d5474e04a781ed61a6079f8edc`. The owner completed the single approved
push after the agent terminal lacked Git HTTPS credentials. No additional commit,
push, dispatch or rerun was performed.

[GitHub run 41157614256](https://github.com/74Cerillion/CyrNava/actions/runs/41157614256),
attempt 1, completed **FAIL**. Workflow validation passed; frontend passed 273 unit
and 16 browser tests. Backend passed 543 tests and failed 3 because its clean job
checkout has no generated `frontend/dist`. The production Flatpak build was skipped
and the final required gate failed. **No production package or checksum exists.**

The missing-assets cause was reproduced with a disposable source tree. Local
verification had passed because generated frontend assets already existed there.
No application security control was weakened. Detailed logs, JUnit, runner data and
independently verified diagnostic ZIP digests are saved under
`evidence/p5a/hosted-attempt-2026-10-31/`.

P5A is not accepted. The proposed correction is an explicit real frontend build
prerequisite for backend tests, followed by clean-checkout regression coverage.
No implementation correction or second push was made; the owner instructed that
this turn stop after reporting the hosted verification results. No release,
signing, hosting, main merge or P5B/P5C work occurred.

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
2. `backend`: requires validate; backend/security/lifecycle/migration/packaging tests.
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
This enforces backend/app/tests/CI Ruff with `backend/pyproject.toml`, then runs
all existing backend tests and retained P2/P3/P4 verifier tests plus new CI tests,
from the required backend working directory. JSON durations and JUnit are saved.

Final local run: **546 PASS**, two existing warnings and 28 subtests PASS, 31.64 seconds
of pytest time. New tests cover workflow policy, final-job failure/skips/cancellation,
missing executable, deliberate exit 17, runtime pin refusal, payload identity and
permissions, missing WebEngine helper, prohibited files, corrupt bundle, staged
artifact/provenance contracts, explicit output and symlink/overlay refusal.
Backend requirements retain their existing exact pins; they are not hash locked.
Production wheel hashes remain enforced separately. Clean dependency resolution
and `pip check` passed. No personal profiles or datasets are used.

## E. Frontend verification

Canonical command: `backend/.venv/bin/python ci/verify.py frontend`.
Requires backend venv, Node 24.19.0, npm 11.6.2, `npm ci --ignore-scripts`, and the
lockfile's Chromium installation through Playwright. No separate dev service is
required for the production-mode integration tests.

ESLint, 273 unit tests, TypeScript/Vite and all 16 browser integration tests pass.
The final orchestrated results and exact durations are in `evidence/p5a/validation.json`
and `frontend-final.txt`. Existing Vite large-chunk and BlockNote jsdom viewport
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

The backend job installs Python dependencies but does not build the frontend.
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

Hosted runtime provisioning/build/icon sandbox validators and production artifact upload remain unexecuted because the backend job failed. Backend test setup needs an explicit frontend-assets prerequisite. A rerun of unchanged source would repeat the deterministic failure. If hosted AppArmor/namespace
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

**P5A STATUS: FAIL — GITHUB-HOSTED BACKEND VERIFICATION FAILED**

- [x] Preserve accepted P4 architecture and existing integration branch.
- [x] Implement least-privilege, pinned, verification-only workflow.
- [x] Pass available local backend/frontend/security/CI contract checks.
- [x] Preserve negative results and distinguish synthetic/native/hosted evidence.
- [x] Deliver workflow, helpers, audit, checksum/provenance and owner procedure.
- [x] Owner authorizes one P5A commit and push.
- [x] Owner completed the single approved push; exact commit observed in the hosted run.
- [ ] Correct the backend frontend-assets prerequisite, then obtain an authorized successful hosted build/audit/upload. Current attempt FAIL.
- [ ] Owner explicitly accepts P5A.

Stop after P5A. No P5B or P5C work is authorized or implemented.

## Final local checkpoint

Final wrapper timings: backend **32.318 s**, frontend **124.732 s**.
Frontend steps: lint 2.699 s, units 14.584 s, TypeScript/build 3.828 s,
Chromium 103.621 s. Workflow contracts: 19 methods with negative subtests.
Exact results, JUnit and source hashes are in `evidence/p5a/`.
Local actionlint syntax/expression checks passed; shellcheck was not installed
locally, so no local shellcheck coverage is claimed. The hosted actionlint may
use the runner's shellcheck when available. The earlier YAML scalar/context
mistakes were corrected before this checkpoint and no hosted run used them.

## Commit/push and reporting boundary

The initial agent-terminal push failed for missing HTTPS authentication; that
historical record is preserved in `push-and-hosted-status.json`. The owner then
completed the same approved push, and the exact commit was observed in Actions.
This resolves the authentication blocker but does not resolve the hosted test
failure. The approved source remains unchanged after that single commit/push.

This report, the owner checks and hosted evidence are updated **locally only**.
They have not been committed or pushed; no second push or workflow trigger was
made. Final structured result: `evidence/p5a/hosted-attempt-2026-10-31/run-41157614256-final.json`.
Stop after reporting P5A FAIL. Any further commit/push requires owner authorization.
