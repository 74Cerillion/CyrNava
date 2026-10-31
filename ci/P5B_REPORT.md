# P5B report — secure release preparation and disposable staging

**31 October 2026 — CONDITIONAL; not accepted.** Required CI run **41205351385** at
**7aaefd0f60a735637ee603ac380587a25b73f6cb** passed every gate. Native signed-OSTree,
negative security, descriptor and interrupted-publication evidence remains accepted.
The owner subsequently approved a single-maintainer model; its revised P5B policy
is locally verified but uncommitted and has not executed in hosted staging.
Registration on main, environment configuration and hosted dispatch remain separately
gated. None has been performed. These gaps prevent unconditional acceptance.

Manual owner authorization now replaces independent GitHub deployment approval.
No second reviewer or self-review prevention is required or claimed. This concentrates
staging authority in the owner's account; production signing remains owner-controlled,
offline and unavailable to staging. Future R2-compatible hosting remains endorsed
without authorizing credentials, permanent keys, purchases or public deployment.

The implementation history is a9de663 → 3027231 → the reviewed appearance correction
7aaefd0. The owner completed its authenticated push; remote and local branch agree.
Local `p5a-accepted` remains unchanged. After reviewing the local results, the owner
authorized one integration commit/push and its automatic CI verification. Main
modification, GitHub settings, workflow dispatch/rerun, permanent keys, public releases
and P5C/P6 remain outside that authorization.

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

## Current hosted CI — appearance correction 7aaefd0: PASS

[Run 41205351385](https://github.com/74Cerillion/CyrNava/actions/runs/41205351385),
workflow **402398273**, attempt **1**, push event, exact source
`7aaefd0f60a735637ee603ac380587a25b73f6cb`: **PASS**.

| Required job/check | Actual hosted result |
| --- | --- |
| Workflow validation (124549189167) | PASS — 31 contracts |
| Backend/security (124549221042) | PASS — 611 tests and 83 subtests |
| Frontend/browser (124549221121) | PASS — lint, 273 units, TypeScript/build, all 21 browser tests including 5 lifecycle and both appearance regressions |
| Production Flatpak/bundle audit (124550104215) | PASS — locked runtime provisioning, build, exported-package audit and validated unsigned upload |
| CI required (124552493850) | PASS — all four upstream jobs successful |

All four artifact ZIP sizes/SHA-256 were independently verified against GitHub:
backend **13043983920**, frontend **13044028910**, Flatpak diagnostics **13044800454**,
validated package **13044630984**. Package ZIP: **210,238,004 bytes**, SHA-256
`560a05310a80ae0d397d7b34936563ea3f674dd6f72b2bdb2984aa246ab35b51`.
Flatpak bundle: **209,189,544 bytes**, SHA-256
`01e13b55a60100e6573de8bfbfc87f1b16373c4d7b8ca05047e35c4e27263153`.

Downloaded SHA256SUMS, result, build inputs, inventory and provenance were crosschecked
for source/run/attempt/identity/version, exact runtime locks, bundle digest/size and
OSTree commit `049e3ffc86aa1b6060c17db4baf7a5b7bde37e0562f6870a06c3ab62322f6971`.
Actual hosted exported-bundle audit PASS is preserved; no repeat local native import
or renderer/portal test is claimed. The latest package does not replace policy-pinned
P5A artifact 13035607417 used for staging.

Evidence: `evidence/p5b/hosted-ci-41205351385/`, including run/jobs/artifacts,
actual result records/log excerpts, all hashes, browser JUnit and focused empty-caret
state verification. Raw ZIPs/logs remain ignored under `ci-output/p5b-hosted-41205351385/`.
Historical failed runs remain unchanged below and in their original evidence records.
This CI PASS is not protected hosted staging and predates the revised policy below.

## Single-maintainer hosted-staging preparation — locally verified

The owner's explicit later architecture decision supersedes the earlier two-person
approval requirement. P5B now requires manual dispatch by `74Cerillion`, exact
integration repository/ref/workflow identity, matching workflow/check-out SHA and
first attempt. Both preflight and live staging recheck identity and the reviewed
workflow contract. `p5b-staging` has no required reviewers; exact branch-only policy
remains mandatory, with no tags, wildcards, main or pull refs. No independent approval
is claimed. The admin-bypass flag is not treated as an approval safeguard when no
reviewer gate exists; branch and immutable-source checks remain independently enforced.

Changed policy/preflight/environment tests reject wrong actor/ref/repo/workflow,
unapproved source, wrong artifacts and missing staging authorization. The existing
P5A CI definition, action pins, package/lock/auditor code, production application,
CSS, autosave/recovery/SQL guard and real signing/integrity/publication safeguards
are unchanged. The release workflow step label and exact contract now accurately
describe owner dispatch. No production keys or publication credentials are referenced.

`ci/release/registration-only.yml` is the exact inert main-file proposal, stored
outside .github/workflows on integration. It matches all five input definitions,
has contents read only and one literal-false job with only a no-op marker. It has
no checkout, environment, release/signing command or secret. `registration_policy.py`
and `test_registration.py` validate it and optional future run/settings readbacks.
Full YAML, main base SHA, security assessment, owner commands and separate A/B/C
approval steps are in `P5B_GITHUB_STAGING_PLAN.md`.

Local final verification: **59 release/registration/signing tests + 31 existing CI
contracts PASS**, Ruff/actionlint and CI/release/registration security policies PASS.
One-day synthetic GPG unit-test keys were cleaned up; no production/permanent key
or full native OSTree rehearsal was created. The initial CI-contract run encountered
the unchanged 5 GiB space guard in two tests; the rerun used spacious /dev/shm for
small synthetic fixtures, preserving the guard and original failure record.
`evidence/p5b/staging-final-preparation-2026-10-31/` records results, hashes and actual
GitHub readbacks: main cbf7cccc686080b2b4b07274a9f5a23fec52999f, zero environments,
and no release definition on main. New policy is not committed, pushed or hosted-tested.

## Hosted continuous-integration result — 3027231

[Run 41197927704](https://github.com/74Cerillion/CyrNava/actions/runs/41197927704),
workflow ID **402398273**, attempt **1**, push event, exact commit
`3027231c390b1814a98a567e5f30afb4ebff0dab`: **FAIL**.
This is ordinary P5A continuous integration, not protected P5B staging execution.

| Required job/check | Hosted result |
| --- | --- |
| Workflow validation | PASS — 31 contracts |
| Backend and security | PASS — 611 tests, 83 subtests; clean frontend-assets prerequisite verified |
| Frontend lint, unit tests, TypeScript/build | PASS — 273 unit tests |
| Browser integration | FAIL — 19 passed, 1 failed; all 5 lifecycle tests passed |
| Production Flatpak build and exported bundle audit | SKIPPED — correctly gated by frontend failure |
| Validated unsigned application artifact upload | NOT EXECUTED; no application package produced |
| Backend/frontend diagnostic uploads | PASS — both downloaded ZIP sizes/SHA-256 independently match GitHub |
| CI required | FAIL — frontend failure and skipped Flatpak job correctly rejected |

The failed test begins at `frontend/e2e/workspace.spec.ts:112`; its assertion at
line **228** expects the last paragraph's CSS `::after` content to contain
`Enter text`. Actual content stayed `none` for the 10,000 ms predicate timeout.
At the initial review this established the failing observation without determining
its cause. That historical record is preserved. The subsequent authorized investigation
established an invalid test precondition; see the separate correction assessment below.

Evidence is in `evidence/p5b/hosted-ci-41197927704/`: run/jobs/artifact metadata,
actual log excerpts, frontend/backend result records, browser JUnit, generated
failure context and summary. The generated Playwright context's instruction text
is diagnostic content, not an owner request to implement a fix. Original diagnostic
ZIPs (including the screenshot/trace) are retained under the ignored
`ci-output/p5b-hosted-41197927704/`; no binaries, signed download URLs or credentials
were copied into the report. Digests and member paths are recorded for recovery
after GitHub's seven-day artifact retention expires. No package checksum/provenance
can be verified for this run because the package job never executed.

The owner's provisional approval of registration-only staging preparation is
recorded; exact main-file YAML and environment settings still require separate
authorization. No main/environment change or staging dispatch occurred.

## Local appearance-test correction — commit/push authorized; hosted result pending

The retained hosted screenshot, trace snapshots, error context and generated CSS
show the last paragraph was empty/editable but lacked BlockNote's selected-empty
paragraph decoration. After Escape and Backspace, an earlier paragraph changed
from `/ bold` to ` bold`; the last paragraph stayed empty and undecorated through
Saved. Its computed placeholder content `none` was correct for that unselected
target. Saved is a persistence assertion, not a caret-placement guarantee.

The old test moved a DOM Range to the editor root's end without establishing the
ProseMirror selection. Three instrumented original runs passed locally but reproduced
that DOM/model mismatch in every helper call. The entire historical failure is not
claimed to reproduce locally, and its exact event-loop interleaving remains unrecorded.
No production application/CSS defect is established.

Only executable change: `frontend/e2e/workspace.spec.ts`. Real click/Control+End
navigation now waits for observable, synchronized paragraph selection and the exact
new empty block before typing. Escape/Backspace/Saved diagnostics record focus,
DOM/model positions and computed styles without note bodies or session credentials.
The original light/dark `Enter text` and contrast assertions remain. A new regression
checks the unselected-empty negative case, reproduces the DOM-only mismatch without
typing from it, and verifies that selecting the intended empty paragraph displays
the real hint while canonical note/revision data remains unchanged.

Final source in a fresh detached checkout at `3027231` passes **20 focused runs**
(10 appearance + 10 regression, zero retries) and the **complete frontend suite**:
lint, **273 unit tests**, TypeScript/production build and **21 browser tests**,
including all **5 lifecycle** tests. No production/backend behavior changed, so
backend tests were not rerun; their hosted **611 tests / 83 subtests PASS** is
preserved. The accepted SQL lifecycle guard, signing code, security controls,
workflow and package payload rules remain unchanged. No keys were generated.

See `P5B_APPEARANCE_CORRECTION.md` for causality, exact modifications and limits;
`evidence/p5b/appearance-correction-2026-10-31/` records candidate hashes,
hosted-trace analysis, baseline/focused state checks and complete-suite results.
Historical hosted evidence remains unchanged in `hosted-ci-41197927704/`.
At the original local-review checkpoint the correction was uncommitted/unpushed.
The owner subsequently authorized commit 7aaefd0 and completed its push; actual hosted
PASS is recorded above. That does not authorize further pushes, reruns or dispatches.

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

Current read-only inspection found **zero GitHub environments**. The new owner-approved
single-maintainer model requires manual owner dispatch and exact integration-branch
restriction, not another person's approval. No independent-reviewer protection is
claimed. Main registration and actual environment setup remain unauthorized.
`P5B_GITHUB_STAGING_PLAN.md` contains the exact inert registration-only proposal on
main, with executable staging kept on integration. No default-branch change or
integration/application merge is proposed or performed.

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
| Initial P5B local full frontend/browser verification | PASS — lint, 273 unit tests, TypeScript/build, all 20 original browser tests including 5 lifecycle tests; zero retries. Hosted follow-up is 19/20 and FAIL as recorded above. |
| Local appearance correction, exact final source in clean checkout | PASS — 20 focused runs; lint, 273 unit tests, TypeScript/build and 21 browser tests including 5 lifecycle tests; zero retries. New hosted verification NOT EXECUTED. |
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
3. Required CI at 7aaefd0 is now PASS, including the appearance correction. Obtain
   separate authorization for one integration commit/push of the revised single-maintainer
   policy/proposal/tests/docs; require its automatic CI to pass. Preserve the local tag.
4. Separately authorize **A**: one inert registration-only main file, and **B**: the
   no-reviewer p5b-staging environment with exact branch-only policy and no secrets.
   Read both back; do not treat registration/configuration as hosted verification.
5. Separately authorize **C**: one owner-initiated workflow_dispatch at the exact approved
   revised tooling SHA, promoting the unchanged accepted P5A source/artifact. Require
   live eligibility, native signing/negative/descriptor/interruption checks, key cleanup,
   safe diagnostic upload and final PASS. No independent deployment approval is required.
6. After actual hosted staging evidence review, obtain explicit owner P5B acceptance.
   Neither current native nor CI PASS proves the new manual staging path executed.
7. Retain known-good snapshots, no-pruning policy, and independently authenticated
   trust bootstrap. Signing alone does not prevent all rollback/freeze attacks.
8. Keep P3 backups/schema compatibility authoritative: a binary rollback is not a
   database downgrade. Preserve existing licensing/distribution-review limitations.

## Acceptance gates and P5C readiness

| Gate | Recommendation |
| --- | --- |
| 1. Accepted baseline preserved | PASS — accepted P5A controls preserved; required CI at 7aaefd0 PASS; new local policy awaits its own hosted verification |
| 2. Hosting architecture | PASS — R2-compatible direction owner-endorsed; provisioning/endpoint/cost authorization deferred |
| 3. Signing infrastructure | PASS — real disposable GPG and native signed OSTree/rejection checks; offline custody direction owner-endorsed; permanent key creation deferred |
| 4. Release workflow | Single-maintainer policy locally verified; registration, exact-branch environment and hosted execution pending |
| 5. Signed repository and descriptors | PASS — owner evidence plus independent retained-generation integrity/signature review |
| 6. Publication safety | PASS for P5B local native staging and interruption protection; future HTTP/cache/update integration is unexecuted |
| 7. Security regressions | PASS for executed paths; no claim about unexecuted integrations |
| 8. Documentation | Delivered with explicit limitations and owner procedure |
| 9. Owner acceptance | Pending |

**Recommendation: CONDITIONAL — native and required CI acceptance gaps are closed;
the revised single-maintainer implementation is locally verified.** Obtain the
separately authorized integration commit/push, main registration, environment setup
and manual hosted staging execution, then review actual evidence for owner acceptance.
No production credentials, keys, public hosting/release, main application merge or
P5C/P6 work is authorized or performed. Hosting/offline-custody directions stay endorsed.
