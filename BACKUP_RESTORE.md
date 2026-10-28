# Local backup and restore (M5)

CyrNava backups are **unencrypted private directories**, not archives. Keep them outside every Git checkout and on storage you control. Checksums detect accidental changes; they do not authenticate a backup from another person. Restore only trusted local backups.

## Before backing up

1. Finish editing. Wait for image uploads to finish and **Saved** to appear.
2. Close the CyrNava browser tab, then stop **all backend processes**, including any Uvicorn reload supervisor, with Ctrl+C in their terminals. Stop Vite too for the simplest procedure.
3. Run backup only after a clean shutdown. It captures confirmed SQLite/filesystem data, not unsaved browser drafts.

M5 backends hold a shared Linux profile lock for their entire lifetime. The backup tool takes the exclusive lock and refuses to run while any cooperating backend remains open. This also prevents an M5 backend from starting during backup. Older CyrNava versions and external SQLite/file tools do not participate: stop those yourself. The lock is a guard, not a live-backup feature.

## Data paths

The profile directory contains `engage.sqlite3` and `assets/`:

- If `XDG_DATA_HOME` is an absolute path: `$XDG_DATA_HOME/engage/`.
- Otherwise: `~/.local/share/engage/`.
- The CLI's `--data-dir` takes that **full profile directory**, including `engage`.
- The backend's `XDG_DATA_HOME` takes the **parent** of that directory.

A relative XDG value is ignored, consistent with the existing application. Current backup validation supports schema versions **3 and 4**. You can back up a schema-3 profile before its first FF-018 startup. Older schemas must be upgraded to a supported version before this tool can validate them.

FF-018 startup adds schema 4's two template tables in one transaction, without rewriting existing note/folder/asset rows. Keep the pre-upgrade backup: older application code rejects schema 4. To return to old code, restore that schema-3 backup into a separate new profile; there is no in-place downgrade. This implementation does not automatically upgrade or reinstall your everyday desktop application.

## Create a backup

From the repository root:

```bash
# Choose a private location outside Git. This creates only the parent directory.
BACKUP_PARENT="$HOME/Backups/engage"
mkdir -p "$BACKUP_PARENT"
BACKUP_PATH="$BACKUP_PARENT/workspace-$(date +%Y%m%d-%H%M%S).engage-backup"
cd backend
.venv/bin/python -m app.backup backup --destination "$BACKUP_PATH"
```

The default source follows the same XDG rules as the backend. To choose it explicitly:

```bash
.venv/bin/python -m app.backup backup \
  --data-dir "/absolute/path/to/profile/engage" \
  --destination "/absolute/private/backups/new-workspace.engage-backup"
```

The destination must **not exist**; its parent must exist. The tool never overwrites an existing backup, even an empty directory. Do not place the destination inside the source profile or vice versa. Symlink paths and paths inside the CyrNava checkout are rejected. Choose a location outside other checkouts too; the runtime guard knows this application's checkout, not every repository on your computer.

On success, the tool prints `Backup completed and validated` and exits 0. Errors exit 1 with a concise message. Do not treat a failed command as a usable backup.

### Exact contents and consistency

```text
new-workspace.engage-backup/
├── manifest.json
├── engage.sqlite3
├── assets/
│   └── <each asset UUID referenced by SQLite metadata>
└── .engage.lock  (cooperative lock file; no application content)
```

The complete SQLite file includes folder hierarchy, notes, native BlockNote JSON, IDs, timestamps, revisions, image metadata and ownership. Schema 4 also includes custom template definitions and their independent image snapshots in SQLite. Built-in templates are supplied by application code. All metadata-owned note image files are included, even if not yet referenced in a saved document. This preserves M4's conservative retention policy. Unowned crash debris, dependency environments, source code, unsaved browser drafts and browser preferences (including navigation collapse) are not part of the saved workspace and are not copied.

Before copying, the tool opens SQLite read-only and checks integrity, foreign keys, schema version, folder cycles, note JSON and image ownership. Every owned image must exist, match its recorded byte size, and pass the existing image-content validation. Stored bytes are copied unchanged; validation's normalized output is discarded. SHA-256 hashes of the database and each image go into the manifest.

For schema 4, it also validates each template's native JSON and exact image snapshot membership, limits and raster contents. A damaged template image fails backup rather than being skipped. Template snapshots are covered by the database checksum; they do not require extra files or a new manifest format. Schema-3 backups are validated and restored without migration; only starting the new backend on a restored runtime profile upgrades its schema.

Copying happens in a new private staging directory beside the destination. The copy is revalidated before publication; an exclusive mkdir reserves the destination. No archive entries or manifest-supplied paths choose output files. New directories are 0700 and files 0600. The source profile stays offline and locked during copying. SQLite journal/WAL sidecars are rejected instead of being ignored: cleanly stop/recover the database first.

## Restore into a new profile

Keep the original profile and backup intact. Stop all backend processes. From `backend/`:

```bash
RESTORE_BASE="$HOME/.local/share/engage-restored"
mkdir -p "$RESTORE_BASE"
.venv/bin/python -m app.backup restore \
  --source "/absolute/private/backups/new-workspace.engage-backup" \
  --data-dir "$RESTORE_BASE/engage"
```

`$RESTORE_BASE/engage` must not already exist. There is no overwrite switch: use a genuinely new destination. Missing/invalid manifests or databases, missing/damaged images, broken relationships, changed checksums and unsafe paths are rejected before publication. Copying failures clean up the tool's staging/partial destination where possible and do not replace existing data.

On success, start the restored backend **with the parent path as XDG_DATA_HOME**:

```bash
XDG_DATA_HOME="$RESTORE_BASE" .venv/bin/python -m uvicorn app.main:app \
  --host 127.0.0.1 --port 8000
```

In another terminal, from the repository's `frontend/`:

```bash
npm run dev
```

Open `http://127.0.0.1:5173`. Confirm the folders, notes, formatting, image positions and image rendering. Make an edit, wait for Saved, reload and confirm it persists. Original identifiers are preserved, so the browser's preferred-note ID can still work; if not, select the restored note from the tree. Changing the environment for this command does not move or replace the original profile.

For a schema-4 backup, also open **Manage templates** and create a test note from a restored custom template. Check its formatting and images; the restored template can remain usable even if its original source note was deleted before backup.

**A backup is verified for recovery only after a restore/open drill.** M5's automated drill performs that sequence in isolated temporary profiles and checks rendered BlockNote formatting plus image decoding. See `M5_VERIFICATION.md` and the restored-workspace preview.

## Failures and limits

- Backend running: stop every instance, then retry. Never bypass the lock or delete its file to force a backup.
- Missing/corrupt image or invalid DB: retain the original and any earlier good backup; investigate before retrying. The tool does not silently skip broken data or repair it.
- Existing destination: choose a new path. No original directory is removed automatically.
- Write/disk-full error: command fails. Check available storage and retry at a new path after reviewing any failed staging destination.
- Abrupt power loss/forced tool termination may leave a staging or incomplete newly reserved destination. It was not reported successful. Retain the intact source/backup, and review that failed destination before choosing another path. Crash-durable publication, encryption, scheduled/cloud backup and backup migration are outside M5.

Normal application use, backup and restore require no network. Installing Python/npm packages and the Playwright test browser may require network access once.
