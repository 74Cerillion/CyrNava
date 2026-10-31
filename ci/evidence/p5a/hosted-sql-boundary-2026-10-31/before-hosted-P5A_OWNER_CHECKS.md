# P5A owner checks — focused lifecycle investigation

**P5A remains FAIL / NOT ACCEPTED.** Latest hosted run 41172242175 remains unchanged.

- [x] Preserve historical trace/revision evidence and superseded hypotheses.
- [x] Review installed Playwright teardown behavior, worker and keepalive limitations.
- [x] Instrument disposable frontend/FastAPI/SQLite with operation IDs/monotonic times.
- [x] Correlate five controlled visibility failures/rollbacks and five later commits.
- [ ] Identify the exact historical escaped request: backend logs were not captured;
  local repetitions did not observe a close-intent HTTP request. Do not infer it.
- [x] Implement independently enforced SQLite note-write guard and fingerprint check.
- [x] Verify direct HTTP, direct SQL, preexisting connections and writer linearization.
- [x] Prove unexpected canonical writes/disarmed guard fail verification.
- [x] Verify plain app has no guard; packaging excludes it and migration rejects it.
- [x] Fresh-checkout focused checks 15/15; full backend 559 + 31 subtests PASS;
  frontend 273 units + 19 browsers, lint and TypeScript/build PASS.
- [x] Preserve initial 5 GiB disk-space test failure and safe dependency-only cleanup.
- [x] Owner approved findings, fixture-only boundary, and one commit/push.
- [x] Final launcher refuses existing unmarked databases before mutation; unchanged-source regression PASS.
- [ ] Successful required hosted jobs, production build/audit/upload and package hash.
- [ ] Owner accepts P5A.

See P5A_LIFECYCLE_INVESTIGATION.md and evidence/p5a/lifecycle-causality-2026-10-31/.
No source-production change, security weakening, new commit, push, workflow trigger,
publication, real-data access or P5B/P5C occurred. No additional host test is requested.

Final source/package review and repeated clean-checkout results: evidence/p5a/lifecycle-final-review-2026-10-31/. Hosted verification remains pending.

Authorized commit `047a99b1473304cc73518dff6427bf7937c542a2` created. Push blocked by unavailable terminal Git HTTPS credentials; complete the recorded exact push from the authenticated owner terminal, then verify the automatically triggered hosted run. No new hosted PASS is claimed.
