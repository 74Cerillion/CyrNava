# N4 — Native CI and public-release preparation

3 November 2026. **LOCAL IMPLEMENTATION VERIFIED; N4 / public release CONDITIONAL.**
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
