# P6 targeted Generation B owner handoff

2 November 2026. **LOCAL IMPLEMENTATION PASS. Native verification NOT EXECUTED.**
P6 remains CONDITIONAL. This is a proposed command for separate owner approval;
do not execute it under the local-implementation authorization.

## Preconditions and current blockers

- Keep `real-pair-r2`, R9 and R11 unchanged. Do not repeat preparation.
- The proposed new root is `~/.cache/p6/targeted-b-attempt-r12`; it must not exist.
  The driver refuses any existing attempt, including an earlier failed attempt.
- Provide **at least 5 GiB free** on the attempt volume. Readback found about
  **1.2 GiB**, so the capacity gate currently FAILS. The retained native client
  measures 3.4 GiB; candidate, signed-store and verification copies also need
  space. The 5 GiB floor is conservative, not a maximum-usage guarantee. Do not
  delete personal data or retained attempts under this authorization.
- The existing disposable signing key was independently verified valid at
  `2026-11-02T03:14:08Z`. It expires **2 November 2026 at 09:32:43 UTC /
  18:32:43 Korea time**. Current trust is checked again by the driver, including
  before uninstall and after reinstall. Stop if expired; do not change the clock,
  bypass expiry checks, extend keys or re-sign/reprepare without separate approval.
- Use an authenticated Ubuntu desktop Wayland session and the existing backend
  Python environment. No credentials need to be entered or pasted.
- Obtain owner authorization for exactly one targeted native invocation. The
  `authorization_ref` string is a provenance label, not a credential or substitute
  for that approval.

Read-only owner prechecks (these do not execute the rehearsal):

```bash
df -h "$HOME/.cache/p6"
test ! -e "$HOME/.cache/p6/targeted-b-attempt-r12"
```

The driver also checks actual free bytes and rejects unsafe paths. Do not replace
its checks with the output of these two commands.

## Exact proposed command — do not run before separate authorization

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
backend/.venv/bin/python -B -u ci/release/targeted_b.py \
  --prepared-root "$HOME/.cache/p6/real-pair-r2" \
  --r11-root "$HOME/.cache/p6/historical-gui-attempt-r11" \
  --attempt-root "$HOME/.cache/p6/targeted-b-attempt-r12" \
  --b-archive "$PWD/ci-output/p5c-hosted-41285343063/package.zip" \
  --b-approval "$PWD/ci-output/p6-owner/B-approved.json" \
  --historical-runtime 76fa01ac42ecf45d2c5020ef80de1c474c0c2ae86a51a79e8fec44c48f9dc473 \
  --authorization-ref P6-owner-authorized-targeted-B-only
```

Run this command once only after approval and capacity/trust preconditions are
satisfied. Do not pipe it to `echo $?`. After it ends, `echo $?` on a separate
line reports the exit status if needed.

This is a separate B-only entry point. It does not call the complete A/B GUI
command, create signing keys, rebuild packages, prepare a new pair, perform A
editing/update/rollback, or repeat native backup/import/recovery.

## Expected progress before the first window

The driver writes flushed `P6` operation events and a final complete result. It
validates the exact approved B ZIP/bundle/source/CI/artifact/OSTree identities,
existing signed preparation and key, R11 source hashes, schema-5 database, rich
text, folder/image relationships and source permissions. It copies only R11's
pinned synthetic imported workspace; original browser storage is never copied.

A new isolated client retrieves the KDE runtime, installs approved B through the
verified local signed repository and checks effective application permissions.
Dependency-resolution drift is recorded, restored only to the explicitly approved
historical runtime, and independently checked for origin/commit/GPG/signature/live
identity. B's compatible Qt imports must pass before the GUI. Ordinary runtime
compatibility remains FALSE. Runtime retrieval can take time; heartbeats are
printed every ten seconds during child operations, with bounded timeouts and
noninteractive Flatpak operations.

## First window: establish the imported preference baseline

1. Wait for the P6 instruction dialog. The application window is disabled while
   the checker records absent appearance/theme keys, selected **System**, actual
   resolved light/dark scheme, OS preference, workspace and Qt profile identities.
   If these checks fail or never become ready, the test fails rather than allowing
   you to repair the initial state. The baseline-readiness deadline is 45 seconds.
2. Read and dismiss the instruction dialog. System may render dark when the OS
   prefers dark; that is expected. Do not select Dark to match the original profile.
3. Select the existing synthetic folder and note, if necessary. Confirm the note
   titled **P4 owner edit**, its folder and its screenshot are visible. Do not edit,
   rename, create or delete content. If anything is missing or broken, interrupt
   the test and report it; do not close normally as a successful confirmation.
4. Choose **Appearance → Light**. Confirm Light is selected, the light theme is
   visible, and the note status is Saved. Do not choose the CyrNava theme.
5. Close CyrNava normally using its window close button. Do not use Ctrl+C for a
   successful phase. The original close/save and backend cleanup protocol runs.

Only a complete native PASS with valid preinteraction evidence, a saved Light
baseline, intact copied data and all original security checks permits uninstall.
Missing or failed evidence stops the sequence. The original baseline record is
retained as `phase-post-import-baseline.json` and hash-bound before uninstall.

## Automatic uninstall/reinstall

The driver rechecks signing trust and installed B identity, records the complete
private-data file and empty-directory state, uninstalls without `--delete-data`,
and verifies preservation. It reinstalls the same approved B from the signed
local repository and rechecks source, commit, schema, version and permissions.
It records/restores any authorized historical runtime drift and independently
checks runtime trust/imports. Private-data and original-baseline equality are
required before the second GUI.

No manual Flatpak command, backup operation or preference restoration is needed.
Do not click the Backup and recovery menu.

## Second window: prove persistence

1. Wait for the P6 instruction dialog. The window is disabled until the original
   Light baseline and both identities are verified **before any input**. A lost
   preference therefore cannot be concealed by reselecting Light.
2. Dismiss the dialog. **Do not change Appearance.** Any observed later preference
   mismatch remains a failure even if Light is subsequently selected again.
3. Confirm the same synthetic note, folder and screenshot are visible. Do not edit
   content. If visual content is missing or broken, interrupt and report it.
4. Close normally. The driver requires the exact original Light baseline,
   schema-5 integrity, unchanged logical records/assets, all native identity,
   authentication, isolation, single-instance, sandbox and backend cleanup checks.

## Results and stop conditions

The final record is:
`~/.cache/p6/targeted-b-attempt-r12/owner-result.json`.
Successful targeted verification must report `status: PASS`, `complete: true`,
`GUI_launches_attempted: 2`, `generation_A_launch_attempted: false`, and
`ordinary_runtime_update_compatibility: false`, with all required checks PASS.
Keep the phase records, separate before/after import probes, runtime journal,
private-data snapshots, code/checker hashes and original baseline intact.
A targeted PASS does not itself accept P6 or rewrite R11's original FAIL.

Stop on any identity/hash/signature/permission/runtime discrepancy, failed import,
missing System/Light baseline, unexpected workspace, missing data, timeout, unsafe
filesystem object, renderer/backend failure or interruption. Do not fix data or
preferences to force a PASS. Do not retry, reuse the root or rerun the full A/B
exercise. If an operation appears stuck, inspect the current progress/heartbeat;
Ctrl+C is an explicit interruption and produces FAIL, not evidence of an app defect.

On failure, preserve the attempt. Safe stage/errno/storage-line diagnostics are
recorded if a filesystem failure recurs; raw child output stays in the private
attempt. Do not upload profiles, browser storage, screenshots, raw subprocess
logs, packages or private key material into public repository evidence.

## Remaining decisions

Next requested authorization: **one B-only two-launch native verification**, only
after storage is sufficient and current signing trust is valid. If the disposable
key expires first, stop for a separate trust/preparation decision; no bypass is
proposed here. No native runtime/GUI action, commit, push or GitHub action is
currently authorized. Production ordinary-runtime compatibility, licensing,
notices/inventory, production trust/final source-CI-release approval and public
HTTPS/independent-client distribution verification remain open.
