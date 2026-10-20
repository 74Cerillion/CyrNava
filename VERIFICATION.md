# M0 verification — 2026-10-21 (Asia/Seoul)

Executed with Node 24.19.0, npm 11.6.2, Python 3.12.14 on the supplied Linux environment. Node/Python were available from bundled runtime paths rather than the shell PATH. A temporary npm CLI/cache was kept outside this repository in the task's `work/` directory. The documented clean Ubuntu 24.04 OS installation was not executed.

| Check | Outcome |
| --- | --- |
| `npm ci --no-audit --no-fund` | Passed, installed from committed-format lockfile |
| `npm ls --depth=0` | Passed, direct dependency tree satisfied |
| `npm run lint` | Passed, no warnings |
| `npm test` | Passed, 4 tests: healthy response, network error, HTTP error, invalid response |
| `npm run build` | Passed TypeScript checking and Vite bundling, including after final viewport change |
| `.venv/bin/python -m pytest` | Passed, 2 tests: health contract and restricted route/method surface |
| `.venv/bin/python -m ruff check .` | Passed |
| `.venv/bin/python -m ruff format --check .` | Passed, 3 Python files formatted |
| `.venv/bin/python -m pip check` | Passed, no broken requirements |
| Live `GET http://127.0.0.1:8000/health` | Passed: `{"status":"ok"}` |
| Live `GET http://127.0.0.1:5173/api/health` | Passed: same response through Vite proxy |
| Browser smoke check | Two panes, real BlockNote editor, backend online; typing worked; reload restored placeholder, proving temporary state |
| Lockfile check | No `@blocknote/xl*` packages |
| `git check-ignore` sample paths | Dependency environments, build output, notes, data, capture, `.env`, and SQLite paths correctly ignored |

Non-blocking warnings: Vite reports a JavaScript chunk above 500 kB (BlockNote UI). Bundle splitting is deferred beyond M0. Starlette 1.9.0 emits a development-only deprecation warning for its HTTPX TestClient adapter and recommends HTTPX2; existing tests pass using HTTPX 0.28.1. This upstream adapter migration is unresolved, not suppressed.

The initial browser check also reported a mobile viewport warning; `interactive-widget=resizes-content` was added to the viewport meta tag. There were no browser error-level messages in that check. Desktop browser behavior was checked; mobile keyboard behavior was not tested.

Runtime assets/fonts are local, the application fetches only `/api/health`, editor media/emoji fetching is disabled, generated API documentation is disabled, and the content security policy restricts network targets. This was source/configuration verification and a browser smoke check, not a packet-level network audit. No external application service was configured or called by the implementation. Dependency installation and official documentation lookup used the internet during setup.

Git is initialized on `main`; no commit or remote was created. No existing unrelated file was modified. M0 ends here pending owner review.
