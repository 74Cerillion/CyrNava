# P5C — Integrated Release Pipeline Verification report

**1 November 2026 — P5C — LOCAL PASS / READY FOR HOSTED VERIFICATION.**

Local implementation and disposable native verification are complete. At the
local verification checkpoint, P5C had
not executed on GitHub and was not formally accepted. No commit, push, dispatch,
registration, settings change, tag, application rebuild, real-data migration,
production key, public endpoint, deployment or release was performed.

## Baseline and identities

The integration branch was clean before implementation. Initial and final
independent readbacks match local/remote HEAD
`182d11dbcddc90670fc02e19e6156dc220074dd1`. Main remains
`1e62cd5ef4d36d048a505e9e4a7029296edfd3da`, with inert P5B registration.
The local `p5a-accepted` tag still resolves to `1a28f68`. Historical failures and
accepted P5A/P5B evidence remain unchanged.

| Identity | Accepted value |
| --- | --- |
| P5B tooling / hosted staging | `3ea472efcd6c3338debe16161de601286a5f177d` / `41265875118`, attempt 1 |
| Application source | `1ee2077b283b8e5dfc2162119dd439ed3baeb109` |
| P5A CI / artifact | `41181510439` / `13035607417` |
| Artifact ZIP SHA-256 | `73e6d58a91ff2e57ca7b801b120ca61eceb399202349345508b8fbf6ce4eba6b` |
| Application bundle SHA-256 | `93957ce5590818e016c5b9e86ed9c6c1d32a684f6c644af44531c316020b26db` |
| Installed OSTree commit | `da1bf73e3169096522f82249b39f9c9c8546b0317ee6461905bbc6952d6de1ac` |
| Application / version / schema | `io.github._74Cerillion.CyrNava` / `0.1.0` / `5` |

The artifact was retrieved through the connected GitHub service and independently
hashed. Current recorded metadata reports it unexpired, expiring **7 November
2026 at 07:53:28 UTC**. Recheck immediately before hosted authorization; expiration
must fail closed, never cause silent substitution. Local execution is explicitly
**PINNED REPLAY**, not a new hosted eligibility result.

## Architecture and exact changes

P5C reuses accepted P5B approval, live eligibility, artifact extraction and payload
audit, exact historical Git checkout, disposable signing, signed summary/commit
checks, descriptor validation, manifest sealing and atomic retained generations.
Existing `core.py`, `stage.py`, `github.py`, release policy/workflow/contract and
application source are unchanged. There is no second publisher/signing system.

The supervisor calls accepted primitives directly, then adds an actual Flatpak
client and separate synthetic update fixture. Source, artifact, CI, tooling,
runtime and signing identities remain distinct. The reused release record retains
its P5B reference-workflow field. A **signed `integration-provenance.json` sidecar**
binds the distinct P5C workflow definition and execution identity. Local evidence
records uncommitted candidate code hashes over `182d11d`; the baseline commit is
not misrepresented as containing the new code.

All changes are new P5C files:

| File | Purpose |
| --- | --- |
| `ci/release/client.py` | Exclusive private profiles; exact descriptor/key trust; native install/update; deployed identity checks; redacted failure categories |
| `ci/release/update_fixture.py` | Synthetic native A/B generations, restricted loopback server, interruption/retention and negative cases |
| `ci/release/integration.py` | Integrated replay/live supervisor, signed provenance, disk budget, signal/error handling, cleanup and atomic diagnostic export |
| `ci/release/readiness.py` | Accepted-lock inventory, bounded advisory lookup, review-only candidate/tag/release plan |
| `ci/release/integration_policy.py` | Exact proposed workflow and immutable owner/ref/tooling/environment checks |
| `ci/release/test_integration.py` | 23 deterministic regression tests |
| `ci/release/p5c-workflow.yml` | Proposed manual workflow outside `.github`; not registered |
| `ci/release/p5c-workflow-contract.json` | Exact semantic contract for the proposal |
| `ci/P5C_PLAN.md`, `ci/P5C_REPORT.md`, `ci/P5C_OWNER_CHECKS.md` | Criteria, results, owner gates |
| `ci/evidence/p5c/` | Baseline, advisory review, safe results, independent verification and checksums |

Clients use fresh, owned, mode-0700 marker-protected roots. Every Flatpak command
uses `--user`, isolated `FLATPAK_USER_DIR`, GnuPG, temporary and XDG directories.
Client commands inherit no HOME, session bus, GitHub token or owner configuration.
The accepted application installs through its generated `.flatpakref` from the
private filesystem repository; its deployed commit and `build-inputs.json` source
SHA are checked. No app is launched or owner workspace accessed.

Updates use the distinct `io.github._74Cerillion.CyrNava.P5CFixture` identity and
HTTP bound only to `127.0.0.1`. A/B are tiny signed synthetic releases using the
same publisher primitives, **not a real application version/schema upgrade**.

## Local verification

Final native execution used a fresh, full-history public remote checkout at the
accepted baseline, with new files overlaid byte-for-byte. Two independent fresh
Python 3.12 environments installed unchanged `ci/requirements.lock` with
`--require-hashes --only-binary=:all:`. Both passed `pip check` and exact workflow
policy validation. No development-installed packages or preexisting local Git
objects were required in the fresh checkout.

| Check | Actual result |
| --- | --- |
| New deterministic P5C tests | **23 PASS** |
| Complete release regressions, including those 23 | **96 PASS** |
| Existing CI workflow contracts | **31 PASS** |
| Ruff across `ci`; new-module formatting; pinned actionlint proposal check | **PASS** |
| Final accepted-artifact/native install/source replay | **PASS**, 144.79 seconds |
| Synthetic native update/failure checks | **13 PASS** |
| Independent signed manifest/provenance and diagnostic hash checks | **PASS** |
| Private-key cleanup before final success | **PASS** |
| Hosted P5C jobs / hosted native parity | **NOT EXECUTED** |
| Runtime download / application launch / cross-machine upgrade | **NOT TESTED** |

Existing application/backend/browser suites were not unnecessarily repeated:
there are no application, API, CSS, schema, packaging-permission or accepted CI
workflow changes. Their accepted historical results remain historical evidence,
not new P5C runs.

New tests cover isolation/markers/symlinks, credential redaction, descriptor
capabilities and key identity, both GPG verification flags, commit/deployment
mismatches, diagnostic whitelist/atomic failure, complete failure records,
dependency-setup failure before processing, partial-key cleanup/cleanup failure,
existing output preservation, insufficient disk before signing, every job's
dependencies/history, unauthorized workflow identities, partial SBOM coverage and
unavailable/paginated advisory responses. Accepted source/artifact/security tests
remain in the full 96-test suite.

The 13 native checks prove install A; interruption leaves A installable; existing
client update to B; object retention; unsafe recovery/object deletion rejection;
stale expected commit rejection; independent wrong fingerprint/native wrong key
rejection; tampered/unsigned summary rejection; missing-object native rejection;
and preservation of installed B after faults. Faulted repos are separate fixtures.

### Final native evidence

`evidence/p5c/local-final-2026-11-01/result.json` is the final execution record.
Its candidate code hashes match development and clean-checkout files. Independent
verification checked all **5,559 signed manifest entries**, native GPG signature,
P5C sidecar, diagnostic hashes and absence of disposable private-key homes.

- Disposable signer: `EF0051362978E5032D912C311BC0EFA9A99067F6`.
- Repository: **301,341,806 bytes; 5,554 files**; static deltas disabled.
- Synthetic A: `0ab6b1642973ee07ee6ace530df5da7edd715da6efdfbb596163880d639d1d00`.
- Synthetic B: `efb7657d26a6ee62f31c454f2f7b58a5791cad8bd3d732ccba178d853504871f`.
- Native tools: Flatpak 1.16.6, OSTree 2025.7, GnuPG 2.4.8.

The constrained environment emitted bubblewrap namespace warnings during native
deployment, while installation returned zero and deployed identities were
independently verified. No sandbox flags were disabled. This proves installation
and commit/source identity, **not application execution or desktop sandbox launch**.
`--no-deps --no-related` deliberately prevented runtime downloads.

## Environment parity and diagnostic safety

The proposed Ubuntu 24.04 workflow has independent full-history immutable
checkouts, `persist-credentials: false`, independent hash-locked Python installs
and public apt Flatpak/OSTree/GnuPG tools. Hosted native versions differ from
this environment: actual hosted parity remains a gate. Faults handle classic
`summary` and optional indexed `summary.idx` metadata.

Probing established concrete preconditions: fixtures require `build-finish`; GPG
requires private writable TMPDIR/GNUPGHOME; agent sockets require short paths;
indexed summaries must also be corrupted for a valid negative case. Flatpak can
hide a bad signature behind a missing-ref error, so OSTree independently verifies
the same isolated remote before classifying it. Initial probe failure is retained
in baseline evidence, never relabelled PASS.

Use a fresh output root at most 48 bytes long; the proposal uses `$RUNNER_TEMP/p5c`.
The conservative preflight reserve was **8,268,348,064 bytes**, with
**51,879,219,200 bytes** available before native work. This reserve is not a measured
peak. Local test TMPDIR used the large filesystem outside the clean checkout,
not the 4.4-GiB temporary mount. No dependency/version pin was changed.

Only `result.json`, `eligibility.json`, `readiness.json` and `SHA256SUMS.json` may
be exported. JSON/size/symlink checks and atomic diagnostic-directory activation
prevent partial success exports. Repositories, packages, traces, environment
dumps and private-key homes are excluded. Native stderr/unknown exceptions are
redacted. SIGINT/SIGTERM and setup failure produce FAIL records where technically
possible; SIGKILL/power loss cannot guarantee finalization. Cleanup failure
overrides success. Evidence contains public metadata, synthetic identities/paths
and results; raw artifacts/profiles remain outside source or ignored outputs.

## Release-candidate assessment

`readiness.json` proposes `0.1.0-rc.1` / `v0.1.0-rc.1` targeting accepted source,
without changing application version/schema or creating a tag/release. Accepted
release notes exist; their checksum, bundle and lock checksums are recorded.
Source/auditor/payload/runtime provenance is verified; **byte-for-byte
reproducibility is not verified**.

The CycloneDX-shaped source-lock inventory has **340 components**, including
build/dev dependencies and Python runtime wheel hashes. It is not a complete
shipped-product SBOM: KDE/PySide/native transitive libraries, generated bundles
and file-level license coverage remain outside scope.

OSV queries completed for 340 components, finding `minimatch@10.2.6` /
`GHSA-g3hv-75wg-m249`. The accepted lock marks it and its direct requiring
ESLint/TypeScript tooling as dev dependencies. That is not proof of
non-reachability or absence from generated bundles. The finding remains
**UNRESOLVED**; accepted pins are unchanged. The upstream advisory describes
pattern-amplification denial of service and identifies 11.0.1 as patched:
<https://github.com/advisories/GHSA-g3hv-75wg-m249>.
Unavailable, malformed or paginated responses become INCOMPLETE, never clearance.
The proposed hosted command leaves advisory queries optional; this scan must be
reviewed/refreshed before production authorization.

Code/logo redistribution approval remains pending (`LicenseRef-proprietary`);
metadata-only CC0 grants no code/logo rights. Notices do not establish distribution
clearance. Runtime pins require upstream-support/advisory/update policy. Retain
all exposed objects until a separately reviewed retention/GC policy exists;
binary rollback does not reverse database schema upgrades. Offline owner signing
and future R2-compatible hosting remain directions, not provisioned capabilities.

## Reproduction and proposed hosted integration

From repository root, using a fresh hash-locked Python environment and writable
TMPDIR outside source:

```bash
python -m unittest discover -s ci/release -p 'test_*.py'
python -m unittest discover -s ci -p test_ci.py
python ci/release/integration_policy.py
actionlint ci/release/p5c-workflow.yml
```

The completed native command used clean-checkout `integration.py`, fresh job
Python, pinned archive, `--output /home/cerillion/.cache/p5c/n2`,
`--diagnostics /home/cerillion/.cache/p5c/d2` and `--advisories`. Existing outputs
are intentionally refused. No extra owner-native run is needed to substitute
for unavailable capabilities: required isolated native operations executed here.

The workflow is **not installed**. It would be reviewed/copied exactly to
`.github/workflows/p5c.yml` in a separately authorized integration commit, then
pass ordinary CI before hosted authorization. It is manual-only, owner-only,
read-only contents/actions, immutable action pins, exact integration branch,
existing single-maintainer `p5b-staging` gate and no production secrets/publication.
Inputs bind the future immutable tooling SHA and
`P5C-owner-authorized-disposable-integration-only`; accepted source/artifact are
pinned in existing policy. Changed workflows, retry attempts, unclean checkouts,
unauthorized identities/refs and unavailable artifacts fail closed.

Default-branch manual registration needs a separate reviewed **inert P5C
registration proposal and authorization**, following the P5B pattern. Main and
existing release registration are unchanged now. Never dispatch the inert main
file or reuse a P5B authorization. Only diagnostic JSON with seven-day retention
would be uploaded, never a signed application repository or private key.

## Remaining gates and recommendation

1. Owner review of files, unresolved advisory and exact workflow proposal.
2. Separate authorization for workflow preparation and integration commit/push;
   ordinary CI must pass the resulting immutable tooling commit.
3. Separate authorization for inert main registration if needed and exactly one
   hosted P5C dispatch, after fresh branch/environment/artifact readback.
4. Actual hosted dependency/history/native install/update/cleanup/diagnostic
   gates and independently verified hosted hashes/provenance.
5. Formal owner acceptance. Production keys, licensing, hosting/publication and
   P6 remain separately gated.

**Recommendation: locally ready for review and the next bounded authorization;
not yet ready for formal acceptance or production release.**


## Authorized integration commit checkpoint — 1 November 2026

The owner subsequently approved one P5C-only implementation commit and one normal
fast-forward integration-branch push from `182d11d`. The reviewed proposal is now
installed byte-for-byte as `.github/workflows/p5c.yml`; its definition SHA-256 is
`62d81a27185e329a0aca14a10e1a1441f6f91572b3f9e61cbd293e0bb8f9e576`.
The executable paths remain `ci/release/integration_policy.py` and
`ci/release/integration.py`, with both jobs independently installing the existing
hash-locked requirements and fetching full history without retained credentials.

This installation is limited to the integration branch. It does not authorize
main registration, P5C dispatch, retries, environment changes or publication.
The existing manual-only trigger means the authorized push should run ordinary
CI only. Post-push results will be appended locally from actual hosted evidence;
no CI success is inferred before that execution. The unresolved minimatch advisory
and all documented SBOM/licensing/runtime/launch/upgrade limitations remain intact.
