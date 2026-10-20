# Cybersecurity workspace — M0

A local development scaffold: React renders a two-pane shell, BlockNote owns a temporary scratchpad, and FastAPI answers one health request. **Notes exist only in browser memory and disappear on reload.** There is no saving, database, authentication, AI, collaboration, or external runtime service.

## Repository map

```text
.
├── .gitignore
├── .nvmrc
├── README.md
├── VERIFICATION.md
├── backend/
│   ├── app/{__init__.py,main.py}
│   ├── tests/test_health.py
│   ├── pyproject.toml
│   ├── requirements.in
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── package.json
    ├── package-lock.json
    ├── eslint.config.js
    ├── tsconfig.json
    ├── vite.config.ts
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── App.test.tsx
        ├── styles.css
        ├── test-setup.ts
        └── components/KnowledgeEditor.tsx
```

`frontend/node_modules/` and `backend/.venv/` are separate, ignored dependency environments. Generated output and caches are also ignored.

## Ubuntu setup

Target: **Ubuntu 24.04**, Python **3.12**, Node **24.x** (tested with 24.19.0), npm **11.6.2**. Downloads during installation require internet; running the application does not.

```bash
sudo apt update
sudo apt install -y git curl ca-certificates python3.12 python3.12-venv
```

Use an existing Node version manager, or install nvm following its [official instructions](https://github.com/nvm-sh/nvm#installing-and-updating). From this repository root:

```bash
nvm install                 # reads .nvmrc
nvm use
npm install --global npm@11.6.2

python3.12 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt

cd frontend
npm ci
cd ..
```

The Python commands call the virtual environment explicitly; activation is optional. Do not install Python packages globally. npm installs application packages inside `frontend/node_modules`; only the npm CLI is installed into the selected nvm environment.

Run in two terminals, starting from the repository root:

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

Open **http://127.0.0.1:5173**. Both services bind only to loopback. Port 5173 is fixed so configuration errors do not silently move the frontend. The backend status is checked once per mount, with a three-second timeout. Reload to check again after restarting the backend. Editing remains available when it is offline. Stop each server with Ctrl+C.

## Request flow and dependencies

```text
Browser / App.tsx
  → GET /api/health on 127.0.0.1:5173
  → Vite's development proxy removes /api
  → GET /health on FastAPI at 127.0.0.1:8000
  ← 200 {"status":"ok"}
  ← App displays "Backend: online"
```

The browser uses one origin; the proxy handles the second port, so no CORS middleware is needed. FastAPI has exactly one route. Its generated documentation and OpenAPI routes are disabled, avoiding CDN-based documentation assets.

The editor setup follows the [official BlockNote Mantine setup](https://www.blocknotejs.org/docs/getting-started/mantine). `KnowledgeEditor.tsx` is the only component that imports BlockNote. `@blocknote/core` defines the text block schema; `@blocknote/react` creates the editor; `@blocknote/mantine` supplies its UI. Mantine core/hooks satisfy the UI's peer dependencies. All three BlockNote packages have the same version, **0.56.0**. No BlockNote XL package is installed. Fonts and styles are served from installed packages.

Media blocks and the emoji picker are disabled to avoid remote media/dataset loading. A content security policy restricts asset and network requests to local sources (plus in-memory images); development HMR uses a local WebSocket. These are small restrictions needed for the no-external-runtime-calls requirement. Text formatting, lists, headings, quotes, and links remain available. The app never sends editor content to FastAPI.

## Verification commands

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

`build` checks TypeScript and creates `frontend/dist`; this milestone runs through the Vite development server, not a production deployment. Frontend unit tests substitute a simple editor placeholder and exercise shell rendering and health success/failure. They do not claim to test BlockNote internals. Backend tests check the health contract, method rejection, and route surface. See `VERIFICATION.md` for executed checks and limitations.

## Pins and deliberate choices

- Direct npm dependencies use exact versions; `package-lock.json` pins transitive resolution. Use `npm ci`, not an unreviewed update.
- `backend/requirements.in` records the five direct dependencies; `requirements.txt` freezes their complete tested resolution on Python 3.12. To intentionally update, edit the direct pins, create a fresh virtual environment, install `requirements.in`, run the checks, then regenerate with `python -m pip freeze > requirements.txt`.
- TypeScript **5.9.3** is intentional rather than the registry's TypeScript 7: the selected `typescript-eslint` supports TypeScript below 6.1. Mantine **8.3.11** is a supported BlockNote peer rather than switching to Mantine 9. Node type definitions stay on the Node 24 major.
- Runtime FastAPI and Uvicorn are installed without optional “standard” extras. pytest, httpx, and Ruff are development tools; httpx is only used by tests.
- One manifest/environment per language keeps dependencies understandable. No monorepo tool, container, API client abstraction, state framework, or persistence layer is introduced.

## Data boundary and M0 limits

Keep real notes, secrets, packet captures, exports, and databases **outside this repository** (for example in `$HOME/.local/share/cyber-workspace/` if persistence is designed later). M0 does not create or use that directory. `.gitignore` excludes common data paths, databases, captures, keys, environment files, and logs as a backup; Git ignore rules are not a general secret scanner. Repository files contain synthetic placeholder text only.

Assumptions: one local user, two terminal sessions, ports 5173/8000 available, Ubuntu 24.04 tooling. Storage format/location, note navigation, authentication, and deployment remain undecided and outside M0. Review this scaffold before adding any further milestone.
