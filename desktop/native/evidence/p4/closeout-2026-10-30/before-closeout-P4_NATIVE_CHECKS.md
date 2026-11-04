# P4 owner-host checks — synthetic only

Status: NOT TESTED until actual host results exist. All available automated checks
must pass first. No personal CyrNava workspace is selected or migrated.

The final staged A build is:
`.p4-cache/cyrnava-builds/p4/local-A-6m4ne70o`.
Build A now has a verified PASS artifact (209,183,720 bytes); its owner-host
export and SHA-256 are recorded in `evidence/p4/build-A-final-2026-10-30/`.
Do not repeat the --finish command below; it is retained as reproduction history.
Build B now also passed at `/home/cerillion/.cache/cyrnava-builds/p4/local-B-f26wev2b`.
Skip both build commands below and continue with the host supervisor.

Run these blocks separately, in order:

```bash
cd /home/cerillion/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/CyrNava
backend/.venv/bin/python packaging/flatpak/production/build.py --finish "$PWD/.p4-cache/cyrnava-builds/p4/local-A-6m4ne70o"
```

Stop if final status is not PASS; preserve its final result/log rather than
rebuilding repeatedly. No validator/sandbox flags should be disabled.

Build B is needed once for the local update test:

```bash
backend/.venv/bin/python packaging/flatpak/production/build.py --build-id local-B
```

Copy the **Build directory** printed for B. It must have final status PASS. Then:

```bash
python3 packaging/flatpak/production/host_verify.py --a "$PWD/.p4-cache/cyrnava-builds/p4/local-A-6m4ne70o" --b /home/cerillion/.cache/cyrnava-builds/p4/local-B-f26wev2b
```

The host supervisor refuses an existing production installation or data directory;
use a disposable Ubuntu desktop account/VM if one exists. It installs only the
production ID, not development. It leaves production B installed and retains
synthetic evidence/data after testing. It never uses `--delete-data`, modifies
Flatpak overrides, launches external tools from notes, or touches Firefox data.

Required interactions:

1. **EDIT:** create a folder; rename the seeded note exactly `P4 owner edit`;
   enter text and make it bold; paste a new screenshot of ONLY this synthetic app;
   choose Appearance **Dark**; wait for Saved/uploads, then close normally.
2. **RESTART:** verify title, formatting, screenshot and Dark remain. Exercise a
   keyboard shortcut (for example Ctrl+B in the editor), wait for Saved, close.
3. **UPDATED / ROLLBACK:** after automatic local B update and A rollback, confirm
   the same note/screenshot/Dark persist and close each window normally.
4. **MAINTENANCE:** Create verified backup, save a NEW `.cyrnava` file in Downloads,
   wait for Completed and verified. Then Import backup into a new workspace,
   select that saved file, confirm and wait for completion; close the manager.
   Explicit import may reset browser preferences, per the approved P3 exclusions.
5. **RECOVERY:** automatic backup/restore and future-schema refusal checks on a
   disposable copied generation. The original active profile is selected again.
6. Automatic uninstall verifies data unchanged; B is reinstalled. Development
   commit must remain unchanged. Final host JSON must report complete PASS.

Per-phase evidence is under:
`~/.var/app/io.github._74Cerillion.CyrNava/data/p4-verification/run-<id>/`.
The supervisor writes `host-run-<id>.json` and effective permissions beside A.
It records helper SHA, bundle hashes/commits, renderer diagnostics, namespaces,
seccomp, API rejection checks, timings, and sampled process RSS. A simulated
chooser/offscreen widget test is never counted as native portal evidence.
On timeout/failure, preserve output; a live window is left for normal closure.

Final manual launcher checks (report these separately; the automated helper uses
an isolated test root rather than the actual launcher data directory):

- Start **CyrNava** from Ubuntu's application launcher. Check correct name/icon,
  window title and welcome choice. Choose an empty workspace, create ONLY
  synthetic content, close, reopen from the desktop launcher, confirm persistence.
- Confirm development's separate launcher remains available.
- Confirm screenshot paste, chooser, keyboard shortcuts and rich formatting worked.
- Report final supervisor JSON/evidence path and these visual results. No P4 PASS
  will be declared until the real host tests and owner review complete.

## Continue the first installed synthetic run

Run `run-83587bd18651` passed fresh installation and native security, but EDIT
did not save the exact checkpoint title. Its folder and screenshot are retained.
No rebuild or reinstall is required for the verification-driver correction.

```bash
python3 packaging/flatpak/production/host_verify.py \
  --a "$PWD/.p4-cache/cyrnava-builds/p4/local-A-6m4ne70o" \
  --b "/home/cerillion/.cache/cyrnava-builds/p4/local-B-f26wev2b" \
  --resume run-83587bd18651
```

Read the test window's instructions, set the NOTE TITLE to exactly `P4 owner edit`,
ensure Appearance is Dark and wait for Saved before closing. Existing folder and
screenshot need not be recreated. Follow the subsequent terminal prompts. Resume
requires installed build A and this recorded test root; normal production data
causes a refusal. Previous records are copied before any phase is rerun.

## Continue at Backup and recovery after verified rollback

Run `run-83587bd18651` now has complete recorded PASS for edit, restart, update B
and rollback A. Its maintenance window was closed without importing; that is an
incomplete check, not an accepted import. No rebuild is needed.

```bash
python3 packaging/flatpak/production/host_verify.py \
  --a "$PWD/.p4-cache/cyrnava-builds/p4/local-A-6m4ne70o" \
  --b "/home/cerillion/.cache/cyrnava-builds/p4/local-B-f26wev2b" \
  --resume run-83587bd18651 --continue-maintenance
```

In the manager:

1. Click **Create verified backup**, save a new `.cyrnava` file in Downloads,
   and wait for **Completed and verified**.
2. Click **Import backup into a new workspace** (the second button), select that
   same saved file, confirm **Yes**, and wait for **Completed and verified** again.
3. Close the manager only after import completes.

The remaining automatic checks verify recovery, safe uninstall/data retention,
reinstallation and development isolation. Expected final supervisor output is
`"status": "PASS", "complete": true`. A failure includes its phase/evidence path;
preserve it. Closing without import produces `import_activated_new_workspace: FAIL`.
Continuation refuses partial prior evidence rather than treating it as success.
Do not open the normal production launcher until this synthetic supervisor run
finishes; the final manual launcher checks above come afterward.

### Existing A/B backup filename workaround

Type the entire filename **test.cyrnava**, including the extension, in the Save
portal. These installed builds filter imports by `.cyrnava` and can hide files
saved as just `test`. A CyrNava backup is a ZIP container; select the archive
itself for import and do not extract it. The source correction suggests a filename
and offers All files on import, but is not yet in the installed A/B artifacts.
