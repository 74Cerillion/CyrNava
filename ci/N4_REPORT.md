# N4 — Native CI and public-release preparation

3 November 2026. **LOCAL CORRECTIONS VERIFIED / READY FOR REVIEW.
Last hosted ordinary CI remains FAIL; N4 / public release CONDITIONAL.**

## Latest checkpoint — authorized local corrective preparation

The owner authorized investigation and preparation after run 41607482461 failed.
No further project commit, push or GitHub execution was authorized or performed.
The integration checkout remains at `7d3bd86ad335b1a518c5dd7df09106b847d2256d`;
the index is empty and the corrective batch is uncommitted.

**Historical release-test cause confirmed for all 74 failures.** The original
JUnit traces identify the unchanged accepted-CI hash guard in 52 failures. A
focused observer then reproduced the remaining 22 failures on the active checkout
and recorded the same original guard rejection in every case, without replacing
its result. These are preserved expected-failure causal observations, not passing
regressions. [Causal evidence](evidence/n4/correction-2026-11-03/remaining-22-causal.json).

`ci/historical_release.py` now copies the **current unchanged** legacy code/tests,
locks and auditors into a small disposable source fixture. Only its CI file is
replaced with the exact accepted bytes recovered from
`b27e33bb0b31ecd93a3792c6b6a889686dfae575:.github/workflows/ci.yml`, hash
`3f11c9ab58d2f7c8cebca0b153a09ccffae06e314545067ddd6b42f7b8e809f4`.
This is a unit-test fixture, not a restored release target or old-code substitute.
Every copied source is hash-checked after testing. Current/native CI validation
runs separately; the accepted real policy still rejects the new native CI bytes.
No policy, workflow identity, artifact/source allowlist, signature guard or useful
historical test is relaxed or removed. `ci/verify.py` requires both test selections
to succeed before backend PASS. All 351 legacy regressions pass in that fixture.

**Frontend correction is test synchronization only.** A controlled delayed initial
selection-focus handoff reproduced the original expected-input/observed-tree
failure, while the immediate case passed. The autosave test now explicitly waits
for initial tree focus before editing, and still requires the title to retain
focus after saving. Immediate/deferred handoffs and independent tree refresh,
tab-stop and blocking-operation focus behavior are covered. The hosted record
did not retain initial event ordering, so that exact ordering remains unproved;
no production focus defect or application-code fix is claimed.

Two path-only build unit tests also depended on the actual temporary filesystem's
5 GiB capacity. Their stage is mocked; capacity is now an explicit synthetic
precondition, with a new independent low-space refusal assertion. The production
guard and original disk-precondition failures remain unchanged. The fixture's
first long temporary layout caused 17 real-GPG setup errors; these remain recorded.
A short child-only temporary path corrected that fixture compatibility. All real
signature tests use fresh disposable one-day synthetic keys, with successful test
cleanup; no production identity or expired accepted rehearsal credential is used.

| Final local selection | Actual result |
| --- | --- |
| Current backend, packaging and workflow | 574 PASS; includes 38 workflow/fixture tests |
| Historical release/security/current-code fixture | 351 PASS; 198 subtests PASS separately |
| Frontend unit | 277 PASS, 22 files, one worker |
| Production Chromium browser | 21 PASS, 2.2 minutes, one worker, zero retries |
| Native installation/security/maintenance tooling | 197 PASS, including the 6 actual disposable-signature tests omitted in the earlier preparation |
| Native feasibility | 54 PASS |
| New source-closure/audit focused subset | 16 PASS, included in native count |
| Ruff, frontend lint, TypeScript/Vite, actionlint and exact workflow contract | PASS |

Unique local total: **1,474 passing tests**, without adding subset counts twice.
The CI-equivalent test selections used the existing dependency environments rather
than reinstalling them. A fresh TypeScript/Vite output matches every preserved
`frontend/dist` byte used by backend/browser tests. No native GUI, A/B preparation,
new Qt build, dependency download, host-policy operation or normal installation ran.
The native assembly/install job itself has not been rerun in this correction pass.

The fresh review packet is `ci-output/native-n4-corrected-metadata-1/`:

- Application ZIP remains `ci-output/native-n4-release-proposal-1/CyrNava-0.1.0-ubuntu-x86_64.zip`,
  SHA-256 `994e526870bd82828a2c2c90c1a71860ea2e1ac828c0e1bfaf7e504261ecf790`.
- Corrected review manifest SHA-256:
  `dd1d694a141f9cfbe0edc44b1ee892f4fade3e26380e6ef7fbb0e32d3eef7f0b`.
- Source ZIP SHA-256:
  `1ddee3e29fc1492e2af7c712c2480b53513e02645f5cb617d368dc6ba4355400`.
  Its 285 source files now include the retained historical-test inputs required
  by the new helper; it still excludes evidence trees, environments and private data.
- Installer ZIP is byte-identical, SHA-256:
  `9c508116919ff4aedc085b7b9bb29800307a45f7d6ed1b7ba743eb9476df261a`.

This is an **audited unsigned local review packet**, based on 7d3bd86 plus explicit
uncommitted source/file hashes. It reuses the immutable application ZIP, with no
binary rebuild or replacement of accepted artifacts. Its source/manifest is distinct
from earlier packets, which remain intact. It is not a new hosted/signed release.

Browser scratch briefly reduced observed free space to 5,361,344,512 bytes, below
the 5 GiB preparation floor. No new packet/build was started then. The running
test's own successful cleanup restored 5,435,625,472 bytes before source-packet
creation; no retained evidence or cache was deleted. This transient observation is
retained rather than reported as uninterrupted resource-floor PASS. Final allocation
and free-space measurements are in the corrective evidence.

[Correction result](evidence/n4/correction-2026-11-03/result.json),
[test scopes](evidence/n4/correction-2026-11-03/tests.json),
[review packet](evidence/n4/correction-2026-11-03/review-packet.json).
Exact files/hashes for a proposed corrective commit are in
`ci/evidence/n4/correction-2026-11-03/commit-proposal.json`. **Next owner checkpoint:
review and separately authorize one corrective commit and normal integration push
for ordinary CI.** The original hosted run remains FAIL; no acceptance is inferred
from local tests. Vendor notices/source correspondence, final public-identity native
verification, genuine production signing and publication remain separate.

## Historical checkpoint — authorized integration commit and push

The owner approved the reviewed 46-file batch and one normal integration push.
Commit **`7d3bd86ad335b1a518c5dd7df09106b847d2256d`**, parent
`b27e33bb0b31ecd93a3792c6b6a889686dfae575`, tree
`1585cd42985f7a8b4ab6dbf9c4bdd27ee39badf3`, was created unsigned and pushed once to
`origin/desktop/p2-production-integration`. Remote parent/tree/exact paths were
independently read back. `main` remains default and unchanged at
`4021bc292267c19b7ebebf219b4f682f8f99bf4c`. No merge or release signing occurred.

[Ordinary CI run 41607482461](https://github.com/74Cerillion/CyrNava/actions/runs/41607482461),
attempt 1, push event, completed **FAIL** (3 November, 18:00:11–18:02:04 Korea time).

| Hosted job | Actual result |
| --- | --- |
| Workflow validation | PASS |
| Backend and security | FAIL: 846 tests passed, 74 failed; 154 subtests passed |
| Frontend and browser | FAIL: unit tests 272 passed, 1 failed; later production-build/browser steps not executed in this job |
| Native Ubuntu package and exported-archive audit | SKIPPED by required dependencies; no hosted native package produced |
| CI required | FAIL; no bypass |

The frontend failure is `frontend/src/App.test.tsx:409`, “does not steal editor
focus when autosave refreshes the directory titles.” Expected focus was the note
title input; actual focus was the corresponding note tree item. The retained result
does not establish whether this is an application race or a test synchronization
defect. Do not call it flaky or silently retry it.

Fifty-two of the 74 backend/release failure traces explicitly contain the historical
guard at `ci/release/core.py:147`: “Accepted CI workflow changed; policy review
required.” The unchanged accepted Flatpak policy expects CI hash
`3f11c9ab58d2f7c8cebca0b153a09ccffae06e314545067ddd6b42f7b8e809f4`;
the reviewed native workflow is
`94e6a3404f138b615450a9ee409405e0cd15de76f04e3fb4665647ebea62e64d`.
The other 22 failures concern early owner-approval/phase expectations and need
specific triage; their exact cause has not been independently reproduced.
No historical policy/hash or accepted application artifact was altered to suppress
these failures. The future correction should isolate historical-policy fixtures
from the new active CI target while retaining useful tests and security assertions.

The earlier 422 backend application passes did **not** cover the complete
920-case backend/release selection in `ci/verify.py`. This local coverage gap was
missed. The earlier 994 local passes remain valid in their recorded scopes; they
do not override this hosted FAIL or certify the final native package.

Both actual diagnostic ZIPs were retained and independently matched GitHub's API
digests, sizes and exact commit/run provenance:

- Backend artifact `13217735615`, 24,724 bytes, SHA-256
  `ae278d25699d0503db40b2a24bf3c61cb555f9b5d76e00eec68c106b200da5a3`.
- Frontend artifact `13217641247`, 337 bytes, SHA-256
  `c909c2f14827cf3cf4ac720d83d056cdbedf40d4cb2da0f25fba88936be98d26`.

Sanitized evidence: [hosted result](evidence/n4/hosted-41607482461/result.json),
[artifact integrity](evidence/n4/hosted-41607482461/artifact-integrity.json),
[remote readback](evidence/n4/hosted-41607482461/remote-readback.json).
Original job output/downloads remain private under `ci-output/native-n4-push-1/`.
The initial local staging attempt was blocked by a read-only `.git`; explicit
sandbox access was then granted before the single commit. No Git/source defect
was inferred from that permission failure.

**Stopped at the failure checkpoint:** no implementation correction, CI rerun,
second commit or second push. These post-run report/evidence updates remain local
and uncommitted. Proposed next bounded work is to reproduce/correct the focus
failure, make historical release tests hermetic without weakening accepted policy,
and run the full CI-equivalent selection before presenting a corrective batch.
Signing, final native testing, vendor source/notice closure and publication remain
separate; no keys or owner GUI interaction are needed for this investigation.

## Prior local preparation checkpoint — preserved scope

N1–N3 are owner-accepted. Current owner-committed baseline:
`b27e33bb0b31ecd93a3792c6b6a889686dfae575`, branch
`desktop/p2-production-integration`; the working tree was initially clean.
No accepted artifact/source identity is replaced by this new preparation.

Local scope: source-based native assembly; audited package/source/installer artifacts;
exact native CI policy on supported Ubuntu 26.04; focused regressions; original MIT
and branding decisions; native install/manual update/recovery and dependency/source
materials. No Qt/Chromium build, old Flatpak rehearsal or custom hosting.

Protected baselines and resource plan: `ci-output/native-n4-1/baseline.json`.
Maximum local added allocation 3 GiB; keep at least 5 GiB free. Exact existing
wheels were reused without dependency upgrades or repeat wheel downloads. Matching
compressed upstream source/notice materials were acquired within that allocation;
no Qt/Chromium compilation or full source-tree extraction occurred. Operations had
individual time bounds; the 1,800-second build-work estimate is not a claim that the
entire investigation/source-review elapsed time stayed below 30 minutes.

Owner selected MIT with **Copyright (c) 2026 74Cerillion** and confirms ownership of
the CyrNava name/logo. Third-party notices/source correspondence remain separate.
No production key/signature exists for these outputs. No commits/pushes/CI executions,
host policy load, normal installation, signing or publication are authorized.

## What is implemented

- `packaging/native/release.py` assembles current application/frontend source with
  the accepted hash-locked 19-wheel dependency closure. It exports the package,
  source snapshot, installer kit, dependency/ELF/notice inventory and checksums.
  Its independent exported-file audit rejects unreviewed/private paths, duplicate
  ZIP members, tampering, wrong source/provider identities and changed bootstrap.
- `ci/native.py` performs a controlled frontend build in a new output directory,
  package/source audit and real isolated offline installation with installed
  imports/ELF/provider/backend/data checks. Clean source is mandatory in CI;
  explicit local patch preparation records the source commit, tracked diff hash
  and every included source file. It never promotes headless imports to renderer PASS.
- The ordinary CI proposal retains backend/security/browser/lifecycle tests and
  immutable actions/read-only permissions/credential-free checkout. Native package
  assembly replaces the required Flatpak artifact job on Ubuntu 26.04 with full Git
  history, independent prerequisites, fail-closed audit/upload and required-job gates.
  Accepted P5B/P5C release workflows and useful historical tests remain unchanged.
  [Exact workflow contract](native-workflow-contract.json) and mutation tests cover it.
- `policy_setup.py` exports a narrow standalone normal-installation adapter to the
  already accepted policy renderer/root helper. It requires verified installation,
  manifest and policy identities; install never loads policy automatically. Explicit
  owner-host load/remove remains separate. Local prepare/parser checks passed;
  there was no host policy load. Safe errors do not publish raw arguments or paths.
- MIT, approved attribution and name/logo decisions are recorded. Native
  [installation/manual maintenance](../docs/native-installation.md),
  [release notes](../docs/native-release-notes-v0.1.0.md),
  [inventory](../docs/native-dependencies.md) and
  [source obligations](../docs/native-source-obligations.md) are supplied. Public
  fingerprint/download examples deliberately remain parameterized until real trust
  and publication approval exist. No signing identity is invented.

The accepted installation/maintenance engine, application/backend/data/schema code,
renderer predicates and existing built `frontend/dist` are unchanged. The CI lint
scope excludes frozen `ci/evidence` source snapshots while checking live code and
the new N4 modules. A path-specific E501 exception preserves the previously audited
cleanup engine's cosmetic diagnostic. No broad lint/security suppression is added.

## Actual artifacts and source identity

| Material | Exact identity / observed scope |
| --- | --- |
| Committed base | `b27e33bb0b31ecd93a3792c6b6a889686dfae575`, `desktop/p2-production-integration`; initially clean, unchanged HEAD |
| Development package | `ci-output/native-n4-build-1/artifacts/CyrNava-0.1.0-n4.1-ubuntu-x86_64.zip`; SHA-256 `b59a3bd4a3178d704d0dfab736f6e6d546578cf5744a6dcda1264b83e3c9736d`; 271,836,075 bytes |
| Development manifest | SHA-256 `cce75b79af6461783d5d331eeeb93ce92aa3d0d5e6ab1a2827a3abcfdcd5fe88` |
| Actual isolated installation | `ci-output/native-n4-build-1/client/releases/0.1.0-n4.1-b59a3bd4a3178d70`; 4,414 provider files; installed headless checks PASS; GUI/policy load NOT EXECUTED |
| Unsigned public-identity proposal | `ci-output/native-n4-release-proposal-1/CyrNava-0.1.0-ubuntu-x86_64.zip`; SHA-256 `994e526870bd82828a2c2c90c1a71860ea2e1ac828c0e1bfaf7e504261ecf790`; audited, not installed/launched/signed as a public identity |
| Current proposal metadata | `ci-output/native-n4-release-metadata-3/manifest.json`; SHA-256 `db5076086f16c0f2c01f2278f7b3591450b2444f6aaf3c03bbe7185469029967` |
| Current source snapshot | Same metadata directory, `CyrNava-source.zip`; 196 source files; SHA-256 `18b53aeefde74708561339561488c435d85f4527dd223ba6f7e2f0accdc562e6` |
| Current standalone installer | Same directory, `CyrNava-installer.zip`; SHA-256 `9c508116919ff4aedc085b7b9bb29800307a45f7d6ed1b7ba743eb9476df261a` |
| Dependency pins | `dependencies.json`: `621c640f428886a7944b654fe6726f2b3ab82644e4911a051f8281ab392eb8a3`; requirements lock: `24876b72281d5427fc9c5c41cdb19a918815e9547e74c5eb4d2c93ac22e4a576`; matched Qt/PySide/Shiboken/WebEngine 6.11.3, CPython 3.14 |

The latest packet refreshes only source/development configuration and standalone
policy diagnostics; it reuses the immutable public-identity ZIP read-only, without
duplicating or rebuilding it. Original proposal/metadata packets remain intact.
`asset-locations.json` maps the physical files; `SHA256SUMS` is presently **unsigned**.
Source provenance records assembly-time local tracked patch
`27e3f3800252174a73b6783e32bf63f952611afdf30729dafca11043d8744fb3`
and individual included source hashes. Later report/evidence additions are separate;
this is not falsely described as a clean committed/reproducible release.

All 96 accepted N3 runtime files are byte/mode-identical in the N4 development
candidate; it adds three notice/inventory files. The public-identity proposal changes
only generated `application/desktop/native/build_identity.py` relative to that runtime
(application ID/channel/title). N1–N3 GUI/security/data evidence is inherited only for
its exact unchanged inputs; public identity/desktop/trust still needs focused evidence.
See [runtime comparison](evidence/n4/local-2026-11-03/runtime-equivalence.json).

## Executed verification and retained failures

| Local verification | Actual result |
| --- | --- |
| Thin frontend/package/audit/installed checks | PASS, 21.661 seconds; 99 payload files; no Qt source build |
| Native installation/security/maintenance suites | 191 PASS, including 16 new N4 focused tests |
| Native feasibility fixtures | 54 PASS |
| Workflow/security contract tests | 33 PASS |
| Backend/security/data tests | 422 PASS, 2 known warnings; run from documented `backend/` context |
| Frontend unit tests | 273 PASS across 22 files |
| Production Chromium browser tests | 21 PASS; browser evidence, not Qt/AppArmor native evidence |
| Ruff, frontend lint, TypeScript/Vite, workflow validator/actionlint | PASS |
| Exported-auditor negatives | All 5 rejected: private extra, duplicate member, binary tamper, source-provenance tamper, installer tamper |
| Host/native GUI, release signing, hosted CI | NOT EXECUTED in N4 |

Total **994 local tests passed**, without double-counting the 16-test N4 subset.
Six real signing/key-generation fixtures were explicitly not executed under the
current no-signing authorization; they are listed in [test evidence](evidence/n4/local-2026-11-03/tests.json).
No signature claim comes from these fixtures or an unsigned checksum.

Failures remain under `ci-output/native-n4-1/`: initial fixture `/tmp` space refusals,
backend repository-TMPDIR isolation refusal, wrong-cwd backend subprocess imports,
overbroad historical-source lint scope, upload-validator exception and old-linter
runner label handling. Corrected harness/config invocations passed in stated scopes.
No application defect was inferred from those invocation failures. Original failed
logs and XML remain; corrected results do not overwrite them or old P6 disk failures.

## Redistribution materials: collected versus still unresolved

The actual wheel inspection records 19 distributions, 498 ELF files and 18 notice
documents. All four Qt/PySide/Shiboken wheels lack license/notice-named documents;
their declared license metadata alone is insufficient. Their full Addons content
must be mapped to applicable module/third-party terms; unused files were not hidden
or stripped to pass the audit.

Bounded compressed source acquisition completed without compiling/unpacking Qt:

- Qt 6.11.3 source: 1,020,081,224 bytes; SHA-256
  `ad0112f2aef1b94b42a7ab653cebda2f7fc9ba88ef509ec456b17be80b0bfdab`.
- PySide/Shiboken 6.11.3 source: 18,063,176 bytes; SHA-256
  `050819cb05e14d6689f42b56e4fa9c8ff63be2bb339e0c094c45b990b7cabde1`.
- Published sizes/hashes matched exact official Qt release metadata; approved
  HTTPS MirrorBrain redirect was recorded. 2,519 notice documents (11,126,280 bytes)
  were inspected by bounded archive streaming. Sources remain at
  `ci-output/native-n4-source-2/`; the first timed-out 498,597,888-byte partial is
  preserved in `native-n4-source-1/`. One exact HTTP 206 Range continuation succeeded.
- All three BlockNote 0.56.0 source tarballs match lockfile integrity and every
  installed package build-input byte (1,454 files compared). Original 8 MiB map
  inspection refusal is retained; independent bounded 16 MiB inspection passed.

Exact wheel-to-source/build/patch correspondence, shipped-module license selection,
notice completeness and practical recipient replacement/rebuild instructions remain
open. `use-composed-ref@1.4.0` still lacks an authoritative retained attribution notice.
These are specific public redistribution blockers, not an enterprise SBOM requirement.
No complete vulnerability clearance, universal compatibility or license clearance is
claimed. The previously unresolved minimatch advisory is not reclassified.

Smallest vendor clarification, for owner review only (not sent): ask Qt for exact
6.11.3 wheel build source revisions/patches and complete module/Chromium notices;
ask the pinned `use-composed-ref` maintainer for its applicable MIT copyright notice.
The matching compressed sources and actual per-file inventory are already available.

## Supported release boundary and remaining checkpoints

Target: **native Ubuntu 26.04 x86_64 / GNOME Wayland via GitHub Releases**, system
CPython 3.14 and bundled locked Qt 6.11.3 family. Manual full-package updates only;
schema 5 and the accepted identical application/storage/browser consumer family.
No arbitrary future runtime promise, automatic update server, platform expansion or
Flatpak completion requirement is added. N1–N3 and P1–P5/R11/R12 retain acceptance
and their actual artifact scope.

| Remaining essential checkpoint | Current status / smallest next action |
| --- | --- |
| Clean-source hosted native CI | Local implementation/contract/tests PASS. Owner review and separate authorization for one N4 commit and normal integration-branch push; hosted execution then independently checked. No main merge/publication. |
| Vendor notices/corresponding source | Materials collected; resolve the specific Qt/module/attribution issues above before distributing. |
| Final exact public-identity package | Audited unsigned proposal exists. After reviewed committed build/trust selection, focused isolated signed install, GNOME launch/renderer/auth/data/relaunch and supported manual-update check; do not repeat the full historical rehearsal. |
| Authentic release trust | Owner selects an existing full primary fingerprint and separately authorizes exact-asset signing. No private-key search/creation or expired rehearsal key reuse. Verify actual signatures, not just checksums. |
| Publication | Separate owner approval only after above gates; then independently download and authenticate published assets. No release/tag/upload has occurred. |

The actual final-package handoff must bind its package/manifest/installer/source
identities and freshly prepared exact installation-root policy. Old N2/N3 root policy
commands must not be reused. Existing key-protection/replacement procedures and backup/
recovery documentation remain proportionate to a single-maintainer local application.

Protected hashes, actual test/artifact results and evidence sources are preserved in
[local N4 evidence](evidence/n4/local-2026-11-03/preservation.json).
Final measured resource usage and the exact uncommitted review batch are in
`resources.json` and `commit-proposal.json` in that directory. No cleanup was performed;
allocated bytes are not a disk-reclamation claim. No application runtime source,
host security setting, accepted artifact, private profile or signing material was changed.

**Next owner decision:** review this local N4 batch for a separately authorized
integration commit/push and ordinary CI. Signing, final owner-host execution and
publication remain distinct checkpoints. N4 is not recommended for acceptance yet.
