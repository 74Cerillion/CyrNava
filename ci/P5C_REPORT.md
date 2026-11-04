# P5C — Integrated Release Pipeline Verification report

**1 November 2026 — P5C — ACCEPTED / COMPLETE.**

The owner formally accepted P5C against implementation commit `bfa0b80`, hosted
run `41287523702` attempt 1, workflow `403379040` and diagnostic artifact
`13074794320`. All required technical gates passed. The existing P5A and P5B
acceptance decisions remain unchanged. P6 is the next milestone and remains
pending separate authorization. The formal acceptance record is
`ci/evidence/p5c/formal-owner-acceptance.json`.

**Latest hosted result:** the one owner-authorized manual integration execution,
`41287523702`, attempt 1, completed SUCCESS at tooling commit
`bfa0b8005a3ddc519354fd7907e9b972fde8126b`. Eligibility, staging, native client and
all 13 synthetic update/failure checks passed. The exact four-file diagnostic
artifact, its hashes and run/code/source provenance were independently checked.
Formal owner acceptance has now been received; no production release or P6 is authorized.

**Historical ordinary CI checkpoint:** the authorized implementation commit
`bfa0b8005a3ddc519354fd7907e9b972fde8126b` is synchronized. Run `41285343063`,
attempt 1, passed every required ordinary-CI gate. Independent artifact checks
also passed. At that checkpoint the manual P5C workflow had **zero executions**.
The later Authorization A/B results are recorded at the end of this report.

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

## Local verification — before hosted execution

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

At the original local-verification checkpoint the workflow was **not installed**.
The subsequent authorized commit installed it exactly at
`.github/workflows/p5c.yml` and passed ordinary CI before any hosted authorization.
It is manual-only, owner-only,
read-only contents/actions, immutable action pins, exact integration branch,
existing single-maintainer `p5b-staging` gate and no production secrets/publication.
Inputs bind the owner-approved immutable tooling SHA and
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
The manual-only trigger caused the authorized push to run ordinary CI only.
Actual post-push results are recorded locally below. The unresolved minimatch advisory
and all documented SBOM/licensing/runtime/launch/upgrade limitations remain intact.

## Hosted ordinary CI — 41285343063, attempt 1

The single authorized commit `bfa0b8005a3ddc519354fd7907e9b972fde8126b` has parent
`182d11dbcddc90670fc02e19e6156dc220074dd1`. The normal fast-forward push succeeded.
The remote integration ref was independently read back at that exact commit.
Main remains `1e62cd5ef4d36d048a505e9e4a7029296edfd3da`, default branch `main`;
its inert P5B registration file still hashes to
`3a8c4ad86f958dc7d437c5ee4e5ad2ac57d8753cc4429252edc0005bf385c7c5`.
The local `p5a-accepted` tag and accepted release/source/artifact policy are unchanged.

Actual execution: [GitHub Actions 41285343063](https://github.com/74Cerillion/CyrNava/actions/runs/41285343063),
push event, ordinary workflow `402398273` / `.github/workflows/ci.yml`, started
1 November 2026 at 07:34:45 UTC; completed SUCCESS at 07:47:05 UTC.

| Required hosted gate | Actual result |
| --- | --- |
| Workflow validation | PASS — all 31 contracts |
| Backend/security/lifecycle/migration/packaging | PASS — 663 tests and 197 subtests |
| New P5C regressions within hosted backend JUnit | PASS — all 23 cases independently checked |
| Frontend unit tests | PASS — 273 |
| Browser integration tests | PASS — 21; zero failures/errors/skips |
| Pinned runtime provisioning and production Flatpak build | PASS |
| Exported package-content audit | PASS |
| Validated unsigned artifact upload | PASS |
| Final CI required job | PASS |
| Overall ordinary workflow | SUCCESS, attempt 1 |

All four uploaded ZIPs were independently downloaded and matched GitHub's exact
size and SHA-256. The package has artifact ID `13075346402`:

- ZIP: 210,239,212 bytes, SHA-256
  `2d11ce5057ae66cd4dc526dac607a2344b89dbc1fcef5e62038ad59583c93fbe`.
- Bundle: 209,190,752 bytes, SHA-256
  `ef732c240d8a01e33a638cd10e83fb985c7ba9e678b573ba508cd48c3934f47c`.
- OSTree commit:
  `f759380dca9aa36e4674ad6dffb24d3e2340342da5fe04537ac17031a3bada15`.
- 5,320 payload entries; 980,984,007 logical installed bytes.

Independent checks crossmatched bundle bytes against SHA256SUMS, build result,
provenance and hosted audit; source against `bfa0b80`; run/attempt against
`41285343063`/1; runtime locks and packaging-tool hashes against source. The
audited inventory excludes the CI/release harness. This is independent downloaded
byte/metadata verification plus the actual hosted exported-bundle audit; no second
local native import, launch or signing rehearsal is claimed.

**This new ordinary-CI artifact does not replace the pinned P5A source/artifact
for the future P5C rehearsal.** Those remain source `1ee2077`, CI `41181510439`,
artifact `13035607417` and their unchanged accepted hashes.

Evidence is in `ci/evidence/p5c/hosted-ci-41285343063/`: sanitized run/job metadata,
safe log excerpts, test JSON/JUnit, new-case verification, downloaded package
metadata, all-artifact checksum verification, and final branch/workflow readback.
Raw ZIPs, package binaries and unnecessary browser traces remain ignored outputs.
GitHub's full run listing contained 18 executions and **zero P5C workflow runs**.
The installed P5C workflow remains byte-identical to the proposal, manual-only,
read-only and protected by owner/ref/tooling checks.

These report/checklist/evidence updates are **local and uncommitted** after the
one authorized commit/push. No additional commit, push, rerun, dispatch, main or
environment change occurred.

## Prior owner authorization checkpoints — completed subsequently under A/B

Ordinary CI is now complete. An owner-reviewable inert registration proposal is
prepared at `ci-output/p5c-main-registration-proposal.yml`, SHA-256
`a2bcc41f15785fe35c105b412ca694d8e8acad71933b168f47e9272ad6456bc9`.
It passes actionlint, retains the two reviewed workflow_dispatch inputs and
read-only contents/actions permissions, and has only a registration job with
unconditional `if: ${{ false }}` and a no-op step. It contains no checkout,
integration code execution, signing, credential handling or publication.

1. **Separate authorization requested:** install only that inert file as
   `main:.github/workflows/p5c.yml`, preserving every existing main file and
   history, using a separately reviewed single registration commit/normal push.
   No main action is authorized or performed by this proposal.
2. **Later separate authorization required:** after registration is verified,
   initiate exactly one manual P5C run on the integration branch at immutable
   tooling commit `bfa0b8005a3ddc519354fd7907e9b972fde8126b`, with fresh
   branch/environment/artifact preflight. No dispatch has been initiated.

P5C remains **LOCAL PASS / READY FOR HOSTED VERIFICATION**, not formally accepted.
The unresolved advisory and existing SBOM, licensing, runtime download,
application launch and real-upgrade limitations remain unchanged. Production
publication and P6 remain outside scope.

## Authorization A — inert main registration verified

The owner separately authorized one registration-only main commit and push.
Commit `4021bc292267c19b7ebebf219b4f682f8f99bf4c` has the exact approved parent
`1e62cd5ef4d36d048a505e9e4a7029296edfd3da` and adds only
`.github/workflows/p5c.yml`. Source and GitHub-readback SHA-256 both equal
`a2bcc41f15785fe35c105b412ca694d8e8acad71933b168f47e9272ad6456bc9`.
The file is inert: manual trigger, two exact inputs, read-only contents/actions,
one literal-false registration job and a single `:` no-op. The executable
integration workflow was not copied to main. Existing P5B registration and
integration ref remained unchanged. GitHub registered workflow **403379040**;
zero executions were verified before Authorization B.

The independently verified registration record is preserved at
`ci-output/p5c-main-registration-a/evidence/result.json`. No registration work
was repeated under Authorization B.

## Authorization B — actual hosted integration PASS

[GitHub Actions run 41287523702](https://github.com/74Cerillion/CyrNava/actions/runs/41287523702),
**attempt 1 — SUCCESS**, is the sole P5C execution. It was submitted once through
GitHub CLI authenticated as `74Cerillion`; GitHub independently reports that same
actor and triggering actor, repository `74Cerillion/CyrNava`, workflow ID
`403379040`, path `.github/workflows/p5c.yml`, and execution branch
`desktop/p2-production-integration` at immutable tooling SHA
`bfa0b8005a3ddc519354fd7907e9b972fde8126b`.

Inputs were exactly the approved tooling SHA and
`P5C-owner-authorized-disposable-integration-only`. The accepted application
remained source `1ee2077b283b8e5dfc2162119dd439ed3baeb109`, CI `41181510439`,
artifact `13035607417`, ZIP SHA-256
`73e6d58a91ff2e57ca7b801b120ca61eceb399202349345508b8fbf6ce4eba6b`.
No newer ordinary-CI artifact was substituted and no application was rebuilt.

### Live preflight and jobs

The preflight independently checked both remote refs, inert main hash, registered
workflow identity/zero prior executions, exact executable contract, successful
ordinary CI on the approved tooling SHA, full accepted-source ancestry and live
P5A eligibility/artifact identity. The actual `p5b-staging` configuration had one
branch-only rule for the exact integration branch, no tags/reviewers/additional
approval protections, and zero environment secrets/variables. Repository Actions
secret/variable counts were also zero. No secret values or tokens were logged.

Both independent jobs used full-history immutable checkouts without persisted
credentials and installed unchanged hash-locked PyYAML 6.0.3 dependencies. The
standard Ubuntu 24.04 runner, native apt tools, short private temporary roots,
space guard and whitelist-only export matched the reviewed contract. GitHub's
[runner reference](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)
documents the public runner's storage baseline; actual measured free space is
recorded below rather than inferred from that specification.

| Job / gate | Actual result |
| --- | --- |
| Eligibility, job `124791747445` | PASS |
| Staging, job `124791783403` | PASS |
| Independent hash-locked dependencies / full historical source checkout | PASS |
| Accepted artifact download/hash/payload audit and exact source binding | PASS |
| Disposable signing, signed repository and P5C sidecar verification | PASS |
| Real isolated `.flatpakref` install and installed source/commit checks | PASS |
| Synthetic A install and existing-client A → B update | PASS |
| Historical-object retention and interrupted activation protection | PASS |
| Independent bad fingerprint / native wrong-key rejection | PASS |
| Tampered and unsigned metadata / missing-object rejection | PASS |
| Stale expected commit / destructive recovery rejection | PASS |
| Existing B installation preserved after negative tests | PASS |
| Private-key cleanup before final success | PASS |
| Safe diagnostic export/upload | PASS |
| Independent diagnostic hashes, run identity and code/provenance binding | PASS |
| Overall workflow | SUCCESS, attempt 1 |

### Native identities and measurements

The actual installed application commit is
`da1bf73e3169096522f82249b39f9c9c8546b0317ee6461905bbc6952d6de1ac` and its deployed
source identity is the exact accepted `1ee2077` SHA. Every positive client
operation returned zero; hosted client operations recorded no namespace warnings.
Runtime fetching remained disabled and the application was not launched.

- Actual disposable signing fingerprint:
  `D4525F36925F5347BD2CF807C9A1218FD4870ED9`.
- Synthetic generation A:
  `b174c44982a1ef04764e38bc8bdbe077740dcbb6f6b6e1c6e341f46027eea626`.
- Synthetic generation B:
  `1ea2b6d2b8cbe1a92a53b95d034cf96ae033eaeb838ace8e01d8b45353d08564`.
- All **13** update/failure checks PASS; transport was `127.0.0.1` only.
- Total integration: **166.158 seconds**; repository generation **134.263 seconds**;
  sign/summary operation **0.223 seconds**.
- Measured free space before native work: **91,248,566,272 bytes**; conservative
  required reserve: **8,268,348,064 bytes**.
- Three repository refs: accepted application, `appstream/x86_64` and
  `appstream2/x86_64`; static deltas disabled.
- Actual native versions: Flatpak **1.14.6**, GnuPG **2.4.4**. The approved
  diagnostic records OSTree's first version-output line (`libostree:`), not its
  complete version. The native operations themselves passed on the hosted runner.

The approved four-file format does **not report hosted repository total bytes or
file count**. Those measurements are unavailable; earlier local measurements are
not substituted. This is a reporting limitation, not an unexecuted native gate.

### Independent diagnostic and provenance verification

GitHub uploaded exactly one artifact, ID **13074794320**, named
`p5c-integration-diagnostics-bfa0b8005a3ddc519354fd7907e9b972fde8126b-1`:
**12,553 bytes**, ZIP SHA-256
`9c4f87fdc682ee12747b5dacab7da8f915eae73a13741995cebf6a21989bdbc1`.

Its ZIP contains exactly `result.json`, `eligibility.json`, `readiness.json` and
`SHA256SUMS.json`, without extra entries or symlinks. The three inner checksums
match their exact downloaded bytes; the original checksum file is preserved
unchanged. No repository, package, private key, credential or test profile was
uploaded. All 20 candidate code hashes match files in the approved tooling commit.

The independently reconstructed P5C sidecar serialization has SHA-256
`aafcd1e36483eaee88db663c83ff09cc605a7534c10369ef0188c24915d2ae67`, matching the
recorded sidecar. Its source, accepted CI/artifact, bundle hash, tooling SHA,
workflow path/hash, run ID and attempt all match the independently read GitHub
execution. The legacy P5B reference-workflow field remains separately identified.

Native GPG seal/summary/commit checks executed inside the verified hosted code
before installation. Independent post-run checks cover diagnostic bytes,
run/code binding and sidecar hash; a second local GPG replay is not claimed,
because repositories/public manifests/signatures are intentionally outside the
approved diagnostic upload. Private-key cleanup reported PASS before final PASS.

Evidence is preserved in `ci/evidence/p5c/hosted-integration-41287523702/`, including
preflight, exclusive dispatch marker, run/job IDs, original four JSON files,
artifact metadata, safe log excerpts, independent verification and final readback.
Its local evidence checksum manifest is separate from the original uploaded
`SHA256SUMS.json`. All prior local, ordinary-CI and historical failure records remain.

### Final readback, limitations and technical recommendation before owner acceptance

Final readback confirms **one P5C execution, attempt 1, SUCCESS**. Main remains
`4021bc292267c19b7ebebf219b4f682f8f99bf4c`; integration remains `bfa0b80`; default
branch is main. Environment rules and all four secret/variable counts are
unchanged. No commit, push, branch/environment change, second dispatch or rerun
occurred under Authorization B. No production key, credential, public hosting,
application publication, GitHub Release, tag or P6 work occurred.

The optional hosted advisory query was NOT EXECUTED by the exact approved
workflow. This does not clear the existing `minimatch@10.2.6` /
`GHSA-g3hv-75wg-m249` finding; it remains **UNRESOLVED**. The inventory remains a
partial 340-component source-lock inventory. Complete runtime/native SBOM,
redistribution licensing, application launch, runtime downloads, a real
application upgrade and byte-for-byte reproducibility remain outside the proven
claims. Production capabilities remain disabled.

**P5C STATUS: PASS — READY FOR FORMAL OWNER ACCEPTANCE.**
All required hosted verification gates passed. Formal owner acceptance is the
remaining phase gate; this technical result does not itself authorize further
commits, pushes, executions, production publication or P6.

## Formal owner acceptance and P5C closeout — 1 November 2026

**P5C — ACCEPTED / COMPLETE.** The owner reviewed the technical assessment and
independently verified hosted results, then explicitly accepted every required
P5C technical gate. This decision supersedes the earlier recommendation to seek
formal acceptance; earlier checkpoint classifications and original evidence are
preserved as historical records rather than rewritten.

| Accepted identity | Value |
| --- | --- |
| Implementation commit | `bfa0b8005a3ddc519354fd7907e9b972fde8126b` |
| Hosted integration | `41287523702`, attempt 1, SUCCESS |
| Registered workflow | `403379040`, `.github/workflows/p5c.yml` |
| Accepted application source | `1ee2077b283b8e5dfc2162119dd439ed3baeb109` |
| Accepted P5A CI | `41181510439` |
| Verified P5C diagnostic artifact | `13074794320` |
| Diagnostic ZIP SHA-256 | `9c4f87fdc682ee12747b5dacab7da8f915eae73a13741995cebf6a21989bdbc1` |

Accepted scope includes source/artifact provenance, disposable signing, signed
repository verification, real isolated installation, installed source identity,
all 13 synthetic update/security checks, object retention, interrupted publication,
key cleanup and diagnostic integrity. P5A and P5B acceptance remain unchanged.

Acceptance provides no claim or authorization for production application launch,
runtime downloads, real version-to-version upgrades, cross-machine distribution,
complete SBOM/vulnerability clearance, minimatch remediation, redistribution
licensing, byte-for-byte reproducibility, production signing or public publication.
`minimatch@10.2.6` / `GHSA-g3hv-75wg-m249` remains **UNRESOLVED**. Hosted repository
byte/file totals remain **UNAVAILABLE**; no measurement is fabricated or substituted.

The additive formal-owner record binds the decision to hashes of the original
hosted evidence. All preexisting successful, failure and checkpoint evidence files
remain byte-identical. Inert-registration readback records are also preserved in
`ci/evidence/p5c/main-registration-4021bc2/`. The top-level P5C checksum index is
refreshed for the final documentation and additive evidence; original uploaded
and historical execution checksum manifests remain unchanged.

The proposed closeout is documentation/evidence only, described in
`ci/P5C_CLOSEOUT_PROPOSAL.md`. It includes the already-local hosted CI/integration
evidence and the final acceptance record. Nothing is staged, committed or pushed;
the integration branch remains at `bfa0b80`. A documentation commit and any push
require separate owner authorization. No integration merge into main, production
key, hosting, release or production security change is authorized.

**Next milestone: P6 — Distribution, Installation, and Update Validation.**
P6 remains **PENDING AUTHORIZATION / NOT STARTED**. P5C is formally complete.
