# ENGAGE M2 verification — 2026-10-22 (Asia/Seoul)

Environment: existing M1 environments, Node 24.19.0, npm 11.6.2, Python 3.12.14 and SQLite 3.53.1 on the supplied Linux host. No package versions or lockfiles changed. This is M2 evidence; the existing `VERIFICATION.md` remains the historical M1 record.

## Automated checks executed

Commands run from the specified directory:

| Directory / command | Observed outcome |
| --- | --- |
| `backend`: `.venv/bin/python -m pytest -q` | 49 passed, including retained M0/M1 tests |
| `backend`: `.venv/bin/python -m ruff check .` | Passed |
| `backend`: `.venv/bin/python -m ruff format --check .` | Passed; 8 files formatted |
| `backend`: `.venv/bin/python -m pip check` | No broken requirements |
| `frontend`: `npm test` | 52 passed across 7 files |
| `frontend`: `npm run lint` | Passed after preserving the caught error as `cause` |
| `frontend`: `npm run build` | TypeScript and Vite bundling passed |
| Repository: `git diff --check` | Passed |

The backend suite covers root/nested folders; 1,202 levels; retrieval through the tree; rename/reparent/root moves; self/descendant/nonexistent-parent rejection; competing cycle-producing writes; note creation/moves/root moves and JSON/metadata preservation; note deletion revision guards; empty/recursive folder deletion; impact counts/intent; changed counts and same-count replacement; changed note revisions; rollback of an interrupted recursive delete; actual SQLite FK enforcement; reconnect persistence; deterministic sorting; copied-M1 migration and repeated startup; failed-migration rollback; code-block JSON; and the existing M1 validation/revision/health cases.

The frontend suite covers nested rendering; expand/collapse; mouse/Enter note opening; new note/folder creation; selected-folder placement; rename/move; invalid operations; exact confirmation counts; cancellation; note deletion; stale deletion errors; tree keyboard traversal and F2/Delete; editor keyboard isolation; save-state feedback; navigation waiting for pending saves; failed-save navigation blocking; immediate same-event edits; preserving editor focus during summary refresh; pre-M2 discovery without localStorage; ID-only preference; API request/intent contracts; a 2,000-folder iterative traversal; and retained M1 debounce/stale-response/conflict tests.

## Real browser acceptance — all mandatory A–U steps completed

An isolated M1-style fixture was created, then copied before launching M2:

- M1 source: `/tmp/engage-m2-acceptance.1ojVBv/m1-original.sqlite3`.
- M2 application data: `/tmp/engage-m2-acceptance.1ojVBv/data/engage/engage.sqlite3`.
- `XDG_DATA_HOME=/tmp/engage-m2-acceptance.1ojVBv/data`.
- Backend `127.0.0.1:8012`; Vite `127.0.0.1:5185` with `ENGAGE_API_PORT=8012`.
- The browser preference was initially absent on this isolated origin. The migrated “M1 original” note was still discovered and opened.

Only synthetic test notes were used. Destructive tests never used the real data path. The acceptance runner did not stop or reconfigure default services; it used only these separate ports and temporary data.

| Required step | Observed result |
| --- | --- |
| A. Start both applications | Started isolated backend/Vite and loaded M2; health online |
| B. Root HTB Academy | Created through New folder with root destination |
| C. Nested B01 | Created inside selected HTB Academy |
| D. Nested Enumeration | Created inside B01 |
| E. Nmap note | Created inside Enumeration |
| F. H1, paragraph, H2, code | Entered through the real BlockNote editor; inspected actual `h1`, `h2`, and `pre` DOM contents |
| G. Save | Saved observed after real PATCH |
| H. Second note | Created Web enumeration in the same folder |
| I. Switch notes | Typed pending content, immediately created/switched notes; drain completed before transition |
| J. Verify contents | Nmap retained headings/code and pending suffix; second note retained its paragraph |
| K. Rename folder | Enumeration became Reconnaissance |
| L. Move Nmap | Moved to B01; also moved to root and back through the GUI |
| M. Unchanged document | Exact JSON equality and stable ID/title/created_at checked; revision advanced only for moves |
| N. Keyboard | Left collapsed/moved to parent; Right expanded/entered children; Up/Down traversed; Enter opened HTTP notes; F2 renamed Web enumeration to HTTP notes; Delete opened confirmations; Escape dismissed an invalid-move dialog |
| O. Invalid move | Moving HTB Academy into Reconnaissance rejected with 422; hierarchy unchanged |
| P. Recursive confirmation | Created Discard test → Nested temporary → Temporary note; counts showed 1 subfolder and 1 note |
| Q. Cancel deletion | Cancel retained all items and their content |
| R. Confirm intended deletion | After an additional stale-confirmation check, fresh confirmation showed 1 subfolder and 2 notes; only that subtree was deleted |
| S. Restart both | Explicitly terminated and waited for both child processes; requests to both ports returned connection refused before restarting |
| T. Surviving data | Exact tree and all three surviving full note records matched their pre-restart snapshot; reopened each through the GUI |
| U. Pre-M2 accessibility | “M1 original” remained root-level and editable; its complete SQLite row matched the original M1 source byte-for-byte, including original JSON text and revision 7 |

Additional browser checks:

- Moved Reconnaissance with its nested note to HTB Academy and back to B01, preserving descendant identity/content.
- Held a deletion confirmation open in one tab, created “Late arrival” in the subtree in a second tab, then submitted the original confirmation. The backend returned 409; the first dialog reported changed contents and nothing was deleted. Cancel/Refresh/reopen produced fresh explicit counts before successful deletion.
- Compared all remaining full note records against a before-deletion snapshot; none changed.
- Direct note deletion required confirmation and cleared its active editor only after success.
- Tree focus returned to the selected/fallback item after dialogs/deletion; dialog Cancel had initial focus for destructive actions.

## Reproduce the manual procedure

Use a disposable XDG directory when testing deletion. From the repository root, create one outside Git and keep the printed path:

```bash
mktemp -d /tmp/engage-m2-review.XXXXXX
```

Start the backend with `XDG_DATA_HOME=<printed-path>` and the normal localhost Uvicorn command from README. Start Vite normally. Use a separate browser profile or origin for a clean preferred-note ID if needed; the tree discovers all notes regardless of that key. To reproduce the migration portion, place a stopped, copied M1 database at `<printed-path>/engage/engage.sqlite3` before starting M2; use synthetic data for deletion tests.

1. Select Workspace root; create HTB Academy, then B01, then Enumeration using each new folder's selection as the next parent.
2. Create Nmap; enter `# ` for H1, a paragraph, `## ` for H2, and three backticks plus space for a plain code block. Type a harmless command as text. Wait for Saved.
3. Add another edit and immediately create a second note. Enter a paragraph there, switch to Nmap and back, and verify both latest documents. Pending saves must complete before the destination opens.
4. Select Enumeration and rename it Reconnaissance. Open Nmap, Move it to B01, and verify all headings/code remain. Optionally move it to root and back.
5. Focus tree items and exercise arrows, Enter, F2, Delete and Escape. In BlockNote, verify typing/navigation continues normally.
6. Select HTB Academy, attempt moving it to Reconnaissance, and verify the rejection. Escape cancels.
7. At root, create a disposable folder, nested folder, and note. Request root deletion; check descendant counts. Cancel and verify all remain.
8. Reopen confirmation. In another tab create another note in that subtree. Submit the first tab's old confirmation; expect 409 and no deletion. Cancel, refresh, reopen, review fresh counts, then confirm.
9. Verify only the explicitly confirmed subtree disappeared. Create/delete a disposable standalone note to exercise its separate confirmation.
10. Wait for Saved. Stop both applications with Ctrl+C, verify listeners are gone, restart with the same XDG path, and reopen. Verify the hierarchy, both surviving notes, and the pre-M2 note through the GUI.

The implementation run used a cooperative subprocess controller in the task's `work/` directory so server shutdown was real and independently verified. No shutdown/control endpoint was added to ENGAGE. The controlled test servers are stopped after verification.

## Failures encountered and corrections

- An initial npm command ran from the repository root instead of `frontend`; it did not execute tests. Corrected the working directory.
- Ruff flagged long SQL/test strings; split/formatted them, then the check passed.
- The first full TypeScript check rejected Testing Library `getByRole` options containing Playwright's `exact` flag. Removed those test-only flags; build passed.
- ESLint required retaining a caught refresh error as the new error's `cause`. Added it and reran lint/build.
- Browser verification exposed initial dialog focus while its field was briefly disabled, and missing post-management tree focus. Focus now runs when the request unlocks; a guard prevents routine autosave refreshes from stealing editor focus. A regression test checks the latter.
- A successful mutation followed by a failed tree refresh is now identified as already committed. The dialog closes after the mutation response so a refresh failure does not invite duplicate mutation submission.

No final assertion failures remain. Existing upstream warnings remain visible: Starlette deprecates its HTTPX TestClient adapter, and Vite reports a large editor chunk. No unrelated dependency update was made to remove them.

## Coverage limits

Not executed: a new Ubuntu installation, dependency reinstall, mobile/touch use, assistive-technology screen-reader testing, full host-browser/OS termination, power-loss/disk-full scenarios, sustained lock contention, or packet-level external-network auditing. jsdom's dialog methods are stubbed because it does not model the browser top layer; real browser dialogs/keyboard/focus were checked separately.

Arbitrary logical depth is represented without a hard folder-depth cap; automated coverage demonstrates 1,202 backend levels and 2,000 frontend levels, not every possible size. Very large libraries are not benchmarked. External direct database edits and unsupported schema modifications are outside the application contract. All runtime services/targets are loopback, assets are local, and no remote highlighter/service was configured.
