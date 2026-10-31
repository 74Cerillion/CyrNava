# CyrNava P5A continuous integration

One verification-only workflow: `.github/workflows/ci.yml`. No signing, release,
publication, deployment or update endpoint is configured. Production remains
`io.github._74Cerillion.CyrNava`; development identity/storage is unchanged.

## Jobs and trust boundary

Pushes to `desktop/p2-production-integration` and `main`, PRs targeting `main`,
and manual dispatch run:

```text
validate -> backend  --+
         -> frontend --+-> flatpak build -> exported-bundle audit -> artifact
all four jobs ---------------------------------------------------> CI required
```

`CI required` runs even after failure and accepts only `success` from every job.
It is the suggested stable branch-protection check; no repository settings are
changed by these files. There are no path filters, tag triggers, privileged PR
triggers, production secrets, persisted checkout credentials or write-scoped
repository tokens. All four official actions are pinned to reviewed commit SHAs
in `tools.json`. Run steps never interpolate GitHub expressions as shell code.

Untrusted PRs run only on disposable GitHub-hosted runners with read-only repository
permissions. They receive no owner credentials. Do not change this to a self-hosted
runner, `pull_request_target`, or a privileged publishing context. A malicious PR
can change its own test code: workflow policy tests are maintenance safeguards,
not a substitute for review or branch protection.

## Local verification

From the repository root, using Python 3.12 and Node from `.nvmrc`:

```bash
backend/.venv/bin/python -m pip install --only-binary=:all: -r backend/requirements.txt
backend/.venv/bin/python -m pip install --require-hashes --only-binary=:all: -r ci/requirements.lock
backend/.venv/bin/python ci/validate.py
backend/.venv/bin/python -m unittest discover -s ci -p test_ci.py -v
backend/.venv/bin/python ci/bootstrap.py /tmp/cyrnava-ci-tools
/tmp/cyrnava-ci-tools/actionlint .github/workflows/ci.yml
backend/.venv/bin/python ci/verify.py backend
```

Flatpak and OSTree must be installed for the existing real timestamp-export test.
Backend tests also require local socket access. Python verification dependencies
use the existing exact pins in `backend/requirements.txt`; this file predates P5A
and has no hashes. The workflow parser has its own wheel/hash lock. Application
runtime wheels retain P4's hash-locked production requirements.

Frontend setup (backend venv is also required by browser integration tests):

```bash
npm --prefix frontend ci --ignore-scripts --no-audit --no-fund
cd frontend
npx --no-install playwright install --with-deps chromium
cd ..
backend/.venv/bin/python ci/verify.py frontend
```

This runs ESLint, 273 existing component/unit tests, TypeScript plus Vite production
build, and the existing production-mode Chromium integration suite. It does not
exercise Qt WebEngine renderer sandboxing, the desktop launcher or real native
file portals. The browser tests use synthetic temporary profiles and bind loopback.
The runner installs only the browser required by the lockfile's Playwright version.

## Production build and audit

`ci/flatpak.py prepare --output ci-output/flatpak` is restricted to disposable
GitHub-hosted runners. It adds the official upstream runtime supplier, installs
KDE/PySide refs, then selects **the exact P4 commits** and calls P4's verifier.
GPG verification stays enabled. A missing pinned object or required namespace
causes failure: there is no new-version or sandbox-disabling fallback. Upstream
Flathub is only a runtime supplier; CyrNava is not submitted or published there.
Do not spoof runner variables to provision an owner's machine.

The workflow installs Flatpak, OSTree, desktop-file-utils and AppStream via the
runner's Ubuntu package manager. It then runs:

```bash
python ci/flatpak.py build --output ci-output/flatpak
python ci/flatpak.py audit --output ci-output/flatpak
```

Build reuses `packaging/flatpak/production/build.py`. Its optional
`--output-directory NEW_PATH` avoids parsing console output; existing local cache
behavior is preserved. It refuses an existing output directory/symlink. Clean
tracked source is required by the CI wrapper. P4 still installs binary-only,
hash-locked CPython 3.13 wheels as data, uses the locked Qt/PySide BaseApp, builds
frontend production assets and retains desktop/icon/AppStream validators.

Audit imports the produced `.flatpak` into a new local OSTree repository, checks
out the exported commit, reruns P4's payload audit, checks required runtime files,
production native identity, metadata and least-privilege permissions, and compares
the actual exported inventory/provenance with the build records. Commit, bundle
size and hash must match. An old P4 artifact cannot stand in for a new CI build.
No application code or desktop window is executed by this audit.

Only after audit PASS is `artifacts/` populated with the unsigned Flatpak,
`SHA256SUMS`, build inputs, payload inventory, result and provenance. Normal
workflow success then uploads it with a seven-day retention and no recompression.
Missing files/upload errors fail the job. Failure diagnostics are separate JSON
and synthetic test reports; unvalidated bundles, full build trees, personal data,
environment dumps and secrets are never selected for upload.

GitHub workflow artifacts are not GitHub Releases. This repository is public;
authenticated users with repository read access may download workflow artifacts.
Do not upload anything private to these paths. P5A does not establish a production
update channel or public release entitlement.

## Caches and measured limits

Only npm's download cache is enabled, through the pinned official setup-node
Action. Keys include OS/architecture and the combined frontend lock/package and
Node version files. `npm ci` still verifies lockfile integrity; node_modules and
finished packages are not cached. GitHub cache ref scoping keeps PR cache writes
from replacing integration/main cache entries. Never consume these caches as a
trusted release artifact.

Local cold/warm download-cache measurements were 8.578/2.963 seconds at roughly
67 MB. Hosted cache transfer cost/hit rate still needs measurement. No complete
Qt runtime/build-tree cache or Python cache is added without evidence that its
size/restore overhead is worthwhile. See `evidence/p5a/npm-cache-measurements.json`.

The hosted OS/apt packages and Python 3.12 patch may evolve; runtime commits,
Python runtime wheels, Node, npm, frontend packages, actions and actionlint are
controlled. Record runner image/build tool versions; this is not a claim of
byte-for-byte reproducibility or hermetic builds.

## Evidence and authorization

See `P5A_REPORT.md`, `P5A_OWNER_CHECKS.md`, and `evidence/p5a/validation.json`.
Hosted PASS requires an actual GitHub run ID, source commit, job conclusions,
package/provenance/checksum and successful upload. Local policy/negative tests do
not establish hosted PASS or native portal coverage.

Do not push, change GitHub settings or manually dispatch this workflow without
owner authorization. Stop at P5A; no P5B/P5C work is included.
