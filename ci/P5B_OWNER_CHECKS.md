# P5B owner checks — staging only, not production authorization

## Final owner acceptance — 1 November 2026

**P5B — ACCEPTED / COMPLETE.** The owner's explicit acceptance supersedes the
historical pending/conditional checklists below.

- [x] Owner reviewed the final technical assessment and independently verified the hosted execution.
- [x] Accepted tooling: `3ea472efcd6c3338debe16161de601286a5f177d`.
- [x] Accepted staging: 41265875118, attempt 1, SUCCESS; workflow 403136895.
- [x] Accepted source: `1ee2077b283b8e5dfc2162119dd439ed3baeb109`; P5A CI 41181510439.
- [x] All required P5B signing, integrity, negative-security, descriptor, interruption, cleanup and diagnostic-provenance gates passed.
- [x] Successful execution evidence and historical failures preserved without rewriting their original records.
- [x] Pinned artifact hashes, workflow identities, security requirements and integration branch preserved.
- [x] Final acceptance record and proposed documentation-only commit prepared for review.

Administrative follow-up, separate from completed acceptance:

- [ ] Owner separately authorizes the proposed final documentation commit.
- [ ] Owner separately authorizes any push.

Next milestone is **P5C — Integrated Release Pipeline Verification**, requiring
separate authorization. No P5C/P6 implementation, main merge, permanent key,
hosting purchase, publication or production deployment is authorized or performed.
See `P5B_CLOSEOUT_REVIEW.md`, the formal acceptance section in `P5B_REPORT.md`,
and `evidence/p5b/owner-acceptance-2026-11-01/acceptance.json`.

## Historical technical checkpoints

**P5B STATUS: PASS — READY FOR FORMAL OWNER ACCEPTANCE.**
Actual hosted staging **41265875118**, attempt 1, at approved tooling
`3ea472efcd6c3338debe16161de601286a5f177d`, completed SUCCESS after exactly one
new manual dispatch. Both jobs and all signing/integrity/negative/descriptor/
interruption gates passed. Complete PASS was persisted after guarded disposable-key
cleanup; the two-member JSON diagnostic ZIP was independently hash/provenance
verified. Repository: 301,341,805 bytes / 5,554 files; total 176.678 seconds.
Formal owner acceptance remains pending. No production key, hosting, publication,
additional commit/push, workflow rerun or P5C/P6 work is authorized or performed.
See final `P5B_REPORT.md` and `evidence/p5b/hosted-staging-41265875118/`.
The prior conditional/failure/checklist/authorization entries below are historical.

**Current hosted result — 1 November 2026: ordinary CI PASS; P5B CONDITIONAL / NOT ACCEPTED.**
The single authorized correction commit/push is complete at `3ea472efcd6c3338debe16161de601286a5f177d`.
Run **41264318875**, attempt 1, passed all five jobs: 31 contracts, 640 backend tests
+ 175 subtests, 273 frontend units, 21 browser cases, production Flatpak build,
exported-package audit, unsigned upload and required gate. All four downloaded ZIP
checksums and package provenance independently verified. See current `P5B_REPORT.md`
and `evidence/p5b/hosted-ci-41264318875/`.

Next: request separate owner authorization for ONE NEW staging dispatch at exact
`3ea472e`, retaining pinned source `1ee2077` and CI `41181510439`. No dispatch/rerun
or further commit/push is authorized. Main, inert registration, staging environment,
local tag and security controls are unchanged. Results below are historical snapshots.

**Owner-authorized commit/push checkpoint — 1 November 2026.** One P5B-only source-checkout correction commit and normal fast-forward push are now authorized from `d32ae20`. Review and ordinary hosted CI are pending. No manual staging dispatch or rerun is authorized; it requires separate approval after successful CI. Earlier authorization/readiness statements below are historical snapshots.

**Current local source-checkout correction, 1 November 2026 — P5B CONDITIONAL / NOT ACCEPTED.** Local verification passes 73 release tests (9 new), 31 CI contracts, Ruff, actionlint and all policies. A fresh shallow remote clone reproduces the missing-ancestor checkout failure; a fresh full-history clone verifies the exact accepted source and auditor hashes. Staging now requires full history and fixed redacted Git diagnostics. Source verification precedes disposable key creation.

No correction commit/push or new hosted execution has occurred. Next gates: explicit owner authorization for one correction commit/push; ordinary CI PASS at its immutable SHA; separate authorization for one new staging execution; all hosted security/cleanup/provenance checks PASS. No earlier dispatch authorization may be reused. See current `P5B_REPORT.md` and `evidence/p5b/source-checkout-correction-2026-11-01/`. The snapshots below are historical.

**Latest result, 1 November 2026: P5B FAIL / CONDITIONAL.** The separately
authorized second manual execution **41261468749**, attempt 1, ran at exact
approved `d32ae20`. Eligibility and both locked dependency installs PASS;
download/hash/candidate validation PASS. It then failed at `signed-repository`:
`Operation failed: git (CalledProcessError)` during accepted-source preparation.
Signed-repository security tests were not reached. The shallow checkout is the
likely cause; exact Git argv/stderr were not retained, so causality is not fully
proven. Diagnostic ZIP checksum/provenance verified. No retry or correction was
performed. Owner review/separate investigation authorization is required next.
See current `P5B_REPORT.md` and `evidence/p5b/hosted-staging-41261468749/`.

**Latest hosted result, 1 November 2026:** correction commit `d32ae20` was pushed
once; ordinary CI **41258927530**, attempt 1, passed every gate: 31 contracts,
631 backend tests + 158 subtests, 273 units, 21 browser tests, production build,
actual exported audit, validated unsigned upload and required gate. All four
artifact ZIP hashes and package provenance were independently verified.

- [x] Single authorized correction commit and normal fast-forward push completed.
- [x] Ordinary CI PASS on exact `d32ae20bfcd9ad3e6ccab530c62e2e2eb1918b8e`.
- [ ] Owner separately authorizes one new manual staging run at this tooling SHA.
- [ ] Hosted staging/security/cleanup/diagnostic gates pass; owner accepts P5B.

**P5B remains CONDITIONAL / NOT ACCEPTED.** No new staging dispatch/rerun is
authorized or performed. Main, registration and environment remain unchanged.
See current `P5B_REPORT.md` and `evidence/p5b/hosted-ci-41258927530/`.
Earlier readiness/checklist entries below are historical snapshots.

**Local correction ready, 1 November 2026:** clean-checkout PASS for 64 release
tests (5 new), 31 CI contracts, Ruff, actionlint and policy/integrity checks.
The unchanged pinned PyYAML dependency is installed independently in staging;
missing-import/setup failures now produce redacted FAIL diagnostics.
P5B remains **CONDITIONAL / NOT ACCEPTED**. Next owner gates:

- [x] Owner authorized one P5B-only correction commit/push after reviewing the diff.
- [ ] Verify ordinary hosted CI passes on that new immutable tooling commit.
- [ ] Separately authorize one new manual staging execution at that commit.
- [ ] Accept P5B only after all hosted staging/security/cleanup/diagnostic gates pass.

Only that one correction commit/push is authorized; no new staging dispatch or
GitHub configuration change is authorized. The accepted P5A artifact is unchanged.
See `P5B_REPORT.md` for exact files, hashes, tests and retained historical evidence.

**1 November 2026: P5B FAIL / CONDITIONAL.** A/B completed; the owner executed
the single authorized C dispatch, run **41256746729**, attempt 1, on approved
tooling `abbb1b7`. Eligibility PASS; staging FAIL because PyYAML was not installed
in that separate job. Diagnostic ZIP hash/provenance verified; signing and native
security tests were not reached. No repeat is authorized. See current
`P5B_REPORT.md`; the earlier checklist/procedures below remain historical.

P5A is accepted. Required CI run 41207770532 at abbb1b7 is PASS. The owner has
approved a **single-maintainer, manual owner-authorization** architecture for P5B.
The revised policy is committed, pushed and verified by automatic CI. Main
registration, environment setup and staging dispatch still require separate approvals.
No independent deployment approval or self-review prevention is required or claimed.
Review `P5B_REPORT.md` and `P5B_GITHUB_STAGING_PLAN.md` for exact evidence/settings.

## Decisions for review

- [x] Owner endorsed `P5B_HOSTING_DECISION.md`: provider-neutral snapshots now; R2-compatible
  storage is proposed for the eventual remote, Releases for an optional bundle mirror.
  No endpoint is selected or provisioned. Approve any domain, cost and account
  setup separately, after native repository size/file-count measurements.
- [x] Owner endorsed `P5B_SIGNING_DESIGN.md`: owner-controlled offline production signing
  recommended. Approve detailed key-creation/backup ceremony separately; staging
  fingerprints are never production trust anchors.
- [ ] Preserve P4 licensing/native-acceptance limitations and P3 schema/backup
  compatibility requirements. P5B does not resolve them by publishing a package.

## Native rehearsal completed — no repeat requested

- [x] Owner native PASS reviewed; accepted artifact/source, signed repository,
  negative cases, descriptor remote and interrupted activation confirmed.
- [x] Active retained generation signature and file hashes independently verified;
  measured 301,341,805 bytes, 5,554 files, 2,016 signed-metadata bytes, no deltas.
- [x] Result/eligibility preserved in `evidence/p5b/owner-native-2026-10-31/`.
  Eligibility is PINNED REPLAY, not a GitHub-hosted P5B run.

The following commands are retained as the reproducible historical procedure.
Do not repeat them merely to refresh documentation.

### Historical native command

This performs no app installation/launch and uses no owner workspace. It promotes
the exact accepted artifact, creates one-day disposable signing keys, signs and
verifies a private local repository, tests wrong keys/tampering/missing objects,
and exercises interrupted local publication. Secret key homes are removed on normal
completion/failure. Candidate/audit copies can occupy several GB: use disk-backed
cache with approximately 8 GB free; do not reuse the small `/tmp` tmpfs for outputs.
This is a planning allowance, not a measured peak. Choose a short path: GPG agent
sockets cannot use arbitrarily long Unix filesystem paths.

Existing tools: Python 3.12 or later, Git, Flatpak/OSTree, GnuPG including gpgconf.
No extra application build, runtime installation or Firefox access is needed.
The accepted ZIP must still be present at the path below. If absent, stop and
report that fact; do not substitute another artifact or disable hash checks.
An authenticated live download can be arranged separately. Do not paste tokens.

Copy these blocks **separately, in order** into the regular Ubuntu terminal.

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
```

```bash
p5b_parent="$(mktemp -d "$HOME/.cache/cyrnava-p5b.XXXXXX")"
```

```bash
python3 ci/release/stage.py \
  --archive /tmp/cyrnava-p5a-hosted-41181510439/package.zip \
  --source-commit 1ee2077b283b8e5dfc2162119dd439ed3baeb109 \
  --ci-run-id 41181510439 \
  --version 0.1.0 \
  --channel staging \
  --authorization-ref P5B-owner-authorized-disposable-staging-only \
  --output "$p5b_parent/run"
```

Expected: final JSON `status: PASS`, `complete: true`; candidate, signed repository,
wrong-key rejection, tampered-repository rejection, missing-object rejection,
unexpected-ref rejection, native `.flatpakrepo` remote resolution and interrupted
publication protection. Eligibility is labeled **PINNED REPLAY**, not live GitHub
verification. The application ref retains the production ID and stable branch,
but its remote/profile/key are disposable; never add this remote to a normal
Flatpak installation. The `.flatpakref` is structurally checked; full client
installation/update through it belongs to P5C and is not claimed here.

Share only `$p5b_parent/run/result.json` and, if needed, `eligibility.json`.
Do not upload the whole directory or any key home. If FAIL occurs, retain this
synthetic run and share the final JSON. Do not repeat it with security flags removed.
Native evidence has now been inspected and PASS recorded; hosted verification remains open.

An optional **separate** delta measurement uses the same command with
`--static-deltas --output "$p5b_parent/delta-run"`. It signs a fresh test repository;
it does not measure a real version-to-version application update. Retain results
before removing only the marked disposable parent. Do not delete any legacy data.

## Remaining owner steps — each external operation is separately authorized

- [x] Latest required CI verified: 31 workflow contracts, 626 backend tests + 144
  subtests, 273 unit tests, 21 browser tests, Flatpak/exported audit/upload/final gate.
- [x] All four downloaded artifact ZIPs independently match GitHub SHA-256; bundle
  and checksum/provenance/runtime/source records agree. See hosted-ci-41207770532.
- [x] Owner-approved single-maintainer tradeoff implemented locally: manual owner
  dispatch replaces independent GitHub deployment approval. No second user needed.
- [x] Revised local verification: 59 release/registration/signing tests + 31 existing
  CI contracts, Ruff/actionlint and both workflow/security policies PASS.
- [x] **Integration update authorization:** one P5B-only commit/push authorized for the revised
  single-maintainer policy, proposal/tests/docs and safe evidence. Review staged files
  first. Commit abbb1b7 was pushed; automatic CI 41207770532 passed all gates.
- [ ] **Authorization A — main registration:** approve only the inert
  `.github/workflows/release.yml` addition against main
  `cbf7cccc686080b2b4b07274a9f5a23fec52999f` (reread tip first). Exact local proposal:
  `ci/release/registration-only.yml`; full YAML, assessment and detached-clone owner
  commands are in the staging plan. No integration merge or default-branch change.
- [ ] **Authorization B — environment:** owner opens repository Settings → Environments,
  creates `p5b-staging`, leaves Required reviewers empty and adds exactly one Selected
  branches and tags rule: Branch `desktop/p2-production-integration`. No tags/wildcards,
  main/pull refs, secrets, production signing keys or publication credentials. No
  self-review setting or collaborator invitation is needed. Read settings back via
  GET APIs and local registration_policy.py; secret-name count must be zero.
- [ ] **Authorization C — dispatch:** approve one owner-initiated manual run from
  the exact revised integration SHA. Pin source 1ee2077b283b8e5dfc2162119dd439ed3baeb109,
  CI 41181510439/attempt 1, version 0.1.0, channel staging and authorization reference
  P5B-owner-authorized-disposable-staging-only. Full future command is in the staging
  plan. This is not permission to dispatch now or to promote the newest CI artifact.
- [ ] Before C, verify main registration, settings, registered workflow ID/path,
  integration tip/tooling SHA, workflow bytes/contract and accepted artifact availability.
  With no reviewer gate, eligible staging starts after dispatch; review must be before it.
- [ ] After C, verify run/actor/ref/SHA, eligibility, signed OSTree checks, all negative
  cases, descriptors, interruption protection, private-key cleanup, safe diagnostic
  upload and final PASS. Preserve provenance and safe result/eligibility hashes.
- [ ] Obtain formal owner P5B acceptance after actual hosted staging evidence review.

Current read-only inspection still shows zero environments and no release workflow
on main. These settings/commands are prepared proposals, not completed operations.
The owner must authorize A/B/C independently. GitHub credentials stay in the owner's
UI/CLI; do not paste tokens. No paid hosting, permanent keys, public release or P5C/P6.

## Permanent key / publication ceremony — not authorized during this rehearsal

- [ ] Approve production custody, algorithms/expiry, backup and recovery owners.
- [ ] Perform owner-controlled offline key generation only after explicit approval.
  Establish an offline primary/revocation backup and expiring release-signing subkey;
  verify fingerprints and restore encrypted backups in a disposable environment.
- [ ] Share the **public** fingerprint through an independently authenticated channel.
  Never paste private keys, passphrases or recovery material into chat.
- [ ] If a future protected CI signing subkey is chosen, approve environment secrets,
  reviewers/admin restrictions and workflow eligibility separately. A second secret
  holding the passphrase does not protect against a runner that can read both.
- [ ] Approve the permanent HTTPS endpoint, provider publication adapter, credentials,
  retention, cache controls, concurrency and client metadata-switch testing.
- [ ] Authorize any public staging deployment separately; no bucket/site is public now.
- [ ] Authorize each production signing/publication and any GitHub Release separately.
  The current workflow/CLI cannot enable this via input. The generated Releases plan
  creates neither a draft/prerelease nor a production tag.
- [ ] Complete the remaining protected hosted evidence and formally accept P5B.
  Native evidence is complete; permanent key creation/public hosting are not P5B
  staging-acceptance prerequisites. Hosting/custody designs can be endorsed without
  authorizing those irreversible operations.
  P5C and P6 remain separately authorized phases.

## Recovery

On staging interruption, retain result/evidence and inspect the marked local store;
do not advance its pointer manually. `recovery.py` can reactivate a verified retained
generation only if it preserves objects already visible to clients. Invalid or
object-dropping rollback is rejected. No automatic pruning is performed.

```bash
python3 ci/release/recovery.py --help
python3 ci/release/plan.py --help
```

For production compromise/outage, stop publication and follow the signing design.
Binary rollback is not SQLite rollback: restore data only through verified P3
snapshots and explicitly supported schema compatibility. No reverse migration is
introduced by P5B.
