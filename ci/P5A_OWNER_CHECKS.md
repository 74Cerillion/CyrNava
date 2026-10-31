# P5A owner checks — lifecycle correction ready

**P5A STATUS: CONDITIONAL — HOSTED VERIFICATION REQUIRED; NOT ACCEPTED**

The latest actual hosted run remains [41163754626](https://github.com/74Cerillion/CyrNava/actions/runs/41163754626),
FAIL at 72f4c7b. Backend 550 tests/31 subtests passed; the production build was
skipped after browser recovery failed. Both historical runs remain unchanged.

Confirmed test defect: writes were blocked only after editor startup, which cannot
stop a request already dispatched. A real-API controlled reproduction commits
revision 4 with acknowledgement withheld and retains draft base 3; the application's
conflict rejection is correct. Historical exact ordering is unprovable because no
hosted trace was captured. Natural original-flow runs passed 10/10 and CPU probes
3/3; neither reclassifies the recorded failure or proves it flaky.

- [x] Install write barrier before opening the recovery page; keep through restart.
- [x] Assert SQLite unchanged, matching draft base, real save response and content.
- [x] Add deterministic lost-ack regression: preserve newer data and stale draft;
  recovery choice makes no automatic write and still requires conflict review.
- [x] Preserve revision/timing diagnostics and future failure traces.
- [x] Repeated affected tests: 10/10 (five per case), no retries.
- [x] Full clean-clone frontend: lint, 273 units, TypeScript/build and 17 browsers PASS.
- [x] CI contracts: 23 PASS. Application/backend/security code unchanged; no new
  backend suite run claimed. Prior hosted backend result remains separate evidence.
- [x] Evidence and selected synthetic traces retained in
  evidence/p5a/lifecycle-correction-2026-10-31/; see manifest and limitations.
- [ ] Authorize one next P5A-only commit/push to desktop/p2-production-integration.
- [ ] Verify resulting hosted run including actual Flatpak build/audit/upload/hash.
- [ ] Owner accepts P5A after required hosted results pass.

No commit, push, dispatch/rerun, release, signing, personal-data migration or
P5B/P5C occurred. No test skip, weakened conflict protection, timeout increase,
arbitrary delay or automatic retry was introduced. Stop at commit/push approval.
