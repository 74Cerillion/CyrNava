# P5B report — secure release preparation and disposable staging

**31 October 2026 — CONDITIONAL; not accepted.** Local implementation and available
automated security checks pass. The owner's Ubuntu native staging rehearsal now
passes, including real signatures, rejection cases, descriptors and interrupted
publication protection. Protected GitHub-hosted staging remains unconfigured and
unexecuted. That remaining evidence gap prevents unconditional acceptance.

The owner has accepted native verification and endorsed future R2-compatible hosting
and owner-controlled offline production signing. These are architectural endorsements,
not permission for permanent keys, credentials, hosting purchases or deployment.
The existing implementation is already in commit a9de663; this checkpoint records
one authorized local P5B documentation/review commit. No push or external configuration
change is performed by this session; no production key/release/deployment or P5C/P6 work.

## Accepted baseline and repository state

- Branch: `desktop/p2-production-integration`; starting worktree clean.
- Original P5B starting HEAD/remote: `1a28f68c5732ccc1275403060e89ff168a846655`.
- This commit-review checkpoint started clean at existing implementation commit
  `a9de66384b4b1ae4e5bb47909df1eba7d50468f0`; read-only remote inspection matches it.
  Preserve that history; the authorized follow-up records endorsements and staging
  architecture, without duplicating/rebasing the existing implementation.
- Local annotated `p5a-accepted` points to `1a28f68`, not the later P5B commit. It remains local;
  read-only `ls-remote` found no matching remote tag. No tag was changed.
- Accepted application build: [P5A run 41181510439](https://github.com/74Cerillion/CyrNava/actions/runs/41181510439),
  source `1ee2077b283b8e5dfc2162119dd439ed3baeb109`, attempt 1.
- Live read-only eligibility verification independently checked all five successful
  required jobs, workflow identity/content, source, artifact ID/digest and expiry.
  See `evidence/p5b/live-eligibility.json` and the existing P5A acceptance evidence.
- Application ID `io.github._74Cerillion.CyrNava`, version `0.1.0`, architecture
  x86_64, stable ref and schema 5 remain unchanged.

The accepted CI workflow, exported-payload auditor, production packaging and locks
remain byte-identical. Application sources and Flatpak permissions were not edited.
P5B implementation/native evidence is already tracked in a9de663. Its source hashes
match the tested candidate. `evidence/p5b/baseline.json` records the original start;
`evidence/p5b/staging-preparation/` records this checkpoint and review. The older
pre-commit evidence remains historical, not a claim about the new repository HEAD.

## Architecture and decisions

Use **promotion of the exact accepted P5A artifact**, followed by independent
validation and disposable signing. This avoids a second application build system.
A reviewed allowlist pins source, CI run/attempt, artifact ID, ZIP/bundle hashes,
inventory/input hashes and exported OSTree commit. An arbitrary successful artifact
or manual input cannot replace them.

```text
Owner-approved immutable source + successful P5A run + exact artifact digest
  -> eligibility and bounded extraction
  -> unchanged P5A exported-payload audit against approved detached source
  -> disposable key; signed application/AppStream commits and summary
  -> clean-client signature/integrity validation; signed snapshot inventory
  -> verified complete local generation; atomic active-pointer replacement
  -> native descriptor check and deliberate publication-interruption exercise
```

The P5A auditor's source check is preserved. A child process binds its `GITHUB_SHA`
to the approved application source; the parent retains and records the actual
release-tooling commit/workflow separately. Promotion does not pretend the later
release tooling is the source of the accepted application bundle.

**Hosting recommendation:** provider-neutral static snapshots now; R2-compatible
object storage is proposed for the eventual update remote, GitHub Releases for an
optional bundle/provenance mirror. Pages, Releases, R2 and Netlify are compared in
`P5B_HOSTING_DECISION.md`, with official pricing/limits and the measured 301,341,805-byte,
5,554-file repository. One repository fits Pages; retained snapshots and growth
traffic still favor object storage. The owner endorses R2-compatible architecture;
provider account, permanent endpoint, cost and provisioning approval remain deferred.

**Signing recommendation:** owner-controlled offline production signing, with an
offline recovery/certification primary and expiring signing subkey after a separately
approved ceremony. The owner endorses this custody direction, without authorizing
key generation. `P5B_SIGNING_DESIGN.md` compares protected Actions secrets,
offline signing and managed infrastructure; it covers custody, bootstrap, rotation,
lost keys, compromise, hosting outage and database-compatible recovery.

These decisions do not block identity-independent disposable staging work.
Production custody, cost, endpoint, credentials and publication require separate
owner approval. No production signing path is enabled by a command-line flag.

## Workflow and implementation

| File/group | Responsibility |
| --- | --- |
| `.github/workflows/release.yml` | Manual staging only; read-only contents/actions; eligibility before protected staging; immutable action pins; bounded jobs; safe status-only diagnostic upload |
| `ci/release/policy.json` | Accepted source/artifact/workflow/auditor/lock pins; production disabled |
| `ci/release/core.py` | Eligibility, bounded untrusted extraction, P5A audit orchestration, disposable GPG, native OSTree checks, descriptors, signed inventories and local snapshot publication |
| `ci/release/audit_candidate.py` | Approved-source child binding for the unchanged P5A payload auditor |
| `ci/release/github.py`, `preflight.py` | Read-only GitHub evidence/environment checks; bounded artifact download without forwarding API credentials to the CDN |
| `ci/release/stage.py` | Explicit local/live rehearsal, actual native positive/negative checks, safe result record, metrics and key-home cleanup |
| `ci/release/workflow_policy.py`, `workflow-contract.json` | Semantic and exact reviewed workflow contract; rejects extra capabilities or unsafe changes |
| `ci/release/recovery.py` | Verify/reactivate retained local generations while preserving client objects; never edits a database |
| `ci/release/plan.py` | Review-only future GitHub Releases plan; creates no tag, draft, prerelease or release |
| `ci/release/test_policy.py`, `test_signing.py` | Eligibility, signing, transport, key isolation, workflow and publication failure regressions |
| `ci/verify.py` | Adds P5B tests to the existing backend regression command; removes no existing test |
| `.gitignore` | Excludes disposable staging directories and keyring/private-key files |
| Four `ci/P5B_*.md` documents and `ci/evidence/p5b/` | Architecture, procedures, results and non-sensitive verification evidence |

The workflow has no push/PR/release trigger, production secrets, write permission,
network publication job or release API call. Inputs pass through quoted environment
variables, not raw shell interpolation. Offline replay is forbidden in Actions;
hosted execution rechecks live CI and environment protection.

Current read-only inspection found **zero GitHub environments**, so no independent reviewer
protection is claimed. The workflow fails closed unless `p5b-staging` actually
requires reviewers, prevents self-review, disables admin bypass and restricts the
exact integration branch. A sole owner cannot independently approve their own job
under that policy. Workflow registration on the default branch also needs a
separately authorized plan; no main merge or default-branch change was performed.
`P5B_GITHUB_STAGING_PLAN.md` recommends a
separately approved inert registration-only workflow file on main, with actual
execution on integration. This avoids merging the integration/application branch.
A temporary default-branch switch is a broader, separately gated fallback.

## Repository generation, provenance and publication safety

The rehearsal imports the accepted bundle into an archive repository, signs the
application ref, generates/signs AppStream and summary metadata, exports only the
public staging key, and creates `.flatpakrepo` / `.flatpakref` descriptors. URLs
are restricted to local paths or reserved `.invalid` staging HTTPS names. The
accepted production application identity is retained to avoid rebuilding; remote,
key and client directories are disposable. No application installation/launch or
owner data access is involved.

Clean OSTree verification requires signed summary and commits with only the supplied
public key, pulls all expected refs and checks object integrity. Native negative
cases include incorrect key, tampered summary, missing commit and unexpected ref.
The `.flatpakrepo` is checked by Flatpak in an isolated installation after local
activation. `.flatpakref` structure is checked; full client installation/update
validation belongs to P5C and is not claimed here.

Release metadata records source/repository, version/architecture/ID, runtime locks,
CI/workflow/artifact identities and hashes, OSTree commit, signing fingerprint,
authorization reference, target and outcome. The unsigned artifact hash is byte
integrity against an approved digest, not a substitute for publisher authentication.
The signed public manifest binds all published file sizes/hashes and rejects
missing, changed, extra, unsafe or private-key-containing content.

Publication copies and verifies a complete generation, syncs data/directories,
retains all old immutable objects/deltas, then atomically replaces the local pointer
on one filesystem under an exclusive lock. Partial copy, failed verification,
concurrent writers and an interruption before activation cannot advance the pointer.
There is no automatic pruning. Recovery refuses rollback that drops client objects.

This is an executable **local filesystem publication contract**, not proof of
multi-request HTTP transactionality. No cloud upload adapter is implemented or
enabled. The approved provider will need safe destination readback, stable URL
mapping, concurrency and cache/summary-signature transition validation. GitHub
Releases integration currently prepares a review plan, not a network writer.

## Tests and evidence

Final verification uses a fresh local clone at `1a28f68`, with the uncommitted P5B
candidate overlaid and hashed. Dependencies and frontend assets were installed/built
there; tests do not rely on the development checkout's generated files. A checkout-local
Python environment is required by existing launcher/installer tests. Crypto fixtures
use short private `/tmp` paths; package tests use disk-backed scratch space to retain
their existing free-space safeguards.

| Verification | Final result |
| --- | --- |
| P5B security/signing/publication/transport regressions | PASS — 44 tests; actual GPG, synthetic publication model clearly labeled |
| Existing P5A workflow contracts | PASS — 31 tests |
| Complete backend/security/lifecycle/migration/packaging plus P5B | PASS — 611 tests, 83 subtests |
| P5B workflow policy | PASS |
| Ruff and actionlint for both workflows | PASS |
| Clean-checkout production frontend build | PASS |
| Full frontend/browser verification | PASS — lint, 273 unit tests, TypeScript/build, all 20 browser tests including 5 lifecycle tests; zero retries |
| Live accepted P5A eligibility recheck | PASS — read-only, no run triggered |
| Disposable GPG smoke/signature verification | PASS; key homes removed |
| Actual native staging generation | PASS — owner Ubuntu run; signed OSTree repository and accepted artifact validation |
| Native signing rejection, descriptor and interruption checks | PASS — wrong key, tampered summary, missing object, unexpected ref, native flatpakrepo remote and interrupted activation |
| Protected GitHub staging workflow | NOT EXECUTED — unconfigured environment and no dispatch authorization |
| HTTP hosting, permanent key/rotation and full update lifecycle | NOT EXECUTED; outside this local staging verification |

Representative commands from the clean candidate checkout:

```bash
backend/.venv/bin/python -m unittest discover -s ci/release -p 'test_*.py' -v
backend/.venv/bin/python -m unittest discover -s ci -p test_ci.py -v
backend/.venv/bin/python ci/release/workflow_policy.py
backend/.venv/bin/python -m ruff check --config backend/pyproject.toml backend/app backend/tests ci
```

The complete backend command, working directories, timings and source hashes are
recorded in `evidence/p5b/local-verification.json`; frontend verification uses
`backend/.venv/bin/python ci/verify.py frontend --output <disposable-evidence-directory>`.
Actionlint uses the accepted tool verified during P5A, against both workflow files.

Historical failures are preserved. The initial clean-checkout setup used an external
venv and an overlong GPG-agent socket path, causing launcher environment failures and
GPG setup errors. The setup was corrected without weakening tests. An intermediate
run passed its tests but failed one Ruff line-length check; that was corrected.
The final review also closed a `..` output-path bypass and added credential-redirection
and diagnostic-redaction regressions. See `evidence/p5b/verification-history.json`.

### Native evidence reviewed — historical Codex blocker preserved

Actual Flatpak import reports **`error: open(O_TMPFILE): Read-only file system`**.
The isolated audit reached the unchanged accepted P5A auditor and failed at bundle
import. It did not produce a verified signed repository. No sandbox permission,
signature check or application security control was weakened to bypass this.
`native-staging-attempt.json`, `native-audit-diagnostic.json` and `capability-probe.json`
preserve the failure. The actual attempt predates the final path/redaction/test-only
refinements; it is not misrepresented as a final-source native success.

The owner subsequently completed that procedure successfully in regular Ubuntu.
Original `result.json` and `eligibility.json` were located at
`/home/cerillion/.cache/cyrnava-p5b.bUyzq5/run/` and preserved byte-for-byte in
`evidence/p5b/owner-native-2026-10-31/`. The result file's modification time is
2026-10-31 10:57:27 UTC; review time and both SHA-256 hashes are recorded in `review.json`.

The review confirmed overall PASS/complete, every required native positive/negative
step, exact approved bundle/source/CI run/OSTree commit, unchanged runtime locks,
version/identity and current release-workflow hash. The active retained generation's
signed inventory was verified independently using `gpgv` with only its exported
public staging key; every listed public file was rehashed, and repository byte/file
counts were recomputed. Both disposable secret-key homes are absent. No original
workspace or native result was modified.

The scratch `public/` copy lacks its manifest and descriptors at review time; no
cause is inferred. The authoritative active generation is complete, signed and
independently verified, so this is not a failure of the retained publication.
The intended interrupted generation remains inactive. See `review.json` for limits.

Eligibility remains **PINNED REPLAY** against run 41181510439/source 1ee2077, not a
hosted P5B run or live CI check. `release_workflow_run_id` is null. The recorded
tooling HEAD is 1a28f68 plus uncommitted P5B work; workflow hash matches, but the native
run did not record individual script hashes at execution. A later hosted run against
an authorized immutable P5B commit supplies that missing release-tooling provenance.
No native rerun is requested for this documentation update.

## Performance and cost

- Accepted bundle: **209,189,544 bytes**; CI ZIP: **210,238,004 bytes**.
- Logical installed application: **980,984,007 bytes**, 5,320 payload entries.
- GPG synthetic 93-byte manifest microbenchmark: key generation 0.185073 s,
  signing 0.010989 s, verification 0.010978 s; public key 667 bytes, detached signature
  310 bytes. These are one local run, not OSTree metadata-overhead measurements.
- Owner native archive repository: **301,341,805 bytes (287.38 MiB), 5,554 files**;
  signed metadata counter **2,016 bytes**. Deltas disabled, recorded delta bytes 0;
  that is not an enabled-delta overhead measurement. Generation **102.06 s**,
  signing/summary **0.13 s**, complete rehearsal **161.167 s** on one Ubuntu host.
  Signing time is included in generation; all positive/negative/publication checks
  are included in total time. Actual client network transfer and small-update size
  remain unmeasured.
- Static deltas default off; optional staging measurement is separate. No unsupported
  storage/performance target is imposed. Native scratch-space allowance is an estimate.
- Hosting scenarios for 5 / 100 / 1,000 installations now model 1.61 / 32.13 / 321.34 GB monthly
  application traffic. Under the documented assumptions, R2 core usage fits its free
  allowances; domain/routing/tax/runtime/CI costs are excluded. See the hosting decision
  for current official pricing, request counts, Netlify comparison and uncertainty.

## Remaining risks and owner actions

1. Review the completed native evidence; Gate 5 is now PASS. Do not repeat a full
   native rehearsal just to regenerate a documentation record.
2. Hosting/offline custody directions are now owner-endorsed. Permanent keys,
   provider purchases, domains, secrets and public hosting are not P5B staging
   acceptance prerequisites and remain separately gated.
3. One local P5B-only follow-up commit is authorized. Request separate authorization
   for its push; no push/authentication attempt occurs under this commit-only grant.
   Preserve the local p5a-accepted tag; publishing it is not required by P5B.
4. Authorize a workflow-registration approach and protected `p5b-staging` environment
   configuration: independent reviewer, prevent self-review, no admin bypass, exact
   integration-branch restriction. Inspect actual settings. The manual workflow's
   default-branch registration requirement must be resolved explicitly; no main merge
   or default-branch change is implied. An approved alternative needs design/policy
   review; do not bypass protection to accommodate a sole reviewer.
5. Separately authorize one manual hosted staging run against that immutable P5B
   tooling commit. Require live source/run/artifact eligibility, approval protection,
   signed repository/native negative cases, descriptors, publication interruption,
   safe diagnostics upload and successful final job conclusions. Record workflow
   run/attempt, tooling SHA, source SHA, checksums, public fingerprint and results.
   The automatically triggered P5A regression workflow after a future push must also
   pass all required gates with the added P5B suite. No run is authorized by this report.
6. After hosted evidence review, obtain explicit owner P5B acceptance. Current native
   PASS does not establish protected Actions execution or artifact download behavior.
7. Retain known-good snapshots, no-pruning policy, and independently authenticated
   trust bootstrap. Signing alone does not prevent all rollback/freeze attacks.
8. Keep P3 backups/schema compatibility authoritative: a binary rollback is not a
   database downgrade. Preserve existing licensing/distribution-review limitations.

## Acceptance gates and P5C readiness

| Gate | Recommendation |
| --- | --- |
| 1. Accepted baseline preserved | PASS for reviewed source and executed regressions |
| 2. Hosting architecture | PASS — R2-compatible direction owner-endorsed; provisioning/endpoint/cost authorization deferred |
| 3. Signing infrastructure | PASS — real disposable GPG and native signed OSTree/rejection checks; offline custody direction owner-endorsed; permanent key creation deferred |
| 4. Release workflow | Implemented/policy-tested; hosted protection/execution pending |
| 5. Signed repository and descriptors | PASS — owner evidence plus independent retained-generation integrity/signature review |
| 6. Publication safety | PASS for P5B local native staging and interruption protection; future HTTP/cache/update integration is unexecuted |
| 7. Security regressions | PASS for executed paths; no claim about unexecuted integrations |
| 8. Documentation | Delivered with explicit limitations and owner procedure |
| 9. Owner acceptance | Pending |

**Recommendation: CONDITIONAL — native acceptance gaps are closed; protected hosted
workflow verification and formal owner acceptance remain.** Hosting/custody directions
are now endorsed, without authorizing irreversible production setup. HTTP
deployment, real install/update lifecycle and production-key operations are later
separately authorized work, not missing native P5B results. No P5C/P6 work has begun.
Stop at this updated P5B checkpoint; production signing/hosting/publication remain disabled.
