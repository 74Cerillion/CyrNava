# P5B release signing design — custody direction endorsed; key ceremony deferred

Recommendation: owner-controlled offline production signing, with an offline
certification/recovery primary and an expiring signing subkey after a separate
owner-approved key ceremony. The owner endorses this architectural direction;
permanent key creation, secrets and credentials remain unauthorized.
**No production key or secret has been created.**
P5B implements disposable staging signing only. Changing a flag or supplying a
manual workflow input cannot enable production signing/publication.

## Trust boundaries

| Mechanism | Authenticates | Does not establish |
| --- | --- | --- |
| Git commit/tag identifier | Specific source/history identity | Safe code or a Flatpak publisher identity by itself |
| Artifact SHA-256 | Exact downloaded bytes against a trusted expected digest | Publisher identity when the expected digest is untrusted |
| CI run and package audit | Tested source, approved build process and exported content | Authorization to release publicly |
| OSTree commit signature | The signed application/tree metadata and content hashes | Database downgrade compatibility or approval of a hosting endpoint |
| Signed repository summary | Authenticated advertised refs | Safe public-key bootstrap or protection from all rollback/freeze attacks |
| Public key fingerprint | Which independently approved trust anchor to use | Authority when copied from the same untrusted download alone |

Threats include compromised CI/artifact storage, malicious manual inputs, wrong
source/version/runtime locks, compromised signing/publishing credentials, forged
or tampered metadata, interrupted publication and a client holding older metadata.
The owner/operator and approved source review remain trust anchors. No tooling can
make a malicious authorized signer safe. Signing is not a substitute for source,
licensing, data-migration or native acceptance review.

## Custody comparison

| Option | Strength | Principal exposure | Cost/maintenance | Assessment |
| --- | --- | --- | --- | --- |
| Protected Actions environment secret | Convenient gated signing on ephemeral runners | A compromised approved workflow/runner can exfiltrate a software private key; storing its passphrase alongside it is not independent protection | Low infrastructure cost, careful environment/admin maintenance | Optional future signing subkey only, explicit approval required |
| Offline/owner-controlled signer | Production key absent from CI and publication infrastructure | Owner device compromise, backup loss, operator error | Manual release step; encrypted backups and a written ceremony | Preferred for this small project |
| Managed signer/HSM service | May offer hardware policy and audit | Provider credentials, service trust, OpenPGP/OSTree compatibility | Added service cost and integration | Not justified by present needs |

Permanent key creation, import into GitHub, secrets and environment changes require
separate approval. Public-repository required reviewers are supported in current
GitHub plans, but their configuration must actually be inspected. The read-only
P5B inspection found **zero environments**. No reviewer protection is claimed.
[GitHub environment controls](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments).

## Current executable staging design

- `stage.py` requires the full approved source SHA, existing version, CI run,
  staging channel and reviewed authorization reference. `policy.json` allows only
  the owner-accepted P5A artifact; its source, ZIP, bundle, inventory and inputs are
  pinned. Production enablement must remain literally false.
- Live workflow mode checks successful push CI, exact repository/workflow content,
  all five required jobs, run attempt and artifact identity/digest/expiry. It
  downloads without forwarding the GitHub API bearer token to artifact CDN URLs.
- Offline mode is explicitly labeled a replay of the hash-pinned owner-accepted
  artifact. It is forbidden in GitHub Actions and never reported as live CI proof.
- Artifact ZIP extraction is bounded and allowlisted; symlinks, duplicates,
  traversal, malformed metadata and hash/identity/lock/version mismatches fail.
- The unchanged P5A auditor imports the exported bundle and checks its contents.
  A disposable detached checkout binds that audit to the approved source. A child
  process binds the auditor's source SHA without changing the release job's own
  source context. Actual release-tooling commit/workflow hash are recorded separately.
- New RSA-2048 **test-only**, one-day GPG keys are created in mode-0700 directories
  outside the repository. Their UID and marker say CYRNAVA P5B STAGING ONLY.
  Production keys are refused by this path. The test key size/expiry is not a
  permanent production-key policy decision.
- `gpg --no-options --homedir` prevents personal profile/configuration use. Keys
  are never fetched automatically. Private keys are neither exported nor printed.
  Key homes are destroyed on normal completion/failure; after a hard kill the
  operator removes only the marked disposable workspace.
- Application commits and summary/AppStream metadata are signed with the disposable
  key. A clean OSTree client with only that public key requires both commit and
  summary GPG verification. Public descriptors embed the exported public key.
- The public snapshot has a signed manifest and strict paths/resource bounds.
  Publication refuses missing/modified/unlisted files and private-key material.
  Key directories cannot be included in the public snapshot or diagnostic upload.

See [OSTree commit signing](https://ostreedev.github.io/ostree/man/ostree-gpg-sign.html),
[summary signing](https://ostreedev.github.io/ostree/man/ostree-summary.html) and
[Flatpak repository guidance](https://docs.flatpak.org/en/latest/hosting-a-repository.html).

## Proposed authorized production release procedure

This is a design for later approval, not permission to execute it during P5B.

1. Approve an immutable source, successful CI run, version/channel and exact artifact
   digest. Recheck artifact eligibility and exported-payload audit. If expired or
   changed, require a newly approved CI candidate; never choose the latest artifact.
2. Independently review release notes, existing redistribution-license limitations,
   schema compatibility, backup requirements and approved hosting configuration.
3. Transfer only audited public candidate bytes/metadata to the owner signer.
   Verify digests using the reviewed authorization record, not only the download.
4. Sign commits and summary with the approved signing identity. Record the primary
   and signing-subkey fingerprints, CI/run/source, authorization, artifact/OSTree
   hashes, target and publication result. Keep the production secret off CI.
5. Independently verify the signed repository with a clean keyring; exercise
   incorrect-key/tamper/missing-object failures before publication authorization.
6. Obtain separate production publication approval. The approved future publisher
   receives only signed public content and scoped upload credentials, never a
   private signing key. Validate destination objects before metadata activation.

The current workflow does not implement this production step. It has only read
permissions and a protected **disposable staging** job. It cannot create releases,
production tags or upload a public repository. A review-only GitHub Releases plan
can be generated; it is not a release API call or an alternative approval path.

## Backup, recovery, rotation and compromise

After production custody approval: create encrypted offline primary/revocation and
signing-key backups, retain copies in physically separated owner-controlled places,
record fingerprints and expiry, and test restoration using an isolated signer.
Never store the only recovery copy on the CI runner or hosting account. Do not paste
private keys, passwords, revocation material or recovery secrets into chat.

For planned rotation, authorize the new key, publish its fingerprint through an
independently authenticated channel, and test a transition retaining old clients.
Cross-signing/overlapping trust or explicit public-key import must be tested before
retiring the old signer. Expiry, revocation and stale cached metadata are distinct
cases. P5B's local staging publisher intentionally rejects unexpected trust-anchor
changes; an untested automatic production rotation is not implemented.

For suspected compromise: stop publication; revoke upload/session credentials;
preserve evidence; notify owners through an independent channel; determine affected
commits; authorize replacement signing identity and clean infrastructure; verify
new candidates and distribute the new trust anchor out of band. A new key signed
only by a compromised key is insufficient trust bootstrap. Preserve known-good
signed snapshots and state the exposure honestly; do not delete history to hide it.

A lost key requires the documented backup/rotation path. Hosting outage requires a
verified mirror/URL transition, not disabling signature verification. A bad binary
requires a reviewed signed replacement or compatible rollback. Binary rollback does
not roll back SQLite schema/data: P3 backup and restoration controls remain authoritative.

## Verification status

Real disposable GPG signing, correct/wrong key and tampered-message/signature checks
are automated. Publication interruption/retention tests use real signatures over
synthetic repository files and are labeled models. The owner Ubuntu procedure now
provides native PASS for signed OSTree generation, wrong-key/tampered-summary/
missing-object/unexpected-ref rejection, native flatpakrepo validation and interruption
protection. The retained active generation's manifest signature and every file hash
were independently checked; disposable key homes are absent. Evidence and review
are in `evidence/p5b/owner-native-2026-10-31/`. Historical Codex O_TMPFILE failure is
preserved. Eligibility is PINNED REPLAY, not live/hosted P5B verification. Protected
hosted workflow execution remains unverified and requires separate authorization.
No production key ceremony is needed to close the disposable-native signing gate.
