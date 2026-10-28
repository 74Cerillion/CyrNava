# Ubuntu checkout migration to CyrNava

The GitHub repository is already renamed. This procedure changes only your local checkout folder and `origin`. It does not rename anything on GitHub, push, install the app automatically, move notes, or change global VS Code settings.

## Before running

Review and commit the rebranding changes yourself. The script refuses staged, unstaged and ordinary untracked changes; it never stages, commits, stashes, resets or discards them. Relevant ignored configuration such as `.env` is included in its private source archive. Backups are unencrypted and must remain outside Git and storage you do not trust.

Wait for **Saved** and completed uploads. Close app tabs and use **Stop ENGAGE** on the old installed version, or **Stop CyrNava** after reinstall. Stop every development/backend process with Ctrl+C. Close VS Code and terminals whose working directories are inside the checkout. Open a separate terminal at your home directory. Keep the same XDG environment used by your existing installation.

Copy the reviewed `migrate_to_cyrnava.sh` outside the checkout before renaming it:

```bash
OLD_REPO="$HOME/Documents/Codex/2026-10-21/role-act-as-an-implementation-partner/outputs/cyber-workspace"
cp -- "$OLD_REPO/migrate_to_cyrnava.sh" "$HOME/migrate_to_cyrnava.sh"
chmod 700 "$HOME/migrate_to_cyrnava.sh"
cd "$HOME"
"$HOME/migrate_to_cyrnava.sh" "$OLD_REPO" --dry-run
```

Replace `OLD_REPO` with your actual repository root if different. The script accepts any path, including spaces. It requires a regular standalone Git checkout, Python 3.12's existing `backend/.venv`, Git and Ubuntu's GNU tar/mv. Linked worktrees, submodules, detached/in-progress Git operations, multiple/re-written remotes, separate push URLs, custom SSH host aliases and symbolic-link paths require manual review; unsupported cases stop without conversion. GitHub HTTPS, `git@github.com:` SSH and `ssh://git@github.com/` SSH are supported while preserving the chosen transport.

Default profile resolution uses the same absolute `$XDG_DATA_HOME` rule as the app, then the existing `engage-application/config.json` if found, otherwise `~/.local/share/engage/`. To select the full profile and a private backup parent explicitly:

```bash
"$HOME/migrate_to_cyrnava.sh" "$OLD_REPO" --dry-run \
  --data-dir "/absolute/existing/data-home/engage" \
  --backup-dir "/absolute/private/CyrNava-migration"
```

Review the printed profile path carefully. If no profile exists there, the script reports that and does not create one; select the actual custom profile before proceeding. Other profiles and browsers are not moved or modified. The location guard matches the existing backup contract: separate from the supplied application repository, with symlink paths refused. Choose locations outside other Git checkouts too.

## Execute only after approving the dry run

```bash
"$HOME/migrate_to_cyrnava.sh" "$OLD_REPO"
NEW_REPO="$(dirname "$OLD_REPO")/CyrNava"
git -C "$NEW_REPO" remote -v
git -C "$NEW_REPO" branch --show-current
git -C "$NEW_REPO" status --short
```

Repeat the same `--data-dir`/`--backup-dir` options if used for the dry run. Do not use sudo. A preexisting `CyrNava` sibling is refused, even if empty. Re-running against a clean, already-renamed checkout with the expected new remote is a no-op. A checkout named CyrNava but still using the old remote is backed up and has only its remote updated.

The default backup location is `~/Backups/CyrNava-migration/<timestamp>-<unique suffix>/`:

```text
repository.tar             .git, source and configuration, including ignored config
repository.tar.sha256      source archive checksum
profile.engage-backup/     verified existing database/images/templates, if present
migration.json             original/new paths, remotes, branch, HEAD, completion flag
```

Only rebuildable `backend/.venv`, `frontend/node_modules` and `frontend/dist` are excluded from the archive. The actual directory rename preserves them and everything else in the checkout. The script compares the archive with source before mutation, verifies the established application backup manifest, checks free space, uses non-replacing rename, and verifies unchanged HEAD/branch plus a clean working tree and the new origin. HTTPS stays HTTPS; SSH stays SSH. No credentials are added or printed.

The existing profile lock is held exclusively through backup and migration. An active cooperating backend prevents the operation. All older/noncooperating writers and external database tools must also be stopped. Current app databases use rollback journals. SQLite sidecars, WAL-mode headers, invalid databases, broken relationships or damaged images stop migration rather than being silently copied. Do not remove sidecars or bypass the lock; recover/checkpoint a WAL profile under separate review. The script never modifies database mode or original data.

## VS Code and dependency environments

No repository-owned `.vscode/settings.json`, `launch.json`, `tasks.json` or `.code-workspace` files were present. Global VS Code settings were not modified. Open the renamed root:

```bash
code "$NEW_REPO"
```

Remove the obsolete old path from Recent Folders if desired. Any external workspace file, shortcut, debugger setting or task you created with an absolute old path must be edited manually to the new path. Relative `${workspaceFolder}` paths remain valid. Existing installed desktop launchers point to program copies outside the checkout and keep working; reinstall separately to update visible branding.

Python virtual environments are not portable across a directory rename. Preserve the moved environment at a unique sibling name, then recreate it at its final path:

```bash
(
set -e
cd "$NEW_REPO"
if [ -e backend/.venv ] || [ -L backend/.venv ]; then
  VENV_BACKUP="backend/.venv-before-cyrnava-$(python3.12 -c 'import uuid; print(uuid.uuid4().hex)')"
  mv -T --no-clobber -- backend/.venv "$VENV_BACKUP"
fi
test ! -e backend/.venv && test ! -L backend/.venv
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m pip check
nvm use
cd frontend
npm ci
npm run build
npm test
cd ../backend
.venv/bin/python -m pytest -q
cd ..
)
```

The subshell stops on command failure; do not proceed after a failed command. Dependency setup may need internet. Node/npm versions remain pinned; use an existing matching installation if you do not use nvm. In VS Code run **Python: Select Interpreter** and select the new `backend/.venv/bin/python`. Existing terminals should be recreated so their current directories and activation paths match.

After tests, update the desktop program copy from the new root, keeping the same custom XDG settings and port:

```bash
cd "$NEW_REPO"
python3.12 desktop/install.py --port 8000
```

Substitute your saved port from `engage-application/config.json` if different; preserve it to retain browser-origin preferences and drafts. The installer preserves configured icons and the established profile/state paths. Existing `org.engage.*.desktop` entry IDs are updated in place with CyrNava names, avoiding duplicate launchers. A GNOME trust prompt may require **Allow Launching** again. Open the app, confirm title/header CyrNava, choose Dark/System, collapse navigation, open an existing note/image and custom template, then edit a synthetic note, wait for Saved, close/reopen and verify it persists.

## Rollback

Stop all app/development processes and close VS Code first. Retain the migrated checkout and every backup. No data rollback is normally required: the profile path and schema never changed. Do not replace newer notes with an older backup merely to restore the old folder name.

To reverse only the directory/remote change, read `migration.json`, verify the recorded original path is absent and verify the new checkout contains your work. From a terminal outside it, move it back with `mv -T --no-clobber`, verify the original now exists and the new path is absent, then set `origin` to the recorded previous URL. Rebuild its venv again at the restored path. These are manual review steps, not an automatic destructive rollback.

Alternatively, verify `repository.tar.sha256` with `sha256sum -c` from the backup directory, create a **new, private, empty** recovery directory outside Git, and extract your trusted `repository.tar` there. Inspect Git status/HEAD/configuration before using it. That archive represents the reviewed source immediately before the move; it does not undo the rebranding commit. Dependency environments must be rebuilt. Earlier installed application releases are retained by the installer; selecting one for program rollback is separate from source migration and does not require deleting the profile.

If data recovery is actually needed, follow [BACKUP_RESTORE.md](../BACKUP_RESTORE.md) and restore `profile.engage-backup` to a **new** profile. Preserve the current profile, inspect both copies and deliberately choose which to launch. Never extract over an existing checkout or restore over existing application data.
