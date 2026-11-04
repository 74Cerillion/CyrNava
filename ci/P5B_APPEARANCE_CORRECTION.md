# P5B appearance placeholder test correction

31 October 2026. Local implementation/verification completed. The owner subsequently
authorized one correction commit and one push after review. No Actions rerun/dispatch,
staging configuration, signing-key creation or P5C/P6 work is authorized.
P5B remains CONDITIONAL; the historical hosted CI result remains FAIL.

Follow-up: correction commit 7aaefd0 was pushed by the owner. Required CI run
41205351385 passed all gates, including this test/regression, 273 units, all 21
browser tests and production Flatpak/audit/upload. See P5B_REPORT.md and
`evidence/p5b/hosted-ci-41205351385/`. The original investigation/limits below
remain historical; the full hosted event timing in the failed run remains unproven.

## Confirmed cause: invalid editor-state precondition in the test

Hosted [run 41197927704](https://github.com/74Cerillion/CyrNava/actions/runs/41197927704),
commit `3027231`, failed the appearance assertion originally at
`frontend/e2e/workspace.spec.ts:228`. Its target was simply the last paragraph.
That paragraph was empty and editable, but it was not the selected empty block
for which BlockNote displays its default placeholder. No production CSS defect
is established by this failure; the computed content `none` was correct there.

The test's `atEnd()` helper focused the contenteditable and installed a browser DOM
Range at its root end. It did not wait for a collapsed paragraph caret shared by
the DOM and ProseMirror. Formatting had previously selected text in an earlier
paragraph. Native editing commands therefore had an invalid synchronization
precondition; selecting a DOM position did not establish the editor-model position.
`Saved` reports persistence, not a selection or placeholder-rendering condition.

## Hosted trace, screenshot and CSS evidence

The retained synthetic screenshot and trace were inspected without executing trace
resources. Playwright snapshot references were resolved using its post-order node
format; derived records and the trace SHA-256 are in
`evidence/p5b/appearance-correction-2026-10-31/hosted-trace-analysis.json`.

| Hosted checkpoint | Trace observation |
| --- | --- |
| Escape, call xkfk@2564 | Editor has ProseMirror-focused class and contenteditable=true. An earlier paragraph contains `/ bold`; last paragraph is empty with trailing break, without empty-focus decoration. |
| Backspace, call xkfk@2566 | Earlier paragraph becomes ` bold`; last paragraph remains unchanged and undecorated. |
| Saved, call xkfk@2568 | Same editor/last-paragraph state; Saved does not move selection. |
| Placeholder polling | `::after` content remains `none`, as the assertion failure records. |

The snapshot contains the actual generated CSS rule requiring
`[data-is-empty-and-focused]:has(.ProseMirror-trailingBreak:only-child)::after`
to supply `Enter text or type '/' for commands`. The last paragraph lacks that
attribute; the document is not a single empty block. BlockNote 0.56.0's installed
`Placeholder.ts` adds that decoration only for an editable, collapsed non-code
selection whose model parent is empty. CyrNava's `styles.css` sets color/opacity
for empty-block hints; it does not change that content rule.

The screenshot corroborates the earlier split text, and the trace shows the
wrong paragraph receiving `/` and Backspace. Historical DOM caret offsets and
the ProseMirror object were not logged, so their exact numeric state and event-loop
interleaving are not invented. The invalid assertion target is directly established;
the unsynchronized DOM-only helper is independently reproduced below.

## Clean-checkout reproduction and correction

A fresh detached clone at `3027231` started without node_modules or frontend/dist.
Locked npm dependencies, a checkout-local Python environment and production assets
were installed/built there. No owner workspace or existing server was targeted.

Three instrumented baseline runs retained the original interaction sequence.
All three passed locally, so they are **not** claimed to reproduce the entire
hosted assertion failure. Read-only snapshots in the existing atEnd evaluation
did reproduce the model/DOM mismatch in every helper call: for example, DOM
position 374 while model selection remained 288–292 in the earlier paragraph.
During the initial helper call the model still pointed into a heading while the
DOM Range pointed at the document end. Those observations expose the invalid
assumption regardless of whether the next browser turn happens to synchronize.

Only `frontend/e2e/workspace.spec.ts` changes executable test code:

- Replace the appearance test's DOM-only helper with a click and Control+End,
  then use the existing read-only `editorSelection` / `paragraphCursor` diagnostics
  to require a focused, collapsed, synchronized paragraph cursor in the intended
  block at its content end.
- After Enter, require the new empty paragraph's block ID before typing `/`.
  After Escape, require the menu hidden and the same paragraph cursor before
  Backspace. After Saved, require that same empty/editable paragraph, caret inside,
  trailing-break structure and BlockNote's empty-focus decoration.
- Retain the original `Enter text` content assertion and 4.5 contrast requirement
  in both light and dark modes. Wrong content still fails; `none` is not accepted
  as a positive result.
- Save read-only diagnostics after Escape, Backspace and Saved: active element,
  model/DOM selection, target ID, editability, empty/focus flags, pseudo-element
  content/color/opacity. No note text, session credentials or native bridge is added.
- Add a regression with a nonempty selected paragraph and other empty paragraphs.
  It establishes why an unselected empty last paragraph correctly has no default
  hint, recreates the DOM-only/model mismatch in one JavaScript turn as a negative
  control, then uses user navigation to require the real placeholder and contrast.
  The negative control never issues typing commands from its invalid state.
  Focus/theme operations must leave canonical note data and revision unchanged.

No application, CSS, dependency, backend, release workflow, signing, packaging,
authentication, lifecycle, SQL fault-boundary or recovery source changes. No new
timeouts, sleeps, retries, skipped tests or weakened assertions.

## Verification

| Check | Result |
| --- | --- |
| Instrumented original sequence | 3/3 local PASS; model/DOM mismatch reproduced, full hosted failure not reproduced locally |
| Final corrected focused tests | 20/20 PASS: 10 appearance + 10 new regression; zero retries |
| State checks across repeats | 20 after-Saved focused/empty hints, 20 regression focused hints and 20 deliberate DOM-only mismatches independently checked |
| Complete clean-checkout frontend verification | PASS — lint, 273 unit tests, TypeScript/production build, 21/21 browser tests (5 lifecycle, 4 search, 12 workspace); zero retries |
| Existing hosted backend/security | Preserved PASS: 611 tests, 83 subtests; not rerun because production behavior did not change |
| Existing native P5B acceptance | Preserved owner-accepted PASS; no signing keys generated during this correction |
| New hosted correction verification | NOT EXECUTED; the single correction commit/push is now owner-authorized |

Commands and exact candidate hashes are recorded in
`evidence/p5b/appearance-correction-2026-10-31/verification.json`.
The final repeated source is copied byte-for-byte into the clean checkout.
Baseline, corrected and complete-suite diagnostics remain separate. Setup command
path/discovery mistakes that executed no tests are retained locally and identified
in the record; they are not relabeled as application failures or passing tests.

## Recommendation and limits

The correction addresses a confirmed test precondition defect, preserving the
original visual contract and production behavior. Exact historical scheduling is
unrecorded; successful local runs alone do not prove a future hosted result.
Local verification is complete; the owner authorized one P5B-only correction commit/push.
Do not rerun existing Actions or change GitHub staging settings under this grant.
Preserve the failed hosted trace and all successful backend/unit/lifecycle/native
evidence. Overall P5B acceptance still requires successful required CI, protected
hosted staging verification and explicit owner acceptance.
