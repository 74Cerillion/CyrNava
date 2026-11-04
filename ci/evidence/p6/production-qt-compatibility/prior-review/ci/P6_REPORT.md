# P6 — Distribution, installation and update validation

**2 November 2026 — P6 — CONDITIONAL / FURTHER ACTION REQUIRED.**

Latest checkpoint: R11 completed edit/restart/first B update/rollback/native
backup-import/recovery and launched the final reinstalled B. It returned FAIL
only because the verifier demanded the original workspace's Dark preference in
a separately imported workspace. Backups explicitly exclude browser preferences.
Retained final preference evidence establishes absent overrides (System default),
not a saved Dark preference or its resolved light/dark rendering. Synthetic data
is intact. The local P6 harness now distinguishes import reset from normal
persistence and captures a new preference before reinstall. No native rerun was
performed and R11 remains recorded as FAIL. A targeted native post-import/reinstall
observation still requires owner authorization. Production ordinary-runtime
compatibility and the remaining release gates stay OPEN. Historical checkpoints
and prior report versions remain preserved below and in the evidence archive.

**Current targeted-B checkpoint:** the separate `ci/release/targeted_b.py`
entry point is implemented and clean-checkout verified. The targeted native test
has NOT run. The host currently lacks the required free capacity (about 1.2 GiB
available; 5 GiB minimum). The existing disposable signing key is valid at the
recorded check but expires 2 November 2026 at 09:32:43 UTC / 18:32:43 KST. Current
trust remains mandatory. See [targeted owner handoff](P6_TARGETED_B_CHECKS.md)
for the exact proposed command, two GUI interactions and stop conditions. No
execution authorization is implied by this local handoff.

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

**Historical checkpoint (subsequently executed as r4):** authorize one instrumented GUI attempt using r2's
prepared inputs and fresh `gui-attempt-r4`. Do not rerun preparation, reuse/delete
r3, or publish private logs. Inspect only safe result JSON publicly; inspect the
new private stderr locally if failure recurs. The exact failing runtime component
remains unresolved until suitable native child evidence exists. P6 is CONDITIONAL.

## R4 exact QtCore ImportError and runtime drift

The helper mapping is confirmed byte for byte. SHA-256 is
`8cec1f8e659063a05c9279aa5d89127a0325b5c7e8c138bdb48d0853d00bd248`; line 15 is
`from PySide6.QtCore import QTimer, QUrl`. Private stderr (281 bytes) hashes to
`e6256b39e537f8e51a8e434093850f0e1d331c13480290ebeb29274c9f4b75ab`; stdout
(322 bytes) hashes to
`663c6fc53ea085e210e7d96cfe10dbb1bd8ad93e345d5e753c427c2345481967`.
Neither was truncated. Both were inspected in place; raw contents remain private
and were not copied to repository evidence.

The sanitized actual error is `ImportError` from `QtCore.abi3.so`: undefined symbol
`_ZN14QObjectPrivateC2E16QtPrivate_6_11_2`, version `Qt_6_PRIVATE_API`. Demangled,
this is `QObjectPrivate::QObjectPrivate(QtPrivate_6_11_2)`.

Read-only ELF inspection independently establishes the native loading failure:

- Installed PySide6/shiboken metadata is 6.11.2. `QtCore.abi3.so` has an undefined
  requirement for exactly that versioned private constructor and needs
  `libQt6Core.so.6`.
- Its RPATH searches its origin, `/usr/lib/x86_64-linux-gnu`, and the neighboring
  shiboken directory. Neither origin directory contains the QtCore library. The
  active runtime provides `libQt6Core.so.6.11.3`.
- That provider exports the `QtPrivate_6_11_3` constructor, not the required
  `QtPrivate_6_11_2` constructor. The failure precedes QtWebEngine initialization
  and application-window creation.

Retrieval verified locked runtime commit
`76fa01ac42ecf45d2c5020ef80de1c474c0c2ae86a51a79e8fec44c48f9dc473`.
The active deployment after A installation is instead
`fb23e178d082b117df7924f9a84710992ec233ebc007385feb85d349c4c81415`, providing
Qt 6.11.3. A's normal dependency-resolving installation is the intervening
runtime-changing transaction in the recorded driver sequence. The driver checked
the application commit and runtime branch name, but did not re-read the runtime
commit after installation. Its install PASS did not establish that the previously
verified runtime remained active. r3 has the same later runtime, but its missing
stderr is not retroactively classified as a recorded identical ImportError.

The app ships no separate Python executable; runtime `python3` resolves to
Python 3.13. The packaged launcher matches source and runs
`python3 -B -m desktop.native` after changing to the application directory. The
verifier runs `python3 -u -`, adds app/backend module paths and has no
LD_LIBRARY_PATH override. Both use the installed PySide binding, native RPATH and
runtime provider. Buffering/bytecode flags and working directory do not supply the
missing C++ constructor. The normal launcher was not executed here; its QtCore
import is expected to encounter the same library combination, an inference from
the common load configuration rather than a newly executed application result.

Classification: an **incompatible installed application/runtime native-library
combination**, plus a confirmed **P6 post-install runtime-validation defect**.
This is not an observed Python-version error, sandbox denial or application logic
failure. The exact symbol mismatch and runtime drift are established without a
native probe, GUI rerun, library loading, package upgrade or rebuild.

The local correction is deliberately fail-closed. `RuntimeClient.verify_runtime`
re-reads the app's runtime ref and exact current runtime commit after installation;
`install_real` cannot return PASS on drift. The same guard runs before every native
phase, covering update/rollback/reinstall transactions, and records expected and
actual hashes on failure. It does not silently repin, disable dependency
resolution, edit the approved lock, change artifacts or override library paths.
It detects invalid test inputs; it does **not** claim to repair compatibility.
Signatures, permissions, sandbox settings and accepted P4 checks remain unchanged.

Seven new synthetic drift regressions pass. From a disposable clean checkout:
**50 focused tests + 15 subtests PASS**; complete release/workflow suite
**207 tests + 219 subtests PASS**, one existing duplicate-ZIP warning.
Ruff/formatting pass. Compatible Qt import after remediation is **UNEXECUTED**.
All r2/r3/r4 evidence and approved inputs are preserved. Sanitized ELF/hash/test
evidence: `ci/evidence/p6/r4-QtCore-ABI/`.

**Current owner checkpoint:** review a runtime-compatibility remediation plan,
not another full GUI run. For the exact locked A/B experiment, one candidate is an
explicitly reviewed restoration of the already approved runtime after dependency
transactions, with drift recorded and import-only validation before GUI. That
would not establish compatibility with updated Qt 6.11.3. Supported-runtime
compatibility and any rebuilt binding/package are separate decisions. None of
these mutations or native tests were performed. No additional native probe is
needed to identify this retained error; any future probe requires its own exact
reviewed command/scope and authorization first. P6 remains CONDITIONAL.

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
unenumerated runtime/native vulnerabilities. The historical inventory identifies
PySide/shiboken 6.11.2, bundled Qt WebEngine 6.11.1 and pinned-runtime Qt 6.11.2 with
exact metadata/SPDX hashes. It indexes 34 upstream SPDX documents, 40 Python
metadata records, 2,971 ELF files and 1,553 notices across app/runtime trees. Unknown
licenses/versions, upstream NOASSERTION, static embedding, driver/extensions,
relationships and source correspondence remain limitations. R4's later runtime
drift to Qt 6.11.3 is separately recorded above, not substituted into that snapshot.
See the inventory and
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
| Real A/B GUI update, rollback/reinstall persistence | **INCOMPLETE**; r4 QtCore import fails from a Qt private-ABI mismatch after runtime drift; no window or B update verified |
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
2. B is approved and r2 preparation is complete PASS. Review the confirmed r4 Qt
   private-ABI mismatch/runtime drift and a bounded compatibility remediation
   before any new native execution. No full GUI retry is currently justified.
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


## Owner-authorized historical-runtime remediation — local only

1 November 2026. P6 remains CONDITIONAL. The owner authorized an explicit historical
replay policy and read-only production compatibility assessment, with no native
execution. The consolidated design, exact owner commands, stop conditions,
production recommendation and open release blocker are in
[P6_RUNTIME_REMEDIATION.md](P6_RUNTIME_REMEDIATION.md).

`historical_runtime.py` provides an exact-commit opt-in, transaction before/after
readbacks, separate drift/restoration records, origin/URL/signature verification,
a bounded restore and bounded sandbox imports for both generations before any GUI.
Normal application dependency resolution is preserved; default runtime drift still
fails closed. Existing preparations/attempts are never reused as writable clients.
This host verifier is outside the production payload; production source, package
permissions, locks, P5B allowlist and signed A/B identities remain unchanged.

New regressions cover explicit opt-in, lock agreement, all six transaction labels,
wrong origin/trust, missing history, failed/wrong restoration, interrupted
transactions, module/provider validation, private import failures, data/evidence
preservation, normal dependency resolution and the two-generation GUI gate.
The earlier 223-test run was an intermediate successful regression run. Final
clean-checkout counts and exact source hashes are recorded in
`ci/evidence/p6/historical-runtime-remediation/tests.json` and `clean-source.json`.
No native import, GUI, renderer, ordinary runtime-update compatibility or production
packaging remedy is classified as PASS on the strength of these local tests.
Historical success/failure records remain preserved; earlier recommendations against
another unchanged GUI retry are superseded only by this explicit proposed mode.


Final local verification: **74 focused tests + 24 subtests PASS; 231 release/workflow
tests + 228 subtests PASS** in a disposable detached checkout with the exact P6
source overlay. Ruff check and formatting PASS. Twenty-four new tests were added.
The sole warning is the existing intentional duplicate-ZIP negative fixture.
No native runtime restoration, import or GUI was executed. No commit/push occurred.


## R6 historical restoration ordering correction — local verification

R6 remains a recorded native FAIL. Installation and app identity verification
succeeded; explicit historical authorization and `defer_runtime_check=True` reached
the install path. The strict post-install guard did **not** cause the failure.
The actual failed child was `ostree show --gpg-verify-remote=flathub <approved SHA>`
within `runtime-signature` (sequence 54, exit 1, 0.008 seconds). The local historical
commit and detached signature objects are absent after dependency installation,
with no parent object repository. The driver's pre-restoration full signature
check therefore required an unavailable local object and stopped before any
restoration. Original child stderr was not retained; no exact original error text
or independently failed restoration is claimed.

`historical_runtime.py` now checks explicit authorization, origin, URL and enabled
GPG enforcement before restoration without reading the missing old object. The
bounded Flatpak transaction retrieves/restores only the approved commit with GPG
checks intact. Exact commit/origin, independent OSTree signature verification and
fresh live runtime identity checks follow before import eligibility. Unexpected
drift or any failed check still stops execution. The successful original install
and ordinary runtime compatibility **false** remain separate from restoration.
Signature child failures now retain private raw output through the existing safe
diagnostic helper; public evidence contains categories/hashes only.

Implementation changes are confined to `historical_runtime.py`,
`native_diagnostics.py`, existing `test_historical_runtime.py`, and new
`test_historical_install.py`. `real_update.py`, `native_distribution.py`, production
application/packaging/runtime locks, P5B signing policy and accepted artifacts are
unchanged by this correction. Existing transaction mocks are adjusted for the
new policy/result boundary; eleven new integration/security regressions exercise
the actual install/replay/import gate using synthetic I/O.

The archived R6 implementation reproduces the early failure under the same
synthetic missing-object condition; corrected ordering reaches imports without
changing ordinary compatibility to true. Readback/evidence, reproduction, tests
and exact clean-source hashes are in `ci/evidence/p6/r6-restoration-order/`.
No native restoration, import, GUI, preparation, build, commit, push or GitHub action
was executed. See P6_RUNTIME_REMEDIATION.md for the updated proposed r7 command and
r8 GUI gate. P6 remains CONDITIONAL.


R6 correction final clean-checkout verification: **85 focused tests + 24 subtests
PASS; 242 release/workflow tests + 228 subtests PASS**. Ruff and formatting PASS.
Eleven new R6 regressions were added. The single existing duplicate-ZIP warning
comes from a deliberate negative fixture. Exact source overlays, test commands,
results and preservation hashes are in `ci/evidence/p6/r6-restoration-order/`.
No new native verification was executed.


## R9 post-reinstall profile-open investigation — 2 November 2026

**P6 remains CONDITIONAL. R9 overall FAIL is preserved.** R9's initial B update
passed, followed by rollback, native backup/import and recovery PASS. The failing
`gui-updated` was the second `updated` invocation, after uninstall/reinstall B.
It had already verified the window, renderer sandbox, backend authentication,
private network/filesystem, single-instance lock, Dark preference and owned-backend
cleanup. It failed between `owned_backend_reaped` and `saved_owner_edit_checks`,
where the unchanged production `Profile(profile_root)` is constructed.

The active-workspace pointer is valid and selects an existing schema-5 imported
workspace. Read-only source inspection and integrity validation **on disposable
copies** establish that the original and active imported database bytes, logical
content fingerprints and image trees match. Each contains one synthetic note,
folder and asset; SQLite integrity/foreign-key and existing P3 validation pass.
The inactive schema-6 workspace is the deliberate future-schema refusal fixture.
All three generations retain the synthetic records and asset. The complete retained
profile remains 96 files / 8,660,684 bytes with unchanged aggregate tree hash.
No data loss, bad pointer or missing workspace was found.

**The exact missing object and originating syscall are undetermined.** The original
helper suppressed filename, errno and traceback, and set its stage only after
construction. Private stderr's only diagnostic is the known Chromium system D-Bus
warning, not a Python traceback. Present-day file existence cannot reconstruct a
transient missing entry. Removal of a Qt profile/cache entry during Profile's
strict recursive scan is a plausible hypothesis; a deterministic synthetic test
reproduces that error path, but does not prove historical causality. An application
filesystem defect versus verifier teardown timing cannot yet be distinguished.

Only the confirmed diagnostic gap is corrected. The host-streamed native helper
persists an allowlisted stage **before** each direct profile reopen and records
OSError errno, bounded path category and storage-function/source-line frames. It
never emits raw filename, traceback path, message, note content or environment.
It still calls the unchanged Profile and propagates failures; no retry, delay,
exception suppression or filesystem/security relaxation was added. The P6 parent
now labels `reinstall-b` separately and keeps `phase-reinstall-b.json` distinct
from the earlier `phase-updated.json`; active/completed phase context is retained.
Existing security, saved-content and integrity assertions remain mandatory.

Exact implementation changes:

- `packaging/flatpak/production/native_check.py`
- `ci/release/real_update.py`
- New `packaging/flatpak/production/test_profile_diagnostics.py`
- New `ci/release/test_native_phase_context.py`

The report, owner checklist, runbook, runtime-remediation status and current review
indexes are updated. Prior helper/driver/docs and original R9 success/failure
summaries are preserved in `ci/evidence/p6/r9-profile-investigation/` alongside
integrity, preservation, clean-source and test evidence. Raw child output and
synthetic image bytes remain outside the repository. Production storage/application
code, package/permissions/runtime locks, historical policy, accepted A/B archives
and signed preparation are unchanged. No preparation, GUI, native import or
runtime transaction was repeated; no commit/push/GitHub action occurred.

Clean-checkout results: **17 focused tests PASS; 109 storage/migration/packaging
tests PASS; 244 release/workflow tests + 228 subtests PASS.** The helper's 14
pre-existing E402/E501 lint findings are unchanged (no new findings); the other
changed Python files pass Ruff and all four changed Python files pass formatting.
Existing duplicate-ZIP and FastAPI/Starlette deprecation warnings are recorded.

Another separately authorized instrumented native observation is necessary to
complete post-reinstall saved-content verification and obtain exact operation
information if the error recurs. It must use a fresh attempt; preserve R9 and r2
preparation. No speculative application fix is proposed. A passing rerun alone
would not establish the historical transient's cause. Native execution is not
currently authorized by this local investigation.


## R10 authorization and Codex bootstrap restriction — 2 November 2026

The owner authorized one fresh historical-runtime GUI verification at
`historical-gui-attempt-r10`. Preflight PASS: reviewed helper/driver match the
clean-tested source; corrected pre-profile diagnostics and reinstall context are
enabled; successful signed A/B preparation and approved archives are unchanged;
prior attempt evidence is intact; R10 did not exist; production storage, sandbox,
signing and runtime controls are unchanged. Host Wayland/session sockets exist.

One driver invocation was attempted through Codex. It returned complete FAIL with
`error: OSError` before creating the attempt directory. Independent filesystem
readback shows that Codex's mount of `~/.cache/p6` is read-only and not writable.
The child-only permission grant did not make the parent writable to create R10.
This is a host execution/bootstrap restriction, not an application, import,
renderer or R9 profile failure. Exact driver errno/traceback was not retained;
the read-only parent is independently established.

**R10 native verification: NOT RUN.** No RuntimeClient, native runtime transaction,
imports, GUI, data, update/rollback, maintenance/recovery, uninstall/reinstall or
final saved-content check was created or executed. No phase is marked PASS from
historical evidence. No runtime drift/restoration or new profile-failure result
exists. No automatic retry was performed. The original terminal FAIL and separate
NOT RUN classification are retained under `ci/evidence/p6/r10-native/`; no fake
owner-result was written into a nonexistent native attempt.

The owner can perform the already-authorized one native execution from the Ubuntu
terminal using the same corrected command and still-fresh R10 root. Do not run
again if an actual native attempt has since started; an actual failure needs a
separate owner decision. Do not repeat preparation or alter prior attempts. The
Codex bootstrap failure is not a completed native GUI observation.

P6 remains CONDITIONAL. Remaining gates include actual R10 completion, ordinary
supported-runtime-update compatibility (historical restoration does not close it),
licensing/notices/inventory review, production trust/final source-CI-release
approval, and authorized public HTTPS/independent-client distribution checks.
No application code or security settings changed; no commit/push/GitHub execution,
production keys, hosting or publication occurred.


## R11 preference-contract investigation — 2 November 2026

**Confirmed cause: verification-harness contract mismatch; no production defect
established.** P4's ordinary saved-edit assertion requires explicit Dark. P6 also
compared every restart/update/rollback preference hash with the original edit
hash. Those expectations remain correct before import. They are incorrect after
native backup/import activates a new workspace: `app.migration.pack` and its
validator explicitly exclude browser preferences, recovery drafts and unfinished
uploads. `Profile.activate_workspace` selects a separate workspace-specific Qt
WebEngine profile/cache without copying the previous profile's localStorage.
The production backup/storage/frontend implementation is unchanged.

Read-only R11 evidence (`ci/evidence/p6/r11-preference-contract/`):

| Observation | Actual result |
| --- | --- |
| Edit, restart, first B update, rollback | PASS including Dark; identical preference hash `70992515ae26d5f17712ddff6e52182309267109d0eb035fce68d6c884bfca85` |
| Native backup/import | PASS; new workspace activated, owner edits and database records preserved |
| Recovery | PASS; verified restore, future-schema refusal and previous profile recovery |
| Final B after reinstall | GUI/security/identity/backend cleanup and saved title/folder/image checks PASS; overall FAIL solely for Dark at `saved_owner_edit_checks` |
| Final saved preference state | Hash `6c70b52b441be65cbbcbaf8b798a9127ac0ca4195d4684a175fcb607fd95f3fa` exactly matches `{appearance: null, theme: null}` — no override, default System |
| Resolved light/dark at final launch | NOT RECORDED; OS-dependent, cannot infer from localStorage hash |
| Live post-import/pre-uninstall preference sample | NOT RECORDED; do not claim end-to-end preference persistence from a missing sample |
| R9 FileNotFoundError | Did not recur in R11; historical cause still unresolved |

The active pointer is valid and selects a genuinely new generation. Its separate
`web-profile-<generation>` directory exists alongside the original `web-profile`.
Read-only validation on disposable workspace copies confirms identical original
and imported schema-5 database bytes and logical content fingerprints: one note,
one folder, one referenced 354,837-byte image each, SQLite integrity/foreign keys
and existing P3 validation PASS. Rich-text/image references and asset hashes are
preserved. The intentional inactive schema-6 recovery fixture remains intact.
Profile inventory is unchanged: 95 files, 8,563,881 bytes, aggregate tree SHA-256
`d73d1aa3253db0719ff74b874e60af768a13fb57eeb8725eb75f2c4b5035dbf8`.
The original R11 driver reached final verification only after its before/after
uninstall/reinstall file-tree equality assertions passed. This supports storage
preservation but does not replace a missing live preference baseline.

### Narrow local correction

- `ci/release/preference_contract.py` (new): bounded read-only observations of the
  two appearance keys, resolved DOM scheme and system color preference. Separate
  explicit reset/preserve modes, tied to hashed workspace AND Qt profile identities.
- `ci/release/real_update.py`: original edit/restart/initial B update/rollback still
  require Dark and the original preference hash. After successful import/recovery,
  a distinct `post-import-baseline` GUI phase first verifies absent keys and correct
  System rendering; the owner then explicitly selects Light. The new Light state
  must be observed and recorded before uninstall. Final B requires that exact
  imported-workspace state and identity, not the original Dark hash. The original
  security/content requirements remain mandatory, and every failed check fails
  the phase. Host-streamed composite checker hashes are recorded.
- `packaging/flatpak/production/native_check.py`: a keyword-only explicit test hook
  and hashed workspace identities allow P6 to reuse P4's security and saved-data
  checks. Direct P4 `main()` still defaults to its original strict Dark assertion.
  No command-line/environment bypass or privileged JavaScript bridge is added.
- `ci/release/test_preference_contract.py` (new) and
  `ci/release/test_native_phase_context.py`: reset versus persistence, System
  resolution, new Light baseline, missing/invalid evidence, wrong profile, lost
  preferences during reinstall, cancelled callbacks, original P4 strictness,
  unchanged other requirements and phase-record preservation regressions.

No old failed Dark assertion is changed to PASS or removed from R11. The corrected
future phases use explicitly named reset/preserve checks. No production application,
backup, Profile storage, API, package, sandbox, runtime lock or signing policy changed.
Raw child output, note contents, screenshots and browser storage are not published.

### Local verification

Fresh detached no-hardlink checkout of the current accepted integration HEAD with
exact local P6 source overlays; existing `frontend/dist` copied only for backend
test prerequisites. No application rebuild, owner GUI/native rehearsal, preparation,
GitHub action, commit or push was performed.

- Focused: **52 PASS** (35 additional cases beyond the previous 17).
- Storage/migration/production packaging: **109 PASS**.
- Release/workflow: **279 PASS + 228 subtests PASS**.
- New/changed driver and tests: Ruff PASS; five changed Python files format PASS.
  Host checker retains its 14 pre-existing E402/E501 findings, with no new findings.
- Initial broad runs encountered genuine environmental disk limits: below 5 GiB
  build prerequisite and OSTree's 3% free-space floor. Original failed outputs are
  retained. Unchanged tests pass using a disposable empty memory-backed test volume;
  no safety check was reduced. Existing duplicate-ZIP/deprecation warnings remain.

Commands, source hashes, outputs, private-log hash verification and before/after
preservation records are saved under the R11 investigation directory. These are
local synthetic results, not native acceptance or proof that the new GUI sampling
has run successfully.

### Smallest next native proposal — NOT AUTHORIZED / NOT EXECUTED

A full A/B rehearsal is unnecessary to establish R11's earlier passing phases.
Retain those actual results. For the remaining gap, propose two GUI launches around
one B uninstall/reinstall in a NEW isolated, identity-verified client:

1. Read-only validate and copy only R11's verified synthetic imported workspace
   into a fresh private profile, with fresh Qt storage. Never open or modify R11
   itself with Profile/Qt. Preserve and independently hash the source before/after.
2. Verify the approved signed B repository, source/OSTree/application identity and
   exact historical runtime origin/signatures; ordinary compatibility stays FALSE.
3. First launch: prove System default and correct OS resolution, then explicitly
   select Light; require saved note/folder/image/database/security/backend checks
   and capture a workspace-bound live Light baseline.
4. Uninstall/reinstall the same approved B without deleting data. Require whole
   private-data tree equality, exact B identity and authorized runtime restoration
   with independent commit/origin/signature validation before the second launch.
5. Second launch: require the same Light snapshot/hash, workspace identity, all
   saved-content/image/database/security checks and backend cleanup. Stop on any
   discrepancy; no retries. Keep diagnostic output private and evidence separate.

This bounded targeted entry point has not been implemented or executed. The
current `gui` command still performs the complete sequence; do not run it as a
substitute. Prepare/review the exact targeted command and its fresh directory
before requesting one native execution authorization. No preparation repeat is
needed. A new successful observation cannot rewrite R11's original FAIL or prove
R9's transient filesystem cause.

Remaining P6 blockers: targeted native verification of the corrected preference
contract; supported ordinary-runtime-update compatibility (historical replay is
not resolution); final redistribution/license/notices/inventory/trust review and
approved production source/CI/release; separately authorized public HTTPS and
independent-client distribution validation. P6 remains CONDITIONAL.


## Targeted B-only implementation and owner handoff — 2 November 2026

**LOCAL IMPLEMENTATION PASS / NATIVE NOT EXECUTED / P6 CONDITIONAL.** This section
supersedes the prior R11 checkpoint's statement that the targeted entry point was
not yet implemented. All historical R9/R11 results remain unchanged.

### Implementation and exact changed paths

New files:

- `ci/release/targeted_b.py`: separate explicit B-only CLI and supervisor; no full
  A/B GUI command or preparation call. Two real B launches surround one normal
  uninstall/reinstall, using the existing approved signed repository only.
- `ci/release/targeted_workspace.py`: strict bounded read-only retained inventory,
  existing-lock protection, P3 immutable SQLite/reference validation, exact
  synthetic-only copying and complete file/empty-directory preservation checks.
- `ci/release/targeted-b-policy.json`: fixed approved B/preparation/trust/R11 hashes,
  schema/version/identity and original synthetic data fingerprints. No personal
  contents, browser storage, signing credentials or private paths.
- `ci/release/test_targeted_b.py`: **103** synthetic cases covering identity,
  artifacts, unsafe/missing data, isolation, runtime/signature/import faults,
  preinteraction evidence, preference loss/reselection, missing baseline,
  complete tree preservation, failures, interruption and retained diagnostics.
- `ci/P6_TARGETED_B_CHECKS.md`: exact proposed owner command, capacity and signing
  validity prerequisites, click-by-click instructions for both windows and stops.

Modified files:

- `ci/release/preference_contract.py`: also records the actual selected Appearance
  option. Before input it requires absent keys + selected System + correct OS
  resolution, or the original Light baseline on launch two. Workspace AND Qt
  profile identities are bound. Any observed later preference mismatch stays
  failed even after reselection. The original baseline is never replaced.
- `packaging/flatpak/production/native_check.py`: the explicit P6 hook disables
  its test window before `show()`, records actual live Profile identity from the
  owned backend, persists preinteraction evidence, then shows owner instructions
  and enables input. Wrong evidence quits the failing test; missing readiness
  fails after a 45-second bounded gate. P4's default path is unchanged. This
  host-streamed checker is not in the production payload.
- `ci/release/historical_runtime.py`: add only `install-b` to the reviewed
  transaction allowlist; reuse the existing drift/restoration/signature/live
  identity protocol without changing its guards or production runtime locks.
- `ci/release/progress.py`: add fixed operation labels for the targeted supervisor;
  existing bounded child execution and interruption behavior remain unchanged.
- `ci/release/test_preference_contract.py`,
  `ci/release/test_native_phase_context.py`: adapt synthetic observations to the
  stronger selected-mode/preinteraction evidence; retain every prior case.
- `ci/release/test_historical_runtime.py`: require seven recorded transactions,
  preserving the original six plus initial B. New exact-allowlist regression
  prevents removing an old transaction or silently adding capabilities.
- `ci/P6_REPORT.md`, `ci/P6_OWNER_CHECKS.md`, `ci/P6_RELEASE_RUNBOOK.md` and
  `ci/evidence/p6/{proposed-files.json,SHA256SUMS.json}`; new non-sensitive evidence
  under `ci/evidence/p6/targeted-B-verification/`.

`ci/release/real_update.py` was not modified in this checkpoint; its complete A/B
mode remains distinct. Production application/backend/frontend/Profile/backup
code, workflows, packaging/permissions, runtime locks and signing policy are
unchanged. Earlier P6 frontend dependency work and P5C closeout are preserved.

### Sequence and fail-closed properties

The new attempt must be a fresh `targeted-b-attempt-*` sibling of the approved
`real-pair-r2` and retained R11 root, outside the source tree. The driver refuses
existing roots, symlinks, traversal and normal application paths. It checks a
5 GiB free-space floor before any native operation. Input preflight binds source,
CI run/attempt/artifact ID, ZIP and bundle hashes, build inputs/inventory, OSTree
commit, version, schema, public key and original approval SHA. Successful signed
preparation, source data and original failure evidence are pinned. The raw public
ZIP's reviewed ordinary readable modes are allowed only for an owned regular
single-link file; world-writable/executable/special objects are refused. Private
source/profile/approval modes remain strict.

Signed B is verified and activated solely in the fresh attempt's local store,
then served on literal loopback. It creates no new signing key and publishes
nothing publicly. A new RuntimeClient has private HOME/Flatpak/XDG directories;
normal application profiles/installations are never queried. The default package
network/filesystem/renderer/authentication protections remain mandatory.

Normal runtime dependency resolution is retained. Initial B installation and
reinstall are journaled separately; drift may only be restored under the explicit
approved historical policy, followed by independent origin/GPG/signature/live
commit validation and bounded compatible Qt import probes. Before/after probes
use separate evidence directories. The top-level ordinary-runtime compatibility
result remains FALSE even if historical restoration passes.

Only the approved synthetic active workspace is copied. R11's existing instance
lock is opened read-only; no production Profile is instantiated on R11. Its full
file and empty-directory state is checked before/after copy. New Qt storage/cache
is empty; original Qt files, other workspace generations and browser state are
not copied. The copy receives a new private profile and is independently validated
before launch. Strict source snapshot ordering matches the original R11 pathlib
inventory; a regression covers Qt profile directory prefix ordering.

The first test window cannot accept input before System/reset/OS/identity evidence
is persisted. The owner confirms synthetic content and selects Light. Only a
complete native PASS, exact saved Light baseline and copied-data validation permit
uninstall. The driver preserves the baseline file and hash, rechecks current key
trust, installed B identity and complete private-data state. Uninstall never uses
`--delete-data`; same-B reinstall rechecks commit/source/version/schema/permissions,
authorized runtime restoration and signing trust. Any changed file, empty directory
or baseline stops the second launch.

The second window is likewise blocked until original Light and both identities
are verified before input. A later selection cannot repair an observed loss. The
same original native security/saved-data requirements remain mandatory; only the
incorrect original-workspace Dark requirement is replaced with explicit imported
preference checks. The final database/record/asset fingerprint is independently
validated. Missing assertions, filesystem failures or interruption produce FAIL;
there is no retry. Safe child stage/errno/storage-line metadata and private raw
output are retained on failures. Bootstrap rejection emits a complete stdout FAIL
without writing to an unsafe/existing root.

### Verified inputs and preservation

Read-only inspection confirms B source `bfa0b8005a3ddc519354fd7907e9b972fde8126b`,
CI `41285343063` attempt 1, artifact `13075346402`, ZIP
`2d11ce5057ae66cd4dc526dac607a2344b89dbc1fcef5e62038ad59583c93fbe`, bundle
`ef732c240d8a01e33a638cd10e83fb985c7ba9e678b573ba508cd48c3934f47c`, and OSTree
`f759380dca9aa36e4674ad6dffb24d3e2340342da5fe04537ac17031a3bada15`.
Version remains 0.1.0/schema 5; production identity remains
`io.github._74Cerillion.CyrNava`.

Preparation SHA `0740b8d035d7db2904ca45d1f7bdd7265fba9157f1313d2440a83e1f2b8d5099`,
original B approval SHA `53aa5025f977629cf6ba3920b390493b6da257987663279d7e1e85c28f231a22`,
A ZIP, R11 evidence/private-output hashes and profile fingerprint are unchanged.
The original approval's legacy authorization-reference wording remains pinned;
it is not rewritten to manufacture new consent.

An actual copy of the retained **synthetic** workspace was locally tested in a
throwaway memory-backed directory, independently validated and removed. Original
R11 file/directory state remains unchanged; database bytes, note/folder/image
counts, rich text, references and asset hashes match. This was only a local data
copy check, with no Profile/Qt/application/runtime operation. Raw contents were
not placed in repository evidence. The proposed R12 native attempt does not exist.

Existing signed-manifest verification and the entire signed B public file tree
PASS. Independent current-signature verification PASS at
`2026-11-02T03:14:08Z`; fingerprint
`B8882601428AC0F08E9209FC353B6BEE05E7D9FC`, public key SHA
`26760a8972ac9ea2eedc63830fb0abf8b0f918e9c06808c81a0c884abc3311d4`.
The key expires **2026-11-02 09:32:43 UTC / 18:32:43 KST**. No key renewal,
clock override, expiry bypass, re-signing or re-preparation is authorized. Native
OSTree/client validation is still required during the future targeted execution;
read-only signed-manifest validation is not reported as a new native rehearsal.

### Clean local results

Fresh detached no-hardlink checkout at `bfa0b8...`, exact source/policy overlays,
existing frontend assets copied only for backend-test prerequisites. Final source
hashes and commands are recorded in the new evidence directory.

- **202 focused tests + 10 subtests PASS.**
- **109 storage/migration/production packaging tests PASS.**
- **382 release/workflow tests + 229 subtests PASS.**
- Changed/new driver/tests pass Ruff and formatting. The host helper retains its
  14 pre-existing E402/E501 findings, with no new findings or global suppression.
- Existing duplicate-ZIP and framework deprecation warnings remain documented.

Existing storage/security/signing/lifecycle/workflow regressions remain enabled.
These are synthetic local results; native PASS is not inferred from mocks. No
application rebuild, real A/B preparation, native runtime installation/restoration,
GUI, commit, push or GitHub execution occurred.

### Owner checkpoint and remaining blockers

The exact command and both GUI procedures are in
[P6_TARGETED_B_CHECKS.md](P6_TARGETED_B_CHECKS.md). Request separate authorization
for one execution only after capacity is sufficient and current signing trust is
valid. The host currently has about **1.2 GiB free**, below the 5 GiB gate; native
execution is therefore not currently ready. Do not delete retained evidence or
personal data without separate approval. If the key expires first, stop for a
separate trust/preparation decision rather than bypassing policy.

Outstanding: actual targeted native preference/reinstall verification; ordinary
supported-runtime compatibility; redistribution/licensing/notices/inventory and
production trust/final source-CI-release approval; authorized public HTTPS and
independent-client distribution verification. R11 remains original FAIL, its
previous actual passing phases are retained, and R9's missing object remains
unresolved. P6 is not accepted or ready for public release.
