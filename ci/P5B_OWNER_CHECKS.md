# P5B owner checks — staging only, not production authorization

P5A is accepted. Required CI run 41205351385 at 7aaefd0 is PASS. The owner has
approved a **single-maintainer, manual owner-authorization** architecture for P5B.
The revised policy is locally verified. The owner subsequently authorized one
integration commit/push; main registration, environment setup and staging dispatch
still require their separate approvals.
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

- [x] Latest required CI verified: 31 workflow contracts, 611 backend tests + 83
  subtests, 273 unit tests, 21 browser tests, Flatpak/exported audit/upload/final gate.
- [x] All four downloaded artifact ZIPs independently match GitHub SHA-256; bundle
  and checksum/provenance/runtime/source records agree. See hosted-ci-41205351385.
- [x] Owner-approved single-maintainer tradeoff implemented locally: manual owner
  dispatch replaces independent GitHub deployment approval. No second user needed.
- [x] Revised local verification: 59 release/registration/signing tests + 31 existing
  CI contracts, Ruff/actionlint and both workflow/security policies PASS.
- [x] **Integration update authorization:** one P5B-only commit/push authorized for the revised
  single-maintainer policy, proposal/tests/docs and safe evidence. Review staged files
  first. Verify its automatic CI before using that immutable tooling commit.
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
