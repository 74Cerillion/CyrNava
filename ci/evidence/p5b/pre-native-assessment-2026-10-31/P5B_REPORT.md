# P5B report — secure release preparation and disposable staging

**31 October 2026 — CONDITIONAL; not accepted.** Local implementation and available
automated security checks pass. Native signed OSTree generation/verification is
blocked by this Codex session's filesystem restriction; protected hosted staging
has not been configured or executed. These are acceptance gaps, not passing tests.

No commit, push, production key, hosting resource, environment modification,
public release, production deployment, main merge, P5C or P6 was performed.

## Accepted baseline and repository state

- Branch: `desktop/p2-production-integration`; starting worktree clean.
- HEAD and inspected remote branch: `1a28f68c5732ccc1275403060e89ff168a846655`.
- Local annotated `p5a-accepted` points to that commit. The tag remains local;
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
P5B changes are uncommitted and separately identifiable. `evidence/p5b/baseline.json`
records the initial state; the final review records hashes and changed paths.

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
`P5B_HOSTING_DECISION.md`, with official pricing/limits, estimates and native
measurement gaps. No permanent endpoint or provider decision has been finalized.

**Signing recommendation:** owner-controlled offline production signing, with an
offline recovery/certification primary and expiring signing subkey after a separately
approved ceremony. `P5B_SIGNING_DESIGN.md` compares protected Actions secrets,
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

Read-only inspection found **zero GitHub environments**, so no independent reviewer
protection is claimed. The workflow fails closed unless `p5b-staging` actually
requires reviewers, prevents self-review, disables admin bypass and restricts the
exact integration branch. A sole owner cannot independently approve their own job
under that policy. Workflow registration on the default branch also needs a
separately authorized plan; no main merge or default-branch change was performed.

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
| Actual native staging generation | BLOCKED — attempt recorded FAIL at P5A bundle import, not native PASS |
| Native signed summary/commit rejection and descriptor remote validation | NOT EXECUTED — downstream of import blocker |
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

### Native blocker and safe next step

Actual Flatpak import reports **`error: open(O_TMPFILE): Read-only file system`**.
The isolated audit reached the unchanged accepted P5A auditor and failed at bundle
import. It did not produce a verified signed repository. No sandbox permission,
signature check or application security control was weakened to bypass this.
`native-staging-attempt.json`, `native-audit-diagnostic.json` and `capability-probe.json`
preserve the failure. The actual attempt predates the final path/redaction/test-only
refinements; it is not misrepresented as a final-source native success.

Use the exact regular-Ubuntu procedure in `P5B_OWNER_CHECKS.md` after local regressions
pass. It reuses the accepted hash-pinned ZIP, needs no new application build, creates
only disposable keys, and produces final `result.json` / `eligibility.json`. Inspect
that native evidence before accepting Gate 5. Do not substitute a simulated result.

## Performance and cost

- Accepted bundle: **209,189,544 bytes**; CI ZIP: **210,238,004 bytes**.
- Logical installed application: **980,984,007 bytes**, 5,320 payload entries.
- GPG synthetic 93-byte manifest microbenchmark: key generation 0.185073 s,
  signing 0.010989 s, verification 0.010978 s; public key 667 bytes, detached signature
  310 bytes. These are one local run, not OSTree metadata-overhead measurements.
- Actual archive repository size/file count, generation/signing time, delta overhead,
  fresh-install transfer and small-update transfer remain unmeasured due to the native
  blocker. `stage.py` records repository metrics on a successful host execution.
- Static deltas default off; optional staging measurement is separate. No unsupported
  storage/performance target is imposed. Native scratch-space allowance is an estimate.
- Hosting scenarios for 5 / 100 / 1,000 installations model 1.35 / 27 / 270 GB monthly
  application traffic. Under the documented assumptions, R2 core usage fits its free
  allowances; domain/routing/tax/runtime/CI costs are excluded. See the hosting decision
  for current official pricing, request counts, Netlify comparison and uncertainty.

## Remaining risks and owner actions

1. Execute the isolated native rehearsal; inspect real signed-repository, descriptor,
   negative-case and interruption evidence and actual repository measurements.
2. Review hosting and offline key-custody recommendations. Approve consequential
   provider/domain/cost/key decisions separately, without sharing private material.
3. Authorize any source commit/push, environment changes and hosted staging execution
   separately. Manual workflow registration and an independent reviewer remain open.
4. Retain known-good snapshots, no-pruning policy, and independently authenticated
   trust bootstrap. Signing alone does not prevent all rollback/freeze attacks.
5. Keep P3 backups/schema compatibility authoritative: a binary rollback is not a
   database downgrade. Preserve existing licensing/distribution-review limitations.

## Acceptance gates and P5C readiness

| Gate | Recommendation |
| --- | --- |
| 1. Accepted baseline preserved | PASS for reviewed source and executed regressions |
| 2. Hosting architecture | Complete proposal; consequential approval pending |
| 3. Signing infrastructure | Real GPG PASS; native OSTree verification still blocked |
| 4. Release workflow | Implemented/policy-tested; hosted protection/execution pending |
| 5. Signed repository and descriptors | BLOCKED pending native evidence |
| 6. Publication safety | Local signed model PASS; native/HTTP evidence incomplete |
| 7. Security regressions | PASS for executed paths; no claim about unexecuted integrations |
| 8. Documentation | Delivered with explicit limitations and owner procedure |
| 9. Owner acceptance | Pending |

**Recommendation: CONDITIONAL — retain P5B as unaccepted until the essential native
evidence and owner review are complete.** The architecture supports a later P5C
handoff, but readiness is conditional and no P5C work has begun. Stop at this P5B
checkpoint; production signing, hosting and publication remain disabled.
