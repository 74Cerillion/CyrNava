# P5A owner checks — correction ready for review

**P5A STATUS: CONDITIONAL — LOCAL CORRECTION PASSED; HOSTED VERIFICATION PENDING**

The first hosted [run 41157614256](https://github.com/74Cerillion/CyrNava/actions/runs/41157614256)
remains FAIL at commit `329020b5286ce0d5474e04a781ed61a6079f8edc`.
Its evidence and previous reports are preserved. The backend job lacked generated
production frontend assets; a separate runner's frontend build cannot supply them.

The local correction gives the backend job its own pinned Node/npm setup and
locked dependency install/production build. No cross-job artifact or test skip
was introduced. Existing read-only permissions and fail-closed gates are preserved.

- [x] Clean baseline clone; explicit four-file candidate overlay; no preexisting dist,
  node_modules or backend venv. Fresh isolated dependencies and synthetic data.
- [x] 550 backend tests, 31 subtests; all three prior failures now pass.
- [x] 273 frontend units, 16 browser tests; lint, TypeScript/build pass.
- [x] 23 CI contract methods including four new prerequisite regressions.
- [x] Ruff, actionlint syntax/expression checks, compile and diff checks pass.
- [x] Reports, exact patch, source hashes, logs and JUnit preserved in
  `evidence/p5a/frontend-prerequisite-correction-2026-10-31/`.
- [ ] Owner authorizes one additional P5A-only commit and push to
  `desktop/p2-production-integration`.
- [ ] Monitor the resulting hosted run; record source SHA/run ID and all job results.
- [ ] Require production build/exported-payload audit/upload and verify package hash.
- [ ] Owner accepts P5A only after required hosted checks succeed.

Local backend setup adds 10.142 s for npm install/build; the full backend wrapper
was 41.472 s. Frontend wrapper was 122.877 s. Hosted timing remains unmeasured for
the correction. ShellCheck is not installed locally; no local ShellCheck PASS is
claimed. Existing P4 native evidence limitations remain unchanged.

No new commit, push, manual Actions trigger, signing, release, main merge or
P5B/P5C work occurred. Do not rerun the old revision. Stop for the explicitly
required commit/push authorization; no owner terminal test is requested now.

An exploratory lint expansion to unchanged desktop/packaging sources found 98
existing style violations outside the established CI lint scope. They were not
changed or represented as passing; canonical CI Ruff passed. See correction
evidence `exploratory-lint.json`.

## Authorized correction commit / push status

Owner authorized one additional commit and push. Created exactly one correction
commit: `72f4c7b0ca1de627b7615f03e20393cf5d423512` (46 P5A-only files).
Staged source and evidence review passed. The saved historical failure JUnit has
original traceback trailing whitespace; it was preserved verbatim rather than
rewritten. All other staged files passed git diff whitespace checks.

Push failed with exit 128 because the terminal lacks Git HTTPS credentials.
Read-only GitHub inspection confirms the remote remains at `329020b`; no corrected
hosted run started. Owner must complete the same already-authorized push from an
authenticated terminal. No second commit, manual workflow trigger or publication
was performed. This status update remains local/uncommitted; no further push is
authorized beyond completing the correction push. See
`evidence/p5a/correction-push-2026-10-31/push-status.json`.
