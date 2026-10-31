# CyrNava P5A — Continuous integration assessment

Date: 31 October 2026, Asia/Seoul.

**P5A STATUS: CONDITIONAL — LIFECYCLE TEST CORRECTION LOCALLY VERIFIED; HOSTED VERIFICATION PENDING**

## A. Executive summary — local lifecycle correction ready for review

**P5A STATUS: CONDITIONAL — CORRECTED HOSTED VERIFICATION REQUIRED**

The browser lifecycle test's outage simulation had an invalid precondition: it
installed write interception only after the editor loaded, without establishing
that no save was already dispatched. A controlled real-API/SQLite reproduction
committed revision 4 while withholding acknowledgement, leaving a recovery draft
based on revision 3. On restart, the same older-revision conflict seen in the
hosted screenshot was correctly shown. No production defect was demonstrated;
production behavior is unchanged. The confirmed defect is in test isolation.

The exact request ordering in historical run 41163754626 cannot be independently
proven: its diagnostic artifact contains screenshot/error context but no trace or
revision timeline. Natural baseline repetitions passed 10/10, and 3/3 CPU scheduling
probes passed. We do not label the hosted result flaky or overwrite it with PASS.
The controlled reproduction confirms a permitted failure ordering, not a missing
historical observation. This residual uncertainty remains explicit.

The corrected test installs its PATCH barrier before page startup, keeps it through
restart, verifies the canonical note is unchanged and the draft revision matches,
then checks the real save acknowledgement, content and revision increment. A new
gated regression confirms a genuinely accepted write with a lost acknowledgement
still retains its stale draft and requires conflict review without an automatic
write. Relative timing/revision diagnostics are saved as explicit files under the existing CI diagnostic upload path; failure traces are retained. Cleanup runs even if attaching a diagnostic fails.

Disposable clean-checkout verification passes: **10/10 focused executions** (five
per case), **273 frontend unit tests**, **17 browser tests**, ESLint and TypeScript/
production build. **23 CI contract tests** pass. Backend/security suites were not
rerun because no application/shared lifecycle/backend logic changed; their hosted
550 tests and 31 subtests remain separately recorded PASS, not a new local result.

No timeout increase, arbitrary delay, test suppression or automatic retry was added.
No application, sandbox, authentication, workflow permission or packaging code
changed. No commit, push, dispatch or rerun occurred. Stop for authorization of one
next P5A-only commit/push. P5A cannot be accepted until all required hosted jobs,
including production build, exported-content audit and upload, succeed.

Current evidence: `evidence/p5a/lifecycle-correction-2026-10-31/validation.json` and
`manifest.json`. Both historical hosted failures and earlier reports are preserved.

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

## D. Backend verification — local prerequisite proof

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

## E. Frontend verification — local baseline (hosted failure in section A)

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

No source-built P5A Flatpak PASS/size exists: the first hosted build was skipped after backend failure; the corrected run was skipped after browser failure. P4
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

## J. First hosted attempt — preserved historical failure

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

Hosted runtime provisioning/build/icon sandbox validators and production artifact upload remain unexecuted: the first run failed backend verification, and the corrected run passed backend verification but failed a browser lifecycle test. The frontend-assets prerequisite is resolved on the hosted runner; the browser recovery failure remains unresolved. If hosted AppArmor/namespace
policies block validation, stop and diagnose; do not disable sandboxing or change
kernel security settings as an unreviewed workaround. Upstream pinned historical
commits may eventually be pruned; fail closed and review lock changes explicitly.

P4's final native evidence gaps (launcher/manual checks, corrected chooser in a
rebuilt native artifact, full final supervisor recovery/uninstall record) remain
recorded, not reclassified. Public redistribution licensing and future release
signing/hosting remain outside P5A. No dependency vulnerability scan is claimed:
existing security regressions and actual packaging audits run without adding
redundant scanners. Source review remains necessary for untrusted PR changes.

## M. Second hosted attempt — preserved result before lifecycle correction

Run 41163754626, attempt 1, push event, commit `72f4c7b0ca1de627b7615f03e20393cf5d423512`.
Created **12:17:51 KST**, completed **12:21:35 KST**, 224 s including queue/startup.
Ubuntu 24.04.5 x86_64, image `20261025.353.1`, runner 2.338.2; CPython 3.12.15.
Logged repository token permissions: Contents read, Metadata read.

| Job | Result | Duration |
| --- | --- | ---: |
| Workflow validation | PASS; 23 contract methods and actionlint | 19 s |
| Backend and security | PASS; 550 tests, 31 subtests | 114 s |
| Frontend and browser | FAIL; 273 units pass; 15 browsers pass, 1 fails | 187 s |
| Production Flatpak and bundle audit | SKIPPED | 0 s |
| CI required | FAIL | 2 s |

Backend wrapper 59.868 s; asset installation/build 5.358 + 5.716 = **11.074 s**;
pytest 46.78 s. Its evidence explicitly records initially absent frontend/dist.
Frontend wrapper 141.910 s; lint 3.244, units 14.064, build 4.091, browsers 120.510 s.
Both jobs restored the npm cache. This does not establish a controlled cache speedup.

| Diagnostic artifact | ID | Bytes | Independently verified SHA-256 |
| --- | ---: | ---: | --- |
| Backend | 13027759948 | 10,406 | `b799b5eb3739ec8ad4645fc35b9aba4e7cfcd7856324a494ed97917d2fb4af67` |
| Frontend | 13028024573 | 4,971,285 | `1a34eed295eb5e989025f8ea53b88276941fca508c0cdc67bed412faa1e44fd2` |

- [x] Confirm exact pushed source and automatically triggered hosted run.
- [x] Verify backend correction on clean hosted runner; all previous failures pass.
- [x] Preserve browser failure evidence and verify diagnostic uploads.
- [x] Confirm fail-closed required gate and absence of production artifact.
- [ ] Investigate and resolve lifecycle recovery revision-conflict failure.
- [ ] Obtain explicitly authorized successful hosted verification.
- [ ] Verify actual production build, exported-content audit, upload and package hash.
- [ ] Owner accepts P5A after all required checks succeed.

## N. Historical hosted-review conclusion (local correction follows)

**Recommendation: FAIL / NOT READY FOR ACCEPTANCE.** The production build, package
audit and artifact upload cannot be verified because the required workflow did not
reach them. No result is inferred from old P4 artifacts or passing local tests.
Native Qt/portal coverage and existing P4 evidence limitations remain separate.

The prior terminal authentication blocker was resolved by the owner's push of the
same authorized commit. No additional commit or push is required to record the
current review locally. Current changes are limited to P5A reports and evidence;
no application or CI implementation was changed. No rerun, dispatch, release,
signing, deployment, main merge, P5B or P5C occurred. Stop for owner review.

## O. Lifecycle test correction — implementation and verification

Exact source files: `frontend/e2e/lifecycle.spec.ts` and
`frontend/playwright.config.ts`. Reports: this file, `P5A_OWNER_CHECKS.md` and
`evidence/p5a/validation.json`; supporting artifacts and complete hashes are listed
in `evidence/p5a/lifecycle-correction-2026-10-31/manifest.json`. Prior hosted review
records remain uncommitted from the preceding authorized reporting turn.

The original test remains, with richer invariants and earlier failure injection.
The original killed-browser, all editor/image/search/close protocol checks remain
required. New regression uses a promise gate on a real successful PATCH response,
not a mocked database or synthetic 409. It proves the newer SQLite revision is
preserved, the stale draft remains byte-for-byte, and recovery choice issues no
PATCH. This is expected conflict handling; it is not counted as successful saving.

A fresh clone of `72f4c7b` began without dist, node_modules or backend venv. Fresh
Python and npm dependencies and production assets were prepared with isolated XDG
storage and synthetic workspaces. Only the two final candidate files overlay the
clean baseline. Matching Playwright Chromium binary was reused; no user browser or
profile was accessed. Candidate hashes match the files used for the complete run.

Focused command: `npx --no-install playwright test e2e/lifecycle.spec.ts --grep
'managed tabs close|committed write' --repeat-each=5 --trace=on --reporter=list,json`.
Result: **10 passed, 0 failed, 0 retries**, five executions of each affected case.
Full command: `backend/.venv/bin/python ci/verify.py frontend`: **273 units and
17 browser tests PASS**, full wrapper **132.748 s** (lint 2.53, units 13.933,
TypeScript/build 3.474, Chromium 112.811 s). CI contracts: **23 PASS**, 0.129 s.
Existing Vite chunk/BlockNote warnings remain; no warning suppression was added.

An investigation-only checkpoint originally auto-waited on a save-state element
absent from the recovery-choice screen, causing two invalid diagnostic timeouts.
Those attempts are preserved and excluded from application/regression counts;
non-waiting observation corrected the instrumentation. This did not change the
application or test timeout. See exploration-classification.json for all probes.

`retain-on-failure` now preserves Playwright traces for future hosted failures.
Synthetic revision timelines contain only method/status/revision/relative timing;
no note bodies, titles or authentication headers. Selected local trace ZIPs contain
only disposable synthetic test traffic, are locally retained and hash recorded;
they may be ignored by Git. No production credentials or personal data were used.

## P. Current recommendation and authorization checkpoint

**CONDITIONAL: local correction ready; P5A remains unaccepted.** The test's missing
precondition is confirmed and corrected, but historical causality cannot be proved
from absent hosted traces. A new hosted run must establish the correction and
reach production Flatpak build, package-content audit and validated artifact upload.
Their latest actual result is still SKIPPED / NOT EXECUTED, not PASS.

- [x] Inspect hosted screenshot/context and preserve failures.
- [x] Trace revisions and reproduce the same conflict with controlled real I/O.
- [x] Correct test synchronization and verify stale-write protections.
- [x] Pass repeated focused checks and the complete frontend suite in clean clone.
- [x] Update reports/evidence and preserve all existing tests/security controls.
- [ ] Owner authorizes one next P5A-only commit and push.
- [ ] Successful hosted required jobs, actual bundle audit/upload/hash verification.
- [ ] Owner accepts P5A.

HEAD remains `72f4c7b0ca1de627b7615f03e20393cf5d423512`. No new commit, push,
workflow trigger, production user-data access, P5B or P5C work occurred.

## Authorized lifecycle correction commit / push status

Created exactly one authorized commit: `129700175cf4716446647572979771d27422fc3f`,
60 P5A-only files. Staged source/evidence review, credential-pattern checks and
trace header/origin inspection passed. Three traces contain only disposable
loopback traffic and synthetic note viewport captures, with no credential-bearing
headers. Workflow is unchanged, verification-only, contents read. Production
security/conflict handling is unchanged; historical uncertainty remains explicit.

Historical failure JUnit/error-context files retain their original traceback
whitespace; all other staged files passed whitespace checks. Historical failures
were preserved verbatim.

The single push attempt failed (exit 128): terminal has no Git HTTPS credentials.
Read-only GitHub inspection confirms the remote remains at `72f4c7b`. No new
workflow was started; no production build/audit/upload result exists for this
correction. Owner must complete the same already-authorized push from an
authenticated terminal. No further commit, push, dispatch or rerun occurred.

Current acceptance recommendation remains CONDITIONAL / UNACCEPTED pending actual
hosted verification. See `evidence/p5a/lifecycle-commit-review-2026-10-31/push-status.json`.
This post-commit status update is local/uncommitted; it will not cause another push.
