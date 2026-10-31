# P5A lifecycle persistence investigation

31 October 2026. **P5A remains FAIL / NOT ACCEPTED.** No hosted run, commit or push.

The confirmed defect is an ineffective test fault boundary: browser route interception
did not prevent a canonical note write during teardown. We have a locally verified
replacement boundary and end-to-end request/transaction telemetry. We cannot identify
the exact historical request retroactively because it had no backend correlation log.

## Confirmed findings and limits

Run 41172242175 captured revision 3 before the no-write interval and revision 4 after
restart, including the later unconfirmed title and bold paragraph. The update timestamp
falls about 9.7 ms after page.close. Routing was installed before the recovery page
and those edits existed, so a request already serialized before interception cannot
explain a body containing those later edits. Browser silence is not proof of no request.

Installed Playwright 1.64.1 sets `_closeWasCalled` when normal close begins; both page
and context route dispatch check this flag and may return without invoking handlers.
Its source hash/line observations are retained. This establishes a teardown limitation,
not the exact internal path of the historical escaped write. See the [upstream client
source](https://github.com/microsoft/playwright/blob/main/packages/playwright-core/src/client/browserContext.ts).

Service-worker routing is a separate documented limitation ([official network guide](https://playwright.dev/docs/network)).
The application registers no worker in the reviewed path, and controlled local contexts
reported zero registrations/controllers. No evidence identifies service workers as the
historical cause. Notes fetch has no keepalive option; local requests report false.
Session close beacons target lifecycle endpoints and carry no note data. The historical
context stayed open for restart, so this was a page close, not whole-context shutdown.
No evidence identifies another backend writer. Normal content/revision mutation is the
PATCH route calling Database.update; exact historical operation identity remains unknown.

## Correlated persistence path

```mermaid
sequenceDiagram
    participant V as visibilitychange(hidden)
    participant S as useAutosave.flush / updateNote / HTTP fetch
    participant A as FastAPI + threadpool
    participant D as Database.update
    participant Q as SQLite
    V->>S: Flush pending synthetic edit
    S->>A: PATCH + test correlation and frontend timing
    A->>D: revision-checked update
    D->>Q: BEGIN IMMEDIATE; UPDATE notes
    alt test guard armed
      Q-->>D: Abort; rollback
      D-->>A: sqlite3.Error
      A-->>S: HTTP 503; draft retained
    else guard disarmed, explicit Retry save
      Q-->>D: Commit complete
      D-->>A: revision + 1
      A-->>S: HTTP 200; Saved
    end
```

Five controlled visibility-event experiments captured this complete path. Each has
one correlated rejection/rollback while armed and one successful commit after disarm
and an explicit UI Retry save. Backend events share monotonic_ns, process identity,
request correlation ID, expected/returned revisions and response status. ContextVars
preserve correlation through FastAPI's synchronous endpoint/threadpool. Commit-complete
is recorded after the actual connection transaction exits successfully. Expanded SQL,
note content/titles, credentials and authentication headers are never journaled.
Frontend capture occurs in a test-context fetch wrapper; it records monotonic browser
timing, visibility, close intent, keepalive and worker-controller state as whitelisted
metadata. An out-of-band driver marker uses the host's monotonic clock. Browser and
server clocks are not assumed to share a numeric origin.

**Causality limit:** controlled visibility events are explicit experiments, not a
recreation of the exact hosted schedule. None of the 15 local focused runs observed a
real close-intent HTTP operation. Instrumentation changes timing. Consequently the
historical close/visibility-flush/interception-bypass explanation remains the most
supported hypothesis, not an independently observed historical request/commit chain.

## Independently verified note-write boundary

The fixture creates private SQLite BEFORE triggers rejecting note INSERT/UPDATE/DELETE
while armed. A separate test control process arms them under BEGIN IMMEDIATE, serializes
with existing writers, commits, and records the canonical baseline. Requests queued
before arming cannot subsequently modify notes; an already-active writer finishes before
arming and is reflected in the baseline. The engine guard survives backend restart.

Verification checks armed state and every note's ID/revision/content/metadata fingerprint.
A real HTTP PATCH from Node, outside Playwright interception, must return 503 while armed.
The test checks canonical equality through restart before disarming and choosing recovery.
The same recovery contract also runs without any browser routing. No fixed sleep,
timeout increase, test suppression or automatic retry was introduced. Explicit UI retry
after releasing the fault is a recovery assertion, not a test retry.

Scope is canonical **note rows**, not a general filesystem/network outage simulator.
The SQL rejection exercises failed persistence (HTTP 503); other application reads and
lifecycle heartbeats continue. Unknown or disarmed guard state and changed fingerprints
fail verification. Tests intentionally demonstrate unexpected writes being caught.

## Production isolation

Only `ci/lifecycle_harness.py`, `backend/tests/test_lifecycle_harness.py` and
`frontend/e2e/lifecycle.spec.ts` change implementation/test behavior. Tests copy and
explicitly invoke a fixture launcher with a fixture-only source descriptor. It installs
instrumentation in its own worker processes. Application and native worker source,
frontend src, API authentication, Host/Origin checks, sandbox permissions and packager
allowlists are unchanged. There is no production environment/config/HTTP activation hook.

Tests verify plain application databases have no guard; production staging contains
neither harness nor frontend test headers; production migration rejects fixture databases
with the additional guard schema. No guarded profile or real owner workspace is imported
into production. The fixture modifies only its disposable synthetic schema.

## Verification and recommendation

- Focused browser checks: **15/15**, five repetitions of each of three modes, no retries.
- Full backend/security/lifecycle/migration/packaging: **558 passed + 31 subtests**,
  two existing warnings; eight new tests. Pytest 29.19 s; wrapper 35.639 s.
- Full frontend: **273 units + 19 browser tests**, lint and TypeScript/build PASS.
- Fresh clone of 1297001: initially no dist/node_modules/venv; fresh dependencies;
  three explicit candidate files. Full backend started with absent dist and built it.
- Initial full run retained: two packaging tests failed the existing 5 GiB free-space
  guard. Only unused dependency directories in earlier disposable checkouts were
  removed; no source/evidence/profile/browser binary or security setting was deleted
  or changed. Full suite then passed. This environment correction is not hidden.

Commands: `backend/.venv/bin/python ci/verify.py backend --require-clean-frontend`,
then `backend/.venv/bin/python ci/verify.py frontend`; focused:
`npx --no-install playwright test e2e/lifecycle.spec.ts --grep 'managed tabs close|visibility flush' --repeat-each=5 --trace=on --reporter=list,json`.
Exact commands, results, logs, journals, trace samples and candidate hashes:
`evidence/p5a/lifecycle-causality-2026-10-31/manifest.json`.

**Recommend reviewing the fixture-only SQL fault boundary and retaining the correlated
journals before authorizing another hosted cycle.** Its enforcement no longer depends
on page teardown interception. Do not weaken the equality assertion or production
revision protection. The original hosted operation remains unidentified; local PASS is
not proof of its cause or P5A acceptance. Latest actual hosted result remains FAIL;
production Flatpak build/audit/upload are still unexecuted. Stop for owner review.

## Final review amendment

The owner accepted the proposed correction and authorized one commit/push. The fixture
launcher now refuses an existing unmarked database before initialization or guard installation;
a ninth regression proves refusal leaves its bytes unchanged. Revalidation: 559 backend
tests + 31 subtests, 273 units + 19 browsers, 15 focused repetitions, 23 CI contracts PASS.
The earlier candidate hashes/results above remain historical evidence. Final candidate
hashes and logs: `evidence/p5a/lifecycle-final-review-2026-10-31/`. Production behavior and
permissions remain unchanged. No hosted PASS is inferred from these local results.

## Hosted verification amendment — 41176826666

All five lifecycle tests passed in the fourth hosted run. Its no-browser-routing
case captured a hidden close-intent PATCH 16.850991 ms after the driver marker:
expected revision 3, SQLite UPDATE rejected, ROLLBACK, HTTP 503, no commit-complete.
The canonical-equality and recovery assertions passed. This is direct evidence of
the replacement boundary resisting a real teardown save in the current run. It
does not retrospectively identify the previous escaped operation. P5A remains FAIL
because a separate workspace image-command test failed; no production package was
built. See hosted-sql-boundary-2026-10-31 evidence and the current P5A_REPORT.
