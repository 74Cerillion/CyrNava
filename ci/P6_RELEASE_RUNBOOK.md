# Current HTTP checkpoint — 2 November 2026

The normal-host namespace probe passed. Candidate-1 is retained BLOCKED at pull-0.
Controlled direct GET proves the pinned signed commit is available; libostree-
identified requests instead receive 403. The responsible HTTP rule/operator is
not established. No dependency or acquisition-driver change is adopted. The sole
current host action is `bash p6_http_diagnostic.sh` from the repository: three small
GETs, no build/install/GUI. Earlier builder commands below are PAUSED pending that
comparison and delivery resolution. See current P6_REPORT.md/P6_OWNER_CHECKS.md.
P6 remains CONDITIONAL; no candidate or release exists.

---

# P6 release handoff — current reduced v0.1 draft, 2 November 2026

**No corrected candidate, authentic release signature or final tag target exists.**
The sole current executable owner handoff is `bash p6_binary_candidate.sh` from the
repository root. It creates a new isolated build attempt and does not launch GUI,
sign, publish, write Git refs or touch normal installations. See the recipe README.
Do not run old historical-runtime/hosting commands retained later in this document.

## Proposed release contents and source binding

After technical gates and the consolidated owner decisions in P6_OWNER_CHECKS.md:

| Release asset | Required content before upload |
| --- | --- |
| `io.github._74Cerillion.CyrNava.flatpak` | Final signed OSTree app bundle; exact approved app source and tested dependency identities |
| `SHA256SUMS` and `SHA256SUMS.asc` | Recomputed for FINAL SIGNED bytes; authentic owner signature, never the unsigned candidate's checksum |
| `CyrNava-release.asc` | Public verification certificate with full fingerprint independently approved/published; no private key |
| `provenance.json` | Final source SHA, packaged-source snapshot/patch correspondence, successful CI, recipe/lock/dependency IDs, installed commit, final bundle hash |
| `THIRD-PARTY-NOTICES` and corresponding sources/source-access arrangement | Actual exported component licenses/notices, exact Qt/PySide/Chromium downstream source/patches, MPL covered sources, attribution issues resolved |
| Release notes and install/manual-update/recovery guide | Supported Ubuntu 26.04 LTS x86_64/GNOME Wayland; observed tests/limitations, no claim of a complete SBOM/reproducibility/future runtime certification |

Proposed public version/tag: **0.1.0 / v0.1.0**. Exact target **UNSET** until the owner
approves a final source commit and CI which actually corresponds to distributed
executable bytes. Do not tag bfa0b800 while shipping its uncommitted corrections.
The candidate records baseline + source snapshot + staged hashes; reconcile those
with final reviewed source rather than claiming it came from an old clean commit.

Keep commit proposals separated: (1) new P6 recipe/lock/provider/security tests and
existing P6 tooling, (2) preserved P5C closeout, (3) actual owner cleanup results if
provided (twenty targets are absent, but no final measurement transcript exists),
(4) documentation/release metadata. No commits/index changes/pushes are made now.
Existing CI source/security/frontend/browser checks remain; its Flatpak job still
uses historical production locks. Propose the smallest reviewed adapter in that
same job for the candidate, without a new pipeline or expanded P5B allowlist.

## Signing and publication — prepare only, no authority to execute

The owner must identify/approve the real production signing fingerprint and custody.
No secret store has been inspected and no permanent/test/rehearsal key is substituted.
Use the owner's separately approved offline signing environment for the exported
commit (`ostree gpg-sign --repo=... COMMIT FINGERPRINT`), verify with ONLY the approved
public certificate in a fresh verification environment, then produce the final
bundle with `flatpak build-bundle --arch=x86_64 --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo --gpg-keys=CyrNava-release.asc REPO FINAL.flatpak io.github._74Cerillion.CyrNava stable`.
Here REPO/COMMIT/FINGERPRINT/FINAL are deliberately unset review parameters, not a
command to execute tonight without signing approval. `build-bundle --gpg-sign` is
an OCI option; it is not substituted for signing the OSTree commit. Do not disable
signature checks. Verify a fresh import/installation against the public key and
final signed commit, then hash FINAL.flatpak and sign SHA256SUMS offline.

Keep one encrypted offline key backup. Record full primary/subkey fingerprints,
expiry, custody and a short revocation/replacement announcement procedure. No server
signer, custom gateway, cloud service or unattended signing automation is required.

After separate final publication approval: create the approved tag/GitHub Release,
upload only the reviewed assets, download those public bytes back into a new client,
verify the authentic signature/fingerprint and final SHA-256, then install from those
exact bytes with normal dependency resolution and verify launch/data/security. Those
public-download checks cannot be PASS before publication. Do not attach unsigned
checksums to a subsequently signed bundle or upload private test/build trees.

## Focused final-package verification — await an actual artifact

Bind the next owner procedure to the new bundle hash/commit; never substitute A/B.
Use an isolated Flatpak installation/profile. Verify normal runtime/graphics
dependency acquisition, actual desktop entry/name/icon and normal launcher, renderer
namespace/seccomp/no-new-privileges evidence, local service/auth/Host-Origin and
navigation/bridge/external-link/file boundaries, clean backend shutdown. Synthetic
folder/rich note/screenshot must show completed upload/Saved and survive offline
restart. Verify one backup/import and incompatible-schema refusal unchanged.
Import may reset browser preferences; observe its NEW baseline before reinstall.

A same-package reinstall verifies reinstall preservation, not an A/B version update.
The old ABI-broken package cannot establish an ordinary successful upgrade. Do not
manufacture a version/schema just for testing. If a real distinct compatible package
or two suitable maintained runtime commits are available, review exact inputs and
perform the relevant supported manual update; otherwise leave that check pending.
A no-op update and restored historical runtime prove neither. A matched 6.11.3 pair
still requires private-symbol inspection and a limited support/maintenance policy.

First install requires network and runtime/graphics downloads: bundles do not include
those dependencies. End users do not need the SDK/BaseApps. Offline editing is a
separate final-candidate observation. Installation/manual update example commands
below were syntax-checked against Flatpak 1.16.6 but remain NOT tested on a corrected
release. `flatpak install --user --bundle --gpg-file=...` must validate real signatures;
ordinary updates use a newly verified signed bundle, not an app update server.
Uninstall without `--delete-data` preserves data; verified backup before changes is
required, and incompatible schema recovery uses the pre-change backup, never a
speculative reverse migration. No production release or clean-client PASS is implied.

Primary references: [Flatpak bundles](https://docs.flatpak.org/en/latest/single-file-bundles.html),
[Flatpak usage](https://docs.flatpak.org/en/latest/using-flatpak.html),
[Qt WebEngine licensing](https://doc.qt.io/qt-6.11/qtwebengine-licensing.html),
[Qt LGPL obligations](https://www.qt.io/development/open-source-lgpl-obligations).

---

# Earlier runbook drafts — historical, not current execution authorization

# P6 v0.1 bundle installation, manual updates and recovery — DRAFT

**2 November 2026: no corrected release candidate or production signature exists.**
P6 remains CONDITIONAL. Follow the current six-gate report/checklist. The historical
repository/gateway/key-rehearsal procedures retained below are not v0.1 prerequisites
or instructions to run them. No production key generation/publication is authorized.

## Release material for the actual final package

Use the existing production packager and unchanged payload auditor. Record source
commit plus exact uncommitted-patch identity if any, manifest/lock/recipe and runtime/
BaseApp/SDK commits, source inventory, bundle SHA-256 and installed OSTree commit.
Do not label accepted A/B archives as the new candidate. Exclude owner data, build
caches and private keys; retain required renderer helper/resources/locales and notices.

Before public redistribution, resolve the original-code license/copyright holder
and logo rights with the owner, actual dependency attribution/notice requirements,
covered-source availability and exact Qt/PySide/Chromium source/patch correspondence.
Existing licensing review is not clearance for a changed payload. Prefer retaining
upstream notices and a reliable exact corresponding-source arrangement over a new
compliance platform. No license or branding-rights decision is invented here.

With the separately approved existing owner-controlled signing identity, sign the
exported OSTree commit before producing the distributable bundle. Independently
verify with only its approved public key; then sign the exact SHA256SUMS offline.
Keep private signing material outside packages/source/diagnostics. No reviewed
production fingerprint is currently recorded; do not use any disposable rehearsal
fingerprint. A checksum, public key file or test signature does not close this gate.

Protect the owner signing key, keep one encrypted offline backup, and record public
fingerprint/expiry and a simple replacement/revocation procedure. No server key,
automatic signing service or production environment secrets are required for v0.1.

## Installation/manual update draft — commands not yet package-validated

The chosen channel is owner-published signed Flatpak bundles on GitHub Releases.
It is a download channel; it supplies no automatic application-update feed.
Required release assets: the signed .flatpak, SHA256SUMS and its authentic detached
signature, independently pinned public fingerprint/key, release notes, notices and
applicable corresponding sources or compliant distribution arrangement.

Flatpak bundles exclude runtime dependencies. First installation needs network
access to the verified runtime source https://dl.flathub.org/repo/ and any graphics
extensions. The SDK/BaseApps are build dependencies, not normal user downloads.
Do not ask users to install the SDK. Normal application editing is offline once
installation completes; test that separately on the final package.

After downloading the **actual approved release** assets into one directory:

```bash
# No release fingerprint is currently approved. Before running this block,
# obtain and verify the owner's full public fingerprint independently.
# Export it as CYRNAVA_RELEASE_FINGERPRINT; do not take it from the same download.
(
set -euo pipefail
: "${CYRNAVA_RELEASE_FINGERPRINT:?An independently verified fingerprint is required}"
cyrnava_verify_home=$(mktemp -d)
chmod 700 "$cyrnava_verify_home"
cyrnava_actual_fingerprint=$(gpg --homedir "$cyrnava_verify_home" --with-colons \
  --show-keys CyrNava-release.asc | awk -F: '$1=="pub" {want=1; next} want && $1=="fpr" {print $10; want=0}')
test "$cyrnava_actual_fingerprint" = "$CYRNAVA_RELEASE_FINGERPRINT"
gpg --homedir "$cyrnava_verify_home" --import CyrNava-release.asc
gpg --homedir "$cyrnava_verify_home" --verify SHA256SUMS.asc SHA256SUMS
sha256sum --check SHA256SUMS
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak install --user --bundle --gpg-file=CyrNava-release.asc CyrNava.flatpak
flatpak info --user --show-commit io.github._74Cerillion.CyrNava
flatpak run io.github._74Cerillion.CyrNava
)
```

The new private verification home contains only the approved public release key;
no personal GnuPG profile or signing key is used. The block stops on any mismatch. These are draft commands,
not an instruction to operate on the owner's normal environment now. Match the
installed commit to the actual release record. Confirm normal application-menu
name/icon/launch separately from flatpak run. No sandbox overrides/disable flags.

For a subsequent verified bundle: close CyrNava, create and validate a backup, repeat
the fingerprint/signature/checksum checks, then use the package manager's update:

```bash
flatpak install --user --or-update --bundle --gpg-file=CyrNava-release.asc CyrNava.flatpak
flatpak info --user --show-commit io.github._74Cerillion.CyrNava
```

CLI option availability was checked with the installed Flatpak; successful clean
installation/update of a new correctly signed candidate is **NOT EXECUTED**. Do not
present syntactic checks as an install PASS. Test real dependency resolution and
new installed commit with disposable persisted data before publishing these as
validated instructions. Reinstalling the same bytes is not proof of an update.
Do not claim an end-to-end old-package update when the old launcher is ABI-broken.

Compatibility boundary: only the actual tested Ubuntu/Wayland/x86_64 and exact
runtime/binding/provider set. Validate ordinary runtime resolution; never restore an
obsolete runtime as a user workaround. When upstream Qt private ABI changes, make
and test a coherent replacement bundle promptly. Do not promise compatibility with
arbitrary future runtimes or claim a runtime-update PASS without an actual tested
commit change with fixed application bytes.

## Recovery

Use Backup and recovery → Create verified backup; keep the .cyrnava archive intact.
For explicit restore, Import backup into a new workspace and wait for Completed and
verified. Backups intentionally exclude browser appearance/localStorage preferences:
a new imported workspace may use the default appearance. Normal restart/update/
reinstall must preserve the selected workspace's actual saved state. Do not unzip
a backup or overwrite the original workspace. Keep the last verified usable data.
An older binary does not downgrade SQLite schema. Refuse unsupported future schemas;
use a separately verified compatible snapshot for recovery. Claim binary rollback
only when that binary/schema/data combination was actually verified.

No cleanup command in this runbook deletes application data; never use --delete-data
for install/update recovery. Preserve safe diagnostics on failure; do not silently
retry or loosen signature/path/sandbox checks.

Primary sources: [Flatpak bundles](https://docs.flatpak.org/en/latest/single-file-bundles.html)
and [Flatpak CLI](https://docs.flatpak.org/en/latest/flatpak-command-reference.html).

## Historical release/rehearsal procedures — superseded scope


**Current compatibility checkpoint — 2 November 2026:** R12's owner-executed
historical-runtime B-only test is independently read back as PASS (two GUI launches,
post-import Light baseline/reinstall, synthetic data and accepted inputs preserved).
Ordinary-runtime compatibility remains FALSE. R9 and R11 remain historical FAIL
records. Do not repeat the historical rehearsal.

The production compatibility assessment is complete; a safe replacement package
has NOT been implemented. See [P6_QT_COMPATIBILITY.md](P6_QT_COMPATIBILITY.md) for
ELF/source causality, four exact-version wheel experiments, options, local tests
and the concrete whole-stack build proposal. Generic wheels omit observed BaseApp
Flatpak renderer-integration markers; host import success does not validate that
security boundary. Accepted manifest/locks/artifacts/security remain unchanged.

Earlier commands/checkpoints below are historical and superseded. Do not run an
old historical-runtime command as the production remedy. The next review is the
source-build feasibility proposal; no native execution is requested/authorized by
this assessment.


Draft local procedure; production is disabled. Never run permanent signing,
hosting, tag or publication steps without separate owner approval.

1. Verify application source, tooling, successful CI and accepted artifact hashes
   independently. Preserve the original P5A identity; no automatic substitution.
2. Review dependency/advisory/runtime support and redistribution obligations.
3. Use an isolated verified candidate, an independently checked public fingerprint
   and owner-controlled offline signing. Never promote disposable rehearsal keys.
4. Validate signed summary, commits, payload, provenance and complete manifest.
5. Dry-run publication; verify complete immutable generation before conditional
   activation. Retain all historical objects. Never synchronize summary and its
   signature with independent mutable PUTs.
6. Verify GET/HEAD, MIME/cache behavior and client operations against the approved
   endpoint. Local loopback tests are not public HTTPS evidence.
7. Clean client: actual runtime retrieval, trusted remote install and identity/
   permissions checks; sandboxed GUI and synthetic persistence.
8. Existing client: verified real A/B update, compatible rollback, backup recovery,
   and uninstall/reinstall retaining private data. Never pass --delete-data.
9. Stop on any integrity failure; keep the previous generation active. Recovery
   activates a complete previously verified snapshot. Do not automatically prune.
10. Only after owner acceptance prepare the separately approved public tag/release.

Never paste keys, tokens or personal notes into evidence. Binary rollback does
not downgrade schema; restore a verified snapshot when an older binary cannot
read a newer database.

## Local verification and owner native procedure

Run from the repository root. These commands do not publish or change normal
Flatpak installations. Use the Python 3.12 verification environment, with the
existing hash-locked `ci/requirements.lock` installed. Owner GUI execution needs
Ubuntu Wayland, Flatpak, OSTree, GnuPG and access to upstream runtime downloads.

```bash
python ci/release/key_ceremony.py --disposable-root "$HOME/.cache/p6/key-rehearsal"
```

This creates ONLY a fixed disposable identity and deletes all private material,
encrypted secret backup and temporary passphrase before reporting success.
The result is local evidence; never promote this public key as production trust.
The supplied root must be new and short enough for GnuPG Unix sockets.

The real-update driver reuses the accepted P4 native assertion script. It uses
the REAL production app ID but a new private HOME, Flatpak installation, XDG
configuration and synthetic data. Only the Wayland socket and session bus are
forwarded for the GUI/portals. It cannot fall back to relaxed sandbox flags.
The synthetic note's required title remains **P4 owner edit**, because those
accepted assertions are reused unchanged.

**Do not execute the next block until the owner approves generation B and an
approved copy of the proposal has `owner_approved_for_disposable_P6_update: true`.**
That approval record must retain the exact proposed hashes; it does not change
the P5A/P5B application-source allowlist or permit publication.

Proposed B uses the already built real P5C application at `bfa0b800…`, ordinary CI
`41285343063`, artifact `13075346402`, version 0.1.0/schema 5. Its distinct commit
changes packaging provenance; no public version is invented. A remains the exact
accepted P5A build. `ci/evidence/p6/real-B-approval-proposal.json` contains the full
identities. Approval for this disposable compatibility exercise does not make B
the final P6 release candidate.

With the two verified artifact ZIPs saved locally as `A.zip` and `B.zip`, and the
owner-approved record saved as `B-approved.json`:

```bash
python ci/release/real_update.py prepare \
  --root "$HOME/.cache/p6/real-pair" \
  --a-archive /absolute/path/A.zip \
  --b-archive /absolute/path/B.zip \
  --b-approval /absolute/path/B-approved.json
python ci/release/real_update.py gui --root "$HOME/.cache/p6/real-pair" \
  --attempt-root "$HOME/.cache/p6/new-gui-attempt"
```

Preparation verifies artifact hashes, exact detached audit sources, exported
payloads, signatures, object retention and both real commit identities. It signs
both generations with one fresh disposable key, then removes the secret home.
No production credential is accepted. GUI execution installs runtimes from the
approved upstream, installs A through its HTTP remote, runs edit/restart, publishes
B locally, updates the existing client, checks B's source, rolls the binary back
to A, verifies native backup/import/recovery and schema refusal, then uninstalls
without `--delete-data` and reinstalls B through the same remote. All phases must
produce complete PASS records. Check `prepared.json`, `owner-result.json` and
`phase-*.json`. Do not post raw profiles, screenshots or package/repository trees.

In the edit window: create a folder; enter the required title; add heading/list/
code formatting; paste a screenshot of ONLY this synthetic workspace; choose Dark;
wait for Saved; close normally. On subsequent windows confirm persistence. In
maintenance, export `p6-backup.cyrnava`, then import the SAME file with the second
button; do not unzip it. Wait for completion after both actions.

Additional owner observations remain manual: launcher name/icon; external-link
navigation restrictions; screenshot file portal; offline editing; startup after
logout/restart; no unexpected processes after normal close. Record these as owner
observations separately from automated native assertions. The streamed native
checker instruments the production shell; a normal uninstrumented launch must
also be reviewed before final acceptance. No current local result proves those.

## Proposed permanent offline key ceremony — NOT AUTHORIZED TO EXECUTE

Use a trusted offline machine, an encrypted removable volume and interactive
pinentry. Review the commands before authorizing permanent creation. Do not run
them in CI, in this repository, or on the disposable rehearsal key home. The
RSA-3072 certificate/signing-subkey layout, encryption and restoration mechanics
have been rehearsed with one-day disposable keys. Proposed production expiry is
two years for the certification-only primary and 90 days for signing subkeys.
Expiry policy and identity UID still require owner approval.

```bash
umask 077
ceremony_root=/media/OWNER_ENCRYPTED_VOLUME/cyrnava-signing
install -d -m 700 "$ceremony_root"
export GNUPGHOME="$ceremony_root/primary"
install -d -m 700 "$GNUPGHOME"
gpg --quick-generate-key 'OWNER-APPROVED RELEASE IDENTITY' rsa3072 cert 2y
gpg --with-colons --list-secret-keys
# Read and independently record the full PRIMARY fingerprint as primary_fpr.
read -r primary_fpr
gpg --quick-add-key "$primary_fpr" rsa3072 sign 90d
gpg --with-colons --list-secret-keys "$primary_fpr"
# Record the full signing SUBKEY fingerprint as signing_fpr.
read -r signing_fpr
gpg --armor --export "$primary_fpr" > "$ceremony_root/public.asc"
gpg --export "$primary_fpr" > "$ceremony_root/public.gpg"
gpg --export-secret-keys "$primary_fpr" | \
  gpg --symmetric --cipher-algo AES256 --output "$ceremony_root/offline-backup.gpg"
gpg --export-secret-subkeys "${signing_fpr}!" | \
  gpg --symmetric --cipher-algo AES256 --output "$ceremony_root/subkey-transfer.gpg"
```

Use distinct strong passphrases entered through pinentry; store recovery
passphrases separately. Do not use `--passphrase ''` for production. Preserve the
automatically generated `openpgp-revocs.d/PRIMARY.rev` on encrypted offline media;
the leading colon deliberately prevents accidental import. Keep at least two
encrypted backups in separate controlled locations. Fingerprints and public keys
may be public; revocation material is controlled until intentionally exercised.

Before relying on a backup, on a second isolated offline home decrypt directly
into `gpg --import` (no plaintext secret file), compare BOTH full fingerprints,
sign a non-sensitive probe with `--local-user "${signing_fpr}!"`, and independently
verify it with a public-only home. Restore the encrypted subkey transfer into the
release-signing home and require `--with-colons --list-secret-keys` to show the
primary secret as a `#` stub. The primary key never leaves offline custody.
After each signing session kill its gpg-agent and unmount the encrypted volume.
The publisher has signed public files only, with separate least-privilege storage
credentials; it must not hold a signing secret. Current tooling deliberately
accepts only marked disposable keys, so permanent signing needs a separately
reviewed owner adapter. These instructions do not enable production signing.

Before subkey expiry, use the offline primary to add a fresh expiring signing
subkey (or deliberately extend an uncompromised one), export the updated public
certificate, verify it independently and rehearse native clients. Monitor both
primary and subkey expiry. Never turn off GPG checks to recover an expired client.
For compromised subkeys, revoke that subkey with `gpg --edit-key`, distribute the
updated certificate and move to a new subkey. For primary compromise, use the
offline revocation certificate and a NEW primary; this is a new trust bootstrap.
Do not authenticate a replacement solely using the compromised key.

For loss without compromise, restore the tested encrypted backup. If recovery is
impossible, halt releases and establish a new fingerprint through independently
authenticated owner channels. Existing installations remain usable; fresh updates
must fail closed until their trust is repaired. Current one-primary validators do
not claim transparent primary rotation. A separately reviewed transition can
authenticate a new certificate using the still-trusted old identity plus an
independent fingerprint check, import it into the exact remote and dual-sign a
transition repository. Test old/new/expired clients before decommissioning old
trust. Keep previous signed objects and verified database backups throughout.

See the [GnuPG key-management manual](https://www.gnupg.org/documentation/manuals/gnupg/OpenPGP-Key-Management.html)
for command semantics. Public-key distribution must include an independent full
fingerprint comparison, not merely a key downloaded from the same endpoint.

## Proposed R2-compatible publication deployment — NOT PROVISIONED

The tested reference adapter is `ci/release/distribution.py`. It uses accepted
P5B signed seals, OSTree validation, file hashes, durable snapshots and retained
generations. Dry-run returns a complete reviewed plan. Activation uses an expected
previous generation under the publisher lock; a stale publisher fails.
No provider SDK, publication credential or external write API is installed.

For an approved object-store provider, implement the same semantics:

1. Private bucket and least-privilege upload identity separate from offline signer.
2. Upload content-addressed objects first into an immutable generation prefix,
   then metadata, seal, signature and provenance. Uploads are invisible to clients.
3. Verify every destination GET hash/size and list against the signed manifest.
   Reject extras, missing objects, invalid refs/signatures and historical deletions.
4. Conditionally replace ONE active-generation pointer using its previous ETag.
   The read gateway resolves complete snapshots. Never overwrite summary and
   summary.sig as independent live objects. No automatic pruning/lifecycle expiry.
5. Serve immutable object hashes with one-year immutable caching; summary,
   signatures, descriptors, active pointers and all 4xx/5xx responses use no-store.
   Disable CDN negative caching, stale-on-error and cache overrides for metadata.
6. Validate GET/HEAD/content length, hashes, MIME types, native client install/
   update, old objects and interrupted readers through the actual approved HTTPS
   endpoint. Validate conditional writes with two simultaneous publishers there.

Snapshot activation is atomic on a single local filesystem; it does not make
multiple client HTTP requests atomic. A client crossing an activation may observe
different summary/signature generations and fail signature validation. Fail closed
and preserve its installed version; do not weaken signatures or promise zero
transient failures. Stale *signed* metadata is also a freshness/rollback issue:
the current P6 verifier pins the expected generation/commit, whereas normal Flatpak
clients do not provide this as a universal anti-rollback policy. Public operation
needs monitored freshness, a reviewed gateway and an operational release window.

R2 offers [strong object consistency](https://developers.cloudflare.com/r2/reference/consistency/),
but caching layers require separate validation. Its [public bucket guidance](https://developers.cloudflare.com/r2/buckets/public-buckets/)
distinguishes custom domains from the rate-limited development URL. The gateway,
domain, access policy, TLS, conditional-pointer implementation and monitoring are
owner-approved deployment work, not capabilities claimed by the local adapter.
No bucket, Worker, DNS or endpoint has been created.

Measured local reference snapshot: **302,485,829 bytes, 5,561 files** including
seal files. At that size, 20 complete retained generations are about 6.05 GB
before provider accounting/deduplication; about 111,220 object uploads. One thousand
full installs are about 5.56 million GETs, plus metadata/HEAD/failed requests and
any repeat downloads. Runtime downloads are supplied separately upstream.

On 1 November 2026 [R2 Standard pricing](https://developers.cloudflare.com/r2/pricing/)
lists $0.015/GB-month, $4.50/million Class A and $0.36/million Class B, free egress,
with monthly allowances of 10 GB, 1 million A and 10 million B. Under an otherwise
unused account those example R2 quantities fit the allowances. This is not a bill
guarantee: rounding, other account use, duplicate requests, more retained releases,
gateway/Workers, domain, monitoring, backup and taxes require a final estimate.
Storage beyond allowances grows with retained history; do not automatically prune
to hit a budget. Prefer Standard over infrequent storage for this small release
repository. Obtain approval of provider, domain, limits and budget before setup.

## Installation and recovery instructions for a future approved public release

Only after the endpoint and production fingerprint are approved: obtain the
public key/descriptor, independently compare its full fingerprint, and use native
`flatpak remote-add --user --from` and `flatpak install --user` with GPG validation
enabled. Inspect `flatpak info --show-commit`, `--show-runtime`, `--show-permissions`
and the exact app ref. Install the official required runtime through its verified
upstream descriptor. Never use `--no-gpg-verify` or a staging key.

Updates use the same named remote and `flatpak update --user APP_ID`. For a
compatible binary rollback, select the previously verified commit using
`flatpak update --user --commit=COMMIT APP_ID`; verify source/runtime/schema
compatibility first. If schemas differ, use P3's verified pre-upgrade backup and
staging restore; no reverse migrations exist. To uninstall while retaining data,
use `flatpak uninstall --user APP_ID` without `--delete-data`. Reinstall from the
trusted remote and verify data. Public endpoint and trust placeholders intentionally
remain unset, so these are not copy-paste production deployment commands.

## Exact cached-artifact owner command after correction approval

Both reference ZIPs are present and independently rehashed. The owner-approved
true-valued record exists at `ci-output/p6-owner/B-approved.json`; its SHA-256 is
`53aa5025f977629cf6ba3920b390493b6da257987663279d7e1e85c28f231a22`.
The original false proposal remains unchanged (SHA-256
`faf402979140916f061ff373ed4400ccd42adbe1d618476994d7bf6165977d85`).

The first preparation at `~/.cache/p6/real-pair` failed because B was sent through
the A-only P5B audit approval check. Preserve that entire directory. The local P6
correction uses a separate exact-owner-approval-bound B audit, retaining the
unchanged payload auditor and security checks. Its focused/related regressions
pass; the corrected native flow has not run.

**Historical preparation procedure (owner completed r2 successfully; do not rerun):**
use a fresh root. If that root exists, stop and select a new reviewed root;
never remove or overlay previous evidence. This is a local pinned replay, not a
CI dispatch, publication or normal Flatpak profile modification:

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
backend/.venv/bin/python ci/release/real_update.py prepare \
  --root "$HOME/.cache/p6/real-pair-r2" \
  --a-archive "$HOME/.cache/p5c/a.zip" \
  --b-archive "$PWD/ci-output/p5c-hosted-41285343063/package.zip" \
  --b-approval "$PWD/ci-output/p6-owner/B-approved.json"
```

Inspect the terminal's final JSON and `real-pair-r2/prepared.json`: require
`status: PASS`, `complete: true`, A/B payload-audit checks PASS, both exact approved
source/OSTree identities, and `disposable_signing_key_removed: PASS`. A failure
must identify its operation; B child failures also retain fixed stage diagnostics
in `p/audit-b/audit-result.json` when the child could initialize. Preserve all
evidence on failure and stop. Do not start GUI from this preparation block.

The owner completed preparation PASS and then interrupted the first GUI command
after about five minutes of prelaunch runtime retrieval. The old r2 client,
owner-result.json and all signed preparations must remain intact. The agent has
not executed preparation or GUI. Cached ZIP use remains PINNED REPLAY.

## Historical r4 GUI execution — do not repeat

The owner authorized and executed this r4 command; it failed at a QtCore import.
Do not execute it again. The following records the historical procedure
from the owner's authenticated Ubuntu Wayland terminal. The prepared pair is a
read-only input; the new attempt has its own empty client/store and results. If
`gui-attempt-r4` already exists, stop rather than deleting or overlaying it.
The existing r3 attempt passed runtime retrieval and A installation but its
host-streamed verifier exited 1. Its stderr was discarded, so the exact cause
remains unresolved. Preserve r3 and the signed pair; no speculative app/security
change or preparation repeat is required.

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
backend/.venv/bin/python -u ci/release/real_update.py gui \
  --root "$HOME/.cache/p6/real-pair-r2" \
  --attempt-root "$HOME/.cache/p6/gui-attempt-r4"
```

Expect `P6` JSON progress lines immediately before runtime retrieval and during
each native operation. Runtime downloads/pinning can take up to the existing
1,800-second bound; ten-second running events show elapsed time and deadline.
Descriptor setup is bounded at 300 seconds. An EDIT instruction and gui-edit
event mark the later launch attempt, after signed A installation/source checks.
No GUI window is expected while runtimes are still downloading.

Inspect `gui-attempt-r4/progress.json`, `operations.jsonl`, `owner-result.json` and
phase records. Ctrl+C must produce an explicit interruption with its operation
and launch-attempt flag; timeout is distinct. Preserve the entire attempt and
stop on failure/interruption. Never infer a Qt/sandbox failure from an interrupted
prelaunch operation. Do not automatically retry or execute another GUI run.

For a nonzero GUI child exit, `owner-result.json` now includes
`native_subprocess_failure` with safe categories, checker hash, Python-bootstrap
stage/exception type/line where available, and private output file basenames.
Raw stdout/stderr tails are kept in `private-subprocess/` (directory 0700, files
0600, at most 1 MiB each). Review them privately on the owner machine; do not paste
or upload them before redaction. Provide only sanitized result JSON as public
evidence. A marker proves only that the Python verifier reached that stage; it
does not establish application-window success. Missing markers leave the
Flatpak/runtime/early-bootstrap cause unresolved. Stop at any failure and preserve
the entire attempt. R4 is now retained failure evidence; this document does not
authorize another execution.

## Current gate: runtime compatibility, not another GUI retry

R4's retained stderr confirms `QtCore.abi3.so` cannot resolve
`QObjectPrivate::QObjectPrivate(QtPrivate_6_11_2)` from active Qt 6.11.3. Runtime
retrieval verified commit `76fa01ac…`, but normal dependency installation of A
left `fb23e178…` active. The local P6 guard now checks the exact runtime after
installation and before each native phase; drift is a FAIL before launch.

Preserve r2, r3 and r4. Do not rerun preparation, edit their runtime deployments,
silently repin, override library paths or upgrade/rebuild packages. The current
change detects drift and leaves compatibility remediation for review. No further
native probe is needed to identify this error. A later import-only validation of
a reviewed remediation must use a new disposable client and an exact separately
authorized command before another full GUI run. No such probe or GUI execution
is authorized or performed at this checkpoint.

## GitHub tag/release plan

Proposed final tag is `v0.1.0`, matching existing version metadata; no tag exists
from this work. Target the final explicitly approved APPLICATION source after
its successful CI/artifact verification, not a later tooling-only commit. The
final target remains unset. After license/trust/endpoint/native/HTTPS gates pass,
obtain separate tag, release-asset upload and publication approval. Prepare
checksums, signed provenance, public certificate/fingerprint, matching notes,
notices/source arrangements, inventory and client instructions from that exact
source. Verify downloaded public bytes and an independent client before announcing
a release. Do not claim reproducibility, full vulnerability clearance or normal
application launch from the current headless/reference evidence.


## Explicit historical policy proposal — 1 November 2026

The owner has authorized local implementation only. See
[P6_RUNTIME_REMEDIATION.md](P6_RUNTIME_REMEDIATION.md) for exact proposed imports-only
and later GUI commands, isolated environment, per-transaction restoration/trust
checks, private diagnostics and stop conditions. Both generations must pass bounded
sandbox imports in the fresh client before any GUI opens. The default remains
strict. A matching version string or a restored historical-runtime PASS cannot be
reported as production runtime-update compatibility. No native execution is
currently authorized by this remediation package.


## R6 ordering diagnosis and next proposed attempt

R6 failed before restoration during the premature full historical signature check;
the normal installation and historical flag propagation succeeded. The corrected
precheck validates origin/GPG policy, then restores the exact approved runtime,
then independently verifies signature and live identity. See
[P6_RUNTIME_REMEDIATION.md](P6_RUNTIME_REMEDIATION.md) for the current **imports-only
r7** command. It requires separate authorization, a fresh root, and stops before
GUI. Proposed GUI r8 remains gated. Preserve r6 and all prior signed inputs.


## Current R9 checkpoint — supersedes earlier next-attempt examples

R7 imports and R9 initial GUI/update/rollback/backup/recovery observations are
preserved as PASS. R9's post-reinstall `updated` check failed while reopening the
profile; its exact missing file was not retained. Read-only inspection confirms
intact workspace data/assets and a valid pointer. The host helper now records
pre-construction stage, safe errno/category/storage source line; the parent labels
reinstall separately. See P6_REPORT.md's R9 investigation and
`ci/evidence/p6/r9-profile-investigation/`.

Stop for owner review. A further native observation requires separate authorization
and a fresh attempt, never reuse or modify R9 and never repeat preparation merely
to collect these diagnostics. The historical r7/r8 command examples are not a new
execution instruction. Normal-runtime production compatibility remains OPEN.


## Current R11 checkpoint — supersedes earlier execution examples

Do not run another full rehearsal. R11's earlier actual phases pass; its final
Dark assertion contradicted the accepted exclusion of browser preferences during
import into separate Qt storage. Final keys are absent/default System; no resolved
scheme or live pre-uninstall sample was retained. Original FAIL evidence remains.

The corrected full-sequence harness keeps Dark/hash checks before import, then
adds a distinct import-reset baseline requiring System followed by an explicit
new Light preference. Final reinstall checks that new preference and all original
security/data assertions. P4's default behavior is unchanged.

See P6_REPORT.md's R11 section for the proposed smaller two-launch B-only
post-import/reinstall test in a NEW verified isolated client. It copies only the
validated synthetic imported workspace, uses fresh Qt storage and never modifies
R11. The targeted entry point/command still needs preparation and review; no
existing `gui` command represents that reduced scope. Do not execute until the
owner separately authorizes the exact fresh-client procedure. Preparation must
not be repeated. Historical replay does not close ordinary runtime compatibility.


## Current targeted-B implementation — 2 November 2026

This supersedes the R11 proposal's earlier statement that no targeted entry point
exists. `ci/release/targeted_b.py` is now locally verified, with a fixed B/R11 policy
and exactly two B GUI launches surrounding one same-B uninstall/reinstall. The
complete `real_update.py gui` command is unchanged and must not be substituted.

The sole current proposed execution procedure is
[P6_TARGETED_B_CHECKS.md](P6_TARGETED_B_CHECKS.md): exact flags, fresh R12 root,
System-before-input evidence, new Light baseline, unmodified reinstall baseline,
identity/runtime/signature/data/security guards and stop conditions. Native has
NOT run. It requires separate owner authorization, at least 5 GiB free (about
1.2 GiB currently), and valid current disposable signing trust. The existing key
expires **2 November 2026 09:32:43 UTC / 18:32:43 KST**. No expiry bypass, clock
change, new signing key, re-signing or preparation repeat is authorized.

Keep R11's original FAIL and earlier actual passing phases, plus R9's unresolved
historical filesystem observation. Successful historical replay must still report
ordinary runtime compatibility FALSE. No commit/push/GitHub execution, production
signing, hosting, publication or real personal-data migration is authorized here.
