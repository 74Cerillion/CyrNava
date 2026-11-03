# P6 release and recovery runbook

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

## Next GUI attempt after r3 exit: review and authorization required

Do not rerun preparation. After separate owner authorization, run the following
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
the entire attempt. This command is proposed only; no r4 execution is authorized
or performed by this documentation.

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
