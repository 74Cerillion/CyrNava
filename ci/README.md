# CyrNava continuous integration

`.github/workflows/ci.yml` verifies pushes to `main` and `desktop/p2-production-integration`, pull requests targeting `main`, and manual dispatches. It does not publish releases, sign packages, or change repository settings.

## Required jobs

`validate` checks the workflow contract and negative policy tests with the hash-locked parser and pinned actionlint. `backend` builds the real frontend before backend, security, lifecycle, migration and packaging regressions. It also runs the historical release-security regressions in a disposable source fixture. `frontend` runs lint, component tests, TypeScript/Vite production build and Chromium integration tests. `native` runs native installer/security/transaction and feasibility regressions on Ubuntu 26.04, then checks a clean no-Git source installation and a distinct-version compatible online update through the existing transaction engine. It verifies preserved profile/data bytes. `CI required` succeeds only when every required job succeeds.

The compatible test version does not establish support for arbitrary future application or database changes. Native GUI, GNOME menu and renderer sandbox operation require native host verification; headless CI does not establish those results.

## Trust and diagnostics

Actions are pinned in `tools.json`. Workflows use disposable GitHub-hosted runners, read-only repository permissions and checkout without persisted credentials. No production signing material is required. Preserve these boundaries: do not replace them with privileged PR triggers or owner machines.

Only the selected synthetic diagnostics are uploaded. Do not place personal data, credentials, raw environment dumps or private logs in upload paths. Public repository readers may be able to download workflow artifacts. Source-install CI uploads safe JSON diagnostics rather than a bundled-wheel application archive.

## Local verification

Use the Python and Node versions and host packages specified in the workflow. Backend checks require a dedicated `backend/.venv`, local loopback/socket access, Node/npm and Flatpak/OSTree for existing historical tests. Frontend browser checks require the lockfile's Chromium installation. Run from the repository root after creating that environment:

```bash
backend/.venv/bin/python -m pip install --only-binary=:all: -r backend/requirements.txt
backend/.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r ci/requirements.lock
backend/.venv/bin/python ci/validate.py
backend/.venv/bin/python -m unittest discover -s ci -p test_ci.py -v
backend/.venv/bin/python ci/bootstrap.py /tmp/cyrnava-ci-tools
/tmp/cyrnava-ci-tools/actionlint .github/workflows/ci.yml
backend/.venv/bin/python ci/verify.py backend
npm --prefix frontend ci --ignore-scripts --no-audit --no-fund
(cd frontend && npx --no-install playwright install --with-deps chromium)
backend/.venv/bin/python ci/verify.py frontend
```

In a fresh disposable Ubuntu 26.04 checkout with the workflow prerequisites, `/usr/bin/python3.14 -B -m unittest discover -s packaging/native -p 'test_*.py' -v` and the equivalent discovery under `packaging/native/feasibility` exercise the native fixtures. `/usr/bin/python3.14 -B ci/native_source.py --output ci-output/native-source` performs actual online acquisition/install/update checks, consumes disk and network, and requires a fresh output path and at least 11 GiB free. Use disposable profiles and installation roots; never substitute real notes or a normal installation.

## Historical tooling

The manually dispatched `release.yml` and `p5c.yml` workflows and `ci/release` helpers preserve historical Flatpak security regressions. They are not prerequisites for publishing the current source-first native release and do not publish automatically. Existing contracts, accepted-CI fixtures and security assertions remain tracked.

Current end-user installation and update instructions are in [native installation](../docs/native-installation.md).
