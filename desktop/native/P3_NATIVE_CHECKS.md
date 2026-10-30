# P3 native acceptance — synthetic profiles only

**Final result: PASS, 30 October 2026.** Run `run-a2e0fcaea12a` has complete
supervisor and all five phase PASS records. Copies are in
`evidence/p3/final-native-2026-10-30/`. Owner confirmed the visual checks.
The procedure below is retained for reproducibility; no rerun is requested.


Prerequisite: automated checks in `evidence/p3/validation.json` pass. Close existing
CyrNava review windows normally. No personal workspace selection is required.
The existing development identity/branch is retained; no production installer,
public release or P4 packaging work is performed.

Run each block separately in the regular Ubuntu terminal:

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
```

Rebuild the isolated review candidate so it contains P3 source. This is necessary;
the accepted P2 installed candidate has no migration modules. Keep at least 4 GiB
free in the build cache filesystem. This does not migrate existing application data.

```bash
backend/.venv/bin/python packaging/flatpak/prepare.py --build
```

Then launch the host supervisor:

```bash
python3 packaging/flatpak/run_migration_verification.py
```

The supervisor generates a fresh run ID and prints instructions before each phase:

1. **PREPARE:** a real Save dialog opens. Save the synthetic `.cyrnava` backup in
   Downloads with the suggested new filename. This first window is a file chooser,
   not the migration manager: its Name field is at the top, and Save is at the top
   right. If the list is empty, use Other Locations or Ctrl+L to choose your
   Downloads directory. The new-folder button only creates a destination folder.
   Click Save, not Cancel. The helper verifies the granted file readback before
   opening the migration manager in the next phase.
2. **IMPORT:** click the SECOND button, **Import backup into a new workspace**.
   Do not click Create verified backup: the destination has no workspace yet.
   This is an OPEN-file chooser: select the saved `.cyrnava` FILE, not a folder
   or destination workspace. CyrNava creates the destination after confirmation.
   Choose only the backup
   just generated, confirm its counts/schema, wait for verified completion, then
   close the manager. The helper checks schema 4→5, exact content preservation and
   source fingerprints. Do not choose your real workspace.
3. **EDIT:** in the synthetic application, rename a note to `P3 owner edit`.
   Take a screenshot of only this synthetic workspace and paste it with Ctrl+V.
   Wait for Saved and completed uploads, then close normally.
4. **RESTART:** confirm the title and screenshot persist, then close normally.
5. **VERIFY:** automatic checks validate database/assets, restart/reap the backend,
   create and restore another verified backup, reject a corrupt backup without
   changing active data, switch to a verified recovered copy and switch back.

Final success requires supervisor `status: PASS`, `complete: true`, and all five
phase results PASS. The per-phase JSON must contain the corresponding checks.
A missing/failed/incomplete record or nonzero process exit is a failure. Host
portals have not been tested by the offscreen QtWidgets probe.

Evidence and disposable profiles remain in:
`~/.var/app/org.cyrnava.CyrNava.Devel/data/p3-verification/run-<id>/`.
The selected synthetic archive remains in Downloads. No cleanup of personal or
legacy data is performed. On failure, preserve the final JSON/evidence path; do not
retry repeatedly or grant broader Flatpak permissions. A timeout leaves any live
native window available for normal close/recovery.

Expected owner reply: final supervisor JSON plus confirmation of the visual
screenshot/restart check. These results have now been received and verified.

Portal startup correction: the streamed helper waits for Qt portal initialization
before opening the initial Save dialog. PREPARE now also requires
`document_portal_destination: PASS`; local readback alone is insufficient. No
rebuild is needed for this driver-only correction. Prior PREPARE records remain
historical and do not independently verify host-portal delivery.

For the successful import in `run-a2e0fcaea12a`, resume only the remaining checks:

```bash
python3 packaging/flatpak/run_migration_verification.py --resume run-a2e0fcaea12a
```

In EDIT, change the note title field to exactly `P3 owner edit`, then click the
note body and paste a newly captured screenshot of the synthetic workspace. The
noise image already present is a fixture and does not count as a new screenshot.
Wait for Saved/uploads complete before closing. RESTART opens the same profile;
confirm the changed title and newly pasted image before closing normally.
