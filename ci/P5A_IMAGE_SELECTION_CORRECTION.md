# P5A image-insertion test correction

**Local correction: PASS. P5A: FAIL / NOT ACCEPTED pending hosted verification.**

The failure at historical `frontend/e2e/workspace.spec.ts:656` was an invalid test
selection precondition. No production or BlockNote integration change is needed.

## Evidence and causality

Run 41176826666's first JPEG chooser succeeded. In its second iteration `/image`
remained literal code text; the Upload image button never existed, so both the
button click and chooser-event wait timed out. This was not evidence of a failing
native portal. Its original trace/screenshot/context remain under
`evidence/p5a/hosted-sql-boundary-2026-10-31/`.

The clean checkout initially had no frontend dist/node_modules or Python venv.
Dependencies were freshly installed with the existing locks; the venv uses CI's
Python 3.12 and the existing matching Playwright Chromium cache. All profiles were
new synthetic profiles with no option to target an owner workspace.

The observational DOM baseline reproduced chooser failure **4/5** times. A separate
synchronous keydown capture reproduced the same failure while recording both actual
DOM and ProseMirror model positions:

| Event in second image iteration | DOM caret | Editor model |
| --- | --- | --- |
| Before End | paragraph, position 239 | codeBlock, position 330 |
| Before Enter | paragraph, position 254 | codeBlock, position 330 |
| Before slash | codeBlock, position 331 | codeBlock, position 331 |

The active element was the contenteditable editor: browser focus alone was
insufficient. Clicking moved the DOM caret before the editor model consumed the
selection transition. End moved the DOM caret again; Enter was sent while the
model still selected code. Subsequent slash typing was therefore code text, where
slash suggestions should not open. This establishes the local causal chain. The
previous successful image selection did not establish the next cursor position.

Read-only diagnostics capture active element, DOM anchor/focus offsets and mapped
positions, collapsed state, model selection type/range/parent/ancestor block ID,
block types and loaded-image state. They use TipTap's DOM editor reference, which
its installed source explicitly attaches for tests. Nothing is exposed by the
production application. Installed ProseMirror's document selectionchange observer
and BlockNote's existing panel focus behavior were reviewed; source hashes are saved.

**Limit:** the historical trace did not record internal ProseMirror state. Local
reproduction matches its failure class but does not prove the exact historical
selectionchange schedule or a browser/BlockNote library defect. Instrumentation
changes timing; intermediate diagnostic outcomes and aborted runs are preserved.

## Exact correction

- `frontend/e2e/editorSelection.ts`: test-only, read-only selection snapshots and
  observable paragraph-cursor assertions. Requires focus, collapse, DOM/model
  position agreement and the correct paragraph block; no editor state is mutated.
- `frontend/e2e/workspace.spec.ts`: check each click/End/new-paragraph transition,
  await the selected Image suggestion, retain keyboard Enter and real file chooser,
  and wait for image load plus canonical persistence before the next operation.
  Verify that all original rich-text blocks remain unchanged after insertion.
- Add a browser regression proving `/image` remains literal inside code, then use
  normal clicks/keys and checked paragraph state to insert and persist an image.

Verification also exposed a later mobile-width measurement race in this same test.
BlockNote's closing popover is temporarily opacity-zero/visibility-hidden while
still mounted at its old absolute position. It continued contributing 405px scroll
width in the 390px viewport. The installed GenericPopover source uses transition
mounting. The test moves the pointer outside the editor and awaits menu **unmount**
then applies the original width assertion. No CSS, width limit or animation changed.

No production application, API behavior, autosave, revision conflict, clipboard,
image handling, keyboard navigation, security, Flatpak permission, or workflow
source changed. The accepted SQLite guard, its tests and lifecycle browser source
are byte-identical to 047a99b. All **33 production frontend assets are byte-identical**
after rebuilding with the correction. Test code is excluded from production assets.

## Verification and preserved failures

Final clean-checkout results:

- **10/10 focused executions:** original broad test and new regression, five each,
  no retries. Both JPEG/WebP uploads, original formatting and mobile-width check pass.
- **273 frontend unit tests + 20 browser integration tests PASS**, zero skipped;
  lint and TypeScript/production build PASS. All five lifecycle cases remain included.
- **9/9 accepted lifecycle-harness backend tests PASS**, one existing deprecation
  warning. These include production staging exclusion and fixture isolation.
- Full backend suite was not rerun: no application/shared lifecycle behavior changed.
  Its actual hosted 559 tests + 31 subtests remain separate historical evidence.

Intermediate results are not hidden: Python 3.14 could not satisfy the CI parser's
Python-3.12-only hash lock, so its disposable venv was recreated with Python 3.12;
no hash changed. The full-model diagnostic and initial correction reached later
mobile-layout failures. A preliminary keydown selector captured no model journal
and is not used as causal evidence. The corrected keydown recorder captured the
causal failure; a second attempt reached the existing 120s timeout and the third
was interrupted once evidence was sufficient (exit 130, not PASS). The first final
candidate passed all image operations/new regressions but still measured the
closing menu; its 5 failures/5 passes are retained. Waiting for unmount corrected
that measurement precondition, after which all 10 focused and all 20 browser cases
passed. No arbitrary delay, timeout increase, suppressed test or test retry was used.

Commands:

```bash
CYRNAVA_E2E_RELEASE=1 npx --no-install playwright test e2e/workspace.spec.ts --grep 'Phase 1 formatting|image command requires' --repeat-each=5 --trace=on --reporter=list,json
backend/.venv/bin/python ci/verify.py frontend
backend/.venv/bin/python -m pytest -q tests/test_lifecycle_harness.py
```

Run the first command from frontend and the last from backend; exact disposable
paths, environments, logs, source hashes and JUnit are in
`evidence/p5a/image-selection-correction-2026-10-31/manifest.json`.

**Recommendation:** approve one P5A-only commit and push of this test correction,
reports and non-sensitive evidence. The actual latest hosted run still FAILS and
its production package gates were skipped. Require a new authorized hosted PASS
before acceptance. No commit, push, rerun/dispatch, publication or P5B/P5C occurred.

Final cleanup review: diagnostic writes use `try/finally`, so a write failure cannot
bypass owned backend shutdown. The exact final source passed another 10/10 focused
executions and the full 273-unit / 20-browser suite, with no retries or skips.

## Hosted verification — 41179709348

The owner-pushed correction at 6743d1d passed both image tests and all 20 browser
cases, with 273 units and 559 backend tests +31 subtests PASS. Hosted selection
journals show synchronized paragraph readiness in both image iterations. This
correction is verified in the hosted environment. P5A remains FAIL because the
next package gate failed during pinned-runtime provisioning; no production package
was built or uploaded. See current P5A_REPORT and hosted-image-selection evidence.
