# P5A owner checks — fourth hosted verification

**P5A remains FAIL / NOT ACCEPTED.** Run 41176826666 / commit 047a99b / attempt 1.

- [x] Owner push independently confirmed by push-triggered workflow source SHA.
- [x] Workflow validation PASS: 23 contracts.
- [x] Backend/security PASS: 559 tests + 31 subtests.
- [x] Frontend units PASS: 273; lint and TypeScript/build PASS.
- [x] All five lifecycle cases PASS, including no-browser-routing SQL boundary.
- [x] Correlated real hidden/close-intent PATCH rejected by SQLite, rollback + 503;
  canonical equality and recovery PASS. Historical operation remains unidentified.
- [x] Downloaded both diagnostic archives; SHA-256 matches GitHub digest.
- [x] Preserve trace/screenshot and previous failures; reports updated locally.
- [ ] All browser integration tests: 18 PASS / 1 FAIL, workspace.spec.ts:656.
  Second /image became code text; no Upload image button/chooser event. Exact focus
  transition cause requires further investigation; no portal defect inferred.
- [ ] Production Flatpak build: SKIPPED due frontend failure.
- [ ] Exported package audit, unsigned artifact upload, production SHA/provenance:
  NOT EXECUTED; no production bundle exists in this run.
- [ ] Final CI required gate: FAIL.
- [ ] Owner acceptance: not eligible.

Evidence: ci/evidence/p5a/hosted-sql-boundary-2026-10-31/.
No additional commit, push, rerun, dispatch, release, signing, deployment, main merge,
or P5B/P5C. Further implementation/hosted execution requires authorization.

## Local image-selection correction — ready for authorization

- [x] Reproduce the second image command's DOM/model selection mismatch.
- [x] Test-only observable cursor, suggestion and upload preconditions corrected.
- [x] Add code-literal-to-paragraph-image regression; preserve all original checks.
- [x] 10/10 focused passes, 273 units + 20 browsers, lint/build PASS in clean checkout.
- [x] 9 lifecycle-harness backend regressions PASS; guard source unchanged.
- [x] All 33 production frontend assets byte-identical; no production source change.
- [x] Preserve hosted fourth-run failure, guard enforcement and local failed attempts.
- [x] Owner authorized one P5A-only commit/push of correction, reports and evidence.
- [ ] All required checks in a new authorized hosted run PASS, including Flatpak
  build, exported package audit, unsigned upload, checksum/provenance and CI gate.
- [ ] Owner accepts P5A. Latest actual hosted result remains FAIL.

Details: P5A_IMAGE_SELECTION_CORRECTION.md and image-selection-correction evidence.
No commit, push, rerun, dispatch, publication or P5B/P5C this turn.

Authorized commit `6743d1d5c76f2db87c2debb6f687a6e57a6826b6` created; one push attempt blocked by unavailable Git HTTPS credentials. Remote remains `047a99b1473304cc73518dff6427bf7937c542a2`. Complete the already-authorized push from the owner terminal; no new hosted result or P5A PASS exists. See image-selection-commit-review push-status.json.
