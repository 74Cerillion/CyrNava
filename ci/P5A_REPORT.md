# CyrNava P5A — Continuous integration assessment

Date: 31 October 2026, Asia/Seoul.

**P5A STATUS: ACCEPTED — FORMAL OWNER ACCEPTANCE RECORDED**

## Formal acceptance and milestone

The owner explicitly declared **P5A IS FORMALLY ACCEPTED**, citing run 41181510439
against implementation commit `1ee2077b283b8e5dfc2162119dd439ed3baeb109`.
Acceptance is recorded in `evidence/p5a/hosted-provisioning-2026-10-31/owner-acceptance.json`.
Required hosted results, independently checked artifact checksums/provenance,
historical failures and the blocked additional local re-audit are preserved.
This documentation-only closeout changes no application, tests, locks or workflow.

The owner authorized one documentation-only acceptance commit. Its push requires
separate authorization. Prepare the local `p5a-accepted` milestone tag only after
that documentation commit is verified synchronized with origin; target that
synchronized documentation commit, retaining the tested implementation SHA above.
No tag, release, main merge, P5B or P5C is part of this unsynchronized checkpoint.
Earlier recommendations and pending-acceptance statements below are historical.

## Current result — sixth hosted run: PASS

[Run 41181510439](https://github.com/74Cerillion/CyrNava/actions/runs/41181510439),
attempt 1, was automatically push-triggered for
`1ee2077b283b8e5dfc2162119dd439ed3baeb109` on the authorized branch. Remote ref and
run source SHA match. Run started 2026-10-31 07:40:11 UTC; all five jobs completed
successfully. **PASS; formally accepted by the owner on 31 October 2026.** Older sections
below preserve historical checkpoints and their then-current recommendations.

| Required gate | Actual hosted result |
| --- | --- |
| Workflow validation and negative/security contracts | PASS — 31 contracts |
| Backend/security/lifecycle/migration/packaging | PASS — 567 tests + 31 subtests; two existing warnings |
| Frontend lint, unit, TypeScript, production build | PASS — 273 unit tests |
| Browser integration | PASS — all 20, zero failures/skips; all five lifecycle cases and both image cases |
| P4 runtime provisioning and final exact commits | PASS — all three expected/actual SHAs explicitly equal; 107.064 s |
| Production P4 builder | PASS — unsigned bundle produced |
| Exported package-content audit | PASS — imported exported bundle; permissions, file hashes/inventory and packaged provenance checked |
| Validated unsigned artifact upload | PASS — artifact 13035607417 |
| Independent artifact SHA/provenance verification | PASS — four ZIP digests match GitHub; bundle checksum/source/run/locks agree |
| Final CI required gate | PASS — all four dependency results success |

Package SHA-256:
`93957ce5590818e016c5b9e86ed9c6c1d32a684f6c644af44531c316020b26db`.
Bundle 209,189,544 bytes; audited payload 5,320 entries, 980,984,007 logical bytes.
OSTree commit `da1bf73e3169096522f82249b39f9c9c8546b0317ee6461905bbc6952d6de1ac`.
The 210,238,004-byte artifact ZIP has a distinct SHA-256:
`73e6d58a91ff2e57ca7b801b120ca61eceb399202349345508b8fbf6ce4eba6b`.
Provenance identifies this source commit, run 41181510439/attempt 1, schema 5,
application 0.1.0, fixed OSTree timestamp and unchanged P4 runtime locks.

Independently downloaded package and all three diagnostic archives; matched each
against GitHub's artifact digest. The bundle matches SHA256SUMS, result and
provenance. Independently reviewed the downloaded inventory for unsafe/duplicate
paths, prohibited content and links; all 28 packaged application-source files with
local source counterparts match their hashes. Hosted audit imported and checked
out the actual exported bundle, compared full file hashes against build inventory,
validated permissions/identity/runtime metadata and compared packaged provenance.
This is verified hosted audit evidence, not merely a successful build step.

**Additional local re-audit limitation:** after correcting an invocation's missing
output directory, the local OSTree import failed with `open(O_TMPFILE): Read-only
file system`. That optional local repetition is BLOCKED, not PASS; its original
failure records are retained. Local inventory review is not represented as hashing
locally re-extracted files. This does not change the successful hosted export audit.
No native application launch/portal validation was performed by this package audit.

Evidence: `evidence/p5a/hosted-provisioning-2026-10-31/` (run/jobs, prepare/build/audit,
package metadata/inventory, JUnit, ZIP digest checks, local limitation and manifest).
The successful corrected sequence establishes the hosted repair. The historical
fifth-run exact failing SHA remains unproven and is not reconstructed from this run.

Production code, accepted lifecycle guard, locks, GPG and sandbox/workflow permissions
remain unchanged. One authorized commit was created; owner completed its push after
local HTTPS authentication failed. No additional commit, push, workflow rerun/dispatch,
GitHub Release, signing, deployment, main merge or P5B/P5C occurred during that hosted review. These hosted-result
updates are included in the authorized documentation-only closeout. The artifact is a verification-only unsigned CI upload, not a
published release. **All required hosted P5A gates PASS; P5A formally accepted.**

## Historical local provisioning correction — pre-hosted checkpoint

The authorized 31 October correction is locally verified, uncommitted and unpushed.
It does not change the hosted FAIL above. See `P5A_PROVISIONING_CORRECTION.md` and
`evidence/p5a/provisioning-correction-2026-10-31/` for source hashes, exact commands,
initial failures, final clean-checkout logs, upstream metadata and security review.

Install all dependencies first; pin all three approved commits using `--no-deps`
only during pin enforcement; verify every final SHA, then retain the production
builder's independent architecture/ref check. No provisioning mutations follow
verification. The unchanged builder checks again before assembly and before export.
Structured failures identify stage, operation, ref, expected/actual SHA (or null),
exception type/message and outcome; successful prepare evidence lists all ref checks.
No retry or floating fallback was added. No production code or workflow changed.

Clean checkout at `6743d1d` plus only the two corrected CI source files:
**8 provisioning regressions PASS; 31 total CI contracts PASS; 45 production
packaging/lifecycle-harness tests PASS; Ruff PASS.** Production frontend assets were
built in that checkout as a packaging prerequisite. No browser rerun was necessary.
An initial absent-dist failure and tmpfs free-space failures are retained, followed
by passing runs after satisfying prerequisites; no assertions or gates were weakened.

Real isolated Flatpak remote-add and metadata reads for all three exact commits
succeeded. Their declared Platform/SDK dependencies agree with the P4 lock names,
architecture and 6.11 branch. GPG verification is true. A real isolated Platform
install failed with `open(O_TMPFILE): Read-only file system`; user-namespace creation
also fails with `uid_map: Operation not permitted`. End-to-end local deployment,
production build and exported audit are **NOT VERIFIED**. Metadata agreement does
not establish binary compatibility. No lock incompatibility was demonstrated.

Confirmed source defect: install/pin interleaving permits later dependency resolution
to undo an earlier pin. Historical run 41179709348 records the later Platform update,
but omitted its final SHA and exact exception. That uncertainty remains preserved.
**Recommendation: authorize one P5A-only commit/push for hosted verification.**
No commit, push, dispatch, rerun, release, signing, deployment or P5B/P5C occurred.

## A. Historical fifth hosted result — application tests passed; provisioning failed

**P5A remains FAIL / NOT ACCEPTED.** Actual run **41179709348**, attempt 1,
was push-triggered for `6743d1d5c76f2db87c2debb6f687a6e57a6826b6`. The owner push
succeeded despite interruption before Git's final confirmation; read-only remote
verification confirms this exact commit and branch.

Workflow validation **23 PASS**; backend/security **559 tests + 31 subtests PASS**;
frontend lint/unit/TypeScript/build **273 units PASS**; browsers **20/20 PASS**,
including all five lifecycle cases, the corrected image-selection test and its new
regression. Hosted selection journals confirm paragraph readiness in both image
iterations. The accepted SQLite boundary remains unchanged.

The Flatpak job failed in **prepare**, before any production build: `ValueError`
after 108.078 s. Logs show a later BaseApp install updating Platform after Platform
had already been pinned. Source review and a read-only simulation demonstrate the
provisioner's sensitivity to such dependency updates. Pin verification is the
supported cause, but the diagnostic omitted the exception message, mismatched ref
and actual final SHA; those missing values are not inferred as confirmed evidence.

The required gate FAILS. Production build, exported audit and validated unsigned
package upload are NOT EXECUTED; no production checksum/provenance exists. All
three diagnostic archives were downloaded and their SHA-256 independently matched
GitHub. They are diagnostics, not a validated production package.

Evidence: `evidence/p5a/hosted-image-selection-2026-10-31/`, including run/job records,
prepare.json, provisioning log, selection/transaction journals and control-flow
analysis. No extra commit, push, rerun/dispatch or implementation change occurred.
Recommendation: keep P5A unaccepted and authorize a focused provisioning correction
that preserves final locked refs/GPG verification and exposes safe mismatch details.

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

## O. Historical local lifecycle correction — insufficient in third hosted run

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

## P. Historical local recommendation — superseded by third hosted result

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

## Authorized lifecycle commit / initial push blocker — subsequently resolved by owner

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

## Q. Third hosted run — actual jobs, diagnostics and recommendation

Run 41172242175, attempt 1, source `129700175cf4716446647572979771d27422fc3f`.
Created **14:21:03 KST**, completed **14:24:25 KST**, 202 s including startup/queue.
Ubuntu 24.04.5 x86_64, image 20261025.353.1, runner 2.338.2; CPython 3.12.15.
Logged repository token: Contents read, Metadata read.

| Job | Result | Duration |
| --- | --- | ---: |
| Workflow validation | SUCCESS | 6 s |
| Backend and security | SUCCESS | 92 s |
| Frontend and browser | FAILURE | 186 s |
| CI required | FAILURE | 2 s |
| Production Flatpak and bundle audit | SKIPPED | 0 s |

Backend pytest: 550 PASS, 31 subtests PASS, two warnings, 44.86 s. All original
missing-assets failures pass in this run's JUnit. Workflow contracts: 23 PASS,
0.191 s. Frontend wrapper: 140.097 s (lint 3.050, units 13.975, build 3.879,
Chromium 119.193 s); 273 units, 16 browser passes, one browser failure. Exact
backend wrapper timings remain in this run's backend.json.

| Diagnostic artifact | ID | Bytes | Independently verified SHA-256 |
| --- | ---: | ---: | --- |
| Backend | 13031313767 | 10,471 | `e35e0cc4ba2b0e87412f3437e8f833ae12f566ac974dbb9e8c4bd1be1bd2a86b` |
| Frontend | 13032025578 | 6,865,466 | `c7ca73e61843fe0c22b2410436250ef24d28a9147ae5af5bce2e2defc88cf50b` |

Trace timing: context interception set at monotonic 6047.582 ms; recovery page
created at 6802.323 ms, so the route preceded startup. Old page close requested
at **05:22:24.640895 UTC**; canonical updated_at is **05:22:24.650597 UTC**
(9.702 ms later, approximately; clock mapping is diagnostic correlation).
The draft was based on revision 3; restart GET returns revision 4 with both title
and rich unconfirmed content. The gap is an unexpected real write outside recorded
browser interception, not merely a slow Saved indicator or a harmless stale UI.
The earlier-interception fix is therefore insufficient.

**Recommendation: FAIL / NOT READY FOR ACCEPTANCE.** A future authorized investigation
needs server-side request/revision correlation and a verified effective fault boundary
for teardown writes. Do not weaken conflict handling, ignore the changed canonical
note, suppress the test, add arbitrary delays or automatically rerun it. No code
changes or additional hosted execution were performed during this monitoring turn.

The owner resolved the previous authentication blocker by pushing the exact authorized
commit. This run does not authorize another commit/push/dispatch. Local report/evidence
updates are uncommitted and unpushed. Production Flatpak build/audit/upload and checksum
remain NOT VERIFIED, with no package to independently inspect. Historical P4 native
limits remain separate. Stop after reporting; no P5B/P5C or publication.

## R. Focused investigation checkpoint

The previous hosted failure and superseded late-routing explanation are preserved in
section Q and historical evidence. New implementation changes are confined to
`ci/lifecycle_harness.py`, `backend/tests/test_lifecycle_harness.py` and
`frontend/e2e/lifecycle.spec.ts`; documentation includes the investigation report,
owner checks and structured assessment. No production source or workflow file changed.

All local verification results, including the disk-space failure and corrected run,
are under `evidence/p5a/lifecycle-causality-2026-10-31/`. SQL boundary scope is note
mutations; it is not a general network outage simulation. The actual hosted bypass
and operation identity remain unresolved, while controlled local visibility persistence
is fully correlated. No new commit, push, rerun, publication, P5B or P5C occurred.
Stop for owner review of findings and proposed test-only correction.


## S. Authorized final source and packaging review

The owner approved the fixture-only SQLite boundary and one commit/push. Final review
added a pre-mutation refusal of any existing unmarked database in the fixture launcher.
A ninth regression verifies a synthetic existing workspace remains byte-for-byte unchanged.
No production source, permissions, workflow, API security or persistence controls changed.

Clean-checkout revalidation after this hardening: **559 backend tests + 31 subtests**,
**273 frontend units + 19 browser tests**, and **15 focused repetitions** PASS, with no
retries. Workflow contract validation and all **23 CI contract tests** PASS.
The previous 558-test evidence remains unchanged as a historical candidate record; final
candidate source hashes/results are in `evidence/p5a/lifecycle-final-review-2026-10-31/`.
Synthetic trace traffic is loopback-only; credential-pattern and sensitive-header review
found no secrets. The harness and fixture schema are excluded from production staging,
and migration rejects guarded fixtures. Exact historical escaped request remains unknown.

P5A remains **FAIL / NOT ACCEPTED**, pending the authorized hosted build/audit/upload
and required gate. One commit/push is authorized; no rerun/dispatch or further push is permitted.

## T. Authorized commit and Git HTTPS blocker

Created exactly one authorized P5A commit: `047a99b1473304cc73518dff6427bf7937c542a2`. Reviewed all 63 staged files;
no production application/security/permission/workflow changes or sensitive data.
Original raw diagnostic whitespace is preserved; authored source/docs checks pass.
One push attempt exited 128: Git HTTPS credentials are unavailable in this terminal.
No remote update or new workflow was triggered by that attempt. Required hosted
build/audit/upload/checksum/provenance checks for this commit are NOT EXECUTED.
P5A remains FAIL / NOT ACCEPTED; owner must complete the already-authorized push
from the authenticated Ubuntu terminal. No additional commit or push was performed.
Evidence: `evidence/p5a/lifecycle-final-review-2026-10-31/push-status.json`.


## U. Fourth hosted run — actual results and acceptance decision

[Run 41176826666](https://github.com/74Cerillion/CyrNava/actions/runs/41176826666)
verified source `047a99b1473304cc73518dff6427bf7937c542a2`, push event, attempt 1.
Workflow: PASS (23 contracts). Backend/security: PASS (559 tests, 31 subtests,
2 warnings, 47.14 s). Frontend lint/unit/TypeScript/build: PASS (273 units).
Browsers: 18 PASS / 1 FAIL; all five lifecycle checks PASS. Final required: FAIL.
Production Flatpak and bundle audit: SKIPPED because frontend job failed. No new
production bundle, checksum or provenance exists to verify; diagnostics are not
misrepresented as a production artifact. Both diagnostic archive digests match GitHub.

The failed test is Phase 1 formatting/clipboard/CRUD/keyboard/documentation at
`frontend/e2e/workspace.spec.ts:604`, failure at line 656, second image-loop iteration.
The first image chooser selected JPEG successfully. The next slash command appears
as literal `/image` inside the existing code block in screenshot and error context;
there is no Upload image button. Both the click and chooser wait timed out at 10 s.
This is an observed editor-command/focus precondition failure. The cause of that
selection transition remains unproven without focused reproduction. Neither a
chooser implementation defect nor a production lifecycle defect is inferred.
No test, timeout, production source or security safeguard was changed during review.

New correlated hosted evidence: the no-browser-routing recovery case received a
close-intent PATCH while hidden, 16.850991 ms after the driver's monotonic marker.
Expected revision was 3; SQLite UPDATE was aborted, transaction rolled back, and
FastAPI returned 503. No commit-complete event occurred for that operation. The
canonical no-write/restart/recovery assertions all passed. This confirms actual
teardown fault enforcement in this run while retaining historical uncertainty.

**Recommendation: FAIL / NOT ACCEPTED.** Preserve the successful lifecycle
correction and investigate the separate image-command/focus assumption under
new authorization. No repeat push, rerun or dispatch was performed. All results
and source/run identity are recorded in the current evidence directory's
`final-result.json`, `artifact-verification.json` and `manifest.json`.


## V. Image-insertion test correction — local verification checkpoint

Confirmed local reproduction shows DOM paragraph position 254 while ProseMirror
selects codeBlock position 330 immediately before Enter in the second image loop.
The following slash is received in codeBlock at position 331. This is a test
selection synchronization defect, not evidence of native chooser failure.

Only implementation/test changes: `frontend/e2e/editorSelection.ts` (new read-only
diagnostics/assertions) and `frontend/e2e/workspace.spec.ts` (selection/suggestion/
upload preconditions, original-rich-text preservation and one code-to-image
regression). A subsequent viewport assertion now waits for the closing hover menu
to unmount; its original width bound is preserved. No production source changed.

Final isolated clean-checkout results: 10 focused passes (five per case), 273 units,
20 browser tests, lint and TypeScript/build PASS; targeted accepted harness suite
9 PASS. Production asset hashes are identical across all 33 files. The SQLite
guard and its tests/browser cases remain byte-identical to the accepted commit.
All historical/diagnostic failures and limitations are preserved. Latest actual
hosted run remains FAIL. Stop for one P5A-only commit/push authorization.

Final cleanup review: diagnostic writes use `try/finally`, so a write failure cannot
bypass owned backend shutdown. The exact final source passed another 10/10 focused
executions and the full 273-unit / 20-browser suite, with no retries or skips.


## W. Image-selection correction — owner commit/push authorization

The owner authorized exactly one P5A-only commit and push to
`origin/desktop/p2-production-integration`. Final source/evidence review verifies
that production source, permissions and the accepted lifecycle guard are unchanged.
Local clean-checkout results remain 10 focused, 273 units, 20 browsers and 9 targeted
backend passes. The latest actual hosted run remains 41176826666 FAIL. No rerun,
dispatch, release, signing, deployment, main merge or P5B/P5C is authorized.


## X. Authorized image-selection commit — Git HTTPS push blocker

Created exactly one authorized P5A commit: `6743d1d5c76f2db87c2debb6f687a6e57a6826b6`. All 86 staged files
and 608 text/trace entries passed scope and credential review; traces are synthetic
loopback only. Production source, permissions, workflow and lifecycle guard remain
unchanged. Exactly one push attempt exited 128 because Git HTTPS credentials are
unavailable in this terminal. A read-only `git ls-remote` confirms the branch still
points to `047a99b1473304cc73518dff6427bf7937c542a2`; no remote update occurred.
No new hosted run or production package checks exist for this commit. P5A remains
FAIL / NOT ACCEPTED. The owner must execute the recorded exact push command in
the authenticated Ubuntu terminal; then monitor the automatically triggered CI.
No additional commit, push, rerun or dispatch was performed.
Evidence: `evidence/p5a/image-selection-commit-review-2026-10-31/push-status.json`.


## Y. Fifth hosted verification — actual acceptance gates

[Run 41179709348](https://github.com/74Cerillion/CyrNava/actions/runs/41179709348),
commit `6743d1d5c76f2db87c2debb6f687a6e57a6826b6`, push event, attempt 1.
The owner completed the already-authorized push; no agent push was repeated.

| Gate | Actual result |
| --- | --- |
| Workflow validation | PASS; 23 contracts |
| Backend/security | PASS; 559 tests + 31 subtests, 2 warnings, 47.31 s |
| Frontend units/lint/TypeScript/build | PASS; 273 units |
| Browser integration | PASS; 20, zero failure/skip/retry |
| Accepted lifecycle cases | PASS; all 5 |
| Image-selection correction/regression | PASS |
| Flatpak runtime provisioning | FAIL; ValueError, 108.078 s |
| Production Flatpak build | NOT EXECUTED |
| Exported bundle audit | NOT EXECUTED |
| Validated unsigned package upload | NOT EXECUTED |
| Production package SHA/provenance | UNAVAILABLE; no package |
| CI required | FAIL |

Provisioning sequence: Platform install 07:17:21Z; Platform pin update 07:17:41Z;
SDK install 07:17:54Z; SDK pin update 07:18:24Z; later Platform update 07:18:51Z
during BaseApp installation; BaseApp installation 07:18:58Z; final BaseApp update
reports Nothing to do; prepare raises ValueError at 07:19:08Z. Install/update
commands did not report nonzero exit. The current prepare function installs/pins
refs one at a time then calls the production builder's fail-closed verify_refs.
The runner is x86_64; the relevant source failure path is a pinned-ref mismatch.
However, the wrapper records only generic ValueError and suppresses that path's
exception text. Exact failing ref and final SHA cannot be independently recovered
from this run. A read-only controlled simulation of a dependent BaseApp install
updating Platform reproduces the mismatch; it does not prove the missing hosted
values. Confirmed observations and supported explanation remain distinguished.

No package exists, so the independent bundle inspection was prepared but **not
executed**. All three diagnostic ZIPs (backend, frontend, prepare) were downloaded
and their sizes/digests independently verified against GitHub metadata; no artifact
checksum is misrepresented as a production package checksum. Historical failures,
local correction evidence and hosted lifecycle verification remain preserved.

Recommended next correction: arrange provisioning so dependent installation cannot
undo the final locked commits; verify all refs only after final pin enforcement;
record safe expected/actual ref/commit mismatch details. Retain lock values, GPG
verification and all fail-closed gates. No code change, weakening, commit, push,
rerun, dispatch, production release/signing/deployment, main merge or P5B/P5C occurred
in this hosted review. **P5A recommendation: FAIL / NOT ACCEPTED.**


## Historical provisioning push attempt — authentication blocked

Created one reviewed P5A-only commit `1ee2077b283b8e5dfc2162119dd439ed3baeb109`. The single authorized
push exited 128: Git HTTPS credentials are unavailable in this terminal. No remote
update or new hosted verification resulted from this attempt. Owner must complete
the same authorized push from an authenticated Ubuntu terminal. No retry, second
commit, workflow dispatch/rerun or P5B/P5C occurred. P5A remains FAIL / NOT ACCEPTED.
Evidence: `evidence/p5a/provisioning-commit-review-2026-10-31/push-status.json`.
