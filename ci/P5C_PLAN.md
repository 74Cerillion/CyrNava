# P5C — Integrated Release Pipeline Verification plan

Baseline verified 1 November 2026: clean local/remote integration HEAD
`182d11dbcddc90670fc02e19e6156dc220074dd1`. P5B is ACCEPTED / COMPLETE;
accepted tooling `3ea472e`, hosted staging 41265875118, source `1ee2077`, CI
41181510439 and artifact 13035607417 remain distinct identities.

## Acceptance criteria defined before implementation

1. Reuse P5B live eligibility, pinned artifact extraction/audit, disposable signing,
   signed summary/commit verification, descriptors and atomic retained snapshots.
2. Install the actual accepted application via its generated .flatpakref into a
   newly marked isolated Flatpak user installation; verify expected commit and
   packaged build-inputs source SHA. Check the public key fingerprint independently
   before trusting the descriptor; reject wrong key/native corrupted content.
3. Use a distinct synthetic application ID and two signed generations for the
   update drill. Install A, publish B retaining historical objects, update the
   existing client to B and verify exact commits. Never change production version
   or schema, run the application, or imply a real production app upgrade.
4. Prove incomplete publication leaves A usable, missing objects/unsigned or
   corrupted metadata fail closed, and retained snapshots cannot drop objects.
   Preserve canonical application data; all clients/config/data live under fresh
   marked disposable roots. Network serving binds only 127.0.0.1 if used.
5. Produce complete, redacted PASS/FAIL evidence, explicit key cleanup evidence
   and a whitelist-only diagnostic export. No keys/repos/packages in diagnostics.
6. Provide a review-only release candidate plan, dependency inventory/SBOM scope,
   vulnerability-check results/limitations, license/runtime/retention obligations,
   release notes/checksums and tag procedure. No unsupported clearance claims.
7. Before proposing hosted execution, validate fresh independent Python jobs,
   full source history, native tool versions/capabilities, resource assumptions,
   diagnostic contents and exact proposed workflow policy. Keep accepted P5B
   workflows/contracts intact. Do not dispatch, commit, push or change settings.
8. Native or hosted gates not executed must remain unexecuted/blocked. If the
   sandbox prevents native operations, finish the runner and provide exact owner
   Ubuntu commands; no weakened permissions or fabricated PASS.

## Design and increment sequence

Add P5C modules around accepted P5B helpers, not a second signing/publisher stack.
The integration supervisor runs the existing stage.py, validates its exact result,
then verifies the actual client. Separate synthetic two-generation fixtures test
updates using the same signing/descriptor/publisher primitives. Client profile
creation is exclusive and marker-guarded; every Flatpak command uses --user,
FLATPAK_USER_DIR and isolated XDG paths, never system/user normal configuration.
No GUI/native app launch or migration is performed. Runtime fetching is disabled
for isolated install drills; report whether launch dependencies are installed.

A separate proposed manual workflow will live outside .github/workflows for
review. It will reuse the environment model but never modify its settings or
register/execute itself. Existing ordinary CI discovers new deterministic tests.
Release-readiness tools use pinned source files and bounded public advisory reads;
production publication remains disabled and licensing approval remains an owner
release gate. P6 owns real-user/cross-machine migration and desktop update acceptance.

Implement safety/profile/native probes first, then client/install/update runner,
negative cases, readiness inventory and workflow parity tests. Run focused tests,
then release/CI regressions in a disposable clean environment. Avoid application
rebuilds by reusing the accepted artifact, whose hashes remain fixed. Record
findings and exact test commands in P5C_REPORT.md and owner actions in
P5C_OWNER_CHECKS.md. Stop at the next external-action authorization checkpoint.

## Implementation reconciliation — 1 November 2026

The supervisor reuses accepted `core.py`/`github.py` primitives directly rather
than launching `stage.py` as a nested supervisor. This keeps one cleanup/final
evidence boundary around repository generation and client checks; accepted code
and contracts remain unchanged. A signed P5C sidecar distinguishes new execution
identity from retained P5B reference-workflow fields. Actual results, environment
caveats and remaining gates are recorded in P5C_REPORT.md. Hosted P5C is unexecuted.
