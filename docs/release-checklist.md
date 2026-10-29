# v0.1.0 owner release checklist

This page is the historical M6 checklist. For current F-09 engineering evidence and owner gates, see the [search release checklist](search-release-checklist.md).

This is a review candidate. Checked items refer to executed evidence in [M6 verification](../M6_VERIFICATION.md), not an authorization to publish.

- [x] Initial repository audit recorded; existing persistence/schema preserved.
- [x] Core-only BlockNote dependencies; no XL, new library or broad upgrade.
- [x] Local built frontend/API mode verified without Vite; supported servers bind loopback.
- [x] Backend 96 tests, frontend 77 tests, lint/type/build and pip checks pass.
- [x] Three browser journeys pass in development and local release configurations.
- [x] Fresh public M5 clone and separate fresh M6 source candidate verified.
- [x] T-01–T-12 evidence and limitations recorded.
- [x] Offline browser network filtering, save races, outage/conflict recovery and restored images verified.
- [x] Targeted keyboard/naming/focus/responsive checks; no full WCAG claim.
- [x] README, architecture, five retrospective ADRs and changelog prepared.
- [x] Four real synthetic screenshots visually reviewed; no demo profile committed.
- [x] Dependency inventory and available third-party notices retained.
- [x] Tracked/current/staged/available-history audit finds no high-signal secrets or runtime data.
- [x] Release description draft and recommended Git commands prepared.
- [ ] Owner selects original-code license, adds accurate LICENSE/copyright and updates metadata/docs. **Explicitly pending.**
- [ ] Resolve/approve use-composed-ref missing copyright provenance before distributing a built bundle; review MPL source availability and all notices.
- [ ] Owner reviews implementation, reports, limitations and human acceptance (including desktop clipboard/accessibility needs).
- [ ] Owner commits/pushes approved files; repeat clean clone/install/tests against that exact public M6 commit. Do not substitute the M5 baseline evidence.
- [ ] Owner authorizes tag/release, confirms draft wording/license and any attached artifact notices.

No publication commands have been executed. Public-release classification: **NOT READY** while licensing/owner gates remain open. That M6 record did not include Phase 2; subsequent feature candidates are recorded separately.
