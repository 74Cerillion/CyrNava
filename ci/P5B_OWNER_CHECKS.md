# P5B owner checks — staging only, not production authorization

P5A is accepted. P5B implementation/native evidence already exists in a9de663.
One local documentation/review follow-up commit is authorized. No push, hosted workflow
trigger, permanent key, hosting subscription, environment change or release is
authorized by these instructions. Review `P5B_REPORT.md` for current test results.

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

## Future GitHub environment/workflow setup — requires separate approval

Read-only inspection found zero environments and only the existing CI workflow.
The release workflow exists on remote integration at a9de663, but not on default
main; only CI is registered. It has not been dispatched. Its definition intentionally
cannot succeed without independent protected approval.

- [x] One local P5B follow-up commit authorized after review.
- [ ] Authorize its push separately; no push is included in the commit-only grant.
- [ ] Review `P5B_GITHUB_STAGING_PLAN.md` and approve the registration strategy.
  Preferred: narrowly scoped inert workflow-registration file on main, with full
  execution on integration; no integration merge. This main-file change needs its
  own authorization.
- [ ] Determine how the manual workflow will be registered on GitHub's default
  branch. `workflow_dispatch` normally requires its file on that branch. No main
  merge/default-branch change is authorized here; do not bypass this requirement.
- [ ] If separately authorized, create `p5b-staging`, require an independent
  reviewer, prevent self-review, disable admin bypass, and allow only the exact
  `desktop/p2-production-integration` branch. Confirm settings through read-only
  API responses. A missing field, denied API or empty environment fails closed.
- [ ] A sole owner cannot independently approve their own initiated job with
  self-review disabled. Add a trusted second reviewer only with approval, or retain
  the offline owner procedure; do not silently remove the safeguard.
- [ ] No production secrets are needed for P5B. Use only read-only GitHub token
  permissions and disposable keys. Do not add a production key to this environment.
- [ ] Authorize one manual staging workflow execution separately. Use full source
  SHA, CI run, unchanged version, staging channel and reviewed authorization ref.
  The workflow rechecks CI and environment protection before signing.

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
