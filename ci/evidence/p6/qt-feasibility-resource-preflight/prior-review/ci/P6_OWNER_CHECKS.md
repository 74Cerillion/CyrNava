# P6 owner acceptance checklist

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


Unchecked items are unexecuted or unresolved, never implied PASS.

- [x] P0–P5C formally accepted; P6 local implementation authorized.
- [x] Local dependency remediation and full local regression evidence produced.
- [ ] Owner reviews that correction and evidence.
- [ ] Shipped inventory, advisory triage and third-party obligations reviewed.
- [ ] Original code/logo license and attribution resolution approved.
- [ ] Production trust anchor, offline ceremony and rotation/recovery approved.
- [x] Two exact real application build identities approved for disposable native A/B exercise; original source allowlist unchanged.
- [x] First preparation failure investigated; B audit approval mismatch reproduced and P6 driver corrected locally.
- [x] Owner authorized corrected preparation and GUI execution against real-pair-r2.
- [x] Retained r2 preparation is complete PASS, including both payload audits and key cleanup.
- [x] First GUI interruption investigated; runtime retrieval had not completed and no A launch is established.
- [x] Owner executed corrected r3 GUI driver: runtime retrieval and A installation/identity checks PASS.
- [x] r3 verifier exit 1 investigated; missing retained child stderr prevents a confirmed application/root-cause diagnosis.
- [x] Owner executed r4; retained private hashes and helper line mapping verified.
- [x] r4 QtCore private-ABI mismatch and post-install runtime drift confirmed without a native rerun.
- [x] P6 fail-closed runtime identity guard passes local regressions; this detects drift and does not repair compatibility.
- [ ] Owner reviews runtime-compatibility remediation before authorizing any further native probe or GUI execution.
- [x] Local isolated real remote install retrieves runtimes and verifies identity.
- [ ] Owner-machine GUI/native operation and independent client verification.
- [ ] Sandboxed native GUI, synthetic persistence, portals, backup/recovery pass.
- [ ] Real A/B update, rollback and reinstall preservation pass.
- [ ] Failure and publication/cache/retention checks pass.
- [ ] Hosting/provider/domain/cost and publication privileges separately approved.
- [ ] Authorized public HTTPS and independent clean-client checks pass.
- [ ] Release-candidate identities, notes, SBOM, notices and runbook reviewed.
- [ ] Commit/push/hosted P6 execution separately authorized and verified.
- [ ] Public tag/release/publication separately authorized.
- [ ] Formal P6 acceptance.

## Grouped next decisions

1. Review local P6 changes and the preserved P5C closeout; separately authorize any
   desired commit/push. Exact groups are in `ci/evidence/p6/proposed-files.json`.
   No commit, push or workflow dispatch is authorized by this checklist.
2. The owner approved the exact already-built B in `real-B-approval-proposal.json`
   for a disposable real-update exercise. Its copy `ci-output/p6-owner/B-approved.json`
   is true-valued; the false proposal is unchanged. A remains pinned P5A. Both use
   0.1.0/schema 5. Review the confirmed first preparation failure and locally tested
   P6 audit correction. Owner-executed `real-pair-r2` preparation is now PASS.
3. Preserve interrupted r2 and failed r3/r4 clients/results. Review the confirmed
   PySide6 6.11.2 versus active Qt 6.11.3 private-ABI mismatch and compatibility
   remediation first. No full GUI/preparation repeat is currently justified.
   Any future native probe needs exact command/scope review and authorization.
   Keep private-subprocess files local; provide sanitized summaries only.
   Provide only prepared/result/phase JSONs, not raw profiles,
   keys, screenshots or repository/package archives as public evidence. Native
   real-client fault cases and ordinary launcher/offline/logout observations
   remain separate required checks; the scripted happy path is not full P6 PASS.
4. Select original-code license/holder and approve logo rights; resolve upstream
   attribution and corresponding-source obligations with an appropriate review.
5. Approve the offline identity/expiry/custody/backup plan before permanent keys;
   approve provider/domain/budget/conditional gateway before hosting. These are
   decisions for review, not requests to create keys or deploy now.
6. Separately authorize final hosted/public HTTPS and independent-client checks,
   then formal acceptance and any tag/release/publication.

Original P5A artifact expiry: 7 November 2026, 07:53:28 UTC. Keep verified local
replay separate from live eligibility. Never silently replace an expired input.


## Historical runtime remediation checkpoint — 1 November 2026

- [x] Local opt-in policy and regressions prepared; ordinary path remains fail-closed.
- [x] A/B archive checksums and retained r2/r3/r4 metadata independently unchanged.
- [x] Raw child logs remain private; no native operation executed for this correction.
- [x] Proposed procedure and production assessment delivered in P6_RUNTIME_REMEDIATION.md.
- [ ] Owner review of final source/evidence and separate native execution authorization.
- [ ] Fresh-client A AND B bounded imports, runtime restoration/trust evidence accepted.
- [ ] Separately authorized GUI/lifecycle verification (or an explicitly authorized
  combined command with both imports enforced before GUI) completed.
- [ ] Production normal runtime-update compatibility resolved and independently tested.

Historical replay success cannot close the last checkbox or authorize publication.
Do not execute the proposed commands until separately authorized. Preserve every
attempt directory; do not repeat preparation or modify the successful signed pair.


## R6 correction checkpoint

- [x] Complete r6 records inspected and hashed; original attempts preserved.
- [x] Confirmed install/authorization success and premature full signature check.
- [x] Recorded native r6 FAIL, no imports or GUI reached, ordinary compatibility false.
- [x] Local correction and synthetic positive/negative regressions prepared.
- [ ] Separate owner authorization for imports-only fresh r7 execution.
- [ ] Review r7 restoration/signature/live-identity and A/B import evidence.
- [ ] Separate authorization for GUI; retain all earlier attempts unchanged.

No real runtime compatibility or restoration PASS is inferred from local tests.


## R9 evidence and pending diagnostic checkpoint — 2 November 2026

- [x] R7 A/B imports PASS independently read back; no GUI claimed from that result.
- [x] Preserve R9 edit/restart/first B update/rollback/backup-import/recovery PASS.
- [x] Record post-reinstall B FAIL separately; retain all seven partial PASS checks.
- [x] Verify active pointer and intact original/imported data/assets on disposable copies.
- [x] Add safe pre-construction stages and filesystem operation diagnostics.
- [x] Preserve prior update records with separate reinstall context; local tests pass.
- [ ] Exact historical missing object/operation identified (not retained by old helper).
- [ ] Separate owner approval for a fresh instrumented native observation.
- [ ] Post-reinstall saved-content verification and final P6 acceptance complete.

No production storage correction is justified by the existing evidence. A Qt
profile scan/cleanup race remains a hypothesis, not an established R9 cause.


## R10 authorized execution handoff — 2 November 2026

- [x] One fresh R10 historical native GUI run explicitly authorized.
- [x] Corrected source, instrumentation, isolation and unchanged controls verified.
- [x] Approved preparation/archives and retained attempts verified unchanged.
- [x] Record Codex bootstrap FAIL separately: parent cache directory is read-only.
- [x] Stop without automatic retry; no R10 directory/client or native phase exists.
- [ ] Owner-terminal execution of the authorized still-unstarted R10 native run.
- [ ] Actual R10 edit/restart/update/rollback/backup/recovery phases verified.
- [ ] Actual R10 reinstall/profile-open/saved-content/image integrity verified.
- [ ] Actual R10 runtime/app identity and drift/restoration records reviewed.

No R10 PASS is inferred from R9. R9's FileNotFoundError remains an unresolved
historical observation even if a later authorized run passes. Normal-runtime
production compatibility and remaining public-release requirements remain OPEN.


## Current R11 checkpoint — supersedes prior next-run examples

- [x] Retained edit/restart/first B update/rollback Dark persistence PASS.
- [x] Retained native backup/import and recovery PASS; imported workspace is new.
- [x] Final B GUI/security/saved title/folder/image checks PASS; original overall FAIL preserved.
- [x] Confirm final stored keys are absent (System default); resolved light/dark not recorded.
- [x] Confirm backup exclusion and workspace-specific Qt storage explain the invalid Dark requirement.
- [x] Read-only copied-workspace database/asset validation PASS; R11 source unchanged.
- [x] Local P6 correction distinguishes import reset from normal persistence.
- [x] Original P4 default Dark semantics and all security/content checks retained.
- [x] Clean local focused 52, storage/migration/packaging 109, release/workflow 279 + 228 subtests PASS.
- [ ] Live imported-workspace baseline captured before reinstall (absent in R11).
- [ ] Reviewed targeted two-launch post-import/reinstall driver/command ready.
- [ ] Separate owner authorization for that ONE targeted native execution.
- [ ] Actual new preference persistence after reinstall verified; no historical PASS substituted.
- [ ] Ordinary supported-runtime compatibility and remaining licensing/trust/public distribution gates closed.

No native rerun is currently authorized. Keep R11 FAIL and R9's historical unknown
cause. No production backup/storage change, native execution, preparation, commit,
push, GitHub action, production key or publication occurred during this correction.


## Current targeted-B handoff — supersedes prior unimplemented-proposal checkpoint

- [x] Separate explicit B-only entry point and pinned policy implemented.
- [x] Approved B/preparation/trust/R11 identities independently read back unchanged.
- [x] Actual retained synthetic copy locally verified without Profile/Qt/native operations; copy removed.
- [x] Fresh Qt storage and preinteraction System/OS/workspace/profile evidence required.
- [x] Exact new Light baseline bound before uninstall; original baseline preserved through reinstall.
- [x] All prior native data/security assertions retained; P4 normal Dark checks unchanged.
- [x] Clean local focused 202 + 10 subtests, storage/packaging 109, release/workflow 382 + 229 subtests PASS.
- [x] Exact proposed command, two-window instructions and stops prepared in P6_TARGETED_B_CHECKS.md.
- [x] Native attempt R12 remains uncreated; R9/R11/preparation preserved.
- [ ] At least 5 GiB free on the native attempt volume (about 1.2 GiB observed).
- [ ] Current disposable signing trust valid at execution; expiry 2026-11-02 09:32:43 UTC / 18:32:43 KST.
- [ ] Separate owner authorization for ONE targeted invocation; no retries or full A/B repeat.
- [ ] Actual targeted native PASS independently reviewed, with original Light baseline and all data/security checks.
- [ ] Ordinary runtime compatibility and remaining production release gates closed.

No native PASS is claimed from local fixtures. The command is prepared, not run.
If capacity/trust fails, stop for a new owner decision; do not alter prior evidence,
change clocks, extend keys, re-sign or repeat preparation under this authorization.

## Production Qt compatibility assessment — current checklist

- [x] Independently read R12 PASS and unchanged synthetic/import/reinstall evidence.
- [x] Preserve accepted A/B ZIP/preparation/approval hashes and R9/R11 failures.
- [x] Trace QtCore's exact private constructor to upstream QIOPipe/Qt source.
- [x] Inspect app/runtime providers, Python ABI, WebEngine, RPATH and plugin dependencies.
- [x] Hash upstream recipes and exact 6.11.3 official-wheel experiment inputs.
- [x] Four host imports and QCoreApplication PASS; all loaded Qt from disposable wheels.
- [x] Four real ELF private-symbol comparisons match positive/negative expectations.
- [x] Clean regressions: 382 release/workflow + 229 subtests, 158 backend/packaging, 273 frontend unit PASS.
- [x] Preserve initial wrong-cwd backup CLI failure; unchanged suite passes from backend/.
- [x] Keep production manifest/locks/launcher/auditor/permissions unchanged.
- [ ] Review whole-stack app-owned source-build proposal and build capacity.
- [ ] Implement/audit coherent replacement with preserved Flatpak renderer sandbox.
- [ ] Verify Flatpak Python 3.13 imports, actual launcher, Wayland and native portals.
- [ ] Verify ordinary runtime update with unchanged candidate and distinct runtime commits.
- [ ] Close licensing, source approval, final native matrix and production release gates.

R12 historical PASS is not production runtime-update acceptance. P6 CONDITIONAL.
