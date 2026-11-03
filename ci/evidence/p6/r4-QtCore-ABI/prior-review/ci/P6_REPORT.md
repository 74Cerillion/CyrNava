# P6 — Distribution, installation and update validation

**1 November 2026 — P6 — CONDITIONAL / FURTHER ACTION REQUIRED.**

Local implementation and available automated verification are complete at this
checkpoint. Real remote installation **with actual runtime retrieval passes**.
The native launch probe fails at the host's user-namespace boundary before Qt
starts. Real GUI/persistence/update, public HTTPS, final licensing/trust and final
source/CI/release approval remain open. The owner subsequently completed corrected
preparation at `real-pair-r2`: complete PASS, both payload audits PASS and key
cleanup PASS. The interrupted prelaunch attempt is preserved. The subsequent r3
attempt retrieved/verified runtimes and installed/verified A, then its gui-edit
verifier child exited 1 without a window. The exact launch-failure cause remains
unresolved because child stderr was not retained. Diagnostic correction passes
locally; another native execution awaits authorization.
No P6 acceptance or public-release readiness is claimed.

## Baseline and preservation

Local and independently reread remote integration HEAD remain
`bfa0b8005a3ddc519354fd7907e9b972fde8126b`; main remains
`4021bc292267c19b7ebebf219b4f682f8f99bf4c`. The local `p5a-accepted` tag still
resolves to `1a28f68c5732ccc1275403060e89ff168a846655`.
P5C's uncommitted formal closeout is preserved separately, byte for byte. No
commit, push, tag, workflow execution, GitHub setting, installation in the normal
Flatpak profile, personal workspace, permanent key or public endpoint was changed.

Accepted P5A source `1ee2077b283b8e5dfc2162119dd439ed3baeb109`, CI `41181510439`,
artifact `13035607417`, ZIP `73e6d58a…4eba6b`, bundle `93957ce5…20b26db` and
OSTree `da1bf73e…de1ac` remain distinct from release tooling and P6 candidate code.
Full values are in `ci/evidence/p6/release-candidate-manifest.json` and the unchanged
P5B policy. A fresh readback confirms the original artifact is unexpired and its
identity/digest are unchanged; it expires **7 November 2026, 07:53:28 UTC**.
Local cached replay is not new hosted eligibility. Expiration must never cause
silent substitution.

P3 migration/backup/schema safeguards, P4 production identity/package auditor,
P5A CI provenance, P5B eligibility/signing/seals/retained snapshots and P5C client
isolation are reused. Application code, schema 5, version 0.1.0, production
packaging, permissions, signing policy, CI workflows and accepted guards are
unchanged.

## Implementation

| Files | Result |
| --- | --- |
| `frontend/package.json`, `frontend/package-lock.json` | Exact minimatch 11.0.1 override and security regression in the normal test command; no wholesale upgrade |
| `frontend/scripts/check-minimatch.mjs` | All three consumer resolutions, ordinary matching and adversarial compilation in a bounded subprocess |
| `ci/release/distribution.py` | Provider-neutral reviewed publication plan and local reference adapter around accepted publisher; conditional activation, retained snapshots, verified HTTP GET/HEAD, MIME/cache/404 policy |
| `ci/release/trust.py` | Additional current primary/subkey identity, expiry and revocation checks on top of accepted cryptographic verification |
| `ci/release/product_inventory.py` | Bounded inventory of source locks and actual app/runtime metadata, SPDX records, native ELF hashes and notices; no symlink traversal or complete-SBOM claim |
| `ci/release/key_ceremony.py` | Fixed disposable certificate/signing-subkey rehearsal, encrypted backup/restore, primary-secret stub verification, expiry/revocation negatives and mandatory private cleanup |
| `ci/release/native_distribution.py` | Empty isolated client, actual upstream runtime retrieval and pin verification, real remote install, source/version/schema/permission validation and sandboxed launch probe |
| `ci/release/real_update.py` | Owner-gated real two-artifact preparation and GUI update/rollback/reinstall supervisor; exact B approval before signing; P5B audits/signing and P4 native assertions reused |
| `ci/release/real_update_audit.py` | Separate P6 B approval-bound child; unchanged exported-payload audit and candidate validation, exact source/approval binding and safe operation/stage diagnostics |
| `ci/release/test_real_update_audit.py` | 20 synthetic regressions for the B audit boundary, evidence validation, redaction, cleanup and failed-directory preservation; native payload auditing mocked in positive fixtures |
| `ci/release/progress.py`, `ci/release/test_progress.py` | Allowlisted operation events, heartbeats, deadlines, child-group cancellation and 12 synthetic interruption/prelaunch regressions; no application launch in tests |
| `ci/release/native_diagnostics.py`, `ci/release/test_native_diagnostics.py` | Private bounded child-output retention, safe Python bootstrap/exception markers and 11 synthetic regressions; production P4 checker unchanged |
| `ci/release/test_distribution.py` | 30 new publication, transport, trust, inventory, isolation, approval and cleanup regressions |
| P6 plan/report/checklist/runbook/license review, release notes and evidence | Acceptance criteria, exact results, unresolved gates, executable owner procedure and release-candidate manifest |

Publication does not create a second signer. The adapter calls the accepted
signed seal, native OSTree verifier and durable publisher. It verifies the whole
source, destination and historical object set, then conditionally activates a
complete immutable snapshot under the existing exclusive lock. Dry-run does not
upload or activate. Production endpoints/credentials are not implemented/enabled.
A future provider must supply equivalent conditional-pointer/gateway semantics;
independent live summary/signature PUTs are explicitly rejected as a design.

HTTP serves only manifest-listed files beneath the current generation; it rejects
traversal, unlisted/private content and damaged objects. Immutable hash objects
are cacheable, while metadata and errors are no-store. The server verifies each
immutable manifest once and hashes every response. Signature pairs spanning two
HTTP requests can still cross an activation boundary and fail closed; the adapter
does not claim transactionality across client requests or universal anti-rollback
freshness for ordinary Flatpak clients. No public CDN behavior has been verified.

The owner approved the already-built real B from accepted P5C implementation
`bfa0b800…`, CI `41285343063`, artifact `13075346402`, distinct OSTree
`f759380d…ada15`, version 0.1.0/schema 5, for this disposable compatibility exercise.
The original proposal remains false and byte-identical; the authorized copy at
`ci-output/p6-owner/B-approved.json` changes only the Boolean to true. This does
not replace the P5A allowlist or select the eventual final P6 release source.
The owner's first preparation **FAIL** and the local correction are described
below. The full corrected native flow and GUI remain unverified.

## Owner preparation failure and local correction

The original failed output remains untouched at `~/.cache/p6/real-pair`.
`prepared.json` reports complete FAIL with `Operation failed: python
(CalledProcessError)` and disposable-key cleanup PASS. A's audit result reports
PASS, its sealed generation and P6 provenance exist, B's detached source resolves
to the exact approved SHA and is clean, `p/audit-b` is empty, and generation B's
public directory does not exist. The signing-key home `p/key` is absent.

There are exactly two Python audit subprocesses in preparation:

1. A: `core.generate_repository` invokes the unchanged `audit_candidate.py`.
   The retained A audit result and completed generation establish that it passed.
2. B: `real_update.prepare` incorrectly invoked the same P5B-only child. That
   child calls `core.approval`, whose unchanged allowlist intentionally contains
   only accepted A. It rejects B with `Source is not approved for staging` before
   candidate validation or exported-payload auditing, despite the separate P6
   owner approval. Isolated execution of this exact child under the owner's
   Python 3.12.15 reproduced exit 1 and that authored rejection; its empty output
   remained unchanged. No full preparation or native audit was repeated.

This is a confirmed **P6 driver integration defect**, not a demonstrated artifact,
checkout, Python-dependency, payload, or signing failure. B's native payload audit
was never reached; passing the correction's unit fixtures does not certify it.

The correction invokes `real_update_audit.py` for B only. The child revalidates
the exact approved JSON hash and true-valued owner authorization, version/schema,
source SHA/environment binding and clean checkout, then calls the unchanged
`core.validate_candidate` and hash-pinned P5A exported-bundle auditor. The parent
requires complete PASS evidence matching the approved source, bundle, OSTree
commit and approval hash before B signing. P5B's A-only auditor/allowlist, signing,
application sources, packaging, permissions and workflows remain byte-identical.

Diagnostics identify `p6-generation-B-payload-audit`, a fixed child stage and
exit/timeout/unavailable categories. Arguments, paths, environment values, raw
stderr and exception messages are excluded. Other preparation failures retain a
fixed operation label; the accepted shared subprocess wrapper is unchanged.

Verification from a new disposable checkout with independent Git objects:

- New focused regressions: **20 PASS + 12 subtests**.
- Complete release and CI/workflow regressions: **177 PASS + 216 subtests**;
  one existing duplicate-ZIP warning, no failures.
- Ruff and formatting on the three correction Python files: **PASS**.
- Both cached A/B ZIPs, retained bundle/metadata hashes, immutable source identities,
  original/approved approval JSONs and accepted security controls: **unchanged**.
- Failed records and retained candidate files: hash-verified unchanged; key home
  absent, B audit still empty, no new native preparation or GUI execution.

The initial wider test attempt is preserved: 140 passed, two disk-precondition
failures and 35 GPG fixture setup errors. `/tmp` had less than the existing 5 GiB
precondition and the sandbox blocked local GPG-agent sockets. With local socket
permission and `/var/tmp` (over 38 GiB free), the unchanged checks passed. No
timeouts, retries, test exclusions, application behavior or security checks changed.

Evidence is in `ci/evidence/p6/real-pair-preparation-correction/`, including the
exact isolated rejection, retained failure JSONs, prior review/checksum/source
snapshots, clean-checkout hashes, test logs and integrity/preservation checks.
The earlier 693-test/full-frontend verification below remains historical evidence
for its recorded source hashes; those full suites were not repeated for this
P6-only driver correction.

**Historical checkpoint:** the owner subsequently authorized and completed
`real-pair-r2` preparation with PASS. The agent did not run it. The next section
records the interrupted GUI command and current checkpoint. Preserve both the
original failed pair and successful r2 pair. P6 remains CONDITIONAL.

## Interrupted GUI command: prelaunch runtime retrieval

The owner reports waiting about five minutes with no window, then pressing Ctrl+C.
The retained r2 `owner-result.json` contains complete FAIL, empty checks and no
error field. This is consistent with the original driver's control flow:
`KeyboardInterrupt` bypasses its ordinary exception handler, but its `finally`
writes the initial FAIL/checks object before propagating the interruption to the
outer CLI handler. There is no custom SIGINT handler. `complete: true` means the
record was finalized, not that launch or verification completed.

The exact pre-window order is:

1. Validate pair marker/preparation PASS, create isolated client, validate Wayland.
2. List empty client; fetch the upstream runtime descriptor; install KDE Platform
   and related extensions; pin and verify the exact runtime commit/signatures.
3. Validate and activate generation A in a local signed store, start loopback HTTP.
4. Validate descriptors/summary, install A, verify source/commit/schema/permissions.
5. Print the EDIT instructions, invoke `flatpak run` with the unchanged native
   checker, then initialize PySide/Qt, the private backend and application window.

Retained state narrows the interrupted operation to **runtime installation**:
the upstream remote exists with both GPG checks enabled; GL/VAAPI/codec/style and
locale extensions are deployed; the KDE Platform deployment is absent; an OSTree
transfer staging directory remains. The app deployment, active store pointer,
edit-phase result and application profile are all absent. Since `runtime_retrieval`
is the first checks assignment and evaluates its RHS first, an interruption there
leaves checks empty. Generation A did not reach installation or launch through
this sequence. This is not evidence of an application, Qt or sandbox defect.

The most likely wait was runtime transfer/import before Platform deployment.
Which network endpoint/object, disk step, lock or helper IPC was pending cannot be
reconstructed from the old wrapper: it captured stdout/stderr without streaming
or progress and allowed 1,800 seconds for runtime installation. Five minutes is
below that existing bound. Download and pin commands already used --noninteractive;
there is no evidence of a prompt. Descriptor fetch/helper IPC could block within
their own subprocess limits, but descriptor setup had already progressed here.

The P6-only correction emits flushed, fixed operation names, start/running/end
state and monotonic elapsed/deadline information to stdout and an attempt-local
`operations.jsonl`/`progress.json`. Long runtime/GUI children report every ten
seconds, without restarting the process or extending its deadline. Descriptor
setup is bounded at 300 seconds, matching existing metadata commands; runtime
download/pin retain 1,800 seconds and synthetic GUI phases retain 900 seconds.
Captured raw output, arguments, URLs, credentials, environment and note contents
are never included in diagnostic events. Runtime child stdin is /dev/null, so a
terminal prompt cannot wait invisibly; GUI checker stdin still carries its script.

Ctrl+C now records `interrupted: true`, the most specific failed operation,
elapsed time and `generation_A_launch_attempted: false` for prelaunch cancellation.
The monitored child's separate process group receives TERM, then KILL only if it
does not exit within a bounded five-second grace; descendants are not left running
by the wrapper. Timeout and nonzero exit have separate categories. Existing P5C
client security/error classification and all signature checks remain unchanged.

GUI now requires a **fresh --attempt-root** containing its own empty client/store,
progress and results, bound to the successful prepared.json hash and current GUI
driver hashes. Signed A/B preparations are read-only inputs. No failed profile,
result or partial runtime installation is overwritten or reused.

Focused tests from a disposable clean checkout: **32 PASS + 12 subtests** (12 new
progress/prelaunch tests plus the existing 20 B-audit tests). Complete release/CI
regressions: **189 PASS + 216 subtests**, one existing duplicate-ZIP warning.
Ruff/formatting pass. Tests use synthetic process fixtures and mock runtime/GUI
execution; no native preparation or GUI was run. Successful preparation, signed
generation metadata, original failed result and both approved artifact identities
are preserved. Evidence and prior review snapshots are in
`ci/evidence/p6/gui-prelaunch-correction/`.

**Historical owner checkpoint (subsequently executed as r3):** review the diagnostics and authorize one GUI command
against r2 with a new `gui-attempt-r3` root. Do not rerun preparation or delete any
old directory. Expect progress before a window, including runtime downloads that
may take substantially longer than five minutes. On interruption/timeout, retain
the attempt's results and stop; never classify an unattempted launch as failure of
Qt or the sandbox. P6 remains CONDITIONAL / native GUI verification incomplete.

## Generation A verification child exits 1: r3 investigation

The owner executed r3 with successful progress output. Retained evidence confirms:
runtime retrieval/pinned KDE verification PASS (109.869 s), A activation PASS,
A installation/source/version/schema/permission checks PASS (18.650 s), then
`gui-edit` started and failed with exit 1 after 1.022 s. The overall record is
complete FAIL, launch-attempt flag true; B update was not reached. No native edit
result or separate child stdout/stderr log was found in the disposable attempt.

The exact command template, with private per-run arguments replaced, was:

```text
flatpak --user run --branch=stable --command=python3 io.github._74Cerillion.CyrNava -u - edit <synthetic-run-id> <host-network-namespace> <synthetic-host-canary>
```

`packaging/flatpak/production/native_check.py` was streamed over stdin. This is
the **host-streamed P4 verification child**, not execution of the normal `cyrnava`
launcher and not a verifier shipped in the production payload. It imports
backend/PySide/application modules, validates configuration and creates initial
phase evidence before its native GUI checks. Without stderr or that phase record,
Flatpak startup, helper imports/configuration, Qt initialization and later native
initialization cannot be reliably distinguished. A one-second exit does not prove
an application defect, sandbox defect, or driver/helper incompatibility.

The confirmed implementation defect is diagnostic loss: `Progress.command`
captures stderr/stdout in `CalledProcessError`, but `exercise` formerly recorded
only the exception class and dropped both buffers. r3's discarded bytes cannot
be recovered by inspecting its JSON. No native rerun was used to guess a cause.

The narrow P6-only correction catches that child failure and saves the last
1 MiB of each output stream in unique, mode-0600 files under an owner-only
0700 `private-subprocess` directory in the **new external attempt root**. Original
byte counts, truncation and retained hashes are explicit. Raw files are never
copied into repository/CI evidence, printed, uploaded or committed automatically.
They can contain private paths or runtime output and require private owner review.

A standard-library bootstrap executes the byte-identical existing P4 checker with
unchanged argv/main/exit semantics, emitting a hash-bound `python-entered` marker
and allowlisted exception type/helper line on Python exceptions. Sanitized result
JSON contains fixed component/stage/stderr categories and private file basenames,
never exception messages, arguments, environment values or raw output. Markers
are diagnostic only: they cannot make a native check PASS. Existing P4 checks,
required evidence, timeout, security configuration and failure policy remain.

No production code, accepted P4 checker, packaging, permission, source/artifact,
signing or sandbox change is made. There is **no confirmed application correction**
and no evidence-based reason to modify application behavior at this checkpoint.

Clean-checkout verification: **43 focused tests + 15 subtests PASS**, including 11
new diagnostics tests; complete release/workflow suite **200 tests + 219 subtests
PASS**, one existing duplicate-ZIP warning. Ruff/formatting pass. Synthetic Python
children test bootstrap/import/exit/redaction behavior; Flatpak/Qt are never run.
Retained r3 and successful r2 hashes remain unchanged. Evidence and prior review
snapshots: `ci/evidence/p6/generation-A-launch-investigation/`.

**Current owner checkpoint:** authorize one instrumented GUI attempt using r2's
prepared inputs and fresh `gui-attempt-r4`. Do not rerun preparation, reuse/delete
r3, or publish private logs. Inspect only safe result JSON publicly; inspect the
new private stderr locally if failure recurs. The exact failing runtime component
remains unresolved until suitable native child evidence exists. P6 is CONDITIONAL.

## Advisory and licensing

The [upstream advisory](https://github.com/advisories/GHSA-g3hv-75wg-m249) affects
minimatch before 11.0.1. No patched 10.x release was available in the registry.
The narrow override changes minimatch 10.2.6 to 11.0.1 and adds its development-only
`@isaacs/nonrecursive-glob-match` helper. Node 24 satisfies the fixed package's
engine requirement. All other package resolutions remain unchanged.

ESLint, config-array and typescript-estree consume this matcher in development
checks. Inspected direct calls do not request optimizationLevel >=2. No
application/editor/API path into those callers was found; this is a bounded
reachability assessment, not a formal exploitability proof. Clean installed
consumers resolve the patched version. The adversarial regression tests repeated
`**/../` patterns at levels 0/1/2 within a hard child-process budget. Full frontend
regressions pass. **All 33 production frontend files are byte-identical to the
accepted application payload**, so a redundant Flatpak rebuild was avoided.
The historical P5C finding and accepted source lock remain intact; only the new
P6 source candidate is remediated.

Candidate OSV matching completed for 341 source-lock components with no matches,
and clean npm installation reported no registry audit findings. Neither clears
unenumerated runtime/native vulnerabilities. The expanded inventory identifies
PySide/shiboken 6.11.2, bundled Qt WebEngine 6.11.1 and runtime Qt 6.11.2 with
exact metadata/SPDX hashes. It indexes 34 upstream SPDX documents, 40 Python
metadata records, 2,971 ELF files and 1,553 notices across app/runtime trees. Unknown
licenses/versions, upstream NOASSERTION, static embedding, driver/extensions,
relationships and source correspondence remain limitations. See the inventory and
[license review](P6_LICENSE_REVIEW.md).

A separate scan of the **40 actual app/runtime Python metadata records** found
three matches in runtime-only Mako 1.4.1.dev0 and setuptools 80.10.2:
[Mako Windows lookup](https://github.com/advisories/GHSA-5639-2j2p-m4mx),
[setuptools macOS sdist exclusion](https://github.com/advisories/GHSA-h35f-9h28-mq5c)
and [setuptools Windows legacy wheel installation](https://github.com/advisories/GHSA-xmj3-9gf7-h52w).
Their documented OS/build preconditions are absent from the declared Linux
application use, and direct application source has no matching imports or API
calls. Packaging consumes prebuilt hash-locked wheels rather than building sdists
inside the runtime. These are **bounded not-reachable assessments; the packages
remain unpatched**. This is not proof about every native/third-party caller or
complete vulnerability clearance. No accepted runtime pin was silently changed.
Details and reassessment triggers are in `runtime-advisory-triage.json`.

Original-code/logo rights, use-composed-ref attribution provenance, MPL covered
source and Qt/LGPL/GPL/module obligations still prevent redistribution clearance.
Existing notices/fonts and metadata-only CC0 approval remain unchanged. MIT is a
recommendation for owner review, not a selected license. No missing attribution
or legal permission is invented.

## Local verification

A disposable detached checkout with independent Git objects starts at accepted
`bfa0b800…`; exact candidate files are overlaid explicitly. A new Python 3.12 venv
installs existing exact backend requirements and hash-locked PyYAML requirements;
`pip check` passes. npm ci installs the candidate from its lock in that checkout.
Tests do not use the development venv, node_modules or prebuilt frontend assets.
The first build begins with absent frontend/dist.

| Check | Actual result |
| --- | --- |
| Focused P6 regressions | **30 PASS** in 6.652 s |
| Complete backend/security/lifecycle/migration/packaging/CI/release suite | **693 PASS + 204 subtests**, 52.76 s, three existing warnings |
| Workflow contracts | **31 PASS**, also included above |
| Frontend lint and security regression | **PASS** |
| Frontend unit tests | **273 PASS** |
| TypeScript and production frontend build | **PASS**, existing large-chunk warning retained |
| Complete production-server Chromium suite, retries 0 | **21 PASS**, 2.4 min, including all five lifecycle tests and appearance/image regressions |
| Ruff, formatting, actionlint on all three installed workflows; exact CI contract | **PASS** |
| Disposable RSA-3072 primary/subkey backup/restore/sign/expiry/revocation/cleanup rehearsal | **PASS**, 1.770 s |
| Native actual runtime retrieval and real application HTTP remote install | **PASS** component checks, 233.451 s including launch attempt |
| Independent installed source/version/schema/runtime/commit/permission readback | **PASS** |
| Full real repository HTTP GET/HEAD/hash/MIME/cache verification | **5,559 files PASS**, 9.441 s final implementation |
| Real native GUI/application initialization | **BLOCKED / launch probe FAIL**, namespace restriction before Qt |
| Real A/B GUI update, rollback/reinstall persistence | **INCOMPLETE**; r2 preparation PASS; r3 runtime/A install PASS, verifier launch attempted and exited 1; no window or B update verified |
| Hosted P6 / public HTTPS / independent machine | **NOT EXECUTED** |

The first full Python run had 684 passes and two failures because `/tmp` had less
than the existing 5 GiB packaging precondition. Re-execution on an isolated
larger-volume TMPDIR passed; no test, threshold, retry configuration or production
code was weakened. Initial HTTP verification took 101.350 s before verified
manifest caching; final transport verification passed in 9.441 s with per-object
hash checks preserved. Intermediate records are retained as history.

Commands and full non-sensitive result summaries are retained in
`ci/evidence/p6/verification.json`, test records and checksums. No GUI result is
inferred from browser/headless results. No native negative-security result is
substituted from unit mocks: the accepted P5C 13 native negatives remain historical
and new actual-client distribution fault gates remain separately unexecuted.

## Actual native installation

The empty private client independently fetched KDE Platform 6.11 and graphics/
codec/style extensions over the network, then pinned and verified Platform commit
`76fa01ac42ecf45d2c5020ef80de1c474c0c2ae86a51a79e8fec44c48f9dc473` with both GPG
checks enabled. BaseApp is already bundled into the application. The real
production app installed through a generated trusted flatpakref and HTTP remote,
without --no-deps and without development dependencies in the client. Installed
source is accepted `1ee2077…`, version 0.1.0, schema 5, branch stable, x86_64 and
commit `da1bf73e…de1ac`. Effective permissions pass the unchanged P4 validator.

The subsequent `flatpak run` failed with the classified
`sandbox-namespace-unavailable` error. An independent `unshare -Ur` probe reports
`Operation not permitted`. The driver correctly records overall FAIL for that
combined launch execution, preserving the passing installation components. No
sandbox flags or host security were changed. The exact isolated Ubuntu owner
commands and manual observations are in the [runbook](P6_RELEASE_RUNBOOK.md).

Measured local snapshot is 302,485,829 bytes / 5,561 files including seals; these
are **local P6 measurements**, not fabricated hosted P5C measurements. Hosting
planning uses these figures. R2 Standard remains preferred subject to owner
approval of provider/domain/budget/gateway; no infrastructure was provisioned.

## Release candidate and remaining approvals

`ci/evidence/p6/release-candidate-manifest.json` ties reference source, CI, artifact,
bundle, OSTree, disposable key, generation, descriptors, notes and inventory.
Production key and endpoint are null; publication is disabled. It is an
owner-review candidate, not a final newly built P6 release. The eventual committed
P6 source, successful CI, final artifact/audit, production trust and corresponding
source/notices must be selected together before release.

One grouped owner package is in [P6_OWNER_CHECKS.md](P6_OWNER_CHECKS.md):

1. Review the exact local source/docs/evidence; authorize a commit/push only if
   desired. No such authorization has been received. Ordinary CI will test the
   new regressions and build/audit the final candidate; no manual P6 run is implied.
2. B is approved and r2 preparation is complete PASS. Review child-diagnostic
   retention/bootstrap instrumentation and separately authorize one fresh r4 GUI
   attempt using r2 as read-only input; investigate its actual child evidence.
   Complete actual-client interrupted update, bad trust,
   availability/cache and other unexecuted distribution cases on capable hosts.
3. Resolve license/logo/attribution/source obligations; approve permanent offline
   identity/custody/expiry and the separately reviewed production signing policy.
4. Approve provider, HTTPS endpoint, budget, gateway/conditional-write and credential
   boundaries before any external setup. Then separately authorize public HTTPS
   and independent-client verification. No deployment is currently ready to run.
5. Review the final artifact manifest and explicitly authorize tag/release/
   publication only after all required gates and formal P6 acceptance.

P5C closeout and P6 changes remain separate review groups in the proposed file
inventory. No main merge, production key, public tag/release or publication occurs.
