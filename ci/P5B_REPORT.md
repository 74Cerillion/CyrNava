# P5B report — secure release preparation and disposable staging

## Formal owner acceptance — 1 November 2026

**P5B — ACCEPTED / COMPLETE.** The owner explicitly accepted Secure Release
Preparation and Disposable Staging after reviewing the final technical assessment
and independently verifying the hosted execution. All required P5B gates passed.

| Accepted identity | Immutable record |
| --- | --- |
| Release-tooling commit | `3ea472efcd6c3338debe16161de601286a5f177d` |
| Hosted staging | [41265875118](https://github.com/74Cerillion/CyrNava/actions/runs/41265875118), attempt 1, SUCCESS |
| Staging workflow | 403136895 — `.github/workflows/release.yml` |
| Application source | `1ee2077b283b8e5dfc2162119dd439ed3baeb109` |
| Accepted P5A CI | 41181510439, attempt 1 — workflow 402398273 |
| Tooling ordinary CI | 41264318875 — SUCCESS |
| Integration branch | `desktop/p2-production-integration` |

The pinned artifact identity, hashes, workflow definitions, auditor hashes and
security requirements are preserved. The owner decision is recorded separately in
`evidence/p5b/owner-acceptance-2026-11-01/acceptance.json`. Actual successful
execution evidence remains in `evidence/p5b/hosted-staging-41265875118/` alongside
historical failed runs 41256746729 and 41261468749. Original evidence files and
manifests are unchanged; their pre-acceptance PENDING fields describe the earlier
technical-review checkpoint and are superseded by the separate owner decision.

The proposed final documentation-only commit is prepared for review in
`P5B_CLOSEOUT_REVIEW.md`. No commit or push is authorized or performed for this
closeout. No integration merge into main, permanent production keys, paid hosting,
application publication or production deployment is authorized.

**Next milestone: P5C — Integrated Release Pipeline Verification.** P5C and P6
implementation have not begun and require separate owner authorization. P5B is
complete; administrative documentation synchronization does not reopen its gates.


## Accepted hosted staging evidence — 1 November 2026

**Technical result: PASS. Formal owner decision: ACCEPTED / COMPLETE.**
The owner accepted this evidence on 1 November 2026. Acceptance does not authorize
production release, keys, hosting, publication or P5C/P6.

The separately authorized third execution was submitted exactly once after all
preflight checks passed. Actual [run 41265875118](https://github.com/74Cerillion/CyrNava/actions/runs/41265875118),
workflow **403136895**, attempt **1**, completed **SUCCESS**. Owner and triggering
actor were `74Cerillion`, repository ID **1427661036**, event `workflow_dispatch`,
exact branch `desktop/p2-production-integration`, immutable tooling
**3ea472efcd6c3338debe16161de601286a5f177d**. The two previous failed runs remain
preserved and were not rerun. There were no additional commits or pushes.

### Preflight and actual hosted gate evidence

Remote integration/tooling/tree and exact workflow bytes matched the approved
source. Main remained `1e62cd5` with byte-identical inert registration; default
branch remained main. The environment still allowed exactly the integration
branch, zero tags, no required reviewers or additional approval protections, zero
secrets and zero variables. Single-maintainer owner authorization remains the
approval model; independent GitHub deployment approval is not claimed.
The manual-only workflow retained read-only contents/actions, immutable action
pins, credential-free full-history staging checkout and independent hash-locked
Python setup. Accepted P5A artifact availability, digest and live CI eligibility
were checked before dispatch. Ordinary CI **41264318875** remained successful.

| Required gate | Actual result and basis |
| --- | --- |
| Execution identity and immutable workflow contract | PASS — actual run metadata, downloaded release definition and exact policy checks |
| Eligibility job 124728452896 | PASS — live approved P5A source, CI jobs, run and artifact |
| Hash-locked dependencies in both jobs | PASS — both actual logs show PyYAML 6.0.3 installed from unchanged locked requirements |
| Full history and exact accepted source before key generation | PASS — hosted log shows fetch-depth 0; reviewed immutable source-preparation and exact detached-SHA check must complete before key creation; source-bound payload auditor completed |
| Approved artifact download/hash/candidate/exported-payload audit | PASS — candidate and signed_repository steps complete; accepted auditor independently imports and checks the actual pinned exported bundle |
| Disposable key and signed repository generation | PASS — signed_repository result, actual fingerprint, signed summary/commit and release seal |
| Signed summary and commit verification | PASS — clean OSTree verifying clients require both GPG checks, untrusted pull and fsck; verified refs are recorded |
| Wrong signing key rejected | PASS — wrong_repository_key_rejected |
| Tampered summary rejected | PASS — tampered_repository_rejected |
| Missing required commit object rejected | PASS — missing_required_object_rejected |
| Unexpected ref rejected | PASS — unexpected_ref_rejected |
| Native Flatpak repository descriptor validation | PASS — native_flatpakrepo_descriptor_remote using disposable Flatpak client |
| Interrupted publication preserves active generation | PASS — interrupted_publication_preserves_previous at intended activation boundary |
| Disposable key cleanup | PASS via fail-closed cleanup protocol described below |
| Safe diagnostic upload and independent hashes/provenance | PASS — one verified ZIP, exactly two JSON members |
| Staging job 124728490631 / final workflow | PASS / SUCCESS |

Pinned release source remains **1ee2077b283b8e5dfc2162119dd439ed3baeb109**,
P5A CI run **41181510439**, artifact **13035607417**, version **0.1.0**, channel
**staging**, authorization reference `P5B-owner-authorized-disposable-staging-only`.
The newer ordinary-CI package was not substituted. The complete result binds:

- Bundle SHA-256: `93957ce5590818e016c5b9e86ed9c6c1d32a684f6c644af44531c316020b26db`.
- OSTree application commit: `da1bf73e3169096522f82249b39f9c9c8546b0317ee6461905bbc6952d6de1ac`.
- Tooling SHA: `3ea472efcd6c3338debe16161de601286a5f177d`.
- Release workflow SHA-256: `5aa32ef85715323490a9375336c245b6dbc1911d480fb4aafc4bc3ba7f8bfb1c`.
- Disposable signing fingerprint: **3495DB69AA4DAA1F867D3D9E19954ED91EAE0E6F**.

The source/auditor guards are established from the approved immutable control
flow plus successful hosted records; the hosted source-checkout fix is now
verified. This does not retroactively identify the exact missing Git subprocess
in the earlier redacted failure. Both historical failures remain intact.

### Metrics, isolation and cleanup

| Measurement | Actual hosted result |
| --- | ---: |
| Repository bytes | 301,341,805 |
| Repository files | 5,554 |
| Signed metadata bytes | 2,016 |
| Static delta bytes | 0 — disabled |
| Repository generation time | 118.335 seconds |
| Signing and summary time | 0.368 seconds |
| Total staging script time | 176.678 seconds |

The signed repository was activated only in the disposable runner-local store.
Result publication target is `LOCAL STAGING ONLY`, release publication result
`NOT PUBLISHED`; no public endpoint or GitHub Release exists from this execution.
Measured size/file count corroborate the earlier native rehearsal and the
previously endorsed future R2-compatible object-storage direction. No hosting
configuration, purchase or production signing decision was executed.

Cleanup verification uses the immutable fail-closed `stage.py` protocol: the
positive and wrong-key tests demonstrate that both disposable key homes were
created; the `finally` block stops their GPG agents and removes both homes before
persisting/printing the final result. Any shutdown/removal failure changes status
to FAIL and records `cleanup_warning`. Actual result is complete PASS with no
cleanup/evidence warning, and the staging job exits successfully. This verifies
completion through that guarded protocol. No separate post-run runner-filesystem
probe is claimed. No private key material was uploaded or preserved locally.

### Independently verified diagnostic artifact

Artifact **13067216650**, name
`p5b-staging-diagnostics-3ea472efcd6c3338debe16161de601286a5f177d-1`,
**2,025 bytes**, ZIP SHA-256:
`1fff9603478b7e6856c2e9e4a901c493ef0d6d81dee2b377ee656cb52b8fe575`.
Downloaded bytes match GitHub metadata and the independent upload-log digest.
Artifact metadata binds to the exact run, source/tooling SHA and repository.
The ZIP contains exactly:

- `result.json`: `fb62775a08533e345ed1a1a905534a2a2d1e6edcec1752d0cf3f1350cbb3eec7`.
- `eligibility.json`: `b0601e26b6aa45db86c24eca906dd7159ed82842c37d647adc2f8a4c018936fa`.

There are no keys, credentials, repository trees or application packages in the
diagnostic upload. Independent verification covers actual hosted evidence,
immutable workflow/code guards, logs, downloaded byte hashes and release/input
provenance. It does not claim a second local signing rehearsal; private repository
and key directories were intentionally not uploaded for local inspection.

Preflight/dispatch evidence: `evidence/p5b/third-staging-preflight-2026-11-01/`.
Actual run/jobs/results, safe excerpts, artifact hashes and gate assessment:
`evidence/p5b/hosted-staging-41265875118/`. Raw diagnostic ZIP remains ignored
under `ci-output/p5b-hosted-staging-41265875118/`. Post-run readback confirms
unchanged main/integration/environment and exactly three staging executions,
each attempt 1: the two preserved historical failures and this single success.

All required technical gates are verified and the owner has formally accepted P5B.
**Final phase classification: ACCEPTED / COMPLETE.** Documentation/evidence
closeout changes remain local and uncommitted pending separate authorization.
No extra dispatch/retry/rerun, commit/push, configuration change, production key,
production credentials, public release/deployment, hosting or P5C/P6 work occurred.
Earlier sections below are historical checkpoints, not current acceptance status
or renewed execution authority.


## Historical hosted ordinary CI — source-checkout correction 3ea472e: PASS

**1 November 2026: ordinary CI PASS. P5B remains CONDITIONAL / NOT ACCEPTED.**
The single authorized correction commit
`3ea472efcd6c3338debe16161de601286a5f177d`, parent `d32ae20`, was created
and pushed once by normal fast-forward. All 77 staged P5B implementation/test,
report and text-evidence paths were reviewed; five implementation hashes match the
clean-checkout verification. No credentials, keys, personal workspace data or
unnecessary binary artifacts were included. Remote commit/tree/parent exactly match
local Git objects. No additional commit/push is authorized or performed.

Actual [CI run 41264318875](https://github.com/74Cerillion/CyrNava/actions/runs/41264318875),
workflow **402398273**, attempt **1**, push event, exact integration branch and
immutable source **3ea472e**, completed **SUCCESS**.

| Hosted job | Actual verified result |
| --- | --- |
| Workflow validation — 124723829833 | PASS — 31 workflow contracts |
| Backend/security — 124723867466 | PASS — 640 tests + 175 subtests; all nine new source-checkout cases verified in downloaded JUnit, zero failures/errors/skips |
| Frontend/browser — 124723867360 | PASS — lint, 273 unit tests, TypeScript/production build, all 21 browser tests including five lifecycle cases; zero browser failures/errors/skips |
| Production Flatpak/exported audit — 124724728539 | PASS — all three installed runtime commits match locks; production build; actual exported-bundle import/checkout/payload audit; validated unsigned upload |
| CI required — 124726555778 | PASS — all four upstream jobs successful |

### Independent downloaded artifact checks and provenance

Every downloaded ZIP size and SHA-256 matches GitHub artifact metadata; each
artifact binds to run 41264318875, attempt 1, repository 1427661036 and source
3ea472e. Upload-log package/diagnostic digests agree independently.

| Artifact | Bytes | ZIP SHA-256 |
| --- | ---: | --- |
| Backend diagnostics 13066991229 | 12,468 | `190223319645e141a8ac67222a301987ee7b97603f8bbbca1498c91d19d566e5` |
| Frontend diagnostics 13066533041 | 4,894,804 | `a0ffef74dbbd889c62f63da180f8e693abbf3905b29500e0492a7aed07a5bcef` |
| Flatpak diagnostics 13066274876 | 2,041 | `391360028ef7d56b34ae588a0464345a57044941c5e806adb1b9e58efbf87519` |
| Validated unsigned package 13066564231 | 210,234,708 | `21ecb322d00fe7c2fabda3f136cb1b80f971b82620c9ba4d856fca9f44208ad6` |

Bundle **209,186,248 bytes**, SHA-256:
`c9486534fe1953b6029599417682a4966808bfdb55ff9fae476b06fbb83313a4`.
OSTree commit:
`8b40081613e33bb8d8820808de9e058b2aafba16be23cf77b8d8bf6733638586`.
Downloaded bytes agree with SHA256SUMS, result, provenance and exported audit.
Source SHA, run/attempt, app/version, runtime locks, package-tool hashes and frontend
lock/package hashes agree. Inventory has **5,320 unique safe paths**, including
242 declared relative symlinks, and **980,984,007 logical bytes**. No release test
harness is packaged. Inventory checksum:
`c0a4e9c0d4fa09792d66a750b0bd2a1b7f6c9ae8a6a17851751f18abd80833ec`.

This is independent downloaded-byte/metadata verification against actual hosted
exported-package audit evidence, not another local native import, renderer/portal
or signing rehearsal. The initial local CLI package transfer timed out at 120
seconds; the connector's complete artifact reference then downloaded successfully
and matched the pinned GitHub digest. No hosted job was retried or rerun.

Curated run/jobs/JUnit/results, checksum/provenance checks and log excerpts are in
`evidence/p5b/hosted-ci-41264318875/`. Raw ZIPs/images/diagnostics remain ignored in
`ci-output/p5b-hosted-ci-41264318875/`; no private data or temporary download URLs
are included in curated evidence. Historical hosted failures are preserved.

### Remaining owner checkpoint — separate manual staging authorization

Post-CI readback confirms integration at `3ea472e`, main at `1e62cd5`, byte-identical
inert registration and unchanged branch-only `p5b-staging` environment: no tags,
reviewers, additional protections, secrets or variables. Local `p5a-accepted` remains
at `1a28f68`. Exactly two historical manual staging runs remain; neither was rerun.
Production application/security/signing/publication controls are unchanged.

The original accepted P5A artifact **13035607417**, source
**1ee2077b283b8e5dfc2162119dd439ed3baeb109**, CI **41181510439**, remains
available/unexpired with unchanged ZIP digest
`73e6d58a91ff2e57ca7b801b120ca61eceb399202349345508b8fbf6ce4eba6b`.
The new ordinary-CI package is not substituted for this pinned staging input.

Request owner authorization for **ONE NEW manual staging execution** of workflow
**403136895** on `desktop/p2-production-integration` at exact tooling commit
**3ea472efcd6c3338debe16161de601286a5f177d**, preserving source `1ee2077`,
CI run `41181510439`, version `0.1.0`, channel `staging`, and authorization reference
`P5B-owner-authorized-disposable-staging-only`. Perform fresh preflight before any
separately approved dispatch. Do not rerun historical failed staging executions.

P5B acceptance still requires actual hosted signing, repository integrity and
negative tests, native descriptor, interrupted publication, key cleanup and diagnostic
hash/provenance gates to PASS in that separately authorized execution. No staging
execution, permanent key, production credentials, hosting/publication or P5C/P6 work
occurred. These post-CI report/evidence updates remain local and uncommitted.

**Owner-authorized commit/push checkpoint — 1 November 2026.** One P5B-only source-checkout correction commit and normal fast-forward push are now authorized from `d32ae20`. Review and ordinary hosted CI are pending. No manual staging dispatch or rerun is authorized; it requires separate approval after successful CI. Earlier authorization/readiness statements below are historical snapshots.

## Historical local accepted-source checkout correction — 1 November 2026

**P5B remains CONDITIONAL / NOT ACCEPTED. Local correction is ready for owner review.**
No commit, push, workflow dispatch, retry, main/environment modification, application
change, build or native OSTree rehearsal was performed under this authorization.
The previously failed hosted executions and successful ordinary CI remain preserved.

### Confirmed defect and historical limits

A new public-remote clone of the exact approved tooling branch at `d32ae20`, with
`--depth=1`, reproduced the existing sequence using the unmodified release code:
local clone **PASS**, detached checkout of accepted source `1ee2077` **FAIL** with
`Operation failed: git (CalledProcessError)`. `cat-file` confirmed the accepted
ancestor was absent. No shared object directory or alternates were used. Thus
missing history is a confirmed reproducible source-checkout defect. The old hosted
message still does not prove which individual Git subprocess failed in that run;
this local reproduction does not retroactively create missing hosted telemetry.

A second fresh public-remote full-history clone at the same tooling commit,
with only the five reviewed correction files overlaid, successfully prepared a
clean detached source checkout at exactly
`1ee2077b283b8e5dfc2162119dd439ed3baeb109`. Every accepted auditor file hash in
`policy.json` matched. The release-tooling commit was never substituted for the
application source; the accepted auditor, approval list and provenance checks
remain unchanged.

### Narrow correction and security review

| File | Correction |
| --- | --- |
| `.github/workflows/release.yml` | Add `fetch-depth: 0` only to staging's immutable tooling checkout |
| `ci/release/core.py` | Extract exact-SHA detached source preparation; verify it before creating a disposable key; add fixed Git operation names and safe failure categories |
| `ci/release/workflow_policy.py` | Require full staging history while preserving exact immutable ref and disabled credential persistence |
| `ci/release/workflow-contract.json` | Exact reviewed contract adds only staging `fetch-depth: 0` |
| `ci/release/test_source_checkout.py` | Nine new Git/source-boundary, workflow-policy and diagnostic regressions |
| `ci/P5B_REPORT.md`, `ci/P5B_OWNER_CHECKS.md`, `ci/P5B_GITHUB_STAGING_PLAN.md` | Current findings, local evidence and remaining approval gates; historical records preserved |
| `ci/evidence/p5b/source-checkout-correction-2026-11-01/` | Sanitized reproduction, hashes, clean-checkout results and artifact readback |

Full history is the simplest maintainable correction: checkout already supports it,
and no additional authenticated fetch code or remote selection is introduced.
Measured Git object storage was **30,274,546 bytes shallow** versus **30,755,355
bytes full** (480,809 bytes additional in these clones). These are local object
storage measurements, not network-transfer or permanent growth guarantees.
A targeted immutable-commit fetch could reduce history in a much larger future
repository, but adds remote-fetch/error/policy handling for little current benefit.
Neither approach changes the requirement to verify the detached source's exact SHA.

Public Git failures now identify `accepted-source-clone`,
`accepted-source-checkout` or `accepted-source-verify`, with only `exit-N`, `timeout`
or `unavailable`. Labels are allowlisted. Arguments, URLs, stderr, paths and
environment values are never copied into diagnostics. Tests inject credential-like
synthetic strings into command/error/environment fields and prove their exclusion.
A missing source or mismatching revision stops before key generation, payload
audit, signing or public output creation. Existing cleanup and signing logic remains
in effect after source preparation. No new production signing authority is added.
Manual-only staging, read-only permissions, action pins, owner/ref restrictions,
locked dependencies, accepted source/artifact identity and publication controls are
unchanged. Production application code and Flatpak permissions are untouched.

Updated integrity hashes:

- Release workflow: `5aa32ef85715323490a9375336c245b6dbc1911d480fb4aafc4bc3ba7f8bfb1c`
- Exact contract: `c47e12e61786633ebf342778dab85644944b6c11e8c74b9ce00dfe85ace45100`
- CI workflow remains `3f11c9ab58d2f7c8cebca0b153a09ccffae06e314545067ddd6b42f7b8e809f4`
- CI dependency lock remains `2322c771f1efab20a6dfd3ec414de1c5ad934099aae347ceef167fdb4dd5de73`

### Actual local verification

The disposable full clone came directly from GitHub, had no alternates, no frontend
build assets and no backend venv. A newly created Python 3.12 venv installed the
unchanged hash-locked requirements; tests did not rely on the development parser.
The focused Git tests create additional two-commit synthetic repositories, with
independent full and shallow object stores and disposable destinations.

| Check | Result |
| --- | --- |
| Exact old shallow sequence | Expected clone success / detached checkout failure reproduced |
| Corrected full historical source and auditor hashes | PASS — exact clean detached accepted source |
| New focused regressions | PASS — **9 tests** |
| Full release regressions | PASS — **73 tests** (previous 64 + 9) |
| Existing CI security/packaging contracts | PASS — **31 tests** |
| Ruff on all CI Python; changed-Python formatting | PASS |
| actionlint 1.7.7, newly downloaded through unchanged hash-verifying bootstrap | PASS — executable workflows and inert registration |
| Exact release, inert registration and ordinary CI policies | PASS |

Coverage includes missing shallow ancestor, correct full-history detached checkout,
unavailable/invalid SHA rejection, wrong resolved revision blocking all later
operations, missing history blocking key/public output, shallow workflow rejection,
and redacted clone/checkout/verification failure categories. Existing eligibility
regressions also reject unapproved source SHAs. CI contracts used a disposable
`/dev/shm` temporary directory to satisfy their unchanged free-space guard; no
resource checks were weakened and no actual Flatpak build was performed.

Commands from the disposable checkout (Python is the fresh sibling `job` venv):

```bash
../job/bin/python -m pip install --require-hashes --only-binary=:all: -r ci/requirements.lock
../job/bin/python -m unittest discover -s ci/release -p test_source_checkout.py -v
../job/bin/python -m unittest discover -s ci/release -p 'test_*.py' -v
TMPDIR=/dev/shm/cyrnava-p5b-source-tests ../job/bin/python -m unittest discover -s ci -p test_ci.py -v
../job/bin/python ci/release/workflow_policy.py
../job/bin/python ci/release/registration_policy.py
../job/bin/python ci/validate.py
```

Tool results, source hashes and all ten check outcomes are recorded with the
curated evidence; the existing pinned Ruff 0.17.1 executable checked all `ci/`
Python, and freshly hash-verified actionlint checked both workflows plus inert
registration. No full frontend/backend suite was repeated because production code
and application tests are unchanged; all relevant release and CI contracts passed.
Release regressions include existing small disposable GPG unit tests, not the
expensive native OSTree staging rehearsal.

### Artifact availability and next owner checkpoint

A fresh connected GitHub read confirms accepted artifact **13035607417**, run
**41181510439**, source **1ee2077**, remains available and unexpired until
**2026-11-07T07:53:28Z**. Its ZIP digest remains
`73e6d58a91ff2e57ca7b801b120ca61eceb399202349345508b8fbf6ce4eba6b`.
All pinned bundle/input/inventory hashes and accepted auditor hashes remain
unchanged in policy. This is a live metadata/identity readback; the 210 MB artifact
was not downloaded or rebuilt again during this correction. Previously independent
archive verification remains preserved and a future staging run must reverify it.

Ready to request **one P5B-only correction commit and normal fast-forward push**.
That requires explicit owner authorization. Ordinary hosted CI must then pass at
the new immutable tooling commit. A further **separately authorized** manual staging
execution must verify signing, repository integrity/negative tests, descriptor,
interrupted publication, key cleanup and diagnostic hashes/provenance before owner
acceptance. Neither local success nor old ordinary CI establishes those hosted gates.

## Historical second hosted staging assessment — 1 November 2026

**P5B STATUS: FAIL / CONDITIONAL — FURTHER ACTION REQUIRED.**

After the owner's separate second-staging authorization, all pre-dispatch checks
passed. The installed authenticated GitHub CLI submitted exactly **one new**
manual dispatch. Actual [run 41261468749](https://github.com/74Cerillion/CyrNava/actions/runs/41261468749),
workflow **403136895**, attempt **1**, executed as `74Cerillion` on
`desktop/p2-production-integration` at approved tooling
**d32ae20bfcd9ad3e6ccab530c62e2e2eb1918b8e**. Its final conclusion is **failure**.
Historical failed run 41256746729 was not rerun.

Preflight independently checked the exact remote branch/tooling bytes and
workflow contract; unchanged inert main registration at `1e62cd5`; unchanged
exact-branch environment with no tags/reviewers/unexpected protection rules;
authenticated zero secrets and zero variables; the locked parser install in
both jobs; successful ordinary CI 41258927530; and live pinned P5A eligibility.
Accepted artifact 13035607417 was available, unexpired and matched its pinned
digest. Inputs remained source `1ee2077b283b8e5dfc2162119dd439ed3baeb109`, CI run
`41181510439`, version `0.1.0`, channel `staging`, and authorization reference
`P5B-owner-authorized-disposable-staging-only`.

| Required gate | Actual hosted result |
| --- | --- |
| Owner/repository/ref/immutable tooling identity | PASS — actual run metadata and workflow bytes verified |
| Eligibility job 124715440186 | PASS — live accepted source, CI jobs and artifact eligibility |
| Hash-locked setup in both independent jobs | PASS — actual logs show PyYAML 6.0.3 installed in each job; previous dependency defect resolved |
| Approved artifact download/hash/extraction/candidate metadata | PASS — eligibility and candidate steps completed |
| Immutable accepted-source preparation | FAIL — Git subprocess while preparing the audit checkout |
| Independent exported payload audit in this staging job | NOT REACHED |
| Disposable signing-key generation | Reached before the first Git operation per reviewed source order; no fingerprint persisted because the release report did not return |
| Signed repository/signatures/negative tests | NOT REACHED |
| Native descriptor/interrupted-publication checks | NOT REACHED |
| Key cleanup | Guarded finally completed with no cleanup_warning; no dedicated cleanup assertion or independent runner-filesystem probe is available, so no stronger cleanup acceptance claim is made |
| Safe diagnostic upload | PASS — result.json and eligibility.json only |
| Independent diagnostic ZIP hash/provenance | PASS |
| Staging job 124715482535 / final workflow conclusion | FAIL |

### Exact failure and remaining causality uncertainty

The complete structured result reports stage `signed-repository`, steps
`eligibility: PASS` and `candidate: PASS`, error type `Rejected`, and exactly:

```text
Operation failed: git (CalledProcessError)
```

Elapsed staging-script time was **4.769 seconds**. `core.generate_repository`
creates its disposable key, then clones the local tooling checkout and attempts
to check out the older immutable accepted P5A source before invoking the payload
auditor. The hosted checkout log confirms **fetch-depth 1** and a fetch of only
the tooling tip. **Likely cause:** that shallow local repository does not provide
the older accepted source commit to the disposable clone. This is an inference
from actual checkout logs and reviewed source, not a claim that stderr proves it.
The safe error intentionally omits argv/stderr and therefore does not distinguish
clone, detached checkout or rev-parse failure. No local reproduction, source fix,
additional hosted run or retry was undertaken under this execution authorization.

The signed repository was not generated, so no signing fingerprint can be
recorded from this failed run. The cleanup guard follows the failed operation,
kills any generated key agent and removes its key home, recording a warning on
failure; the final record contains no such warning. Its absence is protocol
evidence, not a separate remote filesystem observation. No private signing
material was uploaded.

### Preserved evidence and next boundary

Diagnostic artifact **13065456983**, **897 bytes**, ZIP SHA-256:
`18511f21dd83688b7824edd71ee32e22ee1358c9f42658ff605d6a2f40306dcc`.
The downloaded digest matches GitHub metadata and the upload log; metadata binds
the artifact to this run and approved tooling SHA. The two members hash to:

- `result.json`: `7b185f1db1acf2468de231f7712e03c1bf1033ef3b929840edbd6d135f8cd5a5`
- `eligibility.json`: `b0601e26b6aa45db86c24eca906dd7159ed82842c37d647adc2f8a4c018936fa`

Preflight/dispatch evidence is in `evidence/p5b/second-staging-preflight-2026-11-01/`.
Actual run/jobs/results, logs, verified artifact metadata, source-boundary assessment
and hashes are in `evidence/p5b/hosted-staging-41261468749/`. Raw ZIP remains ignored
under `ci-output/p5b-hosted-staging-41261468749/`. Both hosted failures and the
successful ordinary CI/native rehearsal remain preserved.

Post-run readback confirms main and integration remain at `1e62cd5` / `d32ae20`,
environment settings are unchanged, and exactly two manual staging runs exist:
the historical failed run and this single new failed run. No source/workflow
correction, commit, push, rerun, extra dispatch, environment/main modification,
permanent key, public repository/application publication or P5C/P6 work occurred.

Next step requires owner review and separate authorization for a focused
immutable-source checkout investigation/correction. It must preserve the pinned
accepted source/artifact and fail closed; do not substitute the tooling source
or a newer artifact to avoid the failure. No third execution is authorized.

## Historical hosted ordinary CI — correction d32ae20: PASS

**1 November 2026: ordinary CI PASS; P5B remains CONDITIONAL / NOT ACCEPTED.**
The owner-authorized single correction commit
`d32ae20bfcd9ad3e6ccab530c62e2e2eb1918b8e` was created and pushed once by normal
fast-forward from `abbb1b7`. Remote parent, all 77 changed paths and every file
blob independently match the reviewed local commit. Public evidence excludes
unnecessary email fields, private keys, credentials and binary artifacts.

Actual [CI run 41258927530](https://github.com/74Cerillion/CyrNava/actions/runs/41258927530),
workflow **402398273**, attempt **1**, push event, exact branch
`desktop/p2-production-integration` and source `d32ae20`: **all five jobs PASS**.

| Hosted job | Verified result |
| --- | --- |
| Workflow validation — 124707940209 | PASS — all 31 contracts |
| Backend/security — 124707973628 | PASS — 631 tests and 158 subtests; all five new dependency regressions explicitly verified in downloaded JUnit |
| Frontend/browser — 124707973645 | PASS — lint, 273 unit tests, TypeScript/production build and all 21 browser tests, including five lifecycle cases |
| Production Flatpak/exported audit — 124709352764 | PASS — all three actual runtime commits match locks; production build; actual exported-bundle import/checkout/audit; validated unsigned upload |
| CI required — 124711560066 | PASS — all four upstream jobs successful |

### Independent artifact and provenance verification

All four downloaded ZIP lengths and SHA-256 digests match GitHub artifact metadata;
each artifact's run/source/repository binding matches the approved execution.

| Artifact | Bytes | ZIP SHA-256 |
| --- | ---: | --- |
| Backend diagnostics 13064336883 | 12,188 | `1687444fc6e338719307724b50686513630a0ac933df86e17ff7a751d529be68` |
| Frontend diagnostics 13064761229 | 4,892,523 | `9fc4281603a4f051ee6bff11f4e22db2ccf74c496fac780d89bfaf52ec660192` |
| Flatpak diagnostics 13064517200 | 2,042 | `870537b57910e50652bd7b0114c404354cfb94a8f6ae16015812295d78abcf08` |
| Validated unsigned package 13065086140 | 210,241,548 | `30c784428ad004131647155610124a580ec765ae02fde92891d7f1584e5dcd05` |

The downloaded Flatpak bundle is **209,193,088 bytes**, SHA-256
`3671ad864b1726e2e6bb36b3a4c8fb99a135817cb08976a002e93dc4f6ae03c8`.
OSTree commit is
`34abfa4daf5b174bdb2ef98c1e9bb2b5cb83b15233af4e016eb91fccd1957ee3`.
Its bytes match SHA256SUMS, package/build result and provenance. Actual exported
audit metadata agrees on source, app ID/version, digest/size, commit, run/attempt
and runtime locks. Inventory records **5,320 unique safe payload paths** and
**980,984,007 logical bytes**, with no packaged `ci/release` harness.
The backend result also confirms production frontend assets were initially absent
and built before testing, preserving the prior clean-frontend regression.

This independent review checks downloaded bytes and metadata against the actual
hosted exported-package audit. It does not claim an additional local native import,
renderer/portal run, signed staging repository or production signing attestation.
Raw ZIPs/traces/inventory remain ignored under `ci-output/p5b-hosted-ci-41258927530/`.
Curated run/jobs/results/log excerpts, checksum/provenance checks and explicit
dependency-test verification are in `evidence/p5b/hosted-ci-41258927530/`.

### Remaining owner gate — one new staging authorization

Post-CI readback confirms main is still `1e62cd5`, its inert registration workflow
is byte-identical, and `p5b-staging` has the same exact branch-only configuration.
There is still exactly **one** manual staging run: historical failed attempt
41256746729. No new staging dispatch or rerun occurred. The local acceptance tag
and accepted P5A controls remain unchanged.

Accepted staging artifact **13035607417**, P5A run **41181510439** attempt 1 and
source **1ee2077b283b8e5dfc2162119dd439ed3baeb109**, remains available/unexpired
with pinned digest
`73e6d58a91ff2e57ca7b801b120ca61eceb399202349345508b8fbf6ce4eba6b`.
Live eligibility still PASS. The new ordinary-CI package is **not** substituted.

Request separate owner authorization for **one new manual staging execution** of
workflow **403136895** at exact tooling commit
**d32ae20bfcd9ad3e6ccab530c62e2e2eb1918b8e**, using the unchanged P5A source/run,
version `0.1.0`, channel `staging`, and authorization reference
`P5B-owner-authorized-disposable-staging-only`. Perform fresh preflight before
dispatch; do not rerun the failed attempt or reuse approval for old tooling.

P5B acceptance still requires actual live signing, signature/negative tests,
descriptor/interruption checks, disposable-key cleanup and diagnostic provenance
to pass in that separately authorized run. No permanent key, environment/main
change, public release/deployment or P5C/P6 work occurred. Exactly one commit and
one push were used. These hosted-result documentation/evidence updates remain
local and uncommitted; no additional commit/push is authorized.

## Historical local correction readiness — 1 November 2026

**LOCAL CORRECTION: PASS. P5B: CONDITIONAL / NOT ACCEPTED.** The owner authorized
local implementation/testing after reviewing hosted failure 41256746729, then
approved one P5B-only correction commit and normal fast-forward push after review.
This checkpoint contains that reviewed correction; ordinary hosted CI is pending.
No second staging execution is authorized. Its separate approval must follow
successful ordinary CI on the corrected immutable tooling commit.

### Cause, changes and integrity

The hosted traceback below confirms that the separate staging interpreter lacked
PyYAML during workflow-policy revalidation. The corrected staging run block first
executes exactly
`python -m pip install --require-hashes --only-binary=:all: -r ci/requirements.lock`.
The existing lock still pins **PyYAML 6.0.3 with the same wheel hash**. Dependencies
are installed independently in both Python jobs; no cross-job environment or
artifact dependency is introduced.

| Modified implementation file | Narrow change |
| --- | --- |
| `.github/workflows/release.yml` | Install the existing locked parser before staging; installation failure invokes a failure-only JSON recorder and exits nonzero |
| `ci/release/stage.py` | `--setup-failed` can only report FAIL, before private data/download/key creation; catch ImportError with a fixed redacted message and exception type |
| `ci/release/workflow_policy.py` | Require a locked parser install before release Python commands in every independent job |
| `ci/release/workflow-contract.json` | Update the exact approved run block; all other workflow surfaces unchanged |
| `ci/release/test_dependencies.py` | Five new regressions for per-job setup/order/integrity, real missing-YAML failure, real shell failure propagation and diagnostic redaction |

Workflow SHA-256 changes from
`3b2a08b287380693393ed2c5cffc22bd155f53efd42dc13be4ef351b55812922` to
`8e33dc0be70e24c445bd2b373f2468ad242c1852cd817a774896ede4628468e5`.
Exact contract SHA-256 is now
`53164eb5108ffbb85ae189a1a497b83f4520cd6ae2a882635bc0f012a8e9676e`.
The accepted P5A workflow hash, release source/artifact policy, CI dependency lock,
action pins, runtime/auditor locks and inert registration proposal are unchanged;
no associated trust-policy hash needs changing. Signing/core, eligibility,
preflight, recovery and publication code remain byte-identical. Production
application code, sandbox permissions and security controls are unchanged.

The failure-only recorder uses the existing output containment/new-directory
checks and never overwrites prior evidence. Import exception strings/module names,
subprocess output and environment values are not copied into its structured
error. A missing dependency cannot be treated as PASS or bypass policy validation.
Existing signing-key cleanup/finalization remains intact.

### Clean-checkout verification

A disposable detached checkout of `abbb1b7` received exactly the five candidate
implementation/test files above. It had no frontend/dist, backend venv or reused
generated application assets. Two separately created Python 3.12 venvs, with
system-site packages disabled, independently demonstrated **no YAML before setup**.
Each then installed the unchanged lock, passed pip check, imported version 6.0.3
and successfully ran the actual workflow-policy validator. No shared installed
parser was assumed. Exact tested source hashes match the development candidate.

| Verification | Actual local result |
| --- | --- |
| Pre-install missing-import and redaction tests in the fresh staging venv | PASS — 2 focused tests before installing YAML |
| Full release regressions | PASS — **64 tests**, comprising the previous 59 and 5 new tests |
| Ordinary CI security/packaging contracts | PASS — **31 tests** |
| Ruff check / changed-Python format check | PASS — fresh tooling venv, existing backend-pinned Ruff 0.17.1 |
| actionlint | PASS — both executable workflows and inert proposal; unchanged bootstrap verified the pinned 1.7.7 archive hash |
| Exact release, inert registration and CI policies | PASS |

The real missing-import regression uses a new stdlib-only venv and executes the
actual hosted identity/workflow-import path. Tripwires prove no environment fetch,
CI fetch, package download/extraction, signing or repository processing occurs.
The exact workflow shell blocks are also executed with pip deliberately failing;
both jobs stop, and staging retains a complete redacted FAIL at
`python-dependencies`. This shell test models installation failure; it does not
claim a live GitHub or native signing execution.

Initial CI-contract testing encountered the unchanged 5 GiB guard because the
requested /dev/shm directory did not persist between isolated tool invocations;
Python fell back to the smaller /tmp volume. The final invocation created and
asserted TMPDIR on spacious /dev/shm before running all 31 tests successfully.
No guard/test was weakened, and the initial environmental failure log is retained.

Commands in the clean checkout (each Python path is a separately created venv):

```bash
../job-eligibility/bin/python -m pip install --require-hashes --only-binary=:all: -r ci/requirements.lock
../job-staging/bin/python -m pip install --require-hashes --only-binary=:all: -r ci/requirements.lock
../job-staging/bin/python -m unittest discover -s ci/release -p 'test_*.py' -v
TMPDIR=/dev/shm/cyrnava-p5b-dependency-tests ../job-eligibility/bin/python -m unittest discover -s ci -p test_ci.py -v
../tools/bin/python -m ruff check --config backend/pyproject.toml ci
../tools/actionlint/actionlint .github/workflows/release.yml .github/workflows/ci.yml ci/release/registration-only.yml
../job-staging/bin/python ci/release/workflow_policy.py
../job-staging/bin/python ci/release/registration_policy.py
../job-staging/bin/python ci/validate.py
```

Evidence/logs/source hashes: `evidence/p5b/dependency-correction-2026-11-01/`.
The disposable checkout and venvs are ignored under
`ci-output/p5b-dependency-correction/`. No application rebuild or full native
OSTree rehearsal was needed; the unchanged cryptography/publication regressions
are included in the 64-test release suite. Hosted failure evidence and the
accepted owner-native rehearsal remain preserved.

### Remaining hosted gates and owner action

Live recheck confirms accepted artifact **13035607417** remains available and
unexpired until **2026-11-07T07:53:28Z**, with the same pinned ZIP SHA-256
`73e6d58a91ff2e57ca7b801b120ca61eceb399202349345508b8fbf6ce4eba6b`.
Source/run/jobs/workflow/provenance still pass the existing live eligibility check.
The approved bundle/input/inventory hashes in policy.json have not changed; no
replacement artifact is proposed.

1. Owner authorized one P5B-only correction commit/push, with complete staged review.
2. Verify ordinary CI on that new immutable tooling SHA, including package audit
   and artifact upload. Local PASS does not establish hosted PASS.
3. Obtain **separate authorization** for one new manual staging dispatch at the
   corrected SHA; do not rerun failed attempt 41256746729.
4. Require all live eligibility, signing, signature/negative tests, descriptor,
   interruption, key cleanup and diagnostic-hash/provenance gates to pass before
   recommending P5B acceptance.

Pre-commit public-evidence review omitted unnecessary author/committer email
fields from two preflight API snapshots. Original snapshots are preserved locally
in ignored audit storage; `authorization-c-preflight-2026-11-01/privacy-review.json`
records the derivation/hashes. Historical failure evidence remains unchanged.
The final readback confirmed main, inert registration and environment unchanged.

Only the five source/test files, local reports/checklist/plan and non-sensitive
evidence were changed in this correction. No commit, push, dispatch/rerun,
GitHub environment/main change, production key, public release or P5C/P6 work
was performed.

## Historical hosted assessment — 1 November 2026

**P5B STATUS: FAIL / CONDITIONAL — FURTHER ACTION REQUIRED.**

The owner submitted the single authorized manual dispatch. Actual hosted
[run 41256746729](https://github.com/74Cerillion/CyrNava/actions/runs/41256746729),
workflow **403136895**, attempt **1**, ran on exactly
`abbb1b7a723d0b42dae1fa2b3312cb7667299e96` and
`desktop/p2-production-integration`, initiated/triggered by `74Cerillion`.
The immutable workflow/source readback passed the existing execution validator.
Logs confirm the authorized inputs: source
`1ee2077b283b8e5dfc2162119dd439ed3baeb109`, CI run `41181510439`, version `0.1.0`,
channel `staging`, authorization `P5B-owner-authorized-disposable-staging-only`.
The owner's guarded terminal command completed its authenticated zero-secret/
zero-variable checks before dispatch. Post-run public readback confirms the exact
single branch/no-tag environment restrictions and no additional approval rules.

| Required gate | Actual hosted result |
| --- | --- |
| Owner/manual execution, workflow/ref/tooling identity | PASS |
| Eligibility job 124701415505 | PASS — workflow security contract, live accepted P5A source/run/artifact eligibility, exact branch environment |
| Staging job 124701454407 | FAIL — missing Python dependency during workflow-policy revalidation |
| Downloaded accepted package hash/content audit | NOT REACHED in staging job |
| Disposable key generation / signing fingerprint | NOT REACHED / none |
| Signed repository, signature and negative security tests | NOT REACHED |
| Native descriptor and interrupted-publication tests | NOT REACHED |
| Disposable key cleanup | NOT APPLICABLE — failure before any key generation; no cleanup PASS claimed |
| Safe diagnostic upload | PASS — result.json only |
| Diagnostic ZIP checksum and run/tooling provenance | PASS — independently downloaded and verified |

### Confirmed cause and diagnostic limitation

The eligibility job installs hash-pinned `ci/requirements.lock` (PyYAML 6.0.3).
The separate staging job sets up a fresh Python interpreter but never installs
that lock. Its `stage.py --live` calls `github.check_execution()`, which invokes
`workflow_policy.read_workflow()` and imports `ci/validate.py`. Hosted traceback
at **2026-11-01T00:27:18Z** ends at `import yaml` with
`ModuleNotFoundError: No module named 'yaml'`. This is a staging-job dependency
provisioning defect, not evidence of a signing, sandbox or application failure.
Dependencies installed in the eligibility job were not available on this runner.

The `finally` block preserved a complete FAIL result at stage `eligibility`, empty
steps and 0.007 seconds. `ModuleNotFoundError` is not caught by the current authored
error handler, so the result has no `error`/`error_type`; the retained traceback
establishes the cause. Staging `eligibility.json` was not written. The prior
eligibility job's PASS record remains available in its independently fetched logs.
Do not interpret diagnostic-upload success as completion of the security checks.

Diagnostic artifact **13063163006** is **283 bytes**, ZIP SHA-256
`46f94f80b8f098204c0bca8dce2b6df1d5809539686fdce10687708becbe60e3`.
Its only member is `result.json`, SHA-256
`7e1e1d1f114fbbe110cae2eb068e5995de1bc02e8b74057e02cc1228552bbdf3`.
The ZIP digest matches both GitHub metadata and the upload log. Artifact metadata
binds it to this run and tooling commit. No key homes, private keys, package or
repository tree are included. This is diagnostic provenance, not a production
signing attestation. Evidence: `evidence/p5b/hosted-staging-41256746729/`; raw ZIP
is ignored under `ci-output/p5b-hosted-staging-41256746729/`.

Recommended correction, **not implemented under Authorization C**: install the
existing hash-locked CI requirements independently in the staging job before its
policy revalidation, update the exact workflow contract, and cover missing-dependency
provisioning with a fresh-job regression. Also preserve actionable structured
failure evidence for an import/setup failure. No security check should be removed.
Local correction/testing, any later commit/push and another dispatch require
appropriate further authorization; do not rerun this failed attempt.

Post-run main/integration tips remain `1e62cd5` / `abbb1b7`. Exactly one staging
run exists. Accepted native evidence and successful CI 41207770532 are preserved.
Only local reports/evidence were updated; no workflow, application, signing or
security code was changed. No new commit, push, rerun, dispatch, production key,
public application publication, environment change or P5C/P6 work occurred.

## Historical pre-dispatch assessment — 1 November 2026, Authorization C

**P5B STATUS: CONDITIONAL — FURTHER ACTION REQUIRED.** Authorization C approves
one manual staging run, but **no dispatch has been attempted**. The connector has
no supported workflow-dispatch operation, and the local terminal has no `gh`
installation/authenticated dispatch capability. Owner execution is required;
absence of hosted results is not a failed signing test or a PASS.

Final public preflight independently confirms:

- Integration is exactly `abbb1b7a723d0b42dae1fa2b3312cb7667299e96`.
- Main is `1e62cd5ef4d36d048a505e9e4a7029296edfd3da`, with the approved parent
  `cbf7cccc686080b2b4b07274a9f5a23fec52999f` and only the inert registration
  workflow added. All prior application files/history are preserved; main remains
  the default branch. Registration bytes match the approved proposal SHA-256
  `3a8c4ad86f958dc7d437c5ee4e5ad2ac57d8753cc4429252edc0005bf385c7c5`.
- Registered workflow **403136895** is active at `.github/workflows/release.yml`;
  it currently has **zero runs**. The integration workflow is byte-identical to
  the approved tooling commit and passes the exact manual-only/read-only policy.
- Environment **25906950906**, `p5b-staging`, has only the `branch_policy`
  protection rule, custom restrictions enabled, and exactly the branch
  `desktop/p2-production-integration`, with no tags. No reviewer/wait/custom
  approval rule is present. The owner screenshot shows empty secrets and variables;
  the public API cannot independently prove their counts. The owner dispatch
  command must fail closed unless authenticated counts are both zero.
- The actual accepted P5A run **41181510439**, attempt **1**, all five successful
  jobs, source **1ee2077b283b8e5dfc2162119dd439ed3baeb109**, accepted workflow
  bytes and artifact **13035607417** pass the existing CI-eligibility verifier.
  Artifact metadata is available, unexpired until **2026-11-07T07:53:28Z**, and
  matches pinned ZIP SHA-256
  `73e6d58a91ff2e57ca7b801b120ca61eceb399202349345508b8fbf6ce4eba6b`.
  The actual hosted run must still download/hash/audit the artifact before signing.

Readbacks, exact workflow files, preflight summary and file hashes are preserved in
`evidence/p5b/authorization-c-preflight-2026-11-01/`. An initial repository metadata
GET used a trailing slash and returned 404; the supported connector independently
confirmed the repository/default branch. No write or dispatch accompanied that GET.

Hosted run ID, attempt, disposable fingerprint, signature/negative tests, key
cleanup and diagnostic upload/hash/provenance verification are **NOT EXECUTED**.
They remain the outstanding acceptance gate. No keys, settings changes, additional
commits/pushes, public deployment, release or P5C/P6 work were performed.

The dated sections below preserve the earlier CI and preparation history; their
statements that registration/environment creation were pending describe that
earlier checkpoint, superseded by the A/B readbacks above.

## Historical assessment — 31 October 2026

**31 October 2026 — CONDITIONAL; not accepted.** Required CI run **41207770532** at
**abbb1b7a723d0b42dae1fa2b3312cb7667299e96** passed every gate. Native signed-OSTree,
negative security, descriptor and interrupted-publication evidence remains accepted.
The owner subsequently approved a single-maintainer model; its revised P5B policy
is committed/pushed as `abbb1b7a723d0b42dae1fa2b3312cb7667299e96`; automatic CI
run 41207770532 passed. The actual manual staging workflow has not executed.
Registration on main, environment configuration and hosted dispatch remain separately
gated. None has been performed. These gaps prevent unconditional acceptance.

Manual owner authorization now replaces independent GitHub deployment approval.
No second reviewer or self-review prevention is required or claimed. This concentrates
staging authority in the owner's account; production signing remains owner-controlled,
offline and unavailable to staging. Future R2-compatible hosting remains endorsed
without authorizing credentials, permanent keys, purchases or public deployment.

The implementation history is a9de663 → 3027231 → the reviewed appearance correction
7aaefd0, followed by the owner-authorized single-maintainer commit abbb1b7. The owner
completed its authenticated push; remote and local branch agree at abbb1b7.
Local `p5a-accepted` remains unchanged. After reviewing the local results, the owner
authorized one integration commit/push and its automatic CI verification. Main
modification, GitHub settings, workflow dispatch/rerun, permanent keys, public releases
and P5C/P6 remain outside that authorization.

## Accepted baseline and repository state

- Branch: `desktop/p2-production-integration`; starting worktree clean.
- Original P5B starting HEAD/remote: `1a28f68c5732ccc1275403060e89ff168a846655`.
- This commit-review checkpoint started clean at existing implementation commit
  `a9de66384b4b1ae4e5bb47909df1eba7d50468f0`; read-only remote inspection matches it.
  Preserve that history; the authorized follow-up records endorsements and staging
  architecture, without duplicating/rebasing the existing implementation.
- Local annotated `p5a-accepted` points to `1a28f68`, not the later P5B commit. It remains local;
  read-only `ls-remote` found no matching remote tag. No tag was changed.
- Accepted application build: [P5A run 41181510439](https://github.com/74Cerillion/CyrNava/actions/runs/41181510439),
  source `1ee2077b283b8e5dfc2162119dd439ed3baeb109`, attempt 1.
- Live read-only eligibility verification independently checked all five successful
  required jobs, workflow identity/content, source, artifact ID/digest and expiry.
  See `evidence/p5b/live-eligibility.json` and the existing P5A acceptance evidence.
- Application ID `io.github._74Cerillion.CyrNava`, version `0.1.0`, architecture
  x86_64, stable ref and schema 5 remain unchanged.

The accepted CI workflow, exported-payload auditor, production packaging and locks
remain byte-identical. Application sources and Flatpak permissions were not edited.
P5B implementation/native evidence is already tracked in a9de663. Its source hashes
match the tested candidate. `evidence/p5b/baseline.json` records the original start;
`evidence/p5b/staging-preparation/` records this checkpoint and review. The older
pre-commit evidence remains historical, not a claim about the new repository HEAD.

## Current hosted CI — single-maintainer revision abbb1b7: PASS

[Run 41207770532](https://github.com/74Cerillion/CyrNava/actions/runs/41207770532),
workflow **402398273**, attempt **1**, push event, exact source
`abbb1b7a723d0b42dae1fa2b3312cb7667299e96`: **PASS**.

| Required job/check | Actual hosted result |
| --- | --- |
| Workflow validation (124556264768) | PASS — all 31 contracts |
| Backend/security (124556308627) | PASS — 626 tests and 144 subtests, including new staging identity/environment/registration cases |
| Frontend/browser (124556308499) | PASS — lint, 273 units, TypeScript/build and all 21 browser tests, including five lifecycle and both appearance regressions |
| Production Flatpak/bundle audit (124556969346) | PASS — locked runtime provisioning, production build, actual exported-bundle audit, unsigned upload |
| CI required (124559507714) | PASS — all four upstream jobs successful |

All four artifact ZIP lengths/SHA-256 independently match GitHub: backend
**13045495676**, frontend **13044952845**, Flatpak diagnostics **13045073811** and
validated unsigned package **13045049016**. Package ZIP is **210,247,204 bytes**,
SHA-256 `a85282d65891e18402c7d883f560d0150a2562cb6918e37e45c87ca6608e7c06`.
Flatpak bundle is **209,198,744 bytes**, SHA-256
`7a6df1f204939d91d0a0f46adb83da98ad590cd38ac02eba56b8a9fc4139d219`.
OSTree commit: `135b4d0365e9b164464ec66eb5710edb5393f6c74e012c94e44f97f3b6cff822`.

Downloaded checksum, build result/inputs, provenance and inventory were crosschecked
for exact source, run/attempt, app ID/version, bundle hash/size, runtime locks and
OSTree commit. All **5,320 payload paths** equal the previous successful build's
paths. Hosted exported-payload audit PASS is preserved; no repeat local native
import or renderer/portal verification is claimed. The policy still promotes the
older accepted P5A artifact 13035607417, not this latest CI artifact. That accepted
artifact's live metadata remains unexpired and matches its pinned digest/source.

Evidence is in `evidence/p5b/hosted-ci-41207770532/`: actual run/jobs/results/log
excerpts, all artifact hashes, browser JUnit/focused states, explicit new-policy
test collection verification, package/provenance checks and read-only staging
readiness. Raw ZIPs/logs remain ignored under `ci-output/p5b-hosted-41207770532/`.
Historical failed runs and previous successful run 41205351385 remain preserved.

Remote integration is verified at abbb1b7; main remains
`cbf7cccc686080b2b4b07274a9f5a23fec52999f` and the local acceptance tag is unchanged.
Read-only API still shows zero environments and no release definition on main.
No additional commit/push, rerun/dispatch, main change or settings update occurred.
These report/evidence updates remain local and uncommitted after the authorized push.
**This CI PASS verifies the revised code/tests/package, not actual manual hosted staging.**

## Previous hosted CI — appearance correction 7aaefd0: PASS

[Run 41205351385](https://github.com/74Cerillion/CyrNava/actions/runs/41205351385),
workflow **402398273**, attempt **1**, push event, exact source
`7aaefd0f60a735637ee603ac380587a25b73f6cb`: **PASS**.

| Required job/check | Actual hosted result |
| --- | --- |
| Workflow validation (124549189167) | PASS — 31 contracts |
| Backend/security (124549221042) | PASS — 611 tests and 83 subtests |
| Frontend/browser (124549221121) | PASS — lint, 273 units, TypeScript/build, all 21 browser tests including 5 lifecycle and both appearance regressions |
| Production Flatpak/bundle audit (124550104215) | PASS — locked runtime provisioning, build, exported-package audit and validated unsigned upload |
| CI required (124552493850) | PASS — all four upstream jobs successful |

All four artifact ZIP sizes/SHA-256 were independently verified against GitHub:
backend **13043983920**, frontend **13044028910**, Flatpak diagnostics **13044800454**,
validated package **13044630984**. Package ZIP: **210,238,004 bytes**, SHA-256
`560a05310a80ae0d397d7b34936563ea3f674dd6f72b2bdb2984aa246ab35b51`.
Flatpak bundle: **209,189,544 bytes**, SHA-256
`01e13b55a60100e6573de8bfbfc87f1b16373c4d7b8ca05047e35c4e27263153`.

Downloaded SHA256SUMS, result, build inputs, inventory and provenance were crosschecked
for source/run/attempt/identity/version, exact runtime locks, bundle digest/size and
OSTree commit `049e3ffc86aa1b6060c17db4baf7a5b7bde37e0562f6870a06c3ab62322f6971`.
Actual hosted exported-bundle audit PASS is preserved; no repeat local native import
or renderer/portal test is claimed. The latest package does not replace policy-pinned
P5A artifact 13035607417 used for staging.

Evidence: `evidence/p5b/hosted-ci-41205351385/`, including run/jobs/artifacts,
actual result records/log excerpts, all hashes, browser JUnit and focused empty-caret
state verification. Raw ZIPs/logs remain ignored under `ci-output/p5b-hosted-41205351385/`.
Historical failed runs remain unchanged below and in their original evidence records.
This CI PASS is not protected hosted staging and predates the revised policy below.

## Single-maintainer hosted-staging preparation — locally verified

The owner's explicit later architecture decision supersedes the earlier two-person
approval requirement. P5B now requires manual dispatch by `74Cerillion`, exact
integration repository/ref/workflow identity, matching workflow/check-out SHA and
first attempt. Both preflight and live staging recheck identity and the reviewed
workflow contract. `p5b-staging` has no required reviewers; exact branch-only policy
remains mandatory, with no tags, wildcards, main or pull refs. No independent approval
is claimed. The admin-bypass flag is not treated as an approval safeguard when no
reviewer gate exists; branch and immutable-source checks remain independently enforced.

Changed policy/preflight/environment tests reject wrong actor/ref/repo/workflow,
unapproved source, wrong artifacts and missing staging authorization. The existing
P5A CI definition, action pins, package/lock/auditor code, production application,
CSS, autosave/recovery/SQL guard and real signing/integrity/publication safeguards
are unchanged. The release workflow step label and exact contract now accurately
describe owner dispatch. No production keys or publication credentials are referenced.

`ci/release/registration-only.yml` is the exact inert main-file proposal, stored
outside .github/workflows on integration. It matches all five input definitions,
has contents read only and one literal-false job with only a no-op marker. It has
no checkout, environment, release/signing command or secret. `registration_policy.py`
and `test_registration.py` validate it and optional future run/settings readbacks.
Full YAML, main base SHA, security assessment, owner commands and separate A/B/C
approval steps are in `P5B_GITHUB_STAGING_PLAN.md`.

Local final verification: **59 release/registration/signing tests + 31 existing CI
contracts PASS**, Ruff/actionlint and CI/release/registration security policies PASS.
One-day synthetic GPG unit-test keys were cleaned up; no production/permanent key
or full native OSTree rehearsal was created. The initial CI-contract run encountered
the unchanged 5 GiB space guard in two tests; the rerun used spacious /dev/shm for
small synthetic fixtures, preserving the guard and original failure record.
`evidence/p5b/staging-final-preparation-2026-10-31/` records results, hashes and actual
GitHub readbacks: main cbf7cccc686080b2b4b07274a9f5a23fec52999f, zero environments,
and no release definition on main. The policy was subsequently committed/pushed
as abbb1b7; its current automatic CI result is recorded above. Hosted staging remains unexecuted.

## Hosted continuous-integration result — 3027231

[Run 41197927704](https://github.com/74Cerillion/CyrNava/actions/runs/41197927704),
workflow ID **402398273**, attempt **1**, push event, exact commit
`3027231c390b1814a98a567e5f30afb4ebff0dab`: **FAIL**.
This is ordinary P5A continuous integration, not protected P5B staging execution.

| Required job/check | Hosted result |
| --- | --- |
| Workflow validation | PASS — 31 contracts |
| Backend and security | PASS — 611 tests, 83 subtests; clean frontend-assets prerequisite verified |
| Frontend lint, unit tests, TypeScript/build | PASS — 273 unit tests |
| Browser integration | FAIL — 19 passed, 1 failed; all 5 lifecycle tests passed |
| Production Flatpak build and exported bundle audit | SKIPPED — correctly gated by frontend failure |
| Validated unsigned application artifact upload | NOT EXECUTED; no application package produced |
| Backend/frontend diagnostic uploads | PASS — both downloaded ZIP sizes/SHA-256 independently match GitHub |
| CI required | FAIL — frontend failure and skipped Flatpak job correctly rejected |

The failed test begins at `frontend/e2e/workspace.spec.ts:112`; its assertion at
line **228** expects the last paragraph's CSS `::after` content to contain
`Enter text`. Actual content stayed `none` for the 10,000 ms predicate timeout.
At the initial review this established the failing observation without determining
its cause. That historical record is preserved. The subsequent authorized investigation
established an invalid test precondition; see the separate correction assessment below.

Evidence is in `evidence/p5b/hosted-ci-41197927704/`: run/jobs/artifact metadata,
actual log excerpts, frontend/backend result records, browser JUnit, generated
failure context and summary. The generated Playwright context's instruction text
is diagnostic content, not an owner request to implement a fix. Original diagnostic
ZIPs (including the screenshot/trace) are retained under the ignored
`ci-output/p5b-hosted-41197927704/`; no binaries, signed download URLs or credentials
were copied into the report. Digests and member paths are recorded for recovery
after GitHub's seven-day artifact retention expires. No package checksum/provenance
can be verified for this run because the package job never executed.

The owner's provisional approval of registration-only staging preparation is
recorded; exact main-file YAML and environment settings still require separate
authorization. No main/environment change or staging dispatch occurred.

## Local appearance-test correction — commit/push authorized; hosted result pending

The retained hosted screenshot, trace snapshots, error context and generated CSS
show the last paragraph was empty/editable but lacked BlockNote's selected-empty
paragraph decoration. After Escape and Backspace, an earlier paragraph changed
from `/ bold` to ` bold`; the last paragraph stayed empty and undecorated through
Saved. Its computed placeholder content `none` was correct for that unselected
target. Saved is a persistence assertion, not a caret-placement guarantee.

The old test moved a DOM Range to the editor root's end without establishing the
ProseMirror selection. Three instrumented original runs passed locally but reproduced
that DOM/model mismatch in every helper call. The entire historical failure is not
claimed to reproduce locally, and its exact event-loop interleaving remains unrecorded.
No production application/CSS defect is established.

Only executable change: `frontend/e2e/workspace.spec.ts`. Real click/Control+End
navigation now waits for observable, synchronized paragraph selection and the exact
new empty block before typing. Escape/Backspace/Saved diagnostics record focus,
DOM/model positions and computed styles without note bodies or session credentials.
The original light/dark `Enter text` and contrast assertions remain. A new regression
checks the unselected-empty negative case, reproduces the DOM-only mismatch without
typing from it, and verifies that selecting the intended empty paragraph displays
the real hint while canonical note/revision data remains unchanged.

Final source in a fresh detached checkout at `3027231` passes **20 focused runs**
(10 appearance + 10 regression, zero retries) and the **complete frontend suite**:
lint, **273 unit tests**, TypeScript/production build and **21 browser tests**,
including all **5 lifecycle** tests. No production/backend behavior changed, so
backend tests were not rerun; their hosted **611 tests / 83 subtests PASS** is
preserved. The accepted SQL lifecycle guard, signing code, security controls,
workflow and package payload rules remain unchanged. No keys were generated.

See `P5B_APPEARANCE_CORRECTION.md` for causality, exact modifications and limits;
`evidence/p5b/appearance-correction-2026-10-31/` records candidate hashes,
hosted-trace analysis, baseline/focused state checks and complete-suite results.
Historical hosted evidence remains unchanged in `hosted-ci-41197927704/`.
At the original local-review checkpoint the correction was uncommitted/unpushed.
The owner subsequently authorized commit 7aaefd0 and completed its push; actual hosted
PASS is recorded above. That does not authorize further pushes, reruns or dispatches.

## Architecture and decisions

Use **promotion of the exact accepted P5A artifact**, followed by independent
validation and disposable signing. This avoids a second application build system.
A reviewed allowlist pins source, CI run/attempt, artifact ID, ZIP/bundle hashes,
inventory/input hashes and exported OSTree commit. An arbitrary successful artifact
or manual input cannot replace them.

```text
Owner-approved immutable source + successful P5A run + exact artifact digest
  -> eligibility and bounded extraction
  -> unchanged P5A exported-payload audit against approved detached source
  -> disposable key; signed application/AppStream commits and summary
  -> clean-client signature/integrity validation; signed snapshot inventory
  -> verified complete local generation; atomic active-pointer replacement
  -> native descriptor check and deliberate publication-interruption exercise
```

The P5A auditor's source check is preserved. A child process binds its `GITHUB_SHA`
to the approved application source; the parent retains and records the actual
release-tooling commit/workflow separately. Promotion does not pretend the later
release tooling is the source of the accepted application bundle.

**Hosting recommendation:** provider-neutral static snapshots now; R2-compatible
object storage is proposed for the eventual update remote, GitHub Releases for an
optional bundle/provenance mirror. Pages, Releases, R2 and Netlify are compared in
`P5B_HOSTING_DECISION.md`, with official pricing/limits and the measured 301,341,805-byte,
5,554-file repository. One repository fits Pages; retained snapshots and growth
traffic still favor object storage. The owner endorses R2-compatible architecture;
provider account, permanent endpoint, cost and provisioning approval remain deferred.

**Signing recommendation:** owner-controlled offline production signing, with an
offline recovery/certification primary and expiring signing subkey after a separately
approved ceremony. The owner endorses this custody direction, without authorizing
key generation. `P5B_SIGNING_DESIGN.md` compares protected Actions secrets,
offline signing and managed infrastructure; it covers custody, bootstrap, rotation,
lost keys, compromise, hosting outage and database-compatible recovery.

These decisions do not block identity-independent disposable staging work.
Production custody, cost, endpoint, credentials and publication require separate
owner approval. No production signing path is enabled by a command-line flag.

## Workflow and implementation

| File/group | Responsibility |
| --- | --- |
| `.github/workflows/release.yml` | Manual staging only; read-only contents/actions; eligibility before protected staging; immutable action pins; bounded jobs; safe status-only diagnostic upload |
| `ci/release/policy.json` | Accepted source/artifact/workflow/auditor/lock pins; production disabled |
| `ci/release/core.py` | Eligibility, bounded untrusted extraction, P5A audit orchestration, disposable GPG, native OSTree checks, descriptors, signed inventories and local snapshot publication |
| `ci/release/audit_candidate.py` | Approved-source child binding for the unchanged P5A payload auditor |
| `ci/release/github.py`, `preflight.py` | Read-only GitHub evidence/environment checks; bounded artifact download without forwarding API credentials to the CDN |
| `ci/release/stage.py` | Explicit local/live rehearsal, actual native positive/negative checks, safe result record, metrics and key-home cleanup |
| `ci/release/workflow_policy.py`, `workflow-contract.json` | Semantic and exact reviewed workflow contract; rejects extra capabilities or unsafe changes |
| `ci/release/recovery.py` | Verify/reactivate retained local generations while preserving client objects; never edits a database |
| `ci/release/plan.py` | Review-only future GitHub Releases plan; creates no tag, draft, prerelease or release |
| `ci/release/test_policy.py`, `test_signing.py` | Eligibility, signing, transport, key isolation, workflow and publication failure regressions |
| `ci/verify.py` | Adds P5B tests to the existing backend regression command; removes no existing test |
| `.gitignore` | Excludes disposable staging directories and keyring/private-key files |
| Four `ci/P5B_*.md` documents and `ci/evidence/p5b/` | Architecture, procedures, results and non-sensitive verification evidence |

The workflow has no push/PR/release trigger, production secrets, write permission,
network publication job or release API call. Inputs pass through quoted environment
variables, not raw shell interpolation. Offline replay is forbidden in Actions;
hosted execution rechecks live CI and environment protection.

Current read-only inspection found **zero GitHub environments**. The new owner-approved
single-maintainer model requires manual owner dispatch and exact integration-branch
restriction, not another person's approval. No independent-reviewer protection is
claimed. Main registration and actual environment setup remain unauthorized.
`P5B_GITHUB_STAGING_PLAN.md` contains the exact inert registration-only proposal on
main, with executable staging kept on integration. No default-branch change or
integration/application merge is proposed or performed.

## Repository generation, provenance and publication safety

The rehearsal imports the accepted bundle into an archive repository, signs the
application ref, generates/signs AppStream and summary metadata, exports only the
public staging key, and creates `.flatpakrepo` / `.flatpakref` descriptors. URLs
are restricted to local paths or reserved `.invalid` staging HTTPS names. The
accepted production application identity is retained to avoid rebuilding; remote,
key and client directories are disposable. No application installation/launch or
owner data access is involved.

Clean OSTree verification requires signed summary and commits with only the supplied
public key, pulls all expected refs and checks object integrity. Native negative
cases include incorrect key, tampered summary, missing commit and unexpected ref.
The `.flatpakrepo` is checked by Flatpak in an isolated installation after local
activation. `.flatpakref` structure is checked; full client installation/update
validation belongs to P5C and is not claimed here.

Release metadata records source/repository, version/architecture/ID, runtime locks,
CI/workflow/artifact identities and hashes, OSTree commit, signing fingerprint,
authorization reference, target and outcome. The unsigned artifact hash is byte
integrity against an approved digest, not a substitute for publisher authentication.
The signed public manifest binds all published file sizes/hashes and rejects
missing, changed, extra, unsafe or private-key-containing content.

Publication copies and verifies a complete generation, syncs data/directories,
retains all old immutable objects/deltas, then atomically replaces the local pointer
on one filesystem under an exclusive lock. Partial copy, failed verification,
concurrent writers and an interruption before activation cannot advance the pointer.
There is no automatic pruning. Recovery refuses rollback that drops client objects.

This is an executable **local filesystem publication contract**, not proof of
multi-request HTTP transactionality. No cloud upload adapter is implemented or
enabled. The approved provider will need safe destination readback, stable URL
mapping, concurrency and cache/summary-signature transition validation. GitHub
Releases integration currently prepares a review plan, not a network writer.

## Tests and evidence

Final verification uses a fresh local clone at `1a28f68`, with the uncommitted P5B
candidate overlaid and hashed. Dependencies and frontend assets were installed/built
there; tests do not rely on the development checkout's generated files. A checkout-local
Python environment is required by existing launcher/installer tests. Crypto fixtures
use short private `/tmp` paths; package tests use disk-backed scratch space to retain
their existing free-space safeguards.

| Verification | Final result |
| --- | --- |
| P5B security/signing/publication/transport regressions | PASS — 44 tests; actual GPG, synthetic publication model clearly labeled |
| Existing P5A workflow contracts | PASS — 31 tests |
| Complete backend/security/lifecycle/migration/packaging plus P5B | PASS — 611 tests, 83 subtests |
| P5B workflow policy | PASS |
| Ruff and actionlint for both workflows | PASS |
| Clean-checkout production frontend build | PASS |
| Initial P5B local full frontend/browser verification | PASS — lint, 273 unit tests, TypeScript/build, all 20 original browser tests including 5 lifecycle tests; zero retries. Hosted follow-up is 19/20 and FAIL as recorded above. |
| Local appearance correction, exact final source in clean checkout | PASS — 20 focused runs; lint, 273 unit tests, TypeScript/build and 21 browser tests including 5 lifecycle tests; zero retries. New hosted verification NOT EXECUTED. |
| Live accepted P5A eligibility recheck | PASS — read-only, no run triggered |
| Disposable GPG smoke/signature verification | PASS; key homes removed |
| Actual native staging generation | PASS — owner Ubuntu run; signed OSTree repository and accepted artifact validation |
| Native signing rejection, descriptor and interruption checks | PASS — wrong key, tampered summary, missing object, unexpected ref, native flatpakrepo remote and interrupted activation |
| Protected GitHub staging workflow | NOT EXECUTED — unconfigured environment and no dispatch authorization |
| HTTP hosting, permanent key/rotation and full update lifecycle | NOT EXECUTED; outside this local staging verification |

Representative commands from the clean candidate checkout:

```bash
backend/.venv/bin/python -m unittest discover -s ci/release -p 'test_*.py' -v
backend/.venv/bin/python -m unittest discover -s ci -p test_ci.py -v
backend/.venv/bin/python ci/release/workflow_policy.py
backend/.venv/bin/python -m ruff check --config backend/pyproject.toml backend/app backend/tests ci
```

The complete backend command, working directories, timings and source hashes are
recorded in `evidence/p5b/local-verification.json`; frontend verification uses
`backend/.venv/bin/python ci/verify.py frontend --output <disposable-evidence-directory>`.
Actionlint uses the accepted tool verified during P5A, against both workflow files.

Historical failures are preserved. The initial clean-checkout setup used an external
venv and an overlong GPG-agent socket path, causing launcher environment failures and
GPG setup errors. The setup was corrected without weakening tests. An intermediate
run passed its tests but failed one Ruff line-length check; that was corrected.
The final review also closed a `..` output-path bypass and added credential-redirection
and diagnostic-redaction regressions. See `evidence/p5b/verification-history.json`.

### Native evidence reviewed — historical Codex blocker preserved

Actual Flatpak import reports **`error: open(O_TMPFILE): Read-only file system`**.
The isolated audit reached the unchanged accepted P5A auditor and failed at bundle
import. It did not produce a verified signed repository. No sandbox permission,
signature check or application security control was weakened to bypass this.
`native-staging-attempt.json`, `native-audit-diagnostic.json` and `capability-probe.json`
preserve the failure. The actual attempt predates the final path/redaction/test-only
refinements; it is not misrepresented as a final-source native success.

The owner subsequently completed that procedure successfully in regular Ubuntu.
Original `result.json` and `eligibility.json` were located at
`/home/cerillion/.cache/cyrnava-p5b.bUyzq5/run/` and preserved byte-for-byte in
`evidence/p5b/owner-native-2026-10-31/`. The result file's modification time is
2026-10-31 10:57:27 UTC; review time and both SHA-256 hashes are recorded in `review.json`.

The review confirmed overall PASS/complete, every required native positive/negative
step, exact approved bundle/source/CI run/OSTree commit, unchanged runtime locks,
version/identity and current release-workflow hash. The active retained generation's
signed inventory was verified independently using `gpgv` with only its exported
public staging key; every listed public file was rehashed, and repository byte/file
counts were recomputed. Both disposable secret-key homes are absent. No original
workspace or native result was modified.

The scratch `public/` copy lacks its manifest and descriptors at review time; no
cause is inferred. The authoritative active generation is complete, signed and
independently verified, so this is not a failure of the retained publication.
The intended interrupted generation remains inactive. See `review.json` for limits.

Eligibility remains **PINNED REPLAY** against run 41181510439/source 1ee2077, not a
hosted P5B run or live CI check. `release_workflow_run_id` is null. The recorded
tooling HEAD is 1a28f68 plus uncommitted P5B work; workflow hash matches, but the native
run did not record individual script hashes at execution. A later hosted run against
an authorized immutable P5B commit supplies that missing release-tooling provenance.
No native rerun is requested for this documentation update.

## Performance and cost

- Accepted bundle: **209,189,544 bytes**; CI ZIP: **210,238,004 bytes**.
- Logical installed application: **980,984,007 bytes**, 5,320 payload entries.
- GPG synthetic 93-byte manifest microbenchmark: key generation 0.185073 s,
  signing 0.010989 s, verification 0.010978 s; public key 667 bytes, detached signature
  310 bytes. These are one local run, not OSTree metadata-overhead measurements.
- Owner native archive repository: **301,341,805 bytes (287.38 MiB), 5,554 files**;
  signed metadata counter **2,016 bytes**. Deltas disabled, recorded delta bytes 0;
  that is not an enabled-delta overhead measurement. Generation **102.06 s**,
  signing/summary **0.13 s**, complete rehearsal **161.167 s** on one Ubuntu host.
  Signing time is included in generation; all positive/negative/publication checks
  are included in total time. Actual client network transfer and small-update size
  remain unmeasured.
- Static deltas default off; optional staging measurement is separate. No unsupported
  storage/performance target is imposed. Native scratch-space allowance is an estimate.
- Hosting scenarios for 5 / 100 / 1,000 installations now model 1.61 / 32.13 / 321.34 GB monthly
  application traffic. Under the documented assumptions, R2 core usage fits its free
  allowances; domain/routing/tax/runtime/CI costs are excluded. See the hosting decision
  for current official pricing, request counts, Netlify comparison and uncertainty.

## Remaining risks and owner actions

1. Review the completed native evidence; Gate 5 is now PASS. Do not repeat a full
   native rehearsal just to regenerate a documentation record.
2. Hosting/offline custody directions are now owner-endorsed. Permanent keys,
   provider purchases, domains, secrets and public hosting are not P5B staging
   acceptance prerequisites and remain separately gated.
3. The single-maintainer revision is synchronized at abbb1b7 and required CI
   41207770532 is PASS. No additional integration commit/push or rerun is authorized.
   Preserve the local acceptance tag and current verified source.
4. Separately authorize **A**: one inert registration-only main file, and **B**: the
   no-reviewer p5b-staging environment with exact branch-only policy and no secrets.
   Read both back; do not treat registration/configuration as hosted verification.
5. Separately authorize **C**: one owner-initiated workflow_dispatch at the exact approved
   revised tooling SHA, promoting the unchanged accepted P5A source/artifact. Require
   live eligibility, native signing/negative/descriptor/interruption checks, key cleanup,
   safe diagnostic upload and final PASS. No independent deployment approval is required.
6. After actual hosted staging evidence review, obtain explicit owner P5B acceptance.
   Neither current native nor CI PASS proves the new manual staging path executed.
7. Retain known-good snapshots, no-pruning policy, and independently authenticated
   trust bootstrap. Signing alone does not prevent all rollback/freeze attacks.
8. Keep P3 backups/schema compatibility authoritative: a binary rollback is not a
   database downgrade. Preserve existing licensing/distribution-review limitations.

## Acceptance gates and P5C readiness

| Gate | Recommendation |
| --- | --- |
| 1. Accepted baseline preserved | PASS — accepted P5A controls preserved; required CI at revised tooling abbb1b7 PASS |
| 2. Hosting architecture | PASS — R2-compatible direction owner-endorsed; provisioning/endpoint/cost authorization deferred |
| 3. Signing infrastructure | PASS — real disposable GPG and native signed OSTree/rejection checks; offline custody direction owner-endorsed; permanent key creation deferred |
| 4. Release workflow | Single-maintainer policy/tests pass local and hosted CI; registration, exact-branch environment and actual manual staging execution pending |
| 5. Signed repository and descriptors | PASS — owner evidence plus independent retained-generation integrity/signature review |
| 6. Publication safety | PASS for P5B local native staging and interruption protection; future HTTP/cache/update integration is unexecuted |
| 7. Security regressions | PASS for executed paths; no claim about unexecuted integrations |
| 8. Documentation | Delivered with explicit limitations and owner procedure |
| 9. Owner acceptance | Pending |

**Recommendation: CONDITIONAL — native and required CI acceptance gaps are closed;
the revised single-maintainer implementation passes hosted CI at abbb1b7.** Obtain
separate authorization for main registration, environment setup and one manual hosted
staging execution, then review actual evidence for owner acceptance.
No production credentials, keys, public hosting/release, main application merge or
P5C/P6 work is authorized or performed. Hosting/offline-custody directions stay endorsed.
