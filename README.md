# ENGAGE — M5: reliability and verified recovery

ENGAGE is a local cybersecurity knowledge workspace. Its hierarchical library and persistent rich-text editor now support clipboard screenshots and local PNG, JPEG and WebP images. SQLite stores note JSON and image metadata; an application-owned directory stores image bytes. Everything runs locally. M5 adds deliberate conflict recovery and verified offline backup/restore, and strengthens failure feedback while preserving the existing editor and persistence paths.

**Wait for image uploads to finish and for Saved before closing the application.** Switching notes and opening management dialogs drain pending saves first. A failed save keeps the current draft open and blocks the transition.

## Ubuntu setup

Target: Ubuntu 24.04, Python 3.12, Node 24.19.0, npm 11.6.2. M4 adds Pillow 13.0.0 for backend image decoding and validation. Update existing backend environments with `.venv/bin/python -m pip install -r requirements.txt` from `backend/`. M5 also adds the development-only `@playwright/test==1.64.1` package; run `npm ci` in `frontend/` after updating. Runtime frontend package versions are unchanged.

```bash
sudo apt update
sudo apt install -y git curl ca-certificates python3.12 python3.12-venv
```

If nvm is missing, follow its [official installation instructions](https://github.com/nvm-sh/nvm#installing-and-updating), then reload your shell. From the repository root:

```bash
nvm install
nvm use
npm install --global npm@11.6.2
python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cd frontend
npm ci
cd ..
```

Dependencies remain isolated in `backend/.venv` and `frontend/node_modules`, both excluded from Git. Installation downloads packages; application operation uses only loopback services and bundled assets.

## Run and upgrade

Restart the backend after installing the updated requirements so it loads M5 profile locking. The schema remains version 3; M5 adds no migration or API route. Start each service once in its own terminal, from the repository root:

```bash
# Terminal 1
cd backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

```bash
# Terminal 2
cd frontend
npm run dev
```

Open **http://127.0.0.1:5173**. Stop each server with Ctrl+C. If a port is occupied, inspect its existing listener instead of starting a duplicate:

```bash
ss -ltnp 'sport = :8000'
ss -ltnp 'sport = :5173'
```

The startup migration upgrades SQLite `user_version` 1 to 2 in one transaction. M1's `CHECK(folder_id IS NULL)` cannot be removed using SQLite's limited ALTER TABLE; the migration copies every named note column into the new foreign-key-enabled definition, then replaces the old table. IDs, revisions, timestamps and original JSON text are copied unchanged. It creates the folders table and relationship indexes, checks foreign keys, and advances the schema version only on success. M4 then adds the assets table and its note-ownership index and advances to version 3 in the same startup transaction. Version 2 databases need only that additive step; existing notes/folders are untouched. Repeated starts at version 3 do not recreate tables. A newer or invalid schema fails without resetting application data. Tests exercise a **copy** of an M1 database, repeat initialization, and rollback after a failed migration.

## Use the library

- **Workspace root** clears the tree selection for creating root items.
- Click a folder label to select it. Its arrow expands/collapses it. Selection leaves the current editor open.
- **New folder / New note** creates inside the selected folder; when a note is selected, new items are its siblings. With no selection, creation is at root.
- Click a note to open it. Bold text and a dot mark the open note; selection has a background, and keyboard focus has an outline.
- **Rename / Move / Delete** acts on the selected item. Move uses a destination dialog; Workspace root is a valid destination. Invalid self/descendant folder moves are rejected by the backend.
- Every deletion asks for permanent-deletion confirmation. A folder confirmation explicitly counts descendant folders and notes; Cancel removes nothing. A changed subtree produces a conflict. Cancel and reopen deletion to review fresh counts rather than repeatedly submitting an outdated confirmation.
- **Refresh library** reads authoritative folder/note summaries, including changes from another tab. There is no continuous tree synchronization.

Tree ordering is deterministic: folders first, then notes, within each parent. Folders sort by stored `sort_order` (currently 0), case-insensitive SQLite name order, then ID; notes by case-insensitive title, then ID. Duplicate names are allowed. Manual ordering and drag-and-drop are outside M2.

| Key, while a tree item has focus | Behavior |
| --- | --- |
| Up / Down | Previous / next visible item; focus alone does not open notes |
| Left | Collapse an expanded folder; otherwise focus its parent |
| Right | Expand a folder; if already expanded, focus its first visible child |
| Enter | Open the focused note, or select/toggle the focused folder |
| F2 | Rename the focused item |
| Delete | Open permanent-deletion confirmation for the focused item |
| Home / End | First / last visible item |
| Escape, in a dialog | Cancel, unless its request is already running |

Keyboard handlers are attached to the tree or dialog, never globally. BlockNote retains its editing/navigation keys. Native modal dialogs keep background controls inert and return focus to the tree. Expansion state is kept in memory; on reload, ancestors of the reopened note are expanded automatically.

The editor supports headings, paragraphs, lists, checkboxes, quotes, and now a **plain code block**, required by M2 acceptance. Use `/` commands or Markdown-style input shortcuts (`# `, `## `, and three backticks followed by a space). Code is stored/displayed as text and never executed. No remote syntax highlighter or AI feature is configured. Images are fetched only from the local asset endpoint.

## Insert screenshots and images

- Paste an image from the clipboard with **Ctrl+V** inside the editor.
- Or type **/image**, select Image, then use **Upload image** to choose a local file.
- Supported: static PNG, JPEG, WebP. Limit: **10 MiB**, **8192 pixels per side**, **20 million total pixels**. Animated files, SVG, arbitrary attachments and external image embedding are excluded.
- Wait until **Uploading image…** disappears and **Saved** appears. Navigation waits for both upload completion and document autosave. Forced shutdown can still lose unfinished work.
- An upload error leaves existing content intact. Select/paste again to retry; a failed paste may leave an empty image placeholder, which can be reused or removed. Missing saved images show a visible error and preserve the document reference.
- File drag-and-drop is disabled in M4; use clipboard or the image selector. BlockNote's installed default drop path does not catch rejected upload promises.

Image files live beside the database in `engage/assets/<UUID>`, with 0700 directory / 0600 new-file permissions. No user filename is used as a path. Files are decoded and re-encoded before storage: original metadata and trailing data are removed; JPEG is recompressed. ENGAGE does not preserve forensic originals or original file hashes.

Assets belong to notes before document autosave completes. Failed saves therefore do not delete their uploaded images. Deleting a note (including through recursive folder deletion) removes its asset metadata; best-effort file cleanup follows. Startup retries cleanup and removes unowned generated files left by interrupted writes. Removed image blocks and abandoned uploads remain owned by the live note until that note is deleted. This conservative policy protects pending saves; fine-grained garbage collection is deferred.

Copying an existing image block into a different note is rejected by note ownership validation. Upload/paste the source image into the destination note instead. Moving a note between folders preserves its assets.

## Autosave and navigation

The existing 700 ms debounce and single-request saver remain. Local edit numbers prevent an old acknowledgement from marking newer edits Saved. Database revisions reject stale writes with HTTP 409.

A note transition first asks the editor adapter to finish pending uploads and apply their returned URLs, then asks `useAutosave.flush()` to drain its latest snapshot, bypassing only the debounce delay. The editor/title are briefly read-only while switching or managing items. A save error or conflict blocks the transition and retains the draft. Ordinary API errors retain the latest draft and stay visible until Retry save, even if typing continues. Correcting a local title-validation error resumes autosave. Identical title/document events do not schedule extra writes. Conflicts offer Review conflict and recover: inspect the saved version, download both versions as a local JSON recovery file, verify the download, then explicitly reopen the current saved note. The editor stays locked during that decision. No force-save or automatic merge is offered; keep the recovery file private and use it to compare/reapply your draft manually. Metadata changes to the active note remount it only after this drain, using the response's current revision, so the next autosave does not use an obsolete revision.

Saved content is in SQLite. Unsaved drafts remain in memory; the existing beforeunload warning cannot prevent forced process termination. Backend health is sampled at page load; save errors report actual note-request failures.

## Offline backup and restore

See **[BACKUP_RESTORE.md](BACKUP_RESTORE.md)** for the complete procedure and exact data-path mapping. Wait for Saved and all uploads, then stop every backend before copying. The M5 CLI uses a cooperative profile lock, read-only DB/image validation and SHA-256 manifests. It refuses existing destinations and restores only into a new profile.

From `backend/` (choose private absolute paths outside Git, with existing parent directories):

```bash
.venv/bin/python -m app.backup backup --destination /private/backups/new-workspace.engage-backup
.venv/bin/python -m app.backup restore --source /private/backups/new-workspace.engage-backup --data-dir /private/restored/engage
# For that restore, the backend uses XDG_DATA_HOME=/private/restored
```

Backups and conflict recovery downloads are **not encrypted**. Keep both private. A successful backup copy alone is insufficient: open the restored profile and verify notes and images. The M5 automated restoration drill does this without changing your personal profile.

## Data location and schema

The database path is unchanged:

- Absolute `XDG_DATA_HOME`: `$XDG_DATA_HOME/engage/engage.sqlite3`.
- Otherwise: `~/.local/share/engage/engage.sqlite3`.

Relative XDG values are ignored; paths inside the repository are rejected. Newly created data directories/files use 0700/0600 permissions. Data is local and unencrypted. Existing ignore rules remain a secondary guard against committing databases or user notes.

Library folders are logical SQLite records; creating them does not create filesystem directories. Folders use nullable `parent_id` adjacency relationships. Notes use nullable `folder_id`; null means root. SQLite foreign keys are enabled on every connection with RESTRICT deletion. Domain operations validate parent existence/cycles in serialized write transactions. Tree traversal and child-first recursive deletion are iterative, avoiding Python call-stack and SQLite cascade-depth limits. Notes still have their original native JSON, format version, revision and timestamps.

The browser's `engage.note-id.v1` key now remembers only the preferred open note. It does not determine library membership. Clearing browser storage or changing origins loses that preference, while all saved notes remain discoverable through the tree.

## API

Vite forwards `/api/*` unchanged, except the retained browser health request `/api/health`, which maps to `/health`.

| Operation | Contract |
| --- | --- |
| `GET /api/tree` | `{folders: [...], notes: [...]}` flat adjacency lists. Notes are summaries without `document_json`; relationships reconstruct the hierarchy without nested JSON depth limits. |
| `POST /api/folders` | `{name, parent_id?: UUID|null}` → 201, complete folder |
| `PATCH /api/folders/{id}` | `{name?, parent_id?}`; explicit null moves to root |
| `GET /api/folders/{id}/deletion-impact` | Fresh `{folder_id,name,descendant_folders,notes,token}` from one read transaction |
| `DELETE /api/folders/{id}` | JSON body `{recursive,expected_descendant_folders,expected_notes,impact_token}` → 204 |
| `POST /api/notes` | Existing `{title,document_json,format_version:1}` plus optional `folder_id` → 201 |
| `GET /api/notes/{id}` | Full saved note and metadata |
| `PATCH /api/notes/{id}` | Required expected `revision`, with `title?`, `document_json?`, `folder_id?`; explicit null moves to root; successful changes increment revision |
| `DELETE /api/notes/{id}` | Confirmed expected `{revision}` JSON body → 204 |
| `GET /health` | Existing health route |
| `POST /api/assets?note_id=UUID` | Raw image bytes, `Content-Type: image/png`, `image/jpeg` or `image/webp` → 201 `{id,note_id,mime_type,byte_size,url}` |
| `GET /api/assets/{id}` | Validated local image bytes; 404 for missing asset/file |

The existing read-only deletion-impact endpoint supplies fresh authoritative counts and a subtree fingerprint without downloading document contents. DELETE recomputes both inside `BEGIN IMMEDIATE`; count changes, membership substitutions, or changed revisions/metadata reject with 409. Nonempty deletion also requires explicit `recursive:true`. Notes are removed, then folders child-first, in one transaction. An exception rolls back the entire operation.

422 means invalid input/reference/cycle; 404 means a missing target resource; 409 means a stale note revision or deletion conflict; SQLite runtime failures map to a generic 503. Titles/names remain limited to 1–200 trimmed characters. Native document limits remain 1 MiB, 5,000 blocks, and depth 32; these document limits do **not** limit folder depth. Document format version 1 is preserved; code and image blocks are additive supported native block types. Image URLs must refer to assets owned by the containing note; empty image placeholders are allowed.

For isolated checks, `ENGAGE_API_PORT` can select another numeric loopback backend port; `npm run dev -- --port 5185` can select another frontend port. Defaults remain 8000/5173. An alternate frontend port has its own browser preference key namespace.

## Checks and engineering record

```bash
cd frontend
npm run lint
npm test
npm run build
cd ../backend
.venv/bin/python -m pytest -q
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pip check
```

Tests inject temporary database paths; destructive cases never use real application data. The frontend uses the existing Vitest/Testing Library stack; native rich-editor/modal behavior is also exercised in the browser acceptance run.

M5 adds a reproducible Chromium suite. From `frontend/`:

```bash
npx playwright install chromium
npm run test:e2e
```

On a minimal Ubuntu host, `npx playwright install --with-deps chromium` also installs required system libraries. Browser setup may download files; the tests themselves launch new loopback servers and isolated temporary profiles, stop/restart their own backend, verify failure recovery, and restore a backup into a separate profile. They never target an existing server or your default data directory. Fixtures are removed in cleanup. Generated evidence is under ignored `frontend/test-results/`.

Read `M5_REPORT.md` for the full A–H engineering report and file inventory, `M5_VERIFICATION.md` for exact results/failure-injection coverage, and `BACKUP_RESTORE.md` before backing up real data. Earlier milestone reports remain historical records. No commit, push, tag, M6 or later functionality is included.
