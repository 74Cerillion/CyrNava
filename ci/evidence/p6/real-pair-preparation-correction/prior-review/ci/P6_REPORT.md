# P6 — Distribution, installation and update validation

**1 November 2026 — P6 — CONDITIONAL / FURTHER ACTION REQUIRED.**

Local implementation and available automated verification are complete at this
checkpoint. Real remote installation **with actual runtime retrieval passes**.
The native launch probe fails at the host's user-namespace boundary before Qt
starts. Real GUI/persistence/update, public HTTPS, final licensing/trust and final
source/CI/release approval remain open. No P6 acceptance or public-release
readiness is claimed.

## Baseline and preservation

Local and independently reread remote integration HEAD remain
`bfa0b8005a3ddc519354fd7907e9b972fde8126b`; main remains
`4021bc292267c19b7ebebf219b4f682f8f99bf4c`. The local `p5a-accepted` tag still
resolves to `1a28f68c5732ccc1275403060e89ff168a846655`.
P5C's uncommitted formal closeout is preserved separately, byte for byte. No
commit, push, tag, workflow execution, GitHub setting, installation in the normal
Flatpak profile, personal workspace, permanent key or public endpoint was changed.

Accepted P5A source `1ee2077b283b8e5dfc2162119dd439ed3baeb109`, CI `41181510439`,
artifact `13035607417`, ZIP `73e6d58a…4eba6b`, bundle `93957ce5…20b26db` and
OSTree `da1bf73e…de1ac` remain distinct from release tooling and P6 candidate code.
Full values are in `ci/evidence/p6/release-candidate-manifest.json` and the unchanged
P5B policy. A fresh readback confirms the original artifact is unexpired and its
identity/digest are unchanged; it expires **7 November 2026, 07:53:28 UTC**.
Local cached replay is not new hosted eligibility. Expiration must never cause
silent substitution.

P3 migration/backup/schema safeguards, P4 production identity/package auditor,
P5A CI provenance, P5B eligibility/signing/seals/retained snapshots and P5C client
isolation are reused. Application code, schema 5, version 0.1.0, production
packaging, permissions, signing policy, CI workflows and accepted guards are
unchanged.

## Implementation

| Files | Result |
| --- | --- |
| `frontend/package.json`, `frontend/package-lock.json` | Exact minimatch 11.0.1 override and security regression in the normal test command; no wholesale upgrade |
| `frontend/scripts/check-minimatch.mjs` | All three consumer resolutions, ordinary matching and adversarial compilation in a bounded subprocess |
| `ci/release/distribution.py` | Provider-neutral reviewed publication plan and local reference adapter around accepted publisher; conditional activation, retained snapshots, verified HTTP GET/HEAD, MIME/cache/404 policy |
| `ci/release/trust.py` | Additional current primary/subkey identity, expiry and revocation checks on top of accepted cryptographic verification |
| `ci/release/product_inventory.py` | Bounded inventory of source locks and actual app/runtime metadata, SPDX records, native ELF hashes and notices; no symlink traversal or complete-SBOM claim |
| `ci/release/key_ceremony.py` | Fixed disposable certificate/signing-subkey rehearsal, encrypted backup/restore, primary-secret stub verification, expiry/revocation negatives and mandatory private cleanup |
| `ci/release/native_distribution.py` | Empty isolated client, actual upstream runtime retrieval and pin verification, real remote install, source/version/schema/permission validation and sandboxed launch probe |
| `ci/release/real_update.py` | Owner-gated real two-artifact preparation and GUI update/rollback/reinstall supervisor; exact B approval before signing; P5B audits/signing and P4 native assertions reused |
| `ci/release/test_distribution.py` | 30 new publication, transport, trust, inventory, isolation, approval and cleanup regressions |
| P6 plan/report/checklist/runbook/license review, release notes and evidence | Acceptance criteria, exact results, unresolved gates, executable owner procedure and release-candidate manifest |

Publication does not create a second signer. The adapter calls the accepted
signed seal, native OSTree verifier and durable publisher. It verifies the whole
source, destination and historical object set, then conditionally activates a
complete immutable snapshot under the existing exclusive lock. Dry-run does not
upload or activate. Production endpoints/credentials are not implemented/enabled.
A future provider must supply equivalent conditional-pointer/gateway semantics;
independent live summary/signature PUTs are explicitly rejected as a design.

HTTP serves only manifest-listed files beneath the current generation; it rejects
traversal, unlisted/private content and damaged objects. Immutable hash objects
are cacheable, while metadata and errors are no-store. The server verifies each
immutable manifest once and hashes every response. Signature pairs spanning two
HTTP requests can still cross an activation boundary and fail closed; the adapter
does not claim transactionality across client requests or universal anti-rollback
freshness for ordinary Flatpak clients. No public CDN behavior has been verified.

Real-update preparation is intentionally **not executed**: the B proposal remains
`owner_approved_for_disposable_P6_update: false`. It proposes the already-built real
application from accepted P5C implementation `bfa0b800…`, CI `41285343063`, artifact
`13075346402`, distinct OSTree `f759380d…ada15`, version 0.1.0/schema 5. This avoids
inventing a public version or rebuild solely for the compatibility exercise. It
does not replace the P5A allowlist or select the eventual final P6 source. The
supervisor has unit/approval-boundary coverage; its complete native A/B flow
remains unverified until separately approved and executed on a capable owner host.

## Advisory and licensing

The [upstream advisory](https://github.com/advisories/GHSA-g3hv-75wg-m249) affects
minimatch before 11.0.1. No patched 10.x release was available in the registry.
The narrow override changes minimatch 10.2.6 to 11.0.1 and adds its development-only
`@isaacs/nonrecursive-glob-match` helper. Node 24 satisfies the fixed package's
engine requirement. All other package resolutions remain unchanged.

ESLint, config-array and typescript-estree consume this matcher in development
checks. Inspected direct calls do not request optimizationLevel >=2. No
application/editor/API path into those callers was found; this is a bounded
reachability assessment, not a formal exploitability proof. Clean installed
consumers resolve the patched version. The adversarial regression tests repeated
`**/../` patterns at levels 0/1/2 within a hard child-process budget. Full frontend
regressions pass. **All 33 production frontend files are byte-identical to the
accepted application payload**, so a redundant Flatpak rebuild was avoided.
The historical P5C finding and accepted source lock remain intact; only the new
P6 source candidate is remediated.

Candidate OSV matching completed for 341 source-lock components with no matches,
and clean npm installation reported no registry audit findings. Neither clears
unenumerated runtime/native vulnerabilities. The expanded inventory identifies
PySide/shiboken 6.11.2, bundled Qt WebEngine 6.11.1 and runtime Qt 6.11.2 with
exact metadata/SPDX hashes. It indexes 34 upstream SPDX documents, 40 Python
metadata records, 2,971 ELF files and 1,553 notices across app/runtime trees. Unknown
licenses/versions, upstream NOASSERTION, static embedding, driver/extensions,
relationships and source correspondence remain limitations. See the inventory and
[license review](P6_LICENSE_REVIEW.md).

A separate scan of the **40 actual app/runtime Python metadata records** found
three matches in runtime-only Mako 1.4.1.dev0 and setuptools 80.10.2:
[Mako Windows lookup](https://github.com/advisories/GHSA-5639-2j2p-m4mx),
[setuptools macOS sdist exclusion](https://github.com/advisories/GHSA-h35f-9h28-mq5c)
and [setuptools Windows legacy wheel installation](https://github.com/advisories/GHSA-xmj3-9gf7-h52w).
Their documented OS/build preconditions are absent from the declared Linux
application use, and direct application source has no matching imports or API
calls. Packaging consumes prebuilt hash-locked wheels rather than building sdists
inside the runtime. These are **bounded not-reachable assessments; the packages
remain unpatched**. This is not proof about every native/third-party caller or
complete vulnerability clearance. No accepted runtime pin was silently changed.
Details and reassessment triggers are in `runtime-advisory-triage.json`.

Original-code/logo rights, use-composed-ref attribution provenance, MPL covered
source and Qt/LGPL/GPL/module obligations still prevent redistribution clearance.
Existing notices/fonts and metadata-only CC0 approval remain unchanged. MIT is a
recommendation for owner review, not a selected license. No missing attribution
or legal permission is invented.

## Local verification

A disposable detached checkout with independent Git objects starts at accepted
`bfa0b800…`; exact candidate files are overlaid explicitly. A new Python 3.12 venv
installs existing exact backend requirements and hash-locked PyYAML requirements;
`pip check` passes. npm ci installs the candidate from its lock in that checkout.
Tests do not use the development venv, node_modules or prebuilt frontend assets.
The first build begins with absent frontend/dist.

| Check | Actual result |
| --- | --- |
| Focused P6 regressions | **30 PASS** in 6.652 s |
| Complete backend/security/lifecycle/migration/packaging/CI/release suite | **693 PASS + 204 subtests**, 52.76 s, three existing warnings |
| Workflow contracts | **31 PASS**, also included above |
| Frontend lint and security regression | **PASS** |
| Frontend unit tests | **273 PASS** |
| TypeScript and production frontend build | **PASS**, existing large-chunk warning retained |
| Complete production-server Chromium suite, retries 0 | **21 PASS**, 2.4 min, including all five lifecycle tests and appearance/image regressions |
| Ruff, formatting, actionlint on all three installed workflows; exact CI contract | **PASS** |
| Disposable RSA-3072 primary/subkey backup/restore/sign/expiry/revocation/cleanup rehearsal | **PASS**, 1.770 s |
| Native actual runtime retrieval and real application HTTP remote install | **PASS** component checks, 233.451 s including launch attempt |
| Independent installed source/version/schema/runtime/commit/permission readback | **PASS** |
| Full real repository HTTP GET/HEAD/hash/MIME/cache verification | **5,559 files PASS**, 9.441 s final implementation |
| Real native GUI/application initialization | **BLOCKED / launch probe FAIL**, namespace restriction before Qt |
| Real A/B GUI update, rollback/reinstall persistence | **NOT EXECUTED**, B approval and capable GUI required |
| Hosted P6 / public HTTPS / independent machine | **NOT EXECUTED** |

The first full Python run had 684 passes and two failures because `/tmp` had less
than the existing 5 GiB packaging precondition. Re-execution on an isolated
larger-volume TMPDIR passed; no test, threshold, retry configuration or production
code was weakened. Initial HTTP verification took 101.350 s before verified
manifest caching; final transport verification passed in 9.441 s with per-object
hash checks preserved. Intermediate records are retained as history.

Commands and full non-sensitive result summaries are retained in
`ci/evidence/p6/verification.json`, test records and checksums. No GUI result is
inferred from browser/headless results. No native negative-security result is
substituted from unit mocks: the accepted P5C 13 native negatives remain historical
and new actual-client distribution fault gates remain separately unexecuted.

## Actual native installation

The empty private client independently fetched KDE Platform 6.11 and graphics/
codec/style extensions over the network, then pinned and verified Platform commit
`76fa01ac42ecf45d2c5020ef80de1c474c0c2ae86a51a79e8fec44c48f9dc473` with both GPG
checks enabled. BaseApp is already bundled into the application. The real
production app installed through a generated trusted flatpakref and HTTP remote,
without --no-deps and without development dependencies in the client. Installed
source is accepted `1ee2077…`, version 0.1.0, schema 5, branch stable, x86_64 and
commit `da1bf73e…de1ac`. Effective permissions pass the unchanged P4 validator.

The subsequent `flatpak run` failed with the classified
`sandbox-namespace-unavailable` error. An independent `unshare -Ur` probe reports
`Operation not permitted`. The driver correctly records overall FAIL for that
combined launch execution, preserving the passing installation components. No
sandbox flags or host security were changed. The exact isolated Ubuntu owner
commands and manual observations are in the [runbook](P6_RELEASE_RUNBOOK.md).

Measured local snapshot is 302,485,829 bytes / 5,561 files including seals; these
are **local P6 measurements**, not fabricated hosted P5C measurements. Hosting
planning uses these figures. R2 Standard remains preferred subject to owner
approval of provider/domain/budget/gateway; no infrastructure was provisioned.

## Release candidate and remaining approvals

`ci/evidence/p6/release-candidate-manifest.json` ties reference source, CI, artifact,
bundle, OSTree, disposable key, generation, descriptors, notes and inventory.
Production key and endpoint are null; publication is disabled. It is an
owner-review candidate, not a final newly built P6 release. The eventual committed
P6 source, successful CI, final artifact/audit, production trust and corresponding
source/notices must be selected together before release.

One grouped owner package is in [P6_OWNER_CHECKS.md](P6_OWNER_CHECKS.md):

1. Review the exact local source/docs/evidence; authorize a commit/push only if
   desired. No such authorization has been received. Ordinary CI will test the
   new regressions and build/audit the final candidate; no manual P6 run is implied.
2. Approve or replace the exact proposed real B identity, then run the gated native
   pair/GUI procedure. Complete actual-client interrupted update, bad trust,
   availability/cache and other unexecuted distribution cases on capable hosts.
3. Resolve license/logo/attribution/source obligations; approve permanent offline
   identity/custody/expiry and the separately reviewed production signing policy.
4. Approve provider, HTTPS endpoint, budget, gateway/conditional-write and credential
   boundaries before any external setup. Then separately authorize public HTTPS
   and independent-client verification. No deployment is currently ready to run.
5. Review the final artifact manifest and explicitly authorize tag/release/
   publication only after all required gates and formal P6 acceptance.

P5C closeout and P6 changes remain separate review groups in the proposed file
inventory. No main merge, production key, public tag/release or publication occurs.
