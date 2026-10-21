# ENGAGE — M1: first persistent note

ENGAGE is a local cybersecurity knowledge workspace. M1 saves one rich-text note in SQLite and reopens it after refresh or application restart. The two-pane M0 layout remains; the scratchpad is now a titled persistent note.

**Wait for `Saved` before closing.** Unsaved drafts remain in browser memory; SQLite is authoritative for saved content. No internet connection is needed while using the application. Packages must already be installed.

## Ubuntu setup

Target: Ubuntu 24.04, Python 3.12, Node 24.19.0, npm 11.6.2. Existing M0 installations need no new dependencies.

```bash
sudo apt update
sudo apt install -y git curl ca-certificates python3.12 python3.12-venv
```

If `nvm` is missing, install Node Version Manager for your user account:

```bash
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.8/install.sh | bash
source ~/.bashrc
```

This follows the [official nvm installation instructions](https://github.com/nvm-sh/nvm#installing-and-updating). For zsh, reload `~/.zshrc` instead. From the repository root:

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

Python packages live in `backend/.venv`; JavaScript packages live in `frontend/node_modules`. Both are ignored by Git. npm's CLI is installed into the selected nvm environment. Installed dependency versions and lockfiles are unchanged from M0. Pydantic 2.14.1, already installed with FastAPI, is now explicitly declared because the note models import it directly.

## Run locally

**Restart an existing M0 backend first** so it loads the new notes routes. In its terminal, use Ctrl+C, then run from the repository root:

```bash
# Terminal 1
cd backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

```bash
# Terminal 2, from the repository root
cd frontend
npm run dev
```

Open **http://127.0.0.1:5173**. Keep both terminals running. Stop each with Ctrl+C. Only one process can listen on each port; `Address already in use` means another server is already there. Inspect it with `ss -ltnp 'sport = :8000'` or `ss -ltnp 'sport = :5173'` before stopping a process. Do not start duplicate servers. A backend started without `--reload` must be restarted after Python source changes.

Create the initial note, choose its title, and edit. Status progresses through `Unsaved Changes`, `Saving...`, and `Saved`. An error shows `Save Error` and retains the current draft. Ordinary failures have a Retry save button. Revision conflicts stop automatic saving; copy your local changes before reloading, because M1 does not merge competing edits.

The health message is explicitly a sample **at page load**, not a continuous availability monitor. Save feedback reports the result of actual note requests.

## Where the data lives

The backend creates its database and schema on first startup:

- With an absolute `XDG_DATA_HOME`: `$XDG_DATA_HOME/engage/engage.sqlite3`.
- Otherwise: `~/.local/share/engage/engage.sqlite3`.

Relative XDG values are ignored. A location inside this repository is rejected. Newly created data directories use mode 0700 and database files use mode 0600. Data is not encrypted. The existing `.gitignore` remains a secondary guard against committing databases, notes, captures, and credentials.

The browser stores **only the note ID** under `engage.note-id.v1` in localStorage. It fetches the title and native document JSON from SQLite on every opening. Keep using the same browser profile and origin (`127.0.0.1:5173`): changing host/port, clearing browser storage, or using private browsing can lose this pointer. The database content still exists, but M1 has no list/recovery interface. A missing remembered note produces an error instead of silently creating a replacement. Browsers that block localStorage cannot automatically reopen the note; creation reports that limitation and its generated ID.

M1 stores full BlockNote JSON with `format_version = 1`; it never uses Markdown or HTML as canonical storage. Media and remote emoji loading remain disabled. Fonts/styles are bundled locally. Backend documentation/CDN routes remain disabled. The frontend and backend bind to loopback.

## API and request flow

```text
React draft → debounced PATCH /api/notes/{id} on Vite
            → loopback FastAPI → conditional SQLite UPDATE → commit
            ← new revision and metadata ← HTTP response ← save-state acknowledgement
```

Vite now preserves `/api/notes` when proxying. The existing `/api/health` browser request is still specially forwarded to `/health`.

| Endpoint | Contract |
| --- | --- |
| `POST /api/notes` | `{title, document_json, format_version: 1}` → 201, full note, UUID, revision 1 |
| `GET /api/notes/{id}` | Full saved note; 404 for absent UUID, 422 for malformed UUID |
| `PATCH /api/notes/{id}` | `{revision, title?, document_json?}` → full updated note; expected revision is required |
| `GET /health` | Existing M0 health route |

Titles are trimmed and limited to 1–200 characters. A document must have at least one supported block and be at most 1 MiB when serialized, with at most 5,000 blocks and nesting depth 32. The supported M0 blocks are paragraphs, H1–H3 headings, bullets, numbered lists, checkboxes, and quotes. Validation checks the document envelope/inline structure while preserving native properties, styles, children, block IDs, links, and Unicode JSON. Unknown request fields and unsupported document versions are rejected. Invalid request bodies return 422. Stale revisions return 409 without writing. SQLite runtime failures return 503 with a generic message.

The browser sends one save at a time after 700 ms without edits. Typing while a request is pending changes the queued snapshot; an older response acknowledges only its own edit number. SQLite separately prevents writes based on outdated database revisions, including from another tab.

For isolated development checks, an optional numeric `ENGAGE_API_PORT` changes only the loopback proxy port. For example, `ENGAGE_API_PORT=8002 npm run dev -- --port 5175` uses a backend explicitly started on 8002. Default ports remain 8000/5173. Browser pointers differ by frontend port.

## Checks and implementation guide

```bash
cd frontend
npm run lint
npm test
npm run build
cd ../backend
.venv/bin/python -m pytest
.venv/bin/python -m ruff check .
.venv/bin/python -m ruff format --check .
.venv/bin/python -m pip check
```

Backend tests inject a temporary SQLite path through `create_app`; they never use the real data location. Frontend tests use the existing Vitest/Testing Library tools. Unit tests stub the rich editor; a separate adapter test checks JSON snapshots, and browser acceptance uses the actual BlockNote editor.

Read `M1_REPORT.md` for the complete file inventory, execution trace, concurrency example, decisions, and limitations. `VERIFICATION.md` records executed checks and the restart acceptance sequence. No dependencies, XL packages, folder features, or later milestones were added.
