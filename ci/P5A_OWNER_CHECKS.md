# P5A owner checks — fifth hosted verification

**P5A remains FAIL / NOT ACCEPTED.** Run 41179709348 / commit 6743d1d / attempt 1.

- [x] Owner push confirmed: remote branch and push-triggered workflow source SHA.
- [x] Workflow validation PASS: 23 contracts.
- [x] Backend/security PASS: 559 tests + 31 subtests.
- [x] Frontend lint, 273 units, TypeScript and production build PASS.
- [x] Browser integration PASS: all 20, zero failed/skipped/retries.
- [x] All five lifecycle cases and accepted SQLite guard preserved and PASS.
- [x] Corrected image test and code-to-image regression PASS in hosted Chromium.
- [x] Download and independently hash all three diagnostic archives.
- [x] Preserve current provisioning failure plus earlier failures/corrections.
- [ ] Runtime preparation: FAIL, ValueError after 108.078 s.
  Later BaseApp install updated previously pinned Platform. Pin drift is supported;
  exact final ref/SHA and exception text were omitted from hosted diagnostics.
- [ ] Production Flatpak build: NOT EXECUTED after prepare failure.
- [ ] Exported audit, validated unsigned package upload, production SHA/provenance:
  NOT EXECUTED; no production artifact. Diagnostic ZIPs are not a package.
- [ ] CI required: FAIL.
- [ ] Owner accepts P5A: not eligible.

Evidence: ci/evidence/p5a/hosted-image-selection-2026-10-31/.
No further code change, commit, push, rerun, dispatch, publication, security
weakening, main merge or P5B/P5C. Focused runtime-provisioning correction requires
new authorization; preserve pin/GPG verification and capture safe mismatch details.


## Authorized local provisioning correction — pending hosted execution

- [x] Preserve fifth-run and earlier hosted failures and successful application gates.
- [x] Install all dependencies before exact pins; pin with dependency updates disabled.
- [x] Mandatory final SHA checks and independent production builder gate retained.
- [x] Structured ref/stage/expected/actual/exception/final-outcome diagnostics.
- [x] Clean checkout: 8 new provisioning regressions, 31 CI contracts total PASS.
- [x] Packaging and lifecycle-harness regressions: 45 PASS; Ruff PASS.
- [x] Real isolated upstream metadata: all three exact commits available; declared
  dependency names/architecture/branch compatible; GPG verification true.
- [x] P4 locks, production sources, sandbox and read-only workflow unchanged.
- [x] Local real installation limitation recorded: read-only O_TMPFILE deployment;
  namespace probe denied. No sandbox bypass or simulated hosted PASS.
- [ ] Owner authorizes one correction-only commit and push, including P5A reports
  and retained non-sensitive hosted/correction evidence.
- [ ] New automatic hosted run: all application tests, provisioning, production
  build, exported audit, unsigned upload, independent SHA/provenance and required gate PASS.
- [ ] Owner accepts P5A. **Still FAIL / NOT ACCEPTED.**

Details: `ci/P5A_PROVISIONING_CORRECTION.md`.
