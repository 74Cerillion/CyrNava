# Clean-clone verification procedure

The tested code is the clean baseline commit plus the four candidate files listed
and hashed in setup.json. No commit was created. The clone's baseline status was
clean; the overlay is explicitly uncommitted. See setup.json for initial absence
of dist, node_modules and backend/.venv, dependency-results.json for fresh setup.

1. Clone the integration branch with git clone --no-hardlinks --single-branch.
2. Overlay only .github/workflows/ci.yml, ci/verify.py, ci/validate.py, ci/test_ci.py.
3. Create a fresh Python 3.12 backend/.venv; install backend/requirements.txt and
   ci/requirements.lock (the latter using --require-hashes); run pip check.
4. Use Node 24.19.0/npm 11.6.2 and isolated npm/pip/XDG cache/data/config paths.
5. Run backend/.venv/bin/python ci/verify.py backend --require-clean-frontend.
6. Install the lockfile Playwright Chromium, without system package modifications.
7. Set PLAYWRIGHT_JUNIT_OUTPUT_FILE to ci-output/browser-junit.xml and run
   backend/.venv/bin/python ci/verify.py frontend.

Backend and frontend wrappers passed; their exact commands are implemented in the
hashed verifier patch. Browser setup timing is separate from backend overhead.
JUnit hostnames were removed; log trailing whitespace normalized for review.
All datasets are synthetic; no production profile or credentials were copied.
No GitHub workflow, push, publication, or native host verification was executed.
