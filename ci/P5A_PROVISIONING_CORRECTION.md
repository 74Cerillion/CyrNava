# P5A provisioning correction — local review

31 October 2026. Branch `desktop/p2-production-integration`; base
`6743d1d5c76f2db87c2debb6f687a6e57a6826b6`. No commit/push/Actions trigger authorized.
P5A remains **FAIL / NOT ACCEPTED**, pending hosted verification and owner acceptance.

## Cause and uncertainty

The provisioner installed and pinned Platform, then SDK, then BaseApp. A later
install can update an already pinned dependency. Hosted run 41179709348 logs
Platform updating during BaseApp installation, followed by a generic ValueError.
The old implementation is demonstrably sensitive to this dependency drift (retained
historical control-flow simulation). The final failing ref, actual SHA and exception
message were not recorded; the exact hosted mismatch remains unproven.

No production application, browser, lifecycle or SQLite-guard defect is implicated.
All application gates passed in that hosted run and remain preserved.

## Correction and files

`ci/flatpak.py`: complete dependency installation before any final pin; enforce
all three exact commits with `flatpak update --no-deps --no-related --commit=…`;
verify every installed SHA, then call the unchanged production verifier. No installs
or updates occur after final verification. Missing commits and wrong SHAs fail
without retries or substituting newer versions. `--no-deps` applies only after
normal dependency installation; it does not disable GPG or SHA verification.

Structured `prepare.json` failures preserve stage, dependency operation, approved
ref, expected SHA, actual SHA if readable, exception type/message and FAIL outcome.
Final verification includes all three checks. Missing/unreadable commits are null,
not success. Malformed commit output is excluded. Diagnostics omit captured command
output, environment and arbitrary remote configuration; subprocess messages contain
only the fixed approved arguments. The original generic-error record is preserved.

`ci/test_ci.py`: eight deterministic provisioning tests cover normal order, BaseApp
Platform drift restored, incorrect final SHA, unavailable commit without fallback,
runner/GPG controls, complete failure evidence/no build, failed info diagnostics,
and malformed/unavailable commit output. Existing CI tests remain intact.

Documentation: `ci/P5A_REPORT.md`, `ci/P5A_OWNER_CHECKS.md`, this report.
Evidence: `ci/evidence/p5a/validation.json` (append-only correction field) and
`ci/evidence/p5a/provisioning-correction-2026-10-31/`.
Preexisting fifth-run documentation/evidence and image-correction hosted results
remain separate, preserved change groups; they are not new production changes.

## Compatibility and security

P4 toolchain lock, requirements lock, identity, manifest, payload allowlist, package
content audit, checksum/provenance and workflow are unchanged (security-review.json).
The production builder checks refs before assembly and again before export; its
build-init copies installed dependencies and does not install/update runtime refs.
The real isolated remote reports GPG verification true. No credentials or owner
workspace data were accessed or added. No tests/security protections were removed.

Expected final commits (unchanged):

| Ref | SHA-256 |
| --- | --- |
| org.kde.Platform//6.11 | 76fa01ac42ecf45d2c5020ef80de1c474c0c2ae86a51a79e8fec44c48f9dc473 |
| org.kde.Sdk//6.11 | df314f9c067cba031e153a2f3b0be53bd13c1eca6baa78b68982a1d35b873a86 |
| io.qt.PySide.BaseApp//6.11 | a6cddcbcf58032e3f22c66a98779cc07685d376e52718e5aee307ad9aeb1bb8e |

All three exact-commit metadata queries succeeded in an isolated installation.
Metadata declares the expected x86_64/6.11 Platform and SDK. No incompatible declared
dependency was found; this does not establish ABI compatibility or deployment success.
The hosted Flatpak 1.14.6 source supports the chosen flag: [official update source](https://github.com/flatpak/flatpak/blob/1.14.6/app/flatpak-builtins-update.c).
Its option calls `flatpak_transaction_set_disable_dependencies`; see also the
[official command reference](https://docs.flatpak.org/en/latest/flatpak-command-reference.html#flatpak-update).
Local CLI 1.16.6 independently lists the same option. Sources/options retained in evidence.

## Verification

Disposable clone: `/tmp/cyrnava-p5a-provision-clean-pxm40rnc/checkout`, checked out
at exact base HEAD, overlay only `ci/flatpak.py` and `ci/test_ci.py`; hashes recorded.
Python 3.12 interpreter/dependencies reused from an external disposable environment;
source and frontend assets are from this clean checkout, not the development tree.

Commands from that checkout (Python denotes that recorded Python 3.12 interpreter):

```bash
python -m unittest ci.test_ci.ProvisioningTests
python -m unittest ci/test_ci.py
npm --prefix frontend ci --ignore-scripts --no-audit --no-fund
npm --prefix frontend run build
python -m pytest -q packaging/flatpak/production/test_packaging.py backend/tests/test_lifecycle_harness.py
python -m ruff check --isolated --select E,F,I ci/flatpak.py ci/test_ci.py
```

Results: **8 provisioning tests PASS (included in 31 CI contracts PASS); 45 packaging
and lifecycle-harness tests PASS**, one existing Starlette deprecation warning;
Ruff PASS; TypeScript/production frontend build PASS with existing chunk-size warning.
Counts overlap: do not add eight again to 31. Mocked provisioning tests prove control
flow/failure handling, not successful hosted deployment. No full application/browser
rerun: no application changes, and latest hosted 559+31 backend, 273 unit and 20 browser
results are preserved, not relabeled as fresh local results.

Initial local failures are preserved: old tmpfs had less than the builder's required
5 GiB (two build-directory contracts failed); test temporary output moved to an
isolated disk directory, retaining the 5 GiB gate. Packaging tests initially lacked
frontend/dist in the clean clone (43 passed, two failed); a fresh frontend production
build satisfied the existing prerequisite, then all 45 passed. No tests were weakened.

Real operations, isolated FLATPAK_USER_DIR/XDG directories: remote-add PASS and exact
locked-commit metadata 3/3 PASS. Real Platform install returned exit 1 while pulling:
`open(O_TMPFILE): Read-only file system`. Separate namespace probe failed:
`unshare: write failed /proc/self/uid_map: Operation not permitted`.
Full real provisioning/build/audit therefore remain unverified locally. No security
bypass or host configuration change was attempted; disposable install data was removed
only after saving diagnostics. Existing owner installations were not modified.

## Recommendation and checkpoint

Ready for one authorized P5A-only commit and push. The next automatic hosted run must
prove provisioning and all existing application gates, production build, exported
package audit, unsigned upload, independently checked SHA/provenance and required gate.
Do not call P5A PASS before that evidence exists. No further commit/push/rerun/dispatch,
release/signing/distribution, main merge, P5B or P5C is authorized by this local task.


## Hosted outcome — sixth run verified PASS

Owner completed the authorized push of `1ee2077b283b8e5dfc2162119dd439ed3baeb109`.
Run 41181510439/attempt 1 verifies the corrected dependency/pin sequence: all three
final actual SHAs explicitly equal the unchanged locks. Workflow contracts (31),
backend/security (567 +31 subtests), units (273), browsers (20), production build,
exported package audit, unsigned upload and required gate all PASS. Independently
verified four ZIP digests, bundle SHA/checksum and source/run/lock provenance.
See current P5A_REPORT and hosted-provisioning evidence. Additional local payload
re-extraction is BLOCKED by read-only O_TMPFILE; no local payload audit PASS claimed.
P5A recommendation is now PASS for owner acceptance; no further commit/push or rerun.
The earlier FAIL statements above describe the preserved pre-hosted checkpoint.


## Formal owner acceptance

The owner explicitly accepted P5A on 31 October 2026, citing hosted run 41181510439
and implementation commit 1ee2077. The acceptance record retains the successful
hosted gates and the blocked additional local re-audit without changing either.
Documentation-only closeout is authorized. Prepare `p5a-accepted` only after the
closeout commit is synchronized with origin. No main merge, P5B or P5C is authorized.
