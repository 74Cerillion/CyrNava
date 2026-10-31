# Lifecycle verification correction evidence

Base: 72f4c7b0ca1de627b7615f03e20393cf5d423512; uncommitted two-file overlay
in a disposable clone, fresh dist/node_modules/backend venv, synthetic profiles.
Application, backend, native shell, packaging and workflow source are unchanged.

Historical run 41163754626 is still FAIL and remains in the sibling hosted-correction
directory. Its screenshot and error context were reviewed; no hosted trace exists.
The exact historical ordering cannot be reconstructed. Do not describe the
controlled ordering as an independently recorded historical fact.

The natural baseline passed 10/10; scheduling probes passed 3/3. A real-API response
gate then reproduced draft base 3 vs SQLite revision 4, with correct conflict
rejection. See gate-probe.txt and controlled-probe-source.ts.txt, plus its trace.
This demonstrates the missing precondition in the old outage simulation; it does
not justify automatic overwrites, timeouts, delays or retries.

Two initial instrumentation attempts were invalid: a newly added diagnostic
locator auto-waited for an element intentionally absent during draft choice.
They are preserved and excluded from application/regression PASS counts. The
non-waiting checkpoint corrected that investigation-only mistake. No production
or test timeout was changed. See exploration-classification.json.

Focused command in the clone's frontend directory:

    npx --no-install playwright test e2e/lifecycle.spec.ts --grep 'managed tabs close|committed write' --repeat-each=5 --trace=on --reporter=list,json

Full frontend command in clone root:

    backend/.venv/bin/python ci/verify.py frontend

CI contracts in development checkout:

    backend/.venv/bin/python -m unittest discover -s ci -p test_ci.py

Focused results: 10/10; complete: 273 units and 17 browsers; contracts: 23.
Raw reports, timing-only decoded revision timelines, synthetic traces, JUnit and
patch hashes are retained. Trace ZIPs may be ignored by Git but are retained
locally and hashed in manifest.json; textual timelines remain reviewable without
trace viewer. Future CI failures retain traces through the existing diagnostic
upload. No production bundle is generated or validated by this local correction.
